from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from urllib.parse import urlparse
from collections import defaultdict
from typing import List, Dict, Optional # Added for type hinting

from ..utils.logger import get_logger
from ..storage.event_storage import EventStorage
from .formatters import format_event_caption # Updated import

logger = get_logger(__name__)

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    user = update.effective_user
    logger.info(f"User {user.username} (ID: {user.id}) started the bot.")
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! 👋", # Changed to English
        reply_markup=None, # Optional: Add a keyboard later
    )
    # Also send the help message
    await help_command(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message explaining how to use the bot when the /help command is issued."""
    logger.info(f"User {update.effective_user.username} requested help.")
    help_text = (
        "Here's what I can do:\n"
        "📅 /events - Show upcoming events.\n"
        # "🔍 /filter - Filter events by type or date (Coming soon!).\n" # Example for future
        "ℹ️ /help - Show this help message.\n"
    ) # Changed to English
    await update.message.reply_text(help_text)


async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and displays upcoming events when the /events command is issued."""
    user = update.effective_user
    logger.info(f"User {user.username} requested events.")
    chat_id = update.effective_chat.id

    # Access EventStorage from bot_data
    storage: EventStorage = context.application.bot_data.get("event_storage")
    if not storage:
        logger.error("EventStorage not found in bot_data.")
        await context.bot.send_message(chat_id, "Error: Could not access event storage.") # Changed to English
        return

    try:
        # Fetch upcoming events (e.g., from today onwards)
        # TODO: Add more sophisticated filtering options later
        filters = {'min_date': datetime.now().date()}
        events = storage.get_events(filters=filters)

        if not events:
            await context.bot.send_message(chat_id, "No upcoming events found right now. Try again later!") # Changed to English
            # Optionally trigger a crawl here if desired
            return

        logger.info(f"Found {len(events)} upcoming events for user {user.username}.")

        # --- Group, sort, and limit events per source ---
        events_by_source: Dict[str, List] = defaultdict(list)
        for event in events:
            if event.source_url:
                try:
                    domain = urlparse(event.source_url).netloc
                    # Normalize domain (e.g., remove www.)
                    domain = domain.replace("www.", "")
                    events_by_source[domain].append(event)
                except Exception:
                    logger.warning(f"Could not parse domain from URL: {event.source_url}")
                    events_by_source["unknown"].append(event) # Group events with bad URLs
            else:
                 events_by_source["unknown"].append(event) # Group events without URLs


        final_events = []
        for source, source_events in events_by_source.items():
            # Sort events within the source group by date (most recent first)
            source_events.sort(key=lambda x: x.date if x.date else datetime.min, reverse=True)
            # Take the top 2 most recent events
            final_events.extend(source_events[:2])
            logger.debug(f"Selected top {len(source_events[:2])} events from source: {source}")

        # Sort the final combined list by date (most recent first)
        final_events.sort(key=lambda x: x.date if x.date else datetime.min, reverse=True)

        logger.info(f"Prepared {len(final_events)} events to send after per-source filtering.")

        # --- Send events as photos with captions ---
        # No overall limit needed now, as we limited per source
        # max_events_to_show = 10 # Limit the number of events shown initially - REMOVED

        sent_count = 0
        for event in final_events:
            # The limit per source is already applied, no need for max_events_to_show check here
            # if sent_count >= max_events_to_show:
            #     break

            caption = format_event_caption(event) # Use the updated formatter

            # Only proceed if a caption was successfully generated (i.e., summary_en exists)
            if caption:
                try:
                    if event.image_url:
                        await context.bot.send_photo(
                            chat_id=chat_id,
                            photo=event.image_url,
                            caption=caption,
                            parse_mode='HTML'
                        )
                    else:
                        # Send as text if no image, using the formatted caption
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=caption,
                            parse_mode='HTML',
                            disable_web_page_preview=True
                        )
                    sent_count += 1
                except Exception as send_error:
                    logger.error(f"Failed to send event {event.id} ({event.title}) to user {user.username}: {send_error}")
                    # Optionally inform the user about the specific failure
                    # await context.bot.send_message(chat_id, f"Could not send event: {event.title}")
            else:
                logger.info(f"Skipping event {event.id} ({event.title}) for user {user.username} due to missing English summary.")
                # await asyncio.sleep(0.5) # Optional delay


        # Remove or adjust the "more events" message as it might be confusing now
        # if len(events) > sent_count: # Original total vs sent count
        #      await context.bot.send_message(chat_id, f"Displayed the 2 most recent events per source.")

    except Exception as e:
        logger.error(f"Error fetching or sending events for user {user.username}: {e}", exc_info=True)
        await context.bot.send_message(chat_id, "An error occurred while fetching events.") # Changed to English


# --- Placeholder for other handlers (e.g., button callbacks) ---
# async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer() # Acknowledge the button press
#     data = query.data # Data associated with the button
#     logger.info(f"Button pressed with data: {data}")
#     # Handle different button actions based on 'data'
#     await query.edit_message_text(text=f"Selected option: {data}")