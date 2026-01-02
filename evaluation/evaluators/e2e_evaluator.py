"""
End-to-End Task Evaluator.
Measures complete conversation scenarios with success criteria.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evaluation.metrics import compute_task_completion_rate


class EndToEndEvaluator:
    """
    Evaluates end-to-end task completion for multi-turn conversations.
    
    Measures:
    - Task success rate
    - Average turns to completion
    - Error recovery rate
    - Context retention across turns
    """
    
    def __init__(self, voice_assistant=None):
        """
        Initialize the E2E evaluator.
        
        Args:
            voice_assistant: The VoiceAssistant instance to evaluate
        """
        self.voice_assistant = voice_assistant
        self.results = []
    
    def set_voice_assistant(self, voice_assistant):
        """Set or update the voice assistant instance."""
        self.voice_assistant = voice_assistant
    
    def evaluate_scenario(
        self,
        scenario: Dict[str, Any],
        max_turns: int = 10
    ) -> Dict[str, Any]:
        """
        Evaluate a single conversation scenario.
        
        Args:
            scenario: Dictionary with 'turns', 'success_criteria', and metadata
            max_turns: Maximum turns before timeout
            
        Returns:
            Evaluation result with success status and metrics
        """
        if self.voice_assistant is None:
            raise ValueError("VoiceAssistant not set. Use set_voice_assistant() first.")
        
        # Reset conversation history
        self.voice_assistant.conversation_history = []
        
        scenario_name = scenario.get("name", "unnamed")
        task_type = scenario.get("task_type", "unknown")
        turns = scenario.get("turns", [])
        success_criteria = scenario.get("success_criteria", {})
        
        responses = []
        errors = []
        had_error = False
        error_recovered = False
        
        for i, turn in enumerate(turns):
            if i >= max_turns:
                break
            
            user_input = turn.get("user_input", "")
            expected_keywords = turn.get("expected_keywords", [])
            expect_error = turn.get("expect_error", False)
            
            try:
                # Process the turn
                response = self.voice_assistant.process(user_input)
                
                if response is False:  # Exit command
                    responses.append({
                        "turn": i + 1,
                        "input": user_input,
                        "response": "EXIT",
                        "keywords_found": [],
                        "error": None
                    })
                    break
                
                response_str = str(response) if response else ""
                response_lower = response_str.lower()
                
                # Check for expected keywords
                keywords_found = [
                    kw for kw in expected_keywords
                    if kw.lower() in response_lower
                ]
                
                # Check for error indicators
                error_indicators = ["error", "sorry", "apologize", "problem", "couldn't"]
                turn_had_error = any(ind in response_lower for ind in error_indicators)
                
                if turn_had_error and not expect_error:
                    had_error = True
                
                responses.append({
                    "turn": i + 1,
                    "input": user_input,
                    "response": response_str,
                    "keywords_found": keywords_found,
                    "expected_keywords": expected_keywords,
                    "keyword_match_rate": len(keywords_found) / len(expected_keywords) if expected_keywords else 1.0,
                    "had_error": turn_had_error,
                    "error": None
                })
                
            except Exception as e:
                had_error = True
                errors.append(str(e))
                responses.append({
                    "turn": i + 1,
                    "input": user_input,
                    "response": None,
                    "keywords_found": [],
                    "error": str(e)
                })
        
        # Evaluate success criteria
        success = self._evaluate_success_criteria(responses, success_criteria)
        
        # Check if error was recovered
        if had_error:
            # If we had an error but later turns succeeded, we recovered
            error_recovered = success and any(
                r.get("keyword_match_rate", 0) > 0.5 
                for r in responses[-2:]  # Check last 2 turns
            )
        
        result = {
            "scenario_name": scenario_name,
            "task_type": task_type,
            "success": success,
            "turns": len(responses),
            "had_error": had_error,
            "error_recovered": error_recovered,
            "responses": responses,
            "errors": errors,
            "success_criteria_met": self._get_criteria_details(responses, success_criteria)
        }
        
        self.results.append(result)
        return result
    
    def evaluate_batch(
        self,
        scenarios: List[Dict[str, Any]],
        max_turns: int = 10
    ) -> Dict[str, Any]:
        """
        Evaluate a batch of conversation scenarios.
        
        Args:
            scenarios: List of scenario dictionaries
            max_turns: Maximum turns per scenario
            
        Returns:
            Aggregated metrics across all scenarios
        """
        self.results = []  # Reset results
        
        for scenario in scenarios:
            # Reset assistant state between scenarios
            if self.voice_assistant:
                self.voice_assistant.conversation_history = []
            
            self.evaluate_scenario(scenario, max_turns)
        
        return self.compute_metrics()
    
    def _evaluate_success_criteria(
        self,
        responses: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if success criteria are met.
        
        Args:
            responses: List of turn responses
            criteria: Success criteria dictionary
            
        Returns:
            Boolean indicating overall success
        """
        if not criteria:
            # Default: at least 50% keyword match rate in final response
            if responses:
                final_response = responses[-1]
                return final_response.get("keyword_match_rate", 0) >= 0.5
            return False
        
        # Check required keywords in any response
        required_keywords = criteria.get("required_keywords", [])
        if required_keywords:
            all_found_keywords = set()
            for r in responses:
                all_found_keywords.update(r.get("keywords_found", []))
            
            keyword_match = all(
                any(kw.lower() in fk.lower() for fk in all_found_keywords)
                for kw in required_keywords
            )
            if not keyword_match:
                return False
        
        # Check required action completion
        required_action = criteria.get("required_action")
        if required_action:
            action_indicators = criteria.get("action_indicators", [])
            if action_indicators:
                action_found = any(
                    any(ind.lower() in str(r.get("response", "")).lower() for ind in action_indicators)
                    for r in responses
                )
                if not action_found:
                    return False
        
        # Check max turns constraint
        max_turns_allowed = criteria.get("max_turns")
        if max_turns_allowed and len(responses) > max_turns_allowed:
            return False
        
        # Check no errors
        no_errors_required = criteria.get("no_errors", False)
        if no_errors_required:
            if any(r.get("had_error") or r.get("error") for r in responses):
                return False
        
        return True
    
    def _get_criteria_details(
        self,
        responses: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Get detailed breakdown of which criteria passed/failed."""
        details = {}
        
        if not criteria:
            return {"default_keyword_check": True}
        
        # Required keywords
        required_keywords = criteria.get("required_keywords", [])
        if required_keywords:
            all_found = set()
            for r in responses:
                all_found.update(kw.lower() for kw in r.get("keywords_found", []))
            
            for kw in required_keywords:
                details[f"keyword_{kw}"] = any(kw.lower() in fk for fk in all_found)
        
        # Max turns
        max_turns = criteria.get("max_turns")
        if max_turns:
            details["within_max_turns"] = len(responses) <= max_turns
        
        # No errors
        if criteria.get("no_errors"):
            details["no_errors"] = not any(r.get("error") for r in responses)
        
        return details
    
    def compute_metrics(self) -> Dict[str, Any]:
        """
        Compute aggregated metrics from all evaluated scenarios.
        
        Returns:
            Dictionary with task completion metrics
        """
        if not self.results:
            return {"error": "No results to evaluate"}
        
        return compute_task_completion_rate(self.results)
    
    def evaluate_context_retention(
        self,
        context_scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Specifically test context retention across turns.
        
        Args:
            context_scenarios: Scenarios designed to test context
            
        Returns:
            Context retention metrics
        """
        if self.voice_assistant is None:
            raise ValueError("VoiceAssistant not set.")
        
        retention_results = []
        
        for scenario in context_scenarios:
            self.voice_assistant.conversation_history = []
            
            context_info = scenario.get("context_info", {})  # Info from earlier turns
            test_turns = scenario.get("test_turns", [])
            
            # First establish context
            setup_turns = scenario.get("setup_turns", [])
            for turn in setup_turns:
                try:
                    self.voice_assistant.process(turn.get("user_input", ""))
                except:
                    pass
            
            # Now test context retention
            for turn in test_turns:
                user_input = turn.get("user_input", "")
                context_reference = turn.get("context_reference", "")  # What context should be remembered
                
                try:
                    response = self.voice_assistant.process(user_input)
                    response_str = str(response) if response else ""
                    
                    # Check if context was retained
                    context_retained = context_reference.lower() in response_str.lower() if context_reference else True
                    
                    retention_results.append({
                        "scenario": scenario.get("name", "unnamed"),
                        "turn_input": user_input,
                        "context_reference": context_reference,
                        "context_retained": context_retained,
                        "response_preview": response_str[:200]
                    })
                    
                except Exception as e:
                    retention_results.append({
                        "scenario": scenario.get("name", "unnamed"),
                        "turn_input": user_input,
                        "context_reference": context_reference,
                        "context_retained": False,
                        "error": str(e)
                    })
        
        if not retention_results:
            return {"error": "No context retention tests completed"}
        
        retention_rate = sum(1 for r in retention_results if r.get("context_retained", False)) / len(retention_results)
        
        return {
            "context_retention_rate": retention_rate,
            "total_tests": len(retention_results),
            "results": retention_results
        }
    
    def get_failed_scenarios(self) -> List[Dict[str, Any]]:
        """Get scenarios that failed their success criteria."""
        return [r for r in self.results if not r.get("success", False)]
    
    def clear_results(self):
        """Clear accumulated results."""
        self.results = []
    
    def get_summary(self) -> str:
        """
        Get a human-readable summary of the evaluation.
        
        Returns:
            Formatted string summary
        """
        metrics = self.compute_metrics()
        
        if "error" in metrics:
            return f"Error: {metrics['error']}"
        
        lines = [
            "=" * 50,
            "END-TO-END TASK EVALUATION",
            "=" * 50,
            f"Total scenarios: {metrics['total_tasks']}",
            f"Successful: {metrics['successful_tasks']}",
            f"Success rate: {metrics['success_rate']:.2%}",
            f"Avg turns to completion: {metrics['avg_turns_to_completion']:.1f}",
        ]
        
        if metrics.get("error_recovery_rate") is not None:
            lines.append(f"Error recovery rate: {metrics['error_recovery_rate']:.2%}")
        
        # Per task type breakdown
        by_type = metrics.get("by_task_type", {})
        if by_type:
            lines.append("\nBy task type:")
            for task_type, type_metrics in by_type.items():
                lines.append(
                    f"  {task_type}: {type_metrics['success']}/{type_metrics['total']} "
                    f"({type_metrics['success_rate']:.0%})"
                )
        
        # Failed scenarios
        failed = self.get_failed_scenarios()
        if failed:
            lines.append(f"\nFailed scenarios ({len(failed)}):")
            for f in failed[:3]:
                lines.append(f"  - {f.get('scenario_name', 'unnamed')}")
        
        return "\n".join(lines)

