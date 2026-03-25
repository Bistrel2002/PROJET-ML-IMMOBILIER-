import sys
import os
import unittest
from unittest.mock import patch
import pandas as pd

# Ajoute le dossier racine du projet au chemin de recherche Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.data_ingest import get_latest_raw_dataframe
from src.features.data_quality import extract_m2, validate_constraints

dummy_df = pd.DataFrame({
	"title": ["Test appartement 40 m²"],
	"city": ["test city"],
	"type": ["test"],
	"price": [2000],
})


class TestDataQuality(unittest.TestCase):
	@patch("src.features.data_ingest.get_latest_raw_dataframe")
	def test_extract_m2(self, mock_get_latest_raw_dataframe):
		mock_get_latest_raw_dataframe.return_value = dummy_df
		
		df = get_latest_raw_dataframe()
		assert "surface" not in df.columns
		assert "price_m2" not in df.columns
		
		df = extract_m2(df)
		assert "surface" in df.columns
		assert "price_m2" in df.columns
		assert df["surface"].dtype == "float64"
		assert df["price_m2"].dtype == "float64"
	
	@patch("src.features.data_ingest.get_latest_raw_dataframe")
	def test_validate_constraints(self, mock_get_latest_raw_dataframe):
		mock_get_latest_raw_dataframe.return_value = dummy_df
		
		df = extract_m2(get_latest_raw_dataframe())
		df = validate_constraints(df)
		assert df["city"].isna().sum() == 0
		assert df["type"].isna().sum() == 0
		assert (df["price"] <= 0).sum() == 0
		assert (df["surface"] <= 0).sum() == 0
		assert (df["price_m2"] >= 50000).sum() == 0


if __name__ == "__main__":
	print("==============================================")
	print(" Lancement de la suite de tests (data_quality) ")
	print("==============================================")
	unittest.main(verbosity=2)