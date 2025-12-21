import os
import base64
import chromadb
from chromadb.config import Settings

from dotenv import load_dotenv
load_dotenv()

try:
    headers = {}
    chroma_user = os.getenv("CHROMA_USER")
    chroma_password = os.getenv("CHROMA_PASSWORD")
    
    if chroma_user and chroma_password:
        credentials = base64.b64encode(f"{chroma_user}:{chroma_password}".encode()).decode()
        headers["Authorization"] = f"Basic {credentials}"

    client = chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST"),
        port=int(os.getenv("CHROMA_PORT")),
        headers=headers
    )

    client.heartbeat()
    collection = client.get_or_create_collection("test_connection")

    print("Collection créée :", collection.name)
    print("Collections :", [c.name for c in client.list_collections()])
    print("Connexion à ChromaDB réussie")

except Exception as e:
    print("Échec de connexion à ChromaDB")
    print(e)