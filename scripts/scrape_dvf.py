#!/usr/bin/env python3
"""
scrape_dvf.py
─────────────
Télécharge les données DVF (Demandes de Valeurs Foncières) depuis data.gouv.fr
pour les 35 plus grandes villes françaises, sur la période 2022–2025.

Transforme les données au format CSV attendu par le pipeline ML du projet
et les sauvegarde dans data/raw/.

Usage (depuis la racine du projet) :
    python3 scripts/scrape_dvf.py
"""

import io
import logging
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# ── Configuration ────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# URLs officielles DVF sur data.gouv.fr
DVF_URLS = {
    2022: "https://static.data.gouv.fr/resources/demandes-de-valeurs-foncieres/20251018-234844/valeursfoncieres-2022.txt.zip",
    2023: "https://static.data.gouv.fr/resources/demandes-de-valeurs-foncieres/20251018-234851/valeursfoncieres-2023.txt.zip",
    2024: "https://static.data.gouv.fr/resources/demandes-de-valeurs-foncieres/20251018-234857/valeursfoncieres-2024.txt.zip",
    2025: "https://static.data.gouv.fr/resources/demandes-de-valeurs-foncieres/20251018-234902/valeursfoncieres-2025-s1.txt.zip",
}

# ── 35 villes cibles : préfixes de codes postaux ─────────────────────────────
# Chaque entrée est (nom_ville, préfixe_CP, nom_région_LBC)
CITIES = [
    ("Paris",              "75",    "Ile-de-France"),
    ("Lyon",               "690",   "Rhône-Alpes"),
    ("Marseille",          "130",   "Provence-Alpes-Côte d'Azur"),
    ("Toulouse",           "310",   "Midi-Pyrénées"),
    ("Nice",               "060",   "Provence-Alpes-Côte d'Azur"),
    ("Nantes",             "440",   "Pays de la Loire"),
    ("Montpellier",        "340",   "Languedoc-Roussillon"),
    ("Strasbourg",         "670",   "Alsace"),
    ("Bordeaux",           "330",   "Aquitaine"),
    ("Lille",              "590",   "Nord-Pas-de-Calais"),
    ("Rennes",             "350",   "Bretagne"),
    ("Reims",              "51100", "Champagne-Ardenne"),
    ("Saint-Étienne",      "420",   "Rhône-Alpes"),
    ("Le Havre",           "76600", "Haute-Normandie"),
    ("Toulon",             "830",   "Provence-Alpes-Côte d'Azur"),
    ("Grenoble",           "380",   "Rhône-Alpes"),
    ("Dijon",              "21000", "Bourgogne"),
    ("Angers",             "490",   "Pays de la Loire"),
    ("Nîmes",              "300",   "Languedoc-Roussillon"),
    ("Clermont-Ferrand",   "630",   "Auvergne"),
    ("Aix-en-Provence",    "13100", "Provence-Alpes-Côte d'Azur"),
    ("Brest",              "29200", "Bretagne"),
    ("Tours",              "370",   "Centre"),
    ("Limoges",            "87000", "Limousin"),
    ("Amiens",             "80000", "Picardie"),
    ("Perpignan",          "660",   "Languedoc-Roussillon"),
    ("Metz",               "570",   "Lorraine"),
    ("Besançon",           "25000", "Franche-Comté"),
    ("Orléans",            "450",   "Centre"),
    ("Rouen",              "760",   "Haute-Normandie"),
    ("Caen",               "14000", "Basse-Normandie"),
    ("Mulhouse",           "680",   "Alsace"),
    ("Nancy",              "540",   "Lorraine"),
    ("Avignon",            "84000", "Provence-Alpes-Côte d'Azur"),
    ("Poitiers",           "86000", "Poitou-Charentes"),
]

# Mapping : préfixe CP → région (pour enrichir les données DVF)
_CP_TO_REGION = {prefix: region for _, prefix, region in CITIES}

# Mapping DVF "Type local" → type projet (cohérent avec les données LBC)
TYPE_MAPPING = {
    "Maison":                       "Maison",
    "Appartement":                  "Appartement",
    "Dépendance":                   "Autre",
    "Local industriel. commercial ou assimilé": "Autre",
}


# ── Fonctions utilitaires ────────────────────────────────────────────────────

def _matches_city(zipcode: str) -> bool:
    """Vérifie si un code postal correspond à l'une des 35 villes cibles."""
    z = str(zipcode).strip().zfill(5)
    return any(z.startswith(prefix) for _, prefix, _ in CITIES)


def _get_region(zipcode: str) -> str:
    """Retourne la région associée au code postal."""
    z = str(zipcode).strip().zfill(5)
    # Essayer du préfixe le plus long au plus court
    for length in (5, 4, 3, 2):
        prefix = z[:length]
        if prefix in _CP_TO_REGION:
            return _CP_TO_REGION[prefix]
    return "Inconnue"


def download_dvf_year(year: int) -> pd.DataFrame:
    """
    Télécharge le fichier DVF pour une année, le décompresse,
    et retourne un DataFrame filtré sur les 35 villes cibles.
    """
    url = DVF_URLS[year]
    log.info(f"⬇  Téléchargement DVF {year} …")

    resp = requests.get(url, timeout=120, stream=True)
    resp.raise_for_status()

    # Lire le zip en mémoire
    zip_bytes = io.BytesIO(resp.content)
    log.info(f"   {len(resp.content) / 1_048_576:.1f} Mo téléchargés")

    with zipfile.ZipFile(zip_bytes) as zf:
        # Le zip contient un seul fichier .txt
        txt_name = [n for n in zf.namelist() if n.endswith(".txt")][0]
        log.info(f"   Extraction de {txt_name} …")

        with zf.open(txt_name) as f:
            df = pd.read_csv(
                f,
                sep="|",
                decimal=",",
                low_memory=False,
                dtype={"Code postal": str},
                encoding="utf-8",
            )

    log.info(f"   {len(df):,} lignes brutes")

    # ── Filtrage ─────────────────────────────────────────────────────────
    # 1. Ventes uniquement
    df = df[df["Nature mutation"] == "Vente"]

    # 2. Types de biens résidentiels
    df = df[df["Type local"].isin(TYPE_MAPPING.keys())]

    # 3. Codes postaux des 35 villes
    df["Code postal"] = df["Code postal"].astype(str).str.zfill(5)
    df = df[df["Code postal"].apply(_matches_city)]

    # 4. Dédoublonner sur id_mutation (un lot = plusieurs lignes)
    #    On garde la ligne avec la plus grande surface
    df = df.sort_values("Surface reelle bati", ascending=False, na_position="last")
    df = df.drop_duplicates(subset=["No disposition", "Date mutation", "Valeur fonciere"], keep="first")

    log.info(f"   → {len(df):,} transactions retenues pour les 35 villes")
    return df


def transform_to_project_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforme un DataFrame DVF vers le format CSV du projet :
    id,title,category,type,price,city,zipcode,region,url,image_url,
    author,contact,suspicious,score,created_at,updated_at,surface,price_m2
    """
    out = pd.DataFrame()

    # Colonnes principales
    out["id"] = range(1, len(df) + 1)

    # Titre généré à partir du type + surface
    out["title"] = df.apply(
        lambda r: f"{TYPE_MAPPING.get(r['Type local'], 'Bien')} "
                  f"{r.get('Surface reelle bati', '')} m²".strip()
        if pd.notna(r.get("Surface reelle bati"))
        else f"{TYPE_MAPPING.get(r['Type local'], 'Bien immobilier')}",
        axis=1,
    )

    out["category"] = "Ventes immobilières"
    out["type"] = df["Type local"].map(TYPE_MAPPING).fillna("Autre")

    # Prix : la colonne DVF utilise la virgule comme séparateur décimal
    out["price"] = pd.to_numeric(df["Valeur fonciere"], errors="coerce")

    out["city"] = df["Commune"].str.strip().str.title()
    out["zipcode"] = df["Code postal"].astype(str).str.zfill(5)
    out["region"] = df["Code postal"].apply(_get_region)

    # Champs non disponibles dans DVF
    out["url"] = ""
    out["image_url"] = ""
    out["author"] = "DVF"
    out["contact"] = "hidden"
    out["suspicious"] = 0
    out["score"] = 5

    # Dates
    out["created_at"] = pd.to_datetime(df["Date mutation"], dayfirst=True, errors="coerce")
    out["updated_at"] = out["created_at"]

    # Surface et prix/m²
    out["surface"] = pd.to_numeric(df["Surface reelle bati"], errors="coerce")
    out["price_m2"] = out["price"] / out["surface"]
    out["price_m2"] = out["price_m2"].replace([float("inf"), float("-inf")], None)

    # Nettoyage : supprimer les lignes sans prix
    out = out.dropna(subset=["price"])
    out = out[out["price"] > 0]

    return out.reset_index(drop=True)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("SCRAPER DVF — 35 VILLES × 4 ANNÉES")
    log.info("=" * 60)

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    all_dfs = []

    for year in sorted(DVF_URLS.keys()):
        try:
            df_year = download_dvf_year(year)
            all_dfs.append(df_year)
        except Exception as e:
            log.error(f"✗ Erreur pour {year} : {e}")

    if not all_dfs:
        log.error("Aucune donnée récupérée. Abandon.")
        return

    # Concaténer toutes les années
    df_raw = pd.concat(all_dfs, ignore_index=True)
    log.info(f"\n{'─' * 40}")
    log.info(f"Total brut : {len(df_raw):,} transactions")

    # Transformer au format projet
    log.info("Transformation au format projet …")
    df_final = transform_to_project_format(df_raw)

    # Ré-indexer les IDs
    df_final["id"] = range(1, len(df_final) + 1)

    # Exporter
    today = datetime.now().strftime("%Y-%m-%d")
    out_path = RAW_DIR / f"{today}_dvf_france.csv"
    df_final.to_csv(out_path, index=False)

    log.info(f"\n{'=' * 60}")
    log.info(f"✓ {len(df_final):,} transactions exportées → {out_path.name}")
    log.info(f"  Période  : {df_final['created_at'].min()} → {df_final['created_at'].max()}")
    log.info(f"  Villes   : {df_final['city'].nunique()} villes distinctes")
    log.info(f"  Types    : {df_final['type'].value_counts().to_dict()}")
    if "price_m2" in df_final.columns:
        valid = df_final["price_m2"].dropna()
        if len(valid) > 0:
            log.info(f"  Prix/m²  : moy={valid.mean():.0f}€  med={valid.median():.0f}€")
    log.info("=" * 60)

    return df_final


if __name__ == "__main__":
    df = main()
    if df is not None:
        print(f"\n📊 Aperçu ({len(df):,} lignes) :")
        print(df.head(10).to_string())
