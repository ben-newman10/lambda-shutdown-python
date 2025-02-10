Lambda Shutdown Python
==========================

A simple Python script that demonstrates how to stop a AWS Lambda function from running using the AWS SDK.

Table of Contents
-----------------

* [About](#about)
* [Prerequisites](#prerequisites)
* [Usage](#usage)
* [Configuration](#configuration)

## About

This repository contains a Python script that uses the AWS SDK (Boto3) to stop an AWS Lambda function from running. This is useful for shutting down a Lambda function programmatically, for example as part of a CI/CD pipeline.

## Prerequisites

Before you can run this code, you'll need:

* An AWS account with IAM credentials
* The `boto3` library installed (`pip install boto3`
* Your AWS region set in your Boto3 configuration (see below)

## Usage

To use this script, follow these steps:

1. Install the required dependencies: `pip install -r requirements.txt`
2. Set your AWS region using one of the following methods:
    * Set the `AWS_REGION` environment variable
    * Add the following to your Boto3 configuration file (`~/.aws/config`): `[default]
region = YOUR_REGION`
3. Replace `YOUR_LAMBDA_FUNCTION_NAME` with the name of the Lambda function you want to stop

Run the script using: `python lambda_shutdown.py`

## Configuration

The script uses the following variables:

* `AWS_ACCESS_KEY_ID`: Your AWS access key ID
* `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key
* `YOUR_LAMBDA_FUNCTION_NAME`: The name of the Lambda function to stop
* `AWS_REGION`: The region where your Lambda function is running

You can set these variables using environment variables or by adding them to your Boto3 configuration file.

**Note**: This script assumes that you have already configured your AWS credentials and region in your local environment. If you're using a CI/CD pipeline, make sure to configure the necessary credentials and region for the pipeline as well.