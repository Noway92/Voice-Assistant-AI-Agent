"""
Page Statistiques
==================
Dashboard complet avec tous les KPIs et analyses du restaurant
"""

import streamlit as st
import sys
import os
from datetime import datetime, date, timedelta
from pathlib import Path

# Ajouter le chemin parent
sys.path.append(str(Path(__file__).parent.parent.parent))

from streamlit_app.services.database_service import (
    get_client_stats,
    get_menu_stats,
    get_table_stats,
    get_reservation_stats,
    get_order_stats,
    get_revenue_by_day,
    get_top_products,
    get_revenue_by_product_category,
    get_top_clients_by_revenue,
    get_occupancy_rate,
    get_reservations_by_day,
    get_new_clients_by_month
)
from streamlit_app.utils.charts import (
    create_line_chart,
    create_bar_chart,
    create_pie_chart,
    create_area_chart,
    create_horizontal_bar_chart,
    display_kpi_row,
    format_currency,
    format_number,
    format_percentage
)
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="Statistiques - Restaurant Analytics",
    page_icon="�",
    layout="wide"
)

# Titre
st.title("Tableau de Bord - Statistiques Complètes")
st.markdown("---")

# Récupération des données
try:
    client_stats = get_client_stats()
    menu_stats = get_menu_stats()
    table_stats = get_table_stats()
    reservation_stats = get_reservation_stats()
    order_stats = get_order_stats()
    revenue_by_day_df = get_revenue_by_day()
    top_products_df = get_top_products()
    revenue_by_category_df = get_revenue_by_product_category()
    top_clients_df = get_top_clients_by_revenue()
    occupancy_data = get_occupancy_rate()
    reservations_by_day_df = get_reservations_by_day()
    new_clients_df = get_new_clients_by_month()
    
    # ========== SECTION 1: VUE D'ENSEMBLE ==========
    st.header("Vue d'Ensemble")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Clients",
            format_number(client_stats['total']),
            f"+{client_stats['new_this_month']} ce mois",
            help="Nombre total de clients"
        )
    
    with col2:
        st.metric(
            "Produits",
            format_number(menu_stats['total']),
            f"{menu_stats['available']} disponibles",
            help="Items du menu"
        )
    
    with col3:
        st.metric(
            "Tables",
            format_number(table_stats['total']),
            f"{table_stats['total_capacity']} places",
            help="Tables et capacité"
        )
    
    with col4:
        st.metric(
            "Réservations",
            format_number(reservation_stats['total']),
            f"{reservation_stats['this_month']} ce mois",
            help="Total des réservations"
        )
    
    with col5:
        st.metric(
            "Commandes",
            format_number(order_stats['total']),
            format_currency(order_stats['total_revenue']),
            help="Commandes et CA total"
        )
    
    st.markdown("---")
    
    # ========== SECTION 2: CHIFFRE D'AFFAIRES ==========
    st.header("Analyse du Chiffre d'Affaires")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "CA Total",
            format_currency(order_stats['total_revenue']),
            help="Chiffre d'affaires total"
        )
    
    with col2:
        st.metric(
            "Panier Moyen",
            format_currency(order_stats['avg_order_value']),
            help="Montant moyen par commande"
        )
    
    with col3:
        if not revenue_by_day_df.empty:
            avg_daily = revenue_by_day_df['CA'].mean()
            st.metric(
                "CA Moyen Journalier",
                format_currency(avg_daily),
                help="Moyenne du CA par jour"
            )
        else:
            st.metric("CA Moyen Journalier", format_currency(0))
    
    # Graphique CA
    st.subheader("Évolution du CA")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**CA par jour (30 derniers jours)**")
        if not revenue_by_day_df.empty:
            plot_df = revenue_by_day_df.tail(30).copy()
            plot_df['Date'] = plot_df['Date'].astype(str)
            
            chart = create_area_chart(
                plot_df,
                'Date',
                'CA',
                '',
                color='#6C5CE7',
                height=300
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Aucune donnée de CA disponible")
    
    with col2:
        st.markdown("**CA par catégorie de produits**")
        if not revenue_by_category_df.empty:
            chart = create_pie_chart(
                revenue_by_category_df,
                'Catégorie',
                'CA',
                '',
                height=300
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Aucune donnée disponible")
    
    st.markdown("---")
    
    # ========== SECTION 3: PRODUITS ==========
    st.header("Analyse des Produits")
    
    # Top 10 Produits - pleine largeur
    st.subheader("Top 10 Produits")
    
    if not top_products_df.empty:
        # Graphique horizontal
        chart = create_horizontal_bar_chart(
            top_products_df.head(10),
            'Quantité vendue',
            'Produit',
            'Produits les plus vendus',
            color='#FF6B6B',
            height=400
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Aucune donnée de produits disponible")
    
    st.markdown("---")
    
    # CA par Catégorie - en colonnes
    st.subheader("CA par Catégorie")
    
    if not revenue_by_category_df.empty:
        # Créer des colonnes dynamiques (3 par défaut)
        cols = st.columns(4)
        
        for idx, row in revenue_by_category_df.iterrows():
            category = row['Catégorie']
            revenue = row['CA']
            quantity = row['Quantité']
            
            # Utiliser les colonnes de façon cyclique
            col = cols[idx % 4]
            
            with col:
                st.markdown(f"""
                <div style='background-color: #f0f2f6; padding: 15px; border-radius: 5px; margin: 10px 0;'>
                    <h4 style='margin: 0; color: #FF6B6B;'>{category}</h4>
                    <p style='margin: 5px 0;'>
                        <b>{format_currency(revenue)}</b><br>
                        <b>{int(quantity)}</b> unités
                    </p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Aucune donnée disponible")
    
    st.markdown("---")
    
    # ========== SECTION 4: CLIENTS ==========
    st.header("Analyse des Clients")

    # Statistiques clients
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total clients",
            format_number(client_stats['total'])
        )
    
    with col2:
        st.metric(
            "Nouveaux ce mois",
            format_number(client_stats['new_this_month'])
        )
    
    with col3:
        growth_rate = (client_stats['new_this_month'] / max(client_stats['total'], 1)) * 100
        st.metric(
            "Taux croissance",
            format_percentage(growth_rate)
        )
    
    with col4:
        if client_stats['top_clients']:
            best_client = client_stats['top_clients'][0]['reservations']
            st.metric(
                "Record réservations",
                format_number(best_client)
            )
        else:
            st.metric("Record réservations", "0")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Clients par CA")
        
        if not top_clients_df.empty:
            st.dataframe(
                top_clients_df.head(10),
                use_container_width=True,
                hide_index=True,
                height=350
            )
        else:
            st.info("Aucune donnée de clients disponible")
    
    with col2:
        st.subheader("Nouveaux Clients")
        
        if not new_clients_df.empty:
            # Créer période lisible
            plot_df = new_clients_df.copy()
            plot_df['Période'] = plot_df.apply(
                lambda x: f"{int(x['Année'])}-{int(x['Mois']):02d}",
                axis=1
            )
            
            chart = create_bar_chart(
                plot_df.tail(12),
                'Période',
                'Nouveaux clients',
                'Nouveaux clients par mois',
                color='#4ECDC4',
                height=300
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Aucune donnée disponible")
    
    
    st.markdown("---")
    
    # ========== SECTION 5: RÉSERVATIONS & OCCUPATION ==========
    st.header("Réservations & Taux d'Occupation")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total réservations",
            format_number(reservation_stats['total'])
        )
    
    with col2:
        st.metric(
            "Ce mois",
            format_number(reservation_stats['this_month'])
        )
    
    with col3:
        st.metric(
            "Moy. personnes",
            str(reservation_stats['avg_guests'])
        )
    
    with col4:
        st.metric(
            "Taux occupation",
            format_percentage(occupancy_data['occupancy_rate']),
            f"{occupancy_data['reservations_today']} / {occupancy_data['total_tables']} tables"
        )
    
    # Graphiques réservations
    st.subheader("Évolution des Réservations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Réservations par jour**")
        if not reservations_by_day_df.empty:
            plot_df = reservations_by_day_df.tail(30).copy()
            plot_df['Date'] = plot_df['Date'].astype(str)
            
            chart = create_line_chart(
                plot_df,
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
        st.markdown("**Personnes par jour**")
        if not reservations_by_day_df.empty:
            plot_df = reservations_by_day_df.tail(30).copy()
            plot_df['Date'] = plot_df['Date'].astype(str)
            
            chart = create_area_chart(
                plot_df,
                'Date',
                'Total personnes',
                '',
                color='#FFD93D',
                height=300
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Aucune donnée")
    
    st.markdown("---")
    
    # ========== SECTION 6: COMMANDES ==========
    st.header("Analyse des Commandes")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total commandes",
            format_number(order_stats['total'])
        )
    
    with col2:
        # Commandes par type
        st.markdown("**Par type**")
        if order_stats['by_type']:
            for type_info in order_stats['by_type']:
                st.markdown(f"- **{type_info['type']}**: {format_currency(type_info['revenue'])}")
    
    with col3:
        # Commandes par statut
        st.markdown("**Par statut**")
        if order_stats['by_status']:
            for status_info in order_stats['by_status']:
                st.markdown(f"- **{status_info['status']}**: {status_info['count']}")
    
    # Graphique commandes
    st.subheader("Commandes par jour")
    
    if not revenue_by_day_df.empty:
        plot_df = revenue_by_day_df.tail(30).copy()
        plot_df['Date'] = plot_df['Date'].astype(str)
        
        chart = create_bar_chart(
            plot_df,
            'Date',
            'Commandes',
            'Nombre de commandes par jour',
            color='#6C5CE7',
            height=300
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Aucune donnée")
    
    st.markdown("---")
    
    # ========== SECTION 7: TABLES ==========
    st.header("Analyse des Tables")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total tables",
            format_number(table_stats['total'])
        )
    
    with col2:
        st.metric(
            "Capacité totale",
            format_number(table_stats['total_capacity'])
        )
    
    with col3:
        avg_capacity = table_stats['total_capacity'] / max(table_stats['total'], 1)
        st.metric(
            "Capacité moyenne",
            f"{avg_capacity:.1f}"
        )
    
    # Répartition par emplacement
    if table_stats['by_location']:
        st.subheader("Répartition par Emplacement")
        
        location_df = pd.DataFrame(table_stats['by_location'])
        location_df.columns = ['Emplacement', 'Tables', 'Capacité']
        
        col1, col2 = st.columns(2)
        
        with col1:
            chart = create_bar_chart(
                location_df,
                'Emplacement',
                'Tables',
                'Nombre de tables',
                color='#4ECDC4',
                height=250
            )
            st.altair_chart(chart, use_container_width=True)
        
        with col2:
            chart = create_bar_chart(
                location_df,
                'Emplacement',
                'Capacité',
                'Capacité totale',
                color='#FFD93D',
                height=250
            )
            st.altair_chart(chart, use_container_width=True)
    
    st.markdown("---")

except Exception as e:
    st.error(f"Erreur lors du chargement des données : {str(e)}")
    st.info("Vérifiez que la base de données est accessible et initialisée")
    
    # Afficher l'erreur complète en mode debug
    with st.expander("Détails de l'erreur (Debug)"):
        import traceback
        st.code(traceback.format_exc())
