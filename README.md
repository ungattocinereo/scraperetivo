d# Tourist Event Collection System

This project collects tourist events from various Italian websites, processes them using AI, and makes them available via a Telegram bot.

## Project Structure

```
tourist_events/
├── config/             # Configuration files (main config, website rules)
├── crawler/            # Scrapy crawler implementation (spiders, items, settings)
├── data/               # Data storage (e.g., events.json)
├── logs/               # Log files
├── processor/          # Event processing logic (OpenAI client, date extraction)
├── storage/            # Data storage implementation (models, storage class)
├── telegram_bot/       # Telegram bot implementation (bot logic, handlers, formatters)
├── utils/              # Utility modules (logger, helpers)
├── main.py             # Main entry point for running components
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd tourist_events_project # Or your project directory name
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r tourist_events/requirements.txt
    ```

4.  **Configure environment variables:**
    - Create a `.env` file in the project root directory (where `architecture.md` is).
    - Add your API keys to the `.env` file:
      ```dotenv
      OPENAI_API_KEY=your_openai_api_key_here
      TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
      ```

## Usage

You can run different components of the system using `main.py`.

*   **Run the web crawler:**
    ```bash
    python tourist_events/main.py run-crawler
    ```
    *   To run specific spiders:
        ```bash
        python tourist_events/main.py run-crawler --spiders ilvescovado salernotoday
        ```

*   **Run the Telegram bot:**
    ```bash
    python tourist_events/main.py run-bot
    ```

*   **(Experimental) Run crawler then bot:**
    ```bash
    python tourist_events/main.py run-all
    ```

## Next Steps

*   Refine Scrapy spider selectors based on actual website structures.
*   Implement actual OpenAI API calls in `openai_client.py`.
*   Implement pagination and filtering in the Telegram bot.
*   Add more robust error handling and testing.
*   Configure `config/config.json` and `config/website_rules.json`.