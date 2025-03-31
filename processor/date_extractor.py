from dateparser.search import search_dates
from datetime import datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)

class DateExtractor:
    """
    Extracts and parses dates from raw text strings using the dateparser library.
    Configured primarily for Italian dates but attempts other languages.
    """
    def __init__(self):
        # Configure dateparser settings
        # Prioritize Italian, but allow English as fallback.
        # Adjust languages based on expected source website languages.
        self.parser_settings = {
            # 'languages': ['it', 'en'], # Removed: Pass languages as a separate argument
            'PREFER_DATES_FROM': 'future', # Prefer future dates when ambiguity exists
            'RETURN_AS_TIMEZONE_AWARE': False, # Return naive datetime objects
            # 'DATE_ORDER': 'DMY', # Explicitly set DMY for Italian context if needed
        }
        logger.info("DateExtractor initialized with settings: %s", self.parser_settings)

    def extract_date(self, text: str) -> datetime | None:
        """
        Extracts the first valid date found in the given text string.

        Args:
            text: The raw text string potentially containing a date.

        Returns:
            A datetime object if a date is found, otherwise None.
        """
        if not text or not isinstance(text, str):
            logger.warning("Invalid input provided for date extraction.")
            return None

        logger.debug(f"Attempting to extract date from text: '{text}'")
        try:
            # Use search_dates which is better for finding dates within larger text blocks
            # It returns a list of tuples: (original_string, datetime_object)
            # Pass languages separately, extract other settings
            languages = ['it', 'en'] # Define languages here or load from config
            other_settings = {k: v for k, v in self.parser_settings.items() if k != 'languages'}
            date_results = search_dates(text, languages=languages, settings=other_settings)

            if date_results:
                # Select the first found date
                original_str, parsed_date = date_results[0]
                logger.info(f"Successfully extracted date '{parsed_date}' from substring '{original_str}' in text: '{text}'")
                # Ensure it's a datetime object (dateparser might return date)
                if isinstance(parsed_date, datetime):
                    return parsed_date
                else: # Handle cases where only date part is parsed
                    return datetime.combine(parsed_date, datetime.min.time())
            else:
                logger.warning(f"Could not find any valid date in text: '{text}'")
                return None

        except Exception as e:
            logger.error(f"Error during date extraction from text '{text}': {e}", exc_info=True)
            return None

# Example usage (optional)
if __name__ == '__main__':
    extractor = DateExtractor()
    test_cases = [
        "L'evento si terrà Sabato 25 Maggio 2024, ore 18:00",
        "Appuntamento il 15/06/2024",
        "Dal 1 Giugno al 5 Giugno", # Will likely pick June 1st
        "Prossimo martedì alle 20",
        "Event on July 4th, 2024",
        "Nessuna data qui",
        "Oggi",
        "Domani sera",
        "Invalid date string",
        None,
        12345
    ]

    for case in test_cases:
        print(f"\nInput: '{case}'")
        extracted = extractor.extract_date(case)
        if extracted:
            print(f"Output: {extracted} (Type: {type(extracted)})")
        else:
            print("Output: None")