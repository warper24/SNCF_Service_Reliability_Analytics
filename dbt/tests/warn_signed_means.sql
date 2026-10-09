{{ config(tags=['j04']) }}
{{ config(severity='warn') }}
select * from {{ ref('int_tgv_quality_flags') }}
where has_negative_mean_departure_all or has_negative_mean_arrival_all
    or has_negative_mean_arrival_late or has_negative_mean_departure_late
    or has_negative_scheduled_duration or mean_arrival_delay_over_15_minutes < 0
