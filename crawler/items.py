import scrapy

class EventItem(scrapy.Item):
    """
    Scrapy Item representing a raw event extracted by a spider.
    This data will be passed to the processing pipeline.
    """
    title = scrapy.Field()          # Event title
    description = scrapy.Field()    # Event description (raw)
    date_text = scrapy.Field()      # Raw date string extracted from the page
    image_url = scrapy.Field()      # URL of the event image
    source_url = scrapy.Field()     # URL of the page where the event was found
    # Add other fields if needed during scraping, e.g., location, raw html, etc.