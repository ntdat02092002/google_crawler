BOT_NAME = 'google_crawler'

SPIDER_MODULES = ['google_crawler.spiders']
NEWSPIDER_MODULE = 'google_crawler.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 2

# Enable and configure the AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60