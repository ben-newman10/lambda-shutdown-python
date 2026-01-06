import pytest
from unittest.mock import patch, MagicMock
import os
from ec2_handler import stop_ec2_instances_with_tag

@patch('ec2_handler.ec2')
def test_stop_ec2_instances_with_tag_no_env_vars(mock_ec2):
    # Ensure environment variables are not set using patch.dict to clear them
    with patch.dict(os.environ, {}, clear=True):
        # Mock logger
        with patch('ec2_handler.logger') as mock_logger:
            stop_ec2_instances_with_tag({}, {})
            mock_logger.error.assert_called_with("Environment variables TAG_KEY and TAG_VALUE must be set.")

@patch('ec2_handler.ec2')
def test_stop_ec2_instances_with_tag_no_instances(mock_ec2):
    env_vars = {'TAG_KEY': 'Environment', 'TAG_VALUE': 'Test'}
    
    with patch.dict(os.environ, env_vars):
        # Mock Paginator
        mock_paginator = MagicMock()
        mock_ec2.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = iter([{'Reservations': []}])

        # Mock logger
        with patch('ec2_handler.logger') as mock_logger:
            stop_ec2_instances_with_tag({}, {})
            
            # Verify filter call
            mock_paginator.paginate.assert_called_with(Filters=[
                {'Name': 'tag:Environment', 'Values': ['Test']},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ])
            mock_logger.info.assert_called_with("No running EC2 instances found with 'Environment=Test'.")

@patch('ec2_handler.ec2')
def test_stop_ec2_instances_with_tag_instances_found(mock_ec2):
    env_vars = {'TAG_KEY': 'Environment', 'TAG_VALUE': 'Test'}
    
    with patch.dict(os.environ, env_vars):
        # Mock Paginator
        mock_paginator = MagicMock()
        mock_ec2.get_paginator.return_value = mock_paginator
        
        # Simulate two pages of results
        mock_paginator.paginate.return_value = iter([
            {
                'Reservations': [
                    {
                        'Instances': [{'InstanceId': 'i-1'}]
                    }
                ]
            },
            {
                'Reservations': [
                    {
                        'Instances': [{'InstanceId': 'i-2'}]
                    }
                ]
            }
        ])

        # Mock logger
        with patch('ec2_handler.logger') as mock_logger:
            stop_ec2_instances_with_tag({}, {})
            
            mock_ec2.stop_instances.assert_called_with(InstanceIds=['i-1', 'i-2'])
            # Verify log message content partially to avoid strict string matching issues with list order if any
            args, _ = mock_logger.info.call_args
            assert "Stopping 2 EC2 instances" in args[0]

@patch('ec2_handler.ec2')
def test_stop_ec2_instances_with_tag_exception_handling(mock_ec2):
    env_vars = {'TAG_KEY': 'Environment', 'TAG_VALUE': 'Test'}
    
    with patch.dict(os.environ, env_vars):
        # Mock EC2 client to raise an exception
        mock_ec2.get_paginator.side_effect = Exception("Test exception")

        # Mock logger
        with patch('ec2_handler.logger') as mock_logger:
            stop_ec2_instances_with_tag({}, {})
            mock_logger.exception.assert_called_with("An error occurred: Test exception")