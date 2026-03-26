from fastapi import APIRouter
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import sys
import os

# Pour importer depuis src
ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.path.insert(0, str(ROOT))

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

# --- Préparation du Dictionnaire de Target Encoding pour les Villes ---
# On recalcule le dictionnaire au démarrage pour faire la correspondance Ville (Texte) -> Valeur numérique
city_encoding_dict = {}
global_mean_price = 0

def init_city_encoding():
    global city_encoding_dict, global_mean_price
    try:
        df_raw = load_raw()
        df_qual = data_quality(df_raw)
        df_clean = clean_leboncoin_data(df_qual)
        
        if 'prix' in df_clean.columns and 'ville' in df_clean.columns:
            df = df_clean.dropna(subset=['prix', 'ville'])
            global_mean_price = df['prix'].mean()
            smoothing = 20 # Correspond au paramètre actuel dans feature_engineering.py
            
            city_stats = df.groupby('ville')['prix'].agg(['mean', 'count'])
            city_stats['smoothed'] = (
                (city_stats['count'] * city_stats['mean'] + smoothing * global_mean_price)
                / (city_stats['count'] + smoothing)
            )
            city_encoding_dict = city_stats['smoothed'].to_dict()
            print("✓ Target Encoding des villes initialisé pour l'API.")
    except Exception as e:
        print(f"⚠️ Erreur lors de l'initialisation de l'encodage des villes : {e}")

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
    input_dict = {
        'surface': features.surface_area,
        'pieces': float(features.rooms) if features.rooms > 0 else 1.0,
        'ville': encoded_city,
        'type_bien_APPARTEMENT': 1 if type_bien_clean == 'APPARTEMENT' else 0,
        'type_bien_AUTRE': 1 if type_bien_clean == 'AUTRE' else 0,
        'type_bien_MAISON': 1 if type_bien_clean == 'MAISON' else 0,
        'type_bien_PARKING': 1 if type_bien_clean == 'PARKING' else 0,
        'type_bien_TERRAIN': 1 if type_bien_clean == 'TERRAIN' else 0,
    }
    
    # S'assurer que les colonnes sont exactement dans l'ordre attendu par XGBoost
    input_df = pd.DataFrame([input_dict], columns=EXPECTED_FEATURES)
    
    # 5. Prédiction
    prediction = model.predict(input_df)[0]
    
    # Le meilleur modèle sauvegardé prédit le prix brut directement (method='prix_brut')
    estimated_price = float(prediction)
    
    final_price = estimated_price

    # Confiance basée sur le R² réel du modèle
    confidence = 76.8  # R² = 0.7675

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
        "disclaimer": "Projections basées sur le taux moyen annuel de l'immobilier français (~3.5%/an, source INSEE). Le modèle XGBoost prédit le prix actuel (R²=0.7675), pas l'évolution future."
    }

