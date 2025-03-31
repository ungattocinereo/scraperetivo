import os
import openai
from dotenv import load_dotenv
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

class OpenAIClient:
    """
    Client for interacting with the OpenAI API for tasks like
    translation, summarization, and event type detection.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment variables. Please set it in the .env file.")
            raise ValueError("Missing OpenAI API Key")
        # Initialize the OpenAI client instance (v1.0.0+ syntax)
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
            raise ValueError("Failed to initialize OpenAI client")

    def translate_text(self, text: str, target_language: str = "English") -> str | None:
        """
        Translates the given text to the target language using OpenAI.
        (Placeholder implementation)
        """
        logger.info(f"Attempting to translate text to {target_language} (length: {len(text)})")
        if not text:
            return ""
        # TODO: Implement actual OpenAI API call for translation
        # Example using ChatCompletion (adapt model and prompt as needed):
        # try:
        #     response = self.client.chat.completions.create(
        #         model="gpt-3.5-turbo", # Or another suitable model
        #         messages=[
        #             {"role": "system", "content": f"Translate the following text to {target_language}."},
        #             {"role": "user", "content": text}
        #         ],
        #         temperature=0.3,
        #     )
        #     translation = response.choices[0].message.content.strip()
        #     logger.info("Translation successful.")
        #     return translation
        # except Exception as e:
        #     logger.error(f"OpenAI translation failed: {e}", exc_info=True)
        #     return None
        logger.warning("translate_text: OpenAI call not implemented yet. Returning original text.")
        return f"[Translated to {target_language}]: {text}" # Placeholder

    def summarize_text(self, text: str, max_length: int = 100) -> str | None:
        """
        Summarizes the given text using OpenAI.
        (Placeholder implementation)
        """
        logger.info(f"Attempting to summarize text (length: {len(text)}) to max {max_length} chars")
        if not text:
            return ""
        # TODO: Implement actual OpenAI API call for summarization
        # Example:
        # try:
        #     response = self.client.chat.completions.create(
        #         model="gpt-3.5-turbo",
        #         messages=[
        #             {"role": "system", "content": f"Summarize the following text concisely, ideally under {max_length} characters."},
        #             {"role": "user", "content": text}
        #         ],
        #         temperature=0.5,
        #     )
        #     summary = response.choices[0].message.content.strip()
        #     logger.info("Summarization successful.")
        #     return summary
        # except Exception as e:
        #     logger.error(f"OpenAI summarization failed: {e}", exc_info=True)
        #     return None
        logger.warning("summarize_text: OpenAI call not implemented yet. Returning truncated text.")
        return f"[Summary]: {text[:max_length]}..." if len(text) > max_length else text # Placeholder

    def detect_event_type(self, text: str, possible_types: list[str] | None = None) -> str | None:
        """
        Detects the event type from the text using OpenAI.
        (Placeholder implementation)
        """
        logger.info(f"Attempting to detect event type from text (length: {len(text)})")
        if not text:
            return None
        # TODO: Implement actual OpenAI API call for event type detection
        # Example:
        # type_list = ", ".join(possible_types) if possible_types else "common event categories (e.g., Concert, Festival, Exhibition, Conference, Sport)"
        # try:
        #     response = self.client.chat.completions.create(
        #         model="gpt-3.5-turbo",
        #         messages=[
        #             {"role": "system", "content": f"Classify the following event description into one of these categories: {type_list}. Respond with only the category name."},
        #             {"role": "user", "content": text}
        #         ],
        #         temperature=0.2,
        #     )
        #     event_type = response.choices[0].message.content.strip()
        #     # Optional: Validate if the returned type is in the possible_types list
        #     logger.info(f"Event type detection successful: {event_type}")
        #     return event_type
        # except Exception as e:
        #     logger.error(f"OpenAI event type detection failed: {e}", exc_info=True)
        #     return None
        logger.warning("detect_event_type: OpenAI call not implemented yet. Returning 'Unknown'.")
        return "Unknown" # Placeholder

    def generate_english_summary(self, text: str, min_chars: int = 300, max_chars: int = 500) -> str | None:
        """
        Generates a descriptive summary of the given text in English using OpenAI,
        aiming for a length between min_chars and max_chars.
        """
        logger.info(f"Attempting to generate English summary (target: {min_chars}-{max_chars} chars) for text (length: {len(text)})")
        if not text:
            return ""

        prompt = f"""Rewrite the following event description in English. Create a compelling and informative summary suitable for a tourist audience.
Include all essential details like what the event is, where, and any specific highlights mentioned.
The summary should be between {min_chars} and {max_chars} characters long. Do not include the date unless it's part of the core description.

Original Text:
\"\"\"
{text}
\"\"\"

English Summary ({min_chars}-{max_chars} characters):"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo", # Or consider gpt-4-turbo-preview for potentially better results
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes event descriptions for tourists in clear and engaging English."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6, # Allow for some creativity but stay factual
                max_tokens=150, # Estimate tokens needed for ~500 chars + prompt
                n=1,
                stop=None,
            )
            summary = response.choices[0].message.content.strip()
            # Basic length check (can be refined)
            if len(summary) < min_chars / 2 or len(summary) > max_chars * 1.2: # Allow some flexibility
                 logger.warning(f"Generated summary length ({len(summary)}) is outside the target range ({min_chars}-{max_chars}). Using it anyway.")

            logger.info(f"English summary generation successful (length: {len(summary)}).")
            return summary
        except Exception as e:
            logger.error(f"OpenAI English summary generation failed: {e}", exc_info=True)
            return None
# Example usage (optional)
if __name__ == '__main__':
    try:
        client = OpenAIClient()
        sample_text = "Concerto di musica classica stasera al teatro Verdi."
        translation = client.translate_text(sample_text)
        print(f"Translation: {translation}")
        summary = client.summarize_text(sample_text * 5) # Longer text for summary
        print(f"Summary: {summary}")
        event_type = client.detect_event_type(sample_text, ["Concert", "Theatre", "Exhibition"])
        print(f"Event Type: {event_type}")
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")