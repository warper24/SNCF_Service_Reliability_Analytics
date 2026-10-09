{{ config(tags=['j04']) }}
{{ config(severity='warn') }}
select * from {{ ref('int_tgv_quality_flags') }}
where not central_counts_compatible or not is_departure_delay_count_usable
    or not important_delay_nesting_valid
    or (select countif(value < 0) from unnest([
        scheduled_trains, cancelled_trains, departure_delayed_trains,
        arrival_delayed_trains, arrival_delayed_over_15_trains,
        arrival_delayed_over_30_trains, arrival_delayed_over_60_trains
    ]) value) > 0
    or (select countif(value > operated_trains_proxy) from unnest([
        departure_delayed_trains, arrival_delayed_trains, arrival_delayed_over_15_trains,
        arrival_delayed_over_30_trains, arrival_delayed_over_60_trains
    ]) value) > 0
