"""Real-time health monitoring Lambda function."""
import json
import os
import sys
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import StructuredLogger
from utils.config import Config
from utils.aws_client import get_ec2_client
from utils.dynamodb_helpers import save_recovery_event, get_instance_config, get_recovery_history

logger = StructuredLogger(__name__)


def check_instance_status(instance_id: str) -> Dict[str, Any]:
    """Check EC2 instance status checks."""
    try:
        ec2 = get_ec2_client()
        response = ec2.describe_instance_status(InstanceIds=[instance_id])
        
        if not response.get('InstanceStatuses'):
            return {
                'healthy': False,
                'system_status': 'unknown',
                'instance_status': 'unknown',
                'reason': 'Instance not found or not running'
            }
        
        status = response['InstanceStatuses'][0]
        system_status = status.get('SystemStatus', {}).get('Status', 'unknown')
        instance_status = status.get('InstanceStatus', {}).get('Status', 'unknown')
        
        healthy = (system_status == 'ok' and instance_status == 'ok')
        
        return {
            'healthy': healthy,
            'system_status': system_status,
            'instance_status': instance_status,
            'system_status_details': status.get('SystemStatus', {}),
            'instance_status_details': status.get('InstanceStatus', {})
        }
    except Exception as e:
        logger.error(f"Failed to check instance status: {e}", error=e, instance_id=instance_id)
        return {
            'healthy': False,
            'error': str(e)
        }


def check_app_health(instance_id: str, health_endpoint: str = None) -> Dict[str, Any]:
    """Check application-level health endpoint."""
    # This would typically use SSM RunCommand or direct HTTP check
    # For now, return placeholder
    if not health_endpoint:
        return {'checked': False, 'reason': 'No health endpoint configured'}
    
    # In production, this would:
    # 1. Use SSM RunCommand to curl the endpoint
    # 2. Or use Lambda to HTTP check if instance is publicly accessible
    # 3. Parse response and return health status
    
    return {'checked': False, 'reason': 'Not implemented'}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for health monitoring."""
    try:
        logger.info("Health monitoring triggered", event_source=event.get('source'))
        
        # Extract instance ID from event
        instance_id = None
        
        if event.get('source') == 'aws.ec2':
            # EventBridge EC2 event
            instance_id = event.get('detail', {}).get('instance-id')
        elif event.get('detail-type') == 'EC2 Instance State-change Notification':
            instance_id = event.get('detail', {}).get('instance-id')
        elif 'instance_id' in event:
            instance_id = event['instance_id']
        elif 'instance-id' in event.get('detail', {}):
            instance_id = event['detail']['instance-id']
        
        if not instance_id:
            logger.warning("No instance ID found in event", event=event)
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No instance ID in event'})
            }
        
        logger.info(f"Checking health for {instance_id}", instance_id=instance_id)
        
        # Get instance config
        config = get_instance_config(instance_id)
        if config and config.get('monitoring_enabled', True) is False:
            logger.info(f"Monitoring disabled for {instance_id}")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Monitoring disabled'})
            }
        
        # Check instance status
        status_result = check_instance_status(instance_id)
        
        if not status_result['healthy']:
            logger.warning(
                f"Instance {instance_id} is unhealthy",
                instance_id=instance_id,
                system_status=status_result.get('system_status'),
                instance_status=status_result.get('instance_status')
            )
            
            # Save recovery event
            save_recovery_event(
                instance_id=instance_id,
                event_type='health_check',
                status='failed',
                action_taken='detected',
                metadata={
                    'system_status': status_result.get('system_status'),
                    'instance_status': status_result.get('instance_status'),
                    'details': status_result
                }
            )
            
            # Check recovery history to avoid repeated triggers
            history = get_recovery_history(instance_id, limit=5)
            recent_failures = [
                h for h in history
                if h.get('event_type') == 'health_check' and
                h.get('status') == 'failed'
            ]
            
            # Only trigger recovery if not recently attempted
            if len(recent_failures) < 3:  # Allow up to 3 attempts
                # Trigger recovery Lambda via EventBridge
                logger.warning(
                    f"Triggering recovery for {instance_id}",
                    instance_id=instance_id
                )
                # EventBridge rule will trigger auto_recovery Lambda
        
        # Check app health if configured
        health_endpoint = config.get('health_endpoint') if config else None
        if health_endpoint:
            app_health = check_app_health(instance_id, health_endpoint)
            if not app_health.get('healthy', True):
                logger.warning(
                    f"App health check failed for {instance_id}",
                    instance_id=instance_id
                )
                save_recovery_event(
                    instance_id=instance_id,
                    event_type='app_failure',
                    status='failed',
                    action_taken='detected',
                    metadata={'health_check_result': app_health}
                )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'instance_id': instance_id,
                'healthy': status_result['healthy'],
                'status': status_result
            })
        }
    
    except Exception as e:
        logger.error(f"Fatal error in health monitoring: {e}", error=e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

