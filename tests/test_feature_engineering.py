import sys
import os
import unittest
import pandas as pd

# Ajoute le dossier racine du projet au chemin de recherche Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.feature_engineering import FEATURES, feature_selection, clustering

dummy_df = pd.DataFrame({
	"title": ["Test appartement 40 m²"],
	"city": ["test city"],
	"type": ["test"],
	"price": [2000],
	"price_m2": [200.0],
	"surface": [10.0],
	"zipcode": ["12345"],
	"region": ["test region"],
	"author": ["test author"],
	"score": [5],
	"created_at": ["2024-03-25"],
	"updated_at": ["2024-03-25"],
})


class TestFeatureEngineering(unittest.TestCase):
	def test_feature_selection(self):
		df = dummy_df.copy()
		
		df = feature_selection(df)
		assert isinstance(df, pd.DataFrame)
		assert (df.columns == FEATURES).all()
	
	def test_clustering(self):
		df = dummy_df.copy()
		
		df = clustering(df, n_clusters=1)
		assert isinstance(df, pd.DataFrame)
		assert "cluster" in df.columns


if __name__ == "__main__":
	print("======================================================")
	print(" Lancement de la suite de tests (feature_engineering) ")
	print("======================================================")
	unittest.main(verbosity=2)