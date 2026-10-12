-- Effectifs source conservés, usages distincts ; D01 : N est une population déduite non certifiée.
select
    q.* except(raw_payload, external_cause_pct, infrastructure_cause_pct,
        traffic_management_cause_pct, rolling_stock_cause_pct, station_management_cause_pct,
        passenger_handling_cause_pct),
    d.route_key, s.service_key,
    {{ reference_ratio('q.cancelled_trains', 'q.scheduled_trains', 'q.is_cancellation_rate_usable') }} as cancellation_rate,
    {{ reference_ratio('q.arrival_delayed_trains', 'q.operated_trains_proxy', 'q.is_arrival_delay_rate_usable') }} as arrival_delay_rate,
    {{ reference_ratio('q.operated_trains_proxy - q.arrival_delayed_trains', 'q.operated_trains_proxy', 'q.is_arrival_delay_rate_usable') }} as composite_regularity_rate,
    {{ reference_ratio('q.arrival_delayed_over_30_trains', 'q.operated_trains_proxy', 'q.is_important_delay_rate_usable') }} as over_30_delay_rate,
    {{ reference_ratio('q.arrival_delayed_over_60_trains', 'q.operated_trains_proxy', 'q.is_important_delay_rate_usable') }} as over_60_delay_rate,
    if(q.is_important_delay_count_usable, q.arrival_delayed_over_30_trains, null) as over_30_delay_count,
    if(q.is_important_delay_count_usable, q.arrival_delayed_over_60_trains, null) as over_60_delay_count,
    'derived_population_not_certified_D01' as denominator_status
from {{ ref('int_tgv_quality_flags') }} q
join {{ ref('dim_route') }} d using (departure_station, arrival_station)
join {{ ref('dim_service') }} s using (service_type)
