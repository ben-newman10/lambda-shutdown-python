terraform {
  backend "s3" {}
}

# Configure the AWS Provider
provider "aws" {
  region = var.region
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Data source to zip the lambda code
data "archive_file" "ec2_tag_stopper_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../ec2_tag_stopper"
  output_path = "${path.module}/../ec2_tag_stopper.zip"
  excludes    = ["__pycache__", "test_lambda.py"]
}

# Create an IAM Role for Lambda execution
resource "aws_iam_role" "lambda_exec" {
  name        = "lambda-exec-role"
  description = "Execution role for our Lambda function"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

# Attach Basic Execution Role for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Create an IAM Policy for Lambda function execution (tag stopping)
resource "aws_iam_policy" "ec2_tag_stopper_policy" {
  name        = "ec2-tag-stopper-policy"
  description = "Least-privilege policy for Lambda to stop tagged EC2 instances"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "DescribeInstancesWithTag"
        Action   = "ec2:DescribeInstances"
        Effect   = "Allow"
        Resource = "*" # DescribeInstances doesn't support resource-level permissions
        Condition = {
          StringEquals = {
            "ec2:ResourceTag/${var.tag_key}" = var.tag_value
          }
        }
      },
      {
        Sid      = "StopTaggedInstances"
        Action   = "ec2:StopInstances"
        Effect   = "Allow"
        Resource = "arn:aws:ec2:${var.region}:${data.aws_caller_identity.current.account_id}:instance/*"
        Condition = {
          StringEquals = {
            "aws:ResourceTag/${var.tag_key}" = var.tag_value
          }
        }
      }
    ]
  })
}

# Create KMS key for Lambda encryption
resource "aws_kms_key" "lambda_encryption" {
  description             = "KMS key for Lambda function encryption"
  deletion_window_in_days = var.kms_deletion_window_days
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Logs"
        Effect = "Allow"
        Principal = {
          Service = "logs.${var.region}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/ec2-tag-stopper"
          }
        }
      },
      {
        Sid    = "Allow Lambda Service"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name        = "ec2-tag-stopper-lambda-key"
    Environment = "production"
  }
}

resource "aws_kms_alias" "lambda_encryption" {
  name          = "alias/ec2-tag-stopper-lambda"
  target_key_id = aws_kms_key.lambda_encryption.key_id
}

# Create Dead Letter Queue for Lambda
resource "aws_sqs_queue" "lambda_dlq" {
  name                      = "ec2-tag-stopper-dlq"
  message_retention_seconds = var.dlq_message_retention_days * 86400 # Convert days to seconds

  kms_master_key_id = aws_kms_key.lambda_encryption.id

  tags = {
    Name        = "ec2-tag-stopper-dlq"
    Environment = "production"
  }
}

# IAM policy for Lambda to send messages to DLQ
resource "aws_iam_role_policy" "lambda_dlq_policy" {
  name = "lambda-dlq-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.lambda_dlq.arn
      }
    ]
  })
}

# IAM policy for Lambda X-Ray tracing
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# CloudWatch Log Group with retention and encryption
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/ec2-tag-stopper"
  retention_in_days = var.log_retention_days

  kms_key_id = aws_kms_key.lambda_encryption.arn

  tags = {
    Name        = "ec2-tag-stopper-logs"
    Environment = "production"
  }
}

# Attach the IAM Policy to the Role
resource "aws_iam_role_policy_attachment" "ec2_tag_stopper_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.ec2_tag_stopper_policy.arn
}

# Create an AWS Lambda Function
resource "aws_lambda_function" "ec2_tag_stopper" {
  filename      = data.archive_file.ec2_tag_stopper_zip.output_path
  function_name = "ec2-tag-stopper"
  handler       = "ec2_handler.stop_ec2_instances_with_tag"
  runtime       = "python3.12"
  role          = aws_iam_role.lambda_exec.arn

  # Security configurations
  timeout                        = var.lambda_timeout_seconds
  memory_size                    = var.lambda_memory_mb
  reserved_concurrent_executions = 1 # Prevent runaway executions

  # Encryption
  kms_key_arn = aws_kms_key.lambda_encryption.arn

  # Dead Letter Queue
  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  source_code_hash = data.archive_file.ec2_tag_stopper_zip.output_base64sha256

  environment {
    variables = {
      TAG_KEY   = var.tag_key
      TAG_VALUE = var.tag_value
    }
  }

  # Enable X-Ray tracing
  tracing_config {
    mode = "Active"
  }

  # Ensure log group is created first
  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  tags = {
    Name        = "ec2-tag-stopper"
    Environment = "production"
  }
}

# Create a CloudWatch Events rule to trigger at 7 PM every day
resource "aws_cloudwatch_event_rule" "ec2_tag_stopper" {
  name                = "ec2-tag-stopper-schedule"
  description         = "Triggers the Lambda function every day at 7 PM"
  schedule_expression = "cron(0 19 * * ? *)" # 7 PM UTC Daily
}

# Create a CloudWatch Events Target to invoke the Lambda
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule = aws_cloudwatch_event_rule.ec2_tag_stopper.name
  arn  = aws_lambda_function.ec2_tag_stopper.arn
}

# Allow CloudWatch Events to invoke the Lambda function
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ec2_tag_stopper.arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ec2_tag_stopper.arn
}