{{ config(tags=['j04']) }}
select * from {{ ref('int_tgv_quality_flags') }}
where (is_cancellation_count_usable and not coalesce(0 <= cancelled_trains
        and cancelled_trains <= scheduled_trains, false))
    or (is_cancellation_rate_usable and not coalesce(scheduled_trains > 0
        and is_cancellation_count_usable, false))
    or (is_arrival_delay_count_usable and not coalesce(is_cancellation_count_usable
        and 0 <= arrival_delayed_trains and arrival_delayed_trains <= operated_trains_proxy, false))
    or (is_arrival_delay_rate_usable and not coalesce(is_arrival_delay_count_usable
        and operated_trains_proxy > 0, false))
    or (is_important_delay_count_usable and not coalesce(is_arrival_delay_count_usable
        and arrival_delayed_over_60_trains >= 0
        and arrival_delayed_over_60_trains <= arrival_delayed_over_30_trains
        and arrival_delayed_over_30_trains <= arrival_delayed_trains
        and not is_important_delay_quarantined, false))
    or (is_important_delay_rate_usable and not coalesce(is_important_delay_count_usable
        and operated_trains_proxy > 0, false))
    or (is_cause_profile_usable and (cause_present_count != 6
        or cause_out_of_bounds_count != 0 or is_cause_profile_all_zero))
    or (is_mean_arrival_delay_late_usable and coalesce(mean_arrival_delay_late_minutes < 0, true))
    or (is_mean_departure_delay_late_usable and coalesce(mean_departure_delay_late_minutes < 0, true))
    or is_over_15_generic_usable
    or (select countif(value is null) from unnest([
        scheduled_population_valid, central_counts_compatible, is_important_delay_quarantined,
        important_delay_nesting_valid, is_cause_profile_complete, is_cause_profile_all_zero,
        has_cause_sum_warning, is_cancellation_count_usable, is_cancellation_rate_usable,
        is_arrival_delay_count_usable, is_arrival_delay_rate_usable, is_departure_delay_count_usable,
        is_important_delay_count_usable, is_important_delay_rate_usable, is_cause_profile_usable,
        is_mean_arrival_delay_late_usable, is_mean_departure_delay_late_usable,
        is_over_15_generic_usable, has_negative_mean_departure_all, has_negative_mean_arrival_all,
        has_negative_mean_arrival_late, has_negative_mean_departure_late,
        has_negative_scheduled_duration, has_multiple_services_in_month,
        has_multiple_services_in_history
    ]) value) > 0
