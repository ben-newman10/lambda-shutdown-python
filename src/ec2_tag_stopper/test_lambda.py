import os
from unittest.mock import MagicMock, patch

import pytest

from ec2_handler import stop_ec2_instances_with_tag


@patch("ec2_handler._get_ec2_client")
def test_stop_ec2_instances_with_tag_no_env_vars(mock_get_client):
    with patch.dict(os.environ, {}, clear=True):
        with patch("ec2_handler.logger") as mock_logger:
            result = stop_ec2_instances_with_tag({}, {})

            mock_logger.error.assert_called_with(
                "Environment variables TAG_KEY and TAG_VALUE must be set."
            )
            assert result["stopped_instances"] == []
            assert "error" in result


@patch("ec2_handler._get_ec2_client")
def test_stop_ec2_instances_with_tag_no_instances(mock_get_client):
    mock_ec2 = MagicMock()
    mock_get_client.return_value = mock_ec2
    env_vars = {"TAG_KEY": "Environment", "TAG_VALUE": "Test"}

    with patch.dict(os.environ, env_vars):
        mock_paginator = MagicMock()
        mock_ec2.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = iter([{"Reservations": []}])

        with patch("ec2_handler.logger") as mock_logger:
            result = stop_ec2_instances_with_tag({}, {})

            mock_paginator.paginate.assert_called_with(
                Filters=[
                    {"Name": "tag:Environment", "Values": ["Test"]},
                    {"Name": "instance-state-name", "Values": ["running"]},
                ]
            )
            mock_logger.info.assert_called_with(
                "No running EC2 instances found with '%s=%s'.",
                "Environment",
                "Test",
            )
            assert result == {"stopped_instances": []}


@patch("ec2_handler._get_ec2_client")
def test_stop_ec2_instances_with_tag_instances_found(mock_get_client):
    mock_ec2 = MagicMock()
    mock_get_client.return_value = mock_ec2
    env_vars = {"TAG_KEY": "Environment", "TAG_VALUE": "Test"}

    with patch.dict(os.environ, env_vars):
        mock_paginator = MagicMock()
        mock_ec2.get_paginator.return_value = mock_paginator

        mock_paginator.paginate.return_value = iter(
            [
                {"Reservations": [{"Instances": [{"InstanceId": "i-1"}]}]},
                {"Reservations": [{"Instances": [{"InstanceId": "i-2"}]}]},
            ]
        )

        with patch("ec2_handler.logger") as mock_logger:
            result = stop_ec2_instances_with_tag({}, {})

            mock_ec2.stop_instances.assert_called_with(
                InstanceIds=["i-1", "i-2"]
            )
            mock_logger.info.assert_called_with(
                "Stopping %d EC2 instances with '%s=%s'. IDs: %s",
                2,
                "Environment",
                "Test",
                ["i-1", "i-2"],
            )
            assert result == {"stopped_instances": ["i-1", "i-2"]}


@patch("ec2_handler._get_ec2_client")
def test_stop_ec2_instances_with_tag_exception_handling(mock_get_client):
    mock_ec2 = MagicMock()
    mock_get_client.return_value = mock_ec2
    env_vars = {"TAG_KEY": "Environment", "TAG_VALUE": "Test"}

    with patch.dict(os.environ, env_vars):
        mock_ec2.get_paginator.side_effect = Exception("Test exception")

        with patch("ec2_handler.logger") as mock_logger:
            with pytest.raises(Exception, match="Test exception"):
                stop_ec2_instances_with_tag({}, {})

            mock_logger.exception.assert_called_with(
                "An error occurred while stopping EC2 instances"
            )
