"""
train_evaluate.py
-----------------
Loads the ML-ready CSV from data/clean/ (produced by run_pipeline.py)
and trains XGBoost models for regression and classification.

No feature engineering happens here — that is handled by
features/feature_engineering.py via the pipeline.
"""

import json
import numpy as np
import pandas as pd
import joblib
import sys
from pathlib import Path
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor, XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics import accuracy_score, f1_score

# Project root (two levels up from src/models/)
ROOT = Path(__file__).resolve().parent.parent.parent
CLEAN_DIR = ROOT / "data" / "clean"
MODEL_DIR = Path(__file__).resolve().parent


# =====================================================================
# Chargement des données ML-ready
# =====================================================================
def load_clean_data(filepath: str = None) -> pd.DataFrame:
    """
    Charge le CSV ML-ready produit par run_pipeline.py depuis data/clean/.
    Si aucun chemin n'est fourni, utilise le fichier le plus récent.
    """
    if filepath:
        return pd.read_csv(filepath, index_col=0)

    csv_files = sorted(CLEAN_DIR.glob("*.csv"), reverse=True)
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV found in {CLEAN_DIR}. Run 'python src/run_pipeline.py' first."
        )
    latest = csv_files[0]
    print(f"Loading ML-ready data from: {latest.relative_to(ROOT)}")
    return pd.read_csv(latest, index_col=0)


# =====================================================================
# Fonctions d'évaluation
# =====================================================================
def evaluate_regression(model, X_test, y_test, use_log=False):
    """Évalue un modèle de régression. Si use_log, reconvertit les prédictions."""
    predictions = model.predict(X_test)
    if use_log:
        predictions = np.expm1(predictions)
        y_test = np.expm1(y_test)
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)
    return {'MAE': round(mae, 2), 'RMSE': round(rmse, 2), 'R2': round(r2, 4)}


def evaluate_classification(model, X_test, y_test):
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    f1 = f1_score(y_test, predictions, average='weighted')
    return {'Accuracy': round(accuracy, 4), 'F1': round(f1, 4)}


# =====================================================================
# Entraînement des modèles
# =====================================================================
def train_models(df: pd.DataFrame, save_dir: str = None):
    """
    Entraîne les modèles XGBoost de régression et de classification.
    """
    results = {}

    # ---------------------------------------------------------
    # Régression : Prédire le 'prix' avec XGBoost
    # ---------------------------------------------------------
    if 'prix' in df.columns and len(df) > 10:

        # --- A. Régression sur prix brut ---
        X_reg = df.drop(columns=['prix', 'prix_log'])
        y_reg = df['prix']

        X_reg_train, X_reg_test, y_reg_train, y_reg_test = train_test_split(
            X_reg, y_reg, test_size=0.2, random_state=42
        )

        reg_model = XGBRegressor(
            n_estimators=200, learning_rate=0.1, max_depth=7,
            subsample=0.8, colsample_bytree=0.8, random_state=42
        )
        reg_model.fit(X_reg_train, y_reg_train)
        reg_metrics = evaluate_regression(reg_model, X_reg_test, y_reg_test)
        results['XGBoost_prix_brut'] = reg_metrics

        # --- B. Régression sur log(prix) ---
        y_reg_log = df['prix_log']
        X_log_train, X_log_test, y_log_train, y_log_test = train_test_split(
            X_reg, y_reg_log, test_size=0.2, random_state=42
        )

        reg_model_log = XGBRegressor(
            n_estimators=300, learning_rate=0.1, max_depth=7,
            subsample=0.8, colsample_bytree=0.8, random_state=42
        )
        reg_model_log.fit(X_log_train, y_log_train)
        reg_metrics_log = evaluate_regression(
            reg_model_log, X_log_test, y_log_test, use_log=True
        )
        results['XGBoost_log_prix'] = reg_metrics_log

        # --- Sauvegarder le meilleur modèle ---
        if reg_metrics['R2'] > reg_metrics_log['R2']:
            best_model, best_r2, best_label = reg_model, reg_metrics['R2'], "prix_brut"
        else:
            best_model, best_r2, best_label = reg_model_log, reg_metrics_log['R2'], "log_prix"

        _save_dir = Path(save_dir) if save_dir else MODEL_DIR
        _save_dir.mkdir(parents=True, exist_ok=True)
        model_path = _save_dir / 'best_regression_model.joblib'
        joblib.dump(best_model, model_path)
        print(f"\n  ✓ Best model ({best_label}) saved → {model_path.relative_to(ROOT)}")
        results['Best_Regression'] = {'R2': best_r2, 'method': best_label}
        results['model_path'] = str(model_path)

        # Save metrics to JSON for the API to read dynamically
        best_metrics = reg_metrics if best_label == 'prix_brut' else reg_metrics_log
        metrics_path = _save_dir / 'metrics.json'
        metrics_json = {
            'mae': best_metrics['MAE'],
            'rmse': best_metrics['RMSE'],
            'r2': best_metrics['R2'],
            'method': best_label,
        }
        with open(metrics_path, 'w') as f:
            json.dump(metrics_json, f, indent=2, default=str)
        print(f"  ✓ Metrics saved → {metrics_path.relative_to(ROOT)}")

    # ---------------------------------------------------------
    # Classification : prix au-dessus de la médiane (XGBoost)
    # ---------------------------------------------------------
    if 'prix' in df.columns and len(df) > 10:
        median_price = df['prix'].median()
        y_clf = (df['prix'] > median_price).astype(int)
        X_clf = df.drop(columns=['prix', 'prix_log'])

        X_clf_train, X_clf_test, y_clf_train, y_clf_test = train_test_split(
            X_clf, y_clf, test_size=0.2, random_state=42
        )

        clf_model = XGBClassifier(
            n_estimators=200, learning_rate=0.1, max_depth=6,
            random_state=42, eval_metric='logloss'
        )
        clf_model.fit(X_clf_train, y_clf_train)
        clf_metrics = evaluate_classification(clf_model, X_clf_test, y_clf_test)

        results['Classification'] = clf_metrics

    return results


if __name__ == '__main__':
    clean_csvs = list(CLEAN_DIR.glob("*.csv")) if CLEAN_DIR.exists() else []
    if not clean_csvs:
        print("No ML-ready data found — running the pipeline first …")
        sys.path.insert(0, str(ROOT / "src"))
        from run_pipeline import run as run_pipeline
        run_pipeline()

    print("Loading ML-ready data …")
    df = load_clean_data()

    print("\nTraining models …\n")
    results = train_models(df)

    print("\n══════════════════════════════════════════════════════════")
    print("                      RÉSULTATS")
    print("══════════════════════════════════════════════════════════\n")
    for key, value in results.items():
        print(f"  {key}: {value}\n")
