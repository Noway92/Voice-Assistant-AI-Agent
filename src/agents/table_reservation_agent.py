from langchain_ollama import OllamaLLM

class TableReservationAgent:
    def __init__(self, model_name="llama3"):
        self.llm = OllamaLLM(model=model_name, temperature=0)
    
    def process(self, user_input: str) -> str:
        """Process table reservation."""
        # Votre logique ici
        response = self.llm.invoke(user_input)
        return response

# Fonction wrapper pour l'orchestrateur
def table_reservation_agent(user_input: str) -> str:
    agent = TableReservationAgent()
    return agent.process(user_input)