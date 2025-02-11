import boto3
import os

ec2 = boto3.client('ec2')

def stop_ec2_instances_with_tag(event, context):
    tag_key = os.environ['TAG_KEY']
    tag_value = os.environ['TAG_VALUE']
    
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
            print(f"EC2 instances with '{tag_key}={tag_value}' stopped.")
        else:
            print(f"No EC2 instances found with '{tag_key}={tag_value}'.")
    
    except Exception as e:
        print(f"An error occurred: {e}")