-- Variables de diagnostic, sans classement ni score. Fenêtres fixées avant analyse.
with windows as ({{ comparison_windows() }}), candidates as (
    select distinct version_id, route_key, service_key
    from {{ ref('fct_reliability_monthly') }} where service_type = 'National'
), scope as (
    select f.version_id, f.route_key, w.comparison_id,
        count(distinct f.service_type) as services_in_comparison
    from {{ ref('fct_reliability_monthly') }} f
    join windows w on f.month between w.current_start and w.current_end
        or f.month between date_sub(w.current_start, interval 1 year) and date_sub(w.current_end, interval 1 year)
    group by 1,2,3
), grid as (
    select c.*, w.*, d.date_key as current_month
    from candidates c cross join windows w
    join {{ ref('dim_date') }} d on d.is_month_start and d.date_key between w.current_start and w.current_end
), aggregated as (
    select g.version_id, g.route_key, g.service_key, g.comparison_id,
        g.current_start, g.current_end, g.expected_months, g.persistence_applicable,
        coalesce(s.services_in_comparison, 0) as services_in_comparison,
        {% for side, alias in [('current', 'c'), ('previous', 'p')] %}
        count({{ alias }}.month) as {{ side }}_observed_months,
        countif({{ alias }}.central_counts_compatible and {{ alias }}.operated_trains_proxy >= {{ var('minimum_monthly_operated_proxy') }}) as {{ side }}_eligible_months,
        countif({{ alias }}.is_cancellation_rate_usable) as {{ side }}_cancellation_valid_months,
        countif({{ alias }}.is_arrival_delay_rate_usable) as {{ side }}_arrival_valid_months,
        countif({{ alias }}.is_important_delay_rate_usable) as {{ side }}_important_valid_months,
        countif({{ alias }}.is_important_delay_count_usable) as {{ side }}_important_count_valid_months,
        sum(if({{ alias }}.is_cancellation_rate_usable, {{ alias }}.cancelled_trains, null)) as {{ side }}_cancellation_numerator,
        sum(if({{ alias }}.is_cancellation_rate_usable, {{ alias }}.scheduled_trains, null)) as {{ side }}_cancellation_denominator,
        sum(if({{ alias }}.is_arrival_delay_rate_usable, {{ alias }}.arrival_delayed_trains, null)) as {{ side }}_arrival_numerator,
        sum(if({{ alias }}.is_arrival_delay_rate_usable, {{ alias }}.operated_trains_proxy, null)) as {{ side }}_arrival_denominator,
        sum(if({{ alias }}.is_important_delay_rate_usable, {{ alias }}.arrival_delayed_over_30_trains, null)) as {{ side }}_over_30_numerator,
        sum(if({{ alias }}.is_important_delay_rate_usable, {{ alias }}.arrival_delayed_over_60_trains, null)) as {{ side }}_over_60_numerator,
        sum(if({{ alias }}.is_important_delay_rate_usable, {{ alias }}.operated_trains_proxy, null)) as {{ side }}_important_denominator,
        sum({{ alias }}.over_30_delay_count) as {{ side }}_over_30_valid_count_sum,
        sum({{ alias }}.over_60_delay_count) as {{ side }}_over_60_valid_count_sum,
        {% endfor %}
        countif(c.passes_pair_volume_screen) as eligible_month_pairs,
        countif(c.is_monthly_deterioration) as deterioration_months,
        countif(c.is_monthly_underperformance) as underperformance_months
    from grid g
    left join {{ ref('mart_route_trends') }} c on c.version_id = g.version_id
        and c.route_key = g.route_key and c.service_key = g.service_key and c.month = g.current_month
    left join {{ ref('fct_reliability_monthly') }} p on p.version_id = g.version_id
        and p.route_key = g.route_key and p.service_key = g.service_key
        and p.month = date_sub(g.current_month, interval 1 year)
    left join scope s on s.version_id = g.version_id and s.route_key = g.route_key and s.comparison_id = g.comparison_id
    group by 1,2,3,4,5,6,7,8,9
), rates as (
    select *,
        date_sub(current_start, interval 1 year) as previous_start,
        date_sub(current_end, interval 1 year) as previous_end,
        current_eligible_months = expected_months and previous_eligible_months = expected_months
            and services_in_comparison = 1 as is_comparison_eligible,
        {% for side in ['current', 'previous'] %}
        safe_divide({{ side }}_observed_months, expected_months) as {{ side }}_observation_coverage,
        {{ reference_ratio(side ~ '_cancellation_numerator', side ~ '_cancellation_denominator', side ~ '_cancellation_valid_months = expected_months') }} as {{ side }}_cancellation_rate,
        {{ reference_ratio(side ~ '_arrival_numerator', side ~ '_arrival_denominator', side ~ '_arrival_valid_months = expected_months') }} as {{ side }}_arrival_delay_rate,
        {{ reference_ratio(side ~ '_arrival_denominator - ' ~ side ~ '_arrival_numerator', side ~ '_arrival_denominator', side ~ '_arrival_valid_months = expected_months') }} as {{ side }}_composite_regularity_rate,
        {{ reference_ratio(side ~ '_over_30_numerator', side ~ '_important_denominator', side ~ '_important_valid_months = expected_months') }} as {{ side }}_over_30_delay_rate,
        {{ reference_ratio(side ~ '_over_60_numerator', side ~ '_important_denominator', side ~ '_important_valid_months = expected_months') }} as {{ side }}_over_60_delay_rate,
        {% endfor %}
        array(select reason from unnest([
            if(current_observed_months != expected_months, 'missing_current_months', null),
            if(previous_observed_months != expected_months, 'missing_previous_months', null),
            if(current_eligible_months != expected_months, 'invalid_or_low_volume_current', null),
            if(previous_eligible_months != expected_months, 'invalid_or_low_volume_previous', null),
            if(services_in_comparison != 1, 'ambiguous_or_absent_service_scope', null)
        ]) reason where reason is not null) as exclusion_reasons
    from aggregated
)
select *,
    case when is_comparison_eligible then
        {{ change_pp('current_arrival_numerator', 'current_arrival_denominator', 'previous_arrival_numerator', 'previous_arrival_denominator') }}
    end as arrival_delay_change_pp,
    case when not is_comparison_eligible then 'ineligible'
        when {{ deterioration('current_arrival_numerator', 'current_arrival_denominator', 'previous_arrival_numerator', 'previous_arrival_denominator') }} then 'deterioration'
        when {{ deterioration('current_arrival_numerator', 'current_arrival_denominator', 'previous_arrival_numerator', 'previous_arrival_denominator', -1) }} then 'improvement'
        else 'below_project_threshold' end as change_signal,
    case when is_comparison_eligible and persistence_applicable then safe_divide(deterioration_months, eligible_month_pairs) end as deterioration_persistence,
    case when is_comparison_eligible and persistence_applicable then safe_divide(underperformance_months, current_eligible_months) end as underperformance_persistence,
    case when is_comparison_eligible and persistence_applicable then deterioration_months >= {{ var('persistence_months') }} end as is_deterioration_persistent,
    case when is_comparison_eligible and persistence_applicable then underperformance_months >= {{ var('persistence_months') }} end as is_underperformance_persistent,
    {{ var('minimum_monthly_operated_proxy') }} as minimum_monthly_operated_proxy,
    {{ var('deterioration_threshold_pp') }} as deterioration_threshold_pp,
    {{ var('regularity_target_pct') }} as regularity_target_pct,
    'derived_population_not_certified_D01' as denominator_status
from rates
