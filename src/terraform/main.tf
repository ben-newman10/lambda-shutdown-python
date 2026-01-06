terraform {
  backend "s3" {}
}

# Configure the AWS Provider
provider "aws" {
  region = var.region
}

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
  description = "Policy for our Lambda function to stop EC2 instances"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "ec2:DescribeInstances"
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action   = "ec2:StopInstances"
        Effect   = "Allow"
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:ResourceTag/${var.tag_key}" = var.tag_value
          }
        }
      }
    ]
  })
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

  source_code_hash = data.archive_file.ec2_tag_stopper_zip.output_base64sha256

  environment {
    variables = {
      TAG_KEY   = var.tag_key
      TAG_VALUE = var.tag_value
    }
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