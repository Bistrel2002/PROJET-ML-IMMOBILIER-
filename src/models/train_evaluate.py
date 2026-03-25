import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics import accuracy_score, f1_score

import sys

# On suppose que ces imports fonctionnent. On utilise try/except pour rendre le script robuste
# au cas où on l'exécute de façon isolée si les données sont fournies.
try:
    # Ajout au path pour pouvoir importer depuis src en exécutant directement ce fichier
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from src.data_ingest import get_latest_raw_dataframe
    from src.features.data_cleaner import clean_leboncoin_data
except ImportError as e:
    print(f"ImportError: {e}")
    pass

def load_and_prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prépare les données nettoyées pour la modélisation (encodage des variables catégorielles et suppression des colonnes inutiles)."""
    # Exclure les colonnes inutiles pour l'entraînement si elles existent encore
    cols_to_drop = ['id_annonce', 'agence', 'contact']
    df_model = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    
    # Supprimer les lignes où les cibles "prix" ou "type_bien" sont manquantes pour éviter les erreurs
    if 'prix' in df_model.columns:
        df_model = df_model.dropna(subset=['prix'])
    if 'type_bien'in df_model.columns:
        df_model = df_model.dropna(subset=['type_bien'])
        
    # Encodage des caractéristiques catégorielles
    cat_columns = df_model.select_dtypes(include=['object', 'category']).columns
    df_model = pd.get_dummies(df_model, columns=cat_columns, drop_first=True)
    return df_model

def evaluate_regression(model, X_test, y_test):
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)
    return {'MAE': mae, 'RMSE': rmse, 'R2': r2}

def evaluate_classification(model, X_test, y_test):
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    # Utilisation de "weighted" en cas de multi-classes ou de déséquilibre
    f1 = f1_score(y_test, predictions, average='weighted')
    return {'Accuracy': accuracy, 'F1': f1}

def train_models(df: pd.DataFrame, save_dir='src/models/'):
    """
    Entraîne les modèles de régression (prix) et de classification (type_bien).
    Normalise les données pour comparer les performances.
    Sauvegarde le meilleur modèle de régression.
    """
    df_prepared = load_and_prepare_data(df)
    
    results = {}
    
    # ---------------------------------------------------------
    # Régression : Prédire le 'prix'
    # ---------------------------------------------------------
    if 'prix' in df_prepared.columns and len(df_prepared) > 10:
        X_reg = df_prepared.drop(columns=['prix'])
        y_reg = df_prepared['prix']
        
        X_reg_train, X_reg_test, y_reg_train, y_reg_test = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)
        
        # Sans normalisation
        reg_model = RandomForestRegressor(n_estimators=50, random_state=42)
        reg_model.fit(X_reg_train, y_reg_train)
        reg_metrics = evaluate_regression(reg_model, X_reg_test, y_reg_test)
        
        # Avec normalisation
        scaler = StandardScaler()
        X_reg_train_scaled = scaler.fit_transform(X_reg_train)
        X_reg_test_scaled = scaler.transform(X_reg_test)
        
        reg_model_scaled = RandomForestRegressor(n_estimators=50, random_state=42)
        reg_model_scaled.fit(X_reg_train_scaled, y_reg_train)
        reg_metrics_scaled = evaluate_regression(reg_model_scaled, X_reg_test_scaled, y_reg_test)
        
        results['Regression_Unnormalized'] = reg_metrics
        results['Regression_Normalized'] = reg_metrics_scaled
        
        # Sauvegarder le meilleur modèle de régression basé sur le score R2
        best_model = reg_model if reg_metrics['R2'] > reg_metrics_scaled['R2'] else reg_model_scaled
        best_r2 = max(reg_metrics['R2'], reg_metrics_scaled['R2'])
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        joblib.dump(best_model, os.path.join(save_dir, 'best_regression_model.joblib'))
        results['Best_Regression_R2'] = best_r2
    
    # ---------------------------------------------------------
    # Classification : La cible pourrait être une catégorie de prix ou un 'type_bien'
    # Ici, nous prédisons si le prix est "Au-dessus de la médiane" comme une simple 
    # tâche de classification binaire pour répondre à l'exigence de classification.
    # ---------------------------------------------------------
    if 'prix' in df_prepared.columns and len(df_prepared) > 10:
        median_price = df_prepared['prix'].median()
        y_clf = (df_prepared['prix'] > median_price).astype(int)
        X_clf = df_prepared.drop(columns=['prix'])
        
        X_clf_train, X_clf_test, y_clf_train, y_clf_test = train_test_split(X_clf, y_clf, test_size=0.2, random_state=42)
        
        # Sans normalisation
        clf_model = RandomForestClassifier(n_estimators=50, random_state=42)
        clf_model.fit(X_clf_train, y_clf_train)
        clf_metrics = evaluate_classification(clf_model, X_clf_test, y_clf_test)
        
        # Avec normalisation
        scaler_clf = StandardScaler()
        X_clf_train_scaled = scaler_clf.fit_transform(X_clf_train)
        X_clf_test_scaled = scaler_clf.transform(X_clf_test)
        
        clf_model_scaled = RandomForestClassifier(n_estimators=50, random_state=42)
        clf_model_scaled.fit(X_clf_train_scaled, y_clf_train)
        clf_metrics_scaled = evaluate_classification(clf_model_scaled, X_clf_test_scaled, y_clf_test)
        
        results['Classification_Unnormalized'] = clf_metrics
        results['Classification_Normalized'] = clf_metrics_scaled
        
    return results

if __name__ == '__main__':
    print("Chargement des données en cours...")
    # Ceci essaie d'exécuter l'ensemble du pipeline de bout-en-bout si les données existent
    try:
        raw_df = get_latest_raw_dataframe()
        clean_df = clean_leboncoin_data(raw_df)
        print("Entraînement des modèles en cours...")
        res = train_models(clean_df)
        for k, v in res.items():
            print(f"{k}: {v}")
    except Exception as e:
        print(f"Impossible d'exécuter le pipeline de bout-en-bout : {e}")
