"""
Page Tables
===========
Visualisation et analyse des tables du restaurant
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Ajouter le chemin parent
sys.path.append(str(Path(__file__).parent.parent.parent))

from streamlit_app.services.database_service import (
    get_all_tables,
    get_table_stats
)
from streamlit_app.utils.charts import (
    create_bar_chart,
    display_kpi_row,
    format_number
)
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="Tables - Restaurant Analytics",
    page_icon="📊",
    layout="wide"
)

# Titre
st.title("Gestion des Tables")
st.markdown("---")

# Récupération des données
try:
    tables_df = get_all_tables()
    table_stats = get_table_stats()
    
    # KPIs
    st.subheader("Indicateurs Clés")
    
    display_kpi_row([
        {
            'label': 'Total Tables',
            'value': format_number(table_stats['total'])
        },
        {
            'label': 'Capacité Totale',
            'value': format_number(table_stats['total_capacity'])
        },
        {
            'label': 'Capacité Moyenne',
            'value': f"{(table_stats['total_capacity'] / max(table_stats['total'], 1)):.1f}"
        }
    ])
    
    st.markdown("---")
    
    # Deux colonnes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Liste des Tables")
        
        # Filtres
        col_search, col_location = st.columns([2, 1])
        
        with col_search:
            search = st.text_input("Rechercher par numéro", "")
        
        with col_location:
            locations = ['Tous'] + list(tables_df['Emplacement'].unique()) if not tables_df.empty else ['Tous']
            selected_location = st.selectbox("Emplacement", locations)
        
        # Filtrer les données
        filtered_df = tables_df.copy()
        
        if search:
            try:
                search_num = int(search)
                filtered_df = filtered_df[filtered_df['Numéro'] == search_num]
            except ValueError:
                st.warning("Veuillez entrer un numéro valide")
        
        if selected_location != 'Tous':
            filtered_df = filtered_df[filtered_df['Emplacement'] == selected_location]
        
        # Affichage du tableau
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        # Statistiques du filtre
        st.caption(f"Affichage de {len(filtered_df)} tables sur {len(tables_df)}")
        
        # Bouton export
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger CSV",
                data=csv,
                file_name="tables.csv",
                mime="text/csv"
            )
    
    with col2:
        st.subheader("Répartition par Emplacement")
        
        # Statistiques par emplacement
        if table_stats['by_location']:
            for loc in table_stats['by_location']:
                st.markdown(f"""
                <div style='background-color: #f0f2f6; padding: 5px; border-radius: 5px; margin: 5px 0;'>
                    <h4 style='margin: 0; color: #FF6B6B;'>{loc['location'].title()}</h4>
                    <p style='margin: 5px 0;'>
                        <b>{loc['count']}</b> tables<br>
                        <b>{loc['capacity']}</b> places assises
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aucune donnée disponible")
    
    # Graphiques
    st.markdown("---")
    st.subheader("Visualisations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Nombre de tables par emplacement**")
        if table_stats['by_location']:
            location_df = pd.DataFrame(table_stats['by_location'])
            location_df.columns = ['Emplacement', 'Nombre', 'Capacité']
            
            from streamlit_app.utils.charts import create_bar_chart
            chart = create_bar_chart(
                location_df,
                'Emplacement',
                'Nombre',
                '',
                color='#4ECDC4',
                height=300
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Aucune donnée")
    
    with col2:
        st.markdown("**Capacité par emplacement**")
        if table_stats['by_location']:
            chart = create_bar_chart(
                location_df,
                'Emplacement',
                'Capacité',
                '',
                color='#FFD93D',
                height=300
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Aucune donnée")
    

except Exception as e:
    st.error(f"Erreur lors du chargement des données : {str(e)}")
    st.info("Vérifiez que la base de données est accessible et initialisée")
