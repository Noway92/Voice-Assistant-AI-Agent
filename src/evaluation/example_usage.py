"""
Example usage of the evaluation framework.

This script demonstrates how to run evaluations on the Voice Assistant system.
"""

import sys
from pathlib import Path

# Add parent directories to path (project root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.append(str(project_root / "src"))  # Also add src for module imports

from main import VoiceAssistant
from core.orchestrator import Orchestrator
from rag.rag import EmbeddingsManager
from evaluation.runner import EvaluationRunner
from evaluation.report import ReportGenerator


def main():
    """Example evaluation run."""
    
    # Configuration
    is_offline = False  # Set to True to use Ollama instead of OpenAI
    UsePhone = False
    use_custom_xtts = False
    
    print("Initializing Voice Assistant components...")
    
    # Initialize components
    try:
        # Initialize orchestrator (for intent classification and agents)
        orchestrator = Orchestrator(isOffline=is_offline)
        
        # Initialize voice assistant (for E2E tests)
        voice_assistant = VoiceAssistant(isOffline=is_offline,UsePhone=UsePhone,use_custom_xtts=use_custom_xtts)
        
        # Initialize embeddings manager (for RAG evaluation)
        # Note: Requires ChromaDB connection and .env configuration
        try:
            embeddings_manager = EmbeddingsManager(
                json_path="../rag/general-inqueries.json",
                collection_name="restaurant_knowledge"
            )
        except Exception as e:
            print(f"Warning: Could not initialize EmbeddingsManager: {e}")
            print("RAG evaluation will be skipped.")
            embeddings_manager = None

        # Create evaluation runner
        runner = EvaluationRunner(
            orchestrator=orchestrator,
            voice_assistant=voice_assistant,
            embeddings_manager=embeddings_manager,
            is_offline=is_offline
        )
        
        # Run full evaluation
        print("\n" + "=" * 70)
        print("Running Full Evaluation Suite")
        print("=" * 70)
        
        
        results = runner.run_full_evaluation(
            include_agents=True,
            include_rag=(embeddings_manager is not None),
            include_e2e=True
        )
        
        # Generate report
        print("\nGenerating evaluation report...")
        report_generator = ReportGenerator(results)
        
        # Print text report to console
        text_report = report_generator.generate_text_report()
        print("\n" + text_report)
        
        # Save reports to files
        report_generator.save_report("evaluation_reports")
        
        print("\nEvaluation complete!")
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

