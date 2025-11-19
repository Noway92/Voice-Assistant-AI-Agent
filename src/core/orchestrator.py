"""
Orchestrator with Sub-Agents
Simple routing approach - cleaner and more maintainable
"""

from langchain_ollama import OllamaLLM
import sys
import os

# Add parent directory to path to import agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.general_inqueries_agent import GeneralInqueriesAgent
from agents.order_handling_agent import OrderHandlingAgent
from agents.table_reservation_agent import TableReservationAgent
from agents.menu_information_agent import MenuInformationAgent


class Orchestrator:
    """
    Simple orchestrator that routes requests to specialized sub-agents.
    No complex ReAct pattern - just smart routing.
    """
    
    def __init__(self, model_name="llama3"):
        self.llm = OllamaLLM(model=model_name, temperature=0)
        
        # Initialize all sub-agents
        self.general_agent = GeneralInqueriesAgent()
        self.order_agent = OrderHandlingAgent()
        self.reservation_agent = TableReservationAgent()
        self.menu_agent = MenuInformationAgent()
        
    def _classify_intent(self, user_input: str) -> str:
        """
        Classify user intent using the LLM.
        Returns: 'general', 'order', 'reservation', or 'menu'
        """
        prompt = f"""You are a classifier for a restaurant. Analyze the customer's request and determine the category.

            Available categories:
            - general: General questions (opening hours, location, contact, special offers)
            - order: Food orders (placing an order, modifying an order, canceling, order status)
            - reservation: Table reservations (book, modify, cancel, availability)
            - menu: Specific questions about the menu (ingredients, allergens, prices, dish promotions)

            Customer request: {user_input}

            Respond ONLY with a single word from: reservation"""

            #Respond ONLY with a single word from: reservation : general, order, reservation, menu
        try:
            response = self.llm.invoke(prompt).strip().lower()
            
            # Extract the category from the response
            if "general" in response:
                return "general"
            elif "order" in response:
                return "order"
            elif "reservation" in response:
                return "reservation"
            elif "menu" in response:
                return "menu"
            else:
                # Default to general if unclear
                return "general"
                
        except Exception as e:
            print(f"Classification error: {e}")
            return "general"  # Default fallback
    
    def process_request(self, user_input: str) -> str:
        """
        Process user request by routing to the appropriate sub-agent.
        
        Args:
            user_input: The user's question or request
            
        Returns:
            The response from the appropriate sub-agent
        """
        try:
            # Step 1: Classify the intent
            intent = self._classify_intent(user_input)
            print(f"[Orchestrator] Classified intent: {intent}")
            
            # Step 2: Route to the appropriate sub-agent
            if intent == "general":
                response = self.general_agent.process(user_input)
            elif intent == "order":
                response = self.order_agent.process(user_input)
            elif intent == "reservation":
                response = self.reservation_agent.process(user_input)
            elif intent == "menu":
                response = self.menu_agent.process(user_input)
            else:
                response = "I am sorry, I didn't understand your question"
            
            return response
            
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"


def orchestrator(user_input: str) -> str:
    """
    Main orchestrator function.
    
    Args:
        user_input: The user's question or request
        
    Returns:
        The response from the appropriate sub-agent
    """
    orch = Orchestrator()
    return orch.process_request(user_input)


if __name__ == "__main__":
    # Test the orchestrator
    orchestrator_instance = Orchestrator()
    
    test_queries = [
        "Can I book a table for 4 people tomorrow evening at 7 PM?",
    ]
    
    print("Testing Orchestrator with Sub-Agents\n" + "="*50)
    for query in test_queries:
        print(f"\n[User] {query}")
        response = orchestrator_instance.process_request(query)
        print(f"[Assistant] {response}")
        print("-"*50)