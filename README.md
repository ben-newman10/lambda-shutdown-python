# EC2 Tag Stopper Lambda

## Overview

EC2 Tag Stopper Lambda is a project designed to automate the stopping of AWS EC2 instances based on specific tag keys and values. This project leverages AWS Lambda, Terraform, and the AWS SDK for Python (Boto3) to identify and shut down EC2 instances that match pre-defined tags. It's particularly useful for managing costs by ensuring unnecessary instances are stopped automatically at a scheduled time.

## Components

- **AWS Lambda Function**: The core component that performs the action of stopping EC2 instances. It uses Boto3 to interact with AWS and is designed to be triggered on a schedule via AWS CloudWatch Events.

- **Terraform Configuration**: Automates the infrastructure setup needed for this Lambda function. This includes IAM roles and policies, the Lambda function itself, and CloudWatch event rules for scheduling.

- **GitHub Actions Workflow**: Deploys the Terraform configurations when changes are pushed to the main branch, ensuring continuous deployment and updates.

## How It Works

1. **Tag Specification**: You define the tag `Key` and `Value` that identifies which EC2 instances should be stopped. These are set as environment variables in the Lambda function.

2. **Terraform Setup**: The `main.tf` file contains resources like IAM Roles and Policies needed for Lambda execution, and manages the Lambda function's configuration such as its handler and runtime. It also creates CloudWatch rules for scheduled execution.

3. **Lambda Execution**: The Lambda function checks EC2 instances for the specified tags, and triggers the `stop_instances` API call for those that match. This function is executed daily at 7 PM UTC as per the configured CloudWatch schedule.

## Prerequisites

Before using this project, ensure you have:

- An AWS account with the necessary IAM credentials.
- Terraform installed and configured in your environment.
- AWS CLI configured with appropriate permissions to create resources.
- Python 3.12 or later installed (to match the Lambda runtime).

## Deployment

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:ben-newman10/lambda-shutdown-python.git
   cd lambda-shutdown-python
   ```

2. **Configure AWS Credentials**: Make sure your local environment or CI/CD pipeline has AWS credentials configured with permissions to deploy Terraform resources.

3. **Configure Backend**:
   This project uses an S3 backend for Terraform state. You must provide the configuration dynamically or via a file. Copy the example file and fill in your details:
   ```bash
   cp src/terraform/backend.conf.example src/terraform/backend.conf
   # Edit src/terraform/backend.conf with your bucket details
   ```

4. **Deploy Locally**:
   Run Terraform to apply the configuration, passing the backend config:
   ```bash
   cd src/terraform
   terraform init -backend-config=backend.conf
   terraform apply -auto-approve
   ```

4. **Deploy via GitHub Actions**: Push changes to the `main` branch to trigger the `deploy-terraform.yml` workflow, which will automatically apply Terraform configurations.

## Configuration

- **Terraform Variables**: You can adjust the default tag key and value by modifying the `variables.tf` or setting them in a `terraform.tfvars` file.
  ```hcl
  tag_key = "YourTagKey"
  tag_value = "YourTagValue"
  ```

- **AWS Region**: Ensure the `region` variable in `terraform.tfvars` matches the region of your EC2 instances.


## Security

This project implements comprehensive security best practices to protect your AWS infrastructure:

### Infrastructure Security

- **Least-Privilege IAM Policies**: Lambda function has minimal permissions required, with resource-level restrictions and tag-based conditions
- **Encryption at Rest**: 
  - Lambda environment variables encrypted with KMS
  - CloudWatch Logs encrypted with KMS
  - Terraform state encrypted in S3
  - Dead Letter Queue encrypted with KMS
- **Encryption in Transit**: All AWS API calls use TLS 1.2+
- **KMS Key Rotation**: Automatic key rotation enabled for all KMS keys

### Lambda Security Features

- **Timeout Limits**: 60-second timeout to prevent runaway executions
- **Memory Limits**: 256 MB memory allocation
- **Concurrency Limits**: Reserved concurrent execution set to 1
- **Dead Letter Queue**: Failed invocations sent to SQS DLQ for investigation
- **X-Ray Tracing**: Active tracing enabled for performance monitoring and debugging

### Monitoring & Logging

- **CloudWatch Logs**: All Lambda executions logged with 30-day retention
- **Structured Logging**: JSON-formatted logs for easy parsing and analysis
- **Error Tracking**: Comprehensive error handling with detailed error messages
- **X-Ray Tracing**: Distributed tracing for performance analysis

### Input Validation

- **Tag Validation**: All tag keys and values validated against AWS constraints
- **Length Checks**: Enforces AWS tag length limits (128 chars for keys, 256 for values)
- **Character Validation**: Only allows valid AWS tag characters
- **Sanitization**: Input sanitization prevents injection attacks

### CI/CD Security

- **Automated Security Scanning**: 
  - Trivy for vulnerability scanning
  - Checkov for Terraform security analysis
  - Safety for Python dependency vulnerabilities
  - Bandit for Python code security issues
- **Dependency Updates**: Regular automated dependency updates
- **GitHub Security Alerts**: Enabled for vulnerability notifications

### Secrets Management

- **No Hardcoded Secrets**: All sensitive values stored in AWS Secrets Manager or environment variables
- **IAM Roles**: Uses IAM roles instead of access keys where possible
- **GitHub Secrets**: CI/CD credentials stored securely in GitHub Secrets

### Network Security

- **VPC Isolation**: Lambda can be deployed in VPC for additional isolation (optional)
- **Security Groups**: Configurable security groups for VPC deployments
- **Private Subnets**: Recommended deployment in private subnets

### Compliance & Auditing

- **CloudTrail Integration**: All API calls logged to CloudTrail
- **Resource Tagging**: All resources tagged for cost allocation and compliance
- **State Locking**: DynamoDB state locking prevents concurrent modifications
- **Versioning**: S3 state versioning enabled for rollback capability

### Security Best Practices

1. **Regular Updates**: Keep Terraform, Python, and dependencies up to date
2. **Least Privilege**: Grant only necessary permissions to IAM roles
3. **Encryption**: Enable encryption for all data at rest and in transit
4. **Monitoring**: Set up CloudWatch alarms for security events
5. **Audit Logs**: Regularly review CloudTrail and CloudWatch logs
6. **Backup**: Maintain backups of Terraform state and configurations
7. **MFA**: Enable MFA for AWS console access and critical operations
8. **Review**: Conduct regular security reviews and penetration testing

### Incident Response

If you suspect a security incident:

1. **Isolate**: Immediately disable the Lambda function if compromised
2. **Investigate**: Review CloudWatch Logs and CloudTrail for suspicious activity
3. **Rotate**: Rotate all credentials and KMS keys
4. **Patch**: Apply security patches and redeploy
5. **Document**: Document the incident and lessons learned

### Security Contacts

For security issues, please contact the repository maintainers privately before public disclosure.

### Security Updates

Check the [SECURITY_AUDIT_PLAN.md](SECURITY_AUDIT_PLAN.md) for the latest security audit results and planned improvements.



## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Contributing

We welcome contributions to improve this project! Please submit pull requests or issues for review.

---

By setting up this project, you'll have an automated system to manage the state of your EC2 instances based on specific tags, helping streamline your AWS cost management efforts.