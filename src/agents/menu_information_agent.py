from langchain_ollama import OllamaLLM

class MenuInformationAgent:
    def __init__(self, model_name="llama3"):
        self.llm = OllamaLLM(model=model_name, temperature=0)
    
    def process(self, user_input: str) -> str:
        """Process menu information."""
        # Votre logique ici
        response = self.llm.invoke(user_input)
        return response

# Fonction wrapper pour l'orchestrateur
def menu_information_agent(user_input: str) -> str:
    agent = MenuInformationAgent()
    return agent.process(user_input)