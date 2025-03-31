import scrapy
from .base_spider import BaseEventSpider
from ...utils.logger import get_logger

logger = get_logger(__name__)

class AmalfiNewsSpider(BaseEventSpider):
    """
    Spider to scrape events from amalfinews.it.
    NOTE: Selectors are placeholders and need to be defined based on website structure.
    """
    name = "amalfinews"
    allowed_domains = ["amalfinews.it"]
    start_urls = [
        "https://www.amalfinews.it/it/eventi-e-spettacoli-38/"
    ]

    # --- Selectors based on ilvescovado/booble/ilportico/maiorinews structure ---
    EVENT_LIST_SELECTOR = 'div.partialChannelArticlesItems' # Selector for the container of event blocks
    EVENT_LINK_SELECTOR = 'h3 a::attr(href)' # Selector for the link within each block
    TITLE_SELECTOR = 'h1::text' # Selector for the main title on the detail page (Guess)
    DESCRIPTION_SELECTOR = 'div:has(img.full) p::text' # Selector for paragraphs in the main content div (Detail page)
    DATE_SELECTOR = 'p:contains("Inserito da")::text' # Selector for the paragraph containing date info (Detail page)
    IMAGE_SELECTOR = 'img.full::attr(src)' # Selector for the main event image URL (Detail page)
    NEXT_PAGE_SELECTOR = 'a.next.page-numbers::attr(href)' # Selector for the pagination link (List page)
    # --- END PLACEHOLDER SELECTORS ---

    # Limit items per start URL (optional, adjust as needed)
    MAX_ITEMS_PER_URL = 15
    _items_scraped_count = 0 # Counter for scraped items

    def parse(self, response, **kwargs):
        """
        Parses the event list page.
        Finds links to individual event pages and yields requests for them.
        Also handles pagination.
        """
        logger.info(f"Parsing event list page: {response.url}")
        event_links = response.css(self.EVENT_LIST_SELECTOR).css(self.EVENT_LINK_SELECTOR).getall()

        if not event_links:
            logger.warning(f"No event links found on {response.url} using selector '{self.EVENT_LIST_SELECTOR} {self.EVENT_LINK_SELECTOR}'")
            return

        logger.info(f"Found {len(event_links)} potential event links on {response.url}")

        for link in event_links:
            if self.MAX_ITEMS_PER_URL and self._items_scraped_count >= self.MAX_ITEMS_PER_URL:
                logger.info(f"Reached max items limit ({self.MAX_ITEMS_PER_URL}) for {self.name}. Stopping.")
                return # Stop processing links if limit is reached

            absolute_url = response.urljoin(link)
            yield scrapy.Request(absolute_url, callback=self.parse_event_details)
            self._items_scraped_count += 1 # Increment counter after yielding request

        # Handle pagination if limit not reached
        if not self.MAX_ITEMS_PER_URL or self._items_scraped_count < self.MAX_ITEMS_PER_URL:
            next_page = response.css(self.NEXT_PAGE_SELECTOR).get()
            if next_page:
                logger.info(f"Found next page link: {next_page}")
                yield response.follow(next_page, callback=self.parse)
            else:
                logger.info(f"No next page link found on {response.url} using selector '{self.NEXT_PAGE_SELECTOR}'")


    def parse_event_details(self, response):
        """
        Parses the details page of a single event by extracting data
        from the JSON-LD script block.
        """
        logger.info(f"Parsing event details page using JSON-LD: {response.url}")
        import json # Import json module

        # Extract JSON-LD data
        try:
            json_ld_str = response.xpath('//script[@type="application/ld+json"]/text()').get()
            if not json_ld_str:
                logger.error(f"JSON-LD script not found on {response.url}")
                return

            # The script might contain multiple JSON objects or be wrapped in an array
            # Try to find the relevant 'Article' or 'Event' object
            json_data = None
            try:
                # Attempt to parse directly if it's a single object
                potential_data = json.loads(json_ld_str)
                if isinstance(potential_data, list):
                    # If it's a list, search for the main Article/Event
                    for item in potential_data:
                        if isinstance(item, dict) and item.get('@type') in ['Article', 'Event', 'NewsArticle']:
                            json_data = item
                            break
                elif isinstance(potential_data, dict) and potential_data.get('@type') in ['Article', 'Event', 'NewsArticle']:
                    json_data = potential_data

            except json.JSONDecodeError as e:
                 logger.error(f"Failed to decode JSON-LD on {response.url}: {e}. Content: {json_ld_str[:500]}...")
                 return # Cannot proceed without valid JSON

            if not json_data:
                logger.error(f"Could not find relevant Article/Event object in JSON-LD on {response.url}")
                return

            # Extract data from JSON-LD fields
            title = json_data.get('headline')
            description = json_data.get('articleBody') # Or description if @type is Event
            date_text = json_data.get('datePublished') # Use datePublished
            image_data = json_data.get('image')
            image_url = image_data.get('url') if isinstance(image_data, dict) else None

            # Create the data dictionary for the item
            data = {
                'title': title,
                'description': description,
                'date_text': date_text, # Pass the date string directly
                'image_url': response.urljoin(image_url) if image_url else None, # Make URL absolute
                'source_url': response.url,
            }

            # Use helper from base class to create the item
            item = self.create_event_item(data)
            if item:
                logger.info(f"Successfully parsed event via JSON-LD: {item.get('title', 'N/A')} from {response.url}")
                yield item
            else:
                # create_event_item logs warnings if title/source_url are missing
                logger.warning(f"Failed to create item from JSON-LD on page: {response.url}")

        except Exception as e:
            logger.error(f"Error parsing JSON-LD on {response.url}: {e}", exc_info=True)
