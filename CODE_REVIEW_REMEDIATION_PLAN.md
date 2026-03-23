# Code Review Remediation Plan

**Date**: March 23, 2026  
**Project**: EC2 Tag Stopper Lambda  
**Status**: Ready for Implementation

## Executive Summary

Code review identified **15 issues** across the recent security improvements:
- **1 Critical** (blocking deployment)
- **3 High Priority** (must fix before production)
- **8 Medium Priority** (should fix soon)
- **3 Low Priority** (nice to have)

**Estimated Effort**: 2-3 hours  
**Priority**: CRITICAL - Terraform syntax error blocks deployment

---

## Critical Issues (Must Fix Immediately)

### 1. Terraform Syntax Error - Incomplete Resource Definition 🔴

**File**: `src/terraform/main.tf:47-48`

**Issue**: The `aws_iam_policy.ec2_tag_stopper_policy` resource definition is incomplete. The resource starts at line 47 but is interrupted by the KMS key resource at line 50, leaving it without a closing brace. The actual policy content appears later at lines 119-148.

**Impact**: Terraform will fail to parse the configuration, blocking all deployments.

**Root Cause**: During the security improvements, the policy resource was split incorrectly when inserting the KMS and DLQ resources.

**Fix**:
```hcl
# Lines 47-148 should be restructured as:

# Create an IAM Policy for Lambda function execution (tag stopping)
resource "aws_iam_policy" "ec2_tag_stopper_policy" {
  name        = "ec2-tag-stopper-policy"
  description = "Least-privilege policy for Lambda to stop tagged EC2 instances"

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

# Then KMS, DLQ, and other resources follow...
```

**Verification**:
```bash
cd src/terraform
terraform fmt
terraform validate
```

**Effort**: 15 minutes

---

## High Priority Issues (Fix Before Production)

### 2. Missing KMS Key Policy for CloudWatch Logs 🔴

**File**: `src/terraform/main.tf:51-60`

**Issue**: The KMS key lacks a resource policy granting CloudWatch Logs permission to use it for encryption. Without this, CloudWatch Logs cannot encrypt the Lambda logs.

**Impact**: Lambda function will fail to create logs, or logs won't be encrypted as intended.

**Fix**:
```hcl
resource "aws_kms_key" "lambda_encryption" {
  description             = "KMS key for Lambda function encryption"
  deletion_window_in_days = 7
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
```

**Verification**:
```bash
# After deployment, check CloudWatch Logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/ec2-tag-stopper
```

**Effort**: 30 minutes

---

### 3. Security Scan Failures Masked in CI/CD 🔴

**File**: `.github/workflows/deploy-terraform.yml:49-50`

**Issue**: Security checks use `|| true` which masks failures, allowing vulnerable code to be deployed.

**Impact**: Security vulnerabilities could be deployed to production without detection.

**Fix**:
```yaml
- name: Python Security Check
  continue-on-error: true  # Allow pipeline to continue but mark step as failed
  run: |
    pip install safety bandit
    safety check --file requirements-dev.txt
    bandit -r src/ec2_tag_stopper/ -f json -o bandit-results.json

- name: Upload Bandit results
  if: always()  # Upload even if previous step failed
  uses: actions/upload-artifact@v4
  with:
    name: bandit-results
    path: bandit-results.json
```

**Alternative** (stricter - recommended for production):
```yaml
- name: Python Security Check
  run: |
    pip install safety bandit
    set -e  # Exit on any error
    safety check --file requirements-dev.txt
    bandit -r src/ec2_tag_stopper/ -ll -f json -o bandit-results.json
```

**Effort**: 15 minutes

---

## Medium Priority Issues (Should Fix Soon)

### 4. Test File Incompatible with New Return Values ⚠️

**File**: `src/ec2_tag_stopper/test_lambda.py`

**Issue**: Tests don't verify the new structured return values (statusCode, body, instances) introduced in the Lambda handler refactor.

**Impact**: Tests pass but don't validate the actual API contract, potentially missing bugs.

**Fixes Required**:

**Line 13** - Update error message assertion:
```python
# Old
mock_logger.error.assert_called_with("Environment variables TAG_KEY and TAG_VALUE must be set.")

# New
result = stop_ec2_instances_with_tag({}, {})
mock_logger.error.assert_called_with("Environment variables TAG_KEY and TAG_VALUE must be set")
assert result['statusCode'] == 400
assert result['body'] == "Environment variables TAG_KEY and TAG_VALUE must be set"
```

**Line 34** - Update log message assertion:
```python
# Old
mock_logger.info.assert_called_with("No running EC2 instances found with 'Environment=Test'.")

# New
result = stop_ec2_instances_with_tag({}, {})
mock_logger.info.assert_called_with("No running instances found with tag Environment=Test")
assert result['statusCode'] == 200
assert result['body'] == "No running instances found matching criteria"
```

**Line 70** - Update log message assertion:
```python
# Old
args, _ = mock_logger.info.call_args
assert "Stopping 2 EC2 instances" in args[0]

# New
result = stop_ec2_instances_with_tag({}, {})
# Check for the new log format
assert any("Found 2 instances to stop" in str(call) for call in mock_logger.info.call_args_list)
assert result['statusCode'] == 200
assert "Successfully initiated stop for 2 instances" in result['body']
assert result['instances'] == ['i-1', 'i-2']
```

**Line 83** - Update exception message assertion:
```python
# Old
mock_logger.exception.assert_called_with("An error occurred: Test exception")

# New
result = stop_ec2_instances_with_tag({}, {})
mock_logger.exception.assert_called_with("Unexpected error: Test exception")
assert result['statusCode'] == 500
assert result['body'] == "Internal server error"
```

**Add new test for input validation**:
```python
@patch('ec2_handler.ec2')
def test_stop_ec2_instances_with_invalid_tag_key(mock_ec2):
    env_vars = {'TAG_KEY': 'Invalid@#$%Key', 'TAG_VALUE': 'Test'}
    
    with patch.dict(os.environ, env_vars):
        with patch('ec2_handler.logger') as mock_logger:
            result = stop_ec2_instances_with_tag({}, {})
            
            assert result['statusCode'] == 400
            assert "Invalid input" in result['body']
            mock_logger.error.assert_called()
```

**Effort**: 45 minutes

---

### 5. Missing Newline at End of File ⚠️

**File**: `requirements-dev.txt:4`

**Issue**: File doesn't end with a newline, violating POSIX standards.

**Impact**: Minor - some tools may complain, git diffs may show warnings.

**Fix**:
```txt
iniconfig==2.1.0
packaging==26.0
pluggy==1.5.0
pytest==8.3.5
```
(Ensure there's a newline after pytest==8.3.5)

**Effort**: 1 minute

---

### 6. Magic Numbers in Lambda Handler ⚠️

**File**: `src/ec2_tag_stopper/ec2_handler.py:29,36`

**Issue**: AWS tag length constraints (128, 256) are hardcoded without explanation.

**Impact**: Reduces code maintainability and clarity.

**Fix**:
```python
# Add at module level (after imports)
# AWS Tag Constraints
TAG_KEY_MAX_LENGTH = 128
TAG_VALUE_MAX_LENGTH = 256

def validate_tag_input(tag_key, tag_value):
    """
    Validate tag key and value format according to AWS constraints.
    
    Args:
        tag_key: Tag key to validate
        tag_value: Tag value to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # AWS tag key constraints
    if not tag_key or len(tag_key) > TAG_KEY_MAX_LENGTH:
        return False, f"Tag key must be 1-{TAG_KEY_MAX_LENGTH} characters"
    
    if not re.match(r'^[\w\s\.\-\:\/\=\+\@]*$', tag_key):
        return False, "Tag key contains invalid characters"
    
    # AWS tag value constraints
    if not tag_value or len(tag_value) > TAG_VALUE_MAX_LENGTH:
        return False, f"Tag value must be 1-{TAG_VALUE_MAX_LENGTH} characters"
    
    if not re.match(r'^[\w\s\.\-\:\/\=\+\@]*$', tag_value):
        return False, "Tag value contains invalid characters"
    
    return True, None
```

**Effort**: 10 minutes

---

### 7. Magic Numbers in Terraform Configuration ⚠️

**File**: `src/terraform/main.tf:70,165,166`

**Issue**: Configuration values (14 days, 60 seconds, 256 MB) are hardcoded.

**Impact**: Reduces flexibility and requires code changes to adjust values.

**Fix** - Add to `variables.tf`:
```hcl
variable "dlq_message_retention_days" {
  description = "Number of days to retain messages in the Dead Letter Queue"
  type        = number
  default     = 14
}

variable "lambda_timeout_seconds" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_mb" {
  description = "Lambda function memory allocation in MB"
  type        = number
  default     = 256
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 30
}

variable "kms_deletion_window_days" {
  description = "KMS key deletion window in days"
  type        = number
  default     = 7
}
```

**Update `main.tf`**:
```hcl
resource "aws_sqs_queue" "lambda_dlq" {
  name                      = "ec2-tag-stopper-dlq"
  message_retention_seconds = var.dlq_message_retention_days * 86400  # Convert days to seconds
  # ...
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/ec2-tag-stopper"
  retention_in_days = var.log_retention_days
  # ...
}

resource "aws_lambda_function" "ec2_tag_stopper" {
  # ...
  timeout     = var.lambda_timeout_seconds
  memory_size = var.lambda_memory_mb
  # ...
}

resource "aws_kms_key" "lambda_encryption" {
  description             = "KMS key for Lambda function encryption"
  deletion_window_in_days = var.kms_deletion_window_days
  # ...
}
```

**Effort**: 20 minutes

---

## Low Priority Issues (Nice to Have)

### 8. Documentation for Magic Number ℹ️

**File**: `src/terraform/main.tf:70`

**Issue**: The value 1209600 isn't immediately obvious as 14 days.

**Impact**: Minor readability issue.

**Fix** - Add inline comment:
```hcl
resource "aws_sqs_queue" "lambda_dlq" {
  name                      = "ec2-tag-stopper-dlq"
  message_retention_seconds = 1209600  # 14 days (14 * 24 * 60 * 60)
  # ...
}
```

**Effort**: 2 minutes

---

## Implementation Plan

### Phase 1: Critical Fixes (Immediate - 1 hour)
1. ✅ Fix Terraform syntax error in main.tf
2. ✅ Add KMS key policy for CloudWatch Logs
3. ✅ Fix security scan masking in GitHub Actions

**Deliverable**: Deployable infrastructure

### Phase 2: Test Updates (Next - 1 hour)
4. ✅ Update all test assertions for new return values
5. ✅ Add test for input validation
6. ✅ Run full test suite to verify

**Deliverable**: Passing test suite

### Phase 3: Code Quality (Final - 30 minutes)
7. ✅ Extract magic numbers to constants in Python
8. ✅ Extract magic numbers to variables in Terraform
9. ✅ Fix newline at end of requirements-dev.txt
10. ✅ Add inline documentation

**Deliverable**: Clean, maintainable code

---

## Testing Strategy

### After Phase 1:
```bash
# Validate Terraform
cd src/terraform
terraform fmt
terraform validate
terraform plan

# Test GitHub Actions locally (if using act)
act -j security-scan
```

### After Phase 2:
```bash
# Run Python tests
cd src/ec2_tag_stopper
pytest test_lambda.py -v

# Check coverage
pytest test_lambda.py --cov=ec2_handler --cov-report=term-missing
```

### After Phase 3:
```bash
# Full integration test
terraform plan
pytest test_lambda.py -v
bandit -r src/ec2_tag_stopper/
safety check --file requirements-dev.txt
```

---

## Rollback Plan

If issues arise during implementation:

1. **Terraform Changes**: 
   ```bash
   git checkout HEAD -- src/terraform/main.tf
   terraform plan  # Verify rollback
   ```

2. **Python Changes**:
   ```bash
   git checkout HEAD -- src/ec2_tag_stopper/ec2_handler.py
   pytest test_lambda.py  # Verify tests still pass
   ```

3. **GitHub Actions**:
   ```bash
   git checkout HEAD -- .github/workflows/deploy-terraform.yml
   ```

---

## Success Criteria

- ✅ `terraform validate` passes without errors
- ✅ All tests pass with `pytest test_lambda.py -v`
- ✅ Security scans run and report results (not masked)
- ✅ No magic numbers in critical code paths
- ✅ All files follow POSIX standards (newline at EOF)
- ✅ Code review findings addressed

---

## Risk Assessment

**Low Risk**:
- Magic number extraction (backward compatible)
- Test updates (no production impact)
- Documentation improvements

**Medium Risk**:
- KMS key policy changes (test in staging first)
- Security scan behavior changes (may reveal existing issues)

**High Risk**:
- Terraform syntax fix (critical for deployment)

**Mitigation**: Test all changes in staging environment before production deployment.

---

## Next Steps

1. Review this plan with team
2. Create feature branch: `fix/code-review-issues`
3. Implement Phase 1 (critical fixes)
4. Test and validate
5. Implement Phase 2 (test updates)
6. Implement Phase 3 (code quality)
7. Create pull request with all changes
8. Deploy to staging for validation
9. Deploy to production

---

**Plan Status**: ✅ Ready for Implementation  
**Last Updated**: March 23, 2026  
**Estimated Total Time**: 2-3 hours
