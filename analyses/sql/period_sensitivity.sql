-- Populations propres, intersection puis rangs : ne pas confondre changement
-- de calendrier et changement de population. Persistance annuelle non définie.
with diagnostic as ({{ j06_diagnostic() }}), ranked as ({{ j06_rank('diagnostic') }}),
h as (select * from ranked where comparison_id='2026_h1_vs_2025_h1'),
y as (select * from ranked where comparison_id='2025_vs_2024'),
common_population as (
    select r.* except(deterioration_rank,underperformance_rank) from ranked r join h using(version_id,route_key,service_key)
    join y using(version_id,route_key,service_key) where h.is_eligible and y.is_eligible
), common_ranked as (
    -- Même règle sur les deux fenêtres : variation puis volume. La persistance
    -- n'entre pas dans ce rang comparatif puisqu'elle n'est pas définie à l'année.
    select *,case when change_signal='deterioration' then rank() over (
        partition by version_id,comparison_id
        order by (change_signal='deterioration') desc,change_pp desc,current_l desc
    ) end as deterioration_rank from common_population
)
, compared as (
select h.version_id,h.route_key,h.service_key,h.departure_station,h.arrival_station,
    h.is_eligible as semester_eligible,y.is_eligible as year_eligible,
    h.is_eligible and y.is_eligible as common_eligible,
    h.change_signal as semester_signal,y.change_signal as year_signal,
    h.change_pp as semester_change_pp,y.change_pp as year_change_pp,
    h.deterioration_rank as semester_rank,y.deterioration_rank as year_rank,
    ch.deterioration_rank as common_semester_rank,cy.deterioration_rank as common_year_rank
from h join y using(version_id,route_key,service_key)
left join common_ranked ch on ch.version_id=h.version_id and ch.route_key=h.route_key
    and ch.service_key=h.service_key and ch.comparison_id=h.comparison_id
left join common_ranked cy on cy.version_id=y.version_id and cy.route_key=y.route_key
    and cy.service_key=y.service_key and cy.comparison_id=y.comparison_id
)
select *,
    countif(common_eligible) over() as common_eligible_routes,
    countif(semester_eligible and not year_eligible) over() as semester_only_eligible_routes,
    countif(year_eligible and not semester_eligible) over() as year_only_eligible_routes,
    countif(common_eligible and semester_signal='deterioration' and year_signal='deterioration') over() as common_deterioration_both_routes
from compared order by departure_station,arrival_station
