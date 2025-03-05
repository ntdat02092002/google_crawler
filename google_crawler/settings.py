import os
from importlib import import_module

# Basic Scrapy settings
BOT_NAME = 'google_crawler'
SPIDER_MODULES = ['google_crawler.spiders']
NEWSPIDER_MODULE = 'google_crawler.spiders'

# Scrapy behavior settings
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 4
CONCURRENT_REQUESTS = 1
COOKIES_ENABLED = True
DOWNLOAD_TIMEOUT = 60
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500, 502, 503, 504, 403, 408, 429]

# Output encoding
FEED_EXPORT_ENCODING = 'utf-8'

# Turn off headless mode to allow user to solve CAPTCHAs
SELENIUM_HEADLESS = False
SELENIUM_DRIVER_WAIT_TIME = 10

# Tell scrapy-selenium to use our factory function
SELENIUM_DRIVER_FACTORY = 'utils.selenium_utils.selenium_driver_factory'

# Enable the middleware
DOWNLOADER_MIDDLEWARES = {
    'google_crawler.middlewares.SeleniumMiddleware': 800,
    'scrapy_selenium.SeleniumMiddleware': None,  # Disable the original
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'selenium': {'level': 'WARNING'},
        'urllib3': {'level': 'WARNING'},
        'selenium.webdriver.remote': {'level': 'WARNING'},
        'selenium.webdriver.chromium': {'level': 'WARNING'},
        'scrapy.core.engine': {'level': 'INFO'},
        'scrapy.middleware': {'level': 'WARNING'},
        'scrapy.extensions': {'level': 'WARNING'},
        'scrapy.utils.log': {'level': 'WARNING'},
    }
}