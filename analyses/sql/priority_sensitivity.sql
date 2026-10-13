with diagnostic as ({{ j06_diagnostic(sensitivity=true) }}), ranked as ({{ j06_rank('diagnostic') }}),
baseline as (select * from ranked where is_reference)
select r.version_id,r.route_key,r.service_key,r.departure_station,r.arrival_station,r.service_type,
    r.comparison_id,r.current_start,r.current_end,r.previous_start,r.previous_end,
    r.scenario_id,r.is_reference,r.minimum_volume,r.change_threshold_pp,r.target_pct,
    r.is_eligible,r.current_eligible_months,r.previous_eligible_months,r.exclusion_reasons,
    r.change_pp,r.change_signal,r.deterioration_months,r.underperformance_months,
    r.is_deterioration_persistent,r.is_underperformance_persistent,
    r.deterioration_rank,r.underperformance_rank,
    b.is_eligible as baseline_eligible,b.change_signal as baseline_signal,
    b.deterioration_rank as baseline_deterioration_rank,b.underperformance_rank as baseline_underperformance_rank,
    r.deterioration_rank-b.deterioration_rank as deterioration_rank_shift,
    r.underperformance_rank-b.underperformance_rank as underperformance_rank_shift,
    countif(r.is_eligible) over route_window as eligible_scenarios,
    countif(r.deterioration_rank<=5) over route_window as deterioration_top_scenarios,
    if(r.persistence_applicable,countif(r.underperformance_rank<=5) over route_window,null) as underperformance_top_scenarios,
    min(r.deterioration_rank) over route_window as minimum_deterioration_rank,
    max(r.deterioration_rank) over route_window as maximum_deterioration_rank
from ranked r join baseline b using(version_id,route_key,service_key,comparison_id)
window route_window as (partition by r.version_id,r.route_key,r.service_key,r.comparison_id)
order by r.comparison_id,r.scenario_id,r.departure_station,r.arrival_station
