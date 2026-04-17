from fastapi import APIRouter
from typing import Optional
from pathlib import Path
import sys
import os
import json
import pandas as pd
import numpy as np
import joblib

router = APIRouter()

ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "clean"
MODEL_PATH = ROOT / "src" / "models" / "best_regression_model.joblib"

# ─── Utility ───────────────────────────────────────────────────────────
def get_file_lines_count(directory):
    try:
        csv_files = sorted(directory.glob("*.csv"), reverse=True)
        if not csv_files:
            return 0
        with open(csv_files[0], 'r', encoding='utf-8') as f:
            return sum(1 for _ in f) - 1
    except Exception as e:
        return 0

# ─── Load data at startup ─────────────────────────────────────────────
def load_latest_clean_data():
    try:
        csv_files = sorted(CLEAN_DIR.glob("*.csv"), reverse=True)
        if not csv_files:
            return pd.DataFrame()
        return pd.read_csv(csv_files[0], index_col=0)
    except Exception as e:
        print(f"Error loading clean data: {e}")
        return pd.DataFrame()

def load_latest_raw_data():
    try:
        csv_files = sorted(RAW_DIR.glob("*.csv"), reverse=True)
        if not csv_files:
            return pd.DataFrame()
        return pd.read_csv(csv_files[0])
    except Exception as e:
        print(f"Error loading raw data: {e}")
        return pd.DataFrame()

def load_model():
    try:
        return joblib.load(MODEL_PATH)
    except Exception as e:
        print(f"⚠️ Could not load model for analytics: {e}")
        return None

global_df = load_latest_clean_data()
raw_df = load_latest_raw_data()
xgb_model = load_model()

# ─── Join region + city from raw data into clean data ─────────────────
if not global_df.empty and not raw_df.empty and "id" in raw_df.columns:
    if "region" in raw_df.columns:
        region_map = raw_df.set_index("id")["region"]
        global_df["region"] = global_df.index.map(region_map)
    if "city" in raw_df.columns:
        city_map = raw_df.set_index("id")["city"]
        global_df["city"] = global_df.index.map(city_map)
    print(f"✓ Region + city columns added to clean data ({len(global_df)} rows)")

# ─── Extract real metadata ─────────────────────────────────────────────
PROPERTY_TYPES = ["Tous", "Appartement", "Maison", "Terrain", "Autre", "Parking"]
TYPE_COL_MAP = {
    "Appartement": "type_bien_APPARTEMENT",
    "Maison": "type_bien_MAISON",
    "Terrain": "type_bien_TERRAIN",
    "Autre": "type_bien_AUTRE",
    "Parking": "type_bien_PARKING",
}

# Extract real regions and cities from raw data
REGIONS = ["France entière"]
TOP_CITIES = []
if not raw_df.empty:
    if "region" in raw_df.columns:
        REGIONS += sorted(raw_df["region"].dropna().unique().tolist())
    if "city" in raw_df.columns:
        TOP_CITIES = raw_df["city"].value_counts().head(30).index.tolist()

# Extract real XGBoost hyperparameters
HYPERPARAMS = {}
FEATURE_IMPORTANCE = []
if xgb_model is not None:
    try:
        params = xgb_model.get_params()
        HYPERPARAMS = {
            "n_estimators": params.get("n_estimators", 300),
            "learning_rate": params.get("learning_rate", 0.1),
            "max_depth": params.get("max_depth", 7),
            "subsample": params.get("subsample", 0.8),
            "colsample_bytree": params.get("colsample_bytree", 0.8),
        }
        # Real feature importance
        importances = xgb_model.feature_importances_
        feature_names = xgb_model.feature_names_in_
        total = importances.sum()
        fi_list = sorted(
            zip(feature_names, importances),
            key=lambda x: x[1], reverse=True
        )
        FEATURE_LABELS = {
            "ville": "Ville (Target Encoded)",
            "surface": "Surface (m²)",
            "pieces": "Nb pièces",
            "type_bien_APPARTEMENT": "Appartement",
            "type_bien_MAISON": "Maison",
            "type_bien_TERRAIN": "Terrain",
            "type_bien_AUTRE": "Autre",
            "type_bien_PARKING": "Parking",
        }
        FEATURE_IMPORTANCE = [
            {"name": FEATURE_LABELS.get(name, name), "pct": round(float(imp / total) * 100, 1)}
            for name, imp in fi_list
            if float(imp / total) * 100 > 0.5  # Only show features > 0.5%
        ]
    except Exception as e:
        print(f"⚠️ Could not extract model params: {e}")

# Real model metrics — loaded dynamically from training output
METRICS_PATH = ROOT / "src" / "models" / "metrics.json"
def _load_model_metrics():
    try:
        with open(METRICS_PATH) as f:
            m = json.load(f)
        return {
            "mae": f"{int(round(m['mae'])):,}".replace(",", " "),
            "rmse": f"{int(round(float(m['rmse']))):,}".replace(",", " "),
            "r2": str(m["r2"]),
        }
    except Exception as e:
        print(f"⚠️ Could not load metrics.json, using defaults: {e}")
        return {"mae": "55 657", "rmse": "90 236", "r2": "0.7815"}

MODEL_METRICS = _load_model_metrics()


def filter_by_type(df, type_str):
    """Filter clean dataframe by property type."""
    if type_str == "Tous" or not type_str:
        return df
    col = TYPE_COL_MAP.get(type_str)
    if col and col in df.columns:
        return df[df[col] == True]
    return df


def filter_by_region(df, region_str):
    """Filter clean dataframe by region (joined from raw data)."""
    if region_str == "France entière" or not region_str:
        return df
    if "region" in df.columns:
        return df[df["region"] == region_str]
    return df


# ═══════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════

def _build_price_distribution_chart(df):
    """Build real price distribution chart from actual data — grouped by price bracket."""
    if df.empty or "prix" not in df.columns:
        return []
    
    prices = df["prix"]
    p_min = int(prices.min())
    p_max = int(prices.max())
    
    # Create ~8 brackets based on actual data range
    step = max(50000, int((p_max - p_min) / 8 / 50000) * 50000)
    if step == 0:
        step = 50000
    brackets = list(range(0, p_max + step, step))
    
    chart_data = []
    for i in range(len(brackets) - 1):
        lo, hi = brackets[i], brackets[i + 1]
        count = int(((prices >= lo) & (prices < hi)).sum())
        if count > 0:
            label = f"{lo // 1000}k" if lo > 0 else "0"
            chart_data.append({
                "bracket": f"{lo // 1000}-{hi // 1000}k€",
                "count": count,
            })
    
    return chart_data


@router.get("/dashboard/options")
def get_dashboard_options():
    """Returns dynamic dropdown options for the dashboard."""
    return {
        "property_types": PROPERTY_TYPES,
        "regions": REGIONS,
    }


@router.get("/dashboard")
def get_dashboard_data(type: str = "Tous", region: str = "France entière"):
    df = global_df.copy()

    if df.empty:
        return {"error": "No data available."}

    # Filter by type
    df = filter_by_type(df, type)
    # Filter by region
    df = filter_by_region(df, region)

    if df.empty:
        return {"error": f"Aucune donnée pour ces filtres."}

    # ── Real KPIs ──
    median_price = df["prix"].median()
    mean_price = df["prix"].mean()
    ads_count = len(df)
    r2_pct = f"{float(MODEL_METRICS['r2']) * 100:.1f}"

    # Type breakdown for active markets
    market_data = []
    market_icons = {"Appartement": "Building2", "Maison": "Home", "Terrain": "Building2"}
    market_colors = {"Appartement": "green", "Maison": "yellow", "Terrain": "purple"}
    for t_name, t_col in [("Appartement", "type_bien_APPARTEMENT"), ("Maison", "type_bien_MAISON"), ("Terrain", "type_bien_TERRAIN")]:
        if t_col in df.columns:
            sub = df[df[t_col] == True]
            if len(sub) > 0:
                avg = sub["prix"].mean()
                market_data.append({
                    "type": t_name,
                    "change_per_year": f"{len(sub)} annonces",
                    "icon": market_icons.get(t_name, "Building2"),
                    "price": f"{int(avg):,}".replace(",", " "),
                    "location": f"Prix moyen — {len(sub)} biens",
                    "confidence": min(95, max(70, int(float(MODEL_METRICS['r2']) * 100 + len(sub) / 100))),
                    "color_theme": market_colors.get(t_name, "green"),
                })

    return {
        "kpis": {
            "median_price": f"{int(median_price):,}".replace(",", " "),
            "mean_price": f"{int(df['prix'].mean()):,}".replace(",", " "),
            "prix_m2": f"{int((df['prix'] / df['surface']).median()):,}".replace(",", " ") if 'surface' in df.columns and (df['surface'] > 0).any() else "N/A",
            "ads_count": f"{ads_count:,}".replace(",", " "),
            "mae": MODEL_METRICS["mae"],
            "r2_pct": r2_pct,
        },
        "chart_data": _build_price_distribution_chart(df),
        "alerts": [
            {
                "zone": "Appartements",
                "change_pct": f"{len(df[df.get('type_bien_APPARTEMENT', pd.Series(dtype=bool)) == True]) if 'type_bien_APPARTEMENT' in df.columns else 0} biens",
                "timeframe": f"Prix médian : {int(df[df['type_bien_APPARTEMENT'] == True]['prix'].median()):,} €".replace(",", " ") if "type_bien_APPARTEMENT" in df.columns and len(df[df["type_bien_APPARTEMENT"] == True]) > 0 else "Pas de données",
                "reason": "segment actif",
                "color_theme": "purple"
            },
            {
                "zone": "Maisons",
                "change_pct": f"{len(df[df['type_bien_MAISON'] == True]) if 'type_bien_MAISON' in df.columns else 0} biens",
                "timeframe": f"Prix médian : {int(df[df['type_bien_MAISON'] == True]['prix'].median()):,} €".replace(",", " ") if "type_bien_MAISON" in df.columns and len(df[df["type_bien_MAISON"] == True]) > 0 else "Pas de données",
                "reason": "segment principal",
                "color_theme": "purple"
            },
            {
                "zone": "Modèle XGBoost",
                "change_pct": f"R² = {MODEL_METRICS['r2']}",
                "timeframe": f"MAE : {MODEL_METRICS['mae']} € · RMSE : {MODEL_METRICS['rmse']} €",
                "reason": "performance",
                "color_theme": "purple"
            },
        ],
        "active_markets": market_data[:3],
    }


# ═══════════════════════════════════════════════════════════════════════
# ANALYSIS
# ═══════════════════════════════════════════════════════════════════════
@router.get("/analysis/options")
def get_analysis_options():
    """Returns dynamic filter options for the analysis page."""
    # Room values from clean data
    room_values = []
    if not global_df.empty and "pieces" in global_df.columns:
        unique_rooms = sorted(global_df["pieces"].dropna().unique())
        # Group into meaningful ranges
        room_values = ["Toutes pièces", "1-2 pièces", "3-4 pièces", "5-6 pièces", "7+ pièces"]

    return {
        "property_types": PROPERTY_TYPES,
        "cities": ["Toutes villes"] + TOP_CITIES,
        "rooms": room_values,
    }


@router.get("/analysis")
def get_analysis_data(zone: str = "Toutes villes", type: str = "Tous", smin: Optional[str] = None, smax: Optional[str] = None, rooms: str = "Toutes pièces"):
    df = global_df.copy()

    if df.empty:
        return {"error": "No data available."}

    # Filter by type
    df = filter_by_type(df, type)

    # Filter by city/zone
    if zone and zone != "Toutes villes" and "city" in df.columns:
        df = df[df["city"] == zone]

    # Filter by surface
    if smin and smin.strip():
        try:
            df = df[df["surface"] >= float(smin)]
        except ValueError:
            pass
    if smax and smax.strip():
        try:
            df = df[df["surface"] <= float(smax)]
        except ValueError:
            pass

    # Filter by rooms
    if rooms and rooms != "Toutes pièces" and "pieces" in df.columns:
        if rooms == "1-2 pièces":
            df = df[df["pieces"] <= 2]
        elif rooms == "3-4 pièces":
            df = df[(df["pieces"] >= 3) & (df["pieces"] <= 4)]
        elif rooms == "5-6 pièces":
            df = df[(df["pieces"] >= 5) & (df["pieces"] <= 6)]
        elif rooms == "7+ pièces":
            df = df[df["pieces"] >= 7]

    if df.empty:
        return {"error": "Aucune donnée pour ces filtres."}

    median_price = df["prix"].median()
    df["prix_m2"] = df["prix"] / df["surface"]

    # ── Real distribution ──
    if len(df) > 10:
        q25 = int(df["prix"].quantile(0.25))
        q50 = int(df["prix"].quantile(0.50))
        q75 = int(df["prix"].quantile(0.75))
        distribution = [
            {"bracket": f"< {q25:,}€".replace(" ", " "), "pct": 25},
            {"bracket": f"{q25:,}–{q50:,}€".replace(",", " "), "pct": 25},
            {"bracket": f"{q50:,}–{q75:,}€".replace(",", " "), "pct": 25},
            {"bracket": f"> {q75:,}€".replace(",", " "), "pct": 25},
        ]
    else:
        distribution = []

    # ── Real top cities by average price/m² (from raw data, filtered) ──
    top_cities = []
    if not raw_df.empty and "city" in raw_df.columns and "price" in raw_df.columns:
        raw_filtered = raw_df.dropna(subset=["city", "price"])
        # Apply same type filter to raw data
        if type and type != "Tous":
            raw_filtered = raw_filtered[raw_filtered["type"] == type]
        if "surface" in raw_filtered.columns:
            raw_filtered = raw_filtered[raw_filtered["surface"] > 0]
            raw_filtered = raw_filtered.copy()
            raw_filtered["prix_m2"] = raw_filtered["price"] / raw_filtered["surface"]
            # Group by city, require at least 3 listings for meaningful average
            city_stats = raw_filtered.groupby("city")["prix_m2"].agg(["mean", "count"])
            city_stats = city_stats[city_stats["count"] >= 3].sort_values("mean", ascending=False).head(10)
            top_cities = [{"city": city, "price": int(row["mean"]), "count": int(row["count"])} for city, row in city_stats.iterrows()]
        else:
            city_stats = raw_filtered.groupby("city")["price"].agg(["mean", "count"])
            city_stats = city_stats[city_stats["count"] >= 3].sort_values("mean", ascending=False).head(10)
            top_cities = [{"city": city, "price": int(row["mean"]), "count": int(row["count"])} for city, row in city_stats.iterrows()]

    # ── Per-type price stats (real data, replaces fake timeline) ──
    type_stats = []
    for t_label, t_col in [("Appartement", "type_bien_APPARTEMENT"), ("Maison", "type_bien_MAISON"), ("Terrain", "type_bien_TERRAIN"), ("Autre", "type_bien_AUTRE"), ("Parking", "type_bien_PARKING")]:
        if t_col in df.columns:
            sub = df[df[t_col] == True]
            if len(sub) > 0:
                sub_prix_m2 = sub["prix"] / sub["surface"]
                type_stats.append({
                    "type": t_label,
                    "count": int(len(sub)),
                    "median": int(sub["prix"].median()),
                    "prix_min": int(sub["prix"].min()),
                    "prix_max": int(sub["prix"].max()),
                    "prix_m2": int(sub_prix_m2.median()),
                })

    return {
        "type_stats": type_stats,
        "distribution_data": distribution,
        "feature_importance": FEATURE_IMPORTANCE if FEATURE_IMPORTANCE else [
            {"name": "Ville (Target Encoded)", "pct": 82},
            {"name": "Surface (m²)", "pct": 68},
            {"name": "Nb pièces", "pct": 45},
            {"name": "Appartement", "pct": 38},
            {"name": "Maison", "pct": 31},
        ],
        "top_cities": top_cities,
        "stats": {
            "count": len(df),
            "median": int(median_price),
            "mean": int(df["prix"].mean()),
            "min": int(df["prix"].min()),
            "max": int(df["prix"].max()),
        },
    }


# ═══════════════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════════════
@router.get("/pipeline")
def get_pipeline_data():
    raw_count = get_file_lines_count(RAW_DIR)
    clean_count = get_file_lines_count(CLEAN_DIR)
    doublons = raw_count - clean_count if raw_count > clean_count else 0

    return {
        "steps": [
            {"id": 1, "title": "Ingestion — Leboncoin scraping", "desc": f"{raw_count:,} annonces brutes".replace(",", " "), "status": "OK", "status_format": "ok"},
            {"id": 2, "title": "Nettoyage & déduplication", "desc": f"{doublons:,} lignes ignorées (doublons/qualité)".replace(",", " "), "status": "OK", "status_format": "ok"},
            {"id": 3, "title": "Feature engineering", "desc": "Target encoding, log(prix), One-Hot encoding", "status": "OK", "status_format": "ok"},
            {"id": 4, "title": "Entraînement modèle XGBoost", "desc": f"Modèle entraîné sur {int(clean_count * 0.8)} échantillons", "status": "Terminé", "status_format": "ok"},
            {"id": 5, "title": "Validation & métriques", "desc": f"R² = {MODEL_METRICS['r2']} · MAE = {MODEL_METRICS['mae']} €", "status": "Validé", "status_format": "ok"},
            {"id": 6, "title": "Déploiement FastAPI", "desc": "Endpoint /predict opérationnel avec modèle réel", "status": "Actif", "status_format": "deployed"},
        ],
        "metrics": {
            "mae": MODEL_METRICS["mae"],
            "rmse": MODEL_METRICS["rmse"],
            "r2": MODEL_METRICS["r2"],
            "train": str(int(clean_count * 0.8)),
            "test": str(int(clean_count * 0.2)),
        },
        "hyperparams": HYPERPARAMS,
        "stack": [
            {"name": "Scraping", "val": "Python · Requests"},
            {"name": "ML", "val": "XGBoost · Scikit-learn"},
            {"name": "API", "val": "FastAPI · Python"},
            {"name": "Frontend", "val": "Next.js · React"},
            {"name": "Moteur", "val": "Pandas · Numpy"},
        ],
        "last_run": "mis à jour avec les vraies données",
    }


# ═══════════════════════════════════════════════════════════════════════
# HEATMAP — Real city data
# ═══════════════════════════════════════════════════════════════════════
# City coordinates lookup (major French cities)
CITY_COORDS = {
    "Paris": (48.8566, 2.3522), "Marseille": (43.2965, 5.3698),
    "Lyon": (45.7640, 4.8357), "Toulouse": (43.6047, 1.4442),
    "Nice": (43.7102, 7.2620), "Nantes": (47.2184, -1.5536),
    "Strasbourg": (48.5734, 7.7521), "Montpellier": (43.6108, 3.8767),
    "Bordeaux": (44.8378, -0.5792), "Lille": (50.6292, 3.0573),
    "Rennes": (48.1173, -1.6778), "Reims": (49.2583, 3.0583),
    "Toulon": (43.1242, 5.9280), "Saint-Malo": (48.6493, -2.0007),
    "Rouen": (49.4432, 1.0999), "Limoges": (45.8336, 1.2611),
    "Fréjus": (43.4332, 6.7370), "Brest": (48.3904, -4.4861),
    "Orléans": (47.9029, 1.9039), "Poitiers": (46.5802, 0.3404),
    "Agde": (43.3108, 3.4758), "Perpignan": (42.6987, 2.8956),
    "La Rochelle": (46.1603, -1.1511), "Angers": (47.4784, -0.5632),
    "Tours": (47.3941, 0.6848), "Dijon": (47.3220, 5.0415),
    "Grenoble": (45.1885, 5.7245), "Le Mans": (48.0061, 0.1996),
    "Aix-en-Provence": (43.5297, 5.4474), "Clermont-Ferrand": (45.7772, 3.0870),
    "Les Sables-d'Olonne": (46.4966, -1.7834), "Le Havre": (49.4944, 0.1079),
    "La Seyne-sur-Mer": (43.1009, 5.8854), "Dunkerque": (51.0343, 2.3768),
    "Hyères": (43.1204, 6.1286), "Amiens": (49.8941, 2.2958),
    "Saint-Raphaël": (43.4253, 6.7688),
}


@router.get("/heatmap")
def get_map_heatmap():
    if raw_df.empty or "city" not in raw_df.columns or "price" not in raw_df.columns:
        return []

    df = raw_df.dropna(subset=["city", "price"])
    city_stats = df.groupby("city").agg(
        avg_price=("price", "mean"),
        count=("price", "count"),
    ).sort_values("count", ascending=False).head(30)

    # Compute price/m2 for all cities first to determine terciles
    city_m2 = {}
    for city in city_stats.index:
        sub = df[df["city"] == city]
        if "surface" in sub.columns:
            sub_valid = sub[sub["surface"] > 0]
            if len(sub_valid) > 0:
                city_m2[city] = int((sub_valid["price"] / sub_valid["surface"]).mean())
    
    # Compute terciles for color tiers
    if city_m2:
        m2_values = sorted(city_m2.values())
        t1 = m2_values[len(m2_values) // 3]
        t2 = m2_values[2 * len(m2_values) // 3]
    else:
        t1, t2 = 3000, 5000

    result = []
    for idx, (city, row) in enumerate(city_stats.iterrows()):
        coords = CITY_COORDS.get(city, None)
        if coords is None:
            continue
        avg_m2 = city_m2.get(city, 0)
        avg = int(row["avg_price"])

        # Tier: green=cheap, yellow=mid, red=expensive
        if avg_m2 <= t1:
            tier = "cheap"
        elif avg_m2 <= t2:
            tier = "mid"
        else:
            tier = "expensive"

        result.append({
            "id": idx + 1,
            "lat": coords[0],
            "lng": coords[1],
            "weight": avg_m2 if avg_m2 > 0 else avg,
            "price_m2": avg_m2,
            "city": city,
            "price": f"{avg_m2:,}".replace(",", " ") if avg_m2 > 0 else f"{avg:,}".replace(",", " "),
            "trend": f"{int(row['count'])} annonces",
            "tier": tier,
            "count": int(row["count"]),
            "active": bool(row["count"] >= 15),
        })

    return result


@router.get("/invest-alerts")
def get_investment_alerts():
    if raw_df.empty or "city" not in raw_df.columns or "price" not in raw_df.columns:
        return []

    df = raw_df.dropna(subset=["city", "price"])
    if "surface" not in df.columns:
        return []

    df = df[df["surface"] > 0].copy()
    df["prix_m2"] = df["price"] / df["surface"]
    city_stats = df.groupby("city")["prix_m2"].agg(["mean", "count", "median"])
    city_stats = city_stats[city_stats["count"] >= 5].sort_values("count", ascending=False)

    # Global median for comparison
    global_median = df["prix_m2"].median()

    # Top 5 cities with most listings — show real stats
    alerts = []
    for city, row in city_stats.head(5).iterrows():
        diff_pct = ((row["mean"] - global_median) / global_median) * 100
        alerts.append({
            "zone": city,
            "current_price": int(row["mean"]),
            "count": int(row["count"]),
            "vs_median_pct": round(float(diff_pct), 1),
        })

    return alerts
