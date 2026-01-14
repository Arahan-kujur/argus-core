# Argus Project Structure

## Root Directory
```
Argus-core/
├── argus/              # Core library package
│   ├── __init__.py     # Package initialization and exports
│   ├── events.py       # Event model (Event, EventType)
│   ├── logger.py       # EventLogger class
│   ├── storage.py      # Storage interface and JSONEventStorage
│   ├── tracer.py       # Tracer and trace_function decorator
│   └── inspector.py    # TraceInspector for analysis
│
└── examples/           # Examples and documentation
    ├── research_agent.py              # Example AI agent
    ├── failure_demo.py                # Failure scenario demonstration
    ├── inspect_failure_trace.py       # Trace inspection example
    ├── tracer_example.py              # Tracer usage examples
    ├── intervention_comparison.py     # Intervention comparison
    ├── before_after_comparison.py     # Before/after analysis
    ├── README.md                      # Examples documentation
    ├── FAILURE_ANALYSIS.md            # Failure analysis documentation
    ├── INSPECTOR_EXPLANATION.md       # Inspector documentation
    └── intervention_research_note.md  # Intervention research note
```

## Core Library (`argus/`)

### `__init__.py`
- Exports: Event, EventType, EventLogger, EventStorage, JSONEventStorage, Tracer, trace_function, TraceInspector, inspect_trace_from_storage, inspect_trace_from_events

### `events.py`
- EventType enum (LLM_CALL, TOOL_CALL, DECISION, RETRY, FAILURE, TERMINATION)
- Event dataclass (core event model)

### `logger.py`
- EventLogger class (in-memory event recording)

### `storage.py`
- EventStorage abstract base class
- JSONEventStorage implementation

### `tracer.py`
- Tracer context manager class
- trace_function decorator factory

### `inspector.py`
- TraceInspector class (trace analysis)
- inspect_trace_from_storage function
- inspect_trace_from_events function

## Examples (`examples/`)

### Python Scripts
- `research_agent.py`: Example AI agent with multi-step reasoning
- `failure_demo.py`: Demonstrates failure scenario
- `inspect_failure_trace.py`: Shows trace inspection usage
- `tracer_example.py`: Tracer usage examples
- `intervention_comparison.py`: Intervention comparison tool
- `before_after_comparison.py`: Before/after analysis tool

### Documentation
- `README.md`: Examples overview and usage
- `FAILURE_ANALYSIS.md`: Failure scenario analysis
- `INSPECTOR_EXPLANATION.md`: Inspector usage and benefits
- `intervention_research_note.md`: Intervention research documentation

## Verification

✅ All core library files are in `argus/`
✅ All examples and documentation are in `examples/`
✅ Imports work correctly (`from argus import ...`)
✅ No files in wrong locations
✅ Package structure is correct
