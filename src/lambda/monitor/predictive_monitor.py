"""Predictive monitoring Lambda function."""
import json
import os
import sys
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import StructuredLogger
from utils.config import Config
from utils.dynamodb_helpers import save_prediction_event, get_instance_config
from utils.aws_client import get_ec2_client

# Import prediction engine
# When packaged, prediction_engine is at the same level as lambda in src/
# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
from prediction_engine.metric_analysis import MetricAnalyzer
from prediction_engine.anomaly_scoring import AnomalyScorer

logger = StructuredLogger(__name__)


def get_monitored_instances() -> List[str]:
    """Get list of EC2 instances to monitor."""
    try:
        ec2 = get_ec2_client()
        
        # Get instances with monitoring tag
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:AutoRecovery', 'Values': ['enabled', 'true']},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        
        instance_ids = []
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_ids.append(instance['InstanceId'])
        
        return instance_ids
    except Exception as e:
        logger.error(f"Failed to get monitored instances: {e}", error=e)
        return []


def should_monitor_instance(instance_id: str) -> bool:
    """Check if instance should be monitored based on config."""
    config = get_instance_config(instance_id)
    
    if not config:
        return True  # Default to monitoring if no config
    
    # Check if monitoring is disabled
    if config.get('monitoring_enabled', True) is False:
        return False
    
    # Check if instance is in quarantine
    if config.get('quarantine', False):
        return False
    
    return True


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for predictive monitoring."""
    try:
        logger.info("Starting predictive monitoring cycle")
        
        # Get instances to monitor
        instance_ids = get_monitored_instances()
        
        if not instance_ids:
            logger.info("No instances found for monitoring")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No instances to monitor'})
            }
        
        analyzer = MetricAnalyzer()
        scorer = AnomalyScorer()
        
        predictions = []
        
        for instance_id in instance_ids:
            try:
                # Check if should monitor
                if not should_monitor_instance(instance_id):
                    logger.info(f"Skipping {instance_id} - monitoring disabled or quarantined")
                    continue
                
                logger.info(f"Analyzing metrics for {instance_id}")
                
                # Analyze all metrics
                metric_results = analyzer.analyze_all_metrics(instance_id)
                
                # Score anomalies
                prediction = scorer.score_anomalies(metric_results)
                
                # Only save if confidence is medium or high
                if prediction['confidence'] in ['high', 'medium']:
                    save_prediction_event(
                        instance_id=instance_id,
                        confidence=prediction['confidence'],
                        score=prediction['score'],
                        factors=prediction['factors'],
                        predicted_window=prediction['predicted_window']
                    )
                    
                    predictions.append(prediction)
                    
                    logger.warning(
                        f"Prediction detected for {instance_id}",
                        instance_id=instance_id,
                        confidence=prediction['confidence'],
                        failure_type=prediction['failure_type'],
                        score=prediction['score']
                    )
                else:
                    logger.info(
                        f"No significant prediction for {instance_id}",
                        instance_id=instance_id,
                        score=prediction['score']
                    )
            
            except Exception as e:
                logger.error(f"Error processing {instance_id}: {e}", error=e, instance_id=instance_id)
                continue
        
        # Trigger recovery for high-confidence predictions
        if predictions:
            high_confidence = [p for p in predictions if p['confidence'] == 'high']
            if high_confidence:
                logger.warning(
                    f"Found {len(high_confidence)} high-confidence predictions",
                    count=len(high_confidence)
                )
                # EventBridge will trigger recovery Lambda based on DynamoDB stream or EventBridge rule
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Monitoring cycle completed',
                'instances_checked': len(instance_ids),
                'predictions_found': len(predictions)
            })
        }
    
    except Exception as e:
        logger.error(f"Fatal error in predictive monitoring: {e}", error=e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

