-- Sélection avant examen des causes ; aucune agrégation de leurs pourcentages.
with diagnostic as ({{ j06_diagnostic() }}), ranked as ({{ j06_rank('diagnostic') }}),
selected as (
    select * from ranked where comparison_id='2026_h1_vs_2025_h1'
        and (deterioration_rank<=5 or underperformance_rank<=5)
), months as (
    select s.*, period_side,m as month from selected s
    cross join unnest(['current','previous']) period_side
    cross join unnest(generate_date_array(
        if(period_side='current',current_start,previous_start),
        if(period_side='current',current_end,previous_end),interval 1 month)) m
)
select m.version_id,m.route_key,m.service_key,m.departure_station,m.arrival_station,m.service_type,
    m.comparison_id,m.period_side,m.month,m.deterioration_rank,m.underperformance_rank,
    d.cause_key,d.cause_label,d.source_field,c.published_cause_pct,
    c.cause_profile_status,c.is_cause_profile_usable,c.cause_sum_pct,c.has_cause_sum_warning,
    c.row_sha256,c.row_number, c.month is not null as observation_present,
    f.arrival_delay_comment
from months m cross join {{ ref('dim_cause') }} d
left join {{ ref('fct_delay_causes_monthly') }} c on c.version_id=m.version_id
    and c.route_key=m.route_key and c.service_key=m.service_key and c.month=m.month and c.cause_key=d.cause_key
left join {{ ref('fct_reliability_monthly') }} f on f.version_id=m.version_id
    and f.route_key=m.route_key and f.service_key=m.service_key and f.month=m.month
order by m.departure_station,m.arrival_station,m.month,d.cause_key
