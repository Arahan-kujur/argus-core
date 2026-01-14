"""
Core event model for Argus observability.

This module defines the minimal, extensible event abstraction that can represent
behavior in any AI system without making framework-specific assumptions.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class EventType(str, Enum):
    """Core event types that Argus can observe."""
    
    LLM_CALL = "llm_call"          # An LLM API call was made
    TOOL_CALL = "tool_call"         # A tool/function was invoked
    DECISION = "decision"           # A decision point was reached
    RETRY = "retry"                 # A retry attempt occurred
    FAILURE = "failure"             # Something failed
    TERMINATION = "termination"     # Execution ended (success or failure)


@dataclass
class Event:
    """
    Core event data structure for Argus observability.
    
    This class exists to represent a single observable event in an AI system.
    It is minimal, framework-agnostic, and designed for post-hoc analysis.
    
    The Event class does not interpret or analyze data - it only structures
    what was observed. All interpretation happens in analysis layers.
    """
    
    # Mandatory core fields
    event_id: str
    event_type: EventType
    timestamp: datetime
    event_version: str = "1.0"
    
    # Optional correlation fields
    session_id: Optional[str] = None
    parent_id: Optional[str] = None
    
    # Optional outcome fields
    status: Optional[str] = None
    input: Optional[Any] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    
    # Optional extensibility field
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure event_type is EventType enum and timestamp is timezone-aware."""
        if isinstance(self.event_type, str):
            self.event_type = EventType(self.event_type)
        
        # Ensure timestamp is UTC and timezone-aware
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
        elif self.timestamp.tzinfo != timezone.utc:
            self.timestamp = self.timestamp.astimezone(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "event_version": self.event_version,
            "session_id": self.session_id,
            "parent_id": self.parent_id,
            "status": self.status,
            "input": self.input,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
        }
