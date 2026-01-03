"""
Page Commandes
==============
Visualisation et analyse des commandes
"""

import streamlit as st
import sys
import os
from datetime import datetime, date, timedelta
from pathlib import Path

# Ajouter le chemin parent
sys.path.append(str(Path(__file__).parent.parent.parent))

from streamlit_app.services.database_service import (
    get_all_orders,
    get_order_stats,
    get_revenue_by_day,
    get_top_products
)
from streamlit_app.utils.charts import (
    create_line_chart,
    create_area_chart,
    display_kpi_row,
    format_currency,
    format_number
)
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="Commandes - Restaurant Analytics",
    page_icon="�",
    layout="wide"
)

# Titre
st.title("Gestion des Commandes")
st.markdown("---")

# Récupération des données
try:
    orders_df = get_all_orders()
    order_stats = get_order_stats()
    revenue_by_day_df = get_revenue_by_day()
    top_products_df = get_top_products()
    
    # KPIs
    st.subheader("Indicateurs Clés")
    
    display_kpi_row([
        {
            'label': 'Total Commandes',
            'value': format_number(order_stats['total'])
        },
        {
            'label': 'CA Total',
            'value': format_currency(order_stats['total_revenue'])
        },
        {
            'label': 'Panier Moyen',
            'value': format_currency(order_stats['avg_order_value'])
        },
        {
            'label': 'CA moy. journalier',
            "value": format_currency(revenue_by_day_df['CA'].mean()),
        }
    ])
    
    st.markdown("---")
    
    # Deux colonnes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Liste des Commandes")
        
        # Filtres
        col_search, col_status, col_type = st.columns([2, 1, 1])
        
        with col_search:
            search = st.text_input("Rechercher client/téléphone", "")
        
        with col_status:
            statuses = ['Tous'] + [s['status'] for s in order_stats['by_status']]
            selected_status = st.selectbox("Statut", statuses)
        
        with col_type:
            types = ['Tous'] + [t['type'] for t in order_stats['by_type']]
            selected_type = st.selectbox("Type", types)
        
        # Filtrer les données
        filtered_df = orders_df.copy()
        
        if search:
            filtered_df = filtered_df[
                filtered_df['Client'].str.contains(search, case=False, na=False) |
                filtered_df['Téléphone'].str.contains(search, case=False, na=False)
            ]
        
        if selected_status != 'Tous':
            filtered_df = filtered_df[filtered_df['Statut'] == selected_status]
        
        if selected_type != 'Tous':
            filtered_df = filtered_df[filtered_df['Type'] == selected_type]
        
        # Affichage du tableau
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        # Statistiques du filtre
        st.caption(f"Affichage de {len(filtered_df)} commandes sur {len(orders_df)}")
        
        # Bouton export
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger CSV",
                data=csv,
                file_name="commandes.csv",
                mime="text/csv"
            )
    
    with col2:
        st.subheader("Répartition")
        
        # Par statut
        st.markdown("**Par Statut**")
        if order_stats['by_status']:
            for status_info in order_stats['by_status']:
                status = status_info['status']
                count = status_info['count']
                percentage = (count / max(order_stats['total'], 1)) * 100
                
                emoji = {
                    'pending': '',
                    'preparing': '',
                    'ready': '',
                    'delivered': '',
                    'cancelled': ''
                }.get(status, '')
                
                st.markdown(f"**{emoji}{status.title()}**: {count} ({percentage:.1f}%)")
        
        st.markdown("---")
        
        # Par type
        st.markdown("**Par Type**")
        if order_stats['by_type']:
            for type_info in order_stats['by_type']:
                order_type = type_info['type']
                revenue = type_info['revenue']
                
                emoji = {
                    'dine-in': '',
                    'takeaway': '',
                    'delivery': ''
                }.get(order_type, '')
                
                st.markdown(f"**{emoji}{order_type.title()}**: {format_currency(revenue)}")
    
    # Graphiques CA
    st.markdown("---")
    st.subheader("Analyse du Chiffre d'Affaires")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**CA par jour**")
        if not revenue_by_day_df.empty:
            plot_df = revenue_by_day_df.copy()
            plot_df['Date'] = plot_df['Date'].astype(str)
            
            chart = create_area_chart(
                plot_df.tail(30),
                'Date',
                'CA',
                '',
                color='#6C5CE7',
                height=300
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Aucune donnée")
    
    with col2:
        st.markdown("**Commandes par jour**")
        if not revenue_by_day_df.empty:
            plot_df = revenue_by_day_df.copy()
            plot_df['Date'] = plot_df['Date'].astype(str)
            
            chart = create_line_chart(
                plot_df.tail(30),
                'Date',
                'Commandes',
                '',
                color='#4ECDC4',
                height=300
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Aucune donnée")
    
    # Top produits
    st.markdown("---")
    st.subheader("Top 10 Produits")
    
    if not top_products_df.empty:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Par quantité vendue**")
            st.dataframe(
                top_products_df[['Produit', 'Catégorie', 'Quantité vendue']],
                use_container_width=True,
                hide_index=True,
                height=350
            )
        
        with col2:
            st.markdown("**Par chiffre d'affaires**")
            top_by_revenue = top_products_df.sort_values('CA', ascending=False)
            st.dataframe(
                top_by_revenue[['Produit', 'Catégorie', 'CA']],
                use_container_width=True,
                hide_index=True,
                height=350
            )
    else:
        st.info("Aucune donnée de produits disponible")

except Exception as e:
    st.error(f"Erreur lors du chargement des données : {str(e)}")
    st.info("Vérifiez que la base de données est accessible et initialisée")
