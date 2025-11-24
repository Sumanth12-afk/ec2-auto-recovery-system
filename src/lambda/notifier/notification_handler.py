"""Notification handler for SNS, Slack, and Teams."""
import json
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import urllib.request
import urllib.parse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import StructuredLogger
from utils.config import Config
from utils.aws_client import get_sns_client, get_cloudwatch_client
from utils.dynamodb_helpers import get_recovery_history, get_instance_config

logger = StructuredLogger(__name__)


class NotificationHandler:
    """Handles notifications to multiple channels."""
    
    def __init__(self):
        self.sns = get_sns_client()
        self.cloudwatch = get_cloudwatch_client()
    
    def format_incident_summary(
        self,
        instance_id: str,
        trigger_cause: str,
        action_taken: str,
        result: Dict[str, Any],
        region: str
    ) -> Dict[str, Any]:
        """Format comprehensive incident summary."""
        config = get_instance_config(instance_id)
        history = get_recovery_history(instance_id, limit=5)
        
        # Get CloudWatch dashboard link
        dashboard_url = (
            f"https://{region}.console.aws.amazon.com/cloudwatch/home?"
            f"region={region}#dashboards:name=EC2-{instance_id}"
        )
        
        summary = {
            'title': f'EC2 Auto-Recovery Incident: {instance_id}',
            'instance_id': instance_id,
            'region': region,
            'account': os.environ.get('AWS_ACCOUNT_ID', 'unknown'),
            'timestamp': result.get('timestamp'),
            'trigger_cause': trigger_cause,
            'action_taken': action_taken,
            'recovery_status': 'success' if result.get('success') else 'failed',
            'recovery_result': result,
            'cloudwatch_dashboard': dashboard_url,
            'recovery_history': len(history),
            'instance_config': {
                'quarantine': config.get('quarantine', False) if config else False,
                'recovery_enabled': config.get('recovery_enabled', True) if config else True
            }
        }
        
        return summary
    
    def send_sns_notification(
        self,
        topic_arn: str,
        subject: str,
        message: str
    ) -> bool:
        """Send notification via SNS."""
        try:
            self.sns.publish(
                TopicArn=topic_arn,
                Subject=subject,
                Message=message
            )
            logger.info(f"SNS notification sent to {topic_arn}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SNS notification: {e}", error=e)
            return False
    
    def send_slack_notification(
        self,
        webhook_url: str,
        summary: Dict[str, Any]
    ) -> bool:
        """Send notification to Slack."""
        try:
            # Format Slack message
            color = 'good' if summary['recovery_status'] == 'success' else 'danger'
            
            # Get channel and username from environment
            channel = os.environ.get('SLACK_CHANNEL', '#general')
            username = os.environ.get('SLACK_USERNAME', 'EC2 Auto-Recovery')
            
            slack_message = {
                'channel': channel,
                'username': username,
                'attachments': [{
                    'color': color,
                    'title': summary['title'],
                    'fields': [
                        {'title': 'Instance ID', 'value': summary['instance_id'], 'short': True},
                        {'title': 'Region', 'value': summary['region'], 'short': True},
                        {'title': 'Trigger Cause', 'value': summary['trigger_cause'], 'short': True},
                        {'title': 'Action Taken', 'value': summary['action_taken'], 'short': True},
                        {'title': 'Recovery Status', 'value': summary['recovery_status'], 'short': True},
                        {'title': 'CloudWatch Dashboard', 'value': summary['cloudwatch_dashboard'], 'short': False}
                    ],
                    'footer': 'EC2 Auto-Recovery System',
                    'ts': int(datetime.utcnow().timestamp())
                }]
            }
            
            # Send to Slack
            data = json.dumps(slack_message).encode('utf-8')
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info("Slack notification sent successfully")
                    return True
                else:
                    logger.error(f"Slack webhook returned status {response.status}")
                    return False
        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}", error=e)
            return False
    
    def send_teams_notification(
        self,
        webhook_url: str,
        summary: Dict[str, Any]
    ) -> bool:
        """Send notification to Microsoft Teams."""
        try:
            # Format Teams message
            color = '28a745' if summary['recovery_status'] == 'success' else 'dc3545'
            
            teams_message = {
                '@type': 'MessageCard',
                '@context': 'https://schema.org/extensions',
                'summary': summary['title'],
                'themeColor': color,
                'title': summary['title'],
                'sections': [{
                    'activityTitle': f"Instance: {summary['instance_id']}",
                    'facts': [
                        {'name': 'Region', 'value': summary['region']},
                        {'name': 'Trigger Cause', 'value': summary['trigger_cause']},
                        {'name': 'Action Taken', 'value': summary['action_taken']},
                        {'name': 'Recovery Status', 'value': summary['recovery_status']}
                    ],
                    'markdown': True
                }],
                'potentialAction': [{
                    '@type': 'OpenUri',
                    'name': 'View CloudWatch Dashboard',
                    'targets': [{'os': 'default', 'uri': summary['cloudwatch_dashboard']}]
                }]
            }
            
            # Send to Teams
            data = json.dumps(teams_message).encode('utf-8')
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200 or response.status == 201:
                    logger.info("Teams notification sent successfully")
                    return True
                else:
                    logger.error(f"Teams webhook returned status {response.status}")
                    return False
        
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}", error=e)
            return False
    
    def send_notifications(
        self,
        instance_id: str,
        trigger_cause: str,
        action_taken: str,
        result: Dict[str, Any],
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send notifications to all configured channels."""
        if not Config.NOTIFICATION_ENABLED:
            logger.info("Notifications disabled")
            return {'sent': False, 'reason': 'Notifications disabled'}
        
        region = region or os.environ.get('AWS_REGION', 'us-east-1')
        
        # Format summary
        summary = self.format_incident_summary(
            instance_id,
            trigger_cause,
            action_taken,
            result,
            region
        )
        
        results = {
            'sns': False,
            'slack': False,
            'teams': False
        }
        
        # Send SNS if configured
        sns_topic = os.environ.get('SNS_TOPIC_ARN')
        if sns_topic:
            message = json.dumps(summary, indent=2)
            results['sns'] = self.send_sns_notification(
                sns_topic,
                f"EC2 Auto-Recovery: {instance_id}",
                message
            )
        
        # Send Slack if configured
        slack_webhook = os.environ.get('SLACK_WEBHOOK_URL')
        if slack_webhook:
            results['slack'] = self.send_slack_notification(slack_webhook, summary)
        
        # Send Teams if configured
        teams_webhook = os.environ.get('TEAMS_WEBHOOK_URL')
        if teams_webhook:
            results['teams'] = self.send_teams_notification(teams_webhook, summary)
        
        return results


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for notifications."""
    try:
        logger.info("Notification handler triggered", event=event)
        
        # Extract event details
        instance_id = event.get('instance_id') or event.get('detail', {}).get('instance-id')
        trigger_cause = event.get('trigger_cause', 'unknown')
        action_taken = event.get('action_taken', 'unknown')
        result = event.get('result', {})
        
        if not instance_id:
            logger.error("No instance ID in notification event", event=event)
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No instance ID'})
            }
        
        # Send notifications
        handler = NotificationHandler()
        notification_results = handler.send_notifications(
            instance_id,
            trigger_cause,
            action_taken,
            result
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'instance_id': instance_id,
                'notifications_sent': notification_results
            })
        }
    
    except Exception as e:
        logger.error(f"Fatal error in notification handler: {e}", error=e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

