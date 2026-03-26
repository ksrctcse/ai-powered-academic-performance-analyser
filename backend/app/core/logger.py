import logging
import logging.handlers
import os
from datetime import datetime

# Create logs directory if it doesn't exist
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the specified name.
    Logs are written to both console and file.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    
    # File handler - rotating
    log_file = os.path.join(LOGS_DIR, f"{name}.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
