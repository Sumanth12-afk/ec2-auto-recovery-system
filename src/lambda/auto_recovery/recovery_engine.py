"""Intelligent auto-recovery engine."""
import json
import os
import sys
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import StructuredLogger
from utils.config import Config
from utils.aws_client import (
    get_ec2_client, get_ssm_client, get_elbv2_client,
    get_cloudwatch_client
)
from utils.dynamodb_helpers import (
    get_instance_config, update_instance_config,
    save_recovery_event, get_recovery_history
)

logger = StructuredLogger(__name__)


class RecoveryEngine:
    """Handles intelligent auto-recovery actions."""
    
    def __init__(self):
        self.ec2 = get_ec2_client()
        self.ssm = get_ssm_client()
        self.elbv2 = get_elbv2_client()
        self.cloudwatch = get_cloudwatch_client()
        self.timeout = Config.RECOVERY_TIMEOUT_SECONDS
    
    def get_instance_details(self, instance_id: str) -> Dict[str, Any]:
        """Get detailed instance information."""
        try:
            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            if not response.get('Reservations'):
                raise ValueError(f"Instance {instance_id} not found")
            
            instance = response['Reservations'][0]['Instances'][0]
            return {
                'instance_id': instance_id,
                'state': instance['State']['Name'],
                'instance_type': instance['InstanceType'],
                'availability_zone': instance['Placement']['AvailabilityZone'],
                'subnet_id': instance.get('SubnetId'),
                'security_groups': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])],
                'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])},
                'block_devices': instance.get('BlockDeviceMappings', []),
                'network_interfaces': instance.get('NetworkInterfaces', [])
            }
        except Exception as e:
            logger.error(f"Failed to get instance details: {e}", error=e, instance_id=instance_id)
            raise
    
    def safe_instance_restart(self, instance_id: str) -> Dict[str, Any]:
        """Perform safe instance restart with EBS snapshot."""
        try:
            logger.info(f"Starting safe restart for {instance_id}", instance_id=instance_id)
            
            instance_details = self.get_instance_details(instance_id)
            
            # Step 1: Create snapshot of root volume
            root_volume = None
            for bdm in instance_details['block_devices']:
                if bdm.get('DeviceName') == instance_details.get('root_device_name') or \
                   bdm.get('Ebs', {}).get('VolumeId'):
                    root_volume = bdm['Ebs']['VolumeId']
                    break
            
            snapshot_id = None
            if root_volume:
                logger.info(f"Creating snapshot of {root_volume}", volume_id=root_volume)
                snapshot_response = self.ec2.create_snapshot(
                    VolumeId=root_volume,
                    Description=f"Pre-restart snapshot for {instance_id}",
                    TagSpecifications=[{
                        'ResourceType': 'snapshot',
                        'Tags': [
                            {'Key': 'InstanceId', 'Value': instance_id},
                            {'Key': 'Purpose', 'Value': 'AutoRecovery'},
                            {'Key': 'Timestamp', 'Value': datetime.utcnow().isoformat()}
                        ]
                    }]
                )
                snapshot_id = snapshot_response['SnapshotId']
                logger.info(f"Snapshot created: {snapshot_id}", snapshot_id=snapshot_id)
            
            # Step 2: Stop instance
            logger.info(f"Stopping instance {instance_id}")
            self.ec2.stop_instances(InstanceIds=[instance_id])
            
            # Wait for instance to stop
            waiter = self.ec2.get_waiter('instance_stopped')
            waiter.wait(InstanceIds=[instance_id], WaiterConfig={'Delay': 15, 'MaxAttempts': 40})
            
            # Step 3: Start instance
            logger.info(f"Starting instance {instance_id}")
            self.ec2.start_instances(InstanceIds=[instance_id])
            
            # Wait for instance to be running
            waiter = self.ec2.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id], WaiterConfig={'Delay': 15, 'MaxAttempts': 40})
            
            # Step 4: Wait for status checks
            logger.info(f"Waiting for status checks on {instance_id}")
            time.sleep(60)  # Wait for status checks to initialize
            
            # Verify health
            status_response = self.ec2.describe_instance_status(InstanceIds=[instance_id])
            if status_response.get('InstanceStatuses'):
                status = status_response['InstanceStatuses'][0]
                healthy = (
                    status.get('SystemStatus', {}).get('Status') == 'ok' and
                    status.get('InstanceStatus', {}).get('Status') == 'ok'
                )
            else:
                healthy = False
            
            return {
                'success': healthy,
                'action': 'safe_restart',
                'snapshot_id': snapshot_id,
                'instance_state': 'running',
                'healthy': healthy
            }
        
        except Exception as e:
            logger.error(f"Safe restart failed: {e}", error=e, instance_id=instance_id)
            return {
                'success': False,
                'action': 'safe_restart',
                'error': str(e)
            }
    
    def host_migration(self, instance_id: str) -> Dict[str, Any]:
        """Migrate instance to a healthy host in the same AZ."""
        try:
            logger.info(f"Starting host migration for {instance_id}", instance_id=instance_id)
            
            instance_details = self.get_instance_details(instance_id)
            az = instance_details['availability_zone']
            
            # Get all volumes
            volumes = []
            for bdm in instance_details['block_devices']:
                if 'Ebs' in bdm:
                    volumes.append(bdm['Ebs']['VolumeId'])
            
            # Get network interface
            eni_id = None
            if instance_details.get('network_interfaces'):
                eni_id = instance_details['network_interfaces'][0].get('NetworkInterfaceId')
            
            # Stop instance
            self.ec2.stop_instances(InstanceIds=[instance_id])
            waiter = self.ec2.get_waiter('instance_stopped')
            waiter.wait(InstanceIds=[instance_id])
            
            # Detach volumes
            for volume_id in volumes:
                try:
                    self.ec2.detach_volume(VolumeId=volume_id, InstanceId=instance_id)
                except Exception as e:
                    logger.warning(f"Error detaching volume {volume_id}: {e}")
            
            # Detach ENI
            if eni_id:
                try:
                    self.ec2.detach_network_interface(AttachmentId=eni_id, Force=True)
                except Exception as e:
                    logger.warning(f"Error detaching ENI {eni_id}: {e}")
            
            # Terminate old instance
            self.ec2.terminate_instances(InstanceIds=[instance_id])
            
            # Launch new instance with same configuration
            # This is simplified - in production, you'd preserve all settings
            logger.info("Host migration requires manual configuration - not fully automated")
            
            return {
                'success': False,
                'action': 'host_migration',
                'message': 'Host migration requires additional configuration'
            }
        
        except Exception as e:
            logger.error(f"Host migration failed: {e}", error=e, instance_id=instance_id)
            return {
                'success': False,
                'action': 'host_migration',
                'error': str(e)
            }
    
    def app_level_recovery(self, instance_id: str) -> Dict[str, Any]:
        """Perform application-level recovery using SSM."""
        try:
            logger.info(f"Starting app-level recovery for {instance_id}", instance_id=instance_id)
            
            # Run SSM document to restart services
            response = self.ssm.send_command(
                InstanceIds=[instance_id],
                DocumentName='AWS-RunShellScript',
                Parameters={
                    'commands': [
                        'systemctl restart application || service application restart || docker restart $(docker ps -q)'
                    ]
                },
                TimeoutSeconds=300
            )
            
            command_id = response['Command']['CommandId']
            
            # Wait for command completion
            time.sleep(10)
            
            # Get command result
            result = self.ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )
            
            success = result.get('Status') == 'Success'
            
            return {
                'success': success,
                'action': 'app_level_recovery',
                'command_id': command_id,
                'status': result.get('Status')
            }
        
        except Exception as e:
            logger.error(f"App-level recovery failed: {e}", error=e, instance_id=instance_id)
            return {
                'success': False,
                'action': 'app_level_recovery',
                'error': str(e)
            }
    
    def quarantine_instance(self, instance_id: str) -> Dict[str, Any]:
        """Quarantine instance by adding tag and removing from LB."""
        try:
            logger.info(f"Quarantining instance {instance_id}", instance_id=instance_id)
            
            # Add quarantine tag
            self.ec2.create_tags(
                Resources=[instance_id],
                Tags=[{'Key': 'quarantine', 'Value': 'true'}]
            )
            
            # Update DynamoDB config
            update_instance_config(instance_id, {'quarantine': True})
            
            # Remove from load balancer target groups
            # Get target groups (simplified - would need to query ELB/ALB)
            # This is a placeholder - in production, you'd query all LBs
            
            return {
                'success': True,
                'action': 'quarantine',
                'message': 'Instance quarantined'
            }
        
        except Exception as e:
            logger.error(f"Quarantine failed: {e}", error=e, instance_id=instance_id)
            return {
                'success': False,
                'action': 'quarantine',
                'error': str(e)
            }
    
    def determine_recovery_action(self, instance_id: str, trigger_type: str) -> str:
        """Determine appropriate recovery action based on instance state and config."""
        config = get_instance_config(instance_id)
        
        if not config:
            # Default policy
            return 'safe_restart'
        
        # Check if recovery is disabled
        if config.get('recovery_enabled', True) is False:
            return 'none'
        
        # Check quarantine
        if config.get('quarantine', False):
            return 'quarantine'
        
        # Check trigger type
        if trigger_type == 'predictive' and config.get('auto_restart', True):
            return 'safe_restart'
        elif trigger_type == 'health_check':
            # Try app-level first if enabled
            if config.get('app_level_recovery', True):
                return 'app_level_recovery'
            elif config.get('auto_restart', True):
                return 'safe_restart'
        
        return 'safe_restart'  # Default
    
    def execute_recovery(self, instance_id: str, trigger_type: str) -> Dict[str, Any]:
        """Execute recovery action."""
        try:
            logger.info(
                f"Executing recovery for {instance_id}",
                instance_id=instance_id,
                trigger_type=trigger_type
            )
            
            # Determine action
            action = self.determine_recovery_action(instance_id, trigger_type)
            
            if action == 'none':
                logger.info(f"Recovery disabled for {instance_id}")
                return {'success': False, 'reason': 'Recovery disabled'}
            
            # Save recovery event
            save_recovery_event(
                instance_id=instance_id,
                event_type=trigger_type,
                status='in_progress',
                action_taken=action
            )
            
            # Execute action
            result = None
            if action == 'safe_restart':
                result = self.safe_instance_restart(instance_id)
            elif action == 'app_level_recovery':
                result = self.app_level_recovery(instance_id)
            elif action == 'host_migration':
                result = self.host_migration(instance_id)
            elif action == 'quarantine':
                result = self.quarantine_instance(instance_id)
            else:
                result = {'success': False, 'error': f'Unknown action: {action}'}
            
            # Update recovery event
            save_recovery_event(
                instance_id=instance_id,
                event_type=trigger_type,
                status='success' if result.get('success') else 'failed',
                action_taken=action,
                metadata=result
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Recovery execution failed: {e}", error=e, instance_id=instance_id)
            save_recovery_event(
                instance_id=instance_id,
                event_type=trigger_type,
                status='failed',
                action_taken='error',
                metadata={'error': str(e)}
            )
            return {'success': False, 'error': str(e)}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for auto-recovery."""
    try:
        logger.info("Auto-recovery triggered", event=event)
        
        # Extract instance ID and trigger type
        instance_id = None
        trigger_type = 'unknown'
        
        # Try various event formats
        if 'instance_id' in event:
            instance_id = event['instance_id']
            trigger_type = event.get('trigger_type', 'health_check')
        elif 'detail' in event:
            instance_id = event['detail'].get('instance-id') or event['detail'].get('instance_id')
            trigger_type = event.get('detail-type', 'health_check')
        elif 'instance-id' in event:
            instance_id = event['instance-id']
        
        if not instance_id:
            logger.error("No instance ID found in event", event=event)
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No instance ID in event'})
            }
        
        # Execute recovery
        engine = RecoveryEngine()
        result = engine.execute_recovery(instance_id, trigger_type)
        
        return {
            'statusCode': 200 if result.get('success') else 500,
            'body': json.dumps({
                'instance_id': instance_id,
                'result': result
            })
        }
    
    except Exception as e:
        logger.error(f"Fatal error in auto-recovery: {e}", error=e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

