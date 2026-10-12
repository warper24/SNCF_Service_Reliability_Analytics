{{ config(tags=['j05']) }}
select 'calendar_gap' as failure from (select 1) where
 (select count(*) from {{ ref('dim_date') }}) !=
 (select date_diff(max(date_key), min(date_key), day)+1 from {{ ref('dim_date') }})
union all select 'fact_month' from {{ ref('fct_reliability_monthly') }} where month != date_trunc(month, month)
union all select 'calendar_attributes' from {{ ref('dim_date') }}
where month != date_trunc(date_key, month) or is_month_start != (date_key = month)
or year != extract(year from date_key) or month_number != extract(month from date_key)
union all select 'route_key' from {{ ref('dim_route') }}
where route_key != to_hex(sha256(to_json_string(struct(departure_station as departure_station, arrival_station as arrival_station))))
union all select 'service_key' from {{ ref('dim_service') }}
where service_key != to_hex(sha256(service_type))
