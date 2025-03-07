import scrapy
import logging
import random
import urllib
import time

class GoogleSpider(scrapy.Spider):
    name = "GoogleSpider" 
    
    def __init__(self, keywords=None, results_per_keyword=20, max_pages=10, *args, **kwargs):
        """
        Initialize spider with keywords provided externally
        
        Args:
            keywords (list): List of keywords to search for
            results_per_keyword (int): Number of results to fetch per keyword
            max_pages (int): Maximum number of pages to crawl per keyword
        """
        super(GoogleSpider, self).__init__(*args, **kwargs)
        self.keywords = keywords 
        self.results_per_keyword = int(results_per_keyword)  # Ensure it's an integer
        self.max_pages = int(max_pages)  # Ensure it's an integer
        
        self.logger.info(f"Spider initialized with {len(self.keywords)} keywords")
        self.logger.info(f"Target: {self.results_per_keyword} results per keyword, max {self.max_pages} pages per keyword")
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15'
        ]

        # Dictionary to track count of results per keyword
        self.results_count = {keyword: 0 for keyword in self.keywords}
        
        # Track already visited keywords to avoid duplicates
        self.visited_urls = set()
    
    def get_random_user_agent(self):
        """Get a random user agent string"""
        return random.choice(self.user_agents)
    
    def start_requests(self):
        """Generate initial search requests for each keyword (first page only)"""
        self.logger.info(f"Starting requests for keywords: {self.keywords}")
        
        # Group keywords into batches and add delays between batches
        batch_size = 5  # Process keywords in small batches
        
        for i in range(0, len(self.keywords), batch_size):
            batch = self.keywords[i:i+batch_size]
            
            for keyword in batch:
                # Start with page 0 for each keyword
                encoded_keyword = urllib.parse.quote(keyword)
                url = f"https://www.google.com/search?q={encoded_keyword}&start=0&hl=vi&gl=vn&pws=0"
                
                # Use random user agent for each request
                user_agent = self.get_random_user_agent()
                
                self.logger.info(f"Starting search for: '{keyword}'")
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    meta={
                        "keyword": keyword,
                        "page": 0,
                        "selenium": True,  # Use Selenium middleware
                        "dont_merge_cookies": True,
                        "wait_time": 3  # Wait 3 seconds for the page to load
                    },
                    headers={"User-Agent": user_agent}
                )
                
                time.sleep(2)  # Small delay between keywords in a batch
            
            # Add a larger delay between batches
            if i + batch_size < len(self.keywords):
                time.sleep(5)  # 5-second delay between batches


    def parse(self, response):
        keyword = response.meta["keyword"]
        current_page = response.meta["page"]
        self.logger.info(f"Processing page {current_page+1} for keyword: '{keyword}'")
        
        # Try multiple selectors to find search results
        # Modern Google search results structure (as of March 2025)
        search_results = []

        # Primary attempt - target the MjjYud containers directly
        results = response.xpath("//div[contains(@class, 'MjjYud')]")
        if results:
            self.logger.info(f"Found {len(results)} raw results on page {current_page+1} for '{keyword}'")
            search_results = results

        # Fallback approach if no results found
        if not search_results:
            # Look for any search result container with known classes
            fallback_xpath = "//div[contains(@class, 'g') or contains(@class, 'yuRUbf') or contains(@class, 'Ww4FFb')]"
            results = response.xpath(fallback_xpath)
            if results:
                self.logger.info(f"Using fallback selector - found {len(results)} results on page {current_page+1}")
                search_results = results

        # Process search results
        results_on_page = 0
        for result in search_results:
            # Extract title with more specific XPath
            title = None
            title_xpaths = [
                ".//h3[contains(@class, 'LC20lb')]/text()",
                ".//h3[@class='LC20lb MBeuO DKV0Md']/text()",
                ".//div[contains(@class, 'yuRUbf')]//h3/text()"
            ]
            
            for xpath in title_xpaths:
                title_extract = result.xpath(xpath).get()
                if title_extract:
                    title = title_extract.strip()
                    break
            
            # Extract link with more specific XPath
            link = None
            link_xpaths = [
                ".//a[h3]/@href",
                ".//div[contains(@class, 'yuRUbf')]//a/@href",
                ".//div//a[@jsname='UWckNb']/@href"
            ]
            
            for xpath in link_xpaths:
                link_extract = result.xpath(xpath).get()
                if link_extract:
                    link = link_extract
                    break
            
            # Only yield if both title and link were found and link not already visited
            if title and link and link not in self.visited_urls:
                # Skip non-http links or google result page links
                if not link.startswith('http') or 'google.com/search' in link:
                    continue
                    
                # Mark as visited
                self.visited_urls.add(link)
                
                # Yield the result
                item = {
                    'keyword': keyword,
                    'title': title,
                    'link': link
                }
                results_on_page += 1
                self.results_count[keyword] += 1
                yield item
        
        self.logger.info(f"Extracted {results_on_page} valid results from page {current_page+1} for '{keyword}'")
        self.logger.info(f"Total results for '{keyword}': {self.results_count[keyword]}/{self.results_per_keyword}")
        
        # Check if we need to fetch the next page for this keyword
        if (self.results_count[keyword] < self.results_per_keyword and 
            current_page < self.max_pages - 1 and 
            results_on_page > 0):  # Stop if current page had no results
            
            next_page = current_page + 1
            encoded_keyword = urllib.parse.quote(keyword)
            next_url = f"https://www.google.com/search?q={encoded_keyword}&start={next_page*10}&hl=vi&gl=vn&pws=0"
            
            self.logger.info(f"Moving to page {next_page+1} for '{keyword}' to get more results")
            
            # Use random user agent for each request
            user_agent = self.get_random_user_agent()
            
            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                meta={
                    "keyword": keyword,
                    "page": next_page,
                    "selenium": True,
                    "dont_merge_cookies": True,
                    "wait_time": 3
                },
                headers={"User-Agent": user_agent}
            )
        else:
            if self.results_count[keyword] >= self.results_per_keyword:
                self.logger.info(f"✓ Reached target of {self.results_per_keyword} results for '{keyword}'")
            elif current_page >= self.max_pages - 1:
                self.logger.warning(f"⚠ Reached max page limit ({self.max_pages} pages) for '{keyword}' with only {self.results_count[keyword]} results")
            elif results_on_page == 0:
                self.logger.warning(f"⚠ No more results found for '{keyword}' after {self.results_count[keyword]} results")