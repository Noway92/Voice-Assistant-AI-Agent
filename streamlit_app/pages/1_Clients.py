"""
Page Clients
=============
Visualisation et analyse des clients du restaurant
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Ajouter le chemin parent
sys.path.append(str(Path(__file__).parent.parent.parent))

from streamlit_app.services.database_service import (
    get_all_clients,
    get_client_stats,
    get_new_clients_by_month
)
from streamlit_app.utils.charts import (
    create_bar_chart,
    create_line_chart,
    display_kpi_row,
    format_number
)

# Configuration de la page
st.set_page_config(
    page_title="Clients - Restaurant Analytics",
    page_icon="�",
    layout="wide"
)

# Titre
st.title("Gestion des Clients")
st.markdown("---")

# Récupération des données
try:
    clients_df = get_all_clients()
    client_stats = get_client_stats()
    new_clients_df = get_new_clients_by_month()
    
    # KPIs
    st.subheader("Indicateurs Clés")
    
    display_kpi_row([
        {
            'label': 'Total Clients',
            'value': format_number(client_stats['total'])
        },
        {
            'label': 'Nouveaux ce mois',
            'value': format_number(client_stats['new_this_month'])
        },
        {
            'label': 'Taux croissance',
            'value': f"{(client_stats['new_this_month'] / max(client_stats['total'], 1) * 100):.1f}%"
        }
    ])
    
    st.markdown("---")
    
    # Deux colonnes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Liste des Clients")
        
        # Barre de recherche
        search = st.text_input("Rechercher un client", "")
        
        # Filtrer les données
        if search:
            filtered_df = clients_df[
                clients_df['Nom'].str.contains(search, case=False, na=False) |
                clients_df['Téléphone'].str.contains(search, case=False, na=False)
            ]
        else:
            filtered_df = clients_df
        
        # Affichage du tableau
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        # Bouton export
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger CSV",
                data=csv,
                file_name="clients.csv",
                mime="text/csv"
            )
    
    with col2:
        st.subheader("Top Clients")
        st.markdown("*Par nombre de réservations*")
        
        if client_stats['top_clients']:
            for idx, client in enumerate(client_stats['top_clients'], 1):
                st.markdown(f"""
                <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin: 5px 0;'>
                    <b>{idx}. {client['name']}</b><br>
                    {client['reservations']} réservations
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aucune donnée disponible")
    
    # Graphique évolution
    st.markdown("---")
    st.subheader("Évolution des Nouveaux Clients")
    
    if not new_clients_df.empty:
        # Créer une colonne de période lisible
        new_clients_df['Période'] = new_clients_df.apply(
            lambda x: f"{int(x['Année'])}-{int(x['Mois']):02d}",
            axis=1
        )
        
        chart = create_line_chart(
            new_clients_df,
            'Période',
            'Nouveaux clients',
            'Nouveaux clients par mois',
            color='#4ECDC4',
            height=300
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Aucune donnée d'évolution disponible")
    
    # Statistiques détaillées
    st.markdown("---")
    st.subheader("Statistiques Détaillées")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Clients actifs",
            format_number(client_stats['total']),
            help="Nombre total de clients dans la base"
        )
    
    with col2:
        if client_stats['top_clients']:
            top_client_reservations = client_stats['top_clients'][0]['reservations']
            st.metric(
                "Record réservations",
                format_number(top_client_reservations),
                help="Plus grand nombre de réservations par un client"
            )
        else:
            st.metric("Record réservations", "0")
    
    with col3:
        avg_reservations = (
            sum(c['reservations'] for c in client_stats['top_clients']) / 
            len(client_stats['top_clients'])
        ) if client_stats['top_clients'] else 0
        
        st.metric(
            "Moy. top clients",
            f"{avg_reservations:.1f}",
            help="Moyenne de réservations des top clients"
        )

except Exception as e:
    st.error(f"Erreur lors du chargement des données : {str(e)}")
    st.info("Vérifiez que la base de données est accessible et initialisée")
