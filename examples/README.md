# Argus Examples

This directory contains runnable examples demonstrating Argus observability for AI agents.

## Example Scripts

### `research_agent.py`
Multi-step AI agent demonstrating realistic agent behavior:
- LLM calls for query generation and answer synthesis
- Tool calls (search) with retry logic
- Decision-making for result selection
- Intentional imperfections for failure analysis

**Run**: `python -m examples.research_agent`

### `failure_demo.py`
Demonstrates a failure scenario: empty search results causing downstream failure.
- Shows how Argus captures failure events
- Displays complete event trace
- Analyzes failure root cause

**Run**: `python -m examples.failure_demo`

### `inspect_failure_trace.py`
Shows trace inspection and analysis using `TraceInspector`:
- Human-readable execution trace
- Failure root cause analysis
- Early warning signal detection

**Run**: `python -m examples.inspect_failure_trace`

### `before_after_comparison.py`
Compares agent behavior before and after intervention:
- Side-by-side execution flow comparison
- Event trace differences
- Trade-off analysis

**Run**: `python -m examples.before_after_comparison`

### `tracer_example.py`
Basic usage examples for the `Tracer` context manager:
- Context manager usage
- Function decorator usage
- Error handling

**Run**: `python -m examples.tracer_example`

## Documentation

- **`README.md`** (this file): Overview of examples
- **`FAILURE_ANALYSIS.md`**: Detailed analysis of the empty-search failure scenario
- **`INSPECTOR_EXPLANATION.md`**: How the trace inspector supports debugging and research
- **`intervention_research_note.md`**: Research note on input validation intervention

## Research Agent Details

The `ResearchAgent` demonstrates how Argus instruments a realistic AI agent.

## Agent Architecture

The `ResearchAgent` follows a typical AI agent pattern:

1. **Question Reception** → Decision event (question received)
2. **Query Generation** → LLM call (generate search queries)
3. **Information Retrieval** → Tool calls (search with retry logic)
4. **Result Selection** → Decision event (choose relevant results)
5. **Answer Synthesis** → LLM call (synthesize final answer)
6. **Termination** → Termination event (success or failure)

## Reasoning Flow

```
User Question
    ↓
[Decision] Question received
    ↓
[LLM Call] Generate search queries
    ↓
[Tool Call] Search for information (with retries)
    ↓
[Decision] Select relevant results
    ↓
[LLM Call] Synthesize answer
    ↓
[Termination] Return result
```

## Why This Agent is Representative

This agent demonstrates realistic AI agent behavior because:

1. **Multi-step reasoning**: Breaks complex tasks into sequential steps
2. **External dependencies**: Calls tools (search) that can fail
3. **LLM integration**: Uses language models for reasoning (query generation, synthesis)
4. **Decision points**: Makes choices about which information to use
5. **Error handling**: Has retry logic that can succeed or fail
6. **State management**: Maintains context across steps using parent_id

## Intentional Imperfections

The agent includes several suboptimal behaviors that Argus can surface:

1. **Empty result handling**: Doesn't validate that search results exist before using them
2. **Retry exhaustion**: Retry mechanism can fail after max attempts without graceful degradation
3. **No input validation**: Doesn't check if the question is empty or malformed
4. **Simple selection**: Uses first N results without quality filtering
5. **No timeout handling**: Could hang if LLM calls take too long

## What Argus Can Surface

With this agent, Argus enables analysis of:

### Failure Modes
- **Tool failures**: When search_tool() raises exceptions
- **Retry exhaustion**: When retries are exhausted and operations fail
- **Empty result errors**: When agent tries to process empty results
- **LLM failures**: When mock_llm_call() fails (simulated)

### Cost Behavior
- **LLM call frequency**: How many LLM calls per question
- **Tool call patterns**: Which tools are called most often
- **Retry costs**: How many retries occur and their success rate
- **Execution duration**: Time spent in each step

### Decision Analysis
- **Selection quality**: Whether selected results are actually used
- **Query effectiveness**: Whether generated queries return useful results
- **Step ordering**: Whether the reasoning flow is optimal

### Performance Patterns
- **Bottlenecks**: Which steps take the longest
- **Retry overhead**: Cost of retry mechanisms
- **Sequential vs parallel**: Whether steps could be parallelized

## Example Event Trace

A successful run produces events like:
1. `decision` (started) - Question received
2. `llm_call` (started) - Query generation begins
3. `llm_call` (success) - Queries generated
4. `tool_call` (started) - Search begins
5. `tool_call` (success) - Search completed
6. `decision` (started) - Result selection begins
7. `decision` (success) - Results selected
8. `llm_call` (started) - Answer synthesis begins
9. `llm_call` (success) - Answer synthesized
10. `termination` (success) - Agent completed

A failed run might show:
- `tool_call` (failure) - Search failed
- `retry` (retrying) - Retry attempt
- `retry` (retrying) - Another retry
- `failure` (failure) - Retries exhausted
- `termination` (failure) - Agent failed

### Agent Architecture

The `ResearchAgent` follows a typical AI agent pattern:
