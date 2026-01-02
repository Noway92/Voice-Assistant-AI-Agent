"""
RAG Retrieval Evaluator.
Measures the quality of document retrieval from ChromaDB.
Includes Ragas-based evaluation for comprehensive RAG assessment.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evaluation.metrics import compute_retrieval_metrics, compute_semantic_similarity

# Try to import Ragas (optional dependency)
try:
    from ragas import evaluate
    from ragas.metrics import (
        answer_relevancy,
        faithfulness,
        context_precision,
        context_recall,
    )
    try:
        from datasets import Dataset
    except ImportError:
        # Fallback for older versions
        try:
            from ragas.dataset_schema import Dataset
        except ImportError:
            Dataset = None
    RAGAS_AVAILABLE = True and Dataset is not None
except ImportError:
    RAGAS_AVAILABLE = False
    Dataset = None
    # Don't print warning here - let the user know when they try to use it


class RAGEvaluator:
    """
    Evaluates RAG (Retrieval-Augmented Generation) performance.
    
    Measures:
    - Retrieval Precision@K
    - Mean Reciprocal Rank (MRR)
    - Semantic similarity between queries and retrieved documents
    - Ragas metrics (if available): Answer Relevancy, Faithfulness, Context Precision/Recall
    """
    
    def __init__(self, embeddings_manager=None, agent=None):
        """
        Initialize the RAG evaluator.
        
        Args:
            embeddings_manager: The EmbeddingsManager instance to evaluate
            agent: Optional agent instance (e.g., GeneralInqueriesAgent) to generate responses
        """
        self.embeddings_manager = embeddings_manager
        self.agent = agent
        self.results = []
        self.ragas_results = []
    
    def set_embeddings_manager(self, embeddings_manager):
        """Set or update the embeddings manager."""
        self.embeddings_manager = embeddings_manager
    
    def set_agent(self, agent):
        """Set or update the agent instance for generating responses."""
        self.agent = agent
    
    def evaluate_single(
        self,
        query: str,
        relevant_doc_ids: List[str],
        k: int = 5,
        filter_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single retrieval query.
        
        Args:
            query: Search query
            relevant_doc_ids: Ground truth relevant document IDs
            k: Number of results to retrieve
            filter_type: Optional filter for document type
            
        Returns:
            Dictionary with query, retrieved docs, and relevance metrics
        """
        if self.embeddings_manager is None:
            raise ValueError("EmbeddingsManager not set. Use set_embeddings_manager() first.")
        
        # Perform search
        search_results = self.embeddings_manager.search(
            query=query,
            n_results=k,
            filter_type=filter_type
        )
        
        # Handle error case
        if isinstance(search_results, str):
            return {
                "query": query,
                "error": search_results,
                "retrieved_ids": [],
                "relevant_ids": relevant_doc_ids
            }
        
        # Extract retrieved document IDs - use the ID field if available
        retrieved_ids = []
        retrieved_texts = []
        scores = []
        
        for result in search_results:
            # Try to get ID from result (if search() returns it)
            # Otherwise reconstruct from metadata
            if "id" in result:
                doc_id = result["id"]
            else:
                # Fallback: reconstruct from metadata
                doc_type = result.get("metadata", {}).get("type", "unknown")
                item_id = result.get("metadata", {}).get("item_id", result.get("metadata", {}).get("question", "unknown"))
                doc_id = f"{doc_type}_{item_id}" if item_id != "unknown" else doc_type
            
            retrieved_ids.append(doc_id)
            retrieved_texts.append(result.get("text", ""))
            scores.append(result.get("score", 0))
        
        # Calculate metrics for this query
        relevant_set = set(relevant_doc_ids)
        
        # Precision@K
        relevant_in_k = sum(1 for doc_id in retrieved_ids if doc_id in relevant_set)
        precision_at_k = relevant_in_k / k if k > 0 else 0.0
        
        # Reciprocal Rank
        reciprocal_rank = 0.0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in relevant_set:
                reciprocal_rank = 1.0 / (i + 1)
                break
        
        # Hit@K (at least one relevant doc in top-K)
        hit_at_k = relevant_in_k > 0
        
        result = {
            "query": query,
            "retrieved_ids": retrieved_ids,
            "retrieved_texts": retrieved_texts[:3],  # Store first 3 for inspection
            "relevant_ids": relevant_doc_ids,
            "scores": scores,
            "precision_at_k": precision_at_k,
            "reciprocal_rank": reciprocal_rank,
            "hit_at_k": hit_at_k,
            "k": k,
            "filter_type": filter_type,
            "error": None
        }
        
        self.results.append(result)
        return result
    
    def evaluate_batch(
        self,
        test_cases: List[Dict[str, Any]],
        k_values: List[int] = [3, 5]
    ) -> Dict[str, Any]:
        """
        Evaluate a batch of retrieval test cases.
        
        Args:
            test_cases: List of dicts with 'query' and 'relevant_doc_ids'
            k_values: Values of K for Precision@K
            
        Returns:
            Aggregated metrics across all queries
        """
        self.results = []  # Reset results
        
        all_results = {k: [] for k in k_values}
        
        for case in test_cases:
            query = case.get("query", "")
            relevant_ids = case.get("relevant_doc_ids", [])
            filter_type = case.get("filter_type")
            
            if not query:
                continue
            
            for k in k_values:
                result = self.evaluate_single(
                    query=query,
                    relevant_doc_ids=relevant_ids,
                    k=k,
                    filter_type=filter_type
                )
                all_results[k].append(result)
        
        return self.compute_aggregated_metrics(all_results, k_values)
    
    def compute_aggregated_metrics(
        self,
        results_by_k: Dict[int, List[Dict[str, Any]]],
        k_values: List[int]
    ) -> Dict[str, Any]:
        """
        Compute aggregated metrics from batch results.
        
        Args:
            results_by_k: Results grouped by K value
            k_values: List of K values
            
        Returns:
            Dictionary with aggregated metrics
        """
        metrics = {
            "total_queries": 0,
            "mrr": 0.0,
            "precision_at_k": {},
            "hit_rate_at_k": {},
            "errors": 0
        }
        
        for k in k_values:
            results = results_by_k.get(k, [])
            if not results:
                continue
            
            valid_results = [r for r in results if r.get("error") is None]
            error_count = len(results) - len(valid_results)
            
            if valid_results:
                # MRR (use first k's results for MRR)
                if k == k_values[0]:
                    metrics["mrr"] = sum(r["reciprocal_rank"] for r in valid_results) / len(valid_results)
                    metrics["total_queries"] = len(valid_results)
                    metrics["errors"] = error_count
                
                # Precision@K
                metrics["precision_at_k"][k] = sum(r["precision_at_k"] for r in valid_results) / len(valid_results)
                
                # Hit Rate@K
                metrics["hit_rate_at_k"][k] = sum(1 for r in valid_results if r["hit_at_k"]) / len(valid_results)
        
        return metrics
    
    def evaluate_semantic_quality(
        self,
        test_cases: List[Dict[str, Any]],
        embedding_function: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Evaluate semantic similarity between queries and retrieved documents.
        
        Args:
            test_cases: List of dicts with 'query' and expected topics
            embedding_function: Optional embedding function for similarity
            
        Returns:
            Semantic similarity metrics
        """
        if self.embeddings_manager is None:
            raise ValueError("EmbeddingsManager not set.")
        
        similarities = []
        
        for case in test_cases:
            query = case.get("query", "")
            if not query:
                continue
            
            results = self.embeddings_manager.search(query=query, n_results=3)
            
            if isinstance(results, str):  # Error
                continue
            
            # Compute similarity between query and top results
            for result in results:
                text = result.get("text", "")
                if text:
                    sim = compute_semantic_similarity(query, text, embedding_function)
                    similarities.append({
                        "query": query,
                        "retrieved_text": text[:100],
                        "similarity": sim,
                        "retrieval_score": result.get("score", 0)
                    })
        
        if not similarities:
            return {"error": "No valid results"}
        
        avg_similarity = sum(s["similarity"] for s in similarities) / len(similarities)
        
        return {
            "avg_semantic_similarity": avg_similarity,
            "total_comparisons": len(similarities),
            "samples": similarities[:5]  # First 5 for inspection
        }
    
    def get_retrieval_failures(self) -> List[Dict[str, Any]]:
        """
        Get queries where retrieval failed (no relevant docs in top-K).
        
        Returns:
            List of failed queries with details
        """
        failures = []
        
        for result in self.results:
            if result.get("error"):
                failures.append({
                    "query": result["query"],
                    "reason": "error",
                    "details": result["error"]
                })
            elif not result.get("hit_at_k", False):
                failures.append({
                    "query": result["query"],
                    "reason": "no_relevant_in_topk",
                    "k": result.get("k"),
                    "retrieved": result.get("retrieved_ids", []),
                    "expected": result.get("relevant_ids", [])
                })
        
        return failures
    
    def clear_results(self):
        """Clear accumulated results."""
        self.results = []
    
    def get_summary(self) -> str:
        """
        Get a human-readable summary of the evaluation.
        
        Returns:
            Formatted string summary
        """
        if not self.results:
            return "No results to summarize"
        
        valid_results = [r for r in self.results if r.get("error") is None]
        
        if not valid_results:
            return "All queries resulted in errors"
        
        mrr = sum(r["reciprocal_rank"] for r in valid_results) / len(valid_results)
        avg_precision = sum(r["precision_at_k"] for r in valid_results) / len(valid_results)
        hit_rate = sum(1 for r in valid_results if r["hit_at_k"]) / len(valid_results)
        
        lines = [
            "=" * 50,
            "RAG RETRIEVAL EVALUATION",
            "=" * 50,
            f"Total queries: {len(valid_results)}",
            f"Errors: {len(self.results) - len(valid_results)}",
            f"MRR: {mrr:.4f}",
            f"Avg Precision@K: {avg_precision:.4f}",
            f"Hit Rate: {hit_rate:.2%}",
        ]
        
        failures = self.get_retrieval_failures()
        if failures:
            lines.append(f"\nRetrieval failures: {len(failures)}")
            for f in failures[:3]:
                lines.append(f"  - Query: '{f['query'][:50]}...'")
        
        return "\n".join(lines)
    
    def evaluate_with_ragas(
        self,
        test_cases: List[Dict[str, Any]],
        k: int = 5,
        use_ground_truth: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate RAG system using Ragas metrics.
        
        Ragas provides:
        - Answer Relevancy: How relevant is the answer to the query
        - Faithfulness: Is the answer faithful to the retrieved context
        - Context Precision: How precise/relevant are retrieved contexts
        - Context Recall: Did we retrieve all relevant contexts
        
        Args:
            test_cases: List of dicts with 'query' and optionally:
                       - 'reference' (ground truth answer)
                       - 'response' (pre-generated response, otherwise uses agent)
            k: Number of contexts to retrieve
            use_ground_truth: Whether to include ground truth references if available
            
        Returns:
            Dictionary with Ragas metrics
        """
        if not RAGAS_AVAILABLE:
            return {
                "error": "Ragas not available. Install with: pip install ragas",
                "ragas_available": False
            }
        
        if self.embeddings_manager is None:
            return {"error": "EmbeddingsManager not set"}
        
        # Prepare data for Ragas
        queries = []
        contexts_list = []
        responses = []
        ground_truths = []
        
        for case in test_cases:
            query = case.get("query", "")
            if not query:
                continue
            
            # Retrieve contexts
            search_results = self.embeddings_manager.search(query=query, n_results=k)
            if isinstance(search_results, str):  # Error
                continue
            
            # Extract context texts
            contexts = [result.get("text", "") for result in search_results]
            contexts_list.append(contexts)
            queries.append(query)
            
            # Get or generate response
            if "response" in case:
                response = case["response"]
            elif self.agent:
                try:
                    response = self.agent.process(query)
                    if hasattr(response, 'content'):
                        response = response.content
                    response = str(response)
                except Exception as e:
                    response = f"Error generating response: {e}"
            else:
                # Use first context as a simple response placeholder
                response = contexts[0] if contexts else ""
            
            responses.append(response)
            
            # Ground truth (optional)
            if use_ground_truth and "reference" in case:
                ground_truths.append(case["reference"])
            else:
                ground_truths.append("")  # Empty string if no ground truth
        
        if not queries:
            return {"error": "No valid queries to evaluate"}
        
        # Prepare dataset for Ragas
        eval_data = {
            "question": queries,
            "contexts": contexts_list,
            "answer": responses,
        }
        
        # Add ground truth if available
        if use_ground_truth and any(gt for gt in ground_truths):
            eval_data["ground_truth"] = ground_truths
        
        try:
            dataset = Dataset.from_dict(eval_data)
            
            # Define metrics to compute
            metrics_to_compute = [
                answer_relevancy,
                faithfulness,
                context_precision,
                context_recall,
            ]
            
            # Run evaluation
            result_dataset = evaluate(
                dataset=dataset,
                metrics=metrics_to_compute,
            )
            
            # Ragas returns a Dataset with metric scores as columns
            # Extract mean values for each metric
            ragas_metrics = {}
            
            # Try different ways to access the metrics
            if hasattr(result_dataset, 'to_pandas'):
                df = result_dataset.to_pandas()
                ragas_metrics["answer_relevancy"] = float(df.get("answer_relevancy", df.get("answer_relevancy_score", [0.0])).mean())
                ragas_metrics["faithfulness"] = float(df.get("faithfulness", df.get("faithfulness_score", [0.0])).mean())
                ragas_metrics["context_precision"] = float(df.get("context_precision", df.get("context_precision_score", [0.0])).mean())
                ragas_metrics["context_recall"] = float(df.get("context_recall", df.get("context_recall_score", [0.0])).mean())
            elif hasattr(result_dataset, 'to_dict'):
                result_dict = result_dataset.to_dict()
                # Extract mean from lists if present
                for metric_name in ["answer_relevancy", "faithfulness", "context_precision", "context_recall"]:
                    values = result_dict.get(metric_name, result_dict.get(f"{metric_name}_score", [0.0]))
                    if isinstance(values, list):
                        ragas_metrics[metric_name] = float(sum(values) / len(values)) if values else 0.0
                    else:
                        ragas_metrics[metric_name] = float(values)
            else:
                # Fallback: try to access as attributes
                ragas_metrics = {
                    "answer_relevancy": 0.0,
                    "faithfulness": 0.0,
                    "context_precision": 0.0,
                    "context_recall": 0.0,
                }
                for metric_name in ragas_metrics.keys():
                    try:
                        if hasattr(result_dataset, metric_name):
                            val = getattr(result_dataset, metric_name)
                            ragas_metrics[metric_name] = float(val) if not isinstance(val, list) else float(sum(val) / len(val))
                    except:
                        pass
            
            # Calculate average score
            ragas_metrics["average_score"] = sum(ragas_metrics.values()) / len(ragas_metrics)
            ragas_metrics["total_samples"] = len(queries)
            ragas_metrics["ragas_available"] = True
            
            self.ragas_results.append(ragas_metrics)
            
            return ragas_metrics
            
        except Exception as e:
            return {
                "error": f"Ragas evaluation failed: {str(e)}",
                "ragas_available": True
            }
    
    def evaluate_with_ragas_from_responses(
        self,
        queries: List[str],
        contexts_list: List[List[str]],
        responses: List[str],
        ground_truths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate RAG system using Ragas with pre-computed responses.
        
        Args:
            queries: List of query strings
            contexts_list: List of lists of context strings for each query
            responses: List of response strings
            ground_truths: Optional list of ground truth answers
            
        Returns:
            Dictionary with Ragas metrics
        """
        if not RAGAS_AVAILABLE:
            return {
                "error": "Ragas not available. Install with: pip install ragas",
                "ragas_available": False
            }
        
        if len(queries) != len(contexts_list) or len(queries) != len(responses):
            return {"error": "queries, contexts_list, and responses must have the same length"}
        
        # Prepare dataset
        eval_data = {
            "question": queries,
            "contexts": contexts_list,
            "answer": responses,
        }
        
        if ground_truths:
            eval_data["ground_truth"] = ground_truths
        
        try:
            dataset = Dataset.from_dict(eval_data)
            
            metrics_to_compute = [
                answer_relevancy,
                faithfulness,
                context_precision,
                context_recall,
            ]
            
            result_dataset = evaluate(
                dataset=dataset,
                metrics=metrics_to_compute,
            )
            
            # Extract metrics from result dataset
            ragas_metrics = {}
            if hasattr(result_dataset, 'to_pandas'):
                df = result_dataset.to_pandas()
                ragas_metrics["answer_relevancy"] = float(df.get("answer_relevancy", df.get("answer_relevancy_score", [0.0])).mean())
                ragas_metrics["faithfulness"] = float(df.get("faithfulness", df.get("faithfulness_score", [0.0])).mean())
                ragas_metrics["context_precision"] = float(df.get("context_precision", df.get("context_precision_score", [0.0])).mean())
                ragas_metrics["context_recall"] = float(df.get("context_recall", df.get("context_recall_score", [0.0])).mean())
            elif hasattr(result_dataset, 'to_dict'):
                result_dict = result_dataset.to_dict()
                for metric_name in ["answer_relevancy", "faithfulness", "context_precision", "context_recall"]:
                    values = result_dict.get(metric_name, result_dict.get(f"{metric_name}_score", [0.0]))
                    ragas_metrics[metric_name] = float(sum(values) / len(values)) if isinstance(values, list) and values else float(values) if not isinstance(values, list) else 0.0
            else:
                ragas_metrics = {"answer_relevancy": 0.0, "faithfulness": 0.0, "context_precision": 0.0, "context_recall": 0.0}
            
            ragas_metrics["average_score"] = sum(ragas_metrics.values()) / len(ragas_metrics)
            ragas_metrics["total_samples"] = len(queries)
            ragas_metrics["ragas_available"] = True
            
            return ragas_metrics
            
        except Exception as e:
            return {
                "error": f"Ragas evaluation failed: {str(e)}",
                "ragas_available": True
            }

