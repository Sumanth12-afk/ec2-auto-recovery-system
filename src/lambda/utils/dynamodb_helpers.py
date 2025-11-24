"""DynamoDB helper functions."""
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from .aws_client import get_dynamodb_resource
from .config import Config
from .logger import StructuredLogger

logger = StructuredLogger(__name__)


def save_recovery_event(
    instance_id: str,
    event_type: str,
    status: str,
    action_taken: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Save recovery event to DynamoDB."""
    try:
        table = get_dynamodb_resource().Table(Config.RECOVERY_EVENTS_TABLE)
        
        item = {
            'instance_id': instance_id,
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,  # 'predictive', 'health_check', 'app_failure'
            'status': status,  # 'success', 'failed', 'in_progress'
            'action_taken': action_taken,
            'metadata': metadata or {}
        }
        
        table.put_item(Item=item)
        logger.info(
            f"Saved recovery event for {instance_id}",
            instance_id=instance_id,
            event_type=event_type,
            status=status
        )
    except Exception as e:
        logger.error(f"Failed to save recovery event: {e}", error=e)


def save_prediction_event(
    instance_id: str,
    confidence: str,  # 'high', 'medium', 'low'
    score: float,
    factors: List[Dict[str, Any]],
    predicted_window: str
) -> None:
    """Save prediction event to DynamoDB."""
    try:
        table = get_dynamodb_resource().Table(Config.PREDICTION_EVENTS_TABLE)
        
        item = {
            'instance_id': instance_id,
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': confidence,
            'score': score,
            'factors': factors,
            'predicted_window': predicted_window,
            'ttl': int(datetime.utcnow().timestamp()) + (30 * 24 * 60 * 60)  # 30 days TTL
        }
        
        table.put_item(Item=item)
        logger.info(
            f"Saved prediction event for {instance_id}",
            instance_id=instance_id,
            confidence=confidence,
            score=score
        )
    except Exception as e:
        logger.error(f"Failed to save prediction event: {e}", error=e)


def get_instance_config(instance_id: str) -> Optional[Dict[str, Any]]:
    """Get instance configuration from DynamoDB."""
    try:
        table = get_dynamodb_resource().Table(Config.INSTANCE_CONFIG_TABLE)
        response = table.get_item(Key={'instance_id': instance_id})
        
        if 'Item' in response:
            return response['Item']
        return None
    except Exception as e:
        logger.error(f"Failed to get instance config: {e}", error=e)
        return None


def update_instance_config(instance_id: str, config: Dict[str, Any]) -> None:
    """Update instance configuration in DynamoDB."""
    try:
        table = get_dynamodb_resource().Table(Config.INSTANCE_CONFIG_TABLE)
        
        item = {
            'instance_id': instance_id,
            'last_updated': datetime.utcnow().isoformat(),
            **config
        }
        
        table.put_item(Item=item)
        logger.info(f"Updated instance config for {instance_id}", instance_id=instance_id)
    except Exception as e:
        logger.error(f"Failed to update instance config: {e}", error=e)


def get_recovery_history(instance_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recovery history for an instance."""
    try:
        table = get_dynamodb_resource().Table(Config.RECOVERY_EVENTS_TABLE)
        
        response = table.query(
            KeyConditionExpression='instance_id = :instance_id',
            ExpressionAttributeValues={':instance_id': instance_id},
            ScanIndexForward=False,
            Limit=limit
        )
        
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Failed to get recovery history: {e}", error=e)
        return []

