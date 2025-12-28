"""
Test script for the General Inquiries Agent with RAG.
This script tests the agent independently to verify functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.general_inqueries_agent import GeneralInqueriesAgent


def test_general_agent():
    """Test the general inquiries agent with various questions."""
    print("=" * 70)
    print("TESTING GENERAL INQUIRIES AGENT (RAG)")
    print("=" * 70)

    # Initialize agent (using OpenAI for better results)
    print("\nInitializing agent...")
    agent = GeneralInqueriesAgent(isOffline=False)
    print("Agent initialized successfully!\n")

    # Test questions
    test_questions = [
        "What are your opening hours?",
        "Where is the restaurant located?",
        "Do you accept pets?",
        "What special offers do you have?",
        "Do you have vegetarian options?",
        "Can I make a reservation for a birthday party?",
        "What are your contact details?",
        "Do you offer delivery?",
        "Is the restaurant wheelchair accessible?",
        "What payment methods do you accept?"
    ]

    print("Testing with various questions:\n")
    print("-" * 70)

    for i, question in enumerate(test_questions, 1):
        print(f"\n[Question {i}] {question}")
        try:
            response = agent.process(question)
            print(f"[Response] {response}")
        except Exception as e:
            print(f"[ERROR] {str(e)}")
        print("-" * 70)

    print("\n" + "=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)


def test_interactive():
    """Interactive testing mode."""
    print("=" * 70)
    print("INTERACTIVE MODE - GENERAL INQUIRIES AGENT")
    print("=" * 70)
    print("Type your questions. Enter 'quit' to exit.\n")

    agent = GeneralInqueriesAgent(isOffline=False)

    while True:
        question = input("\n[You] ").strip()

        if question.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break

        if not question:
            continue

        try:
            response = agent.process(question)
            print(f"[Agent] {response}")
        except Exception as e:
            print(f"[ERROR] {str(e)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test the General Inquiries Agent")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )

    args = parser.parse_args()

    if args.interactive:
        test_interactive()
    else:
        test_general_agent()
