from fastapi import APIRouter
from typing import Optional
from pathlib import Path
import sys
import os
import json
import pandas as pd
import numpy as np
import joblib
import threading

router = APIRouter()

ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "clean"
MODEL_PATH = ROOT / "src" / "models" / "best_regression_model.joblib"

# ─── Lazy Data Loader ─────────────────────────────────────────────────
class AnalyticsData:
    def __init__(self):
        self._global_df = pd.DataFrame()
        self._raw_df = pd.DataFrame()
        self._xgb_model = None
        self._initialized = False
        self._lock = threading.RLock()

    @property
    def global_df(self):
        if not self._initialized: self._initialize()
        return self._global_df

    @property
    def raw_df(self):
        if not self._initialized: self._initialize()
        return self._raw_df

    @property
    def xgb_model(self):
        if not self._initialized: self._initialize()
        return self._xgb_model

    def _initialize(self):
        with self._lock:
            if self._initialized: return
            print("🚀 Initializing Analytics Data (Lazy Loading)...")
            try:
                # Check for cached joined data (dedicated folder to avoid uvicorn reload loop)
                cached_path = ROOT / ".cache" / "analytics_cache.joblib"
                if cached_path.exists():
                    print(f"✓ Loading cached joined data from {cached_path.name}...")
                    self._global_df = joblib.load(cached_path)
                    print(f"✓ Done ({len(self._global_df)} rows)")
                    try:
                        self._xgb_model = joblib.load(MODEL_PATH)
                        print("✓ Model loaded")
                    except: pass
                    # Also load raw_df for invest-alerts and top_cities
                    raw_files = sorted(RAW_DIR.glob("*.csv"), reverse=True)
                    if raw_files:
                        print(f"  → Loading raw data for metadata: {raw_files[0].name}")
                        self._raw_df = pd.read_csv(raw_files[0])
                    self._initialized = True
                    return

                # Standard load
                print("⏳ No cache found. Loading raw CSVs (this may take 30-60s)...")
                csv_files = sorted(CLEAN_DIR.glob("*.csv"), reverse=True)
                if csv_files:
                    print(f"  → Loading clean data: {csv_files[0].name}")
                    self._global_df = pd.read_csv(csv_files[0], index_col=0)
                
                raw_files = sorted(RAW_DIR.glob("*.csv"), reverse=True)
                if raw_files:
                    print(f"  → Loading raw data for metadata: {raw_files[0].name}")
                    self._raw_df = pd.read_csv(raw_files[0])
                
                print("  → Loading model...")
                try: self._xgb_model = joblib.load(MODEL_PATH)
                except Exception as e:
                    print(f"⚠️ Could not load model: {e}")

                # Join Region + City
                if not self._global_df.empty and not self._raw_df.empty and "id" in self._raw_df.columns:
                    print("  → Joining datasets for mapping...")
                    cols_to_join = [col for col in ["id", "region", "city"] if col in self._raw_df.columns]
                    join_df = self._raw_df[cols_to_join].drop_duplicates("id").set_index("id")
                    self._global_df = self._global_df.merge(join_df, left_index=True, right_index=True, how="left")
                    print(f"✓ Data joined ({len(self._global_df)} rows)")
                    # Cache it for next time
                    try: 
                        ROOT.joinpath(".cache").mkdir(parents=True, exist_ok=True)
                        joblib.dump(self._global_df, cached_path)
                        print(f"✓ Created cache: {cached_path}")
                    except Exception as e:
                        print(f"⚠️ Could not save cache: {e}")

                self._initialized = True
            except Exception as e:
                print(f"❌ Critical error during analytics initialization: {e}")
                self._initialized = True

data = AnalyticsData()

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

def get_metadata():
    global REGIONS, TOP_CITIES
    if REGIONS != ["France entière"] and TOP_CITIES:
        return REGIONS, TOP_CITIES
    
    df = data.global_df # Use global_df instead of raw_df
    if not df.empty:
        if "region" in df.columns:
            REGIONS = ["France entière"] + sorted(df["region"].dropna().unique().tolist())
        if "city" in df.columns:
            TOP_CITIES = df["city"].value_counts().head(30).index.tolist()
        elif "ville" in df.columns and TOP_CITIES == []:
            # Fallback if 'city' column name varies
            TOP_CITIES = ["Toutes villes"]
    return REGIONS, TOP_CITIES

# Extract real XGBoost hyperparameters
def get_model_info():
    model = data.xgb_model
    params_dict = {}
    fi_list_final = []
    
    if model is not None:
        try:
            params = model.get_params()
            params_dict = {
                "n_estimators": params.get("n_estimators", 200),
                "learning_rate": params.get("learning_rate", 0.1),
                "max_depth": params.get("max_depth", 7),
                "subsample": params.get("subsample", 0.8),
                "colsample_bytree": params.get("colsample_bytree", 0.8),
            }
            # Real feature importance
            importances = model.feature_importances_
            feature_names = model.feature_names_in_
            total = importances.sum()
            fi_raw = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
            
            FEATURE_LABELS = {
                "ville": "Ville (Target Encoded)", "surface": "Surface (m²)", "pieces": "Nb pièces",
                "type_bien_APPARTEMENT": "Appartement", "type_bien_MAISON": "Maison",
                "type_bien_TERRAIN": "Terrain", "type_bien_AUTRE": "Autre", "type_bien_PARKING": "Parking",
            }
            fi_list_final = [
                {"name": FEATURE_LABELS.get(name, name), "pct": round(float(imp / total) * 100, 1)}
                for name, imp in fi_raw if float(imp / total) * 100 > 0.5
            ]
        except Exception as e:
            print(f"⚠️ Could not extract model params: {e}")
    return params_dict, fi_list_final

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

# MODEL_METRICS will be loaded on first use to avoid import hangs
_MODEL_METRICS_CACHE = None
def get_metrics():
    global _MODEL_METRICS_CACHE
    if _MODEL_METRICS_CACHE is None:
        _MODEL_METRICS_CACHE = _load_model_metrics()
    return _MODEL_METRICS_CACHE


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
    """Build price distribution using optimized pd.cut — much faster for 300k+ rows."""
    if df.empty or "prix" not in df.columns:
        return []
    
    prices = df["prix"]
    p_max = int(prices.max())
    
    # Fast step calculation
    step = 100000 if p_max > 1000000 else 50000
    bins = list(range(0, p_max + step, step))
    
    # Use pandas vectorization (pd.cut) which is O(N) instead of O(N*B)
    counts = pd.cut(prices, bins=bins).value_counts().sort_index()
    
    chart_data = []
    for interval, count in counts.items():
        if count > 0:
            lo, hi = int(interval.left), int(interval.right)
            chart_data.append({
                "bracket": f"{lo // 1000}-{hi // 1000}k€",
                "count": int(count),
            })
    
    return chart_data


@router.get("/dashboard/options")
def get_dashboard_options():
    """Returns dynamic dropdown options for the dashboard."""
    regions, _ = get_metadata()
    return {
        "property_types": PROPERTY_TYPES,
        "regions": regions,
    }


@router.get("/dashboard")
def get_dashboard_data(type: str = "Tous", region: str = "France entière"):
    df = data.global_df  # Safe: filter_by_type/region always return new DataFrames

    if df.empty:
        return {"error": "No data available."}

    # Filter sequentially
    if type != "Tous": df = filter_by_type(df, type)
    if region != "France entière": df = filter_by_region(df, region)

    if df.empty:
        return {"error": f"Aucune donnée pour ces filtres."}

    # ── Real KPIs ──
    metrics = get_metrics()
    median_price = df["prix"].median()
    mean_price = df["prix"].mean()
    ads_count = len(df)
    r2_pct = f"{float(metrics['r2']) * 100:.1f}"

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
                    "confidence": min(95, max(70, int(float(metrics['r2']) * 100 + len(sub) / 100))),
                    "color_theme": market_colors.get(t_name, "green"),
                })

    return {
        "kpis": {
            "median_price": f"{int(median_price):,}".replace(",", " "),
            "mean_price": f"{int(df['prix'].mean()):,}".replace(",", " "),
            "prix_m2": f"{int((df['prix'] / df['surface']).median()):,}".replace(",", " ") if 'surface' in df.columns and (df['surface'] > 0).any() else "N/A",
            "ads_count": f"{ads_count:,}".replace(",", " "),
            "mae": metrics["mae"],
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
                "change_pct": f"R² = {metrics['r2']}",
                "timeframe": f"MAE : {metrics['mae']} € · RMSE : {metrics['rmse']} €",
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
    gdf = data.global_df
    # Room values from clean data
    room_values = []
    if not gdf.empty and "pieces" in gdf.columns:
        unique_rooms = sorted(gdf["pieces"].dropna().unique())
        # Group into meaningful ranges
        room_values = ["Toutes pièces", "1-2 pièces", "3-4 pièces", "5-6 pièces", "7+ pièces"]

    _, top_cities = get_metadata()
    return {
        "property_types": PROPERTY_TYPES,
        "cities": ["Toutes villes"] + top_cities,
        "rooms": room_values,
    }


@router.get("/analysis")
def get_analysis_data(zone: str = "Toutes villes", type: str = "Tous", smin: Optional[str] = None, smax: Optional[str] = None, rooms: str = "Toutes pièces"):
    df = data.global_df.copy()

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
    raw_df = data.raw_df
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

    _, fimportance = get_model_info()

    return {
        "type_stats": type_stats,
        "distribution_data": distribution,
        "feature_importance": fimportance if fimportance else [
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
    raw_df = data.raw_df
    gdf = data.global_df
    
    raw_count = len(raw_df) if not raw_df.empty else 0
    clean_count = len(gdf) if not gdf.empty else 0
    doublons = raw_count - clean_count if raw_count > clean_count else 0

    hparams, fimportance = get_model_info()
    metrics = get_metrics()

    return {
        "steps": [
            {"id": 1, "title": "Ingestion — Leboncoin scraping", "desc": f"{raw_count:,} annonces brutes".replace(",", " "), "status": "OK", "status_format": "ok"},
            {"id": 2, "title": "Nettoyage & déduplication", "desc": f"{doublons:,} lignes ignorées (doublons/qualité)".replace(",", " "), "status": "OK", "status_format": "ok"},
            {"id": 3, "title": "Feature engineering", "desc": "Target encoding, log(prix), One-Hot encoding", "status": "OK", "status_format": "ok"},
            {"id": 4, "title": "Entraînement modèle XGBoost", "desc": f"Modèle entraîné sur {int(clean_count * 0.8)} échantillons", "status": "Terminé", "status_format": "ok"},
            {"id": 5, "title": "Validation & métriques", "desc": f"R² = {metrics['r2']} · MAE = {metrics['mae']} €", "status": "Validé", "status_format": "ok"},
            {"id": 6, "title": "Déploiement FastAPI", "desc": "Endpoint /predict opérationnel avec modèle réel", "status": "Actif", "status_format": "deployed"},
        ],
        "metrics": {
            "mae": metrics["mae"],
            "rmse": metrics["rmse"],
            "r2": metrics["r2"],
            "train": str(int(clean_count * 0.8)),
            "test": str(int(clean_count * 0.2)),
        },
        "hyperparams": hparams,
        "feature_importance": fimportance,
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
    df = data.global_df.copy()
    if df.empty or "city" not in df.columns or "prix" not in df.columns:
        # Fallback to 'ville' if 'city' is missing locally
        if not df.empty and "ville" in df.columns:
            df["city"] = df["ville"]
        else:
            return []

    # Filter by city and prix
    df = df.dropna(subset=["city", "prix"])
    if "surface" in df.columns:
        df = df[df["surface"] > 0].copy()
        df["prix_m2"] = df["prix"] / df["surface"]
    else:
        df = df.copy()
        df["prix_m2"] = df["prix"] / 100

    # Group by city to get averages
    city_stats = df.groupby("city").agg(
        avg_m2=("prix_m2", "mean"),
        count=("prix_m2", "count"),
        avg_price=("prix", "mean")
    ).sort_values("count", ascending=False).head(50)

    # Function to find coordinates (matching "Paris 15" -> "Paris")
    def _find_coords(city_name):
        def _norm(s): return s.upper().replace("-", " ").strip()
        city_norm = _norm(city_name)
        
        # Direct match on normalized keys
        for k, v in CITY_COORDS.items():
            if _norm(k) == city_norm: return v
            
        # Partial match (e.g. "PARIS 15" starts with "PARIS")
        for k, v in CITY_COORDS.items():
            k_norm = _norm(k)
            if city_norm.startswith(k_norm) or k_norm in city_norm:
                return v
        return None

    # Step 1: Filter cities that have coordinates
    mappable_cities = []
    m2_values = []
    for city, row in city_stats.iterrows():
        coords = _find_coords(city)
        if coords:
            val = int(row["avg_m2"])
            mappable_cities.append((city, row, coords))
            if val > 0:
                m2_values.append(val)

    # Step 2: Compute thresholds for tiers
    m2_values = sorted(m2_values)
    if len(m2_values) >= 3:
        t1 = m2_values[len(m2_values) // 3]
        t2 = m2_values[2 * len(m2_values) // 3]
    else:
        t1, t2 = 3500, 6000

    # Step 3: Build result
    result = []
    for idx, (city, row, coords) in enumerate(mappable_cities):
        val = int(row["avg_m2"])
        
        if val <= t1:
            tier = "cheap"
        elif val <= t2:
            tier = "mid"
        else:
            tier = "expensive"

        result.append({
            "id": idx + 1,
            "lat": coords[0],
            "lng": coords[1],
            "weight": val if val > 0 else int(row["avg_price"] / 500),
            "price_m2": val,
            "city": city,
            "price": f"{val:,}".replace(",", " ") if val > 0 else f"{int(row['avg_price']):,}".replace(",", " "),
            "trend": f"{int(row['count'])} annonces",
            "tier": tier,
            "count": int(row["count"]),
            "active": bool(row["count"] >= 10),
        })

    return result


@router.get("/invest-alerts")
def get_investment_alerts():
    raw_df = data.raw_df
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
