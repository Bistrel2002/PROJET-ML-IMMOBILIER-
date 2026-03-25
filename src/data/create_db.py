import sqlite3
import os

# Configuration
db_name = "../../data/processed/immobilier.db"
sql_file = "../../scripts/sql/init_db.sql"

def create_database():
    """Crée la base de données SQLite et exécute le script SQL d'initialisation."""
    
    # Vérifier si le fichier SQL existe
    if not os.path.exists(sql_file):
        print(f"Erreur : Le fichier '{sql_file}' est introuvable.")
        return

    conn = None
    try:
        # 1. Connexion (Crée le fichier .db s'il n'existe pas)
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        print(f"Connexion à '{db_name}' réussie.")

        # 2. Lecture du script SQL
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # 3. Exécution des commandes SQL
        cursor.executescript(sql_script)
        conn.commit()
        print(f"Schéma en étoile créé avec succès dans '{db_name}'.")

    except sqlite3.Error as e:
        print(f"Erreur lors de la création de la base de données : {e}")
    
    except Exception as e:
        print(f"Une erreur inattendue est survenue : {e}")

    finally:
        # 4. Fermeture de la connexion
        if conn:
            conn.close()
            print("Connexion à la base de données fermée.")

if __name__ == "__main__":
    create_database()
