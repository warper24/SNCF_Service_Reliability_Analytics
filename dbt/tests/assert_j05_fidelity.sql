{{ config(tags=['j05']) }}
with source_rows as (
    select version_id, row_number,
        to_json_string((select as struct q.* except(raw_payload,
        external_cause_pct, infrastructure_cause_pct, traffic_management_cause_pct,
        rolling_stock_cause_pct, station_management_cause_pct, passenger_handling_cause_pct))) as content
    from {{ ref('int_tgv_quality_flags') }} q
), fact_rows as (
    select version_id, row_number,
        to_json_string((select as struct f.* except(route_key, service_key, cancellation_rate,
        arrival_delay_rate, composite_regularity_rate, over_30_delay_rate, over_60_delay_rate,
        over_30_delay_count, over_60_delay_count, denominator_status))) as content
    from {{ ref('fct_reliability_monthly') }} f
)
select coalesce(s.version_id, f.version_id) as version_id, coalesce(s.row_number, f.row_number) as row_number
from source_rows s full join fact_rows f using (version_id, row_number)
where s.content is distinct from f.content
