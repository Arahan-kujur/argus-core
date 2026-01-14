"""
Example AI Agent: Research Assistant

This agent demonstrates realistic AI agent behavior with:
- Multi-step reasoning
- LLM-style calls (mocked)
- Tool calls (search function)
- Decision-making
- Imperfect behavior for failure analysis

The agent is intentionally imperfect to demonstrate how Argus can surface
failure modes and suboptimal behavior patterns.
"""

import time
from typing import List, Dict, Optional
from argus import EventLogger, EventType, Tracer


# Mock LLM function - simulates an LLM API call
def mock_llm_call(prompt: str, temperature: float = 0.7, question_context: str = None) -> str:
    """
    Simulates an LLM API call with realistic delay and behavior.
    
    In a real system, this would be OpenAI, Anthropic, etc.
    """
    time.sleep(0.1)  # Simulate API latency
    
    # Simple mock responses based on prompt content
    prompt_lower = prompt.lower()
    question_lower = (question_context or "").lower()
    
    if "search query" in prompt_lower or "generate query" in prompt_lower:
        # Extract topic from prompt - check question context for obscure topics
        if "xyz123" in question_lower or "xyz123" in prompt_lower:
            # Generate queries that will return empty results (realistic: LLM generates queries for topics with no data)
            return "xyz123 obscure topic, unknown subject matter search, nonexistent information query"
        elif "python" in prompt_lower:
            return "python programming best practices, python tutorials, python documentation"
        elif "machine learning" in prompt_lower or "ml" in prompt_lower:
            return "machine learning algorithms, neural networks, deep learning"
        elif "argus" in prompt_lower:
            return "argus observability, AI agent monitoring, event logging"
        else:
            return "general research, information retrieval, knowledge base"
    
    elif "synthesize" in prompt_lower or "summarize" in prompt_lower:
        # Mock synthesis
        return "Based on the research findings, here is a comprehensive answer..."
    
    else:
        return "I need more context to provide a helpful response."


# Tool function: Search
def search_tool(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Simulates a search tool that could fail or return empty results.
    
    This represents an external API or service call that the agent depends on.
    """
    time.sleep(0.05)  # Simulate network latency
    
    # Simulate occasional failures
    if "fail" in query.lower():
        raise ConnectionError("Search service temporarily unavailable")
    
    # Simulate empty results for certain queries
    # Realistic scenario: search service returns empty for obscure/nonexistent topics
    if "empty" in query.lower() or query.strip() == "":
        return []
    if "xyz123" in query.lower() or "obscure" in query.lower() or "unknown" in query.lower() or "nonexistent" in query.lower():
        return []  # No results found for this topic
    
    # Mock search results
    results = []
    for i in range(min(max_results, 3)):  # Return up to 3 results
        results.append({
            "title": f"Result {i+1} for: {query}",
            "snippet": f"This is relevant information about {query}",
            "url": f"https://example.com/result-{i+1}",
        })
    
    return results


class ResearchAgent:
    """
    A research assistant agent that answers questions by:
    1. Generating search queries (LLM call)
    2. Searching for information (tool call)
    3. Deciding which results to use (decision)
    4. Synthesizing an answer (LLM call)
    5. Returning the final result
    
    This agent is intentionally imperfect:
    - Doesn't validate empty search results well
    - Has a retry mechanism that could loop
    - Doesn't handle all error cases gracefully
    """
    
    def __init__(self, logger: EventLogger, session_id: Optional[str] = None):
        """
        Initialize the research agent.
        
        Args:
            logger: Argus EventLogger for observability
            session_id: Optional session identifier for grouping events
        """
        self.logger = logger
        self.session_id = session_id or "research-session"
        self.max_retries = 3
        self.current_question: Optional[str] = None  # Track current question for failure scenarios
    
    def answer_question(self, question: str) -> Dict[str, any]:
        """
        Main agent entry point: answer a research question.
        
        This method orchestrates the multi-step reasoning process.
        """
        self.current_question = question  # Store for failure scenario detection
        
        parent_event = self.logger.log_event(
            event_type=EventType.DECISION,
            session_id=self.session_id,
            status="started",
            input={"question": question},
            metadata={"agent": "ResearchAgent", "step": "question_received"},
        )
        
        try:
            # Step 1: Generate search queries
            queries = self._generate_queries(question, parent_id=parent_event.event_id)
            
            # Step 2: Search for information (with retry logic)
            search_results = self._search_with_retry(queries, parent_id=parent_event.event_id)
            
            # INTERVENTION: Input validation - guard against empty tool outputs
            # Validate that search returned usable results before proceeding
            if not search_results or len(search_results) == 0:
                # Log validation failure event
                self.logger.log_event(
                    event_type=EventType.FAILURE,
                    session_id=self.session_id,
                    parent_id=parent_event.event_id,
                    status="failure",
                    input={"search_results_count": 0, "queries": queries},
                    error="Search returned no results - cannot proceed with empty data",
                    metadata={"intervention": "input_validation", "step": "search_validation"},
                )
                raise ValueError("Search returned no results. Cannot generate answer without information sources.")
            
            # Step 3: Decide which results to use
            selected_results = self._select_results(search_results, parent_id=parent_event.event_id)
            
            # Step 4: Synthesize final answer
            answer = self._synthesize_answer(question, selected_results, parent_id=parent_event.event_id)
            
            # Step 5: Terminate successfully
            self.logger.log_event(
                event_type=EventType.TERMINATION,
                session_id=self.session_id,
                parent_id=parent_event.event_id,
                status="success",
                output={"answer": answer, "sources_used": len(selected_results)},
                metadata={"agent": "ResearchAgent"},
            )
            
            return {
                "answer": answer,
                "sources_used": len(selected_results),
                "status": "success",
            }
            
        except Exception as e:
            # Record failure
            self.logger.log_event(
                event_type=EventType.TERMINATION,
                session_id=self.session_id,
                parent_id=parent_event.event_id,
                status="failure",
                error=str(e),
                metadata={"agent": "ResearchAgent"},
            )
            raise
    
    def _generate_queries(self, question: str, parent_id: str) -> List[str]:
        """
        Step 1: Use LLM to generate search queries from the question.
        
        This simulates the agent's reasoning about how to search for information.
        """
        prompt = f"Generate 2-3 search queries to research: {question}"
        
        with Tracer(
            logger=self.logger,
            event_type=EventType.LLM_CALL,
            session_id=self.session_id,
            parent_id=parent_id,
            input_summary={"prompt": prompt, "question": question},
            metadata={"step": "query_generation", "model": "mock-llm"},
        ) as tracer:
            response = mock_llm_call(prompt, question_context=question)
            queries = [q.strip() for q in response.split(",")]
            tracer.set_output({"queries": queries, "raw_response": response})
        
        return queries
    
    def _search_with_retry(self, queries: List[str], parent_id: str) -> List[Dict[str, str]]:
        """
        Step 2: Search for information with retry logic.
        
        This demonstrates how retries can be traced and analyzed.
        The retry mechanism is intentionally simple and could fail.
        """
        all_results = []
        attempt = 0
        
        for query in queries:
            attempt += 1
            retry_count = 0
            
            while retry_count < self.max_retries:
                try:
                    with Tracer(
                        logger=self.logger,
                        event_type=EventType.TOOL_CALL,
                        session_id=self.session_id,
                        parent_id=parent_id,
                        input_summary={"query": query, "attempt": attempt},
                        metadata={"tool": "search", "retry_count": retry_count},
                    ) as tracer:
                        results = search_tool(query)
                        # REALISTIC FAILURE SCENARIO: If original question is about obscure topic,
                        # search returns empty (no data available) - this simulates real-world
                        # scenarios where search APIs return empty for topics with no information
                        if self.current_question and "xyz123" in self.current_question.lower():
                            results = []  # Force empty results for obscure topics
                        tracer.set_output({"results_count": len(results), "results": results})
                    
                    all_results.extend(results)
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    retry_count += 1
                    
                    # Log retry event
                    self.logger.log_event(
                        event_type=EventType.RETRY,
                        session_id=self.session_id,
                        parent_id=parent_id,
                        status="retrying",
                        input={"query": query, "retry_count": retry_count},
                        error=str(e),
                        metadata={"tool": "search", "max_retries": self.max_retries},
                    )
                    
                    if retry_count >= self.max_retries:
                        # Final failure after retries exhausted
                        self.logger.log_event(
                            event_type=EventType.FAILURE,
                            session_id=self.session_id,
                            parent_id=parent_id,
                            status="failure",
                            input={"query": query},
                            error=f"Search failed after {self.max_retries} retries: {str(e)}",
                            metadata={"tool": "search"},
                        )
                        raise  # Re-raise to preserve behavior
        
        return all_results
    
    def _select_results(self, results: List[Dict[str, str]], parent_id: str) -> List[Dict[str, str]]:
        """
        Step 3: Decide which search results to use.
        
        This demonstrates decision-making that could be suboptimal.
        The agent doesn't handle empty results well (intentional brittleness).
        """
        with Tracer(
            logger=self.logger,
            event_type=EventType.DECISION,
            session_id=self.session_id,
            parent_id=parent_id,
            input_summary={"total_results": len(results)},
            metadata={"step": "result_selection"},
        ) as tracer:
            # Simple selection: use all results (suboptimal - should filter)
            # Brittleness: doesn't check if results is empty
            selected = results[:5]  # Take first 5 results
            
            # This could fail if results is None or not a list
            # (intentional brittleness for failure analysis)
            tracer.set_output({"selected_count": len(selected), "selection_strategy": "first_n"})
        
        return selected
    
    def _synthesize_answer(self, question: str, results: List[Dict[str, str]], parent_id: str) -> str:
        """
        Step 4: Use LLM to synthesize final answer from search results.
        
        This simulates the agent's final reasoning step.
        
        FAILURE MODE: This method assumes results is non-empty. When results is empty,
        it will try to access results[0] to get a "primary source" for the answer,
        causing an IndexError. This is a realistic bug - agents often assume successful
        tool calls produce usable data without validation.
        """
        # Build context from results
        context = "\n".join([f"- {r['snippet']}" for r in results])
        
        # REALISTIC FAILURE: Agent assumes at least one result exists to cite as primary source
        # This is a common pattern in real agents that don't validate tool outputs
        if len(results) == 0:
            # Agent tries to get primary source without checking if results exist
            # This will cause IndexError when trying to access results[0]
            primary_source = results[0]['title']  # FAILS HERE: IndexError on empty list
            context = f"Primary source: {primary_source}\n{context}"
        
        prompt = f"Question: {question}\n\nContext from research:\n{context}\n\nSynthesize a comprehensive answer."
        
        with Tracer(
            logger=self.logger,
            event_type=EventType.LLM_CALL,
            session_id=self.session_id,
            parent_id=parent_id,
            input_summary={"prompt_length": len(prompt), "results_count": len(results)},
            metadata={"step": "answer_synthesis", "model": "mock-llm"},
        ) as tracer:
            answer = mock_llm_call(prompt)
            tracer.set_output({"answer_length": len(answer), "answer_preview": answer[:100]})
        
        return answer


def run_example():
    """Run example agent with Argus instrumentation."""
    logger = EventLogger()
    agent = ResearchAgent(logger, session_id="example-run-1")
    
    print("=== Research Agent Example ===\n")
    print("Question: What are best practices for Python programming?\n")
    
    try:
        result = agent.answer_question("What are best practices for Python programming?")
        print(f"Answer: {result['answer']}")
        print(f"\nStatus: {result['status']}")
        print(f"Sources used: {result['sources_used']}")
    except Exception as e:
        print(f"Agent failed: {e}")
    
    print("\n=== Argus Events Recorded ===\n")
    events = logger.get_events()
    for i, event in enumerate(events, 1):
        duration = event.metadata.get("duration_seconds", 0)
        print(f"{i}. {event.event_type.value:12} | {event.status:8} | "
              f"duration: {duration:.3f}s | step: {event.metadata.get('step', 'N/A')}")
        if event.error:
            print(f"   Error: {event.error}")
    
    print(f"\nTotal events: {len(events)}")


if __name__ == "__main__":
    run_example()
