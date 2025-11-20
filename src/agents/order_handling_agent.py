import os

from langchain_ollama import OllamaLLM
from langchain.chat_models import ChatOpenAI

class OrderHandlingAgent:
    def __init__(self,isOffline=True):
        if isOffline:
            self.llm = OllamaLLM(model="llama3", temperature=0)
        else:
            api_key = os.getenv("API_KEY_OPENAI")  # Lire la clé depuis les variables d'environnement
            if not api_key:
                raise ValueError("API_KEY_OPENAI not found in environment variables")
            self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)
    
    def process(self, user_input: str) -> str:
        """Process order handling."""
        # Votre logique ici
        response = self.llm.invoke(user_input)
        return response

# Fonction wrapper pour l'orchestrateur
def order_handling_agent(user_input: str) -> str:
    agent = OrderHandlingAgent()
    return agent.process(user_input)