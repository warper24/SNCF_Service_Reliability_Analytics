-- D01–D07 : conserver les valeurs ; expliciter les usages et leurs réserves.
with base as (
    select
        *,
        coalesce(scheduled_trains >= 0 and cancelled_trains >= 0
            and cancelled_trains <= scheduled_trains, false) as scheduled_population_valid,
        coalesce(scheduled_trains >= 0 and cancelled_trains >= 0
            and cancelled_trains <= scheduled_trains and arrival_delayed_trains >= 0
            and arrival_delayed_trains <= scheduled_trains - cancelled_trains,
            false) as central_counts_compatible,
        coalesce(month >= date '2025-01-01' and month < date '2025-04-01', false)
            as is_important_delay_quarantined,
        (select countif(value is not null) from unnest([
            external_cause_pct, infrastructure_cause_pct, traffic_management_cause_pct,
            rolling_stock_cause_pct, station_management_cause_pct, passenger_handling_cause_pct
        ]) value) as cause_present_count,
        (select countif(value < 0 or value > 100) from unnest([
            external_cause_pct, infrastructure_cause_pct, traffic_management_cause_pct,
            rolling_stock_cause_pct, station_management_cause_pct, passenger_handling_cause_pct
        ]) value) as cause_out_of_bounds_count,
        external_cause_pct + infrastructure_cause_pct + traffic_management_cause_pct
            + rolling_stock_cause_pct + station_management_cause_pct
            + passenger_handling_cause_pct as cause_sum_pct,
        count(distinct service_type) over (
            partition by month, departure_station, arrival_station
        ) as services_in_month,
        count(distinct service_type) over (
            partition by departure_station, arrival_station
        ) as services_in_history
    from {{ ref('stg_tgv_reliability') }}
), populations as (
    select
        *,
        case when scheduled_population_valid
            then scheduled_trains - cancelled_trains end as operated_trains_proxy,
        coalesce(arrival_delayed_over_60_trains >= 0
            and arrival_delayed_over_30_trains >= arrival_delayed_over_60_trains
            and arrival_delayed_trains >= arrival_delayed_over_30_trains,
            false) as important_delay_nesting_valid,
        cause_present_count = 6 as is_cause_profile_complete,
        coalesce(cause_present_count = 6 and cause_sum_pct = 0
            and cause_out_of_bounds_count = 0, false) as is_cause_profile_all_zero,
        -- 0,1 point métier ; 1e-9 point absorbe uniquement l'erreur flottante de frontière.
        coalesce(cause_present_count = 6 and cause_sum_pct > 0
            and abs(cause_sum_pct - 100) > 0.1 + 1e-9, false) as has_cause_sum_warning
    from base
), usability as (
    select
        *,
        scheduled_population_valid as is_cancellation_count_usable,
        scheduled_population_valid and coalesce(scheduled_trains > 0, false)
            as is_cancellation_rate_usable,
        central_counts_compatible as is_arrival_delay_count_usable,
        central_counts_compatible and coalesce(operated_trains_proxy > 0, false)
            as is_arrival_delay_rate_usable,
        scheduled_population_valid and coalesce(departure_delayed_trains >= 0
            and departure_delayed_trains <= operated_trains_proxy, false)
            as is_departure_delay_count_usable,
        central_counts_compatible and important_delay_nesting_valid
            and not is_important_delay_quarantined as is_important_delay_count_usable,
        central_counts_compatible and important_delay_nesting_valid
            and not is_important_delay_quarantined and coalesce(operated_trains_proxy > 0, false)
            as is_important_delay_rate_usable,
        -- D03 : un profil hors tolérance reste visible avec avertissement ; pas de renormalisation.
        is_cause_profile_complete and cause_out_of_bounds_count = 0
            and not is_cause_profile_all_zero as is_cause_profile_usable,
        central_counts_compatible and coalesce(arrival_delayed_trains > 0
            and mean_arrival_delay_late_minutes >= 0, false) as is_mean_arrival_delay_late_usable,
        scheduled_population_valid and coalesce(departure_delayed_trains > 0
            and departure_delayed_trains <= operated_trains_proxy
            and mean_departure_delay_late_minutes >= 0, false) as is_mean_departure_delay_late_usable,
        false as is_over_15_generic_usable,
        coalesce(mean_departure_delay_all_minutes < 0, false)
            as has_negative_mean_departure_all,
        coalesce(mean_arrival_delay_all_minutes < 0, false)
            as has_negative_mean_arrival_all,
        coalesce(mean_arrival_delay_late_minutes < 0, false)
            as has_negative_mean_arrival_late,
        coalesce(mean_departure_delay_late_minutes < 0, false)
            as has_negative_mean_departure_late,
        coalesce(scheduled_duration_minutes < 0, false) as has_negative_scheduled_duration,
        services_in_month > 1 as has_multiple_services_in_month,
        services_in_history > 1 as has_multiple_services_in_history
    from populations
)
select
    *,
    case
        when not is_cause_profile_complete then 'missing'
        when cause_out_of_bounds_count > 0 then 'out_of_bounds'
        when is_cause_profile_all_zero then 'all_zero'
        when has_cause_sum_warning then 'sum_warning'
        else 'available'
    end as cause_profile_status,
    array(
        select reason from unnest([
            if(not scheduled_population_valid, 'incompatible_scheduled_population', null),
            if(not central_counts_compatible, 'incompatible_central_counts', null),
            if(scheduled_population_valid and scheduled_trains = 0, 'zero_scheduled_population', null),
            if(operated_trains_proxy = 0, 'zero_operated_proxy', null),
            if(is_important_delay_quarantined, 'important_delay_quarantine_2025_q1', null),
            if(not important_delay_nesting_valid, 'important_delay_nesting', null),
            if(not is_cause_profile_complete, 'missing_cause_values', null),
            if(cause_out_of_bounds_count > 0, 'cause_out_of_bounds', null),
            if(is_cause_profile_all_zero, 'all_zero_cause_profile', null),
            if(has_cause_sum_warning, 'cause_sum_outside_tolerance', null),
            if(has_negative_mean_arrival_late, 'negative_mean_arrival_late', null),
            if(has_negative_mean_departure_late, 'negative_mean_departure_late', null),
            if(has_negative_mean_arrival_all, 'negative_mean_arrival_all', null),
            if(has_negative_mean_departure_all, 'negative_mean_departure_all', null),
            if(has_negative_scheduled_duration, 'negative_scheduled_duration', null),
            if(has_multiple_services_in_month, 'multiple_services_in_month', null)
        ]) reason where reason is not null
    ) as quality_reasons
from usability
