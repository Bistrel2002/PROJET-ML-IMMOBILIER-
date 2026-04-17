# 🏠 Projet ML Immobilier — Prédiction de Prix

Application complète de prédiction de prix immobilier en France utilisant le Machine Learning (XGBoost), avec un pipeline de données automatisé et un dashboard interactif.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-Regression-orange)

---

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Exécution](#-exécution)
- [Pipeline ML](#-pipeline-ml)
- [API Backend](#-api-backend)
- [Dashboard Frontend](#-dashboard-frontend)
- [Tests](#-tests)
- [Résultats du Modèle](#-résultats-du-modèle)
- [Données](#-données)

---

## 🚀 Fonctionnalités

### Pipeline de Données
- **Ingestion** : Chargement des données brutes depuis des fichiers CSV (annonces immobilières scrapées)
- **Nettoyage** : Suppression des doublons, normalisation des textes, nettoyage des caractères spéciaux
- **Qualité** : Validation de la qualité des données (valeurs manquantes, outliers, cohérence)
- **Feature Engineering** : Target encoding des villes, one-hot encoding des types de biens, suppression des outliers
- **Pseudonymisation** : Hachage SHA-256 des contacts pour la protection des données personnelles

### Modèle ML
- **XGBoost Regression** pour la prédiction de prix
- **XGBoost Classification** pour la segmentation de prix
- Comparaison automatique des modèles (prix brut vs log-prix)
- Sauvegarde automatique du meilleur modèle

### Dashboard Interactif
- **Tableau de bord** : KPIs en temps réel, distribution des prix, marchés actifs
- **Analyse détaillée** : Prix par type de bien, facteurs d'influence du modèle, top 10 villes
- **Carte interactive** : 30 villes avec marqueurs colorés (vert/jaune/rouge) et prix/m² au survol
- **Simulateur** : Prédiction de prix avec les paramètres réels du modèle
- **Pipeline ML** : Visualisation des hyperparamètres et métriques du modèle

---

## 🏗 Architecture

```
PROJET-ML-IMMOBILIER/
│
├── data/
│   ├── raw/                              # Données brutes (CSV scrapés)
│   ├── clean/                            # Données nettoyées pour le ML
│   └── processed/
│       └── immobilier.db                 # Base SQLite (schéma en étoile)
│
├── src/
│   ├── data/                             # Data Warehouse & Ingestion
│   │   ├── ingest_data.py                # Ingestion CSV → SQLite (tables de faits/dimensions)
│   │   ├── create_db.py                  # Création de la BDD (exécute init_db.sql)
│   │   └── create_datamarts.py           # Création des vues analytiques (Data Marts)
│   ├── features/                         # Traitement des données
│   │   ├── data_cleaner.py               # Nettoyage (doublons, normalisation, pseudonymisation)
│   │   ├── data_quality.py               # Contrôle qualité des données
│   │   └── feature_engineering.py        # Target encoding, one-hot, outliers
│   ├── models/                           # Machine Learning
│   │   ├── train_evaluate.py             # Entraînement XGBoost (régression + classification)
│   │   └── best_regression_model.joblib  # Meilleur modèle sauvegardé
│   ├── api/                              # API REST (FastAPI)
│   │   ├── main.py                       # App FastAPI (CORS, routing)
│   │   └── routes/
│   │       ├── __init__.py               # Routing config
│   │       ├── analytics.py              # Endpoints dashboard, analyse, carte, alertes
│   │       └── predict.py                # Endpoint simulation / prédiction
│   └── run_pipeline.py                   # Orchestrateur du pipeline complet
│
├── scripts/
│   └── sql/
│       ├── init_db.sql                   # Schéma en étoile (fact_ads + 4 dim tables)
│       └── datamarts/
│           └── create_datamarts.sql      # Vues analytiques (stats par ville, région, mois)
│
├── frontend/                             # Application Next.js 16
│   └── src/
│       ├── app/
│       │   ├── page.tsx                  # Dashboard principal
│       │   ├── globals.css               # Styles globaux + overrides Leaflet
│       │   ├── layout.tsx                # Layout racine (sidebar + contenu)
│       │   ├── analysis/page.tsx         # Analyse détaillée
│       │   ├── simulation/page.tsx       # Simulateur de prix
│       │   ├── map/page.tsx              # Carte interactive + alertes marchés
│       │   └── pipeline/page.tsx         # Métriques du pipeline ML
│       ├── components/
│       │   ├── layout/
│       │   │   └── Sidebar.tsx           # Navigation sidebar
│       │   └── ui/
│       │       ├── MapClient.tsx         # Carte Leaflet interactive (30 villes)
│       │       └── KpiCard.tsx           # Composant carte KPI réutilisable
│       └── lib/
│           ├── constants.ts              # Configuration (API URL)
│           └── utils.ts                  # Utilitaires
│
├── tests/                                # Tests unitaires (pytest)
│   ├── test_data_ingest.py
│   ├── test_data_cleaner.py
│   ├── test_data_quality.py
│   ├── test_feature_engineering.py
│   └── test_train_evaluate.py
│
├── saved_models/
│   └── kmeans.pickle                     # Modèle KMeans (segmentation)
│
├── Schema_BDD.pdf                        # Schéma de la base de données (documentation)
├── requirements.txt                      # Dépendances Python
└── README.md
```

---

## 🗄 Data Warehouse

Le projet intègre un **Data Warehouse** basé sur SQLite avec un schéma en étoile pour l'analyse structurée des données immobilières.

### Schéma en Étoile

```
                ┌──────────────┐
                │  dim_date    │
                │──────────────│
                │ id_date (PK) │
                │ created_at   │
                │ year, month  │
                │ day          │
                └──────┬───────┘
                       │
┌──────────────┐   ┌───┴───────────┐   ┌──────────────┐
│ dim_location │   │   fact_ads    │   │  dim_type    │
│──────────────│   │───────────────│   │──────────────│
│ id_location  │◄──│ id_annonce    │──►│ id_type (PK) │
│ city         │   │ price         │   │ type_name    │
│ zipcode      │   │ title         │   └──────────────┘
│ region       │   │ surface       │
└──────────────┘   │ price_m2      │   ┌──────────────┐
                   │ url           │   │ dim_author   │
                   │ image_url     │──►│──────────────│
                   │ id_date (FK)  │   │ id_author    │
                   │ id_location   │   └──────────────┘
                   │ id_type (FK)  │
                   │ id_author(FK) │
                   └───────────────┘
```

### Data Marts (Vues Analytiques)

| Vue | Description | Utilisation |
|-----|-------------|-------------|
| `dm_stats_par_ville` | Stats par ville (volume, prix moyen, surface, prix/m²) | Dashboard géographique |
| `dm_stats_region_type` | Stats par région × type de bien | Comparaison des marchés |
| `dm_stats_mensuelles` | Volume et prix moyens par mois | Suivi chronologique |

### Exécution

```bash
# 1. Créer la base de données (schéma en étoile)
cd src/data
python create_db.py

# 2. Ingérer les données CSV dans la BDD
python ingest_data.py

# 3. Créer les vues analytiques (Data Marts)
python create_datamarts.py
```

La base SQLite est sauvegardée dans `data/processed/immobilier.db`.

---

## 🛠 Installation

### Prérequis
- Python 3.10+
- Node.js 18+
- npm

### Backend (Python)

```bash
# Cloner le dépôt
git clone https://github.com/Bistrel2002/PROJET-ML-IMMOBILIER-.git
cd PROJET-ML-IMMOBILIER-

# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Installer les dépendances
pip install -r requirements.txt
```

### Frontend (Next.js)

```bash
cd frontend
npm install
```

---

## ▶️ Exécution

### 1. Lancer le pipeline de données

Transforme les données brutes (`data/raw/`) en données nettoyées (`data/clean/`) :

```bash
python src/run_pipeline.py
```

### 2. Entraîner le modèle

```bash
python src/models/train_evaluate.py
```

Le meilleur modèle est sauvegardé dans `src/models/best_regression_model.joblib`.

### 3. Démarrer le serveur API

```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

### 4. Démarrer le dashboard

```bash
cd frontend
npm run dev
```

Le dashboard est accessible sur **http://localhost:3000**.

---

## 🔬 Pipeline ML

Le pipeline est orchestré par `src/run_pipeline.py` et exécute les étapes suivantes :

| Étape | Module | Description |
|-------|--------|-------------|
| 1. Ingestion | `data/ingest_data.py` | Charge le CSV brut le plus récent |
| 2. Nettoyage | `features/data_cleaner.py` | Doublons, normalisation, pseudonymisation SHA-256 |
| 3. Qualité | `features/data_quality.py` | Validation des colonnes, types, valeurs manquantes |
| 4. Features | `features/feature_engineering.py` | Target encoding (villes), one-hot (types), outliers |
| 5. Entraînement | `models/train_evaluate.py` | XGBoost régression + classification, sauvegarde du meilleur |

### Feature Engineering

- **Target Encoding** : Les villes (haute cardinalité) sont encodées par la moyenne lissée du prix
- **One-Hot Encoding** : Les types de bien (Appartement, Maison, Terrain, Autre, Parking)
- **Outliers** : Suppression via IQR sur la surface et le prix
- **Extraction sémantique** : Le titre de l'annonce est analysé pour récupérer les pièces et le type de bien manquants

---

## 🌐 API Backend

FastAPI expose les endpoints suivants :

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/analytics/dashboard` | GET | KPIs, distribution des prix, marchés actifs |
| `/api/analytics/dashboard/options` | GET | Options des dropdowns (types, régions) |
| `/api/analytics/analysis` | GET | Stats par type, feature importance, top villes |
| `/api/analytics/analysis/options` | GET | Options des filtres (villes, pièces) |
| `/api/analytics/pipeline` | GET | Hyperparamètres XGBoost, métriques, split info |
| `/api/analytics/heatmap` | GET | 30 villes avec coordonnées, prix/m², tier de prix |
| `/api/analytics/invest-alerts` | GET | Top 5 marchés actifs vs médiane nationale |
| `/api/predict/options` | GET | Villes, types, bornes surface/pièces |
| `/api/predict/simulate` | POST | Prédiction de prix XGBoost |

### Filtres dynamiques

Les endpoints `/dashboard` et `/analysis` acceptent des paramètres de filtre :
- `type` : Type de bien (Tous, Appartement, Maison, Terrain, Autre, Parking)
- `region` : Région (France entière, Ile-de-France, Bretagne, etc.)
- `zone` : Ville spécifique
- `smin` / `smax` : Surface min/max
- `rooms` : Nombre de pièces

---

## 🖥 Dashboard Frontend

### Pages

| Page | Route | Contenu |
|------|-------|---------|
| **Dashboard** | `/` | KPIs (prix médian, nb annonces, MAE, R²), distribution des prix, marchés actifs |
| **Analyse** | `/analysis` | Prix par type de bien, facteurs d'influence XGBoost, top 10 villes |
| **Simulation** | `/simulation` | Formulaire de prédiction (ville, type, surface, pièces), projection à 2 ans |
| **Carte** | `/map` | Carte Leaflet avec 30 marqueurs colorés, top marchés actifs, légende |
| **Pipeline** | `/pipeline` | Hyperparamètres XGBoost, métriques de performance, info dataset |

### Carte Interactive

Les marqueurs sont colorés selon le prix/m² (terciles des données réelles) :
- 🟢 **Vert** : Villes abordables (tiers inférieur)
- 🟡 **Jaune** : Villes intermédiaires
- 🔴 **Rouge** : Villes les plus chères (tiers supérieur)

---

## 🧪 Tests

Exécuter tous les tests :

```bash
pytest tests/ -v
```

| Fichier | Couverture |
|---------|------------|
| `test_data_ingest.py` | Ingestion CSV, gestion des erreurs |
| `test_data_cleaner.py` | Nettoyage, doublons, normalisation |
| `test_data_quality.py` | Validation qualité, colonnes, types |
| `test_feature_engineering.py` | Target encoding, one-hot, outliers |
| `test_train_evaluate.py` | Entraînement, métriques, sauvegarde |

---

## 📈 Résultats du Modèle

### XGBoost Régression (meilleur modèle)

| Métrique | Valeur |
|----------|--------|
| **R²** | 0.7675 |
| **MAE** | 57 742 € |
| **RMSE** | 93 085 € |
| **Méthode** | prix_brut (prédiction directe) |

### Hyperparamètres

| Paramètre | Valeur |
|-----------|--------|
| `n_estimators` | 300 |
| `max_depth` | 7 |
| `learning_rate` | 0.1 |
| `subsample` | 0.8 |
| `colsample_bytree` | 0.8 |

### Feature Importance

| Feature | Importance |
|---------|-----------|
| Ville (Target Encoded) | 26.7% |
| Terrain (type) | 26.7% |
| Surface (m²) | 8.8% |
| Nb pièces | 8.5% |
| Maison (type) | 8.1% |

### XGBoost Classification

| Métrique | Valeur |
|----------|--------|
| **Accuracy** | ~89% |
| **Classes** | Bas / Moyen / Élevé |

---

## 📦 Données

### Source
Les données proviennent d'annonces immobilières scrapées (LeBonCoin, etc.) couvrant la France métropolitaine.

### Volume
- **~3 900 annonces** brutes
- **~3 586 annonces** après nettoyage
- **30+ villes** principales représentées
- **5 types de biens** : Appartement, Maison, Terrain, Autre, Parking

### Colonnes principales

| Colonne | Description |
|---------|-------------|
| `id` | Identifiant unique |
| `price` / `prix` | Prix du bien |
| `surface` | Surface en m² |
| `city` | Ville |
| `region` | Région |
| `type` | Type de bien |
| `pieces` | Nombre de pièces |
| `zipcode` | Code postal |

---

## 🔧 Stack Technique

| Composant | Technologie |
|-----------|-------------|
| **ML** | XGBoost, scikit-learn, pandas, numpy |
| **Backend** | FastAPI, uvicorn, Pydantic |
| **Frontend** | Next.js 16, React, Recharts, Leaflet |
| **Styling** | Tailwind CSS v4 |
| **Tests** | pytest |
| **Données** | CSV (pandas) |

---

## 👤 Auteurs

**Bistrel**

**Arash**

**Malo**

---

## 📄 Licence

Ce projet est développé dans un cadre académique.
