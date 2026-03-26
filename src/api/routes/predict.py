from fastapi import APIRouter
from pydantic import BaseModel
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

# --- Chargement du modèle ---
MODEL_PATH = ROOT / "src" / "models" / "best_regression_model.joblib"
try:
    model = joblib.load(MODEL_PATH)
    EXPECTED_FEATURES = model.feature_names_in_
except Exception as e:
    model = None
    EXPECTED_FEATURES = []
    print(f"⚠️ Erreur de chargement du modèle : {e}")

# --- Load metrics dynamically from training output ---
def _load_r2():
    try:
        with open(ROOT / "src" / "models" / "metrics.json") as f:
            return float(json.load(f)["r2"])
    except Exception:
        return 0.78

MODEL_R2 = _load_r2()

# --- Load city encoding from the SAME pickle used during training ---
# This ensures the API uses identical encoding values to what the model was trained on.
city_encoding_dict = {}
global_mean_price = 0

def init_city_encoding():
    global city_encoding_dict, global_mean_price
    try:
        from pickle import load as pkl_load
        encoding_path = ROOT / "saved_models" / "city_encoding.pickle"
        with open(encoding_path, "rb") as f:
            city_series = pkl_load(f)
        city_encoding_dict = city_series.to_dict()
        global_mean_price = float(city_series.mean())
        print(f"✓ City encoding loaded from {encoding_path} ({len(city_encoding_dict)} cities)")
    except Exception as e:
        print(f"⚠️ Could not load city_encoding.pickle, falling back to recomputation: {e}")
        try:
            df_raw = load_raw()
            df_qual = data_quality(df_raw)
            df_clean = clean_leboncoin_data(df_qual)
            if 'prix' in df_clean.columns and 'ville' in df_clean.columns:
                df = df_clean.dropna(subset=['prix', 'ville'])
                global_mean_price = df['prix'].mean()
                smoothing = 20
                city_stats = df.groupby('ville')['prix'].agg(['mean', 'count'])
                city_stats['smoothed'] = (
                    (city_stats['count'] * city_stats['mean'] + smoothing * global_mean_price)
                    / (city_stats['count'] + smoothing)
                )
                city_encoding_dict = city_stats['smoothed'].to_dict()
        except Exception as e2:
            print(f"⚠️ Fallback recomputation also failed: {e2}")

# Initialiser l'encodage au lancement
init_city_encoding()

# --- Build list of available cities for the frontend ---
available_cities = []
try:
    df_raw = load_raw()
    if 'city' in df_raw.columns:
        top = df_raw['city'].value_counts().head(30)
        available_cities = [f"{city}, {df_raw[df_raw['city'] == city]['zipcode'].iloc[0]}" 
                           if 'zipcode' in df_raw.columns and len(df_raw[df_raw['city'] == city]) > 0 
                           else city 
                           for city in top.index]
except Exception as e:
    print(f"⚠️ Could not build city list: {e}")
    available_cities = ["Paris, 75000", "Lyon, 69000", "Marseille, 13000", "Bordeaux, 33000", "Nantes, 44000"]


@router.get("/options")
def get_predict_options():
    """Returns available cities, property types, and valid ranges from real data."""
    # Compute real ranges from clean data
    surface_range = {"min": 5, "max": 500}
    pieces_range = {"min": 1, "max": 15}
    try:
        df_clean = pd.read_csv(sorted(CLEAN_DIR.glob("*.csv"), reverse=True)[0], index_col=0)
        q01 = df_clean["surface"].quantile(0.01)
        q99 = df_clean["surface"].quantile(0.99)
        surface_range = {"min": int(q01), "max": int(q99)}
        pieces_range = {"min": 1, "max": int(df_clean["pieces"].quantile(0.99))}
    except Exception:
        pass

    return {
        "cities": available_cities if available_cities else [
            "Paris, 75000", "Lyon, 69000", "Marseille, 13000",
            "Bordeaux, 33000", "Nantes, 44000"
        ],
        "property_types": ["Appartement", "Maison", "Terrain", "Autre", "Parking"],
        "surface_range": surface_range,
        "pieces_range": pieces_range,
    }


class PropertyFeatures(BaseModel):
    city: str
    property_type: str
    surface_area: float
    rooms: int

@router.post("/simulate")
def simulate_price(features: PropertyFeatures):
    if model is None:
        return {"error": "Le modèle n'est pas chargé sur le serveur."}
        
    # 1. Nettoyage de la ville reçue du frontend (ex: "Paris, 75000" -> "PARIS")
    city_clean = features.city.split(',')[0].strip().upper()
    
    # 2. Encodage de la ville
    encoded_city = city_encoding_dict.get(city_clean, global_mean_price)
    
    # 3. Nettoyage du type de bien
    type_bien_clean = features.property_type.strip().upper()
    
    # 4. Construction du dictionnaire des features pour le modèle
    #    Includes ALL features the model was trained on:
    #    surface, pieces, ville, surface_log, type_bien_*, cluster
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
    try:
        from pickle import load as pkl_load
        kmeans_path = ROOT / "saved_models" / "kmeans.pickle"
        with open(kmeans_path, "rb") as f:
            km = pkl_load(f)
        cluster_features = {col: type_flags.get(col, 0) for col in km.feature_names_in_}
        if "surface_log" in km.feature_names_in_:
            cluster_features["surface_log"] = surface_log_val
        if "pieces" in km.feature_names_in_:
            cluster_features["pieces"] = pieces_val
        cluster_df = pd.DataFrame([cluster_features], columns=km.feature_names_in_)
        cluster_val = int(km.predict(cluster_df)[0])
    except Exception as e:
        print(f"⚠️ Could not predict cluster, defaulting to 0: {e}")

    input_dict = {
        'surface': surface_val,
        'pieces': pieces_val,
        'ville': encoded_city,
        'surface_log': surface_log_val,
        'cluster': cluster_val,
        **type_flags,
    }
    
    # S'assurer que les colonnes sont exactement dans l'ordre attendu par XGBoost
    input_df = pd.DataFrame([input_dict], columns=EXPECTED_FEATURES)
    
    # 5. Prédiction
    prediction = model.predict(input_df)[0]
    
    # Le meilleur modèle sauvegardé prédit le prix brut directement (method='prix_brut')
    estimated_price = float(prediction)
    
    final_price = estimated_price

    # Confiance basée sur le R² réel du modèle (chargé dynamiquement)
    confidence = round(MODEL_R2 * 100, 1)

    # Projections basées sur le taux moyen annuel de l'immobilier français (INSEE ~3.5%/an)
    annual_rate = 0.035
    projections = [
        {"period": "6 mois", "price": int(final_price * (1 + annual_rate / 2)), "pct": f"+{annual_rate / 2 * 100:.1f}%"},
        {"period": "1 an", "price": int(final_price * (1 + annual_rate)), "pct": f"+{annual_rate * 100:.1f}%"},
        {"period": "2 ans", "price": int(final_price * (1 + annual_rate) ** 2), "pct": f"+{((1 + annual_rate) ** 2 - 1) * 100:.1f}%"},
    ]

    return {
        "current_estimated_price": int(final_price),
        "confidence": confidence,
        "price_per_sqm": int(final_price / features.surface_area),
        "projection_temporelle": projections,
        "chart_data": [
            { "period": "Auj.", "price": int(final_price) },
            { "period": "6m", "price": projections[0]["price"] },
            { "period": "1 an", "price": projections[1]["price"] },
            { "period": "2 ans", "price": projections[2]["price"] },
        ],
        "disclaimer": f"Projections basées sur le taux moyen annuel de l'immobilier français (~3.5%/an, source INSEE). Le modèle XGBoost prédit le prix actuel (R²={MODEL_R2}), pas l'évolution future."
    }

