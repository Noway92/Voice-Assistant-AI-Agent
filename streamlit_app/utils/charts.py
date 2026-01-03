"""
Chart Utilities
================
Fonctions pour créer des graphiques avec Streamlit et Altair
"""

import streamlit as st
import pandas as pd
import altair as alt
from typing import List, Dict, Optional


def create_bar_chart(data: pd.DataFrame, x_col: str, y_col: str, 
                     title: str = "", color: str = "#FF6B6B",
                     height: int = 400) -> alt.Chart:
    """
    Crée un graphique en barres
    
    Args:
        data: DataFrame contenant les données
        x_col: Nom de la colonne pour l'axe X
        y_col: Nom de la colonne pour l'axe Y
        title: Titre du graphique
        color: Couleur des barres
        height: Hauteur du graphique
    
    Returns:
        Chart Altair
    """
    chart = alt.Chart(data).mark_bar(color=color).encode(
        x=alt.X(x_col, title=x_col),
        y=alt.Y(y_col, title=y_col),
        tooltip=[x_col, y_col]
    ).properties(
        title=title,
        height=height
    ).interactive()
    
    return chart


def create_line_chart(data: pd.DataFrame, x_col: str, y_col: str,
                      title: str = "", color: str = "#4ECDC4",
                      height: int = 400) -> alt.Chart:
    """
    Crée un graphique en ligne
    
    Args:
        data: DataFrame contenant les données
        x_col: Nom de la colonne pour l'axe X
        y_col: Nom de la colonne pour l'axe Y
        title: Titre du graphique
        color: Couleur de la ligne
        height: Hauteur du graphique
    
    Returns:
        Chart Altair
    """
    chart = alt.Chart(data).mark_line(
        point=True,
        color=color,
        strokeWidth=3
    ).encode(
        x=alt.X(x_col, title=x_col),
        y=alt.Y(y_col, title=y_col),
        tooltip=[x_col, y_col]
    ).properties(
        title=title,
        height=height
    ).interactive()
    
    return chart


def create_pie_chart(data: pd.DataFrame, label_col: str, value_col: str,
                     title: str = "", height: int = 400) -> alt.Chart:
    """
    Crée un graphique camembert
    
    Args:
        data: DataFrame contenant les données
        label_col: Nom de la colonne pour les labels
        value_col: Nom de la colonne pour les valeurs
        title: Titre du graphique
        height: Hauteur du graphique
    
    Returns:
        Chart Altair
    """
    chart = alt.Chart(data).mark_arc(innerRadius=50).encode(
        theta=alt.Theta(value_col, type='quantitative'),
        color=alt.Color(
            label_col,
            type='nominal',
            scale=alt.Scale(scheme='category20')
        ),
        tooltip=[label_col, value_col]
    ).properties(
        title=title,
        height=height
    )
    
    return chart


def create_horizontal_bar_chart(data: pd.DataFrame, x_col: str, y_col: str,
                                 title: str = "", color: str = "#FFD93D",
                                 height: int = 400) -> alt.Chart:
    """
    Crée un graphique en barres horizontales
    
    Args:
        data: DataFrame contenant les données
        x_col: Nom de la colonne pour l'axe X (valeurs)
        y_col: Nom de la colonne pour l'axe Y (catégories)
        title: Titre du graphique
        color: Couleur des barres
        height: Hauteur du graphique
    
    Returns:
        Chart Altair
    """
    chart = alt.Chart(data).mark_bar(color=color).encode(
        x=alt.X(x_col, title=x_col),
        y=alt.Y(y_col, sort='-x', title=y_col),
        tooltip=[y_col, x_col]
    ).properties(
        title=title,
        height=height
    ).interactive()
    
    return chart


def create_multi_line_chart(data: pd.DataFrame, x_col: str, y_cols: List[str],
                            title: str = "", height: int = 400) -> alt.Chart:
    """
    Crée un graphique avec plusieurs lignes
    
    Args:
        data: DataFrame contenant les données
        x_col: Nom de la colonne pour l'axe X
        y_cols: Liste des colonnes pour les différentes lignes
        title: Titre du graphique
        height: Hauteur du graphique
    
    Returns:
        Chart Altair
    """
    # Transformer le DataFrame pour Altair
    df_melted = data.melt(x_col, var_name='Série', value_name='Valeur')
    
    chart = alt.Chart(df_melted).mark_line(point=True).encode(
        x=alt.X(x_col, title=x_col),
        y=alt.Y('Valeur:Q', title='Valeur'),
        color='Série:N',
        tooltip=[x_col, 'Série', 'Valeur']
    ).properties(
        title=title,
        height=height
    ).interactive()
    
    return chart


def create_area_chart(data: pd.DataFrame, x_col: str, y_col: str,
                      title: str = "", color: str = "#6C5CE7",
                      height: int = 400) -> alt.Chart:
    """
    Crée un graphique en aire
    
    Args:
        data: DataFrame contenant les données
        x_col: Nom de la colonne pour l'axe X
        y_col: Nom de la colonne pour l'axe Y
        title: Titre du graphique
        color: Couleur de l'aire
        height: Hauteur du graphique
    
    Returns:
        Chart Altair
    """
    chart = alt.Chart(data).mark_area(
        color=color,
        opacity=0.7,
        line={'color': color}
    ).encode(
        x=alt.X(x_col, title=x_col),
        y=alt.Y(y_col, title=y_col),
        tooltip=[x_col, y_col]
    ).properties(
        title=title,
        height=height
    ).interactive()
    
    return chart


def create_stacked_bar_chart(data: pd.DataFrame, x_col: str, y_col: str, 
                             color_col: str, title: str = "",
                             height: int = 400) -> alt.Chart:
    """
    Crée un graphique en barres empilées
    
    Args:
        data: DataFrame contenant les données
        x_col: Nom de la colonne pour l'axe X
        y_col: Nom de la colonne pour l'axe Y
        color_col: Nom de la colonne pour la couleur/catégorie
        title: Titre du graphique
        height: Hauteur du graphique
    
    Returns:
        Chart Altair
    """
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X(x_col, title=x_col),
        y=alt.Y(y_col, title=y_col),
        color=alt.Color(color_col, scale=alt.Scale(scheme='category20')),
        tooltip=[x_col, y_col, color_col]
    ).properties(
        title=title,
        height=height
    ).interactive()
    
    return chart


def display_metric_card(label: str, value: str, delta: str = None,
                        delta_color: str = "normal"):
    """
    Affiche une carte de métrique stylisée
    
    Args:
        label: Label de la métrique
        value: Valeur principale
        delta: Variation (optionnel)
        delta_color: Couleur du delta ("normal", "inverse", "off")
    """
    if delta:
        st.metric(label=label, value=value, delta=delta, delta_color=delta_color)
    else:
        st.metric(label=label, value=value)


def display_kpi_row(metrics: List[Dict]):
    """
    Affiche une ligne de KPIs
    
    Args:
        metrics: Liste de dictionnaires avec 'label', 'value', 'delta' (optionnel)
    
    Example:
        display_kpi_row([
            {'label': 'Total CA', 'value': '15,000€', 'delta': '+12%'},
            {'label': 'Commandes', 'value': '120', 'delta': '+5%'}
        ])
    """
    cols = st.columns(len(metrics))
    
    for idx, metric in enumerate(metrics):
        with cols[idx]:
            if 'delta' in metric:
                st.metric(
                    label=metric['label'],
                    value=metric['value'],
                    delta=metric['delta']
                )
            else:
                st.metric(
                    label=metric['label'],
                    value=metric['value']
                )


def create_gauge_chart(value: float, max_value: float = 100,
                       title: str = "", color: str = "#FF6B6B",
                       height: int = 200) -> alt.Chart:
    """
    Crée un graphique de jauge simple
    
    Args:
        value: Valeur actuelle
        max_value: Valeur maximale
        title: Titre
        color: Couleur
        height: Hauteur
    
    Returns:
        Chart Altair
    """
    data = pd.DataFrame({
        'category': ['Utilisé', 'Restant'],
        'value': [value, max_value - value]
    })
    
    chart = alt.Chart(data).mark_arc(innerRadius=50).encode(
        theta=alt.Theta('value:Q'),
        color=alt.Color(
            'category:N',
            scale=alt.Scale(
                domain=['Utilisé', 'Restant'],
                range=[color, '#E0E0E0']
            ),
            legend=None
        ),
        tooltip=['category', 'value']
    ).properties(
        title=title,
        height=height
    )
    
    return chart


def format_currency(value: float) -> str:
    """Formate un nombre en devise"""
    return f"{value:,.2f}€".replace(',', ' ')


def format_percentage(value: float) -> str:
    """Formate un nombre en pourcentage"""
    return f"{value:.1f}%"


def format_number(value: float) -> str:
    """Formate un nombre avec séparateurs de milliers"""
    return f"{value:,.0f}".replace(',', ' ')
