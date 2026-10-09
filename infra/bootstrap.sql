-- Remplacer PROJECT_ID par l'identifiant du projet Google Cloud avant exécution.
-- Exécuter ces instructions dans BigQuery avec la localisation EU.
-- Aucune expiration par défaut sur les données brutes, publiées ou d'audit.
CREATE SCHEMA IF NOT EXISTS `PROJECT_ID.sncf_dev`
OPTIONS(location="EU", description="Développement SNCF : essais et futurs modèles");

CREATE SCHEMA IF NOT EXISTS `PROJECT_ID.sncf_test`
OPTIONS(location="EU", default_table_expiration_days=7,
        description="Tests transitoires SNCF, expiration par défaut à 7 jours");

CREATE SCHEMA IF NOT EXISTS `PROJECT_ID.sncf_publish`
OPTIONS(location="EU", description="Version figée destinée au rapport publié");

CREATE SCHEMA IF NOT EXISTS `PROJECT_ID.sncf_audit`
OPTIONS(location="EU", description="Traçabilité et contrôles des chargements SNCF");
