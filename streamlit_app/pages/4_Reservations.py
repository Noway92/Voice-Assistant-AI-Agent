"""
Page Réservations
=================
Visualisation et analyse des réservations
"""

import streamlit as st
import sys
import os
from datetime import datetime, date, timedelta
from pathlib import Path

# Ajouter le chemin parent
sys.path.append(str(Path(__file__).parent.parent.parent))

from streamlit_app.services.database_service import (
    get_all_reservations,
    get_reservation_stats,
    get_reservations_by_date,
    get_reservations_by_day
)
from streamlit_app.utils.charts import (
    create_line_chart,
    create_bar_chart,
    display_kpi_row,
    format_number
)
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="Réservations - Restaurant Analytics",
    page_icon="�",
    layout="wide"
)

# Titre
st.title("Gestion des Réservations")
st.markdown("---")

# Récupération des données
try:
    reservations_df = get_all_reservations()
    reservation_stats = get_reservation_stats()
    reservations_by_day_df = get_reservations_by_day()
    
    # KPIs
    st.subheader("Indicateurs Clés")
    
    display_kpi_row([
        {
            'label': 'Total Réservations',
            'value': format_number(reservation_stats['total'])
        },
        {
            'label': 'Ce mois',
            'value': format_number(reservation_stats['this_month'])
        },
        {
            'label': 'Moy. personnes',
            'value': str(reservation_stats['avg_guests'])
        },
        {
            'label': 'Moy. jour',
            'value': str(reservations_by_day_df['Réservations'].mean())
        }
    ])
    
    st.markdown("---")
    
    # Deux colonnes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Liste des Réservations")
        
        # Filtres
        col_search, col_status, col_date = st.columns([2, 1, 1])
        
        with col_search:
            search = st.text_input("Rechercher client/téléphone", "")
        
        with col_status:
            statuses = ['Tous'] + [s['status'] for s in reservation_stats['by_status']]
            selected_status = st.selectbox("Statut", statuses)
        
        with col_date:
            date_filter = st.selectbox("Période", ["Tous", "Aujourd'hui", "Cette semaine", "Ce mois"])
        
        # Filtrer les données
        filtered_df = reservations_df.copy()
        
        if search:
            filtered_df = filtered_df[
                filtered_df['Client'].str.contains(search, case=False, na=False) |
                filtered_df['Téléphone'].str.contains(search, case=False, na=False)
            ]
        
        if selected_status != 'Tous':
            filtered_df = filtered_df[filtered_df['Statut'] == selected_status]
        
        # Filtre par date
        if date_filter != "Tous" and not filtered_df.empty:
            today = date.today()
            filtered_df['Date_obj'] = pd.to_datetime(filtered_df['Date']).dt.date
            
            if date_filter == "Aujourd'hui":
                filtered_df = filtered_df[filtered_df['Date_obj'] == today]
            elif date_filter == "Cette semaine":
                week_start = today - timedelta(days=today.weekday())
                filtered_df = filtered_df[filtered_df['Date_obj'] >= week_start]
            elif date_filter == "Ce mois":
                month_start = today.replace(day=1)
                filtered_df = filtered_df[filtered_df['Date_obj'] >= month_start]
            
            filtered_df = filtered_df.drop('Date_obj', axis=1)
        
        # Affichage du tableau
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        # Statistiques du filtre
        st.caption(f"Affichage de {len(filtered_df)} réservations sur {len(reservations_df)}")
        
        # Bouton export
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger CSV",
                data=csv,
                file_name="reservations.csv",
                mime="text/csv"
            )
    
    with col2:
        st.subheader("Répartition par Statut")
        
        # Affichage par statut
        if reservation_stats['by_status']:
            for status_info in reservation_stats['by_status']:
                status = status_info['status']
                count = status_info['count']
                
                # Émoji selon le statut
                emoji = {
                    'booked': '',
                    'cancelled': '',
                    'completed': ''
                }.get(status, '')
                
                # Couleur selon le statut
                color = {
                    'booked': '#4ECDC4',
                    'cancelled': '#FF6B6B',
                    'completed': '#6C5CE7'
                }.get(status, '#95A5A6')
                
                percentage = (count / max(reservation_stats['total'], 1)) * 100
                
                st.markdown(f"""
                <div style='background-color: {color}20; padding: 5px; border-radius: 5px; 
                            margin: 10px 0; border-left: 4px solid {color};'>
                    <h4 style='margin: 0;'>{emoji} {status.title()}</h4>
                    <p style='margin: 5px 0; font-size: 1.2em;'>
                        <b>{count}</b> réservations ({percentage:.1f}%)
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aucune donnée disponible")
    
    # Graphiques d'évolution
    st.markdown("---")
    st.subheader("Évolution des Réservations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Réservations par jour**")
        if not reservations_by_day_df.empty:
            # Convertir Date en string pour Altair
            plot_df = reservations_by_day_df.copy()
            plot_df['Date'] = plot_df['Date'].astype(str)
            
            chart = create_line_chart(
                plot_df.tail(30),  # 30 derniers jours
                'Date',
                'Réservations',
                '',
                color='#4ECDC4',
                height=300
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Aucune donnée")
    
    with col2:
        st.markdown("**Nombre de personnes par jour**")
        if not reservations_by_day_df.empty:
            plot_df = reservations_by_day_df.copy()
            plot_df['Date'] = plot_df['Date'].astype(str)
            
            chart = create_bar_chart(
                plot_df.tail(30),
                'Date',
                'Total personnes',
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
