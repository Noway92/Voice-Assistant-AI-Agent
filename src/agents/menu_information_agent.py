import os

from langchain_ollama import OllamaLLM
from langchain.chat_models import ChatOpenAI

class MenuInformationAgent:
    def __init__(self,isOffline=True):
        if isOffline:
            self.llm = OllamaLLM(model="llama3", temperature=0)
        else:
            api_key = os.getenv("API_KEY_OPENAI")  # Lire la clé depuis les variables d'environnement
            if not api_key:
                raise ValueError("API_KEY_OPENAI not found in environment variables")
            self.llm = ChatOpenAI(model="gpt-5-mini", temperature=0, api_key=api_key)
    def process(self, user_input: str) -> str:
        """Process menu information."""
        # Votre logique ici
        response = self.llm.invoke(user_input)
        return response

# Fonction wrapper pour l'orchestrateur
def menu_information_agent(user_input: str) -> str:
    agent = MenuInformationAgent()
    return agent.process(user_input)