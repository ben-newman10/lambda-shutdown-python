Lambda Shutdown Python
==========================

A simple Python script that demonstrates how to stop a AWS Lambda function from running using the AWS SDK.
A simple Python script that demonstrates how to stop AWS Lambda functions using the AWS SDK, although it was initially intended for EC2 instances.

Table of Contents
-----------------

* [About](#about)
* [Overview](#overview)
* [Components](#components)
* [How It Works](#how-it-works)
* [Prerequisites](#prerequisites)
* [Usage](#usage)
* [Deployment](#deployment)
* [Configuration](#configuration)
* [License](#license)
* [Contributing](#contributing)

## About
## Overview

This repository contains a Python script that uses the AWS SDK (Boto3) to stop an AWS Lambda function from running. This is useful for shutting down a Lambda function programmatically, for example as part of a CI/CD pipeline.
Lambda Shutdown Python is a project designed to automate the stopping of AWS Lambda functions based on specific criteria. This project leverages AWS Lambda, Terraform, and the AWS SDK for Python (Boto3) to identify and handle AWS resources. It is particularly useful for managing costs by ensuring unnecessary Lambda functions are deactivated automatically.

## Prerequisites
## Components

Before you can run this code, you'll need:
- **AWS Lambda Function**: The core component that can be adapted to perform actions like stopping or scheduling AWS resources. It uses Boto3 to interact with AWS and can be scheduled via CloudWatch Events.

* An AWS account with IAM credentials
* The `boto3` library installed (`pip install boto3`
* Your AWS region set in your Boto3 configuration (see below)
- **Terraform Configuration**: Automates the infrastructure setup needed for this process. This includes IAM roles and policies, and setting up CloudWatch event rules for scheduling.

## Usage
- **GitHub Actions Workflow**: Manages the deployment of Terraform configurations when changes are committed, facilitating continuous deployment and updates.

To use this script, follow these steps:
## How It Works

1. Install the required dependencies: `pip install -r requirements.txt`
2. Set your AWS region using one of the following methods:
    * Set the `AWS_REGION` environment variable
    * Add the following to your Boto3 configuration file (`~/.aws/config`): `[default]
region = YOUR_REGION`
3. Replace `YOUR_LAMBDA_FUNCTION_NAME` with the name of the Lambda function you want to stop
1. **Specification**: Define criteria for AWS resources that require action. This is set as configuration in the script.

Run the script using: `python lambda_shutdown.py`
2. **Terraform Setup**: The `main.tf` file contains resources like IAM Roles and Policies needed for execution, and manages configuration such as handler and runtime. It creates a CloudWatch rule for scheduled execution.

## Configuration
3. **Lambda Execution**: The Lambda function executes actions based on the defined criteria. This function is scheduled at specific intervals as per the CloudWatch configuration.
## Prerequisites

The script uses the following variables:
Before using this project, ensure you have:
- An AWS account with appropriate IAM credentials.
- Terraform installed and configured.
- AWS CLI configured with permissions to create resources.

* `AWS_ACCESS_KEY_ID`: Your AWS access key ID
* `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key
* `YOUR_LAMBDA_FUNCTION_NAME`: The name of the Lambda function to stop
* `AWS_REGION`: The region where your Lambda function is running
## Deployment

You can set these variables using environment variables or by adding them to your Boto3 configuration file.

**Note**: This script assumes that you have already configured your AWS credentials and region in your local environment. If you're using a CI/CD pipeline, make sure to configure the necessary credentials and region for the pipeline as well.
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your/repository.git
   cd repository
