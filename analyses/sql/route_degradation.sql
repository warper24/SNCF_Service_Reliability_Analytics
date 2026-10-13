-- Tous les candidats : les exclusions demeurent visibles, jamais classées.
with diagnostic as ({{ j06_diagnostic() }}), ranked as ({{ j06_rank('diagnostic') }})
select * from ranked order by comparison_id,deterioration_rank nulls last,departure_station,arrival_station
