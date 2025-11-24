"""CloudWatch metric pattern analysis for predictive failure detection."""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import statistics
import sys
import os
# Add lambda directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))
from utils.aws_client import get_cloudwatch_client
from utils.config import Config, PredictionThresholds
from utils.logger import StructuredLogger

logger = StructuredLogger(__name__)


class MetricAnalyzer:
    """Analyzes CloudWatch metrics for failure prediction patterns."""
    
    def __init__(self, thresholds: Optional[PredictionThresholds] = None):
        self.thresholds = thresholds or Config.get_thresholds()
        self.cloudwatch = get_cloudwatch_client()
    
    def get_metric_statistics(
        self,
        instance_id: str,
        metric_name: str,
        namespace: str,
        hours: int,
        statistic: str = 'Average'
    ) -> List[float]:
        """Get metric statistics for the specified time period."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': instance_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=[statistic]
            )
            
            datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
            return [dp[statistic] for dp in datapoints]
        except Exception as e:
            logger.error(f"Failed to get metric statistics: {e}", error=e)
            return []
    
    def analyze_cpu_steal(self, instance_id: str) -> Dict[str, Any]:
        """Analyze CPU steal time patterns."""
        values = self.get_metric_statistics(
            instance_id,
            'CPUStealTime',
            'AWS/EC2',
            Config.PREDICTION_LOOKBACK_HOURS
        )
        
        if not values:
            return {'detected': False, 'severity': 'none', 'trend': 'unknown'}
        
        avg = statistics.mean(values)
        recent_avg = statistics.mean(values[-24:]) if len(values) >= 24 else avg
        trend = 'increasing' if recent_avg > avg * 1.2 else 'stable'
        
        severity = 'none'
        if recent_avg >= self.thresholds.cpu_steal_critical:
            severity = 'critical'
        elif recent_avg >= self.thresholds.cpu_steal_warning:
            severity = 'warning'
        
        return {
            'detected': severity != 'none',
            'severity': severity,
            'trend': trend,
            'current_value': recent_avg,
            'average_value': avg,
            'max_value': max(values)
        }
    
    def analyze_iowait(self, instance_id: str) -> Dict[str, Any]:
        """Analyze I/O wait patterns."""
        values = self.get_metric_statistics(
            instance_id,
            'CPUUtilization',  # Will need CW Agent for iowait specifically
            'AWS/EC2',
            Config.PREDICTION_LOOKBACK_HOURS
        )
        
        # For iowait, we'd need CloudWatch Agent metrics
        # This is a simplified version
        if not values:
            return {'detected': False, 'severity': 'none', 'trend': 'unknown'}
        
        # Check for spikes (high variance)
        if len(values) < 2:
            return {'detected': False, 'severity': 'none', 'trend': 'unknown'}
        
        variance = statistics.variance(values)
        mean_val = statistics.mean(values)
        recent_values = values[-24:] if len(values) >= 24 else values
        recent_avg = statistics.mean(recent_values)
        
        # High variance and increasing trend suggests I/O issues
        trend = 'increasing' if recent_avg > mean_val * 1.3 else 'stable'
        has_spikes = variance > (mean_val * 0.5)  # High variance indicates spikes
        
        severity = 'none'
        if has_spikes and recent_avg >= self.thresholds.iowait_critical:
            severity = 'critical'
        elif has_spikes and recent_avg >= self.thresholds.iowait_warning:
            severity = 'warning'
        
        return {
            'detected': severity != 'none',
            'severity': severity,
            'trend': trend,
            'has_spikes': has_spikes,
            'variance': variance,
            'current_value': recent_avg
        }
    
    def analyze_memory_saturation(self, instance_id: str) -> Dict[str, Any]:
        """Analyze memory saturation patterns."""
        # CloudWatch Agent metric
        values = self.get_metric_statistics(
            instance_id,
            'mem_used_percent',
            'CWAgent',
            Config.PREDICTION_LOOKBACK_HOURS
        )
        
        if not values:
            return {'detected': False, 'severity': 'none', 'trend': 'unknown'}
        
        recent_avg = statistics.mean(values[-24:]) if len(values) >= 24 else statistics.mean(values)
        trend = 'increasing' if len(values) >= 2 and values[-1] > values[-2] else 'stable'
        
        severity = 'none'
        if recent_avg >= self.thresholds.memory_saturation_critical:
            severity = 'critical'
        elif recent_avg >= self.thresholds.memory_saturation_warning:
            severity = 'warning'
        
        return {
            'detected': severity != 'none',
            'severity': severity,
            'trend': trend,
            'current_value': recent_avg,
            'max_value': max(values)
        }
    
    def analyze_disk_usage(self, instance_id: str) -> Dict[str, Any]:
        """Analyze disk usage patterns."""
        values = self.get_metric_statistics(
            instance_id,
            'disk_used_percent',
            'CWAgent',
            Config.PREDICTION_LOOKBACK_HOURS
        )
        
        if not values:
            return {'detected': False, 'severity': 'none', 'trend': 'unknown'}
        
        recent_avg = statistics.mean(values[-24:]) if len(values) >= 24 else statistics.mean(values)
        trend = 'increasing' if len(values) >= 2 and values[-1] > values[-2] else 'stable'
        
        severity = 'none'
        if recent_avg >= self.thresholds.disk_usage_critical:
            severity = 'critical'
        elif recent_avg >= self.thresholds.disk_usage_warning:
            severity = 'warning'
        
        return {
            'detected': severity != 'none',
            'severity': severity,
            'trend': trend,
            'current_value': recent_avg,
            'max_value': max(values)
        }
    
    def analyze_cpu_credit_balance(self, instance_id: str) -> Dict[str, Any]:
        """Analyze CPU credit balance for T-family instances."""
        values = self.get_metric_statistics(
            instance_id,
            'CPUCreditBalance',
            'AWS/EC2',
            Config.PREDICTION_LOOKBACK_HOURS
        )
        
        if not values:
            return {'detected': False, 'severity': 'none', 'trend': 'unknown'}
        
        recent_avg = statistics.mean(values[-24:]) if len(values) >= 24 else statistics.mean(values)
        min_value = min(values)
        trend = 'decreasing' if recent_avg < statistics.mean(values) * 0.8 else 'stable'
        
        severity = 'none'
        if min_value < self.thresholds.cpu_credit_balance_warning:
            severity = 'warning'
        
        return {
            'detected': severity != 'none',
            'severity': severity,
            'trend': trend,
            'current_value': recent_avg,
            'min_value': min_value
        }
    
    def analyze_status_check_failures(self, instance_id: str) -> Dict[str, Any]:
        """Analyze EC2 status check failure patterns."""
        # This would typically come from EventBridge events
        # For now, we'll check CloudWatch alarms or recent events
        # In production, this would query EventBridge or CloudWatch Events
        
        return {
            'detected': False,  # Placeholder - would be populated from EventBridge
            'severity': 'none',
            'failure_count': 0
        }
    
    def analyze_all_metrics(self, instance_id: str) -> Dict[str, Any]:
        """Run all metric analyses and return comprehensive results."""
        results = {
            'instance_id': instance_id,
            'timestamp': datetime.utcnow().isoformat(),
            'cpu_steal': self.analyze_cpu_steal(instance_id),
            'iowait': self.analyze_iowait(instance_id),
            'memory_saturation': self.analyze_memory_saturation(instance_id),
            'disk_usage': self.analyze_disk_usage(instance_id),
            'cpu_credit_balance': self.analyze_cpu_credit_balance(instance_id),
            'status_check_failures': self.analyze_status_check_failures(instance_id)
        }
        
        return results

