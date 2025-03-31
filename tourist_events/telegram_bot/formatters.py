from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ..storage.models import Event
from ..utils.logger import get_logger
import html

logger = get_logger(__name__)

def format_event_caption(event: Event) -> str:
    """
    Formats a single Event object into an HTML caption string for a Telegram photo message.
    Includes Date, Title, Description (as blockquote), and Source Link.

    Args:
        event: The Event object to format.

    Returns:
        The formatted caption string (HTML). Returns empty string if essential info is missing.
    """
    logger.debug(f"Formatting caption for event: {event.title} (ID: {event.id})")

    # --- Prepare content parts ---
    # Date (dd.mm.yyyy, monospace)
    date_str = f"<code>{event.date.strftime('%d.%m.%Y')}</code>" if event.date else ""

    # Title (bold)
    title_str = f"<b>{html.escape(event.title)}</b>" if event.title else ""
    if not title_str:
        logger.warning(f"Event {event.id} missing title. Cannot format caption.")
        return "" # Title is essential

    # Description (blockquote, prefer English summary)
    desc_content = event.summary_en if event.summary_en else event.description
    if not desc_content:
        desc_content = "No description available."
    desc_str = f"<blockquote>{html.escape(desc_content)}</blockquote>"

    # Source Link (monospace)
    source_str = f"Source: <code>{html.escape(event.source_url)}</code>" if event.source_url else ""

    # --- Combine parts ---
    caption_parts = [part for part in [date_str, title_str, desc_str, source_str] if part] # Filter empty parts
    caption_text = "\n\n".join(caption_parts) # Use double newline for better separation

    # --- Truncate if necessary ---
    # Telegram caption limit is 1024 characters
    if len(caption_text) > 1024:
        logger.warning(f"Generated caption for event {event.id} exceeds 1024 chars ({len(caption_text)}). Truncating description.")
        # Calculate overhead (tags, newlines, etc.)
        overhead = len(caption_text) - len(desc_content) # Approx length without description content
        max_desc_len = 1024 - overhead - 3 # -3 for "..."
        if max_desc_len < 0: max_desc_len = 0 # Ensure non-negative

        truncated_desc_content = desc_content[:max_desc_len] + "..."
        desc_str = f"<blockquote>{html.escape(truncated_desc_content)}</blockquote>"

        # Rebuild caption with truncated description
        caption_parts = [part for part in [date_str, title_str, desc_str, source_str] if part]
        caption_text = "\n\n".join(caption_parts)

        # Final check (shouldn't be necessary but as a safeguard)
        if len(caption_text) > 1024:
             caption_text = caption_text[:1021] + "..."


    return caption_text

# Example usage (optional)
# Example usage (optional) - Updated for caption
if __name__ == '__main__':
    from datetime import datetime
    sample_event = Event(
        id="test-123",
        title="Summer Concert",
        description="A great outdoor concert with local and international artists.", # Original desc
        summary_en="Enjoy a fantastic outdoor concert featuring a mix of talented local musicians and renowned international performers. This event celebrates music and culture under the stars. Perfect for an evening out!", # Sample summary
        date=datetime(2024, 7, 15, 21, 0),
        image_url="https://example.com/concert.jpg",
        source_url="https://example.com/event-details",
        event_type="Concert"
    )

    caption = format_event_caption(sample_event)

    print("--- Formatted Caption ---")
    print(caption)