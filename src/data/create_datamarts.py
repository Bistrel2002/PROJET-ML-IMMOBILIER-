import sqlite3
import os

# Configuration
db_name = "../../data/processed/immobilier.db"
sql_file = "../../scripts/sql/datamarts/create_datamarts.sql"

def create_datamarts():
    """Exécute les requêtes de création des Vues Analytiques (Data Mart)"""
    
    if not os.path.exists(sql_file):
        print(f"Erreur : Le fichier '{sql_file}' est introuvable.")
        return

    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        print(f"Connexion à '{db_name}' réussie.")

        # 2. Lecture du script SQL
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # 3. Exécution
        print("Création des vues analytiques...")
        cursor.executescript(sql_script)
        conn.commit()
        print("Le Data Mart Analytique a été créé avec succès.")

        # --- TEST RAPIDE ---
        print("\n--- Aperçu : Top 5 villes (Volume) ---")
        df_test = cursor.execute("SELECT * FROM dm_stats_par_ville LIMIT 5").fetchall()
        for row in df_test:
            print(row)

    except sqlite3.Error as e:
        print(f"Erreur SQL : {e}")

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_datamarts()