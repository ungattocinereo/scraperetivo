import scrapy
from .base_spider import BaseEventSpider
from ...utils.logger import get_logger

logger = get_logger(__name__)

class SalernoTodaySpider(BaseEventSpider):
    """
    Spider to scrape events from salernotoday.it.
    """
    name = "salernotoday"
    allowed_domains = ["salernotoday.it"]
    # Example start URL - replace with actual event listing page(s)
    start_urls = ["https://www.salernotoday.it/eventi/"]

    # Selectors (Placeholders - need verification)
    EVENT_LIST_SELECTOR = 'article.c-card' # Updated selector for each event block
    EVENT_LINK_SELECTOR = 'div.c-card__content a.o-link-text::attr(href)' # Updated selector for the event detail link
    TITLE_SELECTOR = 'h1.p-entry__title::text' # Detail page title selector
    DESCRIPTION_SELECTOR = 'div.p-entry__content p::text' # Detail page description selector
    DATE_SELECTOR = 'time.p-entry__date::attr(datetime)' # Detail page date selector
    IMAGE_SELECTOR = 'figure.p-entry__featured-media img::attr(src)' # Detail page image selector

    # Pagination (Updated - needs verification on live site)
    NEXT_PAGE_SELECTOR = 'a.c-pagination__arrow--next::attr(href)'

    def parse(self, response, **kwargs):
        """
        Parses the event listing page for salernotoday.it.
        """
        logger.info(f"Parsing event list page: {response.url}")
        events = response.css(self.EVENT_LIST_SELECTOR)
        if not events:
            logger.warning(f"No event blocks found on {response.url} using selector '{self.EVENT_LIST_SELECTOR}'")
            return

        for event_block in events:
            # SalernoToday might have full details on the list page or require following a link.
            # This example assumes following a link. Adjust if necessary.
            event_link = event_block.css(self.EVENT_LINK_SELECTOR).get()
            if event_link:
                # Ensure the link is absolute
                absolute_event_link = response.urljoin(event_link)
                logger.debug(f"Found event link: {absolute_event_link}")
                yield response.follow(absolute_event_link, callback=self.parse_event_details)
            else:
                # If details are on the list page, parse them directly here
                # data = self.extract_event_data_from_block(event_block, response.url)
                # item = self.create_event_item(data)
                # if item: yield item
                logger.warning(f"Could not find event link within block: {event_block.get()}")


        # Follow pagination
        next_page = response.css(self.NEXT_PAGE_SELECTOR).get()
        if next_page:
            absolute_next_page = response.urljoin(next_page)
            logger.info(f"Following pagination link: {absolute_next_page}")
            yield response.follow(absolute_next_page, callback=self.parse)
        else:
            logger.info(f"No next page link found on {response.url}")

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
            # Look for JSON-LD within script tags
            # Note: CityNews sites sometimes have multiple JSON-LD blocks
            json_ld_scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
            json_data = None
            if json_ld_scripts:
                logger.debug(f"Found {len(json_ld_scripts)} JSON-LD script(s) on {response.url}")
                for script_content in json_ld_scripts:
                    try:
                        potential_data = json.loads(script_content)
                        # Handle case where JSON-LD is a list of objects
                        if isinstance(potential_data, list):
                            for item_obj in potential_data:
                                if isinstance(item_obj, dict) and item_obj.get('@type') in ['Article', 'Event', 'NewsArticle']:
                                    json_data = item_obj # Found a relevant object
                                    break # Use the first relevant one found in the list
                        # Handle case where JSON-LD is a single object
                        elif isinstance(potential_data, dict) and potential_data.get('@type') in ['Article', 'Event', 'NewsArticle']:
                            json_data = potential_data # Found a relevant object

                        if json_data: # If we found a relevant object in this script, stop searching
                            break

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to decode one JSON-LD script on {response.url}: {e}. Trying next script if available.")
                        continue # Try the next script tag if decoding fails

                if json_data:
                    title = json_data.get('headline')
                    description = json_data.get('articleBody') or json_data.get('description')
                    date_text = json_data.get('datePublished')
                    image_data = json_data.get('image')
                    # Image might be a dict or a list of dicts
                    image_url = None
                    if isinstance(image_data, dict):
                        image_url = image_data.get('url')
                    elif isinstance(image_data, list) and image_data:
                         if isinstance(image_data[0], dict):
                              image_url = image_data[0].get('url') # Take the first image if it's a list

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

            # Clean up description
            cleaned_description = None
            if description_parts:
                cleaned_description = " ".join(part.strip() for part in description_parts if part.strip()).strip()
                if not cleaned_description:
                     logger.warning(f"CSS Description found but became empty after cleaning on {response.url}.")
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
                # Log title only if found
                title_log = item.get('title')
                if not title_log and not parsed_via_json_ld: # Log CSS title failure specifically
                     logger.warning(f"Title not found via CSS on {response.url} using selector '{self.TITLE_SELECTOR}'")
                elif not title_log and parsed_via_json_ld: # Log JSON-LD title failure specifically
                     logger.warning(f"Title (headline) not found via JSON-LD on {response.url}")

                logger.info(f"Successfully parsed event via {log_prefix}: {title_log or 'N/A'} from {response.url}")
                yield item
            else:
                # create_event_item logs warnings if title/source_url are missing after cleaning
                logger.warning(f"Failed to create item from page: {response.url} (data extracted: {data})")
        else:
             logger.error(f"Could not extract data using JSON-LD or CSS for page: {response.url}")
    # Optional: If details are on the list page, implement this
    # def extract_event_data_from_block(self, block, list_url):
    #     """ Extracts event data directly from a block on the listing page. """
    #     data = {
    #         'title': block.css('h3 a::text').get(),
    #         'description': block.css('div.description ::text').getall(),
    #         'date_text': block.css('span.date::text').get(),
    #         'image_url': block.css('img::attr(src)').get(),
    #         'source_url': block.css('h3 a::attr(href)').get(), # Link to details or #
    #     }
    #     # Clean description, make URLs absolute etc.
    #     if data.get('source_url'):
    #         data['source_url'] = urljoin(list_url, data['source_url'])
    #     else:
    #         data['source_url'] = list_url # Fallback if no specific link
    #     # ... more cleaning ...
    #     return data