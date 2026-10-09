-- Vue technique : prouve qu'un modèle dbt peut être créé dans BigQuery.
-- Aucun indicateur métier ni donnée SNCF n'est calculé à J02.
select 1 as connection_ok, 'J02' as milestone
