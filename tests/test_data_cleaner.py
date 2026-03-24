import pandas as pd
import numpy as np
import sys
import os

# Ajoute le dossier racine du projet au chemin de recherche Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.data_cleaner import (
    manage_duplicates, 
    clean_numerical_columns, 
    normalize_text_columns, 
    impute_missing_values,
    hash_contact_names,
    select_features,
    clean_leboncoin_data
)

def test_manage_duplicates():
    df = pd.DataFrame({
        'id_annonce': ['1', '2', '2', '3'],
        'prix': [10, 20, 20, 30]
    })
    df_clean = manage_duplicates(df, id_col='id_annonce')
    assert len(df_clean) == 3
    assert df_clean['id_annonce'].tolist() == ['1', '2', '3']

def test_clean_numerical_columns():
    df = pd.DataFrame({
        'prix': ['150 000 €', '200000', ' 30.5 '],
        'surface': ['45 m²', '120m2', 'NaN']
    })
    df_clean = clean_numerical_columns(df, columns=['prix', 'surface'])
    assert df_clean['prix'].iloc[0] == 150000.0
    assert df_clean['surface'].iloc[0] == 45.0
    assert df_clean['surface'].iloc[1] == 120.0
    assert pd.isna(df_clean['surface'].iloc[2])

def test_normalize_text_columns():
    df = pd.DataFrame({
        'ville': [' Paris ', 'LYON', 'marseille '],
        'type_bien': ['Appartement ', 'maison', ' APPARTEMENT']
    })
    df_clean = normalize_text_columns(df, columns=['ville', 'type_bien'])
    assert df_clean['ville'].tolist() == ['PARIS', 'LYON', 'MARSEILLE']
    assert df_clean['type_bien'].tolist() == ['APPARTEMENT', 'MAISON', 'APPARTEMENT']

def test_impute_missing_values():
    df = pd.DataFrame({
        'prix': [100000, np.nan, 200000], # Moyenne = 150000
    })
    df_clean = impute_missing_values(df, strategy='mean')
    assert df_clean['prix'].iloc[1] == 150000.0

def test_hash_contact_names():
    df = pd.DataFrame({
        'agence': ['Agence A', np.nan]
    })
    df_clean = hash_contact_names(df, columns=['agence'])
    assert df_clean['agence'].iloc[0] != 'Agence A'
    assert len(df_clean['agence'].iloc[0]) == 64 # SHA-256 length
    assert pd.isna(df_clean['agence'].iloc[1])

def test_select_features():
    df = pd.DataFrame({
        'id_annonce': ['1'],
        'prix': [100],
        'email': ['test@test.com'], # PII
        'telephone': ['06000000']   # PII
    })
    df_clean = select_features(df)
    assert 'email' not in df_clean.columns
    assert 'telephone' not in df_clean.columns
    assert 'prix' in df_clean.columns

def test_full_pipeline():
    raw_data = {
        'id_annonce': ['id_1', 'id_2', 'id_3', 'id_3'],
        'ville': [' Paris ', 'LYON', 'marseille', 'marseille'],
        'type_bien': ['Appartement ', 'maison', ' APPARTEMENT', ' APPARTEMENT'],
        'prix': ['150 000 €', '350 000.5', '120 000 €', '120 000 €'],
        'surface': ['45 m²', '120m2', ' 30.5 m² ', ' 30.5 m² '],
        'pieces': ['2 pièces', '4', '1', '1'],
        'email': ['test@test.com', 'a@b.com', 'c@d.com', 'c@d.com'],
        'agence': ['Agence A', 'Agence B', 'Agence C', 'Agence C']
    }
    df = pd.DataFrame(raw_data)
    df_clean = clean_leboncoin_data(df)
    
    # Check duplicate removed
    assert len(df_clean) == 3
    
    # Check PII removed
    assert 'email' not in df_clean.columns
    
    # Check cleaning
    assert isinstance(df_clean['prix'].iloc[0], float)
    assert df_clean['ville'].iloc[0] == 'PARIS'
    assert len(df_clean['agence'].iloc[0]) == 64
