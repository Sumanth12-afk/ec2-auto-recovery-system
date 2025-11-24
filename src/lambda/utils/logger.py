"""Structured JSON logging for Lambda functions."""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredLogger:
    """JSON-structured logger for Lambda functions."""
    
    def __init__(self, name: str = __name__):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Remove default handlers
        self.logger.handlers = []
        
        # Add console handler
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
    
    def _build_log_entry(
        self,
        level: str,
        message: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Build structured log entry."""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'service': os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'unknown'),
            'region': os.environ.get('AWS_REGION', 'unknown'),
            **kwargs
        }
        return entry
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        entry = self._build_log_entry('INFO', message, **kwargs)
        self.logger.info(json.dumps(entry))
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        entry = self._build_log_entry('WARNING', message, **kwargs)
        self.logger.warning(json.dumps(entry))
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs: Any) -> None:
        """Log error message."""
        entry = self._build_log_entry('ERROR', message, **kwargs)
        if error:
            entry['error_type'] = type(error).__name__
            entry['error_message'] = str(error)
            import traceback
            entry['traceback'] = traceback.format_exc()
        self.logger.error(json.dumps(entry))
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        entry = self._build_log_entry('DEBUG', message, **kwargs)
        self.logger.debug(json.dumps(entry))


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        # If already a JSON string, return as-is
        if isinstance(record.msg, str) and record.msg.startswith('{'):
            return record.msg
        return super().format(record)

