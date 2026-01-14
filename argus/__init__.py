"""
Argus: Observability layer for AI agents.

A passive, framework-agnostic system for recording structured events
from AI systems to enable debugging, failure analysis, and cost tracking.
"""

from argus.events import Event, EventType
from argus.logger import EventLogger
from argus.storage import EventStorage, JSONEventStorage
from argus.tracer import Tracer, trace_function
from argus.inspector import TraceInspector, inspect_trace_from_storage, inspect_trace_from_events

__all__ = [
    "Event",
    "EventType",
    "EventLogger",
    "EventStorage",
    "JSONEventStorage",
    "Tracer",
    "trace_function",
    "TraceInspector",
    "inspect_trace_from_storage",
    "inspect_trace_from_events",
]
