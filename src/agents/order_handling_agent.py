from langchain_ollama import OllamaLLM

class OrderHandlingAgent:
    def __init__(self, model_name="llama3"):
        self.llm = OllamaLLM(model=model_name, temperature=0)
    
    def process(self, user_input: str) -> str:
        """Process order handling."""
        # Votre logique ici
        response = self.llm.invoke(user_input)
        return response

# Fonction wrapper pour l'orchestrateur
def order_handling_agent(user_input: str) -> str:
    agent = OrderHandlingAgent()
    return agent.process(user_input)