import os
import re
import logging
import random
import time
import trafilatura

from copy import deepcopy
from trafilatura.settings import use_config

from utils.user_agents import get_user_agent_list
from utils.logger import silence_trafilatura_log

class ContentScraper:
    """
    Content scraper that uses Trafilatura library to scrape content from a URL. 
    """
    
    def __init__(self, logger=None):
        """Initialize the content scraper"""
        self.logger = logger or logging.getLogger(self.__class__.__name__)

        # Load custom Trafilatura configuration
        config_path = os.path.join(os.path.dirname(__file__), 'setting.cfg')
        self.custom_config = use_config(config_path)
        self.logger.debug(f"Loaded Trafilatura config: {self.custom_config}")

        silence_trafilatura_log()
    
    def scrape(self, search_result):
        """
        Scrape content from a specific URL using Trafilatura's bare_extraction.
        
        Args:
            url (str): The URL to scrape
            keyword (str): The keyword that found this URL
            title (str): The title from search result (fallback)
            description (str): The description from search result (fallback)
            
        Returns:
            dict: Scraped content with standardized fields
        """
        url = search_result['link']
        keyword = search_result['keyword']
        title = search_result['title']
        description = search_result.get('description', '')
        
        self.logger.info(f"Scraping content from: {url}")
        
        try:  
            # Use trafilatura's built-in fetch function
            downloaded = trafilatura.fetch_url(
                url,
                config=self.custom_config,
            )
            
            if downloaded is None:
                self.logger.error(f"Failed to download content from {url}")
                return self._create_fallback_result(url, keyword, title, description, 
                                                  "Failed to download content")
            
            # Extract rich content using bare_extraction
            extracted = trafilatura.bare_extraction(
                downloaded, 
                include_images=True, 
                with_metadata=True,
                config=self.custom_config
            )
            
            if not extracted:
                self.logger.warning(f"Trafilatura couldn't extract content from {url}")
                return self._create_fallback_result(url, keyword, title, description, 
                                                  "No content could be extracted")
            
            # Process extracted content
            return self._process_extracted_content(extracted, url, keyword, title, description)
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return self._create_fallback_result(url, keyword, title, description, 
                                              f"Error extracting content")
    
    def _process_extracted_content(self, extracted, url, keyword, search_title, search_description):
        """Process the extracted content and return standardized dict"""
        try:
            # Get content text - this is the main article content
            content = extracted.text if extracted.text else ""
            
            # Get title from metadata, use search result title as fallback
            page_title = extracted.title if extracted.title else search_title
            
            # Get description from metadata, use search result description as fallback
            page_description = extracted.description if extracted.description else search_description
            
            # Get date if available
            page_date = extracted.date if extracted.date else ""
            
            # Get main image if available
            main_image = extracted.image if extracted.image else ""
            # Convert main image to absolute URL if needed
            if main_image:
                main_image = self._make_absolute_url(url, main_image)

            # Get author if available
            author = extracted.author if extracted.author else ""
            
            # Get hostname/site data
            hostname = extracted.hostname if extracted.hostname else ""
            sitename = extracted.sitename if extracted.sitename else ""

            # Extract images from content
            content_cleaned, images = self._extract_images_from_content(content, url)
            
            self.logger.info(f"Successfully extracted content from {url}")
            
            # Return standardized format
            return {
                'title': page_title,
                'url': url,
                'description': page_description,
                'content': content_cleaned,
                'date': page_date,
                'main_image': main_image,
                'images': images,
                'author': author,
                'site': sitename or hostname,
                'keyword': keyword
            }
            
        except Exception as e:
            self.logger.error(f"Error processing extracted content: {str(e)}")
            return self._create_fallback_result(url, keyword, search_title, search_description,
                                              f"Error processing content")
    
    def _extract_images_from_content(self, content, base_url):
        """
        Extract images from content and replace with placeholders
        
        Args:
            content (str): Content text with possible image references
            base_url (str): The base URL of the page for resolving relative URLs
            
        Returns:
            tuple: (content_with_placeholders, list_of_image_urls)
        """
        if not content:
            return "", []
            
        images = []
        base_domain = self._get_base_domain(base_url)
        
        # Process Markdown images with both absolute and relative URLs
        # Format: ![alt text](image_path)
        markdown_pattern = r'!\[(.*?)\]\(([^)]+)\)'
        
        def replace_markdown_image(match):
            img_path = match.group(2)
            # Convert relative URL to absolute URL if needed
            img_url = self._make_absolute_url(base_url, img_path)
            
            if img_url not in images:
                images.append(img_url)
            img_index = images.index(img_url) + 1
            return f"[IMAGE-{img_index}]"
        
        # Replace markdown images with placeholders
        content_with_placeholders = re.sub(markdown_pattern, replace_markdown_image, content)
        
        # Look for any remaining absolute URLs that might be images
        url_pattern = r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp)[^\s]*'
        
        def replace_url_with_placeholder(match):
            img_url = match.group(0)
            if img_url not in images:
                images.append(img_url)
            img_index = images.index(img_url) + 1
            return f"[IMAGE-{img_index}]"
        
        # Replace absolute image URLs with placeholders
        content_with_placeholders = re.sub(url_pattern, replace_url_with_placeholder, content_with_placeholders)
        
        return content_with_placeholders, images

    def _make_absolute_url(self, base_url, relative_url):
        """Convert a relative URL to an absolute URL"""
        if not relative_url:
            return ""
            
        # If it's already an absolute URL, return it as is
        if relative_url.startswith(('http://', 'https://')):
            return relative_url
            
        # Parse the base URL to get components
        from urllib.parse import urlparse, urljoin
        
        # Use urljoin which properly handles all cases of relative URLs
        absolute_url = urljoin(base_url, relative_url)
        return absolute_url

    def _get_base_domain(self, url):
        """Extract the base domain from a URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _create_fallback_result(self, url, keyword, title, description, error_message):
        """Create a fallback result with error message"""
        return {
            'title': title,
            'url': url,
            'description': description,
            'content': error_message,
            'date': "",
            'main_image': "",
            'images': [],
            'author': "",
            'site': "",
            'keyword': keyword
        }