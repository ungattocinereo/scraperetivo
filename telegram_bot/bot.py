import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

from ..utils.logger import get_logger
from .handlers import start, help_command, events_command # Handlers to be created
from ..storage.event_storage import EventStorage # Import storage

logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)


def run_bot():
    """Runs the Telegram bot."""
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables. Please set it in the .env file.")
        raise ValueError("Missing Telegram Bot Token")

    logger.info("Initializing Telegram Bot...")

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(telegram_token).build()

    # --- Persistent storage for context ---
    # Create an instance of EventStorage (or pass it if created elsewhere)
    event_storage = EventStorage()
    application.bot_data["event_storage"] = event_storage
    logger.info("EventStorage added to bot_data.")
    # ------------------------------------

    # --- Register Handlers ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("events", events_command))
    # Add more handlers here (e.g., for button callbacks, messages)
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo)) # Example echo handler

    # --- Register Error Handler ---
    application.add_error_handler(error_handler)

    # --- Start the Bot ---
    logger.info("Starting bot polling...")
    application.run_polling()
    logger.info("Bot stopped.")


if __name__ == '__main__':
    # This allows running the bot directly for testing
    # In production, you might call run_bot() from main.py
    try:
        run_bot()
    except ValueError as e:
        logger.critical(f"Bot failed to start: {e}")
    except Exception as e:
        logger.critical(f"An unexpected error occurred while running the bot: {e}", exc_info=True)