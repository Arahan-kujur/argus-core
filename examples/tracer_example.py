"""
Example usage of Argus Tracer.

This demonstrates how to use the Tracer to instrument code with minimal intrusion.
"""

from argus import EventLogger, EventType, Tracer, trace_function


def example_context_manager():
    """Example: Using Tracer as a context manager."""
    logger = EventLogger()
    
    # Example function we want to trace
    def compute_sum(a, b):
        return a + b
    
    # Trace execution using context manager
    with Tracer(
        logger=logger,
        event_type=EventType.TOOL_CALL,
        session_id="example-session",
        input_summary={"a": 5, "b": 3},
        metadata={"function": "compute_sum"},
    ):
        result = compute_sum(5, 3)
        # Set output for the trace
        # Note: In practice, you'd do this right before the with block ends
        # For this example, we'll show it can be done
    
    # Get the traced events
    events = logger.get_events()
    print(f"Recorded {len(events)} events")
    for event in events:
        print(f"  {event.event_type.value}: {event.status} (duration: {event.metadata.get('duration_seconds', 0):.4f}s)")


def example_decorator():
    """Example: Using Tracer as a function decorator."""
    logger = EventLogger()
    
    # Decorate a function to automatically trace it
    @trace_function(logger, EventType.TOOL_CALL, session_id="example-session")
    def multiply(x, y):
        """Multiply two numbers."""
        return x * y
    
    # Call the function - it's automatically traced
    result = multiply(4, 7)
    print(f"Result: {result}")
    
    # Get the traced events
    events = logger.get_events()
    print(f"Recorded {len(events)} events")
    for event in events:
        if event.status == "success":
            print(f"  {event.event_type.value}: {event.status}")
            print(f"    Input: {event.input}")
            print(f"    Output: {event.output}")


def example_error_handling():
    """Example: Tracer preserves exceptions."""
    logger = EventLogger()
    
    def failing_function():
        raise ValueError("This is a test error")
    
    # Trace execution that raises an exception
    try:
        with Tracer(
            logger=logger,
            event_type=EventType.FAILURE,
            session_id="error-example",
            input_summary={"function": "failing_function"},
        ):
            failing_function()
    except ValueError as e:
        print(f"Exception caught (as expected): {e}")
    
    # Check that the error was recorded
    events = logger.get_events()
    for event in events:
        if event.status == "failure":
            print(f"Recorded failure: {event.error}")


if __name__ == "__main__":
    print("=== Context Manager Example ===")
    example_context_manager()
    print()
    
    print("=== Decorator Example ===")
    example_decorator()
    print()
    
    print("=== Error Handling Example ===")
    example_error_handling()
