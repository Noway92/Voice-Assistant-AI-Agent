"""
Intent Classification Evaluator.
Measures the orchestrator's ability to correctly classify user intents.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evaluation.metrics import compute_classification_metrics


class IntentEvaluator:
    """
    Evaluates intent classification performance of the orchestrator.
    
    Measures:
    - Accuracy across all intent classes
    - Per-class precision, recall, F1-score
    - Confusion matrix to identify misclassification patterns
    """
    
    INTENT_CLASSES = ["general", "order", "reservation"]
    
    def __init__(self, orchestrator=None):
        """
        Initialize the evaluator.
        
        Args:
            orchestrator: The Orchestrator instance to evaluate
        """
        self.orchestrator = orchestrator
        self.results = []
    
    def set_orchestrator(self, orchestrator):
        """Set or update the orchestrator instance."""
        self.orchestrator = orchestrator
    
    def evaluate_single(self, input_text: str, expected_intent: str) -> Dict[str, Any]:
        """
        Evaluate a single intent classification.
        
        Args:
            input_text: User input to classify
            expected_intent: Ground truth intent label
            
        Returns:
            Dictionary with input, expected, predicted, and correct flag
        """
        if self.orchestrator is None:
            raise ValueError("Orchestrator not set. Use set_orchestrator() first.")
        
        # Get predicted intent
        predicted_intent = self.orchestrator._classify_intent(input_text)
        
        result = {
            "input": input_text,
            "expected": expected_intent,
            "predicted": predicted_intent,
            "correct": expected_intent == predicted_intent
        }
        
        self.results.append(result)
        return result
    
    def evaluate_batch(self, test_cases: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Evaluate a batch of test cases.
        
        Args:
            test_cases: List of dicts with 'input' and 'expected_intent' keys
            
        Returns:
            Dictionary with overall metrics and individual results
        """
        self.results = []  # Reset results
        
        for case in test_cases:
            input_text = case.get("input", "")
            expected = case.get("expected_intent", "")
            
            if input_text and expected:
                self.evaluate_single(input_text, expected)
        
        return self.compute_metrics()
    
    def compute_metrics(self) -> Dict[str, Any]:
        """
        Compute classification metrics from accumulated results.
        
        Returns:
            Dictionary with accuracy, per-class metrics, confusion matrix
        """
        if not self.results:
            return {"error": "No results to evaluate"}
        
        y_true = [r["expected"] for r in self.results]
        y_pred = [r["predicted"] for r in self.results]
        
        metrics = compute_classification_metrics(
            y_true=y_true,
            y_pred=y_pred,
            labels=self.INTENT_CLASSES
        )
        
        # Find weakest class
        per_class = metrics.get("per_class", {})
        if per_class:
            weakest = min(per_class.items(), key=lambda x: x[1]["f1"])
            metrics["weakest_class"] = {
                "name": weakest[0],
                "f1": weakest[1]["f1"]
            }
        
        # Add misclassification details
        misclassifications = [r for r in self.results if not r["correct"]]
        metrics["misclassifications"] = misclassifications
        metrics["misclassification_rate"] = len(misclassifications) / len(self.results)
        
        return metrics
    
    def get_confusion_pairs(self) -> List[Dict[str, Any]]:
        """
        Get frequently confused intent pairs.
        
        Returns:
            List of confusion pairs sorted by frequency
        """
        confusion_counts = {}
        
        for r in self.results:
            if not r["correct"]:
                pair = (r["expected"], r["predicted"])
                confusion_counts[pair] = confusion_counts.get(pair, 0) + 1
        
        sorted_pairs = sorted(
            confusion_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {"expected": pair[0], "predicted": pair[1], "count": count}
            for pair, count in sorted_pairs
        ]
    
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
            "INTENT CLASSIFICATION EVALUATION",
            "=" * 50,
            f"Total samples: {metrics['total_samples']}",
            f"Accuracy: {metrics['accuracy']:.2%}",
            f"Macro F1: {metrics['macro_f1']:.4f}",
            "",
            "Per-class metrics:",
        ]
        
        for cls, cls_metrics in metrics.get("per_class", {}).items():
            lines.append(
                f"  {cls}: P={cls_metrics['precision']:.2f} "
                f"R={cls_metrics['recall']:.2f} "
                f"F1={cls_metrics['f1']:.2f} "
                f"(n={cls_metrics['support']})"
            )
        
        if "weakest_class" in metrics:
            wc = metrics["weakest_class"]
            lines.append(f"\nWeakest class: '{wc['name']}' (F1={wc['f1']:.2f})")
        
        confusion_pairs = self.get_confusion_pairs()
        if confusion_pairs:
            lines.append("\nTop confusion pairs:")
            for pair in confusion_pairs[:3]:
                lines.append(
                    f"  '{pair['expected']}' → '{pair['predicted']}': {pair['count']} times"
                )
        
        return "\n".join(lines)

