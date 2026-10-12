-- Dictionnaire contractuel ; les six catégories ne constituent pas un dénominateur.
select * from unnest([
    struct('external' as cause_key, 'Causes externes' as cause_label, 'external_cause_pct' as normalized_field, 'prct_cause_externe' as source_field),
    ('infrastructure', 'Infrastructure', 'infrastructure_cause_pct', 'prct_cause_infra'),
    ('traffic_management', 'Gestion du trafic', 'traffic_management_cause_pct', 'prct_cause_gestion_trafic'),
    ('rolling_stock', 'Matériel roulant', 'rolling_stock_cause_pct', 'prct_cause_materiel_roulant'),
    ('station_management', 'Gestion en gare', 'station_management_cause_pct', 'prct_cause_gestion_gare'),
    ('passenger_handling', 'Prise en charge voyageurs', 'passenger_handling_cause_pct', 'prct_cause_prise_en_charge_voyageurs')
])
