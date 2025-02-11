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

## Deployment

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:ben-newman10/lambda-shutdown-python.git
   cd lambda-shutdown-python
   ```

2. **Configure AWS Credentials**: Make sure your local environment or CI/CD pipeline has AWS credentials configured with permissions to deploy Terraform resources.

3. **Deploy Locally**:
   Run Terraform to apply the configuration:
   ```bash
   terraform init
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

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Contributing

We welcome contributions to improve this project! Please submit pull requests or issues for review.

---

By setting up this project, you'll have an automated system to manage the state of your EC2 instances based on specific tags, helping streamline your AWS cost management efforts.