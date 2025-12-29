"""
Evaluation Runner.
Orchestrates all evaluators and produces unified evaluation reports.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from evaluation.evaluators.intent_evaluator import IntentEvaluator
from evaluation.evaluators.agent_evaluator import AgentEvaluator
from evaluation.evaluators.rag_evaluator import RAGEvaluator
from evaluation.evaluators.e2e_evaluator import EndToEndEvaluator
from evaluation.evaluators.quality_evaluator import QualityEvaluator


class EvaluationRunner:
    """
    Main orchestrator for running comprehensive evaluations.
    
    Coordinates:
    - Intent classification evaluation
    - Agent-level evaluation
    - RAG retrieval evaluation
    - End-to-end task evaluation
    - Response quality evaluation
    """
    
    def __init__(
        self,
        orchestrator=None,
        voice_assistant=None,
        embeddings_manager=None,
        is_offline: bool = True
    ):
        """
        Initialize the evaluation runner.
        
        Args:
            orchestrator: Orchestrator instance
            voice_assistant: VoiceAssistant instance (for E2E tests)
            embeddings_manager: EmbeddingsManager instance (for RAG tests)
            is_offline: Whether to use offline LLMs for evaluation
        """
        self.orchestrator = orchestrator
        self.voice_assistant = voice_assistant
        self.embeddings_manager = embeddings_manager
        self.is_offline = is_offline
        
        # Initialize evaluators
        self.intent_evaluator = IntentEvaluator(orchestrator)
        self.agent_evaluator = AgentEvaluator()
        self.rag_evaluator = RAGEvaluator(embeddings_manager)
        self.e2e_evaluator = EndToEndEvaluator(voice_assistant)
        self.quality_evaluator = QualityEvaluator(use_offline=is_offline)
        
        # Results storage
        self.results = {}
    
    def _load_test_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """Load a test dataset from JSON file."""
        dataset_file = Path(__file__).parent / "datasets" / dataset_path
        if not dataset_file.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_file}")
        
        with open(dataset_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def evaluate_intent_classification(self) -> Dict[str, Any]:
        """
        Evaluate intent classification performance.
        
        Returns:
            Intent classification metrics
        """
        if self.orchestrator is None:
            return {"error": "Orchestrator not set"}
        
        print("Evaluating intent classification...")
        dataset = self._load_test_dataset("intent_test_data.json")
        test_cases = dataset.get("test_cases", [])
        
        metrics = self.intent_evaluator.evaluate_batch(test_cases)
        self.results["intent_classification"] = metrics
        
        return metrics
    
    def evaluate_agents(
        self,
        agents: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate individual agent performance.
        
        Args:
            agents: Dictionary mapping agent names to instances
                   If None, tries to extract from orchestrator
        
        Returns:
            Agent evaluation metrics
        """
        if self.orchestrator is None:
            return {"error": "Orchestrator not set"}
        
        print("Evaluating agents...")
        agent_results = {}
        
        # Get agents from orchestrator if not provided
        if agents is None:
            agents = {
                "reservation": getattr(self.orchestrator, "reservation_agent", None),
                "general": getattr(self.orchestrator, "general_agent", None),
                "order": getattr(self.orchestrator, "order_agent", None)
            }
        
        # Evaluate reservation agent
        if agents.get("reservation"):
            print("  - Reservation agent...")
            reservation_dataset = self._load_test_dataset("reservation_scenarios.json")
            reservation_results = self.agent_evaluator.evaluate_reservation_agent(
                agents["reservation"],
                reservation_dataset.get("scenarios", [])[:5]  # Limit for speed
            )
            agent_results["reservation"] = reservation_results
        
        # Evaluate general agent (handles both general inquiries and menu queries)
        if agents.get("general"):
            print("  - General agent (general + menu queries)...")
            # Load both general and menu test cases
            general_dataset = self._load_test_dataset("general_queries.json")
            menu_dataset = self._load_test_dataset("menu_queries.json")

            # Merge test cases from both datasets
            combined_test_cases = (
                general_dataset.get("test_cases", [])[:10] +
                menu_dataset.get("test_cases", [])[:10]
            )

            general_results = self.agent_evaluator.evaluate_general_agent(
                agents["general"],
                combined_test_cases
            )
            agent_results["general"] = general_results
        
        # Evaluate order agent
        if agents.get("order"):
            print("  - Order agent...")
            # Use simple test cases for order agent
            order_test_cases = [
                {"input": "I'd like to order a pizza", "expected_items": ["pizza"], "expected_action": "place_order"},
                {"input": "Add a burger to my order", "expected_items": ["burger"], "expected_action": "modify_order"}
            ]
            order_results = self.agent_evaluator.evaluate_order_agent(
                agents["order"],
                order_test_cases
            )
            agent_results["order"] = order_results
        
        self.results["agents"] = agent_results
        return agent_results
    
    def evaluate_rag_retrieval(self, use_ragas: bool = True) -> Dict[str, Any]:
        """
        Evaluate RAG retrieval performance.
        
        Args:
            use_ragas: Whether to use Ragas for comprehensive evaluation
        
        Returns:
            RAG evaluation metrics (including Ragas metrics if enabled)
        """
        if self.embeddings_manager is None:
            return {"error": "EmbeddingsManager not set"}
        
        print("Evaluating RAG retrieval...")
        
        # Load RAG test cases from both menu and general queries
        # (both are handled by the same GeneralInqueriesAgent)
        menu_dataset = self._load_test_dataset("menu_queries.json")
        rag_test_cases = menu_dataset.get("rag_test_cases", [])

        general_dataset = self._load_test_dataset("general_queries.json")
        general_rag_cases = general_dataset.get("rag_test_cases", [])

        all_rag_cases = rag_test_cases + general_rag_cases
        
        # Standard retrieval metrics
        metrics = self.rag_evaluator.evaluate_batch(all_rag_cases, k_values=[3, 5])
        
        # Add Ragas evaluation if requested and agent is available
        if use_ragas:
            print("  - Running Ragas evaluation...")
            # Try to get general agent for generating responses
            if self.orchestrator:
                general_agent = getattr(self.orchestrator, "general_agent", None)
                if general_agent:
                    self.rag_evaluator.set_agent(general_agent)
            
            ragas_metrics = self.rag_evaluator.evaluate_with_ragas(
                all_rag_cases,
                k=5,
                use_ground_truth=False  # Ground truth not available in current test cases
            )
            metrics["ragas"] = ragas_metrics
        
        self.results["rag"] = metrics
        
        return metrics
    
    def evaluate_end_to_end(self) -> Dict[str, Any]:
        """
        Evaluate end-to-end task completion.
        
        Returns:
            E2E evaluation metrics
        """
        if self.voice_assistant is None:
            return {"error": "VoiceAssistant not set"}
        
        print("Evaluating end-to-end tasks...")
        dataset = self._load_test_dataset("reservation_scenarios.json")
        scenarios = dataset.get("scenarios", [])[:10]  # Limit for speed
        
        metrics = self.e2e_evaluator.evaluate_batch(scenarios)
        self.results["end_to_end"] = metrics
        
        return metrics
    
    def evaluate_response_quality(
        self,
        sample_responses: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate response quality using LLM-as-judge.
        
        Args:
            sample_responses: Optional list of query-response pairs to evaluate
                             If None, generates from agent responses
        
        Returns:
            Quality evaluation metrics
        """
        print("Evaluating response quality...")
        
        if sample_responses is None:
            # Generate sample responses from previous evaluations
            sample_responses = []
            
            # Extract from agent results
            if "agents" in self.results:
                for agent_type, agent_result in self.results["agents"].items():
                    if "results" in agent_result:
                        for r in agent_result["results"][:3]:  # Sample 3 per agent
                            if r.get("input") and r.get("response"):
                                sample_responses.append({
                                    "query": r["input"],
                                    "response": r["response"]
                                })
        
        if not sample_responses:
            return {"error": "No sample responses provided"}
        
        metrics = self.quality_evaluator.evaluate_batch(sample_responses)
        self.results["quality"] = metrics
        
        return metrics
    
    def run_full_evaluation(
        self,
        include_agents: bool = True,
        include_rag: bool = True,
        include_e2e: bool = True,
        include_quality: bool = True
    ) -> Dict[str, Any]:
        """
        Run a complete evaluation suite.
        
        Args:
            include_agents: Whether to evaluate individual agents
            include_rag: Whether to evaluate RAG retrieval
            include_e2e: Whether to evaluate end-to-end tasks
            include_quality: Whether to evaluate response quality
        
        Returns:
            Complete evaluation results
        """
        print("=" * 70)
        print("STARTING FULL EVALUATION")
        print("=" * 70)
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "is_offline": self.is_offline,
                "evaluations_run": []
            }
        }
        
        # Intent classification (always run)
        try:
            intent_metrics = self.evaluate_intent_classification()
            self.results["configuration"]["evaluations_run"].append("intent")
        except Exception as e:
            intent_metrics = {"error": str(e)}
        self.results["intent_classification"] = intent_metrics
        
        # Agent evaluation
        if include_agents:
            try:
                agent_metrics = self.evaluate_agents()
                self.results["configuration"]["evaluations_run"].append("agents")
            except Exception as e:
                agent_metrics = {"error": str(e)}
            self.results["agents"] = agent_metrics
        
        # RAG evaluation
        if include_rag:
            try:
                rag_metrics = self.evaluate_rag_retrieval(use_ragas=True)
                self.results["configuration"]["evaluations_run"].append("rag")
            except Exception as e:
                rag_metrics = {"error": str(e)}
            self.results["rag"] = rag_metrics
        
        # E2E evaluation
        if include_e2e:
            try:
                e2e_metrics = self.evaluate_end_to_end()
                self.results["configuration"]["evaluations_run"].append("e2e")
            except Exception as e:
                e2e_metrics = {"error": str(e)}
            self.results["end_to_end"] = e2e_metrics
        
        # Quality evaluation
        if include_quality:
            try:
                quality_metrics = self.evaluate_response_quality()
                self.results["configuration"]["evaluations_run"].append("quality")
            except Exception as e:
                quality_metrics = {"error": str(e)}
            self.results["quality"] = quality_metrics
        
        print("\n" + "=" * 70)
        print("EVALUATION COMPLETE")
        print("=" * 70)
        
        return self.results
    
    def get_results(self) -> Dict[str, Any]:
        """Get accumulated evaluation results."""
        return self.results
    
    def clear_results(self):
        """Clear all evaluation results."""
        self.results = {}
        self.intent_evaluator.clear_results()
        self.agent_evaluator.clear_results()
        self.rag_evaluator.clear_results()
        self.e2e_evaluator.clear_results()
        self.quality_evaluator.clear_results()

