from langchain_ollama import OllamaLLM
from openai import OpenAI
import os

def llm_offline(input_text) :
    print("Offline: ")
    # Fontionnelle mais très long
    llm = OllamaLLM(model="mistral")

    # Faire une requête simple
    response = llm.invoke(input_text)
    print(response)


llm_offline("Bonjour, tu vas bien ?")

def llm_online(input_text: str, client: OpenAI = None):
    print("Online: ")
    if client is None:
        client = OpenAI(api_key=os.environ["API_KEY_OPENAI"])
    
    response = client.responses.create(model="gpt-5",input=input_text)
    print(response.output_text)

#llm_online("Bonjour, tu vas bien ?")