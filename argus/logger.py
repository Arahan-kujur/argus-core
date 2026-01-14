"""
Event logging mechanism for Argus.

This module provides EventLogger, a passive recorder that maintains an ordered
sequence of events without interpretation or analysis.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional
import uuid

from argus.events import Event, EventType


class EventLogger:
    """
    Passive event recorder for Argus.
    
    This class exists to record events in order without modification or interpretation.
    It automatically assigns event_id and timestamp, but does not analyze, aggregate,
    or transform events. All events are stored in insertion order.
    
    EventLogger avoids interpretation because:
    - Analysis belongs in separate layers, not in the recording mechanism
    - Keeping the logger neutral ensures events are recorded exactly as observed
    - Post-hoc analysis requires raw, unmodified event data
    - Separation of concerns: recording vs. analysis are distinct responsibilities
    """
    
    def __init__(self):
        """Initialize an empty event log."""
        self._events: List[Event] = []
    
    def log_event(
        self,
        event_type: EventType,
        session_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        status: Optional[str] = None,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        error: Optional[str] = None,
        metadata: Optional[dict] = None,
        event_version: str = "1.0",
    ) -> Event:
        """
        Record a new event.
        
        Automatically assigns:
        - event_id: Unique UUID-based identifier
        - timestamp: Current UTC time
        
        Args:
            event_type: Type of event (required)
            session_id: Optional session identifier for grouping events
            parent_id: Optional parent event identifier for event hierarchies
            status: Optional status string (e.g., "success", "failure", "pending")
            input: Optional input data that triggered the event
            output: Optional output data from the event
            error: Optional error message if the event failed
            metadata: Optional dictionary for additional event-specific data
            event_version: Event schema version (default: "1.0")
        
        Returns:
            The created Event instance
        """
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            event_version=event_version,
            session_id=session_id,
            parent_id=parent_id,
            status=status,
            input=input,
            output=output,
            error=error,
            metadata=metadata or {},
        )
        
        self._events.append(event)
        return event
    
    def get_events(self) -> List[Event]:
        """
        Get all recorded events in insertion order.
        
        Returns:
            List of Event instances in the order they were recorded
        """
        return self._events.copy()
    
    def clear(self):
        """Clear all recorded events."""
        self._events.clear()
