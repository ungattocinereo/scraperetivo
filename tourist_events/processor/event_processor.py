from .openai_client import OpenAIClient
from .date_extractor import DateExtractor # To be created
from ..storage.models import Event
from ..utils.logger import get_logger
from itemadapter import ItemAdapter

logger = get_logger(__name__)

class EventProcessor:
    """
    Processes raw event data scraped by the spiders.
    It cleans data, uses OpenAI for enrichment (translation, summary, type),
    extracts dates, and formats the final Event object.
    """
    def __init__(self):
        try:
            self.openai_client = OpenAIClient()
        except ValueError as e:
            logger.error(f"Failed to initialize OpenAIClient: {e}. Event processing might be limited.")
            self.openai_client = None # Allow processor to run without OpenAI for basic tasks

        self.date_extractor = DateExtractor() # Initialize date extractor
        logger.info("EventProcessor initialized.")

    def process_event(self, raw_event_item) -> Event | None:
        """
        Takes a raw event item (from Scrapy pipeline) and processes it
        into a structured Event object.
        """
        adapter = ItemAdapter(raw_event_item)
        source_url = adapter.get('source_url', 'Unknown Source')
        logger.info(f"Processing event from: {source_url}")

        try:
            title = adapter.get('title', '').strip()
            raw_description = adapter.get('description', '').strip()
            date_text = adapter.get('date_text', '').strip()
            image_url = adapter.get('image_url', '').strip()

            if not title:
                logger.warning(f"Skipping event due to missing title: {source_url}")
                return None

            # 1. Generate English Summary (using OpenAIClient)
            english_summary = None
            if self.openai_client:
                english_summary = self.openai_client.generate_english_summary(raw_description, min_chars=300, max_chars=500)
                if not english_summary:
                    logger.warning(f"Failed to generate English summary for event: {title}. Falling back.")
            else:
                 logger.warning("OpenAI client not available, skipping English summary generation.")
            
            # Keep original description
            processed_description = raw_description


            # 2. Extract Date (using DateExtractor)
            extracted_date = self.date_extractor.extract_date(date_text)
            if not extracted_date:
                 logger.warning(f"Could not extract date from '{date_text}' for event: {title}")


            # 3. Detect Event Type (using OpenAIClient)
            event_type = None
            if self.openai_client:
                # TODO: Get possible types from config
                event_type = self.openai_client.detect_event_type(f"{title} {raw_description}")
            else:
                logger.warning("OpenAI client not available, skipping event type detection.")


            # 4. Create Final Event Object
            final_event = Event(
                title=title,
                description=processed_description, # Keep original description
                summary_en=english_summary, # Store the generated summary
                date=extracted_date,
                image_url=image_url if image_url else None,
                source_url=source_url,
                event_type=event_type if event_type else "Unknown"
            )

            logger.info(f"Successfully processed event: {final_event.title} (ID: {final_event.id})")
            return final_event

        except Exception as e:
            logger.error(f"Error processing event from {source_url}: {e}", exc_info=True)
            return None

# Example usage (optional)
if __name__ == '__main__':
    # Mock raw item
    sample_item = {
        'title': ' Grande Festival di Musica a Salerno ',
        'description': 'Un fantastico festival con molti artisti internazionali si terrà nel centro della città. Non mancate a questo evento imperdibile che celebra la musica e la cultura. Ci saranno stand gastronomici e attività per tutte le età. L\'evento dura tutto il weekend. ',
        'date_text': ' Sabato 25 Maggio 2024, ore 18:00 ',
        'image_url': ' https://example.com/image.jpg ',
        'source_url': 'https://www.salernotoday.it/eventi/grande-festival-musica-salerno.html'
    }

    processor = EventProcessor()
    processed_event = processor.process_event(sample_item)

    if processed_event:
        print("\nProcessed Event:")
        print(f"  ID: {processed_event.id}")
        print(f"  Title: {processed_event.title}")
        print(f"  Description: {processed_event.description}")
        print(f"  Date: {processed_event.date}")
        print(f"  Image URL: {processed_event.image_url}")
        print(f"  Source URL: {processed_event.source_url}")
        print(f"  Event Type: {processed_event.event_type}")
        print(f"  Created At: {processed_event.created_at}")
        print("\nEvent as Dictionary:")
        print(processed_event.to_dict())