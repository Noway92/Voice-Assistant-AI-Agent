"""
Metrics computation utilities for evaluation framework.
Provides reusable functions for classification, retrieval, and task metrics.
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import numpy as np


def compute_classification_metrics(
    y_true: List[str],
    y_pred: List[str],
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compute classification metrics: accuracy, precision, recall, F1-score.
    
    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels
        labels: Optional list of label names for ordering
        
    Returns:
        Dictionary with accuracy, per-class metrics, macro averages, and confusion matrix
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    
    if len(y_true) == 0:
        return {"error": "Empty input"}
    
    # Get unique labels
    if labels is None:
        labels = sorted(list(set(y_true) | set(y_pred)))
    
    # Accuracy
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / len(y_true)
    
    # Per-class metrics
    per_class = {}
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        support = sum(1 for t in y_true if t == label)
        
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support
        }
    
    # Macro averages
    macro_precision = np.mean([m["precision"] for m in per_class.values()])
    macro_recall = np.mean([m["recall"] for m in per_class.values()])
    macro_f1 = np.mean([m["f1"] for m in per_class.values()])
    
    # Confusion matrix
    confusion_matrix = {}
    for true_label in labels:
        confusion_matrix[true_label] = {}
        for pred_label in labels:
            count = sum(1 for t, p in zip(y_true, y_pred) if t == true_label and p == pred_label)
            confusion_matrix[true_label][pred_label] = count
    
    return {
        "accuracy": accuracy,
        "per_class": per_class,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "confusion_matrix": confusion_matrix,
        "total_samples": len(y_true)
    }


def compute_retrieval_metrics(
    queries: List[str],
    retrieved_docs: List[List[str]],
    relevant_docs: List[List[str]],
    k_values: List[int] = [3, 5]
) -> Dict[str, Any]:
    """
    Compute retrieval metrics: Precision@K, Recall@K, MRR.
    
    Args:
        queries: List of query strings
        retrieved_docs: List of retrieved document IDs for each query
        relevant_docs: List of relevant document IDs for each query (ground truth)
        k_values: Values of K for Precision@K and Recall@K
        
    Returns:
        Dictionary with MRR, Precision@K, Recall@K for each K value
    """
    if len(queries) != len(retrieved_docs) or len(queries) != len(relevant_docs):
        raise ValueError("All input lists must have the same length")
    
    if len(queries) == 0:
        return {"error": "Empty input"}
    
    # Mean Reciprocal Rank
    reciprocal_ranks = []
    for retrieved, relevant in zip(retrieved_docs, relevant_docs):
        relevant_set = set(relevant)
        rr = 0.0
        for i, doc_id in enumerate(retrieved):
            if doc_id in relevant_set:
                rr = 1.0 / (i + 1)
                break
        reciprocal_ranks.append(rr)
    
    mrr = np.mean(reciprocal_ranks)
    
    # Precision@K and Recall@K
    precision_at_k = {}
    recall_at_k = {}
    
    for k in k_values:
        precisions = []
        recalls = []
        
        for retrieved, relevant in zip(retrieved_docs, relevant_docs):
            relevant_set = set(relevant)
            retrieved_at_k = retrieved[:k]
            
            # Relevant docs in top-k
            relevant_in_k = sum(1 for doc in retrieved_at_k if doc in relevant_set)
            
            precision = relevant_in_k / k if k > 0 else 0.0
            recall = relevant_in_k / len(relevant_set) if len(relevant_set) > 0 else 0.0
            
            precisions.append(precision)
            recalls.append(recall)
        
        precision_at_k[k] = np.mean(precisions)
        recall_at_k[k] = np.mean(recalls)
    
    return {
        "mrr": mrr,
        "precision_at_k": precision_at_k,
        "recall_at_k": recall_at_k,
        "total_queries": len(queries)
    }


def compute_task_completion_rate(
    results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compute task completion metrics from evaluation results.
    
    Args:
        results: List of task results with 'success', 'turns', 'error_recovered' fields
        
    Returns:
        Dictionary with success rate, avg turns, error recovery rate
    """
    if len(results) == 0:
        return {"error": "Empty input"}
    
    # Success rate
    successes = sum(1 for r in results if r.get("success", False))
    success_rate = successes / len(results)
    
    # Average turns to completion (for successful tasks)
    successful_turns = [r.get("turns", 0) for r in results if r.get("success", False)]
    avg_turns = np.mean(successful_turns) if successful_turns else 0.0
    
    # Error recovery rate
    tasks_with_errors = [r for r in results if r.get("had_error", False)]
    if tasks_with_errors:
        recovered = sum(1 for r in tasks_with_errors if r.get("error_recovered", False))
        error_recovery_rate = recovered / len(tasks_with_errors)
    else:
        error_recovery_rate = None  # No errors occurred
    
    # Per-task-type breakdown
    by_task_type = {}
    for r in results:
        task_type = r.get("task_type", "unknown")
        if task_type not in by_task_type:
            by_task_type[task_type] = {"total": 0, "success": 0}
        by_task_type[task_type]["total"] += 1
        if r.get("success", False):
            by_task_type[task_type]["success"] += 1
    
    for task_type in by_task_type:
        total = by_task_type[task_type]["total"]
        success = by_task_type[task_type]["success"]
        by_task_type[task_type]["success_rate"] = success / total if total > 0 else 0.0
    
    return {
        "success_rate": success_rate,
        "avg_turns_to_completion": avg_turns,
        "error_recovery_rate": error_recovery_rate,
        "by_task_type": by_task_type,
        "total_tasks": len(results),
        "successful_tasks": successes
    }


def compute_semantic_similarity(
    text1: str,
    text2: str,
    embedding_function: Optional[callable] = None
) -> float:
    """
    Compute semantic similarity between two texts using embeddings.
    
    Args:
        text1: First text
        text2: Second text  
        embedding_function: Function to compute embeddings (returns numpy array)
        
    Returns:
        Cosine similarity score between 0 and 1
    """
    if embedding_function is None:
        # Fallback to simple word overlap (Jaccard similarity)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0
    
    # Use embeddings for semantic similarity
    emb1 = embedding_function(text1)
    emb2 = embedding_function(text2)
    
    # Cosine similarity
    dot_product = np.dot(emb1, emb2)
    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def aggregate_scores(
    scores: List[float],
    weights: Optional[List[float]] = None
) -> Dict[str, float]:
    """
    Aggregate a list of scores into summary statistics.
    
    Args:
        scores: List of numeric scores
        weights: Optional weights for weighted average
        
    Returns:
        Dictionary with mean, std, min, max, median
    """
    if len(scores) == 0:
        return {"error": "Empty input"}
    
    scores_array = np.array(scores)
    
    result = {
        "mean": float(np.mean(scores_array)),
        "std": float(np.std(scores_array)),
        "min": float(np.min(scores_array)),
        "max": float(np.max(scores_array)),
        "median": float(np.median(scores_array)),
        "count": len(scores)
    }
    
    if weights is not None and len(weights) == len(scores):
        weights_array = np.array(weights)
        result["weighted_mean"] = float(np.average(scores_array, weights=weights_array))
    
    return result

