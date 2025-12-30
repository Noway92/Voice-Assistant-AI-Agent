# Evaluation Framework

Comprehensive evaluation system for the Voice Assistant AI Agent.

## Overview

The evaluation framework provides multi-layered assessment of the agentic system:

1. **Intent Classification** - Measures orchestrator's ability to correctly route requests
2. **Agent Performance** - Evaluates individual specialized agents
3. **RAG Retrieval** - Measures ChromaDB document retrieval quality
4. **End-to-End Tasks** - Complete conversation scenario evaluation

## Quick Start

```python
from main import VoiceAssistant
from core.orchestrator import Orchestrator
from rag.rag import EmbeddingsManager
from evaluation.runner import EvaluationRunner
from evaluation.report import ReportGenerator

# Initialize components
orchestrator = Orchestrator(isOffline=False)
voice_assistant = VoiceAssistant(isOffline=False)
embeddings_manager = EmbeddingsManager()

# Create runner
runner = EvaluationRunner(
    orchestrator=orchestrator,
    voice_assistant=voice_assistant,
    embeddings_manager=embeddings_manager,
    is_offline=False
)

# Run evaluation
results = runner.run_full_evaluation()

# Generate report
report_generator = ReportGenerator(results)
print(report_generator.generate_text_report())
report_generator.save_report("evaluation_reports")
```

## Directory Structure

```
evaluation/
├── __init__.py
├── runner.py              # Main evaluation orchestrator
├── report.py              # Report generation
├── metrics.py             # Metric computation utilities
├── example_usage.py       # Example script
├── datasets/              # Test datasets
│   ├── intent_test_data.json
│   ├── reservation_scenarios.json
│   ├── menu_queries.json
│   └── general_queries.json
└── evaluators/            # Individual evaluators
    ├── intent_evaluator.py
    ├── agent_evaluator.py
    ├── rag_evaluator.py
    └── e2e_evaluator.py
```

## Evaluation Components

### Intent Evaluator

Evaluates the orchestrator's intent classification:

```python
from evaluation.evaluators.intent_evaluator import IntentEvaluator

evaluator = IntentEvaluator(orchestrator)
metrics = evaluator.evaluate_batch(test_cases)
```

**Metrics**: Accuracy, Precision, Recall, F1-score per intent class, Confusion matrix

### Agent Evaluator

Evaluates individual agents (reservation, general, order):

**Note**: Menu queries are now handled by the GeneralInqueriesAgent (merged).

```python
from evaluation.evaluators.agent_evaluator import AgentEvaluator

evaluator = AgentEvaluator()
metrics = evaluator.evaluate_reservation_agent(reservation_agent, test_cases)
metrics = evaluator.evaluate_general_agent(general_agent, test_cases)  # Handles both general + menu queries
```

**Metrics**: Task success rate, parameter extraction rate, keyword coverage

### RAG Evaluator

Evaluates document retrieval from ChromaDB with both traditional metrics and Ragas:

```python
from evaluation.evaluators.rag_evaluator import RAGEvaluator

evaluator = RAGEvaluator(embeddings_manager, agent=general_agent)
metrics = evaluator.evaluate_batch(test_cases, k_values=[3, 5])

# Ragas evaluation (comprehensive RAG assessment)
ragas_metrics = evaluator.evaluate_with_ragas(test_cases, k=5)
```

**Traditional Metrics**: MRR (Mean Reciprocal Rank), Precision@K, Hit Rate@K

**Ragas Metrics** (if installed):
- **Answer Relevancy**: How relevant is the answer to the query
- **Faithfulness**: Is the answer faithful to the retrieved context (grounded)
- **Context Precision**: How precise/relevant are retrieved contexts
- **Context Recall**: Did we retrieve all relevant contexts

### E2E Evaluator

Evaluates complete conversation scenarios:

```python
from evaluation.evaluators.e2e_evaluator import EndToEndEvaluator

evaluator = EndToEndEvaluator(voice_assistant)
metrics = evaluator.evaluate_batch(scenarios)
```

**Metrics**: Task success rate, average turns to completion, error recovery rate

## Test Datasets

The framework includes comprehensive test datasets:

- **intent_test_data.json** - 100+ labeled queries for intent classification
- **reservation_scenarios.json** - 30+ E2E reservation scenarios
- **menu_queries.json** - 40+ menu information queries with RAG test cases
- **general_queries.json** - 30+ general inquiry test cases

## Report Formats

The framework generates reports in multiple formats:

1. **Text Report** - Human-readable console output
2. **JSON Report** - Structured data for programmatic analysis

Reports include:
- Per-component metrics
- Overall system health indicators
- Identified weak points
- Actionable recommendations

## Example Output

```
======================================================================
EVALUATION REPORT
======================================================================
Generated: 2024-12-21T10:30:00

INTENT CLASSIFICATION
----------------------------------------------------------------------
Accuracy: 94.00%
Macro F1: 0.9300
Weakest class: 'order' (F1=0.89)

AGENT PERFORMANCE
----------------------------------------------------------------------
Reservation: 87% task success, 92% param extraction
General: 95% success rate (includes menu queries)

RAG RETRIEVAL
----------------------------------------------------------------------
MRR: 0.8400
Precision@3: 0.7800
Precision@5: 0.8200

Ragas Metrics:
  Answer Relevancy: 0.850
  Faithfulness: 0.920
  Context Precision: 0.810
  Context Recall: 0.760
  Average Score: 0.835

RECOMMENDATIONS
----------------------------------------------------------------------
1. Intent class 'order' has low F1-score (0.89). Add more examples for this class.
2. RAG Precision@3 is 0.78. Review document chunking strategy.
...
```

## Dependencies

- numpy>=1.24.0 (for metric computations)
- ragas>=0.1.0 (optional, for comprehensive RAG evaluation - install with `pip install ragas`)
- All standard Voice Assistant dependencies

**Note**: Ragas is optional. If not installed, traditional RAG metrics (MRR, Precision@K) will still work, but Ragas-specific metrics will be skipped.

## Usage Notes

- Set `is_offline=True` to use Ollama for evaluations (slower but no API costs)
- RAG evaluation requires ChromaDB connection (configured via .env)
- E2E evaluation resets conversation history between scenarios

