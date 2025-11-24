"""Configuration management using Pydantic models."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import os


class NotificationConfig(BaseModel):
    """Notification configuration."""
    sns_topic_arn: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    teams_webhook_url: Optional[str] = None
    enabled: bool = True


class RecoveryPolicy(BaseModel):
    """Recovery policy configuration."""
    instance_id: str
    enabled: bool = True
    auto_restart: bool = True
    host_migration: bool = False
    cross_az_failover: bool = False
    ebs_repair: bool = False
    app_level_recovery: bool = True
    quarantine_mode: bool = False
    notification_channels: List[str] = Field(default_factory=list)


class PredictionThresholds(BaseModel):
    """Thresholds for predictive failure detection."""
    cpu_steal_warning: float = 5.0  # Percentage
    cpu_steal_critical: float = 10.0
    iowait_warning: float = 20.0
    iowait_critical: float = 40.0
    memory_saturation_warning: float = 85.0
    memory_saturation_critical: float = 95.0
    disk_usage_warning: float = 80.0
    disk_usage_critical: float = 90.0
    network_drop_warning: int = 10  # Packets per minute
    cpu_credit_balance_warning: float = 100.0  # Credits
    disk_queue_depth_warning: float = 10.0
    status_check_failure_count: int = 3  # Consecutive failures


class Config:
    """Application configuration."""
    
    # DynamoDB table names
    RECOVERY_EVENTS_TABLE = os.environ.get('RECOVERY_EVENTS_TABLE', 'ec2-recovery-events')
    PREDICTION_EVENTS_TABLE = os.environ.get('PREDICTION_EVENTS_TABLE', 'ec2-prediction-events')
    INSTANCE_CONFIG_TABLE = os.environ.get('INSTANCE_CONFIG_TABLE', 'ec2-instance-config')
    
    # CloudWatch
    METRIC_NAMESPACE = os.environ.get('METRIC_NAMESPACE', 'EC2/AutoRecovery')
    METRIC_RETENTION_DAYS = int(os.environ.get('METRIC_RETENTION_DAYS', '7'))
    
    # Prediction
    PREDICTION_LOOKBACK_HOURS = int(os.environ.get('PREDICTION_LOOKBACK_HOURS', '168'))  # 7 days
    HIGH_CONFIDENCE_THRESHOLD = float(os.environ.get('HIGH_CONFIDENCE_THRESHOLD', '0.8'))
    MEDIUM_CONFIDENCE_THRESHOLD = float(os.environ.get('MEDIUM_CONFIDENCE_THRESHOLD', '0.6'))
    
    # Recovery
    RECOVERY_TIMEOUT_SECONDS = int(os.environ.get('RECOVERY_TIMEOUT_SECONDS', '600'))
    HEALTH_CHECK_RETRY_COUNT = int(os.environ.get('HEALTH_CHECK_RETRY_COUNT', '3'))
    HEALTH_CHECK_RETRY_DELAY = int(os.environ.get('HEALTH_CHECK_RETRY_DELAY', '30'))
    
    # Notification
    NOTIFICATION_ENABLED = os.environ.get('NOTIFICATION_ENABLED', 'true').lower() == 'true'
    
    @classmethod
    def get_thresholds(cls) -> PredictionThresholds:
        """Get prediction thresholds from environment or defaults."""
        return PredictionThresholds(
            cpu_steal_warning=float(os.environ.get('CPU_STEAL_WARNING', '5.0')),
            cpu_steal_critical=float(os.environ.get('CPU_STEAL_CRITICAL', '10.0')),
            iowait_warning=float(os.environ.get('IOWAIT_WARNING', '20.0')),
            iowait_critical=float(os.environ.get('IOWAIT_CRITICAL', '40.0')),
            memory_saturation_warning=float(os.environ.get('MEMORY_SATURATION_WARNING', '85.0')),
            memory_saturation_critical=float(os.environ.get('MEMORY_SATURATION_CRITICAL', '95.0')),
            disk_usage_warning=float(os.environ.get('DISK_USAGE_WARNING', '80.0')),
            disk_usage_critical=float(os.environ.get('DISK_USAGE_CRITICAL', '90.0')),
            network_drop_warning=int(os.environ.get('NETWORK_DROP_WARNING', '10')),
            cpu_credit_balance_warning=float(os.environ.get('CPU_CREDIT_BALANCE_WARNING', '100.0')),
            disk_queue_depth_warning=float(os.environ.get('DISK_QUEUE_DEPTH_WARNING', '10.0')),
            status_check_failure_count=int(os.environ.get('STATUS_CHECK_FAILURE_COUNT', '3'))
        )

