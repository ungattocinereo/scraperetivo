# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from itemadapter import ItemAdapter
from ..utils.logger import get_logger
from ..processor.event_processor import EventProcessor
from ..storage.event_storage import EventStorage
from scrapy.exceptions import DropItem # Import DropItem for skipping

logger = get_logger(__name__)

class TouristEventsPipeline:
    """
    Placeholder pipeline.
    This pipeline will eventually pass the scraped item to the Event Processor.
    This pipeline processes scraped items, sends them to the EventProcessor,
    and saves the resulting Event object using EventStorage.
    """
    def __init__(self):
        self.processor = None
        self.storage = None

    def open_spider(self, spider):
        logger.info(f"Opening pipeline for spider: {spider.name}")
        try:
            # Initialize processor and storage here
            self.processor = EventProcessor()
            self.storage = EventStorage() # Use default path or get from settings
            logger.info("EventProcessor and EventStorage initialized in pipeline.")
        except Exception as e:
            logger.critical(f"Failed to initialize processor/storage in pipeline: {e}", exc_info=True)
            # Depending on severity, you might want to stop the spider
            # raise NotConfigured("Pipeline could not be initialized.")
            self.processor = None # Ensure it's None if failed
            self.storage = None

    def close_spider(self, spider):
        logger.info(f"Closing pipeline for spider: {spider.name}")
        # No explicit cleanup needed for processor/storage in this implementation

    def process_item(self, item, spider):
        """
        Processes a single item scraped by the spider.
        Processes a scraped item using EventProcessor and saves it via EventStorage.
        """
        if not self.processor or not self.storage:
            logger.error("Processor or Storage not initialized. Skipping item processing.")
            return item # Or raise DropItem

        adapter = ItemAdapter(item)
        logger.debug(f"Pipeline received item from {spider.name}: {adapter.get('title')}")

        try:
            # Process the raw item
            processed_event = self.processor.process_event(item)

            if processed_event:
                # Save the processed event
                logger.debug(f"Attempting to save processed event: {processed_event.title}")
                self.storage.save_events([processed_event]) # save_events expects a list
            else:
                logger.warning(f"Event processing returned None for item: {adapter.get('source_url')}. Item might be skipped or invalid.")
                # Optionally drop the item if processing fails consistently
                # raise DropItem(f"Failed to process event: {adapter.get('source_url')}")

        except Exception as e:
            logger.error(f"Error during pipeline processing for item {adapter.get('source_url')}: {e}", exc_info=True)
            # Depending on the error, you might drop the item or let it pass
            # raise DropItem(f"Pipeline error: {e}")

        return item # Return original item (standard practice)