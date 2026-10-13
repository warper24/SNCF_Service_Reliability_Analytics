{% macro j06_scenarios(sensitivity=false) -%}
select n as minimum_volume, d as change_threshold_pp, t as target_pct,
    format('n%d_d%d_t%d', n, d, t) as scenario_id,
    n = 30 and d = 2 and t = 90 as is_reference
from unnest({{ '[15,30,60]' if sensitivity else '[30]' }}) n
cross join unnest({{ '[1,2,3]' if sensitivity else '[2]' }}) d
cross join unnest({{ '[85,90,95]' if sensitivity else '[90]' }}) t
{%- endmacro %}

{% macro j06_diagnostic(source_relation=none, sensitivity=false) -%}
-- Une grille explicite rend les mois absents visibles. Les seuils des scénarios
-- sont appliqués aux effectifs, jamais aux drapeaux J05 précalculés à N≥30.
with source_rows as (
    select * from {{ source_relation if source_relation else ref('fct_reliability_monthly') }}
), windows as ({{ comparison_windows() }}), scenarios as ({{ j06_scenarios(sensitivity) }}),
candidates as (
    select distinct version_id, route_key, service_key, departure_station, arrival_station, service_type
    from source_rows where service_type = 'National'
), scope as (
    select f.version_id, f.route_key, w.comparison_id, count(distinct f.service_type) as services_in_comparison
    from source_rows f join windows w on f.month between w.current_start and w.current_end
        or f.month between date_sub(w.current_start, interval 1 year) and date_sub(w.current_end, interval 1 year)
    group by 1,2,3
), pairs as (
    select k.*, w.*, m as current_month, coalesce(s.services_in_comparison,0) as services_in_comparison,
        {% for side, alias in [('current','c'),('previous','p')] %}
        {{ alias }}.month as {{ side }}_observed_month,
        {{ alias }}.central_counts_compatible as {{ side }}_compatible,
        {{ alias }}.operated_trains_proxy as {{ side }}_n,
        {{ alias }}.arrival_delayed_trains as {{ side }}_l,
        {{ alias }}.scheduled_trains as {{ side }}_p,
        {{ alias }}.cancelled_trains as {{ side }}_a,
        {{ alias }}.is_cancellation_rate_usable as {{ side }}_cancellation_usable,
        {{ alias }}.is_arrival_delay_rate_usable as {{ side }}_arrival_usable,
        {% endfor %}
        c.month is not null and p.month is not null as has_pair
    from candidates k cross join windows w
    cross join unnest(generate_date_array(w.current_start,w.current_end,interval 1 month)) m
    left join source_rows c on c.version_id=k.version_id and c.route_key=k.route_key
        and c.service_key=k.service_key and c.month=m
    left join source_rows p on p.version_id=k.version_id and p.route_key=k.route_key
        and p.service_key=k.service_key and p.month=date_sub(m,interval 1 year)
    left join scope s on s.version_id=k.version_id and s.route_key=k.route_key and s.comparison_id=w.comparison_id
), aggregated as (
    select version_id, route_key, service_key, departure_station, arrival_station, service_type,
        comparison_id,current_start,current_end,expected_months,persistence_applicable,services_in_comparison,
        scenario_id,is_reference,minimum_volume,change_threshold_pp,target_pct,
        {% for side in ['current','previous'] %}
        count({{ side }}_observed_month) as {{ side }}_observed_months,
        countif({{ side }}_compatible and {{ side }}_n >= minimum_volume) as {{ side }}_eligible_months,
        countif({{ side }}_observed_month is not null and not coalesce({{ side }}_compatible,false)) as {{ side }}_invalid_months,
        countif({{ side }}_compatible and {{ side }}_n < minimum_volume) as {{ side }}_low_volume_months,
        countif({{ side }}_arrival_usable) as {{ side }}_arrival_valid_months,
        countif({{ side }}_cancellation_usable) as {{ side }}_cancellation_valid_months,
        sum(if({{ side }}_arrival_usable,{{ side }}_n,null)) as {{ side }}_n,
        sum(if({{ side }}_arrival_usable,{{ side }}_l,null)) as {{ side }}_l,
        sum(if({{ side }}_cancellation_usable,{{ side }}_p,null)) as {{ side }}_p,
        sum(if({{ side }}_cancellation_usable,{{ side }}_a,null)) as {{ side }}_a,
        {% endfor %}
        countif(current_compatible and previous_compatible and current_n >= minimum_volume and previous_n >= minimum_volume
            and 100 * (cast(current_l as numeric)*previous_n-cast(previous_l as numeric)*current_n)
                >= change_threshold_pp * cast(current_n as numeric)*previous_n) as deterioration_months,
        countif(current_compatible and current_n >= minimum_volume
            and 100 * cast(current_n-current_l as numeric) < target_pct * cast(current_n as numeric)) as underperformance_months
    from pairs cross join scenarios
    group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17
), rates as (
    select *, date_sub(current_start,interval 1 year) as previous_start,
        date_sub(current_end,interval 1 year) as previous_end,
        current_eligible_months=expected_months and previous_eligible_months=expected_months
            and services_in_comparison=1 as is_eligible,
        {% for side in ['current','previous'] %}
        {{ reference_ratio(side ~ '_l',side ~ '_n',side ~ '_arrival_valid_months=expected_months') }} as {{ side }}_rate,
        {{ reference_ratio(side ~ '_a',side ~ '_p',side ~ '_cancellation_valid_months=expected_months') }} as {{ side }}_cancellation_rate,
        {% endfor %}
        array(select reason from unnest([
            if(current_observed_months!=expected_months,'missing_current_months',null),
            if(previous_observed_months!=expected_months,'missing_previous_months',null),
            if(current_invalid_months>0,'invalid_current_counts',null),
            if(previous_invalid_months>0,'invalid_previous_counts',null),
            if(current_low_volume_months>0,'low_current_volume',null),
            if(previous_low_volume_months>0,'low_previous_volume',null),
            if(services_in_comparison!=1,'ambiguous_or_absent_service_scope',null)
        ]) reason where reason is not null) as exclusion_reasons
    from aggregated
), classified as (
    select *,
        case when is_eligible then {{ change_pp('current_l','current_n','previous_l','previous_n') }} end as change_pp,
        case when not is_eligible then 'ineligible'
            when 100*(cast(current_l as numeric)*previous_n-cast(previous_l as numeric)*current_n)
                >= change_threshold_pp*cast(current_n as numeric)*previous_n then 'deterioration'
            when 100*(cast(current_l as numeric)*previous_n-cast(previous_l as numeric)*current_n)
                <= -change_threshold_pp*cast(current_n as numeric)*previous_n then 'improvement'
            else 'below_project_threshold' end as change_signal,
        case when is_eligible and persistence_applicable then deterioration_months>=4 end as is_deterioration_persistent,
        case when is_eligible and persistence_applicable then underperformance_months>=4 end as is_underperformance_persistent,
        'derived_population_not_certified_D01' as denominator_status
    from rates
)
select * from classified
{%- endmacro %}

{% macro j06_rank(relation) -%}
select *,
    case when change_signal='deterioration' then rank() over (
        partition by version_id,comparison_id,scenario_id
        order by (change_signal='deterioration') desc,
            coalesce(is_deterioration_persistent,false) desc,change_pp desc,current_l desc
    ) end as deterioration_rank,
    case when is_underperformance_persistent then rank() over (
        partition by version_id,comparison_id,scenario_id
        order by coalesce(is_underperformance_persistent,false) desc,
            underperformance_months desc,current_rate desc,current_l desc
    ) end as underperformance_rank
from {{ relation }}
{%- endmacro %}

{% macro j06_decomposition(relation) -%}
with components as (
    select *, current_l-previous_l as delta_l,
        safe_divide(cast(current_n-previous_n as numeric)*previous_l,previous_n) as volume_effect,
        safe_divide(cast(current_l as numeric)*previous_n-cast(previous_l as numeric)*current_n,previous_n) as rate_effect
    from {{ relation }} where is_eligible
)
select *, cast(delta_l as numeric)-volume_effect-rate_effect as reconciliation_residual from components
{%- endmacro %}
