-- Six lignes, même en présence de NULL. Aucun effectif de trains répété dans ce fait.
with long_profile as (
    select version_id, row_number, row_sha256, month, departure_station, arrival_station,
        service_type, cause_profile_status, is_cause_profile_usable, cause_sum_pct,
        has_cause_sum_warning, normalized_field, published_cause_pct
    from {{ ref('int_tgv_quality_flags') }}
    unpivot include nulls (published_cause_pct for normalized_field in (
        external_cause_pct, infrastructure_cause_pct, traffic_management_cause_pct,
        rolling_stock_cause_pct, station_management_cause_pct, passenger_handling_cause_pct))
)
select p.version_id, p.row_number, p.row_sha256, p.month,
    d.route_key, s.service_key, c.cause_key, p.published_cause_pct,
    p.cause_profile_status, p.is_cause_profile_usable, p.cause_sum_pct, p.has_cause_sum_warning
from long_profile p
join {{ ref('dim_route') }} d using (departure_station, arrival_station)
join {{ ref('dim_service') }} s using (service_type)
join {{ ref('dim_cause') }} c using (normalized_field)
