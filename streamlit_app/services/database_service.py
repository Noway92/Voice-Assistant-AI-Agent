"""
Database Service Layer
======================
Gère toutes les interactions avec la base de données via SQLAlchemy
"""

import streamlit as st
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
import pandas as pd
from sqlalchemy import func, and_, or_, desc, extract
from sqlalchemy.orm import Session

# Ajouter le chemin parent pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.db_config import SessionLocal
from src.database.database import Client, Reservation, Table, MenuItem, Order, OrderItem


def get_db_session():
    """Crée et retourne une session de base de données"""
    return SessionLocal()


# ==================== CLIENTS ====================

@st.cache_data(ttl=300)
def get_all_clients() -> pd.DataFrame:
    """Récupère tous les clients"""
    db = get_db_session()
    try:
        clients = db.query(Client).all()
        data = [{
            'ID': c.id,
            'Nom': c.name,
            'Téléphone': c.phone,
            'Email': c.email,
            'Date création': c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else None
        } for c in clients]
        return pd.DataFrame(data)
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_client_stats() -> Dict:
    """Statistiques sur les clients"""
    db = get_db_session()
    try:
        total_clients = db.query(func.count(Client.id)).scalar()
        
        # Nouveaux clients ce mois
        now = datetime.now()
        first_day = now.replace(day=1)
        new_this_month = db.query(func.count(Client.id))\
            .filter(Client.created_at >= first_day).scalar()
        
        # Top clients par réservations
        top_clients = db.query(
            Client.name,
            func.count(Reservation.id).label('reservation_count')
        ).join(Reservation)\
         .group_by(Client.id, Client.name)\
         .order_by(desc('reservation_count'))\
         .limit(5)\
         .all()
        
        return {
            'total': total_clients,
            'new_this_month': new_this_month,
            'top_clients': [{'name': c[0], 'reservations': c[1]} for c in top_clients]
        }
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_new_clients_by_month() -> pd.DataFrame:
    """Nouveaux clients par mois"""
    db = get_db_session()
    try:
        results = db.query(
            extract('year', Client.created_at).label('year'),
            extract('month', Client.created_at).label('month'),
            func.count(Client.id).label('count')
        ).group_by('year', 'month')\
         .order_by('year', 'month')\
         .all()
        
        data = [{
            'Année': int(r[0]),
            'Mois': int(r[1]),
            'Nouveaux clients': r[2]
        } for r in results]
        
        return pd.DataFrame(data)
    finally:
        db.close()


# ==================== MENU ====================

@st.cache_data(ttl=300)
def get_all_menu_items() -> pd.DataFrame:
    """Récupère tous les items du menu"""
    db = get_db_session()
    try:
        items = db.query(MenuItem).all()
        data = [{
            'ID': item.id,
            'Nom': item.name,
            'Catégorie': item.category,
            'Prix': f"{item.price:.2f}€",
            'Disponible': 'Oui' if item.is_available else 'Non',
            'Description': item.description
        } for item in items]
        return pd.DataFrame(data)
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_menu_by_category(category: str = None) -> pd.DataFrame:
    """Filtre le menu par catégorie"""
    db = get_db_session()
    try:
        query = db.query(MenuItem)
        if category:
            query = query.filter(MenuItem.category == category)
        
        items = query.all()
        data = [{
            'ID': item.id,
            'Nom': item.name,
            'Catégorie': item.category,
            'Prix': item.price,
            'Disponible': item.is_available
        } for item in items]
        return pd.DataFrame(data)
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_menu_stats() -> Dict:
    """Statistiques sur le menu"""
    db = get_db_session()
    try:
        total_items = db.query(func.count(MenuItem.id)).scalar()
        available_items = db.query(func.count(MenuItem.id))\
            .filter(MenuItem.is_available == True).scalar()
        
        # Répartition par catégorie
        by_category = db.query(
            MenuItem.category,
            func.count(MenuItem.id).label('count')
        ).group_by(MenuItem.category).all()
        
        return {
            'total': total_items,
            'available': available_items,
            'by_category': [{'category': c[0], 'count': c[1]} for c in by_category]
        }
    finally:
        db.close()


# ==================== TABLES ====================

@st.cache_data(ttl=300)
def get_all_tables() -> pd.DataFrame:
    """Récupère toutes les tables"""
    db = get_db_session()
    try:
        tables = db.query(Table).all()
        data = [{
            'ID': t.id,
            'Numéro': t.table_number,
            'Capacité': t.capacity,
            'Emplacement': t.location,
            'Active': 'Oui' if t.is_active else 'Non'
        } for t in tables]
        return pd.DataFrame(data)
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_table_stats() -> Dict:
    """Statistiques sur les tables"""
    db = get_db_session()
    try:
        total_tables = db.query(func.count(Table.id)).scalar()
        total_capacity = db.query(func.sum(Table.capacity)).scalar() or 0
        
        # Tables par emplacement
        by_location = db.query(
            Table.location,
            func.count(Table.id).label('count'),
            func.sum(Table.capacity).label('capacity')
        ).group_by(Table.location).all()
        
        return {
            'total': total_tables,
            'total_capacity': total_capacity,
            'by_location': [{'location': loc[0], 'count': loc[1], 'capacity': loc[2]} 
                          for loc in by_location]
        }
    finally:
        db.close()


# ==================== RESERVATIONS ====================

@st.cache_data(ttl=300)
def get_all_reservations() -> pd.DataFrame:
    """Récupère toutes les réservations"""
    db = get_db_session()
    try:
        reservations = db.query(Reservation)\
            .join(Client)\
            .join(Table)\
            .order_by(desc(Reservation.date), desc(Reservation.time))\
            .all()
        
        data = [{
            'ID': r.id,
            'Client': r.client.name,
            'Téléphone': r.client.phone,
            'Table': r.table.table_number,
            'Date': r.date.strftime('%Y-%m-%d'),
            'Heure': r.time,
            'Personnes': r.num_guests,
            'Statut': r.status,
            'Demandes spéciales': r.special_requests
        } for r in reservations]
        
        return pd.DataFrame(data)
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_reservations_by_date(start_date: date = None, end_date: date = None) -> pd.DataFrame:
    """Filtre les réservations par date"""
    db = get_db_session()
    try:
        query = db.query(Reservation).join(Client).join(Table)
        
        if start_date:
            query = query.filter(Reservation.date >= start_date)
        if end_date:
            query = query.filter(Reservation.date <= end_date)
        
        reservations = query.order_by(desc(Reservation.date)).all()
        
        data = [{
            'ID': r.id,
            'Client': r.client.name,
            'Date': r.date,
            'Heure': r.time,
            'Personnes': r.num_guests,
            'Statut': r.status
        } for r in reservations]
        
        return pd.DataFrame(data)
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_reservation_stats() -> Dict:
    """Statistiques sur les réservations"""
    db = get_db_session()
    try:
        total_reservations = db.query(func.count(Reservation.id)).scalar()
        
        # Réservations ce mois
        now = datetime.now()
        first_day = now.replace(day=1)
        this_month = db.query(func.count(Reservation.id))\
            .filter(Reservation.date >= first_day.date()).scalar()
        
        # Par statut
        by_status = db.query(
            Reservation.status,
            func.count(Reservation.id).label('count')
        ).group_by(Reservation.status).all()
        
        # Moyenne de personnes par réservation
        avg_guests = db.query(func.avg(Reservation.num_guests)).scalar() or 0
        
        return {
            'total': total_reservations,
            'this_month': this_month,
            'by_status': [{'status': s[0], 'count': s[1]} for s in by_status],
            'avg_guests': round(avg_guests, 1)
        }
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_reservations_by_day() -> pd.DataFrame:
    """Réservations groupées par jour"""
    db = get_db_session()
    try:
        results = db.query(
            Reservation.date,
            func.count(Reservation.id).label('count'),
            func.sum(Reservation.num_guests).label('total_guests')
        ).group_by(Reservation.date)\
         .order_by(Reservation.date)\
         .all()
        
        data = [{
            'Date': r[0],
            'Réservations': r[1],
            'Total personnes': r[2]
        } for r in results]
        
        return pd.DataFrame(data)
    finally:
        db.close()


# ==================== ORDERS ====================

@st.cache_data(ttl=300)
def get_all_orders() -> pd.DataFrame:
    """Récupère toutes les commandes"""
    db = get_db_session()
    try:
        orders = db.query(Order)\
            .order_by(desc(Order.created_at))\
            .all()
        
        data = [{
            'ID': o.id,
            'Client': o.customer_name or 'N/A',
            'Téléphone': o.customer_phone or 'N/A',
            'Table': o.table_number or 'N/A',
            'Montant': f"{o.total_amount:.2f}€",
            'Statut': o.status,
            'Type': o.order_type,
            'Date': o.created_at.strftime('%Y-%m-%d %H:%M') if o.created_at else None
        } for o in orders]
        
        return pd.DataFrame(data)
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_order_stats() -> Dict:
    """Statistiques sur les commandes"""
    db = get_db_session()
    try:
        total_orders = db.query(func.count(Order.id)).scalar()
        total_revenue = db.query(func.sum(Order.total_amount)).scalar() or 0
        
        # Panier moyen
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Par statut
        by_status = db.query(
            Order.status,
            func.count(Order.id).label('count')
        ).group_by(Order.status).all()
        
        # CA par type
        by_type = db.query(
            Order.order_type,
            func.sum(Order.total_amount).label('revenue')
        ).group_by(Order.order_type).all()
        
        return {
            'total': total_orders,
            'total_revenue': round(total_revenue, 2),
            'avg_order_value': round(avg_order_value, 2),
            'by_status': [{'status': s[0], 'count': s[1]} for s in by_status],
            'by_type': [{'type': t[0], 'revenue': round(t[1], 2)} for t in by_type]
        }
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_revenue_by_day() -> pd.DataFrame:
    """CA par jour"""
    db = get_db_session()
    try:
        results = db.query(
            func.date(Order.created_at).label('date'),
            func.sum(Order.total_amount).label('revenue'),
            func.count(Order.id).label('order_count')
        ).group_by(func.date(Order.created_at))\
         .order_by('date')\
         .all()
        
        data = [{
            'Date': r[0],
            'CA': round(r[1], 2),
            'Commandes': r[2]
        } for r in results]
        
        return pd.DataFrame(data)
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_top_products() -> pd.DataFrame:
    """Produits les plus vendus"""
    db = get_db_session()
    try:
        results = db.query(
            MenuItem.name,
            MenuItem.category,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.subtotal).label('total_revenue')
        ).join(OrderItem)\
         .group_by(MenuItem.id, MenuItem.name, MenuItem.category)\
         .order_by(desc('total_quantity'))\
         .limit(10)\
         .all()
        
        data = [{
            'Produit': r[0],
            'Catégorie': r[1],
            'Quantité vendue': int(r[2]),
            'CA': round(r[3], 2)
        } for r in results]
        
        return pd.DataFrame(data)
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_revenue_by_product_category() -> pd.DataFrame:
    """CA par catégorie de produit"""
    db = get_db_session()
    try:
        results = db.query(
            MenuItem.category,
            func.sum(OrderItem.subtotal).label('revenue'),
            func.sum(OrderItem.quantity).label('quantity')
        ).join(OrderItem)\
         .group_by(MenuItem.category)\
         .order_by(desc('revenue'))\
         .all()
        
        data = [{
            'Catégorie': r[0],
            'CA': round(r[1], 2),
            'Quantité': int(r[2])
        } for r in results]
        
        return pd.DataFrame(data)
    finally:
        db.close()


# ==================== STATISTIQUES AVANCÉES ====================

@st.cache_data(ttl=300)
def get_top_clients_by_revenue() -> pd.DataFrame:
    """Top clients par CA"""
    db = get_db_session()
    try:
        results = db.query(
            Client.name,
            Client.phone,
            func.count(Order.id).label('order_count'),
            func.sum(Order.total_amount).label('total_revenue')
        ).join(Order, Order.customer_phone == Client.phone)\
         .group_by(Client.id, Client.name, Client.phone)\
         .order_by(desc('total_revenue'))\
         .limit(10)\
         .all()
        
        data = [{
            'Client': r[0],
            'Téléphone': r[1],
            'Commandes': r[2],
            'CA total': round(r[3], 2)
        } for r in results]
        
        return pd.DataFrame(data)
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_occupancy_rate() -> Dict:
    """Taux d'occupation des tables"""
    db = get_db_session()
    try:
        # Tables actives
        total_tables = db.query(func.count(Table.id))\
            .filter(Table.is_active == True).scalar()
        
        # Réservations aujourd'hui
        today = date.today()
        reservations_today = db.query(func.count(Reservation.id))\
            .filter(Reservation.date == today)\
            .filter(Reservation.status == 'booked')\
            .scalar()
        
        occupancy_rate = (reservations_today / total_tables * 100) if total_tables > 0 else 0
        
        return {
            'total_tables': total_tables,
            'reservations_today': reservations_today,
            'occupancy_rate': round(occupancy_rate, 1)
        }
    finally:
        db.close()
