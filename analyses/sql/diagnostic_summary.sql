-- Comptages de liaisons, jamais de trains distincts entre liaisons.
with diagnostic as ({{ j06_diagnostic(sensitivity=true) }}), ranked as ({{ j06_rank('diagnostic') }}),
baseline as (select * from ranked where is_reference)
select r.version_id,r.comparison_id,r.scenario_id,r.minimum_volume,r.change_threshold_pp,r.target_pct,
    count(*) as candidates,countif(r.is_eligible) as eligible_routes,
    countif(r.change_signal='deterioration') as deterioration_routes,
    countif(r.change_signal='improvement') as improvement_routes,
    countif(r.change_signal='below_project_threshold') as below_threshold_routes,
    if(logical_or(r.persistence_applicable),countif(r.is_deterioration_persistent),null) as persistent_deterioration_routes,
    if(logical_or(r.persistence_applicable),countif(r.is_underperformance_persistent),null) as persistent_underperformance_routes,
    if(logical_or(r.persistence_applicable),countif(r.is_underperformance_persistent and r.change_signal='improvement'),null) as improving_underperformance_routes,
    countif(r.deterioration_rank<=5) as deterioration_top_routes,
    if(logical_or(r.persistence_applicable),countif(r.underperformance_rank<=5),null) as underperformance_top_routes,
    countif(r.deterioration_rank<=5 and b.deterioration_rank<=5) as deterioration_top_overlap,
    if(logical_or(r.persistence_applicable),countif(r.underperformance_rank<=5 and b.underperformance_rank<=5),null) as underperformance_top_overlap,
    countif(r.is_eligible and not b.is_eligible) as eligible_entries,
    countif(not r.is_eligible and b.is_eligible) as eligible_exits
from ranked r join baseline b using(version_id,route_key,service_key,comparison_id)
group by 1,2,3,4,5,6 order by r.comparison_id,r.scenario_id
