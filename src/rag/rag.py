"""
Script de gestion des embeddings ChromaDB.
Crée et met à jour les embeddings à partir de general-inqueries.json et PostgreSQL
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import os
from dotenv import load_dotenv

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sqlalchemy.orm import Session
from database.database import MenuItem
from database.db_config import SessionLocal

load_dotenv()


class EmbeddingsManager:
    """Gestionnaire simplifié des embeddings ChromaDB."""
    
    def __init__(
        self,
        json_path: str = "general-inqueries.json",
        collection_name: str = "restaurant_knowledge",
    ):
        """Initialise le gestionnaire."""
        self.json_path = Path(json_path)
        self.collection_name = collection_name
        
        # Configuration OpenAI
        self.api_key = os.getenv("API_KEY_OPENAI")
        
        # Configuration ChromaDB depuis .env
        chroma_host = os.getenv("CHROMA_HOST")
        chroma_port = int(os.getenv("CHROMA_PORT"))
        chroma_user = os.getenv("CHROMA_USER")
        chroma_password = os.getenv("CHROMA_PASSWORD")
        
        # Connexion ChromaDB
        print(f"Connecting to ChromaDB ({chroma_host}:{chroma_port})...")

        try:
            # ChromaDB 0.4.22 : HttpClient accepte host et port uniquement
            self.client = chromadb.HttpClient(
                host=os.getenv("CHROMA_HOST"),
                port=int(os.getenv("CHROMA_PORT")),
                tenant="default_tenant",
                database="default_database"
            )
            
            if chroma_user and chroma_password:
                print(f"Credentials configured: {chroma_user}")
            else:
                print("No authentication configured")
            
            print("Connected to ChromaDB successfully")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to ChromaDB at {chroma_host}:{chroma_port}. Is the server running? Error: {e}")
        
        # Fonction d'embedding OpenAI
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.api_key,
            model_name="text-embedding-3-small"
        )
        
    
    def _load_json(self) -> Dict[str, Any]:
        """Charge le fichier JSON."""
        if not self.json_path.exists():
            raise FileNotFoundError(f"File not found: {self.json_path}")
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _dict_to_text(self, data: Dict, indent: int = 0) -> str:
        """Convertit un dict en texte lisible (fonction générique)."""
        lines = []
        for key, value in data.items():
            if value is None or (isinstance(value, (list, dict)) and not value):
                continue
            
            # Formater la clé (underscores → espaces, capitalize)
            formatted_key = key.replace('_', ' ').title()
            
            if isinstance(value, bool):
                # Convertir booléen en texte
                value = "Yes" if value else "No"
                lines.append(f"{formatted_key}: {value}")
            
            elif isinstance(value, (int, float, str)):
                # Valeurs simples
                lines.append(f"{formatted_key}: {value}")
            
            elif isinstance(value, list):
                # Listes
                if value and isinstance(value[0], str):
                    lines.append(f"{formatted_key}: {', '.join(value)}")
                else:
                    lines.append(f"{formatted_key}: {value}")
            
            elif isinstance(value, dict):
                # Dicts imbriqués (récursif)
                lines.append(f"{formatted_key}:")
                nested_text = self._dict_to_text(value, indent + 1)
                for line in nested_text.split('\n'):
                    if line.strip():
                        lines.append(f"  {line}")
        
        return '\n'.join(lines)
    
    def _prepare_documents(self) -> List[Dict[str, Any]]:
        """Transforme le JSON en documents structurés."""
        data = self._load_json()
        documents = []
        general = data.get('general_inquiries', {})
        
        # Mapping de sections → ID et type
        sections = {
            'location': ('location', 'location'),
            'opening_hours': ('opening_hours', 'opening_hours'),
            'contact': ('contact', 'contact'),
            'reservation_policy': ('reservation', 'reservation_policy'),
            'delivery_and_takeaway': ('delivery', 'delivery'),
            'payment_methods': ('payment', 'payment'),
            'atmosphere': ('atmosphere', 'atmosphere'),
            'accessibility': ('accessibility', 'accessibility'),
            'dietary_restrictions': ('dietary', 'dietary'),
            'allergies_handling': ('allergies', 'allergies'),
        }
        
        # Traiter les sections simples
        for key, (doc_id, doc_type) in sections.items():
            if key in general:
                data_section = general[key]
                
                # Cas spécial: dietary_restrictions est une liste
                if key == 'dietary_restrictions' and isinstance(data_section, list):
                    text = f"Available dietary options: {', '.join(data_section)}"
                else:
                    # Convertir en texte lisible
                    text = self._dict_to_text(data_section)
                
                documents.append({
                    'id': doc_id,
                    'text': text,
                    'metadata': {'type': doc_type, 'source': 'general_inquiries'}
                })
        
        # FAQs (liste)
        if 'faqs' in general:
            for idx, faq in enumerate(general['faqs']):
                question = faq.get('question', '')
                answer = faq.get('answer', '')
                text = f"Q: {question}\nA: {answer}"
                
                documents.append({
                    'id': f'faq_{idx}',
                    'text': text,
                    'metadata': {
                        'type': 'faq',
                        'source': 'general_inquiries',
                        'question': question
                    }
                })
        
        # Special offers (liste)
        if 'special_offers' in general:
            for idx, offer in enumerate(general['special_offers']):
                text = self._dict_to_text(offer)
                
                documents.append({
                    'id': f'offer_{idx}',
                    'text': text,
                    'metadata': {
                        'type': 'special_offer',
                        'source': 'general_inquiries',
                        'title': offer.get('title', '')
                    }
                })
        
        return documents
    
    def _load_menu_items(self) -> List[Dict[str, Any]]:
        """Charge les items du menu depuis PostgreSQL."""
        documents = []
        
        try:
            db: Session = SessionLocal()
            menu_items = db.query(MenuItem).all()
            
            for item in menu_items:
                text = f"Dish: {item.name}. "
                text += f"Category: {item.category}. "
                
                if item.description:
                    text += f"Description: {item.description}. "
                
                text += f"Price: ${item.price}. "
                
                if item.ingredients:
                    text += f"Ingredients: {item.ingredients}. "
                
                if item.allergens:
                    text += f"Allergens: {item.allergens}. "
                
                text += f"Available: {'Yes' if item.is_available else 'No'}"
                
                documents.append({
                    'id': f'menu_item_{item.id}',
                    'text': text,
                    'metadata': {
                        'type': 'menu_item',
                        'source': 'database',
                        'item_id': item.id,
                        'category': item.category,
                        'name': item.name,
                        'price': item.price,
                        'is_available': item.is_available
                    }
                })
            
            db.close()
            
        except Exception as e:
            print(f"Error loading menu items: {e}")
        
        return documents
    
    def create_embeddings(self, force_update: bool = False) -> Dict[str, int]:
        """Crée les embeddings."""
        if force_update:
            print("Deleting existing collection...")
            try:
                self.client.delete_collection(self.collection_name)
            except:
                pass
            
            collection=self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Restaurant knowledge base"}
            )
        
        print("Preparing documents...")
        general_docs = self._prepare_documents()
        
        print("Loading menu from PostgreSQL...")
        menu_docs = self._load_menu_items()
        
        all_docs = general_docs + menu_docs
        
        if not all_docs:
            print("No documents to process!")
            return {'total': 0, 'general': 0, 'menu': 0}
        
        ids = [doc['id'] for doc in all_docs]
        texts = [doc['text'] for doc in all_docs]
        metadatas = [doc['metadata'] for doc in all_docs]
        
        # Remove old documents if present
        try:
            self.collection.delete(ids=ids)
        except:
            pass
        
        print(f"Creating embeddings ({len(all_docs)} documents)")
        print(f"   • General documents: {len(general_docs)}")
        print(f"   • Menu items: {len(menu_docs)}")
        
        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        
        stats = self.get_stats()
        print(f"\nEmbeddings created successfully!")
        print(f"   • Total documents: {stats['total']}")
        print(f"   • By type: {stats['by_type']}")
        
        return {
            'total': stats['total'],
            'general': len(general_docs),
            'menu': len(menu_docs)
        }
    
    def update_embeddings(self) -> Dict[str, int]:
        """Met à jour les embeddings SANS supprimer les existants."""
        print("Updating embeddings (non-destructif)...")
        try:
            # Récupérer la collection à nouveau (en cas de perte de référence)
            collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            # Juste ajouter les nouveaux documents
            general_docs = self._prepare_documents()
            menu_docs = self._load_menu_items()
            all_docs = general_docs + menu_docs
            
            # Ajouter/mettre à jour sans supprimer
            collection.add(
                ids=[doc['id'] for doc in all_docs],
                documents=[doc['text'] for doc in all_docs],
                metadatas=[doc['metadata'] for doc in all_docs]
            )
        
            stats = self.get_stats()
            print(f"Embeddings updated!")
            return {'total': stats['total'], 'general': len(general_docs), 'menu': len(menu_docs)}
        except Exception as e:
            print(f"Erreur lors de la récupération des stats: {e}")
            return {'total': 0, 'general':0, 'menu': 0 }
    
    def get_stats(self) -> Dict[str, Any]:
        """Récupère les stats de la collection."""

        try:
            # Récupérer la collection à nouveau (en cas de perte de référence)
            collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            
            total = collection.count()
            
            type_counts = {}
            try:
                sample = collection.get(limit=1000)
                if sample['metadatas']:
                    for meta in sample['metadatas']:
                        doc_type = meta.get('type', 'unknown')
                        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            except:
                pass
            
            return {
                'total': total,
                'by_type': type_counts
            }
        except Exception as e:
            print(f"Erreur lors de la récupération des stats: {e}")
            return {'total': 0, 'by_type': {}}
    
    def search(self, query: str, n_results: int = 5, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Effectue une recherche."""
        where_filter = None
        if filter_type:
            where_filter = {"type": filter_type}
        
        try:
            # Récupérer la collection à nouveau (en cas de perte de référence)
            collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
        
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            formatted = []
            if results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    formatted.append({
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i],
                        'score': 1 - results['distances'][0][i]
                    })
            
            return formatted
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return f"Erreur lors de la recherche: {e}"


def print_menu():
    """Affiche le menu principal."""
    print("\n" + "=" * 70)
    print("EMBEDDINGS MANAGER - CHROMADB")
    print("=" * 70)
    print("\n📋 Choisissez une option:\n")
    print("1 CREATE - Créer tous les embeddings (base vierge)")
    print("2 UPDATE - Mettre à jour les embeddings")
    print("3 SEARCH - Rechercher dans la base")
    print("4 STATS - Afficher les statistiques")
    print("5 EXIT  - Quitter\n")
    print("=" * 70)


def search_mode(manager: EmbeddingsManager):
    """Mode recherche interactif."""
    print("\nMODE RECHERCHE")
    print("-" * 70)
    
    while True:
        print("\nOptions:")
        print("  1. Recherche générale")
        print("  2. Filtrer par type")
        print("  3. Retour au menu principal")
        
        choice = input("\nChoisissez (1-3): ").strip()
        
        if choice == "1":
            query = input("\nEntrez votre question: ").strip()
            if query:
                n_results = input("Nombre de résultats (défaut: 5): ").strip()
                n_results = int(n_results) if n_results.isdigit() else 5
                
                print(f"\nRecherche: '{query}'")
                results = manager.search(query, n_results=n_results)
                
                if results:
                    for i, result in enumerate(results, 1):
                        print(f"\nRésultat {i} [{result['score']:.0%}]")
                        print(f"Type: {result['metadata'].get('type', 'N/A')}")
                        print(f"Texte: {result['text']}...")
                else:
                    print("Aucun résultat trouvé")
        
        elif choice == "2":
            print("\nTypes disponibles:")
            print("  • location, opening_hours, contact, reservation_policy")
            print("  • delivery, payment, atmosphere, accessibility")
            print("  • dietary, allergies, faq, special_offer, menu_item")
            
            filter_type = input("\nEntrez le type: ").strip()
            query = input("Entrez votre question: ").strip()
            
            if query and filter_type:
                n_results = input("Nombre de résultats (défaut: 5): ").strip()
                n_results = int(n_results) if n_results.isdigit() else 5
                
                print(f"\nRecherche: '{query}' (filtre: {filter_type})")
                results = manager.search(query, n_results=n_results, filter_type=filter_type)
                
                if results:
                    for i, result in enumerate(results, 1):
                        print(f"\nRésultat {i} [{result['score']:.0%}]")
                        print(f"Texte: {result['text']}...")
                else:
                    print("Aucun résultat trouvé")
        
        elif choice == "3":
            break
        
        else:
            print("Choix invalide")


def main():
    """Script principal avec menu interactif."""
    try:
        # Initialiser le manager
        print("Initialisation du manager...")
        manager = EmbeddingsManager(
            json_path="general-inqueries.json",
            collection_name="restaurant_knowledge",
        )
        
        while True:
            print_menu()
            choice = input("Votre choix (1-5): ").strip()
            
            if choice == "1":
                print("\n" + "=" * 70)
                print("CRÉATION DES EMBEDDINGS")
                print("=" * 70)
                confirm = input("Cela supprimera la base existante. Continuer? (y/n): ").strip().lower()
                if confirm == 'y':
                    manager.create_embeddings(force_update=True)
                else:
                    print("Opération annulée")
            
            elif choice == "2":
                print("\n" + "=" * 70)
                print("MISE À JOUR DES EMBEDDINGS")
                print("=" * 70)
                manager.update_embeddings()
            
            elif choice == "3":
                search_mode(manager)
            
            elif choice == "4":
                stats = manager.get_stats()
                print("\n" + "=" * 70)
                print("STATISTIQUES")
                print("=" * 70)
                print(f"Total de documents: {stats['total']}")
                print(f"Par type:")
                for doc_type, count in stats['by_type'].items():
                    print(f"   • {doc_type}: {count}")
            
            elif choice == "5":
                print("\nAu revoir!")
                break
            
            else:
                print("\nChoix invalide. Veuillez entrer 1-5.")
    
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()