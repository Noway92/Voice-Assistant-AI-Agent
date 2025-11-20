import os

from langchain_ollama import OllamaLLM
from langchain.chat_models import ChatOpenAI

class GeneralInqueriesAgent:
    def __init__(self,isOffline=True, db_config=None):
        if isOffline:
            self.llm = OllamaLLM(model="llama3", temperature=0)
        else:
            api_key = os.getenv("API_KEY_OPENAI")  # Lire la clé depuis les variables d'environnement
            if not api_key:
                raise ValueError("API_KEY_OPENAI not found in environment variables")
            self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)
        self.db_config = db_config or {
            "host": "localhost",
            "database": "restaurant_db",
            "user": "your_user",
            "password": "your_password",
            "port": 5432
        }
    
    def _query_database(self, query_type: str) -> str:
        """Query PostgreSQL database for restaurant info."""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Requête simple pour récupérer les infos
            sql = """
                SELECT key, value 
                FROM restaurant_info 
                WHERE key IN ('opening_hours', 'location', 'phone', 'email', 'special_offers')
            """
            
            cursor.execute(sql)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            if results:
                info = "\n".join([f"{row['key']}: {row['value']}" for row in results])
                return info
            else:
                return "No information available."
                
        except Exception as e:
            return f"Database error: {str(e)}"
    
    def process(self, user_input: str) -> str:
        """Process general inquiries."""
        try:
            # 1. Récupérer les infos de la BDD
            db_info = self._query_database("general_info")
            
            # 2. Créer un prompt avec les infos de la BDD
            prompt = f"""Tu es un assistant pour un restaurant. Réponds à la question du client en utilisant les informations suivantes :
                    Informations du restaurant :
                    {db_info}

                    Question du client : {user_input}

                    Réponds de manière claire et professionnelle."""
            
            # 3. Envoyer au LLM
            response = self.llm.invoke(prompt)
            return response
            
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"

# Fonction wrapper pour l'orchestrateur
def general_inqueries_agent(user_input: str) -> str:
    agent = GeneralInqueriesAgent()
    return agent.process(user_input)