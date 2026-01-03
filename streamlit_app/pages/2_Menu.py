"""
Page Menu
=========
Visualisation et analyse des items du menu
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Ajouter le chemin parent
sys.path.append(str(Path(__file__).parent.parent.parent))

from streamlit_app.services.database_service import (
    get_all_menu_items,
    get_menu_stats,
    get_menu_by_category
)
from streamlit_app.utils.charts import (
    create_pie_chart,
    display_kpi_row,
    format_number
)
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="Menu - Restaurant Analytics",
    page_icon="📊",
    layout="wide"
)

# Titre
st.title("Gestion du Menu")
st.markdown("---")

# Récupération des données
try:
    menu_df = get_all_menu_items()
    menu_stats = get_menu_stats()
    
    # KPIs
    st.subheader("Indicateurs Clés")
    
    display_kpi_row([
        {
            'label': 'Total Items',
            'value': format_number(menu_stats['total'])
        },
        {
            'label': 'Disponibles',
            'value': format_number(menu_stats['available'])
        },
        {
            'label': 'Catégories',
            'value': format_number(len(menu_stats['by_category']))
        }
    ])
    
    st.markdown("---")
    
    # Deux colonnes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Items du Menu")
        
        # Filtres
        col_search, col_category = st.columns([2, 1])
        
        with col_search:
            search = st.text_input("Rechercher un item", "")
        
        with col_category:
            categories = ['Tous'] + [cat['category'] for cat in menu_stats['by_category']]
            selected_category = st.selectbox("Catégorie", categories)
        
        # Filtrer les données
        filtered_df = menu_df.copy()
        
        if search:
            filtered_df = filtered_df[
                filtered_df['Nom'].str.contains(search, case=False, na=False) |
                filtered_df['Description'].str.contains(search, case=False, na=False)
            ]
        
        if selected_category != 'Tous':
            filtered_df = filtered_df[filtered_df['Catégorie'] == selected_category]
        
        # Affichage du tableau
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        # Statistiques du filtre
        st.caption(f"Affichage de {len(filtered_df)} items sur {len(menu_df)}")
        
        # Bouton export
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger CSV",
                data=csv,
                file_name="menu.csv",
                mime="text/csv"
            )
    
    with col2:
        st.subheader("Répartition par Catégorie")
        
        # Graphique camembert
        if menu_stats['by_category']:
            category_df = pd.DataFrame(menu_stats['by_category'])
            category_df.columns = ['Catégorie', 'Nombre']
            
            chart = create_pie_chart(
                category_df,
                'Catégorie',
                'Nombre',
                'Distribution des items',
                height=300
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Aucune catégorie disponible")
    
    # Tableau récapitulatif par catégorie
    st.markdown("---")
    st.subheader("Récapitulatif par Catégorie")
    
    if menu_stats['by_category']:
        summary_df = pd.DataFrame(menu_stats['by_category'])
        summary_df.columns = ['Catégorie', 'Nombre d\'items']
        
        # Calculer le pourcentage
        summary_df['Pourcentage'] = (
            summary_df['Nombre d\'items'] / summary_df['Nombre d\'items'].sum() * 100
        ).round(1).astype(str) + '%'
        
        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Erreur lors du chargement des données : {str(e)}")
    st.info("Vérifiez que la base de données est accessible et initialisée")
