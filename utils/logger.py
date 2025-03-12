import os
import logging
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """Configure logging to file and console"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # Log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"logs/google_crawler_{timestamp}.log"
    
    # Set up logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Create and return logger
    logger = logging.getLogger("GoogleCrawlerApp")
    logger.info(f"Logging initialized. Log file: {log_file}")
    
    return logger

def silence_scrapy_log():
    """Silence Scrapy loggers to reduce noise"""
    from scrapy.utils import log
    log.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'loggers': {
            'scrapy': {
                'level': 'INFO',
            }
        }
    })

def silence_trafilatura_log():
    """Silence Trafilatura loggers to reduce noise"""
    logger = logging.getLogger("trafilatura")
    logger.setLevel(logging.INFO)