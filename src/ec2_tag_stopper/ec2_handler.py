from __future__ import annotations

import logging
import os
from typing import Any

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_ec2_client = None


def _get_ec2_client():
    """Return a lazily-initialised EC2 client.

    The client is created once and reused across Lambda invocations (module
    scope) but deferred until first call so that import-time failures (e.g.
    missing region configuration) are avoided.
    """
    global _ec2_client
    if _ec2_client is None:
        _ec2_client = boto3.client("ec2")
    return _ec2_client


def stop_ec2_instances_with_tag(
    event: dict[str, Any],
    context: Any,
) -> dict[str, Any]:
    """Stop all running EC2 instances that match a given tag key/value pair.

    The tag key and value are read from the TAG_KEY and TAG_VALUE environment
    variables respectively.
    """
    tag_key = os.environ.get("TAG_KEY")
    tag_value = os.environ.get("TAG_VALUE")

    if not tag_key or not tag_value:
        logger.error("Environment variables TAG_KEY and TAG_VALUE must be set.")
        return {"stopped_instances": [], "error": "TAG_KEY and TAG_VALUE must be set"}

    try:
        ec2 = _get_ec2_client()
        paginator = ec2.get_paginator("describe_instances")
        page_iterator = paginator.paginate(
            Filters=[
                {"Name": f"tag:{tag_key}", "Values": [tag_value]},
                {
                    "Name": "instance-state-name",
                    "Values": ["running"],
                },
            ],
        )

        instances_to_stop: list[str] = []
        for page in page_iterator:
            for reservation in page["Reservations"]:
                for instance in reservation["Instances"]:
                    instances_to_stop.append(instance["InstanceId"])

        if instances_to_stop:
            ec2.stop_instances(InstanceIds=instances_to_stop)
            logger.info(
                "Stopping %d EC2 instances with '%s=%s'. IDs: %s",
                len(instances_to_stop),
                tag_key,
                tag_value,
                instances_to_stop,
            )
        else:
            logger.info(
                "No running EC2 instances found with '%s=%s'.",
                tag_key,
                tag_value,
            )

        return {"stopped_instances": instances_to_stop}

    except Exception:
        logger.exception("An error occurred while stopping EC2 instances")
        raise
