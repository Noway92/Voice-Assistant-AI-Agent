import os
import chromadb
from chromadb.config import Settings

from dotenv import load_dotenv
load_dotenv()


try:
    client = chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST"),
        port=int(os.getenv("CHROMA_PORT")),
        tenant="default_tenant",
        database="default_database"
    )

    client.heartbeat()
    collection = client.get_or_create_collection("test_connection")

    print("Collection créée :", collection.name)
    print("Collections :", [c.name for c in client.list_collections()])



    print("Connexion à ChromaDB réussie")

except Exception as e:
    print("Échec de connexion à ChromaDB")
    print(e)
