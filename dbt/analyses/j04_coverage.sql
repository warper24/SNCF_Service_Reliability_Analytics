-- Trous internes : l'intervalle observé ne certifie aucune période de desserte.
with coverage as (
    select version_id, departure_station, arrival_station, service_type,
        min(month) as first_month, max(month) as last_month,
        count(*) as observed_rows, count(distinct month) as observed_months,
        countif(is_cancellation_rate_usable) as cancellation_valid_months,
        countif(is_arrival_delay_rate_usable) as arrival_delay_valid_months,
        countif(is_important_delay_rate_usable) as important_delay_valid_months,
        countif(is_cause_profile_usable) as cause_profile_usable_months,
        countif(has_multiple_services_in_month) as multiple_service_months,
        array_agg(month order by month) as present_months
    from {{ ref('int_tgv_quality_flags') }}
    group by 1,2,3,4
)
select * except(present_months),
    date_diff(last_month, first_month, month) + 1 as months_in_observed_interval,
    date_diff(last_month, first_month, month) + 1 - observed_months as internal_missing_months,
    array(select m from unnest(generate_date_array(first_month,last_month,interval 1 month)) m
        where m not in unnest(present_months)) as internal_missing_month_list
from coverage
order by service_type, departure_station, arrival_station
