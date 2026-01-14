"""
Example: Inspect the failure trace from the empty search results scenario.

This demonstrates how the TraceInspector analyzes agent failures and provides
human-readable insights into what went wrong and why.
"""

from argus import EventLogger
from argus.inspector import TraceInspector
from examples.research_agent import ResearchAgent


def main():
    """Run agent, save trace, then inspect it."""
    # Run the agent and capture events
    logger = EventLogger()
    agent = ResearchAgent(logger, session_id="failure-inspection-demo")
    
    print("Running agent with question that will cause failure...")
    print()
    
    try:
        agent.answer_question("What is xyz123 obscure topic?")
    except Exception:
        pass  # Expected failure
    
    # Get events and inspect
    events = logger.get_events()
    
    print("\n" + "=" * 80)
    print("USING TRACE INSPECTOR TO ANALYZE FAILURE")
    print("=" * 80)
    print()
    
    inspector = TraceInspector(events)
    inspector.print_trace()
    inspector.print_analysis()


if __name__ == "__main__":
    main()
