# Testing Guide for Argus

## Quick Test

Run the comprehensive test suite:

```bash
python test_argus.py
```

This will test:
1. ✅ Imports - All modules can be imported
2. ✅ Event Creation - Events can be created
3. ✅ EventLogger - Events can be logged and retrieved
4. ✅ Storage - Events can be saved and loaded
5. ✅ Tracer - Code can be traced with context manager
6. ✅ TraceInspector - Traces can be analyzed
7. ✅ ResearchAgent - Example agent works
8. ✅ Integration - Full pipeline works

## Manual Testing

### Test Core Functionality

```python
from argus import EventLogger, EventType, Tracer

# Create logger
logger = EventLogger()

# Log an event
event = logger.log_event(
    event_type=EventType.LLM_CALL,
    status="success",
    input={"prompt": "test"}
)

# Get events
events = logger.get_events()
print(f"Logged {len(events)} events")
```

### Test Tracer

```python
from argus import EventLogger, EventType, Tracer

logger = EventLogger()

with Tracer(logger, EventType.TOOL_CALL, input_summary={"x": 1}):
    result = some_function(x=1)

events = logger.get_events()
print(f"Tracer created {len(events)} events")
```

### Test Storage

```python
from argus import EventLogger, JSONEventStorage

logger = EventLogger()
logger.log_event(EventType.DECISION, status="success")

# Save
storage = JSONEventStorage("test_trace.json")
storage.save(logger.get_events())

# Load
loaded_events = storage.load()
print(f"Loaded {len(loaded_events)} events")
```

### Test Inspector

```python
from argus import EventLogger, TraceInspector

logger = EventLogger()
# ... create events ...

inspector = TraceInspector(logger.get_events())
inspector.print_trace()
inspector.print_analysis()
```

### Test ResearchAgent

```python
from argus import EventLogger
from examples.research_agent import ResearchAgent

logger = EventLogger()
agent = ResearchAgent(logger, session_id="test")

try:
    result = agent.answer_question("What is Python?")
    print(f"Status: {result['status']}")
except Exception as e:
    print(f"Agent failed: {e}")

events = logger.get_events()
print(f"Created {len(events)} events")
```

## Test Examples

### Run Failure Demo

```bash
python -m examples.failure_demo
```

### Run Trace Inspection

```bash
python -m examples.inspect_failure_trace
```

### Run Intervention Comparison

```bash
python -m examples.before_after_comparison
```

## Expected Results

When everything works correctly, you should see:

- ✅ All imports succeed
- ✅ Events can be created and logged
- ✅ Events can be saved to and loaded from JSON
- ✅ Tracer captures execution with timing
- ✅ Inspector analyzes traces and identifies failures
- ✅ ResearchAgent creates events for all steps
- ✅ Full integration pipeline works

## Troubleshooting

### Import Errors

If imports fail, make sure you're in the project root directory:
```bash
cd Argus-core
python test_argus.py
```

### Module Not Found

If you get "ModuleNotFoundError", check that:
- You're running from the project root
- The `argus/` directory exists
- `argus/__init__.py` exists

### Storage Errors

If storage tests fail:
- Check file permissions
- Ensure the directory exists for JSON files
- Check that JSON serialization works (events must be JSON-serializable)

## Continuous Testing

For development, you can run tests after each change:

```bash
# Run all tests
python test_argus.py

# Run specific example
python -m examples.research_agent

# Check imports
python -c "from argus import Event, EventLogger; print('OK')"
```
