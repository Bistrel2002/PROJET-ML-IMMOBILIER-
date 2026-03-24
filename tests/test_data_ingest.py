import sys
import os
import unittest
from unittest.mock import patch
import pandas as pd

# Ajoute le dossier racine du projet au chemin de recherche Python 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.data_ingest import list_raw_files, raw_dataframe, get_latest_raw_dataframe

class TestDataIngest(unittest.TestCase):

    @patch('src.features.data_ingest.path.exists')
    @patch('src.features.data_ingest.listdir')
    def test_list_raw_files(self, mock_listdir, mock_exists):
        # Simule que le dossier data/raw/ existe bien
        mock_exists.return_value = True
        
        # Simule le contenu du dossier (avec des fichiers .csv et d'autres extensions)
        mock_listdir.return_value = ['2023-10-01_data.csv', '2023-10-05_data.csv', 'readme.txt', 'image.png']
        
        result = list_raw_files()
        
        # Vérifie qu'il ne renvoie QUE les .csv et qu'ils sont triés du plus récent au plus ancien (reverse=True)
        self.assertEqual(result, ['2023-10-05_data.csv', '2023-10-01_data.csv'])
        mock_exists.assert_called_once_with('data/raw/')
        mock_listdir.assert_called_once_with('data/raw/')

    @patch('src.features.data_ingest.path.exists')
    @patch('src.features.data_ingest.pd.read_csv')
    def test_raw_dataframe(self, mock_read_csv, mock_exists):
        # Simule que le chemin du fichier complet existe
        mock_exists.return_value = True
        
        # Simule le retour de pandas.read_csv pour ne pas avoir besoin d'un vrai fichier
        dummy_df = pd.DataFrame({'prix': [100000, 200000], 'ville': ['Paris', 'Lyon']})
        mock_read_csv.return_value = dummy_df

        # Exécute la fonction avec juste un nom de fichier (sans .csv et sans chemin)
        result = raw_dataframe('mon_fichier_test')
        
        # Vérifie que la fonction a bien ajouté le chemin data/raw/ et l'extension .csv
        # avant d'appeler pd.read_csv
        mock_read_csv.assert_called_once_with('data/raw/mon_fichier_test.csv', header=0, index_col=0)
        
        # Vérifie que le dataframe retourné est bien notre DataFrame simulé
        pd.testing.assert_frame_equal(result, dummy_df)

    @patch('src.features.data_ingest.raw_dataframe')
    @patch('src.features.data_ingest.list_raw_files')
    def test_get_latest_raw_dataframe(self, mock_list_raw_files, mock_raw_dataframe):
        # Simule la liste des fichiers renvoyés
        mock_list_raw_files.return_value = ['fichier_recent.csv', 'fichier_ancien.csv']
        
        # Simule le DataFrame qui sera chargé
        dummy_df = pd.DataFrame({'donnee': ['valeur']})
        mock_raw_dataframe.return_value = dummy_df
        
        result = get_latest_raw_dataframe()
        
        # Vérifie qu'il a bien appelé raw_dataframe avec le PREMIER élément de la liste (le plus récent)
        mock_raw_dataframe.assert_called_once_with('fichier_recent.csv')
        pd.testing.assert_frame_equal(result, dummy_df)

if __name__ == '__main__':
    print("==============================================")
    print(" Lancement de la suite de tests (data_ingest) ")
    print("==============================================")
    unittest.main(verbosity=2)
