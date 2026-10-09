{{ config(tags=['j04']) }}
select coalesce(s.row_number, q.row_number) as row_number
from {{ ref('stg_tgv_reliability') }} s
full outer join {{ ref('int_tgv_quality_flags') }} q
    on s.row_number = q.row_number and s.version_id = q.version_id
where s.row_number is null or q.row_number is null
    or to_json_string(s) != to_json_string((select as struct q.* except (
        scheduled_population_valid, central_counts_compatible, is_important_delay_quarantined,
        cause_present_count, cause_out_of_bounds_count, cause_sum_pct, services_in_month,
        services_in_history, operated_trains_proxy, important_delay_nesting_valid,
        is_cause_profile_complete, is_cause_profile_all_zero, has_cause_sum_warning,
        is_cancellation_count_usable, is_cancellation_rate_usable, is_arrival_delay_count_usable,
        is_arrival_delay_rate_usable, is_departure_delay_count_usable,
        is_important_delay_count_usable, is_important_delay_rate_usable,
        is_cause_profile_usable, is_mean_arrival_delay_late_usable,
        is_mean_departure_delay_late_usable, is_over_15_generic_usable,
        has_negative_mean_departure_all, has_negative_mean_arrival_all,
        has_negative_mean_arrival_late, has_negative_mean_departure_late,
        has_negative_scheduled_duration, has_multiple_services_in_month,
        has_multiple_services_in_history, cause_profile_status, quality_reasons
    )))
