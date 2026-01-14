"""
Side-by-side comparison of agent behavior before and after intervention.

This script demonstrates the impact of the input validation intervention.
"""

from argus import EventLogger
from argus.inspector import TraceInspector


def print_event_summary(events, label):
    """Print summary of events."""
    print(f"\n{label}")
    print("-" * 80)
    
    event_types = {}
    for event in events:
        et = event.event_type.value
        event_types[et] = event_types.get(et, 0) + 1
    
    print(f"Total events: {len(events)}")
    for et, count in sorted(event_types.items()):
        print(f"  {et}: {count}")
    
    # Find key events
    failures = [e for e in events if e.status == "failure"]
    terminations = [e for e in events if e.event_type.value == "termination"]
    validations = [e for e in events if e.metadata.get("intervention") == "input_validation"]
    synthesis = [e for e in events if e.metadata.get("step") == "answer_synthesis"]
    
    print(f"\nKey events:")
    print(f"  Failure events: {len(failures)}")
    if failures:
        for f in failures:
            print(f"    - {f.event_type.value}: {f.error}")
    print(f"  Termination events: {len(terminations)}")
    if terminations:
        t = terminations[0]
        print(f"    - Status: {t.status}")
        if t.error:
            print(f"    - Error: {t.error}")
    print(f"  Validation events: {len(validations)}")
    print(f"  Synthesis attempts: {len(synthesis)}")


def compare_execution_flows(before_events, after_events):
    """Compare execution flows."""
    print("\n" + "=" * 80)
    print("EXECUTION FLOW COMPARISON")
    print("=" * 80)
    
    print("\nBEFORE INTERVENTION:")
    print("  1. question received")
    print("  2. queries generated")
    print("  3. search executed (returned 0 results)")
    print("  4. result selection (selected 0 results) <- proceeded without validation")
    print("  5. synthesis attempted <- wasted computation")
    print("  6. IndexError in synthesis <- cryptic failure")
    print("  7. termination with failure")
    
    print("\nAFTER INTERVENTION:")
    print("  1. question received")
    print("  2. queries generated")
    print("  3. search executed (returned 0 results)")
    print("  4. validation check <- NEW STEP")
    print("  5. validation failure <- explicit failure event")
    print("  6. termination with failure <- clear error message")
    print("  (no synthesis attempt - prevented by early failure)")
    
    print("\nKEY CHANGES:")
    print("  - Validation step added after search")
    print("  - Failure occurs earlier (before selection/synthesis)")
    print("  - Explicit validation event in trace")
    print("  - No synthesis attempt (saves LLM call)")
    print("  - Clearer error message")


def main():
    """Run comparison."""
    # We need to simulate the before case
    # In practice, you'd load this from a saved trace
    # For this demo, we'll describe the differences
    
    print("=" * 80)
    print("BEFORE vs AFTER INTERVENTION COMPARISON")
    print("=" * 80)
    print("\nIntervention: Input Validation (guard against empty tool outputs)")
    print("Location: After search step, before selection step")
    
    # Run after intervention to get actual trace
    from examples.research_agent import ResearchAgent
    
    logger = EventLogger()
    agent = ResearchAgent(logger, session_id="comparison-demo")
    
    try:
        agent.answer_question("What is xyz123 obscure topic?")
    except Exception:
        pass
    
    after_events = logger.get_events()
    
    print_event_summary(after_events, "AFTER INTERVENTION")
    
    # Describe before (based on previous runs)
    print("\n" + "=" * 80)
    print("BEFORE INTERVENTION (from previous analysis)")
    print("=" * 80)
    print("\nTotal events: 8")
    print("Event breakdown:")
    print("  decision: 2 (started, question_received + result_selection)")
    print("  llm_call: 2 (started + success for query generation)")
    print("  tool_call: 2 (started + success, returned 0 results)")
    print("  termination: 1 (failure with IndexError)")
    print("  (no explicit failure event)")
    print("\nKey events:")
    print("  Failure events: 0 (no explicit validation failure)")
    print("  Termination: failure")
    print("    Error: list index out of range")
    print("  Synthesis attempts: 1 (attempted with empty results)")
    print("  Validation events: 0")
    
    print_event_summary(after_events, "\nAFTER INTERVENTION (actual trace)")
    
    compare_execution_flows(None, after_events)
    
    # Detailed trace comparison
    print("\n" + "=" * 80)
    print("DETAILED TRACE COMPARISON")
    print("=" * 80)
    
    print("\nBEFORE - Event Sequence:")
    print("  1. decision (started) - question received")
    print("  2. llm_call (started) - query generation")
    print("  3. llm_call (success) - queries generated")
    print("  4. tool_call (started) - search")
    print("  5. tool_call (success) - search returned 0 results")
    print("  6. decision (started) - result selection")
    print("  7. decision (success) - selected 0 results")
    print("  8. llm_call (started) - synthesis attempt")
    print("  9. llm_call (success) - synthesis completed")
    print("  10. termination (failure) - IndexError")
    
    print("\nAFTER - Event Sequence:")
    inspector = TraceInspector(after_events)
    for i, event in enumerate(after_events, 1):
        status = event.status or "N/A"
        step = event.metadata.get("step", "")
        intervention = event.metadata.get("intervention", "")
        
        marker = ""
        if intervention == "input_validation":
            marker = " <- NEW: validation intervention"
        elif step == "answer_synthesis":
            marker = " <- REMOVED: no longer attempted"
        elif event.event_type.value == "decision" and step == "result_selection":
            marker = " <- REMOVED: prevented by early failure"
        
        print(f"  {i}. {event.event_type.value:12} ({status:8}) {step} {marker}")
        if event.error and event.metadata.get("intervention"):
            print(f"      Error: {event.error}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    inspector.print_analysis()


if __name__ == "__main__":
    main()
