from fastapi import APIRouter
from typing import Optional

router = APIRouter()

@router.get("/dashboard")
def get_dashboard_data(type: str = "Maison", region: str = "France entière"):
    # Apply a dynamic multiplier to fake real data changes based on filters
    mult = 1.0
    if type == "Appartement":
        mult *= 0.8
    if region == "Île-de-France":
        mult *= 2.5
        
    return {
        "kpis": {
            "median_price": f"{int(3480 * mult):,}".replace(",", " "),
            "trend_1yr": "+2.4%",
            "pred_6mo": f"{int(3562 * mult):,}".replace(",", " "),
            "pred_6mo_pct": "+2.3%",
            "ads_count": "142 680" if region == "France entière" else "38 450",
            "mae": str(int(187 * mult))
        },
        "chart_data": [
            { "month": "Avr", "price": int(3280 * mult), "isPrediction": False },
            { "month": "Mai", "price": int(3300 * mult), "isPrediction": False },
            { "month": "Jun", "price": int(3310 * mult), "isPrediction": False },
            { "month": "Jul", "price": int(3330 * mult), "isPrediction": False },
            { "month": "Aoû", "price": int(3350 * mult), "isPrediction": False },
            { "month": "Sep", "price": int(3370 * mult), "isPrediction": False },
            { "month": "Oct", "price": int(3390 * mult), "isPrediction": False },
            { "month": "Nov", "price": int(3410 * mult), "isPrediction": False },
            { "month": "Déc", "price": int(3430 * mult), "isPrediction": False },
            { "month": "Jan", "price": int(3450 * mult), "isPrediction": False },
            { "month": "Fév", "price": int(3470 * mult), "isPrediction": False },
            { "month": "Mar", "price": int(3480 * mult), "isPrediction": False, "predictedPrice": int(3480 * mult) },
            { "month": "Avr ", "price": None, "isPrediction": True, "predictedPrice": int(3510 * mult) },
            { "month": "Mai ", "price": None, "isPrediction": True, "predictedPrice": int(3540 * mult) },
            { "month": "Jun ", "price": None, "isPrediction": True, "predictedPrice": int(3562 * mult) },
        ],
        "alerts": [
            {
                "zone": "Nantes" if region == "France entière" else "Paris 11e",
                "change_pct": "+8.2%",
                "timeframe": "dans 12 mois selon le modèle Random Forest",
                "reason": "hausse prévue",
                "color_theme": "purple"
            },
            {
                "zone": "Lyon 69003",
                "change_pct": "",
                "timeframe": "+34% d'annonces vs mois précédent",
                "reason": "demande en forte hausse",
                "color_theme": "purple"
            },
            {
                "zone": "Bordeaux",
                "change_pct": "-3%",
                "timeframe": "stock d'annonces en hausse, délais allongés",
                "reason": "correction probable",
                "color_theme": "red"
            }
        ],
        "active_markets": [
            {
                "type": "Appt",
                "change_per_year": "+4.2% / an",
                "icon": "Building2",
                "price": "285 000",
                "location": "Nantes — 44000 · 68 m²",
                "confidence": 87,
                "color_theme": "green"
            },
            {
                "type": "Maison",
                "change_per_year": "+5.8% / an",
                "icon": "Home",
                "price": "420 000",
                "location": "Lyon — 69003 · 112 m²",
                "confidence": 92,
                "color_theme": "yellow"
            },
            {
                "type": "Appt",
                "change_per_year": "-1.2% / an",
                "icon": "Building2",
                "price": "195 000",
                "location": "Bordeaux — 33000 · 45 m²",
                "confidence": 79,
                "color_theme": "red"
            }
        ]
    }

@router.get("/analysis")
def get_analysis_data(zone: str = "Nantes 44", type: str = "Appartement", smin: Optional[str] = None, smax: Optional[str] = None, rooms: str = "Toutes pièces"):
    mult = 1.0
    if zone == "Paris 75":
        mult *= 3.0
    if type == "Maison":
        mult *= 1.2
        
    if rooms == "1-2 pièces":
        mult *= 0.8
    elif rooms == "5+ pièces":
        mult *= 1.5

    return {
        "history_data": [
          { "month": "Avr", "price": int(3280 * mult), "min": int(3220 * mult), "max": int(3340 * mult) },
          { "month": "Mai", "price": int(3300 * mult), "min": int(3240 * mult), "max": int(3360 * mult) },
          { "month": "Jun", "price": int(3310 * mult), "min": int(3250 * mult), "max": int(3370 * mult) },
          { "month": "Jul", "price": int(3320 * mult), "min": int(3260 * mult), "max": int(3380 * mult) },
          { "month": "Aoû", "price": int(3340 * mult), "min": int(3270 * mult), "max": int(3410 * mult) },
          { "month": "Sep", "price": int(3360 * mult), "min": int(3290 * mult), "max": int(3430 * mult) },
          { "month": "Oct", "price": int(3375 * mult), "min": int(3300 * mult), "max": int(3450 * mult) },
          { "month": "Nov", "price": int(3390 * mult), "min": int(3310 * mult), "max": int(3470 * mult) },
          { "month": "Déc", "price": int(3410 * mult), "min": int(3320 * mult), "max": int(3500 * mult) },
          { "month": "Jan", "price": int(3430 * mult), "min": int(3340 * mult), "max": int(3520 * mult) },
          { "month": "Fév", "price": int(3450 * mult), "min": int(3350 * mult), "max": int(3550 * mult) },
          { "month": "Mar", "price": int(3480 * mult), "min": int(3370 * mult), "max": int(3590 * mult) },
        ],
        "distribution_data": [
            { "bracket": "<2k", "pct": 2 if type == "Maison" else 4 },
            { "bracket": "2-3k", "pct": 10 if type == "Maison" else 18 },
            { "bracket": "3-4k", "pct": 20 if type == "Maison" else 34 },
            { "bracket": "4-5k", "pct": 35 if type == "Maison" else 25 },
            { "bracket": "5-6k", "pct": 20 if type == "Maison" else 11 },
            { "bracket": "6-7k", "pct": 10 if type == "Maison" else 5 },
            { "bracket": ">7k", "pct": 3 if type == "Maison" else 3 },
        ],
        "feature_importance": [
            { "name": "Localisation", "pct": 82 if zone == "Nantes 44" else 88 },
            { "name": "Surface (m²)", "pct": 68 if type == "Appartement" else 75 },
            { "name": "Nb pièces", "pct": 45 },
            { "name": "Type de bien", "pct": 38 },
            { "name": "Marché local", "pct": 31 },
            { "name": "Étage", "pct": 18 if type == "Appartement" else 2 },
        ],
        "top_cities": [
            {"city": "Paris", "price": int(10500 * mult)},
            {"city": "Boulogne", "price": int(8900 * mult)},
            {"city": "Neuilly", "price": int(8600 * mult)},
            {"city": "Levallois", "price": int(8400 * mult)},
            {"city": "Vincennes", "price": int(7900 * mult)},
            {"city": "Cannes", "price": int(6800 * mult)},
            {"city": "Nice", "price": int(6200 * mult)},
            {"city": "Lyon", "price": int(5200 * mult)},
            {"city": "Bordeaux", "price": int(4600 * mult)},
            {"city": "Aix-en-P", "price": int(4400 * mult)},
        ]
    }

@router.get("/pipeline")
def get_pipeline_data():
    return {
        "steps": [
            { "id": 1, "title": "Ingestion — Leboncoin scraping", "desc": "142 680 annonces · dernière exécution il y a 2h", "status": "OK", "status_format": "ok" },
            { "id": 2, "title": "Nettoyage & déduplication", "desc": "8 420 doublons supprimés · 97.2% qualité", "status": "OK", "status_format": "ok" },
            { "id": 3, "title": "Feature engineering", "desc": "34 features générées · géolocalisation, surface/pièce...", "status": "OK", "status_format": "ok" },
            { "id": 4, "title": "Entraînement modèle Random Forest", "desc": "En cours — epoch 142/200 · RMSE 187", "status": "Running", "status_format": "running" },
            { "id": 5, "title": "Validation & métriques", "desc": "En attente de l'entraînement", "status": "En attente", "status_format": "pending" },
            { "id": 6, "title": "Déploiement FastAPI", "desc": "Endpoint /predict · Dernier déploiement v2.4.1", "status": "v2.4.1", "status_format": "deployed" }
        ],
        "metrics": {
            "mae": "187",
            "rmse": "243",
            "r2": "0.913",
            "train": "114 144",
            "test": "28 536"
        },
        "stack": [
            {"name": "Scraping", "val": "Python · Scrapy"},
            {"name": "ML", "val": "Random Forest · Scikit-learn"},
            {"name": "API", "val": "FastAPI · Python"},
            {"name": "Frontend", "val": "React · Recharts"},
            {"name": "Stockage", "val": "PostgreSQL · S3"}
        ],
        "last_run": "mis à jour il y a 2h"
    }

# Keeping the heatmap and invest-alerts for the map
@router.get("/heatmap")
def get_map_heatmap():
    return [
        {
            "id": 1, "lat": 48.8566, "lng": 2.3522, "weight": 10500,
            "city": "Paris", "price": "10 500", "trend": "+1.2%", "confidence": 85, "active": True
        },
        {
            "id": 2, "lat": 45.7640, "lng": 4.8357, "weight": 5200,
            "city": "Lyon", "price": "5 200", "trend": "+5.8%", "confidence": 92, "active": True
        },
        {
            "id": 3, "lat": 44.8377, "lng": -0.5791, "weight": 4600,
            "city": "Bordeaux", "price": "4 600", "trend": "-1.2%", "confidence": 79, "active": False
        },
        {
            "id": 4, "lat": 47.2183, "lng": -1.5536, "weight": 3500,
            "city": "Nantes", "price": "3 500", "trend": "+4.2%", "confidence": 87, "active": True
        },
        {
            "id": 5, "lat": 43.2965, "lng": 5.3698, "weight": 3800,
            "city": "Marseille", "price": "3 800", "trend": "+2.1%", "confidence": 81, "active": True
        },
        {
            "id": 6, "lat": 50.6292, "lng": 3.0572, "weight": 3200,
            "city": "Lille", "price": "3 200", "trend": "+0.5%", "confidence": 88, "active": False
        }
    ]

@router.get("/invest-alerts")
def get_investment_alerts():
    return [
        {"zone": "Bordeaux", "current_price": 4500, "predicted_growth_1yr_pct": 8.5},
        {"zone": "Nantes", "current_price": 3800, "predicted_growth_1yr_pct": 6.2}
    ]
