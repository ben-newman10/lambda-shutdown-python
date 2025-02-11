terraform {
  backend "s3" {
    bucket         = "lambda-shutdown-terraform-state" # Replace with your S3 bucket name
    key            = "terraform/state"             # Path to store the state file within the bucket
    region         = "eu-west-2"                   # Replace with your AWS region
    encrypt        = true                          # Encrypt the state file on S3
  }
}

# Configure the AWS Provider
provider "aws" {
  region = var.region
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

# Create an IAM Policy for Lambda execution
resource "aws_iam_policy" "lambda_exec_policy" {
  name        = "lambda-exec-policy"
  description = "Policy for our Lambda function to execute"

  policy      = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Action = ["ec2:StopInstances"]
        Effect = "Allow"
        Resource = "*"
      },
    ]
  })
}

# Attach the IAM Policy to the Role
resource "aws_iam_role_policy_attachment" "lambda_exec_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_exec_policy.arn
}

# Create an IAM Policy for Lambda function execution (tag stopping)
resource "aws_iam_policy" "ec2_tag_stopper_policy" {
  name        = "ec2-tag-stopper-policy"
  description = "Policy for our Lambda function to stop EC2 instances"

  policy      = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Action = ["ec2:DescribeInstances", "ec2:StopInstances"]
        Effect = "Allow"
        Resource = "*"
      },
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
  filename      = "../ec2_tag_stopper.zip"
  function_name = "ec2-tag-stopper"
  handler       = "stop_ec2_instances_with_tag"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_exec.arn

  source_code_hash = filebase64sha256("../ec2_tag_stopper.zip")
}

# Create a CloudWatch Events rule to trigger at 7 PM every day
resource "aws_cloudwatch_event_rule" "ec2_tag_stopper" {
  name        = "ec2-tag-stopper-schedule"
  description = "Triggers the Lambda function every day at 7 PM"
  schedule_expression = "cron(0 19 * * ? *)" # 7 PM UTC Daily
}

# Create a CloudWatch Events Target to invoke the Lambda
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.ec2_tag_stopper.name
  arn       = aws_lambda_function.ec2_tag_stopper.arn
}

# Allow CloudWatch Events to invoke the Lambda function
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ec2_tag_stopper.arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ec2_tag_stopper.arn
}