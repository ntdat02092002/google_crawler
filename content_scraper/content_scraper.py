import logging
import random
import time
import trafilatura

from copy import deepcopy
from trafilatura.settings import DEFAULT_CONFIG

from utils.user_agents import get_user_agent_list
from utils.logger import silence_trafilatura_log

class ContentScraper:
    """
    Simplified content scraper that takes a link and returns content using Trafilatura
    """
    
    def __init__(self, logger=None):
        """Initialize the content scraper"""
        self.logger = logger or logging.getLogger(self.__class__.__name__)

        custom_config = deepcopy(DEFAULT_CONFIG)
        custom_config['DEFAULT']['USER_AGENTS'] = "\n".join(get_user_agent_list())

        self.custom_config = custom_config

        silence_trafilatura_log()
    
    def scrape(self, url, keyword, title, description):
        """
        Scrape content from a specific URL using Trafilatura.
        
        Args:
            url (str): The URL to scrape
            keyword (str): The keyword that found this URL
            title (str): The title of the search result
            description (str): The description of the search result
            
        Returns:
            dict: Scraped content with standard fields
        """
        self.logger.info(f"Scraping content from: {url}")
        
        try:  
            # Use trafilatura's built-in fetch function
            downloaded = trafilatura.fetch_url(
                url,
                config=self.custom_config,
            )
            
            if downloaded is None:
                self.logger.error(f"Failed to download content from {url}")
                content = "Failed to download content"
            else:
                # Extract text content from the downloaded HTML
                content = trafilatura.extract(downloaded, config=self.custom_config)
                
                if not content:
                    self.logger.warning(f"Trafilatura couldn't extract meaningful content from {url}")
                    content = "No meaningful content could be extracted"
            
            # Return structured data
            return {
                'title': title,
                'url': url,
                'description': description,
                'content': content,
                'keyword': keyword,
            }
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            # Return basic information even on error
            return {
                'title': title,
                'url': url,
                'description': description,
                'content': f"Error extracting content: {str(e)}",
                'keyword': keyword,
            }