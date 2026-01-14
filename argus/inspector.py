"""
Trace inspection and analysis utility for Argus.

This module provides human-readable analysis of event traces to support
debugging and research into agent behavior and failure modes.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime

from argus.events import Event, EventType
from argus.storage import JSONEventStorage


class TraceInspector:
    """
    Inspects and analyzes Argus event traces.
    
    This class exists to transform raw event data into human-readable
    insights about agent execution, failures, and behavior patterns.
    """
    
    def __init__(self, events: List[Event]):
        """
        Initialize inspector with events.
        
        Args:
            events: List of Event instances to analyze
        """
        self.events = events
        self._event_map: Dict[str, Event] = {e.event_id: e for e in events}
        self._children_map: Dict[str, List[Event]] = self._build_children_map()
    
    def _build_children_map(self) -> Dict[str, List[Event]]:
        """Build a map of parent_id -> list of child events."""
        children = {}
        for event in self.events:
            if event.parent_id:
                if event.parent_id not in children:
                    children[event.parent_id] = []
                children[event.parent_id].append(event)
        return children
    
    def print_trace(self):
        """Print a human-readable execution trace."""
        print("=" * 80)
        print("ARGUS EXECUTION TRACE")
        print("=" * 80)
        print()
        
        # Find root events (events without parent_id or whose parent isn't in the trace)
        root_events = [
            e for e in self.events
            if not e.parent_id or e.parent_id not in self._event_map
        ]
        
        # Sort by timestamp
        root_events.sort(key=lambda e: e.timestamp)
        
        for root_event in root_events:
            self._print_event_tree(root_event, indent=0, visited=set())
        
        print()
    
    def _print_event_tree(self, event: Event, indent: int, visited: set):
        """Recursively print event tree with indentation."""
        if event.event_id in visited:
            return  # Avoid cycles
        visited.add(event.event_id)
        
        # Print this event
        prefix = "  " * indent
        duration = event.metadata.get("duration_seconds", 0)
        
        # Format status with highlighting
        status_str = self._format_status(event.status)
        
        # Format event type
        event_type_str = event.event_type.value
        
        # Build description line
        desc_parts = [f"{prefix}{event_type_str:12} | {status_str:10}"]
        
        if duration > 0:
            desc_parts.append(f"duration: {duration:.3f}s")
        
        # Add key metadata
        metadata_str = self._format_key_metadata(event)
        if metadata_str:
            desc_parts.append(metadata_str)
        
        print(" | ".join(desc_parts))
        
        # Print input/output summary if relevant
        self._print_event_details(event, indent + 1)
        
        # Print children
        children = self._children_map.get(event.event_id, [])
        children.sort(key=lambda e: e.timestamp)
        for child in children:
            self._print_event_tree(child, indent + 1, visited)
    
    def _format_status(self, status: Optional[str]) -> str:
        """Format status with highlighting for failures."""
        if status == "failure":
            return f"[FAILURE] {status}"
        elif status == "success":
            return f"[OK] {status}"
        elif status == "retrying":
            return f"[RETRY] {status}"
        else:
            return status or "N/A"
    
    def _format_key_metadata(self, event: Event) -> str:
        """Extract and format key metadata for display."""
        parts = []
        
        # Step information
        step = event.metadata.get("step")
        if step:
            parts.append(f"step: {step}")
        
        # Tool information
        tool = event.metadata.get("tool")
        if tool:
            parts.append(f"tool: {tool}")
        
        # Retry information
        retry_count = event.metadata.get("retry_count")
        if retry_count is not None:
            parts.append(f"retry: {retry_count}")
        
        # Results count (important for failure analysis)
        if isinstance(event.output, dict):
            results_count = event.output.get("results_count")
            if results_count is not None:
                parts.append(f"results: {results_count}")
        
        if isinstance(event.input, dict):
            total_results = event.input.get("total_results")
            if total_results is not None:
                parts.append(f"total_results: {total_results}")
        
        return ", ".join(parts) if parts else ""
    
    def _print_event_details(self, event: Event, indent: int):
        """Print additional event details (input/output/error)."""
        prefix = "  " * indent
        
        # Show error if present
        if event.error:
            print(f"{prefix}  -> ERROR: {event.error}")
        
        # Show key input information
        if isinstance(event.input, dict):
            if "question" in event.input:
                print(f"{prefix}  -> Question: {event.input['question']}")
            if "query" in event.input:
                print(f"{prefix}  -> Query: {event.input['query']}")
        
        # Show key output information
        if isinstance(event.output, dict):
            if "queries" in event.output:
                queries = event.output["queries"]
                print(f"{prefix}  -> Generated queries: {queries}")
            if "selected_count" in event.output:
                print(f"{prefix}  -> Selected: {event.output['selected_count']} results")
    
    def analyze_failure(self) -> Optional[Dict]:
        """
        Analyze the trace for failures and return analysis.
        
        Returns:
            Dictionary with failure analysis, or None if no failure found
        """
        failure_events = [e for e in self.events if e.status == "failure"]
        termination_failures = [
            e for e in self.events
            if e.event_type == EventType.TERMINATION and e.status == "failure"
        ]
        
        if not failure_events and not termination_failures:
            return None
        
        analysis = {
            "has_failure": True,
            "failure_events": failure_events,
            "terminal_failure": termination_failures[0] if termination_failures else None,
            "root_cause": self._identify_root_cause(),
            "failure_chain": self._build_failure_chain(),
        }
        
        return analysis
    
    def _identify_root_cause(self) -> Optional[Dict]:
        """Identify the root cause of the failure."""
        # Look for tool calls that returned empty results
        empty_result_events = []
        for event in self.events:
            if event.event_type == EventType.TOOL_CALL:
                if isinstance(event.output, dict):
                    results_count = event.output.get("results_count", 0)
                    if results_count == 0:
                        empty_result_events.append(event)
        
        if empty_result_events:
            return {
                "type": "empty_tool_output",
                "event": empty_result_events[0],
                "description": "Tool call returned empty results",
            }
        
        # Look for retry exhaustion
        retry_events = [e for e in self.events if e.event_type == EventType.RETRY]
        if retry_events:
            last_retry = retry_events[-1]
            max_retries = last_retry.metadata.get("max_retries")
            retry_count = last_retry.input.get("retry_count") if isinstance(last_retry.input, dict) else None
            if retry_count and max_retries and retry_count >= max_retries:
                return {
                    "type": "retry_exhaustion",
                    "event": last_retry,
                    "description": f"Retries exhausted after {max_retries} attempts",
                }
        
        return None
    
    def _build_failure_chain(self) -> List[Event]:
        """Build the chain of events leading to failure."""
        failure_events = [e for e in self.events if e.status == "failure"]
        if not failure_events:
            return []
        
        # Start from the terminal failure and trace back
        terminal = next((e for e in self.events if e.event_type == EventType.TERMINATION and e.status == "failure"), None)
        if not terminal:
            return failure_events
        
        chain = [terminal]
        current = terminal
        
        # Trace back through parent_id chain to find root cause
        visited = set()
        while current.parent_id and current.parent_id not in visited:
            visited.add(current.parent_id)
            parent = self._event_map.get(current.parent_id)
            if not parent:
                break
            chain.insert(0, parent)
            current = parent
        
        # Also include events that led to the failure (empty results, etc.)
        # Find the tool_call that returned empty results and the decision that used it
        for event in self.events:
            if event in chain:
                continue
            # Include tool_call with empty results
            if event.event_type == EventType.TOOL_CALL:
                if isinstance(event.output, dict):
                    results_count = event.output.get("results_count", 0)
                    if results_count == 0:
                        # Check if this event is related to the failure (same parent chain)
                        if terminal.parent_id:
                            # Check if this event is in the same execution path
                            if self._is_ancestor(event.event_id, terminal.event_id) or event.parent_id == terminal.parent_id:
                                if event not in chain:
                                    chain.insert(-1, event)  # Insert before terminal
            # Include decision that selected empty results
            elif event.event_type == EventType.DECISION:
                if isinstance(event.input, dict):
                    total_results = event.input.get("total_results", -1)
                    if total_results == 0 and event.status == "success":
                        # This decision selected from 0 results - should have been a warning
                        if terminal.parent_id:
                            if self._is_ancestor(event.event_id, terminal.event_id) or event.parent_id == terminal.parent_id:
                                if event not in chain:
                                    # Insert after tool_call but before terminal
                                    tool_call_pos = next((i for i, e in enumerate(chain) if e.event_type == EventType.TOOL_CALL), -1)
                                    if tool_call_pos >= 0:
                                        chain.insert(tool_call_pos + 1, event)
                                    else:
                                        chain.insert(-1, event)
        
        return chain
    
    def _is_ancestor(self, ancestor_id: str, descendant_id: str) -> bool:
        """Check if ancestor_id is an ancestor of descendant_id."""
        current = self._event_map.get(descendant_id)
        visited = set()
        while current and current.parent_id and current.parent_id not in visited:
            visited.add(current.parent_id)
            if current.parent_id == ancestor_id:
                return True
            current = self._event_map.get(current.parent_id)
        return False
    
    def print_analysis(self):
        """Print human-readable failure analysis."""
        analysis = self.analyze_failure()
        
        if not analysis:
            print("=" * 80)
            print("ANALYSIS: No failures detected in this trace")
            print("=" * 80)
            return
        
        print("=" * 80)
        print("FAILURE ANALYSIS")
        print("=" * 80)
        print()
        
        # What failed
        terminal = analysis["terminal_failure"]
        if terminal:
            print("WHAT FAILED:")
            print(f"  The agent terminated with failure: {terminal.error}")
            print()
        
        # Root cause
        root_cause = analysis["root_cause"]
        if root_cause:
            print("WHY IT FAILED:")
            print(f"  {root_cause['description']}")
            root_event = root_cause["event"]
            if root_event.event_type == EventType.TOOL_CALL:
                if isinstance(root_event.input, dict):
                    query = root_event.input.get("query", "N/A")
                    print(f"  Tool call query: {query}")
                if isinstance(root_event.output, dict):
                    results_count = root_event.output.get("results_count", 0)
                    print(f"  Tool returned: {results_count} results")
            print()
        
        # Assumption violation
        print("ASSUMPTION VIOLATED:")
        if root_cause and root_cause["type"] == "empty_tool_output":
            print("  Agent assumed tool calls would return usable data")
            print("  Agent did not validate that results list was non-empty")
            print("  Agent proceeded to use empty results in downstream steps")
        elif root_cause and root_cause["type"] == "retry_exhaustion":
            print("  Agent assumed retries would eventually succeed")
            print("  Agent did not handle permanent failures gracefully")
        else:
            print("  Agent made an assumption that was not validated")
        print()
        
        # Early warning signal
        print("EARLY WARNING SIGNAL:")
        failure_chain = analysis["failure_chain"]
        if failure_chain:
            # Find the first problematic event in the entire trace
            for event in self.events:
                if event.event_type == EventType.TOOL_CALL:
                    if isinstance(event.output, dict):
                        results_count = event.output.get("results_count", 0)
                        if results_count == 0:
                            event_num = self.events.index(event) + 1
                            print(f"  Event #{event_num}: Tool call returned 0 results")
                            print(f"    Event type: {event.event_type.value}")
                            print(f"    Status: {event.status}")
                            if isinstance(event.input, dict):
                                query = event.input.get("query", "N/A")
                                print(f"    Query: {query}")
                            print(f"    This occurred at: {event.timestamp.isoformat()}")
                            print(f"    The agent should have detected this and handled it")
                            print(f"    Instead, the agent proceeded to use empty results")
                            break
        print()
        
        # Failure chain summary
        print("FAILURE CHAIN:")
        for i, event in enumerate(failure_chain, 1):
            event_type = event.event_type.value
            status = event.status or "N/A"
            print(f"  {i}. {event_type} ({status})")
            
            # Add context for key events
            if event.event_type == EventType.TOOL_CALL:
                if isinstance(event.output, dict):
                    results_count = event.output.get("results_count", 0)
                    print(f"     -> Tool returned {results_count} results")
            elif event.event_type == EventType.DECISION:
                if isinstance(event.input, dict):
                    total_results = event.input.get("total_results")
                    if total_results is not None:
                        print(f"     -> Agent selected from {total_results} results")
            
            if event.error:
                print(f"     Error: {event.error}")
        print()


def inspect_trace_from_storage(storage_path: str):
    """
    Load events from storage and print trace analysis.
    
    Args:
        storage_path: Path to JSON storage file
    """
    storage = JSONEventStorage(storage_path)
    events = storage.load()
    
    if not events:
        print(f"No events found in {storage_path}")
        return
    
    inspector = TraceInspector(events)
    inspector.print_trace()
    inspector.print_analysis()


def inspect_trace_from_events(events: List[Event]):
    """
    Analyze events and print trace analysis.
    
    Args:
        events: List of Event instances
    """
    inspector = TraceInspector(events)
    inspector.print_trace()
    inspector.print_analysis()
