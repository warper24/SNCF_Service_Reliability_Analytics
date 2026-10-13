with diagnostic as ({{ j06_diagnostic() }}), decomposed as ({{ j06_decomposition('diagnostic') }})
select version_id,route_key,service_key,departure_station,arrival_station,service_type,
    comparison_id,current_start,current_end,previous_start,previous_end,current_n,previous_n,
    current_l,previous_l,current_rate,previous_rate,change_pp,change_signal,
    delta_l,volume_effect,rate_effect,reconciliation_residual,denominator_status
from decomposed order by comparison_id,departure_station,arrival_station
