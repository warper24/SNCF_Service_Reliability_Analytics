-- Chaque ligne donne un contrôle réellement exécuté et son nombre d'écarts.
with diagnostic as ({{ j06_diagnostic(sensitivity=true) }}), ranked as ({{ j06_rank('diagnostic') }}),
base as (select * from ranked where is_reference),
decomposed as ({{ j06_decomposition('base') }}),
reference_differences as (
    select b.route_key from base b full join {{ ref('mart_route_priorities') }} m
        using(version_id,route_key,service_key,comparison_id)
    where b.version_id is null or m.version_id is null
        or b.is_eligible is distinct from m.is_comparison_eligible
        or b.change_signal is distinct from m.change_signal
        or b.change_pp is distinct from m.arrival_delay_change_pp
        or b.services_in_comparison is distinct from m.services_in_comparison
        or b.deterioration_months is distinct from m.deterioration_months
        or b.underperformance_months is distinct from m.underperformance_months
        or b.is_deterioration_persistent is distinct from m.is_deterioration_persistent
        or b.is_underperformance_persistent is distinct from m.is_underperformance_persistent
        {% for side in ['current','previous'] %}
        or b.{{ side }}_observed_months is distinct from m.{{ side }}_observed_months
        or b.{{ side }}_eligible_months is distinct from m.{{ side }}_eligible_months
        or b.{{ side }}_n is distinct from m.{{ side }}_arrival_denominator
        or b.{{ side }}_l is distinct from m.{{ side }}_arrival_numerator
        or b.{{ side }}_rate is distinct from m.{{ side }}_arrival_delay_rate
        or b.{{ side }}_cancellation_rate is distinct from m.{{ side }}_cancellation_rate
        {% endfor %}
), expected_rank as (
    select a.version_id,a.comparison_id,a.route_key,a.service_key,a.deterioration_rank,
        1+countif(b.is_deterioration_persistent and not coalesce(a.is_deterioration_persistent,false)
            or coalesce(b.is_deterioration_persistent,false)=coalesce(a.is_deterioration_persistent,false)
            and (b.change_pp>a.change_pp or b.change_pp=a.change_pp and b.current_l>a.current_l)) as expected_rank
    from base a join base b on a.version_id=b.version_id and a.comparison_id=b.comparison_id
        and b.change_signal='deterioration'
    where a.change_signal='deterioration' group by 1,2,3,4,5
), expected_under_rank as (
    select a.version_id,a.comparison_id,a.route_key,a.service_key,a.underperformance_rank,
        1+countif(b.underperformance_months>a.underperformance_months
            or b.underperformance_months=a.underperformance_months
            and (b.current_rate>a.current_rate or b.current_rate=a.current_rate and b.current_l>a.current_l)) as expected_rank
    from base a join base b on a.version_id=b.version_id and a.comparison_id=b.comparison_id
        and b.is_underperformance_persistent
    where a.is_underperformance_persistent group by 1,2,3,4,5
)
select 'reference_equals_j05' as check_name,count(*) as failures from reference_differences
union all select 'unique_scenario_grain',count(*) from (
    select version_id,route_key,service_key,comparison_id,scenario_id from ranked group by 1,2,3,4,5 having count(*)!=1)
union all select 'scenario_coverage',count(*) from (
    select version_id,route_key,service_key,comparison_id from ranked group by 1,2,3,4 having count(*)!=27 or countif(is_reference)!=1)
union all select 'exclusions_and_unavailable_ranks',countif(
    is_eligible != (array_length(exclusion_reasons)=0)
    or not is_eligible and (deterioration_rank is not null or underperformance_rank is not null or change_pp is not null)
    or not persistence_applicable and (is_deterioration_persistent is not null or is_underperformance_persistent is not null or underperformance_rank is not null)) from ranked
union all select 'decomposition_identity',countif(reconciliation_residual is null or abs(reconciliation_residual)>numeric '0.01') from decomposed
union all select 'degradation_rank_order',countif(e.deterioration_rank!=e.expected_rank) from expected_rank e
union all select 'underperformance_rank_order',countif(e.underperformance_rank!=e.expected_rank) from expected_under_rank e
union all select 'volume_eligibility_monotonic',count(*) from ranked a join ranked b
    using(version_id,route_key,service_key,comparison_id,change_threshold_pp,target_pct)
    where a.minimum_volume>b.minimum_volume and a.is_eligible and not b.is_eligible
union all select 'target_does_not_change_degradation_rank',count(*) from ranked a join ranked b
    using(version_id,route_key,service_key,comparison_id,minimum_volume,change_threshold_pp)
    where a.target_pct<b.target_pct and a.deterioration_rank is distinct from b.deterioration_rank
union all select 'variation_does_not_change_underperformance_rank',count(*) from ranked a join ranked b
    using(version_id,route_key,service_key,comparison_id,minimum_volume,target_pct)
    where a.change_threshold_pp<b.change_threshold_pp and a.underperformance_rank is distinct from b.underperformance_rank
