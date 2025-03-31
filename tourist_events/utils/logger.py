import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "tourist_events.log")

# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5) # 10MB per file, 5 backups
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

def get_logger(name):
    """Gets a configured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Example usage (optional, can be removed or kept for testing)
if __name__ == '__main__':
    logger = get_logger(__name__)
    logger.info("Logging setup complete.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")