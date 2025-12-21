import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Configuration de la connexion depuis les variables d'environnement
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "restaurant_db")

# Construction de l'URL de connexion
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Créer l'engine SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()

def get_db():
    """Obtenir une session de base de données."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialiser la base de données (créer toutes les tables)."""
    from .database import Client, Reservation, Table, MenuItem, Order, OrderItem
    Base.metadata.create_all(bind=engine)
    print("[SUCCESS] Tables created successfully!")

def test_connection():
    """Tester la connexion à la base de données."""
    try:
        connection = engine.connect()
        connection.close()
        print("[SUCCESS] Database connection successful!")
        return True
    except Exception as e:
        print(f"[ERROR] Database connection failed: {str(e)}")
        return False