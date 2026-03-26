import sys
import os
import unittest
import pandas as pd
import numpy as np

# Ajoute le dossier racine du projet au chemin de recherche Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.feature_engineering import (
    remove_outliers, 
    target_encode_ville,
    encode_ville,
    add_derived_features, 
    drop_non_features, 
    encode_categoricals,
    train_clustering,
    predict_cluster,
    engineer_features
)

def make_clean_df():
    return pd.DataFrame({
        "prix": [100000, 200000, 300000, 400000, 500000],
        "surface": [50.0, 60.0, 70.0, 80.0, 90.0],
        "pieces": [2.0, 3.0, 3.0, 4.0, 5.0],
        "ville": ["PARIS", "LYON", "PARIS", "LYON", "BORDEAUX"],
        "type_bien": ["APPARTEMENT", "MAISON", "APPARTEMENT", "MAISON", "APPARTEMENT"],
        "title": [
            "Bel appartement rénové", 
            "Maison avec jardin", 
            "Studio calme", 
            "Maison à rénover",
            "Appartement neuf"
        ]
    })

class TestFeatureEngineering(unittest.TestCase):

    def test_remove_outliers(self):
        df = pd.DataFrame({"prix": list(range(100))})
        result = remove_outliers(df, lower=0.1, upper=0.9)
        # Should keep roughly 80 rows
        self.assertTrue(len(result) < 100)
        self.assertEqual(result["prix"].min(), 10)
        # range(100) -> 0 to 99. Quantile 0.9 is 89.1. result max is 89.
        self.assertEqual(result["prix"].max(), 89)

    def test_add_derived_features(self):
        df = make_clean_df()
        result = add_derived_features(df)
        
        self.assertIn("prix_log", result.columns)
        self.assertTrue(pd.api.types.is_numeric_dtype(result["prix_log"]))

    def test_target_encode_ville(self):
        df = make_clean_df()
        result = target_encode_ville(df)
        # 'ville' should now be numeric (mean prices)
        self.assertTrue(pd.api.types.is_numeric_dtype(result["ville"]))
        
    def test_encode_ville(self):
        df = make_clean_df()
        result = encode_ville(df)
        compare = target_encode_ville(df)
        
        self.assertEqual(result["ville"][0], compare["ville"][0])

    def test_encode_categoricals(self):
        df = make_clean_df()
        # drop non features first to simulate real flow
        df = drop_non_features(df)
        result = encode_categoricals(df)
        
        self.assertIn("type_bien_APPARTEMENT", result.columns)
        self.assertIn("type_bien_MAISON", result.columns)
        # Check if type_bien_APPARTEMENT is present
        self.assertTrue("type_bien_APPARTEMENT" in result.columns)

    def test_train_clustering(self):
        df = make_clean_df()
        result = train_clustering(df, n_cluster=2, cols_used=["surface", "pieces"])
        
        self.assertIn("cluster", result.columns)
    
    def test_predict_cluster(self):
        df = make_clean_df()
        result = predict_cluster(df)
        
        self.assertIn("cluster", result.columns)

    def test_engineer_features_pipeline(self):
        df = make_clean_df()
        result = engineer_features(df, n_cluster=2, cluster_cols=["surface", "pieces"])
        
        # Final result should be all numeric
        for col in result.columns:
            self.assertTrue(pd.api.types.is_numeric_dtype(result[col]), f"Column {col} is not numeric")


if __name__ == "__main__":
    unittest.main()
