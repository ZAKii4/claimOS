import json
import logging
from datetime import datetime
from typing import Dict, Any
from app.observability.tracing import tracing_manager

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "trace_id": tracing_manager.get_current_trace_id()
        }
        if hasattr(record, "extra_data"):
            log_obj["data"] = record.extra_data
        return json.dumps(log_obj)

class LoggingManager:
    """
    Centralized JSON Logger.
    """
    def __init__(self):
        self.logger = logging.getLogger("claimOS")
        self.logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        
        # Remove existing handlers to avoid duplicates during hot-reloads
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        self.logger.addHandler(handler)
        
    def info(self, msg: str, extra: Dict[str, Any] = None):
        self.logger.info(msg, extra={"extra_data": extra} if extra else None)
        
    def error(self, msg: str, extra: Dict[str, Any] = None):
        self.logger.error(msg, extra={"extra_data": extra} if extra else None)
        
    def warning(self, msg: str, extra: Dict[str, Any] = None):
        self.logger.warning(msg, extra={"extra_data": extra} if extra else None)

logging_manager = LoggingManager()
