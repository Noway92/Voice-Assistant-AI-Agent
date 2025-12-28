"""
Response Quality Evaluator.
Uses LLM-as-a-judge pattern to assess response quality.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from evaluation.metrics import aggregate_scores


class QualityEvaluator:
    """
    Evaluates response quality using LLM-as-a-judge pattern.
    
    Criteria (1-5 scale):
    - Relevance: How well the response addresses the query
    - Accuracy: Factual correctness of the information
    - Helpfulness: How useful the response is to the user
    - Tone: Appropriateness of professional, courteous tone
    """
    
    QUALITY_CRITERIA = {
        "relevance": "How well does the response address the user's query? (1=completely off-topic, 5=perfectly relevant)",
        "accuracy": "Is the information provided factually correct? (1=mostly incorrect, 5=completely accurate)",
        "helpfulness": "How useful is this response for the user? (1=not helpful at all, 5=extremely helpful)",
        "tone": "Is the tone professional, courteous, and appropriate for a restaurant assistant? (1=inappropriate, 5=perfect tone)"
    }
    
    def __init__(self, llm=None, use_offline: bool = True):
        """
        Initialize the quality evaluator.
        
        Args:
            llm: LLM instance for judging (if None, will create one)
            use_offline: Whether to use offline (Ollama) or online (OpenAI) LLM
        """
        self.llm = llm
        self.use_offline = use_offline
        self.results = []
        
        if self.llm is None:
            self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM for judging."""
        try:
            if self.use_offline:
                from langchain_ollama import OllamaLLM
                self.llm = OllamaLLM(model="llama3", temperature=0)
            else:
                from langchain.chat_models import ChatOpenAI
                api_key = os.getenv("API_KEY_OPENAI")
                if api_key:
                    self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
                else:
                    print("Warning: API_KEY_OPENAI not found, quality evaluation will be limited")
                    self.llm = None
        except Exception as e:
            print(f"Warning: Could not initialize LLM for quality evaluation: {e}")
            self.llm = None
    
    def evaluate_single(
        self,
        query: str,
        response: str,
        context: Optional[str] = None,
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single query-response pair.
        
        Args:
            query: User query
            response: Assistant response
            context: Optional context (conversation history, RAG documents)
            ground_truth: Optional expected/ideal response
            
        Returns:
            Dictionary with scores for each criterion
        """
        if self.llm is None:
            return self._fallback_evaluation(query, response, ground_truth)
        
        # Build the evaluation prompt
        prompt = self._build_evaluation_prompt(query, response, context, ground_truth)
        
        try:
            llm_response = self.llm.invoke(prompt)
            
            # Parse LLM response
            if hasattr(llm_response, 'content'):
                response_text = llm_response.content
            else:
                response_text = str(llm_response)
            
            scores = self._parse_scores(response_text)
            
            result = {
                "query": query,
                "response": response,
                "scores": scores,
                "overall_score": sum(scores.values()) / len(scores) if scores else 0,
                "llm_feedback": response_text,
                "error": None
            }
            
        except Exception as e:
            result = {
                "query": query,
                "response": response,
                "scores": {},
                "overall_score": 0,
                "llm_feedback": None,
                "error": str(e)
            }
        
        self.results.append(result)
        return result
    
    def _build_evaluation_prompt(
        self,
        query: str,
        response: str,
        context: Optional[str] = None,
        ground_truth: Optional[str] = None
    ) -> str:
        """Build the LLM evaluation prompt."""
        prompt = f"""You are an expert evaluator for a restaurant voice assistant. 
Evaluate the following assistant response on a scale of 1-5 for each criterion.

USER QUERY: {query}

ASSISTANT RESPONSE: {response}
"""
        
        if context:
            prompt += f"\nCONTEXT: {context}\n"
        
        if ground_truth:
            prompt += f"\nEXPECTED/IDEAL RESPONSE: {ground_truth}\n"
        
        prompt += """
EVALUATION CRITERIA:
1. RELEVANCE (1-5): How well does the response address the user's query?
2. ACCURACY (1-5): Is the information factually correct?
3. HELPFULNESS (1-5): How useful is this response?
4. TONE (1-5): Is the tone professional and appropriate?

Provide your evaluation in this EXACT format:
RELEVANCE: [score]
ACCURACY: [score]
HELPFULNESS: [score]
TONE: [score]
FEEDBACK: [brief explanation]

Be strict but fair in your evaluation."""
        
        return prompt
    
    def _parse_scores(self, response_text: str) -> Dict[str, float]:
        """Parse scores from LLM response."""
        scores = {}
        
        lines = response_text.upper().split('\n')
        
        for criterion in self.QUALITY_CRITERIA.keys():
            criterion_upper = criterion.upper()
            for line in lines:
                if criterion_upper in line and ':' in line:
                    try:
                        # Extract number after colon
                        parts = line.split(':')
                        if len(parts) >= 2:
                            score_part = parts[1].strip()
                            # Get first number found
                            for char in score_part:
                                if char.isdigit():
                                    score = int(char)
                                    if 1 <= score <= 5:
                                        scores[criterion] = float(score)
                                    break
                    except:
                        pass
        
        # Fill missing scores with neutral value
        for criterion in self.QUALITY_CRITERIA.keys():
            if criterion not in scores:
                scores[criterion] = 3.0  # Neutral
        
        return scores
    
    def _fallback_evaluation(
        self,
        query: str,
        response: str,
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fallback evaluation using heuristics when LLM is not available.
        """
        scores = {}
        
        query_lower = query.lower()
        response_lower = response.lower() if response else ""
        
        # Relevance: Check if response contains query keywords
        query_words = set(query_lower.split())
        response_words = set(response_lower.split())
        common_words = query_words & response_words - {"the", "a", "an", "is", "are", "do", "you", "i", "what", "how"}
        relevance_ratio = len(common_words) / max(len(query_words), 1)
        scores["relevance"] = min(5, max(1, 1 + relevance_ratio * 4))
        
        # Accuracy: If ground truth provided, compare
        if ground_truth:
            gt_words = set(ground_truth.lower().split())
            match_ratio = len(response_words & gt_words) / max(len(gt_words), 1)
            scores["accuracy"] = min(5, max(1, 1 + match_ratio * 4))
        else:
            scores["accuracy"] = 3.0  # Neutral without ground truth
        
        # Helpfulness: Check response length and structure
        if len(response) > 50:
            scores["helpfulness"] = 4.0
        elif len(response) > 20:
            scores["helpfulness"] = 3.0
        else:
            scores["helpfulness"] = 2.0
        
        # Tone: Check for politeness indicators
        polite_indicators = ["please", "thank", "welcome", "happy to help", "certainly"]
        negative_indicators = ["error", "cannot", "unable", "sorry"]
        
        polite_count = sum(1 for ind in polite_indicators if ind in response_lower)
        negative_count = sum(1 for ind in negative_indicators if ind in response_lower)
        
        tone_score = 3 + polite_count - negative_count
        scores["tone"] = min(5, max(1, tone_score))
        
        result = {
            "query": query,
            "response": response,
            "scores": scores,
            "overall_score": sum(scores.values()) / len(scores),
            "llm_feedback": "Heuristic evaluation (LLM not available)",
            "error": None
        }
        
        self.results.append(result)
        return result
    
    def evaluate_batch(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate a batch of query-response pairs.
        
        Args:
            test_cases: List of dicts with 'query', 'response', optional 'context', 'ground_truth'
            
        Returns:
            Aggregated quality metrics
        """
        self.results = []
        
        for case in test_cases:
            self.evaluate_single(
                query=case.get("query", ""),
                response=case.get("response", ""),
                context=case.get("context"),
                ground_truth=case.get("ground_truth")
            )
        
        return self.compute_metrics()
    
    def compute_metrics(self) -> Dict[str, Any]:
        """
        Compute aggregated quality metrics.
        
        Returns:
            Dictionary with per-criterion and overall metrics
        """
        if not self.results:
            return {"error": "No results to evaluate"}
        
        valid_results = [r for r in self.results if r.get("scores")]
        
        if not valid_results:
            return {"error": "No valid scores"}
        
        # Aggregate per criterion
        per_criterion = {}
        for criterion in self.QUALITY_CRITERIA.keys():
            scores = [r["scores"].get(criterion, 0) for r in valid_results if r["scores"].get(criterion)]
            if scores:
                per_criterion[criterion] = aggregate_scores(scores)
        
        # Overall scores
        overall_scores = [r.get("overall_score", 0) for r in valid_results]
        overall_metrics = aggregate_scores(overall_scores)
        
        # Find weakest criterion
        criterion_means = {c: m["mean"] for c, m in per_criterion.items()}
        weakest = min(criterion_means.items(), key=lambda x: x[1]) if criterion_means else None
        
        return {
            "total_evaluated": len(valid_results),
            "errors": len(self.results) - len(valid_results),
            "overall": overall_metrics,
            "per_criterion": per_criterion,
            "weakest_criterion": {"name": weakest[0], "score": weakest[1]} if weakest else None
        }
    
    def get_low_scoring_responses(self, threshold: float = 3.0) -> List[Dict[str, Any]]:
        """
        Get responses that scored below a threshold.
        
        Args:
            threshold: Minimum acceptable score
            
        Returns:
            List of low-scoring results
        """
        return [
            r for r in self.results
            if r.get("overall_score", 0) < threshold
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
            "RESPONSE QUALITY EVALUATION (LLM Judge)",
            "=" * 50,
            f"Total evaluated: {metrics['total_evaluated']}",
            f"Errors: {metrics['errors']}",
            f"Overall score: {metrics['overall']['mean']:.2f}/5 (±{metrics['overall']['std']:.2f})",
            "",
            "Per-criterion scores:"
        ]
        
        for criterion, scores in metrics.get("per_criterion", {}).items():
            lines.append(f"  {criterion.capitalize()}: {scores['mean']:.2f}/5")
        
        weakest = metrics.get("weakest_criterion")
        if weakest:
            lines.append(f"\nWeakest: {weakest['name']} ({weakest['score']:.2f})")
        
        low_scoring = self.get_low_scoring_responses(3.0)
        if low_scoring:
            lines.append(f"\nLow-scoring responses: {len(low_scoring)}")
            for r in low_scoring[:2]:
                lines.append(f"  - Query: '{r['query'][:40]}...' (score: {r['overall_score']:.1f})")
        
        return "\n".join(lines)

