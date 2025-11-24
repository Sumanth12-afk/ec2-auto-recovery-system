"""Anomaly scoring engine for predictive failure detection."""
from typing import Dict, List, Any
from datetime import datetime
import sys
import os
# Add lambda directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))
from utils.config import Config
from utils.logger import StructuredLogger

logger = StructuredLogger(__name__)


class AnomalyScorer:
    """Scores anomalies and calculates failure prediction confidence."""
    
    def __init__(self):
        self.high_confidence_threshold = Config.HIGH_CONFIDENCE_THRESHOLD
        self.medium_confidence_threshold = Config.MEDIUM_CONFIDENCE_THRESHOLD
    
    def calculate_severity_score(self, metric_result: Dict[str, Any]) -> float:
        """Calculate severity score for a single metric result."""
        if not metric_result.get('detected', False):
            return 0.0
        
        severity = metric_result.get('severity', 'none')
        trend = metric_result.get('trend', 'stable')
        
        base_score = 0.0
        if severity == 'critical':
            base_score = 0.8
        elif severity == 'warning':
            base_score = 0.4
        
        # Increase score if trend is worsening
        if trend == 'increasing' or trend == 'decreasing':
            base_score *= 1.2
        
        return min(base_score, 1.0)
    
    def calculate_aggregate_score(self, metric_results: Dict[str, Any]) -> float:
        """Calculate aggregate anomaly score from all metric results."""
        scores = []
        
        # CPU Steal
        if metric_results.get('cpu_steal', {}).get('detected'):
            scores.append(self.calculate_severity_score(metric_results['cpu_steal']))
        
        # I/O Wait
        if metric_results.get('iowait', {}).get('detected'):
            scores.append(self.calculate_severity_score(metric_results['iowait']))
        
        # Memory Saturation
        if metric_results.get('memory_saturation', {}).get('detected'):
            scores.append(self.calculate_severity_score(metric_results['memory_saturation']))
        
        # Disk Usage
        if metric_results.get('disk_usage', {}).get('detected'):
            scores.append(self.calculate_severity_score(metric_results['disk_usage']))
        
        # CPU Credit Balance
        if metric_results.get('cpu_credit_balance', {}).get('detected'):
            scores.append(self.calculate_severity_score(metric_results['cpu_credit_balance']))
        
        # Status Check Failures (weighted higher)
        if metric_results.get('status_check_failures', {}).get('detected'):
            status_score = self.calculate_severity_score(metric_results['status_check_failures'])
            scores.append(status_score * 1.5)  # Weight status checks more heavily
        
        if not scores:
            return 0.0
        
        # Use weighted average with emphasis on worst indicators
        if len(scores) == 1:
            return scores[0]
        
        # Average of top 3 scores (if multiple issues, they compound)
        sorted_scores = sorted(scores, reverse=True)
        top_scores = sorted_scores[:min(3, len(sorted_scores))]
        
        # Weighted average: highest score gets 50%, next gets 30%, third gets 20%
        if len(top_scores) == 1:
            return top_scores[0]
        elif len(top_scores) == 2:
            return (top_scores[0] * 0.6) + (top_scores[1] * 0.4)
        else:
            return (top_scores[0] * 0.5) + (top_scores[1] * 0.3) + (top_scores[2] * 0.2)
    
    def determine_confidence_level(self, score: float) -> str:
        """Determine confidence level based on score."""
        if score >= self.high_confidence_threshold:
            return 'high'
        elif score >= self.medium_confidence_threshold:
            return 'medium'
        else:
            return 'low'
    
    def predict_failure_window(self, score: float, confidence: str) -> str:
        """Predict failure window based on score and confidence."""
        if confidence == 'high':
            return '24 hours'
        elif confidence == 'medium':
            return '24-72 hours'
        else:
            return '72+ hours'
    
    def classify_failure_type(self, metric_results: Dict[str, Any]) -> str:
        """Classify the type of potential failure."""
        factors = []
        
        if metric_results.get('cpu_steal', {}).get('detected'):
            factors.append('CPU Steal')
        if metric_results.get('iowait', {}).get('detected'):
            factors.append('I/O Wait')
        if metric_results.get('memory_saturation', {}).get('detected'):
            factors.append('Memory Saturation')
        if metric_results.get('disk_usage', {}).get('detected'):
            factors.append('Disk Saturation')
        if metric_results.get('status_check_failures', {}).get('detected'):
            factors.append('Status Check Failures')
        
        # Classify based on primary indicators
        if 'Status Check Failures' in factors:
            return 'Imminent Failure'
        elif 'CPU Steal' in factors or 'I/O Wait' in factors:
            return 'Potential Hardware Issue'
        elif 'Memory Saturation' in factors or 'Disk Saturation' in factors:
            return 'Performance Risk'
        else:
            return 'Performance Risk'
    
    def extract_prediction_factors(self, metric_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract factors contributing to the prediction."""
        factors = []
        
        for metric_name, result in metric_results.items():
            if metric_name in ['instance_id', 'timestamp']:
                continue
            
            if result.get('detected', False):
                factors.append({
                    'metric': metric_name,
                    'severity': result.get('severity', 'unknown'),
                    'trend': result.get('trend', 'unknown'),
                    'current_value': result.get('current_value'),
                    'details': result
                })
        
        return factors
    
    def score_anomalies(self, metric_results: Dict[str, Any]) -> Dict[str, Any]:
        """Main scoring function that returns comprehensive prediction."""
        score = self.calculate_aggregate_score(metric_results)
        confidence = self.determine_confidence_level(score)
        failure_window = self.predict_failure_window(score, confidence)
        failure_type = self.classify_failure_type(metric_results)
        factors = self.extract_prediction_factors(metric_results)
        
        return {
            'instance_id': metric_results.get('instance_id'),
            'timestamp': datetime.utcnow().isoformat(),
            'score': score,
            'confidence': confidence,
            'predicted_window': failure_window,
            'failure_type': failure_type,
            'factors': factors,
            'metric_results': metric_results
        }

