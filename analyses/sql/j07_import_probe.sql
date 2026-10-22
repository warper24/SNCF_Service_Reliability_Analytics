-- Expérience Import isolée. Remplacer PROJECT_ID ; exécuter une seule étape à la fois.
-- Le dataset sncf_test expire ses tables de test. Aucun fait SNCF n'est modifié.
CREATE TABLE IF NOT EXISTS `PROJECT_ID.sncf_test.j07_import_probe`
OPTIONS(expiration_timestamp=TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY))
AS SELECT 1 AS probe_value, CURRENT_TIMESTAMP() AS changed_at_utc;

-- Après import de la valeur 1 et conservation de la preuve :
-- UPDATE `PROJECT_ID.sncf_test.j07_import_probe`
-- SET probe_value = 2, changed_at_utc = CURRENT_TIMESTAMP() WHERE probe_value = 1;
-- Observer 1 dans Desktop avant actualisation, puis 2 après actualisation.
