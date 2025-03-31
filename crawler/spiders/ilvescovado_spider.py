import scrapy
from .base_spider import BaseEventSpider
from ...utils.logger import get_logger

logger = get_logger(__name__)

class IlVescovadoSpider(BaseEventSpider):
    """
    Spider to scrape events from ilvescovado.it.
    """
    name = "ilvescovado"
    allowed_domains = ["ilvescovado.it"]
    start_urls = [
        "https://www.ilvescovado.it/it/eventi-e-spettacoli-38/",
        "https://www.ilvescovado.it/it/notizie-lifestyle-47/"
    ]

    # Selectors (Updated based on provided HTML)
    EVENT_LIST_SELECTOR = 'div.partialChannelArticlesItems' # Selector for each event block on the list page
    EVENT_LINK_SELECTOR = 'h3 a::attr(href)' # Selector for the link to the event detail page (relative to EVENT_LIST_SELECTOR)
    TITLE_SELECTOR = 'h3::text' # Selector for the event title on the detail page
    DESCRIPTION_SELECTOR = 'div:has(img.full) p::text' # Reverted: Selector for paragraphs in the main content div
    DATE_SELECTOR = 'p:contains("Inserito da")::text' # Selector for the paragraph containing date info
    IMAGE_SELECTOR = 'img.full::attr(src)' # Selector for the main event image URL

    # Pagination (Placeholder - needs verification, disabled for now due to item limit)
    # NEXT_PAGE_SELECTOR = 'a.next.page-numbers::attr(href)'

    # Limit items per start URL
    MAX_ITEMS_PER_URL = 15

    def parse(self, response, **kwargs):
        """
        Parses the event listing page.
        Finds links to individual event pages and yields requests to parse them,
        up to MAX_ITEMS_PER_URL.
        Does not follow pagination to enforce the limit per section easily.
        """
        logger.info(f"Parsing event list page: {response.url}")
        events = response.css(self.EVENT_LIST_SELECTOR)
        if not events:
            logger.warning(f"No event blocks found on {response.url} using selector '{self.EVENT_LIST_SELECTOR}'")
            return

        items_yielded = 0
        for event_block in events:
            if items_yielded >= self.MAX_ITEMS_PER_URL:
                logger.info(f"Reached item limit ({self.MAX_ITEMS_PER_URL}) for {response.url}. Stopping.")
                break

            event_link = event_block.css(self.EVENT_LINK_SELECTOR).get()
            if event_link:
                absolute_event_link = response.urljoin(event_link)
                logger.debug(f"Found event link: {absolute_event_link}")
                yield response.follow(absolute_event_link, callback=self.parse_event_details)
                items_yielded += 1
            else:
                # Log if a block is found but doesn't contain the expected link
                logger.warning(f"Could not find event link within block using selector '{self.EVENT_LINK_SELECTOR}' in block: {event_block.get()}")

        logger.info(f"Finished parsing {response.url}, yielded {items_yielded} item requests.")

        # Pagination is disabled to respect MAX_ITEMS_PER_URL per initial page load
        # next_page = response.css(self.NEXT_PAGE_SELECTOR).get()
        # if next_page and items_yielded < self.MAX_ITEMS_PER_URL: # Optional: only paginate if limit not reached
        #     logger.info(f"Following pagination link: {next_page}")
        #     yield response.follow(response.urljoin(next_page), callback=self.parse)
        # else:
        #     logger.info(f"No next page link found or item limit reached on {response.url}")


    def parse_event_details(self, response):
        """
        Parses the details page of a single event from ilvescovado.it.
        Extracts event details using defined selectors and yields an EventItem.
        """
        logger.info(f"Parsing event details page: {response.url}")

        # Use helper from base class or define specific extraction logic here
        # Extract raw data using updated selectors
        title = response.css(self.TITLE_SELECTOR).get()
        description_parts = response.css(self.DESCRIPTION_SELECTOR).getall()
        date_text_raw = response.css(self.DATE_SELECTOR).get()
        image_url_relative = response.css(self.IMAGE_SELECTOR).get()

        # Create the data dictionary
        data = {
            'title': title.strip() if title else None,
            'description': description_parts, # Will be joined later
            'date_text': date_text_raw.strip() if date_text_raw else None,
            'image_url': response.urljoin(image_url_relative) if image_url_relative else None, # Make URL absolute
            'source_url': response.url,
        }

        # Clean up description (Filter out unwanted lines and join the list from .getall())
        raw_description_list = data.get('description', [])
        if raw_description_list:
            # Filter out the date/author line before joining
            filtered_parts = [
                part.strip() for part in raw_description_list
                if part.strip() and "Inserito da" not in part
            ]
            if filtered_parts:
                 data['description'] = " ".join(filtered_parts).strip()
            else:
                 # Log if filtering removed everything (might indicate selector issue)
                 logger.warning(f"Description found but became empty after filtering 'Inserito da' on {response.url}. Original parts: {raw_description_list}")
                 data['description'] = None
        else:
             logger.warning(f"Description parts not found or empty on {response.url} using selector '{self.DESCRIPTION_SELECTOR}'")
             data['description'] = None # Ensure it's None if nothing found


        # Use helper from base class to create the item
        item = self.create_event_item(data)
        if item:
            # Perform specific cleaning/validation for this spider if needed
            if not item.get('title'):
                 logger.warning(f"Title not found or empty on {response.url} using selector '{self.TITLE_SELECTOR}'")

            logger.info(f"Successfully parsed event: {item.get('title', 'N/A')} from {response.url}")
            yield item
        else:
            logger.warning(f"Failed to create item from page: {response.url}")