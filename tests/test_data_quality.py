import sys
import os
import unittest
import pandas as pd
import numpy as np

# Ajoute le dossier racine du projet au chemin de recherche Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.data_quality import extract_m2, validate_constraints, data_quality


# ---------------------------------------------------------------------------
# DataFrame simulant la sortie de data_ingest.load_raw() (colonnes brutes)
# ---------------------------------------------------------------------------
def make_raw_df():
    return pd.DataFrame({
        "id":      [1, 2, 3, 4, 5],
        "title":   [
            "Appartement 4 pièces 90 m²", 
            "Maison rénovée avec jardin", 
            "T3 au centre ville", 
            "Vente place de parking",
            "Terrain constructible 500m2"
        ],
        "type":    ["Appartement", "Autre", "Autre", "Autre", "Terrain"],
        "price":   [130000, 400000, 200000, 15000, 50000],
        "city":    ["Aubenas", "Mérignies", "Lyon", "Paris", "Nice"],
        "surface": [float("nan"), 150.0, float("nan"), float("nan"), float("nan")],
        "pieces":  [float("nan"), float("nan"), float("nan"), float("nan"), float("nan")]
    })


class TestDataQuality(unittest.TestCase):

    def test_extract_m2_fills_surface_from_title(self):
        """La surface manquante doit être extraite du titre."""
        df = make_raw_df()
        result = extract_m2(df)
        # Row 0: "90 m²"
        self.assertEqual(result.iloc[0]["surface"], 90.0)
        # Row 4: "500m2"
        self.assertEqual(result.iloc[4]["surface"], 500.0)

    def test_extract_pieces_from_title(self):
        """Le nombre de pièces doit être extrait du titre (4 pièces, T3, etc.)."""
        df = make_raw_df()
        result = extract_m2(df)
        # Row 0: "4 pièces"
        self.assertEqual(result.iloc[0]["pieces"], 4.0)
        # Row 2: "T3"
        self.assertEqual(result.iloc[2]["pieces"], 3.0)

    def test_extract_type_from_title(self):
        """Le type de bien doit être déduit du titre si manquant ou 'Autre'."""
        df = make_raw_df()
        result = extract_m2(df)
        # Row 1: title contains "Maison" -> type should become Maison
        self.assertEqual(result.iloc[1]["type"], "Maison")
        # Row 3: title contains "parking" -> type should become Parking
        self.assertEqual(result.iloc[3]["type"], "Parking")

    def test_validate_constraints_filters_invalid_rows(self):
        """Les lignes avec des données aberrantes doivent être supprimées."""
        df = pd.DataFrame({
            "type":     ["Maison", "Appartement"],
            "price":    [0, 200000], # Prix 0 invalide
            "city":     ["Paris", "Lyon"],
            "surface":  [100.0, 50.0],
            "price_m2": [0.0, 4000.0]
        })
        result = validate_constraints(df)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["city"], "Lyon")

    def test_data_quality_full_pipeline(self):
        """Le pipeline complet doit extraire les données et filtrer les lignes."""
        df = make_raw_df()
        result = data_quality(df)
        # Seules les lignes avec surface extraite (0, 1, 4) sont gardées.
        # Les lignes 2 et 3 n'ont pas de surface mentionnée -> dropped.
        self.assertEqual(len(result), 3)
        self.assertTrue("price_m2" in result.columns)


if __name__ == "__main__":
    unittest.main()
