-- Script de création de la base de données pour SQLite (Schéma en étoile)
-- Active le support des clés étrangères
PRAGMA foreign_keys = ON;

-- Suppression des tables existantes (pour réinitialisation propre)
DROP TABLE IF EXISTS fact_ads;
DROP TABLE IF EXISTS dim_location;
DROP TABLE IF EXISTS dim_type;
DROP TABLE IF EXISTS dim_author;
DROP TABLE IF EXISTS dim_date;

-- 1. Création des tables de dimensions
CREATE TABLE dim_location (
    id_location INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    zipcode TEXT,
    region TEXT
);

CREATE TABLE dim_type (
    id_type INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE
);

CREATE TABLE dim_author (
    id_author TEXT PRIMARY KEY
);

CREATE TABLE dim_date (
    id_date INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL
);

-- 2. Création de la table de faits
CREATE TABLE fact_ads (
    id_annonce INTEGER PRIMARY KEY, -- ID provenant de l'export CSV
    price REAL NOT NULL,
    title TEXT NOT NULL,
    surface REAL, -- Nouvelle colonne
    price_m2 REAL, -- Nouvelle colonne
    url TEXT,
    image_url TEXT,
    id_date INTEGER NOT NULL,
    id_location INTEGER NOT NULL,
    id_type INTEGER NOT NULL,
    id_author TEXT NOT NULL,
    -- Définition des relations
    FOREIGN KEY (id_date) REFERENCES dim_date(id_date),
    FOREIGN KEY (id_location) REFERENCES dim_location(id_location),
    FOREIGN KEY (id_type) REFERENCES dim_type(id_type),
    FOREIGN KEY (id_author) REFERENCES dim_author(id_author)
);