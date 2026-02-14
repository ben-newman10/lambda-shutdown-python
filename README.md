# EC2 Tag Stopper Lambda

## Overview

EC2 Tag Stopper Lambda automates stopping AWS EC2 instances based on tag key/value pairs. It runs on a daily schedule via CloudWatch Events and is deployed with Terraform.

## Components

- **AWS Lambda Function** (`src/ec2_tag_stopper/ec2_handler.py`) -- Identifies and stops running EC2 instances that match the configured tag. Uses boto3 with pagination for large fleets.

- **Terraform Configuration** (`src/terraform/`) -- Provisions the Lambda function, IAM roles/policies, and CloudWatch event schedule. Uses the AWS provider `~> 5.0` and requires Terraform `>= 1.6`.

- **GitHub Actions Workflow** (`.github/workflows/deploy-terraform.yml`) -- Runs tests on push to `main`, then deploys the Terraform configuration. Uses `hashicorp/setup-terraform@v3` with Terraform 1.9.8.

## How It Works

1. **Tag Specification** -- Define the tag `Key` and `Value` via Terraform variables. These are passed to the Lambda as `TAG_KEY` and `TAG_VALUE` environment variables.

2. **Scheduled Execution** -- CloudWatch Events triggers the Lambda daily at 7 PM UTC.

3. **Instance Discovery & Shutdown** -- The Lambda uses server-side filtering with pagination to find running instances matching the tag, then calls `stop_instances` on them.

## Prerequisites

- An AWS account with IAM credentials that can create Lambda functions, IAM roles/policies, and CloudWatch rules.
- [Terraform](https://www.terraform.io/) >= 1.6 installed locally (for manual deploys).
- Python 3.12+ (to match the Lambda runtime).

## Development

Install development dependencies and run the test suite:

```bash
pip install -r requirements-dev.txt
pytest src/
```

## Deployment

### Via GitHub Actions (recommended)

Push to the `main` branch. The workflow will:

1. Run the test suite.
2. Deploy the Terraform configuration.

AWS credentials must be stored as repository secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).

### Manual

```bash
# Configure the S3 backend
cp src/terraform/backend.conf.example src/terraform/backend.conf
# Edit src/terraform/backend.conf with your bucket details

# Deploy
cd src/terraform
terraform init -backend-config=backend.conf
terraform apply
```

## Configuration

| Variable    | Description                             | Default           |
| ----------- | --------------------------------------- | ----------------- |
| `region`    | AWS region for the Lambda and EC2 scope | *(required)*      |
| `tag_key`   | Tag key to match EC2 instances          | `Rowden`          |
| `tag_value` | Tag value to match EC2 instances        | `rowden-example`  |

Set these in `src/terraform/terraform.tfvars` or pass them via `-var` flags.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.
