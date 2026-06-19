from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
import sys
import os

# Pour importer depuis src
ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.path.insert(0, str(ROOT))
CLEAN_DIR = ROOT / "data" / "clean"

from src.features.data_ingest import load_raw
from src.features.data_quality import data_quality
from src.features.data_cleaner import clean_leboncoin_data

router = APIRouter()

# Model path
MODEL_PATH = ROOT / "src" / "models" / "best_regression_model.joblib"

# --- Lazy Predict Data ---
class PredictData:
    def __init__(self):
        self._model = None
        self._expected_features = []
        self._city_encoding_dict = {}
        self._global_mean_price = 0
        self._available_cities = []
        self._kmeans = None
        self._initialized = False

    def _initialize(self):
        if self._initialized: return
        print("🚀 Initializing Predict Data (Lazy Loading)...")
        
        # Load Model
        try:
            self._model = joblib.load(MODEL_PATH)
            self._expected_features = self._model.feature_names_in_
        except Exception as e:
            print(f"⚠️ Erreur de chargement du modèle : {e}")

        # Load encoding
        try:
            encoding_path = ROOT / "saved_models" / "city_encoding.pickle"
            city_series = joblib.load(encoding_path)
            self._city_encoding_dict = city_series.to_dict()
            self._global_mean_price = float(city_series.mean())
            print(f"✓ City encoding loaded ({len(self._city_encoding_dict)} cities)")
        except Exception as e:
            print(f"⚠️ Could not load city_encoding.pickle: {e}")
            self._global_mean_price = 4500 # Default fallback

        # Load KMeans
        try:
            kmeans_path = ROOT / "saved_models" / "kmeans.pickle"
            self._kmeans = joblib.load(kmeans_path)
            print("✓ KMeans model loaded")
        except Exception as e:
            print(f"⚠️ Could not load kmeans.pickle: {e}")

        # Build city list
        try:
            df_raw = load_raw()
            if not df_raw.empty and 'city' in df_raw.columns:
                top = df_raw['city'].value_counts().head(30)
                self._available_cities = [
                    f"{city}, {df_raw[df_raw['city'] == city]['zipcode'].iloc[0]}" 
                    if 'zipcode' in df_raw.columns and len(df_raw[df_raw['city'] == city]) > 0 
                    else city for city in top.index
                ]
        except Exception as e:
            print(f"⚠️ Could not build city list: {e}")
            self._available_cities = ["Paris, 75000", "Lyon, 69000", "Marseille, 13000"]
        
        self._initialized = True

    @property
    def model(self):
        self._initialize()
        return self._model
    
    @property
    def expected_features(self):
        self._initialize()
        return self._expected_features

    @property
    def city_encoding_dict(self):
        self._initialize()
        return self._city_encoding_dict

    @property
    def global_mean_price(self):
        self._initialize()
        return self._global_mean_price

    @property
    def available_cities(self):
        self._initialize()
        return self._available_cities

    @property
    def kmeans(self):
        self._initialize()
        return self._kmeans

pdata = PredictData()


def _build_temporal_features(target_date: date) -> dict:
    """Compute temporal features from a date, matching feature_engineering.py logic."""
    return {
        'annee': target_date.year,
        'mois': target_date.month,
        'trimestre': (target_date.month - 1) // 3 + 1,
        'annee_mois': target_date.year + target_date.month / 12.0,
    }


def _predict_for_date(base_input: dict, target_date: date, model, expected_features) -> float:
    """Run model prediction with temporal features for a given date."""
    input_dict = {**base_input, **_build_temporal_features(target_date)}
    input_df = pd.DataFrame([input_dict], columns=expected_features)
    prediction = model.predict(input_df)[0]
    return float(prediction)


@router.get("/options")
def get_predict_options():
    """Returns available cities, property types, and valid ranges from real data."""
    # Compute real ranges from clean data
    surface_range = {"min": 5, "max": 500}
    pieces_range = {"min": 1, "max": 15}
    try:
        csv_files = sorted(CLEAN_DIR.glob("*.csv"), reverse=True)
        if csv_files:
            df_clean = pd.read_csv(csv_files[0], index_col=0)
            q01 = df_clean["surface"].quantile(0.01)
            q99 = df_clean["surface"].quantile(0.99)
            surface_range = {"min": int(q01), "max": int(q99)}
            pieces_range = {"min": 1, "max": int(df_clean["pieces"].quantile(0.99))}
    except Exception:
        pass

    cities = pdata.available_cities
    return {
        "cities": cities if cities else ["Paris, 75000", "Lyon, 69000", "Marseille, 13000"],
        "property_types": ["Appartement", "Maison", "Terrain", "Autre", "Parking"],
        "surface_range": surface_range,
        "pieces_range": pieces_range,
    }


class PropertyFeatures(BaseModel):
    city: str
    property_type: str
    surface_area: float
    rooms: int
    target_date: Optional[str] = None  # Format YYYY-MM-DD, defaults to today


@router.post("/simulate")
def simulate_price(features: PropertyFeatures):
    model = pdata.model
    if model is None:
        return {"error": "Le modèle n'est pas chargé sur le serveur."}
        
    # 1. Nettoyage de la ville reçue du frontend (ex: "Paris, 75000" -> "PARIS")
    city_clean = features.city.split(',')[0].strip().upper()
    
    # 2. Encodage de la ville
    encoded_city = pdata.city_encoding_dict.get(city_clean, pdata.global_mean_price)
    
    # 3. Nettoyage du type de bien
    type_bien_clean = features.property_type.strip().upper()
    
    # 4. Construction du dictionnaire des features pour le modèle
    surface_val = features.surface_area
    pieces_val = float(features.rooms) if features.rooms > 0 else 1.0
    surface_log_val = float(np.log1p(surface_val))

    type_flags = {
        'type_bien_APPARTEMENT': 1 if type_bien_clean == 'APPARTEMENT' else 0,
        'type_bien_AUTRE': 1 if type_bien_clean == 'AUTRE' else 0,
        'type_bien_MAISON': 1 if type_bien_clean == 'MAISON' else 0,
        'type_bien_PARKING': 1 if type_bien_clean == 'PARKING' else 0,
        'type_bien_TERRAIN': 1 if type_bien_clean == 'TERRAIN' else 0,
    }

    # Predict cluster using the saved KMeans model
    cluster_val = 0
    km = pdata.kmeans
    if km is not None:
        try:
            cluster_features = {col: type_flags.get(col, 0) for col in km.feature_names_in_}
            if "surface_log" in km.feature_names_in_:
                cluster_features["surface_log"] = surface_log_val
            if "pieces" in km.feature_names_in_:
                cluster_features["pieces"] = pieces_val
            cluster_df = pd.DataFrame([cluster_features], columns=km.feature_names_in_)
            cluster_val = int(km.predict(cluster_df)[0])
        except Exception as e:
            print(f"⚠️ Could not predict cluster, defaulting to 0: {e}")

    # Base input dict (without temporal features)
    base_input = {
        'surface': surface_val,
        'pieces': pieces_val,
        'ville': encoded_city,
        'surface_log': surface_log_val,
        'cluster': cluster_val,
        **type_flags,
    }
    
    # 5. Date cible — défaut : aujourd'hui
    if features.target_date:
        try:
            current_date = datetime.strptime(features.target_date, "%Y-%m-%d").date()
        except ValueError:
            current_date = date.today()
    else:
        current_date = date.today()

    # 6. Prédiction pour la date cible
    final_price = _predict_for_date(base_input, current_date, model, pdata.expected_features)

    # Confiance basée sur le R² réel du modèle
    try:
        with open(ROOT / "src" / "models" / "metrics.json") as f:
            r2 = float(json.load(f)["r2"])
    except Exception:
        r2 = 0.78
    confidence = round(r2 * 100, 1)

    # 7. Projections : prédictions du modèle à +6m, +1an, +2ans
    date_6m = current_date + relativedelta(months=6)
    date_1y = current_date + relativedelta(years=1)
    date_2y = current_date + relativedelta(years=2)

    price_6m = _predict_for_date(base_input, date_6m, model, pdata.expected_features)
    price_1y = _predict_for_date(base_input, date_1y, model, pdata.expected_features)
    price_2y = _predict_for_date(base_input, date_2y, model, pdata.expected_features)

    def _pct(future, current):
        if current == 0:
            return "+0.0%"
        pct = ((future - current) / abs(current)) * 100
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:.1f}%"

    projections = [
        {"period": "6 mois", "price": int(price_6m), "pct": _pct(price_6m, final_price)},
        {"period": "1 an", "price": int(price_1y), "pct": _pct(price_1y, final_price)},
        {"period": "2 ans", "price": int(price_2y), "pct": _pct(price_2y, final_price)},
    ]

    return {
        "current_estimated_price": int(final_price),
        "confidence": confidence,
        "price_per_sqm": int(final_price / features.surface_area),
        "target_date": current_date.isoformat(),
        "projection_temporelle": projections,
        "chart_data": [
            {"period": "Auj.", "price": int(final_price)},
            {"period": "6m", "price": int(price_6m)},
            {"period": "1 an", "price": int(price_1y)},
            {"period": "2 ans", "price": int(price_2y)},
        ],
        "disclaimer": f"Projections calculées par le modèle XGBoost (R²={r2}) entraîné sur des données DVF de 2022 à 2025. Les prédictions futures sont des extrapolations basées sur les tendances passées."
    }

