# Trace Inspector: Supporting Debugging and Research

## Overview

The `TraceInspector` transforms raw Argus event data into human-readable insights about agent execution, failures, and behavior patterns. It provides structured analysis without requiring dashboards, visualizations, or machine learning.

## How It Supports Debugging

### 1. **Complete Execution Visibility**

The inspector shows the full execution trace with:
- Event hierarchy (parent-child relationships via indentation)
- Event types, status, and duration
- Key metadata (results_count, retry_count, step information)
- Input/output summaries for important events

**Example Output:**
```
decision     | started    | step: question_received
  llm_call     | [OK] success | duration: 0.100s | step: query_generation
  tool_call    | [OK] success | duration: 0.050s | tool: search, results: 0
  decision     | [OK] success | step: result_selection, total_results: 0
  termination  | [FAILURE] failure
```

This allows developers to:
- See exactly what the agent did step-by-step
- Understand the execution flow and timing
- Identify where time was spent
- Trace relationships between events

### 2. **Failure Root Cause Analysis**

The inspector automatically identifies:
- **What failed**: The terminal failure event and error message
- **Why it failed**: Root cause (e.g., empty tool output, retry exhaustion)
- **Assumption violated**: What the agent assumed that wasn't true
- **Early warning signal**: The first event that should have been detected

**Example Analysis:**
```
WHAT FAILED:
  The agent terminated with failure: list index out of range

WHY IT FAILED:
  Tool call returned empty results
  Tool returned: 0 results

ASSUMPTION VIOLATED:
  Agent assumed tool calls would return usable data
  Agent did not validate that results list was non-empty

EARLY WARNING SIGNAL:
  Event #5: Tool call returned 0 results
    The agent should have detected this and handled it
    Instead, the agent proceeded to use empty results
```

This enables developers to:
- Quickly understand the failure without manual trace inspection
- Identify the root cause, not just the symptom
- Understand what assumptions were violated
- See where validation should have been added

### 3. **Failure Chain Reconstruction**

The inspector builds the complete failure chain showing:
- The sequence of events leading to failure
- Which events were warnings (e.g., empty results)
- How the failure propagated through the system

**Example Chain:**
```
FAILURE CHAIN:
  1. decision (started)
  2. tool_call (success)
     -> Tool returned 0 results
  3. decision (success)
     -> Agent selected from 0 results
  4. termination (failure)
     Error: list index out of range
```

This helps developers:
- Understand the failure propagation path
- See which steps should have caught the problem
- Identify where to add validation or error handling

## How It Supports Research

### 1. **Pattern Discovery**

By analyzing multiple traces, researchers can:
- Identify common failure modes across different runs
- Find patterns in agent behavior (e.g., always fails when search returns empty)
- Understand which assumptions are frequently violated
- Discover correlations between events and outcomes

### 2. **Behavioral Analysis**

The structured output enables:
- Comparing successful vs. failed runs
- Understanding decision-making patterns
- Analyzing tool usage effectiveness
- Studying retry behavior and success rates

### 3. **Hypothesis Testing**

Researchers can:
- Test hypotheses about failure causes
- Validate assumptions about agent behavior
- Study the impact of different inputs on outcomes
- Analyze the effectiveness of error handling strategies

### 4. **Reproducibility**

The inspector provides:
- Complete, structured event traces
- Consistent analysis format across runs
- Easy comparison between different executions
- Foundation for automated analysis tools

## Design Principles

### Human-Readable, Not Metrics-Focused

The inspector prioritizes:
- **Reasoning over numbers**: Explains *why* something failed, not just statistics
- **Narrative over charts**: Tells a story of what happened
- **Insight over aggregation**: Highlights specific problems, not averages

### No External Dependencies

The inspector:
- Uses only Python standard library
- No visualization libraries (charts, graphs)
- No machine learning (pattern recognition is rule-based)
- Works with plain text output

### Extensible Analysis

The inspector is designed to be extended with:
- Additional root cause detection patterns
- Custom analysis functions
- Different output formats
- Integration with other analysis tools

## Usage Example

```python
from argus import EventLogger
from argus.inspector import TraceInspector
from examples.research_agent import ResearchAgent

# Run agent and capture events
logger = EventLogger()
agent = ResearchAgent(logger, session_id="demo")
try:
    agent.answer_question("What is xyz123 obscure topic?")
except Exception:
    pass  # Expected failure

# Analyze the trace
events = logger.get_events()
inspector = TraceInspector(events)
inspector.print_trace()
inspector.print_analysis()
```

Or load from storage:

```python
from argus.inspector import inspect_trace_from_storage

inspect_trace_from_storage("traces/session-123.json")
```

## Key Benefits

1. **Fast Debugging**: Quickly understand failures without manual trace inspection
2. **Clear Insights**: Human-readable analysis explains what happened and why
3. **Research Support**: Structured data enables pattern discovery and hypothesis testing
4. **No Dependencies**: Works anywhere Python runs, no external libraries needed
5. **Extensible**: Easy to add new analysis patterns and insights

The inspector transforms raw event data into actionable insights, making agent behavior debuggable and researchable.
