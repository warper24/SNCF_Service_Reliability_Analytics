-- Exemples de contrôle limités ; ni le brut complet ni une sélection de performance.
select version_id, row_number, row_sha256, month, departure_station, arrival_station,
    service_type, scheduled_trains, cancelled_trains, operated_trains_proxy, arrival_delayed_trains,
    arrival_delayed_over_30_trains, arrival_delayed_over_60_trains,
    is_arrival_delay_rate_usable, is_important_delay_rate_usable,
    mean_arrival_delay_late_minutes, mean_arrival_delay_all_minutes,
    cause_sum_pct, cause_profile_status, quality_reasons
from {{ ref('int_tgv_quality_flags') }}
where array_length(quality_reasons) > 0
order by (departure_station = 'DIJON VILLE' and arrival_station = 'PARIS LYON'
    and month = date '2025-01-01') desc,
    (cause_profile_status = 'sum_warning') desc, row_number
limit 100
