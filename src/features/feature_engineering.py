"""
feature_engineering.py
---------------------
Step 4 of the pipeline — Prepares cleaned data for ML modelling.

Chains:
  remove_outliers → target_encode_ville → add_derived_features →
  drop_non_features → encode_categoricals

Input  : cleaned DataFrame from data_cleaner.clean_leboncoin_data()
Output : ML-ready DataFrame with only numeric columns
"""

import os
import tempfile
import shutil
import numpy as np
import pandas as pd
from pathlib import Path
from os import makedirs
from sklearn.cluster import KMeans
import joblib

def atomic_dump(obj, filename):
    """Saves an object to a file atomatically."""
    temp_dir = Path(filename).parent
    with tempfile.NamedTemporaryFile(dir=temp_dir, delete=False) as tf:
        joblib.dump(obj, tf.name)
        temp_name = tf.name
    shutil.move(temp_name, filename)

# Compute project root as two levels up from this file (src/features/ -> project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = str(PROJECT_ROOT / "saved_models")
CITY_ENCODING_FILE = str(Path(MODEL_DIR) / "city_encoding.pickle")
KMEANS_FILE = str(Path(MODEL_DIR) / "kmeans.pickle")
makedirs(MODEL_DIR, exist_ok=True)


# =====================================================================
# 4a. Suppression des outliers
# =====================================================================
def remove_outliers(df: pd.DataFrame, col: str = 'prix',
                    lower: float = 0.01, upper: float = 0.99) -> pd.DataFrame:
    """
    Supprime les lignes dont le prix est en dehors de l'intervalle
    [quantile(lower), quantile(upper)].
    """
    df = df.copy()
    q_lo = df[col].quantile(lower)
    q_hi = df[col].quantile(upper)
    before = len(df)
    df = df[(df[col] >= q_lo) & (df[col] <= q_hi)]
    print(f"  Outliers supprimés : {before - len(df)} lignes "
          f"(prix hors [{q_lo:.0f}, {q_hi:.0f}])")
    return df


# =====================================================================
# 4b. Target encoding pour 'ville' (haute cardinalité)
# =====================================================================
def target_encode_ville(df: pd.DataFrame, target_col: str = 'prix',
                        smoothing: int = 50) -> pd.DataFrame:
    """
    Encode la variable 'ville' en utilisant la moyenne lissée.
    Smoothing augmenté à 40 pour plus de stabilité.
    """
    df = df.copy()
    global_mean = df[target_col].mean()
    city_stats = df.groupby('ville')[target_col].agg(['mean', 'count'])
    city_stats['smoothed'] = (
        (city_stats['count'] * city_stats['mean'] + smoothing * global_mean)
        / (city_stats['count'] + smoothing)
    )
    df['ville'] = df['ville'].map(city_stats['smoothed'])
    atomic_dump(city_stats['smoothed'], CITY_ENCODING_FILE)
    return df


def encode_ville(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode la variable 'ville' en utilisant l'association générée par target_encode_ville.
    """
    df = df.copy()
    city_code = joblib.load(CITY_ENCODING_FILE)
    df['ville'] = df['ville'].map(lambda city: city_code[city.upper()])
    return df


# =====================================================================
# 4c. Features dérivées
# =====================================================================
def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crée des colonnes dérivées utiles pour la modélisation :
    - prix_log  : log(1 + prix)  — réduit la dispersion
    - surface_log : log(1 + surface)
    """
    df = df.copy()
    df['prix_log'] = np.log1p(df['prix'])
    df['surface_log'] = np.log1p(df['surface'])
    return df


# =====================================================================
# 4c-bis. Features temporelles
# =====================================================================
def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrait des features temporelles depuis la colonne 'created_at'.
    - annee       : année de la transaction (int)
    - mois        : mois (1–12)
    - trimestre   : trimestre (1–4)
    - annee_mois  : valeur continue (année + mois/12) pour capturer la tendance
    """
    df = df.copy()
    if 'created_at' not in df.columns:
        return df

    dt = pd.to_datetime(df['created_at'], errors='coerce')
    df['annee'] = dt.dt.year
    df['mois'] = dt.dt.month
    df['trimestre'] = dt.dt.quarter
    df['annee_mois'] = dt.dt.year + dt.dt.month / 12.0
    return df


# =====================================================================
# 4d. Suppression des colonnes non-prédictives
# =====================================================================
def drop_non_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Supprime les colonnes redondantes ou non-prédictives.
    """
    cols_to_drop = ['zipcode', 'region', 'agence', 'title', 'created_at']
    return df.drop(columns=[c for c in cols_to_drop if c in df.columns])


# =====================================================================
# 4e. Encodage des catégorielles
# =====================================================================
def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    One-hot encode les colonnes catégorielles restantes.
    """
    cat_cols = df.select_dtypes(
        include=['object', 'category']
    ).columns.tolist()
    if cat_cols:
        df = pd.get_dummies(df, columns=cat_cols, drop_first=False)
    return df


# =====================================================================
# 4f. Clustering
# =====================================================================
def train_clustering(df: pd.DataFrame, n_cluster: int = 8, cols_used: list = ["surface_log", "pieces", "type_bien_APPARTEMENT", "type_bien_MAISON", "type_bien_TERRAIN"]) -> pd.DataFrame:
    """
    Entraine le modèle de clustering (KMeans) et rajoute une colonne au DF avec le cluster de chaque ligne.
    :param df: DataFrame pandas, les données à cluster
    :param n_cluster: int, le nombre de cluster à identifier, 4 par défaut
    :param cols_used: list de str, la liste des variables à utiliser pour le clustering (n'utilisera pas les autres)
    :return: DataFrame pandas, les données fournies avec les clusters dans une colonne supplémentaire (cluster)
    """
    km = KMeans(n_clusters=n_cluster)
    df = df.copy()
    cluster_data = df[cols_used].fillna(0)
    km.fit(cluster_data)
    atomic_dump(km, KMEANS_FILE)
    df["cluster"] = km.labels_
    return df


def predict_cluster(df: pd.DataFrame) -> pd.DataFrame:
    """
    Utilise le modèle de clustering sauvegardé pour prédire le cluster de nouvelles données.
    """
    df = df.copy()
    km = joblib.load(KMEANS_FILE)
    labels = km.predict(df[km.feature_names_in_])
    df["cluster"] = labels
    return df


# =====================================================================
# Pipeline Step 4 : chaîne complète
# =====================================================================
def engineer_features(df: pd.DataFrame, n_cluster: int = None, cluster_cols: list = None) -> pd.DataFrame:
    """
    Step 4 of the pipeline — full feature engineering.
    """
    # Supprimer les lignes avec cibles manquantes
    if 'prix' in df.columns:
        df = df.dropna(subset=['prix'])

    df = remove_outliers(df)
    df = target_encode_ville(df)
    df = add_derived_features(df)
    df = add_temporal_features(df)
    df = drop_non_features(df)
    df = encode_categoricals(df)
    if n_cluster and cluster_cols:
        df = train_clustering(df, n_cluster=n_cluster, cols_used=cluster_cols)
    else:
        default_cols = ["surface_log", "pieces", "type_bien_APPARTEMENT", "type_bien_MAISON", "type_bien_TERRAIN"]
        available_cols = [c for c in default_cols if c in df.columns]
        if available_cols:
            df = train_clustering(df, cols_used=available_cols)
    return df
