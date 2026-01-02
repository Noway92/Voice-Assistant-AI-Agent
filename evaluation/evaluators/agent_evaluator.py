"""
Agent-Level Evaluator.
Measures performance of individual specialized agents.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import re

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class AgentEvaluator:
    """
    Evaluates individual agent performance.

    Supports evaluation of:
    - Reservation Agent: Tool call accuracy, parameter extraction
    - General Agent: FAQ matching, factual correctness, menu information (merged with menu queries)
    - Order Agent: Order parsing, confirmation handling
    """

    def __init__(self):
        """Initialize the agent evaluator."""
        self.results = {
            "reservation": [],
            "general": [],
            "order": []
        }
    
    def evaluate_reservation_agent(
        self,
        agent,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate the reservation agent.
        
        Args:
            agent: TableReservationAgent instance
            test_cases: List of test scenarios with expected outcomes
            
        Returns:
            Evaluation metrics for reservation agent
        """
        results = []
        
        for case in test_cases:
            input_text = case.get("input", "")
            expected_action = case.get("expected_action")  # e.g., "make_reservation", "check_availability"
            expected_params = case.get("expected_params", {})
            expected_success = case.get("expected_success", True)
            
            try:
                response = agent.process(input_text)
                
                # Analyze response for success indicators
                success_indicators = [
                    "confirmed", "reservation", "booked", "available",
                    "cancelled", "table"
                ]
                failure_indicators = [
                    "sorry", "error", "no tables", "unavailable", 
                    "missing", "provide"
                ]
                
                response_lower = response.lower() if isinstance(response, str) else ""
                
                has_success = any(ind in response_lower for ind in success_indicators)
                has_failure = any(ind in response_lower for ind in failure_indicators)
                
                # Determine if task succeeded
                if expected_success:
                    task_success = has_success and not has_failure
                else:
                    task_success = has_failure
                
                # Check parameter extraction
                params_extracted = self._extract_reservation_params(response_lower)
                params_match = self._compare_params(expected_params, params_extracted)
                
                result = {
                    "input": input_text,
                    "response": response,
                    "expected_action": expected_action,
                    "task_success": task_success,
                    "params_extracted": params_extracted,
                    "params_match": params_match,
                    "error": None
                }
                
            except Exception as e:
                result = {
                    "input": input_text,
                    "response": None,
                    "expected_action": expected_action,
                    "task_success": False,
                    "params_extracted": {},
                    "params_match": False,
                    "error": str(e)
                }
            
            results.append(result)
        
        self.results["reservation"] = results
        return self._compute_agent_metrics(results, "reservation")
    
    def evaluate_menu_agent(
        self,
        agent,
        test_cases: List[Dict[str, Any]],
        ground_truth: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate menu information queries.

        DEPRECATED: Menu queries are now handled by GeneralInqueriesAgent.
        This method now delegates to evaluate_general_agent for backward compatibility.

        Args:
            agent: GeneralInqueriesAgent instance
            test_cases: List of test queries with expected information
            ground_truth: Optional menu data for accuracy checking (unused)

        Returns:
            Evaluation metrics for menu queries (handled by general agent)
        """
        # Menu agent merged with general agent - delegate to general evaluation
        print("  [Note: Menu queries now evaluated as part of GeneralInqueriesAgent]")
        return self.evaluate_general_agent(agent, test_cases)
    
    def evaluate_general_agent(
        self,
        agent,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate the general inquiries agent.
        
        Args:
            agent: GeneralInqueriesAgent instance
            test_cases: List of test queries with expected answers
            
        Returns:
            Evaluation metrics for general agent
        """
        results = []
        
        for case in test_cases:
            input_text = case.get("input", "")
            expected_keywords = case.get("expected_keywords", [])
            expected_topic = case.get("expected_topic", "")
            
            try:
                response = agent.process(input_text)
                response_str = str(response) if response else ""
                response_lower = response_str.lower()
                
                # Check keyword presence
                keywords_found = [
                    kw for kw in expected_keywords 
                    if kw.lower() in response_lower
                ]
                keyword_coverage = len(keywords_found) / len(expected_keywords) if expected_keywords else 1.0
                
                result = {
                    "input": input_text,
                    "response": response_str,
                    "expected_topic": expected_topic,
                    "keywords_found": keywords_found,
                    "keyword_coverage": keyword_coverage,
                    "success": keyword_coverage >= 0.5,
                    "error": None
                }
                
            except Exception as e:
                result = {
                    "input": input_text,
                    "response": None,
                    "expected_topic": expected_topic,
                    "keywords_found": [],
                    "keyword_coverage": 0.0,
                    "success": False,
                    "error": str(e)
                }
            
            results.append(result)
        
        self.results["general"] = results
        return self._compute_agent_metrics(results, "general")
    
    def evaluate_order_agent(
        self,
        agent,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate the order handling agent.
        
        Args:
            agent: OrderHandlingAgent instance
            test_cases: List of order scenarios
            
        Returns:
            Evaluation metrics for order agent
        """
        results = []
        
        for case in test_cases:
            input_text = case.get("input", "")
            expected_items = case.get("expected_items", [])
            expected_action = case.get("expected_action", "place_order")
            
            try:
                response = agent.process(input_text)
                response_str = str(response) if response else ""
                response_lower = response_str.lower()
                
                # Check if expected items are mentioned
                items_found = [
                    item for item in expected_items
                    if item.lower() in response_lower
                ]
                
                result = {
                    "input": input_text,
                    "response": response_str,
                    "expected_action": expected_action,
                    "expected_items": expected_items,
                    "items_found": items_found,
                    "success": len(items_found) >= len(expected_items) * 0.5 if expected_items else True,
                    "error": None
                }
                
            except Exception as e:
                result = {
                    "input": input_text,
                    "response": None,
                    "expected_action": expected_action,
                    "expected_items": expected_items,
                    "items_found": [],
                    "success": False,
                    "error": str(e)
                }
            
            results.append(result)
        
        self.results["order"] = results
        return self._compute_agent_metrics(results, "order")
    
    def _extract_reservation_params(self, response: str) -> Dict[str, Any]:
        """Extract reservation parameters from response text."""
        params = {}
        
        # Date pattern: YYYY-MM-DD
        date_match = re.search(r'\d{4}-\d{2}-\d{2}', response)
        if date_match:
            params["date"] = date_match.group()
        
        # Time pattern: HH:MM
        time_match = re.search(r'\d{1,2}:\d{2}', response)
        if time_match:
            params["time"] = time_match.group()
        
        # Guests: number + guests/people/persons
        guests_match = re.search(r'(\d+)\s*(?:guests?|people|persons?)', response)
        if guests_match:
            params["guests"] = int(guests_match.group(1))
        
        # Table number
        table_match = re.search(r'table\s*(?:#|number)?\s*(\d+)', response)
        if table_match:
            params["table"] = int(table_match.group(1))
        
        return params
    
    def _compare_params(
        self, 
        expected: Dict[str, Any], 
        actual: Dict[str, Any]
    ) -> bool:
        """Compare expected and actual parameters."""
        if not expected:
            return True
        
        matches = 0
        for key, expected_value in expected.items():
            if key in actual:
                if str(actual[key]).lower() == str(expected_value).lower():
                    matches += 1
        
        return matches >= len(expected) * 0.7  # 70% match threshold
    
    def _compute_agent_metrics(
        self, 
        results: List[Dict[str, Any]], 
        agent_type: str
    ) -> Dict[str, Any]:
        """Compute metrics for an agent's results."""
        if not results:
            return {"error": "No results"}
        
        total = len(results)
        
        if agent_type == "reservation":
            successes = sum(1 for r in results if r.get("task_success", False))
            param_matches = sum(1 for r in results if r.get("params_match", False))
            errors = sum(1 for r in results if r.get("error"))
            
            return {
                "agent_type": agent_type,
                "total_tests": total,
                "task_success_rate": successes / total,
                "param_extraction_rate": param_matches / total,
                "error_rate": errors / total,
                "results": results
            }
        
        elif agent_type == "general":
            successes = sum(1 for r in results if r.get("success", False))
            avg_coverage = sum(r.get("keyword_coverage", 0) for r in results) / total
            errors = sum(1 for r in results if r.get("error"))
            
            return {
                "agent_type": agent_type,
                "total_tests": total,
                "success_rate": successes / total,
                "avg_keyword_coverage": avg_coverage,
                "error_rate": errors / total,
                "results": results
            }
        
        elif agent_type == "order":
            successes = sum(1 for r in results if r.get("success", False))
            errors = sum(1 for r in results if r.get("error"))
            
            return {
                "agent_type": agent_type,
                "total_tests": total,
                "success_rate": successes / total,
                "error_rate": errors / total,
                "results": results
            }
        
        return {"error": f"Unknown agent type: {agent_type}"}
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all evaluated agents."""
        return {
            agent_type: self._compute_agent_metrics(results, agent_type)
            for agent_type, results in self.results.items()
            if results
        }
    
    def clear_results(self):
        """Clear all accumulated results."""
        self.results = {
            "reservation": [],
            "general": [],
            "order": []
        }

