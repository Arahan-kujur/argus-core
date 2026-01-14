"""
Tracing mechanism for Argus observability.

This module provides a tracer that can wrap arbitrary code blocks to emit
Argus events with minimal intrusion. The tracer is framework-agnostic and
does not modify program behavior.
"""

import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional

from argus.events import EventType
from argus.logger import EventLogger


class Tracer:
    """
    Context manager for tracing code execution and emitting Argus events.
    
    This class exists to instrument arbitrary code blocks (functions, methods,
    code sections) without modifying their behavior. It records execution
    duration, inputs, outputs, and errors, then emits events to an EventLogger.
    
    The tracer uses a context manager as the primary mechanism because:
    - Flexibility: Works with any code block, not just functions
    - Minimal intrusion: No function signature changes required
    - Clarity: Explicit scope boundaries (enter/exit)
    - Optional: Code works identically without the tracer
    
    Example:
        logger = EventLogger()
        with Tracer(logger, EventType.TOOL_CALL, input_data={"x": 1}):
            result = some_function(x=1)
    """
    
    def __init__(
        self,
        logger: EventLogger,
        event_type: EventType,
        session_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        input_summary: Optional[Any] = None,
        metadata: Optional[dict] = None,
    ):
        """
        Initialize a tracer for a code block.
        
        Args:
            logger: EventLogger instance to emit events to
            event_type: Type of event to emit
            session_id: Optional session identifier
            parent_id: Optional parent event identifier for event hierarchies
            input_summary: Optional summary of inputs (will be stored in event.input)
            metadata: Optional additional metadata
        """
        self.logger = logger
        self.event_type = event_type
        self.session_id = session_id
        self.parent_id = parent_id
        self.input_summary = input_summary
        self.metadata = metadata or {}
        self.start_time: Optional[float] = None
        self.start_event_id: Optional[str] = None
        self._output: Optional[Any] = None
    
    def __enter__(self):
        """Enter the traced code block and record start event."""
        self.start_time = time.perf_counter()
        
        # Emit start event (optional - can be used for event hierarchies)
        start_event = self.logger.log_event(
            event_type=self.event_type,
            session_id=self.session_id,
            parent_id=self.parent_id,
            status="started",
            input=self.input_summary,
            metadata=self.metadata,
        )
        self.start_event_id = start_event.event_id
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the traced code block and record completion event.
        
        Records execution duration, output (if successful), or error (if exception).
        Re-raises any exception that occurred to preserve program behavior.
        """
        end_time = time.perf_counter()
        duration_seconds = end_time - self.start_time if self.start_time else 0.0
        
        # Determine status and capture output/error
        if exc_type is None:
            status = "success"
            error = None
            output = self._output  # Use stored output if set
        else:
            status = "failure"
            error = f"{exc_type.__name__}: {str(exc_val)}"
            output = None
        
        # Add duration to metadata
        completion_metadata = {**self.metadata, "duration_seconds": duration_seconds}
        
        # Emit completion event
        self.logger.log_event(
            event_type=self.event_type,
            session_id=self.session_id,
            parent_id=self.parent_id,
            status=status,
            input=self.input_summary,
            output=output,
            error=error,
            metadata=completion_metadata,
        )
        
        # Re-raise exception to preserve program behavior
        return False  # False means we don't suppress the exception
    
    def set_output(self, output: Any) -> None:
        """
        Set the output value for the traced execution.
        
        This is useful when you want to capture the return value in a context manager.
        Note: For function decorators, output is captured automatically.
        
        Args:
            output: The output value to record
        """
        # Store output for use in __exit__
        self._output = output


def trace_function(
    logger: EventLogger,
    event_type: EventType,
    session_id: Optional[str] = None,
    input_summary_fn: Optional[Callable] = None,
    metadata_fn: Optional[Callable] = None,
):
    """
    Decorator factory for tracing function execution.
    
    This is a convenience wrapper around Tracer that works as a decorator.
    It automatically captures function inputs and return values.
    
    Args:
        logger: EventLogger instance to emit events to
        event_type: Type of event to emit
        session_id: Optional session identifier
        input_summary_fn: Optional function to summarize inputs: fn(*args, **kwargs) -> summary
        metadata_fn: Optional function to generate metadata: fn(*args, **kwargs) -> dict
    
    Example:
        @trace_function(logger, EventType.TOOL_CALL)
        def my_function(x, y):
            return x + y
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate input summary
            if input_summary_fn:
                input_summary = input_summary_fn(*args, **kwargs)
            else:
                # Default: capture args and kwargs
                input_summary = {"args": args, "kwargs": kwargs}
            
            # Generate metadata
            if metadata_fn:
                metadata = metadata_fn(*args, **kwargs)
            else:
                metadata = {}
            
            # Trace execution
            tracer = Tracer(
                logger=logger,
                event_type=event_type,
                session_id=session_id,
                input_summary=input_summary,
                metadata=metadata,
            )
            with tracer:
                result = func(*args, **kwargs)
                # Store output before context manager exits
                tracer.set_output(result)
            
            return result
        
        return wrapper
    return decorator
