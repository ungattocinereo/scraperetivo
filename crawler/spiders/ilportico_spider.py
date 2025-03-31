import scrapy
from .base_spider import BaseEventSpider
from ...utils.logger import get_logger

logger = get_logger(__name__)

class IlPorticoSpider(BaseEventSpider):
    """
    Spider to scrape events from ilportico.it.
    NOTE: Selectors are placeholders and need to be defined based on website structure.
    """
    name = "ilportico"
    allowed_domains = ["ilportico.it"]
    start_urls = [
        "https://www.ilportico.it/it/eventi-e-spettacoli-38/"
    ]

    # --- Selectors based on ilvescovado/booble structure ---
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
        # Reset counter if it's a new start_url being processed
        if response.url in self.start_urls:
             self._items_scraped_count = 0

        event_links = response.css(self.EVENT_LIST_SELECTOR).css(self.EVENT_LINK_SELECTOR).getall()

        if not event_links:
            logger.warning(f"No event links found on {response.url} using selector '{self.EVENT_LIST_SELECTOR} {self.EVENT_LINK_SELECTOR}'")
            return

        logger.info(f"Found {len(event_links)} potential event links on {response.url}")

        for link in event_links:
            if self.MAX_ITEMS_PER_URL and self._items_scraped_count >= self.MAX_ITEMS_PER_URL:
                logger.info(f"Reached max items limit ({self.MAX_ITEMS_PER_URL}) for {self.name} on {response.url}. Stopping this list page.")
                return # Stop processing links for this specific start_url if limit is reached

            absolute_url = response.urljoin(link)
            yield scrapy.Request(absolute_url, callback=self.parse_event_details)
            self._items_scraped_count += 1 # Increment counter after yielding request

        # Handle pagination if limit not reached for this start_url
        if not self.MAX_ITEMS_PER_URL or self._items_scraped_count < self.MAX_ITEMS_PER_URL:
            next_page = response.css(self.NEXT_PAGE_SELECTOR).get()
            if next_page:
                logger.info(f"Found next page link: {next_page}")
                yield response.follow(next_page, callback=self.parse)
            else:
                logger.info(f"No next page link found on {response.url} using selector '{self.NEXT_PAGE_SELECTOR}'")

    def parse_event_details(self, response):
        """
        Parses the details page of a single event.
        Attempts to extract data from JSON-LD first, falls back to CSS selectors.
        """
        logger.info(f"Attempting to parse event details page: {response.url}")
        import json # Import json module

        data = None
        parsed_via_json_ld = False

        # --- Attempt 1: Parse JSON-LD ---
        try:
            json_ld_str = response.xpath('//script[@type="application/ld+json"]/text()').get()
            if json_ld_str:
                logger.debug(f"Found JSON-LD script on {response.url}")
                json_data = None
                try:
                    potential_data = json.loads(json_ld_str)
                    if isinstance(potential_data, list):
                        for item_obj in potential_data:
                            if isinstance(item_obj, dict) and item_obj.get('@type') in ['Article', 'Event', 'NewsArticle']:
                                json_data = item_obj
                                break
                    elif isinstance(potential_data, dict) and potential_data.get('@type') in ['Article', 'Event', 'NewsArticle']:
                        json_data = potential_data

                    if json_data:
                        title = json_data.get('headline')
                        description = json_data.get('articleBody') or json_data.get('description')
                        date_text = json_data.get('datePublished')
                        image_data = json_data.get('image')
                        image_url = image_data.get('url') if isinstance(image_data, dict) else None

                        data = {
                            'title': title,
                            'description': description,
                            'date_text': date_text,
                            'image_url': response.urljoin(image_url) if image_url else None,
                            'source_url': response.url,
                        }
                        parsed_via_json_ld = True
                        logger.info(f"Successfully extracted data via JSON-LD for: {response.url}")
                    else:
                         logger.warning(f"JSON-LD found but no suitable Article/Event object on {response.url}")

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to decode JSON-LD on {response.url}: {e}. Falling back to CSS.")
            else:
                logger.info(f"JSON-LD script not found on {response.url}. Falling back to CSS selectors.")

        except Exception as e:
            logger.error(f"Error processing JSON-LD on {response.url}: {e}. Falling back to CSS.", exc_info=True)

        # --- Attempt 2: Parse using CSS selectors (Fallback) ---
        if not parsed_via_json_ld:
            logger.info(f"Parsing event details page using CSS selectors: {response.url}")
            title = response.css(self.TITLE_SELECTOR).get()
            description_parts = response.css(self.DESCRIPTION_SELECTOR).getall()
            date_text_raw = response.css(self.DATE_SELECTOR).get()
            image_url_relative = response.css(self.IMAGE_SELECTOR).get()

            # Clean description parts
            cleaned_description = None
            if description_parts:
                filtered_parts = [part.strip() for part in description_parts if part.strip() and "Inserito da" not in part]
                if filtered_parts:
                    cleaned_description = " ".join(filtered_parts).strip()
                else:
                    logger.warning(f"CSS Description found but became empty after filtering on {response.url}.")
            else:
                logger.warning(f"CSS Description parts not found or empty on {response.url} using selector '{self.DESCRIPTION_SELECTOR}'")

            data = {
                'title': title.strip() if title else None,
                'description': cleaned_description,
                'date_text': date_text_raw.strip() if date_text_raw else None,
                'image_url': response.urljoin(image_url_relative) if image_url_relative else None,
                'source_url': response.url,
            }

        # --- Create Item ---
        if data:
            item = self.create_event_item(data)
            if item:
                log_prefix = "JSON-LD" if parsed_via_json_ld else "CSS"
                logger.info(f"Successfully parsed event via {log_prefix}: {item.get('title', 'N/A')} from {response.url}")
                yield item
            else:
                logger.warning(f"Failed to create item from page: {response.url} (data: {data})")
        else:
             logger.error(f"Could not extract data using JSON-LD or CSS for page: {response.url}")
