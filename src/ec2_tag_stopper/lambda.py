import boto3

ec2 = boto3.client('ec2')

def stop_ec2_instances_with_tag(tag_key, tag_value):
    """
    Stops EC2 instances based on a specific tag key and value.
    
    Args:
        tag_key (str): The key of the tag to look for.
        tag_value (str): The value of the tag to look for in the specified key.
        
    Returns:
        None
    """

    try:
        # Filter EC2 instances based on tags
        response = ec2.describe_instances()
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                for tag in instance['Tags']:
                    if tag['Key'] == tag_key and tag['Value'] == tag_value:
                        instances.append(instance['InstanceId'])
        
        # Stop the identified instances
        ec2.stop_instances(InstanceIds=instances)
        print(f"EC2 instances with '{tag_key}={tag_value}' stopped.")
    
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
stop_ec2_instances_with_tag('Rowden', 'rowden-example')