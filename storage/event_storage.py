import json
import os
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from .models import Event
from ..utils.logger import get_logger

logger = get_logger(__name__)

class EventStorage:
    """
    Handles storing and retrieving Event objects using a JSON file.
    Includes basic thread safety for file operations.
    """
    def __init__(self, storage_path: str = "data/events.json"):
        self.storage_path = storage_path
        self.lock = threading.Lock() # Lock for thread-safe file access
        self._ensure_storage_file_exists()
        logger.info(f"EventStorage initialized with path: {self.storage_path}")

    def _ensure_storage_file_exists(self):
        """Creates the storage file and its directory if they don't exist."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            logger.warning(f"Storage file not found at {self.storage_path}. Creating an empty file.")
            with self.lock:
                try:
                    with open(self.storage_path, 'w', encoding='utf-8') as f:
                        json.dump([], f) # Initialize with an empty list
                except IOError as e:
                    logger.error(f"Failed to create storage file {self.storage_path}: {e}")
                    raise # Re-raise the exception as this is critical

    def _load_events(self) -> List[Dict]:
        """Loads raw event data (dictionaries) from the JSON file."""
        with self.lock:
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content: # Handle empty file
                        return []
                    data = json.loads(content)
                    if isinstance(data, list):
                        return data
                    else:
                        logger.error(f"Invalid format in storage file {self.storage_path}. Expected a list, got {type(data)}. Returning empty list.")
                        return []
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Error loading events from {self.storage_path}: {e}")
                return [] # Return empty list on error to prevent crashes

    def _save_events(self, events_data: List[Dict]):
        """Saves raw event data (dictionaries) to the JSON file."""
        with self.lock:
            try:
                with open(self.storage_path, 'w', encoding='utf-8') as f:
                    json.dump(events_data, f, indent=4, ensure_ascii=False)
            except IOError as e:
                logger.error(f"Error saving events to {self.storage_path}: {e}")

    def save_events(self, new_events: List[Event]):
        """
        Saves a list of new Event objects to the storage.
        Avoids duplicates based on event ID.
        """
        if not new_events:
            return

        logger.info(f"Attempting to save {len(new_events)} new events.")
        current_events_data = self._load_events()
        current_event_ids = {event_data.get('id') for event_data in current_events_data}
        added_count = 0

        for event in new_events:
            if event.id not in current_event_ids:
                current_events_data.append(event.to_dict())
                current_event_ids.add(event.id)
                added_count += 1
            else:
                logger.debug(f"Event with ID {event.id} already exists. Skipping.")

        if added_count > 0:
            self._save_events(current_events_data)
            logger.info(f"Successfully saved {added_count} new events.")
        else:
            logger.info("No new events were added to storage.")


    def get_events(self, filters: Optional[Dict] = None) -> List[Event]:
        """
        Retrieves events from storage, optionally applying filters.

        Args:
            filters: A dictionary of filters (e.g., {'event_type': 'Concert', 'min_date': datetime(...)})

        Returns:
            A list of matching Event objects.
        """
        events_data = self._load_events()
        events = [Event.from_dict(data) for data in events_data if data] # Recreate objects

        if filters:
            logger.info(f"Applying filters: {filters}")
            filtered_events = []
            min_date = filters.get('min_date')
            max_date = filters.get('max_date')
            event_type = filters.get('event_type')

            for event in events:
                match = True
                if event_type and event.event_type != event_type:
                    match = False
                if min_date and (not event.date or event.date.date() < min_date):
                    match = False
                if max_date and (not event.date or event.date.date() > max_date):
                    match = False
                # Add more filter conditions as needed

                if match:
                    filtered_events.append(event)
            logger.info(f"Found {len(filtered_events)} events matching filters.")
            return filtered_events
        else:
            logger.info(f"Retrieved {len(events)} total events (no filters).")
            return events

    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """Retrieves a single event by its ID."""
        logger.debug(f"Attempting to retrieve event by ID: {event_id}")
        events_data = self._load_events()
        for data in events_data:
            if data.get('id') == event_id:
                logger.info(f"Found event with ID: {event_id}")
                return Event.from_dict(data)
        logger.warning(f"Event with ID {event_id} not found.")
        return None

    def remove_old_events(self, days_old: int = 30):
        """
        Removes events older than a specified number of days based on their date.
        (Phase 4, Step 3)
        """
        logger.info(f"Starting removal of events older than {days_old} days.")
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        current_events_data = self._load_events()
        kept_events_data = []
        removed_count = 0

        for event_data in current_events_data:
            event = Event.from_dict(event_data)
            # Keep events that have no date or are newer than the cutoff
            if event.date is None or event.date >= cutoff_date.date(): # Compare date part only
                 kept_events_data.append(event_data)
            else:
                logger.debug(f"Removing old event: {event.title} (Date: {event.date}, ID: {event.id})")
                removed_count += 1

        if removed_count > 0:
            self._save_events(kept_events_data)
            logger.info(f"Removed {removed_count} old events (older than {cutoff_date.date()}).")
        else:
            logger.info("No old events found to remove.")


# Example usage (optional)
if __name__ == '__main__':
    storage = EventStorage(storage_path="data/test_events.json") # Use a test file

    # Clean up previous test file if exists
    if os.path.exists("data/test_events.json"):
        os.remove("data/test_events.json")
    storage._ensure_storage_file_exists()


    # Create some sample events
    event1 = Event(title="Test Event 1", description="Desc 1", date=datetime(2024, 5, 20), source_url="url1")
    event2 = Event(title="Test Event 2", description="Desc 2", date=datetime(2024, 6, 15), source_url="url2", event_type="Concert")
    event3 = Event(title="Old Event", description="Old Desc", date=datetime(2023, 1, 1), source_url="url3")
    event4 = Event(title="Future Event", description="Future Desc", date=datetime.now().date() + timedelta(days=10), source_url="url4", event_type="Festival")


    print("\n--- Saving Events ---")
    storage.save_events([event1, event2, event3, event4])
    storage.save_events([event1]) # Try saving duplicate

    print("\n--- Retrieving All Events ---")
    all_events = storage.get_events()
    for ev in all_events:
        print(f"- {ev.title} ({ev.date})")

    print("\n--- Retrieving by ID ---")
    found_event = storage.get_event_by_id(event2.id)
    print(f"Found by ID ({event2.id}): {found_event.title if found_event else 'Not Found'}")
    not_found_event = storage.get_event_by_id("non-existent-id")
    print(f"Found by ID (non-existent-id): {not_found_event.title if not_found_event else 'Not Found'}")


    print("\n--- Retrieving with Filters ---")
    concerts = storage.get_events(filters={'event_type': 'Concert'})
    print(f"Concerts: {[ev.title for ev in concerts]}")
    future_events = storage.get_events(filters={'min_date': datetime.now()})
    print(f"Future Events: {[ev.title for ev in future_events]}")


    print("\n--- Removing Old Events ---")
    storage.remove_old_events(days_old=90) # Remove events older than 90 days

    print("\n--- Retrieving Events After Cleanup ---")
    all_events_after_cleanup = storage.get_events()
    for ev in all_events_after_cleanup:
        print(f"- {ev.title} ({ev.date})")

    # Clean up test file
    # os.remove("data/test_events.json")
    print("\nTest complete. Check data/test_events.json")