# Projet de Prédiction de l'Immobilier (ML)

Ce projet vise à développer une application capable de prédire les prix de l'immobilier (appartements et maisons) en utilisant des techniques de Machine Learning, basées sur des données scrapées.

## 🚀 Fonctionnalités
- **Pipeline de données complet** : Ingestion, nettoyage, gestion de la qualité et feature engineering.
- **Extraction sémantique** : Analyse des titres d'annonces pour extraire le nombre de pièces et le type de bien si manquants.
- **Modélisation XGBoost** : Entraînement de modèles performants pour la régression (prix) et la classification (segmentation de prix).
- **Optimisation** : Target encoding pour les villes et One-Hot encoding pour les types de biens.

## 🏗 Architecture du Projet
```text
/
├── data/
│   ├── raw/          # Données brutes (CSV)
│   └── clean/        # Données prêtes pour le ML
├── src/
│   ├── features/     # Logique de traitement des données
│   ├── models/       # Entraînement et évaluation des modèles
│   └── run_pipeline.py # Script principal d'exécution
├── requirements.txt  # Dépendances Python
└── README.md
```

## 🛠 Installation
1. Clonez le dépôt.
2. Créez un environnement virtuel : `python -m venv .venv`
3. Installez les dépendances : `pip install -r requirements.txt`

## 📊 Exécution

### 1. Lancer le pipeline de données
Prépare les données brutes en données nettoyées pour le ML :
```bash
python src/run_pipeline.py
```

### 2. Entraîner le modèle
Exécute l'entraînement XGBoost et sauvegarde le meilleur modèle :
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python src/models/train_evaluate.py
```

## 📈 Résultats Actuels (XGBoost)
*   **R² (Régression)** : **~0.77 - 0.79**
*   **Précision (Classification)** : **~89%**
*   **Meilleur Modèle** : Sauvegardé dans `src/models/best_regression_model.joblib`

## 🔑 Points Clés du Traitement
- **Sémantique** : Le titre de l'annonce est utilisé pour récupérer les infos manquantes (pièces, type de bien).
- **Target Encoding** : Les villes sont encodées via la moyenne lissée du prix pour gérer la haute cardinalité.
- **Flexibilité** : Le pipeline est capable de fonctionner même si certaines colonnes (comme `pieces`) sont absentes au départ.
