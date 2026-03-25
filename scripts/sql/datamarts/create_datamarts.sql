-- Vues analytiques pour le Data Mart Immobilier (En attendant la surface et le prix_m2)

-- 1. Vue Analytique : Statistiques globales par Ville
-- Utile pour : Dashboard géographique, volume par zone, prix moyen.
DROP VIEW IF EXISTS dm_stats_par_ville;
CREATE VIEW dm_stats_par_ville AS
SELECT 
    l.region,
    l.city,
    COUNT(f.id_annonce) AS volume_annonces,
    ROUND(AVG(f.price), 2) AS prix_moyen,
    ROUND(AVG(f.surface), 1) AS surface_moyenne,
    ROUND(AVG(f.price_m2), 2) AS prix_m2_moyen,
    MIN(f.price) AS prix_minimum,
    MAX(f.price) AS prix_maximum
FROM fact_ads f
JOIN dim_location l ON f.id_location = l.id_location
GROUP BY l.region, l.city
ORDER BY volume_annonces DESC;

-- 2. Vue Analytique : Tendances par Région et Type de bien
-- Utile pour : Comparaison des marchés (ex: Maisons vs Appartements en Ile-de-France)
DROP VIEW IF EXISTS dm_stats_region_type;
CREATE VIEW dm_stats_region_type AS
SELECT 
    l.region,
    t.type_name,
    COUNT(f.id_annonce) AS volume_annonces,
    ROUND(AVG(f.price), 2) AS prix_moyen
FROM fact_ads f
JOIN dim_location l ON f.id_location = l.id_location
JOIN dim_type t ON f.id_type = t.id_type
GROUP BY l.region, t.type_name
ORDER BY l.region, volume_annonces DESC;

-- 3. Vue Analytique : Suivi chronologique mensuel
-- Utile pour : Volume d'annonces au fil du temps (saisonnalité)
DROP VIEW IF EXISTS dm_stats_mensuelles;
CREATE VIEW dm_stats_mensuelles AS
SELECT 
    d.year,
    d.month,
    COUNT(f.id_annonce) AS volume_annonces,
    ROUND(AVG(f.price), 2) AS prix_moyen
FROM fact_ads f
JOIN dim_date d ON f.id_date = d.id_date
GROUP BY d.year, d.month
ORDER BY d.year, d.month;
