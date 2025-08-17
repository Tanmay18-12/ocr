import logging
import os
from datetime import datetime
from config import Config

def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    os.makedirs(Config.LOGS_DIR, exist_ok=True)
    
    # Create log filename with timestamp
    log_filename = os.path.join(
        Config.LOGS_DIR, 
        f"extraction_{datetime.now().strftime('%Y%m%d')}.log"
    )
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    # Create logger
    logger = logging.getLogger('DocumentExtractor')
    
    # Log startup message
    logger.info("="*50)
    logger.info("Document Extraction System Started")
    logger.info(f"Log file: {log_filename}")
    logger.info("="*50)
    
    return logger