-- Cas déterministes pour revue humaine ; valeurs conservées et usages séparés.
with labelled as (
    select q.*, label from {{ ref('int_tgv_quality_flags') }} q
    cross join unnest([
        if(departure_station = 'DIJON VILLE' and arrival_station = 'PARIS LYON'
            and month = date '2025-01-01' and service_type = 'National', 'real_dijon', null),
        if(operated_trains_proxy = 0, 'zero_operated_proxy', null),
        if(not central_counts_compatible, 'incompatible_central_counts', null),
        if(is_cause_profile_all_zero and arrival_delayed_trains > 0, 'zero_causes_with_delays', null),
        if(cause_profile_status = 'sum_warning', 'nonzero_cause_sum_warning', null),
        if(has_negative_mean_arrival_late, 'negative_late_mean', null),
        if(has_negative_mean_arrival_all, 'signed_all_trains_mean', null),
        if(is_arrival_delay_rate_usable and is_important_delay_rate_usable
            and cause_profile_status = 'available', 'ordinary_usable', null)
    ]) label
    where label is not null
    qualify row_number() over(partition by label order by row_number) = 1
)
select label, version_id, row_number, month, departure_station, arrival_station, service_type,
    scheduled_trains, cancelled_trains, operated_trains_proxy, arrival_delayed_trains,
    arrival_delayed_over_30_trains, arrival_delayed_over_60_trains,
    mean_arrival_delay_late_minutes, mean_arrival_delay_all_minutes, cause_sum_pct,
    is_cancellation_rate_usable, is_arrival_delay_count_usable, is_arrival_delay_rate_usable,
    is_important_delay_rate_usable, is_mean_arrival_delay_late_usable,
    cause_profile_status, is_cause_profile_usable, quality_reasons
from labelled order by label
