import pandas as pd
import sqlite3
import os

# Racine du projet (2 niveaux au-dessus de src/data/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "immobilier.db")

# Configuration
def list_raw_files() -> list:
    """
    Lists the names of the csv files in the RAW_DIR sorted in descending order.
    :return: list of csv filenames
    """
    if not os.path.exists(RAW_DIR):
        raise FileNotFoundError(f"{RAW_DIR} does not exist")
    raw_files = os.listdir(RAW_DIR)
    raw_files = [file for file in raw_files if file[-4:] == ".csv"]
    raw_files.sort(reverse=True)
    return raw_files

def ingest_data(csv_file=None, db_name=DB_PATH):
    # Si aucun fichier CSV n'est spécifié, on prend le plus récent dans data/raw/
    if csv_file is None:
        raw_files = list_raw_files()
        if not raw_files:
            print("Erreur : Aucun fichier CSV trouvé dans data/raw/.")
            return
        csv_file = os.path.join(RAW_DIR, raw_files[0])

    if not os.path.exists(csv_file):
        print(f"Erreur : Le fichier '{csv_file}' est introuvable.")
        return

    # 1. Charger les données
    print(f"Lecture du fichier {csv_file}...")
    df = pd.read_csv(csv_file)
    
    # Forcer le zipcode en string pour éviter les erreurs de type (ex: 07200 vs 7200)
    df['zipcode'] = df['zipcode'].astype(str).str.zfill(5)
    
    # Prétraitement de la date
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['year'] = df['created_at'].dt.year
    df['month'] = df['created_at'].dt.month
    df['day'] = df['created_at'].dt.day

    # 2. Connexion à la base de données
    conn = sqlite3.connect(db_name)
    
    try:
        # --- DIMENSION : TYPE ---
        print("Insertion de dim_type...")
        types_uniques = df[['type']].drop_duplicates().rename(columns={'type': 'type_name'})
        types_uniques.to_sql('dim_type', conn, if_exists='append', index=False)
        
        # --- DIMENSION : LOCATION ---
        print("Insertion de dim_location...")
        loc_uniques = df[['city', 'zipcode', 'region']].drop_duplicates()
        loc_uniques.to_sql('dim_location', conn, if_exists='append', index=False)

        # --- DIMENSION : AUTHOR ---
        print("Insertion de dim_author...")
        authors_uniques = df[['author']].drop_duplicates().rename(columns={'author': 'id_author'})
        authors_uniques.to_sql('dim_author', conn, if_exists='append', index=False)

        # --- DIMENSION : DATE ---
        print("Insertion de dim_date...")
        dates_uniques = df[['created_at', 'year', 'month', 'day']].drop_duplicates()
        # On convertit created_at en string pour SQLite
        dates_uniques['created_at'] = dates_uniques['created_at'].astype(str)
        dates_uniques.to_sql('dim_date', conn, if_exists='append', index=False)

        # --- TABLE DE FAITS : FACT_ADS ---
        print("Préparation de la table de faits (Mapping des IDs)...")
        
        # Récupération des mappings pour remplacer les noms par les IDs
        dim_type_map = pd.read_sql("SELECT id_type, type_name FROM dim_type", conn)
        dim_loc_map = pd.read_sql("SELECT id_location, city, zipcode, region FROM dim_location", conn)
        dim_date_map = pd.read_sql("SELECT id_date, created_at FROM dim_date", conn)

        # Jointures pour récupérer les IDs
        fact_df = df.merge(dim_type_map, left_on='type', right_on='type_name')
        fact_df = fact_df.merge(dim_loc_map, on=['city', 'zipcode', 'region'])
        
        # Conversion pour la jointure de date
        dim_date_map['created_at'] = pd.to_datetime(dim_date_map['created_at'])
        fact_df = fact_df.merge(dim_date_map, on='created_at')

        # Sélection des colonnes finales pour la table de faits
        # On s'assure de faire correspondre avec les noms de colonnes de init_db.sql
        final_fact_ads = fact_df[[
            'id', 'price', 'title', 'surface', 'price_m2', 
            'url', 'image_url', 'id_date', 'id_location', 
            'id_type', 'author'
        ]].rename(columns={'id': 'id_annonce', 'author': 'id_author'})

        print("Insertion dans fact_ads...")
        final_fact_ads.to_sql('fact_ads', conn, if_exists='append', index=False)

        print("Félicitations ! L'ingestion est terminée.")

    except Exception as e:
        print(f"Erreur lors de l'ingestion : {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    ingest_data()
