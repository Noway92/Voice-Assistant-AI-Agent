"""
Orchestrator with Sub-Agents
Simple routing approach - cleaner and more maintainable
"""

from langchain_ollama import OllamaLLM
from langchain.chat_models import ChatOpenAI
import sys
import os
from typing import List, Dict, Optional

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
    
    def __init__(self,isOffline=True):
        if isOffline:
            self.llm = OllamaLLM(model="llama3", temperature=0)
        else:
            api_key = os.getenv("API_KEY_OPENAI")  # Lire la clé depuis les variables d'environnement
            if not api_key:
                raise ValueError("API_KEY_OPENAI not found in environment variables")
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

        
        # Initialize all sub-agents
        self.general_agent = GeneralInqueriesAgent(isOffline)
        self.order_agent = OrderHandlingAgent(isOffline)
        self.reservation_agent = TableReservationAgent(isOffline)
        self.menu_agent = MenuInformationAgent(isOffline)
        
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

            Respond ONLY with a single word from: general, order, reservation, menu"""
        try:
            llm_response = self.llm.invoke(prompt)
            
            # Handle different response types (AIMessage (Online) vs string (Offline))
            if hasattr(llm_response, 'content'):
                response = llm_response.content.strip().lower()
            else:
                response = str(llm_response).strip().lower()
            
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
    
    def _build_context(self, current_input: str, history: List[Dict]) -> str:
        """
        Build enriched context by combining conversation history with current input.
        
        Args:
            current_input: The current user's question or request
            history: List of previous conversation messages with 'role' and 'content' keys
            
        Returns:
            A formatted string containing recent conversation context and current request.
            If no history exists, returns the current input unchanged.
        """
        if not history or len(history) == 0:
            return current_input
        
        # Take last 3 exchanges (6 messages) for context
        recent_history = history[-6:] if len(history) > 6 else history
        
        context_parts = ["Previous conversation context:"]
        for msg in recent_history:
            role = "Customer" if msg["role"] == "user" else "Assistant"
            context_parts.append(f"{role}: {msg['content']}")
        
        context_parts.append(f"\nCurrent customer request: {current_input}")
        
        return "\n".join(context_parts)
    
    def process_request(self, user_input: str, conversation_history: Optional[List[Dict]] = []) -> str:
        """
        Process user request by routing to the appropriate sub-agent.
        
        Args:
            user_input: The user's question or request
            conversation_history: Optional conversation history for context 
            
        Returns:
            The response from the appropriate sub-agent
        """
        try:
            # Step 1: Build context with history
            if len(conversation_history) != 0:
                user_input = self._build_context(user_input, conversation_history)
                print(f"[Orchestrator] Use context for answering")

            # Step 2: Classify the intent (using context if available)
            intent = self._classify_intent(user_input)
            print(f"[Orchestrator] Classified intent: {intent}")
            
            # Step 3: Route to the appropriate sub-agent with context
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
    orch = Orchestrator(False)
    return orch.process_request(user_input)


if __name__ == "__main__":
    # Test the orchestrator
    orchestrator_instance = Orchestrator(False)
    
    test_queries = [
        "Can I book a table for 2 people tomorrow evening at 7 PM? My name is Noé and my Phone is +33769624396",
        #"Can you cancel my reservation for the 2025-11-22 at 7 PM, my name is Noé",
        #"Can you tell me if you got places for 2025-11-22 ",
    ]
    
    print("Testing Orchestrator with Sub-Agents\n" + "="*50)
    for query in test_queries:
        print(f"\n[User] {query}")
        response = orchestrator_instance.process_request(query)
        print(f"[Assistant] {response}")
        print("-"*50)