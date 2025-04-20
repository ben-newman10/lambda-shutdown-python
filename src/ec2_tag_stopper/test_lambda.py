import pytest
from unittest.mock import patch, MagicMock
import os
from ec2_handler import stop_ec2_instances_with_tag

@patch('ec2_handler.ec2')
def test_stop_ec2_instances_with_tag_no_env_vars(mock_ec2):
    # Ensure environment variables are not set
    if 'TAG_KEY' in os.environ:
        del os.environ['TAG_KEY']
    if 'TAG_VALUE' in os.environ:
        del os.environ['TAG_VALUE']

    # Mock logger
    with patch('ec2_handler.logger') as mock_logger:
        stop_ec2_instances_with_tag({}, {})
        mock_logger.error.assert_called_with("Environment variables TAG_KEY and TAG_VALUE must be set.")

@patch('ec2_handler.ec2')
def test_stop_ec2_instances_with_tag_no_instances(mock_ec2):
    os.environ['TAG_KEY'] = 'Environment'
    os.environ['TAG_VALUE'] = 'Test'

    # Mock EC2 client and describe_instances response
    mock_ec2.describe_instances.return_value = {'Reservations': []}

    # Mock logger
    with patch('ec2_handler.logger') as mock_logger:
        stop_ec2_instances_with_tag({}, {})
        mock_logger.info.assert_called_with("No EC2 instances found with 'Environment=Test'.")

@patch('ec2_handler.ec2')
def test_stop_ec2_instances_with_tag_instances_found(mock_ec2):
    os.environ['TAG_KEY'] = 'Environment'
    os.environ['TAG_VALUE'] = 'Test'

    # Mock EC2 client and describe_instances response
    mock_ec2.describe_instances.return_value = {
        'Reservations': [
            {
                'Instances': [
                    {
                        'InstanceId': 'i-1234567890abcdef0',
                        'Tags': [{'Key': 'Environment', 'Value': 'Test'}]
                    }
                ]
            }
        ]
    }

    # Mock logger
    with patch('ec2_handler.logger') as mock_logger:
        stop_ec2_instances_with_tag({}, {})
        mock_ec2.stop_instances.assert_called_with(InstanceIds=['i-1234567890abcdef0'])
        mock_logger.info.assert_called_with("EC2 instances with 'Environment=Test' stopped.")

@patch('ec2_handler.ec2')
def test_stop_ec2_instances_with_tag_exception_handling(mock_ec2):
    os.environ['TAG_KEY'] = 'Environment'
    os.environ['TAG_VALUE'] = 'Test'

    # Mock EC2 client to raise an exception
    mock_ec2.describe_instances.side_effect = Exception("Test exception")

    # Mock logger
    with patch('ec2_handler.logger') as mock_logger:
        stop_ec2_instances_with_tag({}, {})
        mock_logger.exception.assert_called_with("An error occurred: Test exception")

@patch('ec2_handler.ec2')
def test_stop_ec2_instances_with_tag_partial_env_vars(mock_ec2):
    os.environ['TAG_KEY'] = 'Environment'
    if 'TAG_VALUE' in os.environ:
        del os.environ['TAG_VALUE']

    # Mock logger
    with patch('ec2_handler.logger') as mock_logger:
        stop_ec2_instances_with_tag({}, {})
        mock_logger.error.assert_called_with("Environment variables TAG_KEY and TAG_VALUE must be set.")

@patch('ec2_handler.ec2')
def test_stop_ec2_instances_with_tag_no_tags(mock_ec2):
    os.environ['TAG_KEY'] = 'Environment'
    os.environ['TAG_VALUE'] = 'Test'

    # Mock EC2 client and describe_instances response
    mock_ec2.describe_instances.return_value = {
        'Reservations': [
            {
                'Instances': [
                    {
                        'InstanceId': 'i-1234567890abcdef0',
                        'Tags': []
                    }
                ]
            }
        ]
    }

    # Mock logger
    with patch('ec2_handler.logger') as mock_logger:
        stop_ec2_instances_with_tag({}, {})
        mock_logger.info.assert_called_with("No EC2 instances found with 'Environment=Test'.")