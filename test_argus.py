"""
Comprehensive test script for Argus.

This script verifies that all core functionality works correctly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work."""
    print("=" * 80)
    print("TEST 1: Imports")
    print("=" * 80)
    
    try:
        from argus import (
            Event, EventType, EventLogger, 
            EventStorage, JSONEventStorage,
            Tracer, trace_function,
            TraceInspector, inspect_trace_from_storage, inspect_trace_from_events
        )
        print("[OK] All imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False


def test_event_creation():
    """Test event creation."""
    print("\n" + "=" * 80)
    print("TEST 2: Event Creation")
    print("=" * 80)
    
    try:
        from argus import Event, EventType
        from datetime import datetime, timezone
        
        event = Event(
            event_id="test-1",
            event_type=EventType.LLM_CALL,
            timestamp=datetime.now(timezone.utc),
            status="success",
            input={"prompt": "test"},
            output={"response": "test response"}
        )
        
        assert event.event_id == "test-1"
        assert event.event_type == EventType.LLM_CALL
        assert event.status == "success"
        print("[OK] Event creation works")
        print(f"  Event ID: {event.event_id}")
        print(f"  Event Type: {event.event_type.value}")
        print(f"  Status: {event.status}")
        return True
    except Exception as e:
        print(f"✗ Event creation failed: {e}")
        return False


def test_logger():
    """Test EventLogger."""
    print("\n" + "=" * 80)
    print("TEST 3: EventLogger")
    print("=" * 80)
    
    try:
        from argus import EventLogger, EventType
        
        logger = EventLogger()
        
        # Log some events
        event1 = logger.log_event(
            event_type=EventType.LLM_CALL,
            status="success",
            input={"test": "data"}
        )
        
        event2 = logger.log_event(
            event_type=EventType.TOOL_CALL,
            status="success",
            parent_id=event1.event_id
        )
        
        events = logger.get_events()
        assert len(events) == 2
        assert events[0].event_id == event1.event_id
        assert events[1].parent_id == event1.event_id
        
        print("[OK] EventLogger works")
        print(f"  Logged {len(events)} events")
        print(f"  Event 1 ID: {event1.event_id}")
        print(f"  Event 2 parent: {event2.parent_id}")
        
        logger.clear()
        assert len(logger.get_events()) == 0
        print("[OK] Clear works")
        
        return True
    except Exception as e:
        print(f"[FAIL] EventLogger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_storage():
    """Test storage functionality."""
    print("\n" + "=" * 80)
    print("TEST 4: Storage")
    print("=" * 80)
    
    try:
        from argus import EventLogger, EventType, JSONEventStorage
        from datetime import datetime, timezone
        import tempfile
        import os
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            # Create and save events
            logger = EventLogger()
            event = logger.log_event(
                event_type=EventType.DECISION,
                status="success",
                input={"test": "data"}
            )
            
            storage = JSONEventStorage(temp_path)
            storage.save(logger.get_events())
            
            # Load events
            loaded_events = storage.load()
            assert len(loaded_events) == 1
            assert loaded_events[0].event_id == event.event_id
            assert loaded_events[0].event_type == EventType.DECISION
            
            print("[OK] Storage save/load works")
            print(f"  Saved {len(logger.get_events())} events")
            print(f"  Loaded {len(loaded_events)} events")
            print(f"  Event ID matches: {loaded_events[0].event_id == event.event_id}")
            
            # Test clear
            storage.clear()
            assert len(storage.load()) == 0
            print("[OK] Storage clear works")
            
            return True
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    except Exception as e:
        print(f"[FAIL] Storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tracer():
    """Test Tracer functionality."""
    print("\n" + "=" * 80)
    print("TEST 5: Tracer")
    print("=" * 80)
    
    try:
        from argus import EventLogger, EventType, Tracer
        import time
        
        logger = EventLogger()
        
        # Test context manager
        with Tracer(
            logger=logger,
            event_type=EventType.TOOL_CALL,
            input_summary={"x": 1, "y": 2},
            metadata={"tool": "test"}
        ):
            time.sleep(0.01)  # Small delay
            result = 1 + 2
            # Set output
            pass  # Output will be None in this case
        
        events = logger.get_events()
        assert len(events) >= 2  # At least started and success events
        
        tool_call_events = [e for e in events if e.event_type == EventType.TOOL_CALL]
        assert len(tool_call_events) >= 1
        
        success_event = next((e for e in tool_call_events if e.status == "success"), None)
        assert success_event is not None
        assert "duration_seconds" in success_event.metadata
        
        print("[OK] Tracer context manager works")
        print(f"  Created {len(events)} events")
        print(f"  Duration recorded: {success_event.metadata.get('duration_seconds', 0):.3f}s")
        
        # Test with exception
        logger2 = EventLogger()
        try:
            with Tracer(logger2, EventType.TOOL_CALL):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        failure_events = [e for e in logger2.get_events() if e.status == "failure"]
        assert len(failure_events) >= 1
        print("[OK] Tracer handles exceptions correctly")
        
        return True
    except Exception as e:
        print(f"[FAIL] Tracer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_inspector():
    """Test TraceInspector."""
    print("\n" + "=" * 80)
    print("TEST 6: TraceInspector")
    print("=" * 80)
    
    try:
        from argus import EventLogger, EventType, TraceInspector
        
        logger = EventLogger()
        
        # Create a simple trace
        parent = logger.log_event(
            event_type=EventType.DECISION,
            status="started",
            input={"question": "test"}
        )
        
        child = logger.log_event(
            event_type=EventType.TOOL_CALL,
            status="success",
            parent_id=parent.event_id,
            output={"results_count": 0}
        )
        
        failure = logger.log_event(
            event_type=EventType.TERMINATION,
            status="failure",
            parent_id=parent.event_id,
            error="Test error"
        )
        
        inspector = TraceInspector(logger.get_events())
        analysis = inspector.analyze_failure()
        
        assert analysis is not None
        assert analysis["has_failure"] is True
        assert analysis["terminal_failure"] is not None
        
        print("[OK] TraceInspector works")
        print(f"  Analyzed {len(logger.get_events())} events")
        print(f"  Found failure: {analysis['has_failure']}")
        print(f"  Terminal failure: {analysis['terminal_failure'].error}")
        
        return True
    except Exception as e:
        print(f"[FAIL] TraceInspector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_research_agent():
    """Test ResearchAgent example."""
    print("\n" + "=" * 80)
    print("TEST 7: ResearchAgent Example")
    print("=" * 80)
    
    try:
        from argus import EventLogger
        from examples.research_agent import ResearchAgent
        
        logger = EventLogger()
        agent = ResearchAgent(logger, session_id="test-session")
        
        # Test with a question that should work
        try:
            result = agent.answer_question("What is Python?")
            events = logger.get_events()
            assert len(events) > 0
            
            print("[OK] ResearchAgent works")
            print(f"  Created {len(events)} events")
            print(f"  Status: {result.get('status', 'N/A')}")
            
            return True
        except Exception as e:
            # Even if it fails, check that events were created
            events = logger.get_events()
            if len(events) > 0:
                print("[OK] ResearchAgent creates events (even on failure)")
                print(f"  Created {len(events)} events")
                print(f"  Error: {e}")
                return True
            else:
                print(f"[FAIL] ResearchAgent failed and created no events: {e}")
                return False
    except Exception as e:
        print(f"[FAIL] ResearchAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test full integration: logger -> storage -> inspector."""
    print("\n" + "=" * 80)
    print("TEST 8: Full Integration")
    print("=" * 80)
    
    try:
        from argus import EventLogger, EventType, JSONEventStorage, TraceInspector
        import tempfile
        import os
        
        # Create events
        logger = EventLogger()
        logger.log_event(
            event_type=EventType.DECISION,
            status="success",
            input={"test": "integration"}
        )
        
        # Save to storage
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            storage = JSONEventStorage(temp_path)
            storage.save(logger.get_events())
            
            # Load from storage
            loaded_events = storage.load()
            
            # Inspect
            inspector = TraceInspector(loaded_events)
            inspector.print_trace()
            
            print("[OK] Full integration works")
            print("  Logger -> Storage -> Inspector pipeline successful")
            
            return True
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    except Exception as e:
        print(f"[FAIL] Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("ARGUS COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Imports", test_imports),
        ("Event Creation", test_event_creation),
        ("EventLogger", test_logger),
        ("Storage", test_storage),
        ("Tracer", test_tracer),
        ("TraceInspector", test_inspector),
        ("ResearchAgent", test_research_agent),
        ("Integration", test_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[FAIL] {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
