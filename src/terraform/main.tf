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
  filename      = "${path.module}/lambda.py"
  function_name = "ec2-tag-stopper"
  handler       = "stop_ec2_instances_with_tag"
  runtime       = "python3.8"

  # The `source_code_hash` is required for Lambda to work correctly
  source_code_hash = filebase64sha256("${path.module}/lambda.py")
}

# Create an AWS Lambda Event Source Mapping (Trigger)
resource "aws_lambda_event_source_mapping" "ec2_tag_stopper_trigger" {
  event_source_arn = aws_cloudwatch_event_rule.ec2_tag_stopper.arn
  function_name    = aws_lambda_function.ec2_tag_stopper.function_name
}