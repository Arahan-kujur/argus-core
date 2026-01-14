# Argus

A passive, framework-agnostic observability layer for AI agents that records structured events to enable debugging, failure analysis, and cost tracking.

## Problem

AI agents are opaque. When they fail, it's difficult to understand why. When they succeed, it's unclear what they did or how much it cost. Traditional logging doesn't capture the structure of agent reasoning—the LLM calls, tool invocations, decisions, and retries that compose agent behavior.

Argus provides structured event recording without modifying agent behavior, making agent execution inspectable and analyzable.

## Design Philosophy

- **Passive**: Observes and records only. Does not modify agent execution.
- **Event-based**: Records discrete, timestamped events with clear schemas.
- **Framework-agnostic**: Works with any agent implementation, LLM provider, or tooling stack.
- **Failures as first-class data**: Failures are events to record, not exceptions to hide.
- **Analysis-friendly**: Structured for post-hoc debugging and research.

## Core Components

- **Event Model**: Minimal, extensible event abstraction (`Event`, `EventType`)
- **EventLogger**: In-memory event recorder with automatic ID and timestamp assignment
- **Storage**: Pluggable backends (JSON included) for persistence
- **Tracer**: Context manager for instrumenting code blocks
- **Inspector**: Human-readable trace analysis and failure detection

## Usage

```python
from argus import EventLogger, EventType, Tracer

logger = EventLogger()

with Tracer(logger, EventType.TOOL_CALL, input_summary={"query": "test"}):
    result = search_tool("test")

events = logger.get_events()
for event in events:
    print(f"{event.event_type.value}: {event.status}")
```

## Examples

The `examples/` directory contains:

- **`research_agent.py`**: Multi-step AI agent demonstrating LLM calls, tool invocations, and decision-making
- **`failure_demo.py`**: Demonstrates failure scenario with empty search results
- **`inspect_failure_trace.py`**: Shows trace inspection and analysis
- **`before_after_comparison.py`**: Compares agent behavior before and after intervention

See `examples/README.md` for detailed documentation.

## What Argus Does NOT Do

- **Does not control agent behavior**: No hooks that modify execution flow
- **Does not assume specific architectures**: Works with any agent pattern
- **Does not provide runtime decision-making**: Records only, no active intervention
- **Does not wrap LLM libraries**: Not a wrapper around OpenAI, Anthropic, etc.
- **Does not implement agent logic**: Not an agent framework or orchestration system
- **Does not provide real-time feedback**: Focused on recording, not live control

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/argus-core.git
cd argus-core

# Install (if using as package)
pip install -e .
```

## Testing

```bash
python test_argus.py
```

## License

MIT License (see LICENSE file)
