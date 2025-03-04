import scrapy
import logging
from pathlib import Path

class GoogleSpider(scrapy.Spider):
    name = "google" 
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1
    }
    
    def __init__(self, keywords=None, *args, **kwargs):
        """
        Initialize spider with keywords provided externally
        
        Args:
            keywords (list): List of keywords to search for
        """
        super(GoogleSpider, self).__init__(*args, **kwargs)
        # Default keywords if none provided
        self.keywords = keywords 
        self.logger.info(f"Spider initialized with {len(self.keywords)} keywords")
    
    def start_requests(self):
        """Generate search requests for each keyword"""
        self.logger.info(f"Starting requests for keywords: {self.keywords}")
        
        for keyword in self.keywords:
            for page in range(1):  # Crawl first 1 pages for each keyword
                start = page * 10
                url = f"https://www.google.com/search?q={keyword}&start={start}"
                self.logger.info(f"Queuing search for: {keyword} (page {page+1})")
                yield scrapy.Request(url, 
                                   self.parse, 
                                   meta={"keyword": keyword},
                                   headers={'User-Agent': self.custom_settings['USER_AGENT']})

    def parse(self, response):
        keyword = response.meta["keyword"]
        self.logger.info(f"Parsing Google search results for: {keyword}")
        self.logger.info(f"Response body: {response.body}")
        # Debug - save response for analysis (uncomment if needed)
        # with open('google_response.html', 'wb') as f:
        #     f.write(response.body)
        
        # Try multiple selectors to find search results
        # Modern Google search results structure (as of March 2025)
        search_results = []
        
        # Method 1: Main search result containers
        results = response.css("div.g")
        if results:
            self.logger.info(f"Found {len(results)} results with 'div.g' selector")
            search_results = results
        
        # Method 2: Alternative modern container
        if not search_results:
            results = response.css("div.MjjYud")
            if results:
                self.logger.info(f"Found {len(results)} results with 'div.MjjYud' selector")
                search_results = results
        
        # Method 3: Another alternative container
        if not search_results:
            results = response.css("div.yuRUbf")
            if results:
                self.logger.info(f"Found {len(results)} results with 'div.yuRUbf' selector")
                search_results = results
                
        # If we found results with any method, process them
        for result in search_results:
            # Try different selectors for titles and links
            title = None
            link = None
            
            # Title selectors
            title_selectors = [
                "h3.LC20lb::text",  # Current common title class
                "h3::text",         # Generic h3 text
                ".LC20lb::text"     # Just the class without h3
            ]
            
            for selector in title_selectors:
                title_text = result.css(selector).get()
                if title_text and title_text.strip():
                    title = title_text.strip()
                    break
            
            # Link selectors
            link_selectors = [
                "a::attr(href)",                  # Direct link
                ".yuRUbf a::attr(href)",          # Link inside containing div
                "div > div > a::attr(href)"       # Nested structure
            ]
            
            for selector in link_selectors:
                link_url = result.css(selector).get()
                if link_url and link_url.startswith('http'):
                    link = link_url
                    break
            
            if title and link:
                self.logger.info(f"Found result: {title} - {link}")
                yield {
                    "keyword": keyword,
                    "title": title,
                    "link": link
                }
            else:
                self.logger.warning(f"Incomplete result found, skipping...")
        
        # If we didn't find any results with our selectors
        if not search_results:
            self.logger.error(f"No search result containers found for keyword: {keyword}")
            self.logger.error("Google may have updated their HTML structure again")