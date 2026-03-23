# Security Audit & Remediation Plan

**Date**: March 23, 2026  
**Project**: EC2 Tag Stopper Lambda  
**Status**: Ready for Implementation

## Executive Summary

Security audit completed for the EC2 Tag Stopper Lambda project. While Python dependencies show no known vulnerabilities, several infrastructure and configuration improvements are needed to align with AWS security best practices and modern DevOps standards.

**Risk Level**: Medium  
**Estimated Effort**: 4-6 hours  
**Priority**: High

---

## Findings & Remediation Steps

### 1. GitHub Actions Workflow Dependencies ⚠️ MEDIUM PRIORITY

**Issue**: Using outdated GitHub Actions versions
- `actions/checkout@v2` (current: v4)
- `aws-actions/configure-aws-credentials@v2` (current: v4)

**Risk**: Missing security patches, deprecated features, potential compatibility issues

**Remediation**:
```yaml
# Update in .github/workflows/deploy-terraform.yml
- uses: actions/checkout@v4
- uses: aws-actions/configure-aws-credentials@v4
```

**Effort**: 15 minutes

---

### 2. Terraform Version Upgrade 🔴 HIGH PRIORITY

**Issue**: Using Terraform 1.0.11 (released October 2021)
- Current stable: 1.9.x
- Missing 3+ years of security patches and features

**Risk**: Known vulnerabilities, missing security features, compatibility issues

**Remediation**:
```yaml
# Update in .github/workflows/deploy-terraform.yml
wget https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_linux_amd64.zip
```

**Additional Steps**:
- Test locally with new version first
- Review Terraform upgrade guide for breaking changes
- Update any deprecated syntax

**Effort**: 1 hour (including testing)

---

### 3. IAM Policy Least Privilege 🔴 HIGH PRIORITY

**Issue**: Overly permissive IAM policies
```hcl
# Current - allows describing ALL instances
Action   = "ec2:DescribeInstances"
Resource = "*"
```

**Risk**: Excessive permissions, violates least-privilege principle

**Remediation**:
```hcl
# Improved policy with conditions
resource "aws_iam_policy" "ec2_tag_stopper_policy" {
  name        = "ec2-tag-stopper-policy"
  description = "Policy for Lambda to stop tagged EC2 instances"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DescribeInstancesWithTag"
        Action = "ec2:DescribeInstances"
        Effect = "Allow"
        Resource = "*"  # DescribeInstances doesn't support resource-level permissions
        Condition = {
          StringEquals = {
            "ec2:ResourceTag/${var.tag_key}" = var.tag_value
          }
        }
      },
      {
        Sid    = "StopTaggedInstances"
        Action = "ec2:StopInstances"
        Effect = "Allow"
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

# Add data source for account ID
data "aws_caller_identity" "current" {}
```

**Effort**: 30 minutes

---

### 4. Lambda Security Configuration ⚠️ MEDIUM PRIORITY

**Issue**: Missing critical Lambda security configurations
- No timeout set (defaults to 3 seconds, may be too short)
- No memory limit specified
- No Dead Letter Queue (DLQ) for failed invocations
- No reserved concurrent executions
- No encryption configuration

**Risk**: Function failures, no failure tracking, potential cost overruns

**Remediation**:
```hcl
resource "aws_lambda_function" "ec2_tag_stopper" {
  filename      = data.archive_file.ec2_tag_stopper_zip.output_path
  function_name = "ec2-tag-stopper"
  handler       = "ec2_handler.stop_ec2_instances_with_tag"
  runtime       = "python3.12"
  role          = aws_iam_role.lambda_exec.arn
  
  # Security configurations
  timeout                        = 60  # 1 minute should be sufficient
  memory_size                    = 256 # MB
  reserved_concurrent_executions = 1   # Prevent runaway executions
  
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
}

# Create KMS key for Lambda encryption
resource "aws_kms_key" "lambda_encryption" {
  description             = "KMS key for Lambda function encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "lambda_encryption" {
  name          = "alias/ec2-tag-stopper-lambda"
  target_key_id = aws_kms_key.lambda_encryption.key_id
}

# Create DLQ
resource "aws_sqs_queue" "lambda_dlq" {
  name                      = "ec2-tag-stopper-dlq"
  message_retention_seconds = 1209600 # 14 days
  
  kms_master_key_id = aws_kms_key.lambda_encryption.id
}

# Grant Lambda permission to send to DLQ
resource "aws_lambda_permission" "allow_dlq" {
  statement_id  = "AllowSQSDLQ"
  action        = "sqs:SendMessage"
  function_name = aws_lambda_function.ec2_tag_stopper.function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = aws_lambda_function.ec2_tag_stopper.arn
}
```

**Effort**: 1 hour

---

### 5. CloudWatch Logs Retention ⚠️ MEDIUM PRIORITY

**Issue**: No retention policy configured for Lambda logs
- Logs retained indefinitely by default
- Increases storage costs
- Compliance concerns

**Risk**: Unnecessary costs, potential compliance violations

**Remediation**:
```hcl
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.ec2_tag_stopper.function_name}"
  retention_in_days = 30  # Adjust based on compliance requirements
  
  kms_key_id = aws_kms_key.lambda_encryption.arn
}
```

**Effort**: 15 minutes

---

### 6. Terraform S3 Backend Encryption 🔴 HIGH PRIORITY

**Issue**: No visible encryption configuration for Terraform state
- State file may contain sensitive data
- Should use encryption at rest

**Risk**: Potential exposure of sensitive infrastructure data

**Remediation**:
```hcl
# Update backend.conf
bucket         = "your-terraform-state-bucket"
key            = "ec2-tag-stopper/terraform.tfstate"
region         = "eu-west-2"
encrypt        = true
kms_key_id     = "arn:aws:kms:eu-west-2:ACCOUNT_ID:key/KEY_ID"
dynamodb_table = "terraform-state-lock"
```

**Additional**: Ensure S3 bucket has:
- Versioning enabled
- Server-side encryption enabled
- Public access blocked
- Bucket policy restricting access

**Effort**: 30 minutes

---

### 7. Enhanced Lambda Error Handling ⚠️ MEDIUM PRIORITY

**Issue**: Basic error handling in Lambda code
- Generic exception catching
- Limited error context
- No retry logic for transient failures

**Risk**: Difficult troubleshooting, potential silent failures

**Remediation**:
```python
import boto3
import os
import logging
from botocore.exceptions import ClientError, BotoCoreError

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ec2 = boto3.client('ec2')

def stop_ec2_instances_with_tag(event, context):
    """
    Stop EC2 instances matching specified tags.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        dict: Response with status and details
    """
    tag_key = os.environ.get('TAG_KEY')
    tag_value = os.environ.get('TAG_VALUE')

    # Input validation
    if not tag_key or not tag_value:
        error_msg = "Environment variables TAG_KEY and TAG_VALUE must be set"
        logger.error(error_msg)
        return {
            'statusCode': 400,
            'body': error_msg
        }

    logger.info(f"Starting EC2 instance stop process for tag {tag_key}={tag_value}")

    try:
        # Filter EC2 instances with pagination
        paginator = ec2.get_paginator('describe_instances')
        page_iterator = paginator.paginate(
            Filters=[
                {
                    'Name': f'tag:{tag_key}',
                    'Values': [tag_value]
                },
                {
                    'Name': 'instance-state-name',
                    'Values': ['running']
                }
            ]
        )

        instances_to_stop = []
        for page in page_iterator:
            for reservation in page['Reservations']:
                for instance in reservation['Instances']:
                    instances_to_stop.append(instance['InstanceId'])
        
        # Stop instances if found
        if instances_to_stop:
            logger.info(f"Found {len(instances_to_stop)} instances to stop: {instances_to_stop}")
            
            response = ec2.stop_instances(InstanceIds=instances_to_stop)
            
            # Log stopping instances details
            stopping_instances = response.get('StoppingInstances', [])
            for instance in stopping_instances:
                logger.info(
                    f"Instance {instance['InstanceId']} transitioning from "
                    f"{instance['PreviousState']['Name']} to "
                    f"{instance['CurrentState']['Name']}"
                )
            
            return {
                'statusCode': 200,
                'body': f"Successfully initiated stop for {len(instances_to_stop)} instances",
                'instances': instances_to_stop
            }
        else:
            logger.info(f"No running instances found with tag {tag_key}={tag_value}")
            return {
                'statusCode': 200,
                'body': "No running instances found matching criteria"
            }
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(
            f"AWS API error: {error_code} - {error_message}",
            exc_info=True
        )
        return {
            'statusCode': 500,
            'body': f"AWS API error: {error_code}"
        }
    
    except BotoCoreError as e:
        logger.error(f"Boto3 error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': "Internal error communicating with AWS"
        }
    
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': "Internal server error"
        }
```

**Effort**: 45 minutes

---

### 8. CI/CD Security Scanning 🔴 HIGH PRIORITY

**Issue**: No security scanning in CI/CD pipeline
- No SAST (Static Application Security Testing)
- No dependency vulnerability scanning
- No Terraform security scanning

**Risk**: Deploying vulnerable code/infrastructure

**Remediation**:
```yaml
# Add to .github/workflows/deploy-terraform.yml

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Run Checkov for Terraform
        uses: bridgecrewio/checkov-action@master
        with:
          directory: src/terraform
          framework: terraform
          output_format: sarif
          output_file_path: checkov-results.sarif

      - name: Upload Checkov results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: checkov-results.sarif

      - name: Python Security Check
        run: |
          pip install safety bandit
          safety check --file requirements-dev.txt
          bandit -r src/ec2_tag_stopper/ -f json -o bandit-results.json

  deploy:
    needs: security-scan
    runs-on: ubuntu-latest
    # ... rest of deploy job
```

**Effort**: 1 hour

---

### 9. Python Dependencies Update ✅ LOW PRIORITY

**Issue**: Dependencies could be updated to latest versions

**Current Status**: ✅ No known vulnerabilities found

**Recommendation**: 
```txt
# requirements-dev.txt - Updated versions
iniconfig==2.1.0
packaging==26.0
pluggy==1.5.0
pytest==8.3.5
```

**Effort**: 15 minutes

---

### 10. Input Validation & Sanitization ⚠️ MEDIUM PRIORITY

**Issue**: Limited input validation in Lambda function
- Tag key/value not validated for format
- No length checks
- No sanitization

**Risk**: Potential injection attacks, unexpected behavior

**Remediation**:
```python
import re

def validate_tag_input(tag_key, tag_value):
    """
    Validate tag key and value format.
    
    Args:
        tag_key: Tag key to validate
        tag_value: Tag value to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # AWS tag key constraints
    if not tag_key or len(tag_key) > 128:
        return False, "Tag key must be 1-128 characters"
    
    if not re.match(r'^[\w\s\.\-\:\/\=\+\@]*$', tag_key):
        return False, "Tag key contains invalid characters"
    
    # AWS tag value constraints
    if not tag_value or len(tag_value) > 256:
        return False, "Tag value must be 1-256 characters"
    
    if not re.match(r'^[\w\s\.\-\:\/\=\+\@]*$', tag_value):
        return False, "Tag value contains invalid characters"
    
    return True, None

# Use in lambda handler
is_valid, error = validate_tag_input(tag_key, tag_value)
if not is_valid:
    logger.error(f"Invalid tag input: {error}")
    return {
        'statusCode': 400,
        'body': f"Invalid input: {error}"
    }
```

**Effort**: 30 minutes

---

### 11. Security Documentation 📝 LOW PRIORITY

**Issue**: README lacks security best practices section

**Remediation**: Add security section to README.md covering:
- IAM permissions required
- Encryption at rest/in transit
- Logging and monitoring
- Incident response
- Regular security updates
- Secrets management (AWS Secrets Manager for sensitive configs)

**Effort**: 30 minutes

---

## Implementation Priority

### Phase 1: Critical (Week 1)
1. ✅ Terraform version upgrade
2. ✅ IAM policy least privilege
3. ✅ Terraform S3 backend encryption
4. ✅ CI/CD security scanning

### Phase 2: Important (Week 2)
5. ✅ Lambda security configurations
6. ✅ CloudWatch Logs retention
7. ✅ Enhanced error handling
8. ✅ GitHub Actions updates

### Phase 3: Improvements (Week 3)
9. ✅ Input validation
10. ✅ Python dependencies update
11. ✅ Security documentation

---

## Testing Plan

After each remediation:
1. **Local Testing**: Test Terraform changes locally with `terraform plan`
2. **Staging Deployment**: Deploy to staging environment first
3. **Functional Testing**: Verify Lambda still stops instances correctly
4. **Security Validation**: Run security scans to confirm fixes
5. **Production Deployment**: Deploy to production with monitoring

---

## Monitoring & Alerts

Add CloudWatch alarms for:
- Lambda errors/throttles
- DLQ message count
- IAM policy violations
- Unexpected instance stops

```hcl
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "ec2-tag-stopper-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alert on Lambda function errors"
  
  dimensions = {
    FunctionName = aws_lambda_function.ec2_tag_stopper.function_name
  }
}
```

---

## Cost Impact

Estimated monthly cost increase:
- KMS key: ~$1/month
- CloudWatch Logs (30-day retention): ~$0.50/month
- DLQ SQS queue: ~$0.40/month
- X-Ray tracing: ~$0.50/month

**Total**: ~$2.40/month additional cost

---

## Rollback Plan

For each change:
1. Tag current Terraform state before applying
2. Keep previous Lambda version available
3. Document rollback commands
4. Test rollback procedure in staging

```bash
# Rollback example
terraform state pull > backup.tfstate
terraform apply -target=aws_lambda_function.ec2_tag_stopper -var="lambda_version=previous"
```

---

## Success Criteria

- ✅ All security scans pass in CI/CD
- ✅ Lambda function operates correctly with new configurations
- ✅ IAM policies follow least-privilege principle
- ✅ All infrastructure encrypted at rest
- ✅ Comprehensive logging and monitoring in place
- ✅ Documentation updated with security practices

---

## Next Steps

1. Review this plan with team/stakeholders
2. Schedule implementation windows
3. Set up staging environment for testing
4. Begin Phase 1 implementation
5. Monitor and validate each change
6. Document lessons learned

---

**Plan Status**: ✅ Ready for Review and Approval  
**Last Updated**: March 23, 2026
