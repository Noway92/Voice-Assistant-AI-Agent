# Restaurant Analytics Dashboard

Application Streamlit multi-pages pour analyser les données d'un restaurant à partir de modèles SQLAlchemy et PostgreSQL.

## Fonctionnalités

### Visualisation des Données
- **Clients** : Liste complète, recherche, top clients, évolution
- **Menu** : Items du menu, filtres par catégorie, statistiques
- **Tables** : Gestion des tables, capacités, emplacements
- **Réservations** : Suivi des réservations, filtres par date/statut
- **Commandes** : Analyse des commandes, CA, top produits

### Tableau de Bord Statistiques
- KPIs métier en temps réel
- Analyse du chiffre d'affaires
- Top produits et catégories
- Top clients par CA
- Taux d'occupation des tables
- Évolutions temporelles

### Interface Utilisateur
- Layout wide pour plus d'espace
- Navigation par sidebar
- Graphiques interactifs (Altair)
- Export CSV pour chaque page
- Dark theme disponible
- Design responsive

## Architecture

```
streamlit_app/
├── app.py                      # Page d'accueil
├── pages/
│   ├── 1_Clients.py           # Page clients
│   ├── 2_Menu.py              # Page menu
│   ├── 3_Tables.py            # Page tables
│   ├── 4_Reservations.py      # Page réservations
│   ├── 5_Orders.py            # Page commandes
│   └── 6_Statistics.py        # Page statistiques complètes
├── services/
│   └── database_service.py    # Logique base de données
├── utils/
│   └── charts.py              # Utilitaires graphiques
├── .streamlit/
│   └── config.toml            # Configuration Streamlit
├── requirements.txt           # Dépendances Python
└── README.md                  # Ce fichier
```

## Installation

### Prérequis
- Python 3.10
- PostgreSQL
- Variables d'environnement configurées (voir `.env`)

### Étapes

1. **Installer les dépendances**
   ```bash
   cd streamlit_app
   pip install -r requirements.txt
   ```

2. **Vérifier la configuration de la base de données**
   
   Assurez-vous que votre fichier `.env` à la racine du projet contient :
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=restaurant_db
   DB_USER=your_user
   DB_PASSWORD=your_password
   ```

3. **Initialiser la base de données** (si ce n'est pas déjà fait)
   ```bash
   cd ..
   python src/database/init_database.py
   ```

4. **Lancer l'application**
   ```bash
   cd streamlit_app
   streamlit run app.py
   ```

L'application sera accessible sur `http://localhost:8501`

## Pages Disponibles

### Accueil (`app.py`)
- Vue d'ensemble des fonctionnalités
- Statut de la connexion à la base de données
- Navigation vers les différentes sections

### Clients
- Liste complète des clients
- Recherche par nom/téléphone
- Top clients par réservations
- Évolution des nouveaux clients

### Menu
- Tous les items du menu
- Filtres par catégorie
- Statistiques de disponibilité
- Répartition par catégorie (graphique)

### Tables
- Liste des tables
- Filtres par emplacement
- Capacités et statistiques
- Graphiques par emplacement

### Réservations
- Toutes les réservations
- Filtres par date, statut
- Répartition par statut
- Évolution temporelle

### Commandes
- Liste des commandes
- Filtres par statut, type
- Top 10 produits
- Analyse du CA par jour

### Statistiques
- Vue d'ensemble complète
- KPIs métier
- Graphiques interactifs
- Analyses multi-dimensionnelles

## Configuration

### Thème (`config.toml`)
```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

### Cache
Les requêtes sont cachées pendant 5 minutes (`ttl=300`) pour optimiser les performances.

## Dépendances Principales

- **Streamlit** (≥1.30.0) : Framework web
- **SQLAlchemy** (≥2.0.0) : ORM
- **Pandas** (≥2.0.0) : Manipulation de données
- **Altair** (≥5.0.0) : Graphiques interactifs
- **psycopg2-binary** (≥2.9.0) : Connecteur PostgreSQL

### Modifier les graphiques
Toutes les fonctions de graphiques sont dans `utils/charts.py`

## Export de Données

Chaque page permet d'exporter les données affichées au format CSV via le bouton "📥 Télécharger CSV".

## Performance

- **Cache** : Les requêtes sont cachées (TTL: 5 minutes)
- **Pagination** : Limitation des résultats pour les graphiques (30 derniers jours)
- **Lazy loading** : Chargement des données uniquement quand nécessaire

## Licence

Ce projet fait partie du système Voice Assistant AI Agent pour restaurant.

## Support

Pour toute question ou problème, consultez la documentation du projet principal.

---

**Version** : 1.0  
**Dernière mise à jour** : Janvier 2026
