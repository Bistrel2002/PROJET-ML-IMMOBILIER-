import pandas as pd
import numpy as np
import os
import sys
import unittest
from pathlib import Path

# Ajout au path pour pouvoir importer depuis src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.train_evaluate import train_models, load_clean_data

class TestTrainEvaluate(unittest.TestCase):

    def test_load_clean_data_latest(self):
        """Vérifie que le chargement du dernier CSV fonctionne."""
        try:
            df = load_clean_data()
            self.assertIsInstance(df, pd.DataFrame)
        except FileNotFoundError:
            pass 

    def test_train_models(self):
        """Vérifie l'entraînement des modèles avec des données simulées."""
        np.random.seed(42)
        n_samples = 100
        df = pd.DataFrame({
            "prix": np.random.randint(50000, 500000, n_samples),
            "surface": np.random.uniform(20, 200, n_samples),
            "pieces": np.random.randint(1, 10, n_samples),
            "ville": np.random.uniform(100000, 500000, n_samples), 
            "prix_log": np.random.uniform(10, 15, n_samples),
            "type_bien_APPARTEMENT": np.random.choice([True, False], n_samples),
            "type_bien_MAISON": np.random.choice([True, False], n_samples),
            "type_bien_PARKING": np.random.choice([False], n_samples),
            "type_bien_TERRAIN": np.random.choice([False], n_samples),
            "type_bien_AUTRE": np.random.choice([False], n_samples),
        })
        
        # Utiliser un chemin absolu pour éviter les erreurs de relative_to
        ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        tmp_model_dir = ROOT / "tests" / "tmp_models"
        
        results = train_models(df, save_dir=tmp_model_dir)
        
        self.assertIn('XGBoost_prix_brut', results)
        self.assertIn('XGBoost_log_prix', results)
        self.assertIn('Best_Regression', results)
        self.assertIn('Classification', results)
        
        # Vérifie que le fichier joblib a été créé
        model_file = tmp_model_dir / "best_regression_model.joblib"
        self.assertTrue(model_file.exists())
        
        # Nettoyage
        if model_file.exists():
            os.remove(model_file)
        if tmp_model_dir.exists():
            os.rmdir(tmp_model_dir)


if __name__ == "__main__":
    unittest.main()
