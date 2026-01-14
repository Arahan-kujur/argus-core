"""
Storage layer for Argus event persistence.

This module provides a storage interface and implementations for persisting
recorded events. Storage is kept separate from logging to allow:
- Different storage backends (JSON, SQLite, database, etc.)
- Independent evolution of logging vs. storage
- Testing without file I/O
- Multiple storage strategies per logger instance
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
import json

from argus.events import Event, EventType
from datetime import datetime, timezone


class EventStorage(ABC):
    """
    Abstract storage interface for Argus events.
    
    This interface exists to allow multiple storage backends (JSON, SQLite, etc.)
    without coupling the logger to a specific implementation. Future backends
    (e.g., SQLiteStorage, DatabaseStorage) can implement this interface.
    
    Storage is kept separate from logging because:
    - Logging is in-memory and fast; storage is I/O-bound and optional
    - Different use cases need different storage strategies
    - Storage can be swapped without changing logging code
    - Analysis tools can read storage directly without the logger
    """
    
    @abstractmethod
    def save(self, events: List[Event]) -> None:
        """
        Persist a list of events.
        
        Args:
            events: List of Event instances to save
        """
        pass
    
    @abstractmethod
    def load(self) -> List[Event]:
        """
        Load all persisted events.
        
        Returns:
            List of Event instances in the order they were saved
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Remove all persisted events."""
        pass


class JSONEventStorage(EventStorage):
    """
    JSON-based file storage for Argus events.
    
    Stores events in a single JSON file, one event per line (JSONL format)
    or as a JSON array. Uses JSONL for simplicity and append-friendly writes.
    
    This implementation makes no assumptions about event semantics, performs
    no indexing or analytics, and focuses on reliable serialization/deserialization.
    """
    
    def __init__(self, file_path: str):
        """
        Initialize JSON storage backend.
        
        Args:
            file_path: Path to the JSON file for storing events
        """
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def save(self, events: List[Event]) -> None:
        """
        Save events to JSON file, overwriting existing content.
        
        Events are saved as a JSON array to preserve insertion order.
        """
        event_dicts = [self._serialize_event(event) for event in events]
        
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(event_dicts, f, indent=2, ensure_ascii=False)
    
    def load(self) -> List[Event]:
        """
        Load events from JSON file.
        
        Returns:
            List of Event instances in saved order
            
        Raises:
            FileNotFoundError: If the storage file does not exist
        """
        if not self.file_path.exists():
            return []
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            event_dicts = json.load(f)
        
        return [self._deserialize_event(event_dict) for event_dict in event_dicts]
    
    def clear(self) -> None:
        """Remove the storage file if it exists."""
        if self.file_path.exists():
            self.file_path.unlink()
    
    def _serialize_event(self, event: Event) -> dict:
        """
        Convert Event to dictionary for JSON serialization.
        
        Handles:
        - Timestamps as ISO format strings (round-trips correctly)
        - EventType enum as string value
        - All other fields as-is
        """
        return {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "event_version": event.event_version,
            "session_id": event.session_id,
            "parent_id": event.parent_id,
            "status": event.status,
            "input": event.input,
            "output": event.output,
            "error": event.error,
            "metadata": event.metadata,
        }
    
    def _deserialize_event(self, event_dict: dict) -> Event:
        """
        Convert dictionary to Event instance.
        
        Handles:
        - ISO timestamp strings back to datetime objects
        - EventType string values back to enum
        - Unknown fields are ignored (won't break loading)
        - Missing optional fields default to None
        """
        # Parse timestamp from ISO format string
        timestamp_str = event_dict.get("timestamp")
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            # Fallback if timestamp is missing (shouldn't happen, but be defensive)
            timestamp = datetime.now(timezone.utc)
        
        # Parse event_type from string to enum
        event_type_str = event_dict.get("event_type")
        if event_type_str:
            try:
                event_type = EventType(event_type_str)
            except ValueError:
                # Unknown event type - use a default or raise
                # For robustness, we'll use LLM_CALL as fallback
                event_type = EventType.LLM_CALL
        else:
            event_type = EventType.LLM_CALL
        
        # Extract all known fields, ignoring unknown ones
        return Event(
            event_id=event_dict.get("event_id", ""),
            event_type=event_type,
            timestamp=timestamp,
            event_version=event_dict.get("event_version", "1.0"),
            session_id=event_dict.get("session_id"),
            parent_id=event_dict.get("parent_id"),
            status=event_dict.get("status"),
            input=event_dict.get("input"),
            output=event_dict.get("output"),
            error=event_dict.get("error"),
            metadata=event_dict.get("metadata", {}),
        )
