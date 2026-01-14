"""
Compare agent behavior before and after intervention.

This script demonstrates the impact of adding input validation to guard against
empty tool outputs in the ResearchAgent.
"""

from argus import EventLogger
from argus.inspector import TraceInspector
from examples.research_agent import ResearchAgent


def run_agent_and_analyze(agent, question, run_name):
    """Run agent and return events and analysis."""
    logger = EventLogger()
    agent.logger = logger  # Use fresh logger
    
    print(f"\n{'=' * 80}")
    print(f"{run_name}")
    print(f"{'=' * 80}\n")
    
    try:
        result = agent.answer_question(question)
        print(f"Status: {result['status']}")
        if 'answer' in result:
            print(f"Answer: {result['answer'][:100]}...")
    except Exception as e:
        print(f"Agent failed: {type(e).__name__}: {e}")
    
    events = logger.get_events()
    
    # Quick summary
    print(f"\nTotal events: {len(events)}")
    failure_events = [e for e in events if e.status == "failure"]
    termination_events = [e for e in events if e.event_type.value == "termination"]
    
    if failure_events:
        print(f"Failure events: {len(failure_events)}")
        for fe in failure_events:
            print(f"  - {fe.event_type.value}: {fe.error}")
    
    if termination_events:
        term = termination_events[0]
        print(f"Termination: {term.status}")
        if term.error:
            print(f"  Error: {term.error}")
    
    return events, logger


def compare_traces(before_events, after_events):
    """Compare before and after traces."""
    print(f"\n{'=' * 80}")
    print("SIDE-BY-SIDE COMPARISON")
    print(f"{'=' * 80}\n")
    
    print("BEFORE INTERVENTION:")
    print("-" * 80)
    before_inspector = TraceInspector(before_events)
    before_analysis = before_inspector.analyze_failure()
    
    if before_analysis:
        print(f"Terminal failure: {before_analysis['terminal_failure'].error if before_analysis['terminal_failure'] else 'N/A'}")
        if before_analysis['root_cause']:
            print(f"Root cause: {before_analysis['root_cause']['description']}")
        print(f"Failure chain length: {len(before_analysis['failure_chain'])}")
    
    # Find key events
    before_tool_calls = [e for e in before_events if e.event_type.value == "tool_call"]
    before_failures = [e for e in before_events if e.event_type.value == "failure"]
    before_terminations = [e for e in before_events if e.event_type.value == "termination"]
    
    print(f"Tool calls: {len(before_tool_calls)}")
    print(f"Failure events: {len(before_failures)}")
    print(f"Termination events: {len(before_terminations)}")
    
    # Check where failure occurred
    if before_terminations:
        term = before_terminations[0]
        if term.status == "failure":
            print(f"Failure point: termination (after synthesis attempt)")
    
    print("\nAFTER INTERVENTION:")
    print("-" * 80)
    after_inspector = TraceInspector(after_events)
    after_analysis = after_inspector.analyze_failure()
    
    if after_analysis:
        print(f"Terminal failure: {after_analysis['terminal_failure'].error if after_analysis['terminal_failure'] else 'N/A'}")
        if after_analysis['root_cause']:
            print(f"Root cause: {after_analysis['root_cause']['description']}")
        print(f"Failure chain length: {len(after_analysis['failure_chain'])}")
    
    # Find key events
    after_tool_calls = [e for e in after_events if e.event_type.value == "tool_call"]
    after_failures = [e for e in after_events if e.event_type.value == "failure"]
    after_terminations = [e for e in after_events if e.event_type.value == "termination"]
    
    print(f"Tool calls: {len(after_tool_calls)}")
    print(f"Failure events: {len(after_failures)}")
    print(f"Termination events: {len(after_terminations)}")
    
    # Check where failure occurred
    if after_terminations:
        term = after_terminations[0]
        if term.status == "failure":
            # Check if there's a failure event before termination
            validation_failure = next((e for e in after_events if e.metadata.get("intervention") == "input_validation"), None)
            if validation_failure:
                print(f"Failure point: input validation (after search, before selection)")
    
    print("\nKEY DIFFERENCES:")
    print("-" * 80)
    
    # Event count comparison
    print(f"Total events: {len(before_events)} -> {len(after_events)} ({len(after_events) - len(before_events):+d})")
    print(f"Failure events: {len(before_failures)} -> {len(after_failures)} ({len(after_failures) - len(before_failures):+d})")
    
    # Check if synthesis was attempted
    before_synthesis = [e for e in before_events if e.metadata.get("step") == "answer_synthesis"]
    after_synthesis = [e for e in after_events if e.metadata.get("step") == "answer_synthesis"]
    
    print(f"Synthesis attempts: {len(before_synthesis)} -> {len(after_synthesis)} ({len(after_synthesis) - len(before_synthesis):+d})")
    
    # Check for validation event
    validation_event = next((e for e in after_events if e.metadata.get("intervention") == "input_validation"), None)
    if validation_event:
        print(f"New event type: validation failure (intervention)")
        print(f"  Error: {validation_event.error}")
    
    # Execution flow
    print("\nEXECUTION FLOW CHANGES:")
    print("-" * 80)
    print("BEFORE: question -> queries -> search -> selection -> synthesis -> [IndexError]")
    print("AFTER:  question -> queries -> search -> [validation failure] -> termination")
    
    print("\nTRADE-OFFS:")
    print("-" * 80)
    print("BENEFITS:")
    print("  - Failure occurs earlier (before synthesis attempt)")
    print("  - Clear error message (no cryptic IndexError)")
    print("  - No wasted computation on synthesis with empty data")
    print("  - Explicit validation event in trace")
    print("\nLIMITATIONS:")
    print("  - Agent still fails (doesn't handle empty results gracefully)")
    print("  - No fallback strategy (can't proceed without results)")
    print("  - User gets error instead of partial answer")


def main():
    """Run comparison."""
    question = "What is xyz123 obscure topic?"
    
    # Run BEFORE intervention (need to use original agent without validation)
    # For this demo, we'll run the current agent which has the intervention
    # In a real scenario, you'd compare against a version without the fix
    
    print("=" * 80)
    print("INTERVENTION COMPARISON: Input Validation")
    print("=" * 80)
    print("\nIntervention: Guard against empty tool outputs")
    print("Strategy: Validate search results before proceeding to selection/synthesis")
    print()
    
    # Run agent with intervention
    logger_after = EventLogger()
    agent_after = ResearchAgent(logger_after, session_id="after-intervention")
    
    try:
        agent_after.answer_question(question)
    except Exception:
        pass
    
    after_events = logger_after.get_events()
    
    # Print detailed trace for after
    print("\n" + "=" * 80)
    print("AFTER INTERVENTION - DETAILED TRACE")
    print("=" * 80)
    after_inspector = TraceInspector(after_events)
    after_inspector.print_trace()
    after_inspector.print_analysis()
    
    # For comparison, we need the before trace
    # In practice, you'd load this from a saved trace
    # For this demo, we'll describe what changed
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print("\nBEFORE INTERVENTION:")
    print("  - Agent attempted synthesis with empty results")
    print("  - Failed with IndexError in synthesis step")
    print("  - No explicit validation of search results")
    print("  - Failure occurred late in execution")
    
    print("\nAFTER INTERVENTION:")
    print("  - Agent validates search results immediately after search")
    print("  - Fails early with clear error message")
    print("  - Validation failure event explicitly recorded")
    print("  - No synthesis attempt (saves computation)")
    
    print("\nNEW EVENT IN TRACE:")
    validation_events = [e for e in after_events if e.metadata.get("intervention") == "input_validation"]
    if validation_events:
        ve = validation_events[0]
        print(f"  - failure event with intervention metadata")
        print(f"    Type: {ve.event_type.value}")
        print(f"    Error: {ve.error}")
        print(f"    Step: {ve.metadata.get('step')}")
    
    print("\nEVENTS REMOVED FROM TRACE:")
    print("  - No synthesis LLM call (prevented by early failure)")
    print("  - No IndexError (replaced by controlled ValueError)")


if __name__ == "__main__":
    main()
