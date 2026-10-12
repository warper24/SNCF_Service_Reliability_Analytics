{{ config(tags=['j05']) }}
with expected as (
    select q.version_id, q.row_number, q.row_sha256, q.month, d.route_key, s.service_key,
        c.cause_key, q.cause_profile_status, q.is_cause_profile_usable, q.has_cause_sum_warning, q.cause_sum_pct,
        case c.cause_key when 'external' then external_cause_pct
            when 'infrastructure' then infrastructure_cause_pct
            when 'traffic_management' then traffic_management_cause_pct
            when 'rolling_stock' then rolling_stock_cause_pct
            when 'station_management' then station_management_cause_pct
            when 'passenger_handling' then passenger_handling_cause_pct end as published_cause_pct
    from {{ ref('int_tgv_quality_flags') }} q
    join {{ ref('dim_route') }} d using (departure_station, arrival_station)
    join {{ ref('dim_service') }} s using (service_type)
    cross join {{ ref('dim_cause') }} c
)
select coalesce(e.row_number, f.row_number) as row_number, coalesce(e.cause_key, f.cause_key) as cause_key
from expected e full join {{ ref('fct_delay_causes_monthly') }} f using(version_id, row_number, cause_key)
where e.row_number is null or f.row_number is null or e.month is distinct from f.month
    or e.row_sha256 is distinct from f.row_sha256 or e.route_key is distinct from f.route_key
    or e.service_key is distinct from f.service_key
    or e.published_cause_pct is distinct from f.published_cause_pct
    or e.cause_profile_status is distinct from f.cause_profile_status
    or e.is_cause_profile_usable is distinct from f.is_cause_profile_usable
    or e.has_cause_sum_warning is distinct from f.has_cause_sum_warning
    or e.cause_sum_pct is distinct from f.cause_sum_pct
union all
select cast(null as int64), 'category_count' from (select 1)
where (select count(*) from {{ ref('dim_cause') }}) != 6
