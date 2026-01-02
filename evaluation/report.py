"""
Evaluation Report Generator.
Creates human-readable and structured reports from evaluation results.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class ReportGenerator:
    """
    Generates evaluation reports in various formats.
    
    Supports:
    - Human-readable text reports
    - JSON reports
    - HTML reports (optional)
    """
    
    def __init__(self, results: Dict[str, Any]):
        """
        Initialize the report generator.
        
        Args:
            results: Evaluation results dictionary from EvaluationRunner
        """
        self.results = results
        self.timestamp = results.get("timestamp", datetime.now().isoformat())
    
    def generate_text_report(self) -> str:
        """
        Generate a human-readable text report.
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 70)
        lines.append("EVALUATION REPORT")
        lines.append("=" * 70)
        lines.append(f"Generated: {self.timestamp}")
        lines.append("")
        
        # Intent Classification
        if "intent_classification" in self.results:
            intent = self.results["intent_classification"]
            if "error" not in intent:
                lines.append("INTENT CLASSIFICATION")
                lines.append("-" * 70)
                lines.append(f"Accuracy: {intent.get('accuracy', 0):.2%}")
                lines.append(f"Macro F1: {intent.get('macro_f1', 0):.4f}")
                
                weakest = intent.get("weakest_class")
                if weakest:
                    lines.append(f"Weakest class: '{weakest.get('name', 'N/A')}' (F1={weakest.get('f1', 0):.2f})")
                
                per_class = intent.get("per_class", {})
                if per_class:
                    lines.append("\nPer-class metrics:")
                    for cls, metrics in per_class.items():
                        lines.append(
                            f"  {cls}: P={metrics.get('precision', 0):.2f} "
                            f"R={metrics.get('recall', 0):.2f} "
                            f"F1={metrics.get('f1', 0):.2f}"
                        )
                lines.append("")
        
        # Agent Performance
        if "agents" in self.results:
            agents = self.results["agents"]
            if "error" not in agents:
                lines.append("AGENT PERFORMANCE")
                lines.append("-" * 70)
                
                for agent_type, agent_result in agents.items():
                    if isinstance(agent_result, dict) and "error" not in agent_result:
                        if agent_type == "reservation":
                            success_rate = agent_result.get("task_success_rate", 0)
                            param_rate = agent_result.get("param_extraction_rate", 0)
                            lines.append(f"Reservation: {success_rate:.0%} task success, {param_rate:.0%} param extraction")
                        elif agent_type == "general":
                            success_rate = agent_result.get("success_rate", 0)
                            lines.append(f"General: {success_rate:.0%} success rate")
                        elif agent_type == "order":
                            success_rate = agent_result.get("success_rate", 0)
                            lines.append(f"Order: {success_rate:.0%} success rate")
                lines.append("")
        
        # RAG Retrieval
        if "rag" in self.results:
            rag = self.results["rag"]
            if "error" not in rag:
                lines.append("RAG RETRIEVAL")
                lines.append("-" * 70)
                lines.append(f"MRR: {rag.get('mrr', 0):.4f}")
                
                precision_at_k = rag.get("precision_at_k", {})
                if precision_at_k:
                    for k, precision in precision_at_k.items():
                        lines.append(f"Precision@{k}: {precision:.2f}")
                
                # Ragas metrics
                ragas = rag.get("ragas", {})
                if ragas and "error" not in ragas:
                    lines.append("\nRagas Metrics:")
                    lines.append(f"  Answer Relevancy: {ragas.get('answer_relevancy', 0):.3f}")
                    lines.append(f"  Faithfulness: {ragas.get('faithfulness', 0):.3f}")
                    lines.append(f"  Context Precision: {ragas.get('context_precision', 0):.3f}")
                    lines.append(f"  Context Recall: {ragas.get('context_recall', 0):.3f}")
                    lines.append(f"  Average Score: {ragas.get('average_score', 0):.3f}")
                elif ragas and "error" in ragas:
                    lines.append(f"\nRagas: {ragas.get('error', 'Not available')}")
                
                lines.append("")
        
        # End-to-End
        if "end_to_end" in self.results:
            e2e = self.results["end_to_end"]
            if "error" not in e2e:
                lines.append("END-TO-END TASK COMPLETION")
                lines.append("-" * 70)
                lines.append(f"Success rate: {e2e.get('success_rate', 0):.2%}")
                lines.append(f"Avg turns to completion: {e2e.get('avg_turns_to_completion', 0):.1f}")
                
                error_recovery = e2e.get("error_recovery_rate")
                if error_recovery is not None:
                    lines.append(f"Error recovery rate: {error_recovery:.2%}")
                lines.append("")
        
        # Response Quality
        if "quality" in self.results:
            quality = self.results["quality"]
            if "error" not in quality:
                lines.append("RESPONSE QUALITY (LLM Judge)")
                lines.append("-" * 70)
                overall = quality.get("overall", {})
                if overall:
                    lines.append(f"Avg Score: {overall.get('mean', 0):.2f}/5 (±{overall.get('std', 0):.2f})")
                
                per_criterion = quality.get("per_criterion", {})
                if per_criterion:
                    lines.append("\nPer-criterion scores:")
                    for criterion, scores in per_criterion.items():
                        lines.append(f"  {criterion.capitalize()}: {scores.get('mean', 0):.2f}/5")
                
                weakest = quality.get("weakest_criterion")
                if weakest:
                    lines.append(f"\nLowest: {weakest.get('name', 'N/A')} ({weakest.get('score', 0):.2f})")
                lines.append("")
        
        # Recommendations
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 70)
        recommendations = self._generate_recommendations()
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"{i}. {rec}")
        else:
            lines.append("No specific recommendations at this time.")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def generate_json_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate a JSON report.
        
        Args:
            output_path: Optional path to save JSON file
        
        Returns:
            JSON string representation
        """
        report_data = {
            "metadata": {
                "timestamp": self.timestamp,
                "version": "1.0"
            },
            "results": self.results
        }
        
        json_str = json.dumps(report_data, indent=2, default=str)
        
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on evaluation results."""
        recommendations = []
        
        # Intent classification recommendations
        if "intent_classification" in self.results:
            intent = self.results["intent_classification"]
            if "error" not in intent:
                accuracy = intent.get("accuracy", 1.0)
                if accuracy < 0.90:
                    recommendations.append(
                        f"Intent classification accuracy is {accuracy:.0%}. "
                        "Consider adding more training examples or improving the classification prompt."
                    )
                
                weakest = intent.get("weakest_class")
                if weakest and weakest.get("f1", 1.0) < 0.80:
                    recommendations.append(
                        f"Intent class '{weakest.get('name')}' has low F1-score ({weakest.get('f1', 0):.2f}). "
                        "Add more examples for this class."
                    )
        
        # Agent recommendations
        if "agents" in self.results:
            agents = self.results["agents"]
            if isinstance(agents, dict):
                for agent_type, agent_result in agents.items():
                    if isinstance(agent_result, dict) and "error" not in agent_result:
                        if agent_type == "reservation":
                            success_rate = agent_result.get("task_success_rate", 1.0)
                            if success_rate < 0.85:
                                recommendations.append(
                                    f"Reservation agent task success rate is {success_rate:.0%}. "
                                    "Review tool call logic and parameter extraction."
                                )
                        
        
        # RAG recommendations
        if "rag" in self.results:
            rag = self.results["rag"]
            if "error" not in rag:
                mrr = rag.get("mrr", 1.0)
                if mrr < 0.80:
                    recommendations.append(
                        f"RAG retrieval MRR is {mrr:.2f}. "
                        "Consider improving document embeddings or query formulation."
                    )
                
                precision_3 = rag.get("precision_at_k", {}).get(3, 1.0)
                if precision_3 < 0.70:
                    recommendations.append(
                        f"RAG Precision@3 is {precision_3:.2f}. "
                        "Review document chunking strategy or embedding model."
                    )
                
                # Ragas-based recommendations
                ragas = rag.get("ragas", {})
                if ragas and "error" not in ragas:
                    faithfulness = ragas.get("faithfulness", 1.0)
                    if faithfulness < 0.80:
                        recommendations.append(
                            f"Ragas faithfulness score is {faithfulness:.2f}. "
                            "Responses may not be well-grounded in retrieved context. "
                            "Improve answer generation to better use context."
                        )
                    
                    answer_relevancy = ragas.get("answer_relevancy", 1.0)
                    if answer_relevancy < 0.80:
                        recommendations.append(
                            f"Ragas answer relevancy is {answer_relevancy:.2f}. "
                            "Responses may not adequately address queries. "
                            "Review prompt engineering for answer generation."
                        )
                    
                    context_recall = ragas.get("context_recall", 1.0)
                    if context_recall < 0.70:
                        recommendations.append(
                            f"Ragas context recall is {context_recall:.2f}. "
                            "May be missing relevant information in retrieval. "
                            "Consider increasing retrieval count or improving embeddings."
                        )
        
        # E2E recommendations
        if "end_to_end" in self.results:
            e2e = self.results["end_to_end"]
            if "error" not in e2e:
                success_rate = e2e.get("success_rate", 1.0)
                if success_rate < 0.85:
                    recommendations.append(
                        f"End-to-end task success rate is {success_rate:.0%}. "
                        "Review conversation flow and error handling."
                    )
                
                avg_turns = e2e.get("avg_turns_to_completion", 0)
                if avg_turns > 4:
                    recommendations.append(
                        f"Average turns to completion is {avg_turns:.1f}. "
                        "Optimize agent efficiency to reduce conversation length."
                    )
        
        # Quality recommendations
        if "quality" in self.results:
            quality = self.results["quality"]
            if "error" not in quality:
                overall = quality.get("overall", {})
                avg_score = overall.get("mean", 5.0)
                if avg_score < 4.0:
                    recommendations.append(
                        f"Response quality score is {avg_score:.1f}/5. "
                        "Improve response generation prompts and tone consistency."
                    )
                
                weakest = quality.get("weakest_criterion")
                if weakest and weakest.get("score", 5.0) < 3.5:
                    recommendations.append(
                        f"Response quality is weakest in '{weakest.get('name')}' ({weakest.get('score', 0):.1f}/5). "
                        "Focus improvement efforts on this aspect."
                    )
        
        return recommendations
    
    def save_report(self, output_dir: str = "evaluation_reports"):
        """
        Save both text and JSON reports to files.
        
        Args:
            output_dir: Directory to save reports
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save text report
        text_report = self.generate_text_report()
        text_file = output_path / f"evaluation_report_{timestamp_str}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_report)
        
        # Save JSON report
        json_file = output_path / f"evaluation_report_{timestamp_str}.json"
        self.generate_json_report(str(json_file))
        
        print(f"Reports saved to:")
        print(f"  - {text_file}")
        print(f"  - {json_file}")
        
        return str(text_file), str(json_file)

