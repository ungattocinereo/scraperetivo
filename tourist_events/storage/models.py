from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class Event:
    """Represents a tourist event."""
    title: str
    description: str
    date: Optional[datetime] = None
    image_url: Optional[str] = None
    source_url: str = ""
    event_type: Optional[str] = None
    summary_en: Optional[str] = None # Added field for English summary
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        """Converts the Event object to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "date": self.date.isoformat() if self.date else None,
            "image_url": self.image_url,
            "source_url": self.source_url,
            "event_type": self.event_type,
            "summary_en": self.summary_en, # Added field
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        """Creates an Event object from a dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title"),
            description=data.get("description"),
            date=datetime.fromisoformat(data["date"]) if data.get("date") else None,
            image_url=data.get("image_url"),
            source_url=data.get("source_url"),
            event_type=data.get("event_type"),
            summary_en=data.get("summary_en"), # Added field
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat()))
        )