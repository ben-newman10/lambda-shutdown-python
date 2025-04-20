import boto3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

ec2 = boto3.client('ec2')

def stop_ec2_instances_with_tag(event, context):
    tag_key = os.environ.get('TAG_KEY')
    tag_value = os.environ.get('TAG_VALUE')

    if not tag_key or not tag_value:
        logger.error("Environment variables TAG_KEY and TAG_VALUE must be set.")
        return

    try:
        # Filter EC2 instances based on tags
        response = ec2.describe_instances()
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                for tag in instance.get('Tags', []):
                    if tag['Key'] == tag_key and tag['Value'] == tag_value:
                        instances.append(instance['InstanceId'])
        
        # Stop the identified instances
        if instances:
            ec2.stop_instances(InstanceIds=instances)
            logger.info(f"EC2 instances with '{tag_key}={tag_value}' stopped.")
        else:
            logger.info(f"No EC2 instances found with '{tag_key}={tag_value}'.")
    
    except Exception as e:
        logger.exception(f"An error occurred: {e}")