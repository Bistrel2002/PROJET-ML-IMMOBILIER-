import pandas as pd
import numpy as np
import os
import sys

# Ajout au path pour pouvoir importer depuis src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.train_evaluate import load_and_prepare_data, train_models
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

def test_load_and_prepare_data():
    df = pd.DataFrame({
        'id_annonce': ['1', '2'],
        'prix': [100000, 200000],
        'surface': [50, 100],
        'type_bien': ['APPARTEMENT', 'MAISON'],
        'agence': ['A', 'B']
    })
    
    df_prepared = load_and_prepare_data(df)
    
    # Vérifie que les colonnes indésirables sont supprimées
    assert 'id_annonce' not in df_prepared.columns
    assert 'agence' not in df_prepared.columns
    
    # Vérifie l'encodage catégoriel
    assert 'type_bien' not in df_prepared.columns
    # type_bien_MAISON devrait exister parce que drop_first=True supprime APPARTEMENT (c'est le premier alphabétiquement s'il est de base)
    # L'action exacte de pd.get_dummies peut varier, mais elle créera certainement une nouvelle colonne
    assert any([col.startswith('type_bien_') for col in df_prepared.columns])
    
    assert 'prix' in df_prepared.columns

def test_train_models(tmp_path):
    # Création de fausses données propres avec suffisamment de lignes
    np.random.seed(42)
    n_samples = 50
    df = pd.DataFrame({
        'prix': np.random.randint(50000, 500000, n_samples),
        'surface': np.random.randint(20, 200, n_samples),
        'pieces': np.random.randint(1, 10, n_samples),
        'type_bien': np.random.choice(['APPARTEMENT', 'MAISON'], n_samples)
    })
    
    save_dir = str(tmp_path / "models")
    
    results = train_models(df, save_dir=save_dir)
    
    # Vérifie que les métriques de régression sont dans les résultats
    assert 'Regression_Unnormalized' in results
    assert 'MAE' in results['Regression_Unnormalized']
    assert 'RMSE' in results['Regression_Unnormalized']
    assert 'R2' in results['Regression_Unnormalized']
    
    # Vérifie que les métriques de classification sont dans les résultats
    assert 'Classification_Unnormalized' in results
    assert 'Accuracy' in results['Classification_Unnormalized']
    assert 'F1' in results['Classification_Unnormalized']
    
    # Vérifie que le meilleur modèle a été sauvegardé
    assert os.path.exists(os.path.join(save_dir, 'best_regression_model.joblib'))


