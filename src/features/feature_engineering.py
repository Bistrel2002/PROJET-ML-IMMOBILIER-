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
# Pipeline Step 4 : chaîne complète
# =====================================================================
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
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
    return df
