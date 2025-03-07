import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from google_crawler.spiders.google_spider import GoogleSpider
from scrapy import signals
from scrapy.signalmanager import dispatcher

class GoogleCrawler:
    """
    Manages the Google search crawling process using Scrapy and returns links directly
    """
    
    def __init__(self, logger=None):
        """Initialize the Google crawler"""
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.results = []  # Will store search results directly
            
    def run(self, keywords=None, results_per_keyword=20, max_pages=10):
        """
        Run the Google crawler and return search results directly
        
        Args:
            keywords (list): List of keywords to search for
            results_per_keyword (int): Target number of results to fetch per keyword
            max_pages (int): Maximum number of pages to crawl per keyword
            
        Returns:
            list: List of dictionaries with search results (keyword, title, link)
        """
        self.logger.info("Initializing Google search crawler")
        self.results = []  # Reset results
        
        if not keywords:
            self.logger.warning("No keywords provided to GoogleCrawler")
            return []
            
        self.logger.info(f"Starting Google crawler with {len(keywords)} keywords")
        self.logger.info(f"Target: collect up to {results_per_keyword} results per keyword")
        self.logger.info(f"Maximum {max_pages} pages will be crawled per keyword")
        
        try:
            # Configure Scrapy crawler process
            settings = get_project_settings()
            process = CrawlerProcess(settings)
            
            # Set up the signal to collect items
            dispatcher.connect(self._item_scraped, signals.item_scraped)
            
            # Add the Google spider to the process with all parameters
            process.crawl(GoogleSpider, 
                         keywords=keywords, 
                         results_per_keyword=results_per_keyword,
                         max_pages=max_pages)
            
            # Run the crawler
            self.logger.info("Starting Google search crawling...")
            process.start()
            
            # Process is complete at this point
            self.logger.info(f"Google search crawling finished with {len(self.results)} total results")
            
            return self.results
                
        except Exception as e:
            self.logger.error(f"Error during Google crawling: {str(e)}")
            self.logger.exception("Exception details:")
            return []
    
    def _item_scraped(self, item, response, spider):
        """
        Callback function for scrapy signal when an item is scraped
        """
        result_dict = dict(item)
        self.results.append(result_dict)