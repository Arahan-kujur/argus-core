"""
Demonstration of a realistic failure scenario in ResearchAgent.

This script shows how Argus captures a failure that emerges naturally from
the agent's logic: empty search results causing downstream failure.
"""

from argus import EventLogger
from examples.research_agent import ResearchAgent


def demonstrate_failure():
    """
    Demonstrate the empty search results failure scenario.
    
    This failure occurs when:
    1. Agent generates queries for an obscure topic
    2. Search returns empty results (no data available)
    3. Agent doesn't validate results before using them
    4. Agent tries to access results[0] assuming data exists
    5. IndexError occurs, causing agent failure
    """
    logger = EventLogger()
    agent = ResearchAgent(logger, session_id="failure-demo-1")
    
    print("=" * 70)
    print("FAILURE DEMONSTRATION: Empty Search Results Causing Downstream Failure")
    print("=" * 70)
    print()
    print("Question: 'What is xyz123 obscure topic?'")
    print("(This question will generate queries that return no search results)")
    print()
    
    try:
        result = agent.answer_question("What is xyz123 obscure topic?")
        print(f"Answer: {result['answer']}")
        print(f"Status: {result['status']}")
    except Exception as e:
        print(f"\n[FAILED] Agent failed with: {type(e).__name__}: {e}")
        print()
    
    print("=" * 70)
    print("ARGUS EVENT TRACE")
    print("=" * 70)
    print()
    
    events = logger.get_events()
    
    # Group events by step for clarity
    step_events = {}
    for event in events:
        step = event.metadata.get("step", "other")
        if step not in step_events:
            step_events[step] = []
        step_events[step].append(event)
    
    print("Event Flow:")
    print("-" * 70)
    
    for i, event in enumerate(events, 1):
        # Format event display
        event_type = event.event_type.value
        status = event.status or "N/A"
        step = event.metadata.get("step", "N/A")
        duration = event.metadata.get("duration_seconds", 0)
        
        # Show parent relationship
        parent_info = f" (parent: {event.parent_id[:8]}...)" if event.parent_id else ""
        
        print(f"{i:2}. {event_type:12} | {status:8} | step: {step:20} | "
              f"duration: {duration:.3f}s{parent_info}")
        
        # Show key information
        if event.input:
            if isinstance(event.input, dict):
                if "question" in event.input:
                    print(f"    -> Question: {event.input['question']}")
                if "query" in event.input:
                    print(f"    -> Query: {event.input['query']}")
                if "total_results" in event.input:
                    print(f"    -> Total results: {event.input['total_results']}")
                if "results_count" in event.input:
                    print(f"    -> Results count: {event.input['results_count']}")
        
        if event.output:
            if isinstance(event.output, dict):
                if "queries" in event.output:
                    print(f"    -> Generated queries: {event.output['queries']}")
                if "results_count" in event.output:
                    print(f"    -> Results returned: {event.output['results_count']}")
                if "selected_count" in event.output:
                    print(f"    -> Selected results: {event.output['selected_count']}")
        
        if event.error:
            print(f"    -> [ERROR] {event.error}")
        
        # Highlight the failure point
        if event.event_type.value == "failure":
            print(f"    -> [FAILURE EVENT] {event.error}")
        if event.event_type.value == "termination" and event.status == "failure":
            print(f"    -> [TERMINATION] Agent failed")
    
    print()
    print("=" * 70)
    print("FAILURE ANALYSIS")
    print("=" * 70)
    print()
    
    # Analyze the failure
    failure_events = [e for e in events if e.event_type.value == "failure"]
    termination_events = [e for e in events if e.event_type.value == "termination" and e.status == "failure"]
    empty_result_events = [e for e in events if isinstance(e.output, dict) and e.output.get("results_count") == 0]
    
    print("Failure Indicators:")
    print(f"  - Failure events: {len(failure_events)}")
    print(f"  - Failed termination: {len(termination_events)}")
    print(f"  - Empty result tool calls: {len(empty_result_events)}")
    print()
    
    if empty_result_events:
        print("Root Cause Analysis:")
        print("  1. Search queries were generated successfully")
        print("  2. Search tool calls completed but returned 0 results")
        print("  3. Agent selected 0 results (decision completed)")
        print("  4. Agent attempted to synthesize answer with empty results")
        print("  5. Agent tried to access results[0] without validation")
        print("  6. IndexError occurred -> agent failure")
        print()
    
    print("What Argus Reveals:")
    print("  - Exact point of failure (synthesis step)")
    print("  - That search returned empty results (tool_call output)")
    print("  - That agent proceeded without validation (decision with 0 results)")
    print("  - The error type and message (IndexError)")
    print("  - The full event chain leading to failure")
    print("  - Timing information for each step")
    print()
    
    print(f"Total events recorded: {len(events)}")


if __name__ == "__main__":
    demonstrate_failure()
