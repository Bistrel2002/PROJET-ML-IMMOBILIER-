import pandas as pd
import numpy as np
import hashlib

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
        'code_postal', 
        'agence'       
    ]

    # On garde seulement les colonnes présentes
    cols = [c for c in features_utiles if c in df.columns]
    return df[cols].copy()

def clean_leboncoin_data(df: pd.DataFrame, 
                         numeric_cols=['prix', 'surface', 'pieces'], 
                         text_cols=['ville', 'type_bien'],
                         hash_cols=['agence', 'contact'],
                         id_col='id_annonce') -> pd.DataFrame:
    """
    Pipeline principal qui enchaîne le nettoyage complet.
    """
    # 0. Sélectionner uniquement les traits utiles pour le ML
    df_clean = select_features(df)
    
    # 1. Tâche 3: Gérer les doublons
    df_clean = manage_duplicates(df_clean, id_col=id_col)
    
    # 2. Hachage des contacts pour pseudonymisation (SHA-256)
    df_clean = hash_contact_names(df_clean, columns=hash_cols)
    
    # 3. Tâche 1: Nettoyer les caractères spéciaux dans les nombres
    df_clean = clean_numerical_columns(df_clean, columns=numeric_cols)
    
    # 4. Tâche 2: Normaliser le texte
    df_clean = normalize_text_columns(df_clean, columns=text_cols)
    
    # 5. Tâche 4: Imputer les valeurs manquantes numériques par la moyenne
    df_clean = impute_missing_values(df_clean, strategy='mean')
    
    return df_clean