import argparse
import sys
import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from dotenv import load_dotenv

# Ensure the project root is in the Python path
# This allows relative imports like 'from .utils' to work correctly
# when running main.py directly.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Also add the parent directory if tourist_events is a sub-package
parent_dir = os.path.dirname(project_root)
if parent_dir not in sys.path:
     sys.path.insert(0, parent_dir)


from tourist_events.utils.logger import get_logger
# Import necessary components (ensure correct relative paths)
try:
    from tourist_events.telegram_bot.bot import run_bot
    # Import specific spiders if needed, or let Scrapy discover them
    from tourist_events.crawler.spiders.ilvescovado_spider import IlVescovadoSpider
    from tourist_events.crawler.spiders.salernotoday_spider import SalernoTodaySpider
    from tourist_events.crawler.spiders.booble_spider import BoobleSpider
    from tourist_events.crawler.spiders.ilportico_spider import IlPorticoSpider
    from tourist_events.crawler.spiders.maiorinews_spider import MaioriNewsSpider
    from tourist_events.crawler.spiders.amalfinews_spider import AmalfiNewsSpider
    # Import processor and storage if main needs to interact directly (less common)
    # from tourist_events.processor.event_processor import EventProcessor
    # from tourist_events.storage.event_storage import EventStorage
except ImportError as e:
    print(f"Error importing modules: {e}. Make sure PYTHONPATH is set correctly or run from the project root directory.", file=sys.stderr)
    sys.exit(1)


logger = get_logger(__name__)
load_dotenv() # Load .env variables for components that need them

def run_crawler(spiders_to_run=None):
    """
    Runs the Scrapy crawler process for specified spiders.
    If no spiders are specified, runs all discovered spiders.
    """
    logger.info(f"Starting crawler process for spiders: {spiders_to_run or 'all'}")
    settings = get_project_settings()
    # Explicitly ensure the pipeline is enabled in the settings passed to CrawlerProcess
    # This can help if settings loading behaves differently when run via CrawlerProcess
    settings['ITEM_PIPELINES'] = {
        "tourist_events.crawler.pipelines.TouristEventsPipeline": 300,
    }
    logger.debug(f"Using settings for CrawlerProcess: {settings.copy_to_dict()}") # Log settings being used
    process = CrawlerProcess(settings)

    if spiders_to_run:
        for spider_name in spiders_to_run:
            logger.info(f"Adding spider '{spider_name}' to crawl process.")
            # Dynamically get spider class - requires correct SPIDER_MODULES in settings.py
            # This is a bit more complex, for now, we hardcode known spiders
            if spider_name == 'ilvescovado':
                 process.crawl(IlVescovadoSpider)
            elif spider_name == 'salernotoday':
                 process.crawl(SalernoTodaySpider)
            elif spider_name == 'booble':
                 process.crawl(BoobleSpider)
            elif spider_name == 'ilportico':
                 process.crawl(IlPorticoSpider)
            elif spider_name == 'maiorinews':
                 process.crawl(MaioriNewsSpider)
            elif spider_name == 'amalfinews':
                 process.crawl(AmalfiNewsSpider)
            else:
                 logger.warning(f"Unknown spider name specified: {spider_name}. Skipping.")
                 # TODO: Implement dynamic spider loading if needed
    else:
        logger.info("No specific spiders specified, attempting to run all discovered spiders.")
        # Scrapy discovers spiders listed in SPIDER_MODULES in settings.py
        # This requires running scrapy crawlall command or similar logic.
        # For simplicity here, we explicitly list the known ones.
        # A better approach might involve using CrawlerRunner for more control.
        process.crawl(IlVescovadoSpider)
        process.crawl(SalernoTodaySpider)
        process.crawl(BoobleSpider)
        process.crawl(IlPorticoSpider)
        process.crawl(MaioriNewsSpider)
        process.crawl(AmalfiNewsSpider)


    try:
        process.start() # The script will block here until the crawling is finished
        logger.info("Crawler process finished.")
    except Exception as e:
        logger.error(f"Crawler process failed: {e}", exc_info=True)


def main():
    parser = argparse.ArgumentParser(description="Tourist Event Collection System")
    parser.add_argument(
        "command",
        choices=["run-crawler", "run-bot", "run-all"],
        help="The command to execute."
    )
    parser.add_argument(
        "--spiders",
        nargs='+',
        choices=['ilvescovado', 'salernotoday', 'booble', 'ilportico', 'maiorinews', 'amalfinews'], # Add new spider names here
        help="Specify which spider(s) to run (e.g., --spiders ilvescovado amalfinews). Only used with 'run-crawler'."
    )
    # Add other arguments if needed
    # Add other arguments if needed

    args = parser.parse_args()

    logger.info(f"Executing command: {args.command}")

    if args.command == "run-crawler":
        run_crawler(args.spiders)
    elif args.command == "run-bot":
        try:
            run_bot()
        except ValueError as e:
             logger.critical(f"Bot failed to start: {e}")
        except Exception as e:
             logger.critical(f"An unexpected error occurred while running the bot: {e}", exc_info=True)
    elif args.command == "run-all":
        # Example: Run crawler first, then bot (in separate processes ideally)
        logger.info("Running crawler first...")
        run_crawler(args.spiders)
        logger.info("Starting bot...")
        try:
            run_bot()
        except ValueError as e:
             logger.critical(f"Bot failed to start: {e}")
        except Exception as e:
             logger.critical(f"An unexpected error occurred while running the bot: {e}", exc_info=True)
    else:
        logger.error(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()