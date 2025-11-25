import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict

class PrivacyAwareFormatter(logging.Formatter):
    def format(self, record):
        # Basic structured log
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'metadata'):
            log_record['metadata'] = record.metadata
            
        return json.dumps(log_record)

def setup_logger(name: str = "pocket_ai", level: str = "INFO"):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(PrivacyAwareFormatter())
    logger.addHandler(handler)
    
    return logger

logger = setup_logger()

def log_audit(operation: str, allowed: bool, reason: str, metadata: Dict[str, Any] = None):
    """
    Log an audit event for policy enforcement.
    """
    extra = {
        "audit": True,
        "operation": operation,
        "allowed": allowed,
        "reason": reason
    }
    if metadata:
        extra.update(metadata)
        
    # We use 'extra' to pass data to the formatter if we were using a more complex one,
    # but here we'll just include it in the message or a separate structured field.
    # For simplicity in this prototype, we just log it.
    logger.info(f"AUDIT: {operation} allowed={allowed} reason={reason}", extra={'metadata': extra})

