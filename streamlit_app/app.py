"""
Restaurant Analytics Dashboard - Main Page
============================================
Application Streamlit pour l'analyse des données du restaurant
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Ajouter le chemin parent pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration de la page
st.set_page_config(
    page_title="Restaurant Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #FF6B6B;
        font-size: 3em;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .subtitle {
        text-align: center;
        color: #4ECDC4;
        font-size: 1.5em;
        margin-bottom: 30px;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Titre principal
st.markdown('<h1 class="main-title">Restaurant Analytics Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Analyse complète des données de votre restaurant</p>', unsafe_allow_html=True)

# Introduction
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Visualisation")
    st.info("""
    - Clients
    - Menu & Produits
    - Tables
    - Réservations
    - Commandes
    """)

with col2:
    st.markdown("### Statistiques")
    st.success("""
    - KPIs métier
    - Analyses CA
    - Tendances
    - Top produits
    - Taux d'occupation
    """)

with col3:
    st.markdown("### Fonctionnalités")
    st.warning("""
    - Filtres avancés
    - Export CSV
    - Graphiques interactifs
    - Mise à jour temps réel
    """)

st.markdown("---")

# Instructions
st.markdown("### Comment utiliser l'application")

st.markdown("""
1. **Navigation** : Utilisez la barre latérale pour accéder aux différentes pages
2. **Visualisation** : Consultez les données de chaque table avec des filtres
3. **Statistiques** : Analysez les KPIs et tendances dans la page Statistics
4. **Export** : Téléchargez les données au format CSV si nécessaire
""")

st.markdown("---")

# Statut de la connexion DB
st.markdown("### Statut de la connexion")

try:
    from src.database.db_config import test_connection
    
    if test_connection():
        st.success("Connexion à la base de données établie")
    else:
        st.error("Impossible de se connecter à la base de données")
        st.info("Vérifiez votre fichier .env et que PostgreSQL est en cours d'exécution")
except Exception as e:
    st.error(f"Erreur de connexion : {str(e)}")
    st.info("Vérifiez votre configuration de base de données")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Restaurant Analytics Dashboard v1.0 | Powered by Streamlit & SQLAlchemy</p>
</div>
""", unsafe_allow_html=True)
