import pandas as pd
import numpy as np
import hashlib

# ---------------------------------------------------------------------------
# Step 3 — Column renaming: bridges raw CSV names → ML-ready names.
# Applied AFTER data_quality so quality checks can use the original names.
# ---------------------------------------------------------------------------
COLUMN_MAPPING = {
    "id":     "id_annonce",
    "title":  "title",
    "type":   "type_bien",
    "price":  "prix",
    "city":   "ville",
    "author": "agence",
    # 'surface', 'zipcode', 'region' keep their names
}

# Columns dropped after quality checks — not useful for ML
_COLUMNS_TO_DROP = [
    "category", "url", "image_url",
    "contact", "suspicious", "score",
    "created_at", "updated_at", "price_m2",
]

def manage_duplicates(df: pd.DataFrame, id_col: str = 'id_annonce') -> pd.DataFrame:
    """
    Tâche 3: Gérer les doublons basés sur l'identifiant technique de l'annonce.
    """
    df_cleaned = df.copy()
    if id_col in df_cleaned.columns:
        df_cleaned = df_cleaned.drop_duplicates(subset=[id_col], keep='first')
        
    return df_cleaned

def clean_numerical_columns(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
    """
    Tâche 1: Nettoyer les caractères spéciaux (€, m², espaces) dans les colonnes numériques.
    """
    df_cleaned = df.copy()
    if columns is None:
        columns = ['prix', 'surface'] 
        
    for col in columns:
        if col in df_cleaned.columns:
            # S'assurer de convertir en string pour le regex si c'est pas déjà un nombre pur
            s = df_cleaned[col].astype(str)
            
            # Enlever explicitement 'm2', 'm²' et '€' pour ne pas garder le '2' de 'm2'
            s = s.str.lower()
            s = s.str.replace('m2', '', regex=False)
            s = s.str.replace('m²', '', regex=False)
            s = s.str.replace('€', '', regex=False)
            
            s = s.str.replace(',', '.', regex=False)
            # Enlever tous les caractères qui ne sont pas des chiffres ou des points (ex: espaces)
            s = s.str.replace(r'[^\d.]', '', regex=True)
            
            # Convertir en numerique, les erreurs ou chaines vides deviennent NaN
            df_cleaned[col] = pd.to_numeric(s, errors='coerce')
                
    return df_cleaned

def normalize_text_columns(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
    """
    Tâche 2: Normaliser les noms de villes (Majuscules/Minuscules) et types de biens.
    """
    df_cleaned = df.copy()
    if columns is None:
        columns = ['ville', 'type_bien']
        
    for col in columns:
        if col in df_cleaned.columns:
            # Strip whitespace and convert to Upper case to standardise
            df_cleaned[col] = df_cleaned[col].astype(str).str.strip().str.upper()
            
    return df_cleaned

def impute_missing_values(df: pd.DataFrame, strategy: str = 'mean') -> pd.DataFrame:
    """
    Tâche 4: Gérer les valeurs manquantes (imputation par moyenne pour les colonnes numériques).
    """
    df_cleaned = df.copy()
    
    # Select numerical columns
    num_cols = df_cleaned.select_dtypes(include=[np.number]).columns
    
    for col in num_cols:
        if strategy == 'mean':
            mean_val = df_cleaned[col].mean()
            # If mean is nan (column completely empty), it just stays nan
            if not pd.isna(mean_val):
                df_cleaned[col] = df_cleaned[col].fillna(mean_val)
            
    return df_cleaned

def hash_contact_names(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
    """
    Hacher (SHA-256) les colonnes contenant des noms (ex: agence, contact) pour pseudonymisation.
    """
    df_cleaned = df.copy()
    if columns is None:
        columns = ['agence']
        
    for col in columns:
        if col in df_cleaned.columns:
            # On applique SHA-256 seulement sur les valeurs non nulles
            df_cleaned[col] = df_cleaned[col].apply(
                lambda x: hashlib.sha256(str(x).encode('utf-8')).hexdigest() if pd.notna(x) else x
            )
            
    return df_cleaned

def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renames raw CSV column names to ML-ready names using COLUMN_MAPPING,
    then drops columns that are irrelevant for ML.
    This is applied as step 0 of clean_leboncoin_data().
    """
    df_out = df.copy()
    mapping = {k: v for k, v in COLUMN_MAPPING.items() if k in df_out.columns}
    df_out = df_out.rename(columns=mapping)
    cols_to_drop = [c for c in _COLUMNS_TO_DROP if c in df_out.columns]
    df_out = df_out.drop(columns=cols_to_drop)
    return df_out


def select_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtrer les colonnes pour ne garder que celles utiles au Machine Learning,
    et supprimer les informations personnelles (PII) ou non pertinentes.
    """
    # Colonnes pertinentes pour prédire le prix + colonnes traçables pseudonymisées
    features_utiles = [
        'id_annonce',
        'prix',
        'surface',
        'pieces',
        'type_bien',
        'ville',
        'zipcode',
        'region',
        'agence',
    ]

    # On garde seulement les colonnes présentes
    cols = [c for c in features_utiles if c in df.columns]
    return df[cols].copy()

def clean_leboncoin_data(df: pd.DataFrame,
                         numeric_cols=None,
                         text_cols=None,
                         hash_cols=None,
                         id_col='id_annonce') -> pd.DataFrame:
    """
    Step 3 of the pipeline — full cleaning after data_quality.

    Chains:
      rename_columns → select_features → manage_duplicates →
      hash_contact_names → clean_numerical_columns →
      normalize_text_columns → impute_missing_values

    :param df: DataFrame from data_quality.data_quality()
    :return: clean, ML-ready DataFrame
    """
    if numeric_cols is None:
        numeric_cols = ['prix', 'surface', 'pieces']
    if text_cols is None:
        text_cols = ['ville', 'type_bien']
    if hash_cols is None:
        hash_cols = ['agence']

    # 0. Renommer les colonnes brutes → noms ML + supprimer les colonnes inutiles
    df_clean = rename_columns(df)

    # 1. Sélectionner uniquement les traits utiles pour le ML
    df_clean = select_features(df_clean)

    # 2. Gérer les doublons
    df_clean = manage_duplicates(df_clean, id_col=id_col)

    # 3. Hachage pour pseudonymisation (SHA-256)
    df_clean = hash_contact_names(df_clean, columns=hash_cols)

    # 4. Nettoyer les caractères spéciaux dans les nombres
    df_clean = clean_numerical_columns(df_clean, columns=numeric_cols)

    # 5. Normaliser le texte
    df_clean = normalize_text_columns(df_clean, columns=text_cols)

    # 6. Imputer les valeurs manquantes numériques par la moyenne
    df_clean = impute_missing_values(df_clean, strategy='mean')

    return df_clean