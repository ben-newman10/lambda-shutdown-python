import boto3
import os
import logging
import re
from botocore.exceptions import ClientError, BotoCoreError

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ec2 = boto3.client('ec2')

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

    # Validate tag format
    is_valid, error = validate_tag_input(tag_key, tag_value)
    if not is_valid:
        logger.error(f"Invalid tag input: {error}")
        return {
            'statusCode': 400,
            'body': f"Invalid input: {error}"
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
