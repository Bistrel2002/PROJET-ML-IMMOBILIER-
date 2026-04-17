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

import numpy as np
import pandas as pd
from pathlib import Path
from os import makedirs
from sklearn.cluster import KMeans
from pickle import dump, load

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
                        smoothing: int = 20) -> pd.DataFrame:
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
    with open(CITY_ENCODING_FILE, "wb") as f:
        dump(city_stats['smoothed'], f)
    return df


def encode_ville(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode la variable 'ville' en utilisant l'association générée par target_encode_ville.
    (à utiliser sur les nouvelles données)
    :param df: DataFrame pandas
    :return: DataFrame pandas
    """
    df = df.copy()
    with open(CITY_ENCODING_FILE, "rb") as f:
        city_code = load(f)
    df['ville'] = df['ville'].map(lambda city: city_code[city.upper()])
    return df


# =====================================================================
# 4c. Features dérivées
# =====================================================================
def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crée des colonnes dérivées utiles pour la modélisation :
    - prix_log  : log(1 + prix)  — réduit la dispersion
    """
    df = df.copy()
    df['prix_log'] = np.log1p(df['prix'])
    df ['surface_log'] = np.log1p(df['surface'])
    return df


# =====================================================================
# 4d. Suppression des colonnes non-prédictives
# =====================================================================
def drop_non_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Supprime les colonnes redondantes ou non-prédictives.
    """
    cols_to_drop = ['zipcode', 'region', 'agence', 'title']
    return df.drop(columns=[c for c in cols_to_drop if c in df.columns])


# =====================================================================
# 4e. Encodage des catégorielles
# =====================================================================
def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    One-hot encode les colonnes catégorielles restantes.
    """
    cat_cols = df.select_dtypes(
        include=['object', 'category', 'str']
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
    km.fit(df[cols_used])
    with open(KMEANS_FILE, 'wb') as f:
        dump(km, f, protocol=5)
    df["cluster"] = km.labels_
    return df


def predict_cluster(df: pd.DataFrame) -> pd.DataFrame:
    """
    Utilise le modèle de clustering sauvegardé pour prédire le cluster de nouvelles données.
    :param df: DataFrame pandas, les (nouvelles) données à cluster
    :return: DataFrame pandas, les données fournies avec les clusters dans une colonne supplémentaire (cluster)
    """
    df = df.copy()
    with open(KMEANS_FILE, 'rb') as f:
        km: KMeans = load(f)
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
    df = drop_non_features(df)
    df = encode_categoricals(df)
    if n_cluster and cluster_cols:
        df = train_clustering(df, n_cluster=n_cluster, cols_used=cluster_cols)
    else:
        df = train_clustering(df)
    return df
