import scrapy
import logging
import random
import time

class GoogleSpider(scrapy.Spider):
    name = "GoogleSpider" 
    
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
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15'
        ]
        
        # Track already visited keywords to avoid duplicates
        self.visited_urls = set()
    
    def get_random_user_agent(self):
        """Get a random user agent string"""
        return random.choice(self.user_agents)
    
    def start_requests(self):
        """Generate search requests for each keyword"""
        self.logger.info(f"Starting requests for keywords: {self.keywords}")
        
        # Group keywords into batches and add delays between batches
        batch_size = 5  # Process keywords in small batches
        
        for i in range(0, len(self.keywords), batch_size):
            batch = self.keywords[i:i+batch_size]
            
            for keyword in batch:
                for page in range(2):  # Crawl first page for each keyword
                    # Add jitter to start parameter
                    start = page * 10
                    
                    # Create URL with unique hl and gl parameters
                    url = f"https://www.google.com/search?q={keyword}&start={start}&hl=vi&gl=vn&pws=0"
                    
                    if url in self.visited_urls:
                        continue
                        
                    self.visited_urls.add(url)
                    
                    # Get a random user agent for each request
                    user_agent = self.get_random_user_agent()
                    
                    # Random delay before each request
                    delay = random.uniform(1.0, 2.0)
                    time.sleep(delay)
                    
                    self.logger.info(f"Queuing search for: '{keyword}' (page {page+1}) with UA: {user_agent[:30]}...")
                    
                    # Create request with Selenium flag
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse,
                        meta={
                            "keyword": keyword,
                            "selenium": True,  # Tell middleware to use Selenium
                            "wait_time": 2,    # Wait 5 seconds for page to load
                        },
                        headers={
                            'User-Agent': user_agent,
                        },
                        dont_filter=True
                    )
            
            # Add a larger delay between batches
            if i + batch_size < len(self.keywords):
                batch_delay = random.uniform(5.0, 7.0)
                self.logger.info(f"Adding delay of {batch_delay:.2f}s between keyword batches...")
                time.sleep(batch_delay)


    def parse(self, response):
        keyword = response.meta["keyword"]
        self.logger.info(f"Received response for: '{keyword}'")
        
        # # Save the HTML response for debugging
        # debug_filename = f"debug_google_{keyword.replace(' ', '_')}.html"
        # with open(debug_filename, 'wb') as f:
        #     f.write(response.body)
        # self.logger.info(f"Saved response to {debug_filename} for debugging")
        
        # Try multiple selectors to find search results
        # Modern Google search results structure (as of March 2025)
        search_results = []

        # Primary attempt - target the MjjYud containers directly
        results = response.xpath("//div[contains(@class, 'MjjYud')]")
        if results:
            self.logger.info(f"Found {len(results)} results")
            search_results = results

        # Fallback approach if no results found
        if not search_results:
            # Look for any search result container with known classes
            fallback_xpath = "//div[contains(@class, 'g') or contains(@class, 'yuRUbf') or contains(@class, 'Ww4FFb')]"
            results = response.xpath(fallback_xpath)
            if results:
                self.logger.info(f"Found {len(results)} results")
                search_results = results

        # Process search results
        for result in search_results:
            # Extract title with more specific XPath based on your HTML example
            title = None
            title_xpaths = [
                ".//h3[contains(@class, 'LC20lb')]/text()",
                ".//h3[@class='LC20lb MBeuO DKV0Md']/text()",  # Very specific to your example
                ".//div[contains(@class, 'yuRUbf')]//h3/text()"
            ]
            
            for xpath in title_xpaths:
                title_text = result.xpath(xpath).get()
                if title_text and title_text.strip():
                    title = title_text.strip()
                    break
            
            # Extract link with more specific XPath
            link = None
            link_xpaths = [
                ".//a[@jsname='UWckNb']/@href",  # Using the jsname attribute from your HTML
                ".//div[contains(@class, 'yuRUbf')]//a/@href",
                ".//cite[contains(@class, 'qLRx3b')]/ancestor::a/@href"
            ]
            
            for xpath in link_xpaths:
                link_url = result.xpath(xpath).get()
                if link_url and link_url.startswith('http'):
                    link = link_url
                    break
            
            if title and link:
                # self.logger.info(f"Found result: {title} - {link}")
                yield {
                    "keyword": keyword,
                    "title": title,
                    "link": link
                }
            else:
                self.logger.warning(f"Incomplete result found, skipping... ")
        
        # If we didn't find any results with our selectors
        if not search_results:
            self.logger.error(f"No search result containers found for keyword: {keyword}")
            self.logger.error("Google may have updated their HTML structure again")