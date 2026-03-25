import sys
import os
import unittest
import pandas as pd

# Ajoute le dossier racine du projet au chemin de recherche Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.data_quality import extract_m2, validate_constraints, data_quality


# ---------------------------------------------------------------------------
# DataFrame simulant la sortie de data_ingest.load_raw() (colonnes brutes)
# ---------------------------------------------------------------------------
def make_raw_df():
    return pd.DataFrame({
        "id":      [1, 2, 3],
        "title":   ["Appartement 40 m²", "Maison 100 m²", "Studio 20 m²"],
        "type":    ["Appartement", "Maison", "Studio"],
        "price":   [80000, 250000, 45000],
        "city":    ["Paris", "Lyon", "Bordeaux"],
        "surface": [float("nan"), 100.0, float("nan")],  # partiellement rempli
    })


class TestDataQuality(unittest.TestCase):

    def test_extract_m2_uses_existing_surface(self):
        """La surface existante (non-NaN) doit être conservée, pas écrasée."""
        df = make_raw_df()
        result = extract_m2(df)
        # Row 1 has surface=100 in the CSV — must not be overwritten
        self.assertEqual(result.loc[1, "surface"], 100.0)

    def test_extract_m2_fills_missing_from_title(self):
        """La surface manquante doit être extraite du titre."""
        df = make_raw_df()
        result = extract_m2(df)
        # Row 0: title "Appartement 40 m²" → surface should be 40
        self.assertEqual(result.loc[0, "surface"], 40.0)
        # Row 2: title "Studio 20 m²" → surface should be 20
        self.assertEqual(result.loc[2, "surface"], 20.0)

    def test_extract_m2_adds_price_m2(self):
        """price_m2 doit être calculé et présent après extract_m2."""
        df = make_raw_df()
        result = extract_m2(df)
        self.assertIn("surface", result.columns)
        self.assertIn("price_m2", result.columns)
        self.assertTrue(pd.api.types.is_float_dtype(result["surface"]))

    def test_validate_constraints_filters_invalid_rows(self):
        """Les lignes avec price ≤ 0, surface ≤ 0, ou price_m2 ≥ 50 000 doivent être supprimées."""
        df = pd.DataFrame({
            "type":     ["Maison", "Appart", "Villa"],
            "price":    [250000,   -1000,    200000],
            "city":     ["Paris",  "Lyon",   "Nice"],
            "surface":  [100.0,    80.0,     0.0],    # surface=0 → invalide
            "price_m2": [2500.0,   1000.0,   60000.0],  # price_m2 ≥ 50 000 → invalide
        })
        result = validate_constraints(df)
        # Only the first row should survive
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["city"], "Paris")

    def test_validate_constraints_keeps_valid_rows(self):
        """Les lignes valides ne doivent pas être supprimées."""
        df = pd.DataFrame({
            "type":     ["Maison"],
            "price":    [200000],
            "city":     ["Paris"],
            "surface":  [80.0],
            "price_m2": [2500.0],
        })
        result = validate_constraints(df)
        self.assertEqual(len(result), 1)

    def test_data_quality_pipeline(self):
        """Le pipeline complet data_quality() doit retourner uniquement les lignes valides."""
        df = make_raw_df()
        result = data_quality(df)
        # All 3 rows in make_raw_df() are valid — all should remain
        self.assertEqual(len(result), 3)
        self.assertIn("surface", result.columns)
        self.assertIn("price_m2", result.columns)
        # Original raw column names must still be present (renaming belongs to data_cleaner)
        self.assertIn("type", result.columns)
        self.assertIn("price", result.columns)
        self.assertIn("city", result.columns)


if __name__ == "__main__":
    print("==============================================")
    print(" Lancement de la suite de tests (data_quality) ")
    print("==============================================")
    unittest.main(verbosity=2)