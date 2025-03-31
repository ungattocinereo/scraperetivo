import scrapy
from abc import ABC, abstractmethod
from ..items import EventItem  # Assuming EventItem will be defined in items.py
from ...utils.logger import get_logger

logger = get_logger(__name__)

class BaseEventSpider(scrapy.Spider, ABC):
    """
    Abstract base class for event spiders.
    Provides common structure and requires subclasses to implement parsing logic.
    """
    name = "base_event_spider" # Default name, should be overridden by subclasses
    allowed_domains = [] # Should be overridden by subclasses
    start_urls = [] # Should be overridden by subclasses

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: Load keywords and event types from config for filtering

    def parse(self, response, **kwargs):
        """
        Main parsing method. It should yield requests for detail pages or EventItems.
        Subclasses might override this or implement more specific parsing methods.
        """
        logger.info(f"Parsing page: {response.url}")
        # Example: Find links to individual event pages
        # event_links = response.css('a.event-link::attr(href)').getall()
        # for link in event_links:
        #     yield response.follow(link, callback=self.parse_event_details)
        #
        # Or directly extract items if they are on the listing page
        # events = self.extract_events_from_list(response)
        # for event_data in events:
        #     yield self.create_event_item(event_data)
        raise NotImplementedError(f"{self.__class__.__name__} must implement the 'parse' method.")


    @abstractmethod
    def parse_event_details(self, response):
        """
        Parses the details page of a single event.
        This method MUST be implemented by subclasses.
        It should extract event details and yield an EventItem.
        """
        pass

    def extract_event_data(self, response):
        """
        Helper method to extract common event data fields.
        Subclasses can override or extend this.
        """
        # Example implementation - subclasses should provide specific selectors
        data = {
            'title': response.css('h1.event-title::text').get(),
            'description': response.css('div.event-description ::text').getall(),
            'date_text': response.css('span.event-date::text').get(), # Raw date text
            'image_url': response.css('img.event-image::attr(src)').get(),
            'source_url': response.url,
        }
        # Clean up description
        if data.get('description'):
            data['description'] = " ".join(data['description']).strip()
        return data

    def create_event_item(self, data):
        """
        Creates and populates an EventItem from extracted data.
        Includes basic filtering logic (can be expanded).
        """
        # TODO: Add filtering based on keywords and event types from config
        item = EventItem()
        # Ensure strip() is only called on strings, handle None values gracefully
        title_raw = data.get('title')
        item['title'] = title_raw.strip() if title_raw else ''

        description_raw = data.get('description')
        item['description'] = description_raw.strip() if description_raw else ''

        date_text_raw = data.get('date_text')
        item['date_text'] = date_text_raw.strip() if date_text_raw else '' # Store raw date text for later processing

        image_url_raw = data.get('image_url')
        item['image_url'] = image_url_raw.strip() if image_url_raw else ''

        source_url_raw = data.get('source_url')
        item['source_url'] = source_url_raw.strip() if source_url_raw else ''

        if not item['title'] or not item['source_url']:
            logger.warning(f"Skipping item due to missing title or source URL: {item['source_url']}")
            return None # Skip items missing essential info

        logger.info(f"Extracted basic data for: {item['title']}")
        return item

    def closed(self, reason):
        logger.info(f"Spider {self.name} finished scraping. Reason: {reason}")