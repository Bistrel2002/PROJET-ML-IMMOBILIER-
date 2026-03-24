import pandas as pd
import numpy as np
import pprint

# Import the module we just created
from src.features.data_cleaner import clean_leboncoin_data

print("--- Création d'un dataset de test simulant les données brutes ---")

raw_data = {
    'id_annonce': ['id_1', 'id_2', 'id_3', 'id_3', 'id_4', 'id_5'],
    'ville': [' Paris ', 'LYON', 'marseille', 'marseille', ' Bordeaux', 'paris'],
    'type_bien': ['Appartement ', 'maison', ' APPARTEMENT', ' APPARTEMENT', 'Maison ', 'APPARTEMENT'],
    'prix': ['150 000 €', '350 000.5', '120 000 €', '120 000 €', '200000', np.nan],
    'surface': ['45 m²', '120m2', ' 30.5 m² ', ' 30.5 m² ', np.nan, '50'],
    'pieces': ['2 pièces', '4', '1', '1', '5', np.nan],
    'email': ['test@test.com', 'a@b.com', 'c@d.com', 'c@d.com', 'e@f.com', 'g@h.com'],
    'telephone': ['0600000000', '0700000000', '0600000000', '0600000000', '0600000000', '0600000000'],
    'description': ['Bel appartement', 'Grande maison', 'Studio', 'Studio', 'Maison de campagne', 'Appartement'],
    'agence': ['Agence A', 'Agence B', 'Agence C', 'Agence C', 'Agence D', np.nan]
}

df_raw = pd.DataFrame(raw_data)
print("\n[Avant] DataFrame brut :")
print(df_raw.to_string())

print("\n--- Exécution de la fonction de nettoyage ---")
df_cleaned = clean_leboncoin_data(df_raw, numeric_cols=['prix', 'surface', 'pieces'], text_cols=['ville', 'type_bien'], id_col='id_annonce')

print("\n[Après] DataFrame nettoyé :")
print(df_cleaned.to_string())
print("\nTypes des colonnes :")
print(df_cleaned.dtypes)
