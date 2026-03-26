import pandas as pd
import numpy as np
import sys
import os
import unittest

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

class TestDataCleaner(unittest.TestCase):

    def test_manage_duplicates(self):
        df = pd.DataFrame({
            'id_annonce': ['1', '2', '2', '3'],
            'prix': [10, 20, 20, 30]
        })
        df_clean = manage_duplicates(df, id_col='id_annonce')
        self.assertEqual(len(df_clean), 3)
        self.assertEqual(df_clean['id_annonce'].tolist(), ['1', '2', '3'])

    def test_clean_numerical_columns(self):
        df = pd.DataFrame({
            'prix': ['150 000 €', '200000', ' 30.5 '],
            'surface': ['45 m²', '120m2', 'NaN']
        })
        df_clean = clean_numerical_columns(df, columns=['prix', 'surface'])
        self.assertEqual(df_clean['prix'].iloc[0], 150000.0)
        self.assertEqual(df_clean['surface'].iloc[0], 45.0)
        self.assertEqual(df_clean['surface'].iloc[1], 120.0)
        self.assertTrue(pd.isna(df_clean['surface'].iloc[2]))

    def test_normalize_text_columns(self):
        df = pd.DataFrame({
            'ville': [' Paris ', 'LYON', 'marseille '],
            'type_bien': ['Appartement ', 'maison', ' APPARTEMENT']
        })
        df_clean = normalize_text_columns(df, columns=['ville', 'type_bien'])
        self.assertEqual(df_clean['ville'].tolist(), ['PARIS', 'LYON', 'MARSEILLE'])
        self.assertEqual(df_clean['type_bien'].tolist(), ['APPARTEMENT', 'MAISON', 'APPARTEMENT'])

    def test_impute_missing_values(self):
        df = pd.DataFrame({
            'prix': [100000, np.nan, 200000], # Moyenne = 150000
        })
        df_clean = impute_missing_values(df, strategy='mean')
        self.assertEqual(df_clean['prix'].iloc[1], 150000.0)

    def test_hash_contact_names(self):
        df = pd.DataFrame({
            'agence': ['Agence A', np.nan]
        })
        df_clean = hash_contact_names(df, columns=['agence'])
        self.assertNotEqual(df_clean['agence'].iloc[0], 'Agence A')
        self.assertEqual(len(df_clean['agence'].iloc[0]), 64) # SHA-256
        self.assertTrue(pd.isna(df_clean['agence'].iloc[1]))

    def test_full_pipeline_with_pieces(self):
        raw_data = {
            'id': ['id_1', 'id_2'],
            'city': [' Paris ', 'LYON'],
            'type': ['Appartement ', 'maison'],
            'price': ['150 000 €', '350 000'],
            'surface': ['45 m²', '120m2'],
            'pieces': ['2', '4'],
            'author': ['Agence A', 'Agence B']
        }
        df = pd.DataFrame(raw_data)
        # On simule le renommage car clean_leboncoin_data() l'attend
        df_clean = clean_leboncoin_data(df)
        
        self.assertIn('pieces', df_clean.columns)
        self.assertEqual(df_clean['ville'].iloc[0], 'PARIS')

    def test_full_pipeline_without_pieces(self):
        """Vérifie que le pipeline fonctionne même si 'pieces' est absent."""
        raw_data = {
            'id': ['id_1', 'id_2'],
            'city': [' Paris ', 'LYON'],
            'type': ['Appartement ', 'maison'],
            'price': ['150 000 €', '350 000'],
            'surface': ['45 m²', '120m2'],
            'author': ['Agence A', 'Agence B']
        }
        df = pd.DataFrame(raw_data)
        df_clean = clean_leboncoin_data(df)
        
        self.assertNotIn('pieces', df_clean.columns)
        self.assertEqual(df_clean['ville'].iloc[0], 'PARIS')


if __name__ == "__main__":
    unittest.main()
