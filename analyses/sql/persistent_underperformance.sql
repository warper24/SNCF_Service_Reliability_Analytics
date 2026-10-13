-- Une amélioration peut coexister avec un niveau durablement sous la cible fictive.
with diagnostic as ({{ j06_diagnostic() }}), ranked as ({{ j06_rank('diagnostic') }})
select * from ranked order by comparison_id,underperformance_rank nulls last,departure_station,arrival_station
