"""AWS client initialization and configuration."""
import os
import boto3
from typing import Optional
from functools import lru_cache


@lru_cache(maxsize=1)
def get_cloudwatch_client(region: Optional[str] = None):
    """Get CloudWatch client."""
    return boto3.client('cloudwatch', region_name=region or os.environ.get('AWS_REGION'))


@lru_cache(maxsize=1)
def get_ec2_client(region: Optional[str] = None):
    """Get EC2 client."""
    return boto3.client('ec2', region_name=region or os.environ.get('AWS_REGION'))


@lru_cache(maxsize=1)
def get_ssm_client(region: Optional[str] = None):
    """Get SSM client."""
    return boto3.client('ssm', region_name=region or os.environ.get('AWS_REGION'))


@lru_cache(maxsize=1)
def get_dynamodb_client(region: Optional[str] = None):
    """Get DynamoDB client."""
    return boto3.client('dynamodb', region_name=region or os.environ.get('AWS_REGION'))


@lru_cache(maxsize=1)
def get_dynamodb_resource(region: Optional[str] = None):
    """Get DynamoDB resource."""
    return boto3.resource('dynamodb', region_name=region or os.environ.get('AWS_REGION'))


@lru_cache(maxsize=1)
def get_sns_client(region: Optional[str] = None):
    """Get SNS client."""
    return boto3.client('sns', region_name=region or os.environ.get('AWS_REGION'))


@lru_cache(maxsize=1)
def get_elbv2_client(region: Optional[str] = None):
    """Get ELBv2 client."""
    return boto3.client('elbv2', region_name=region or os.environ.get('AWS_REGION'))


@lru_cache(maxsize=1)
def get_logs_client(region: Optional[str] = None):
    """Get CloudWatch Logs client."""
    return boto3.client('logs', region_name=region or os.environ.get('AWS_REGION'))

