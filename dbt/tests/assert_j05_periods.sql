{{ config(tags=['j05']) }}
-- Réconciliation depuis J04, indépendamment de la grille et des tendances du mart.
with windows as ({{ comparison_windows() }}), candidates as (
 select distinct version_id, departure_station, arrival_station, service_type
 from {{ ref('int_tgv_quality_flags') }} where service_type = 'National'
), expected as (
 select c.version_id, c.departure_station, c.arrival_station, c.service_type, w.comparison_id, w.expected_months,
 count(distinct q.service_type) as service_count,
 {% for side, start, end in [('current','w.current_start','w.current_end'),('previous','date_sub(w.current_start, interval 1 year)','date_sub(w.current_end, interval 1 year)')] %}
 countif(q.service_type='National' and q.month between {{ start }} and {{ end }}) as {{ side }}_observed,
 countif(q.service_type='National' and q.month between {{ start }} and {{ end }} and q.central_counts_compatible
     and q.operated_trains_proxy >= {{ var('minimum_monthly_operated_proxy') }}) as {{ side }}_eligible,
 {% for kind, mask, num, den in [
 ('arrival','is_arrival_delay_rate_usable','arrival_delayed_trains','operated_trains_proxy'),
 ('cancellation','is_cancellation_rate_usable','cancelled_trains','scheduled_trains'),
 ('important','is_important_delay_rate_usable','arrival_delayed_over_30_trains','operated_trains_proxy')] %}
 countif(q.service_type='National' and q.month between {{ start }} and {{ end }} and q.{{ mask }}) as {{ side }}_{{ kind }}_valid,
 sum(if(q.service_type='National' and q.month between {{ start }} and {{ end }} and q.{{ mask }}, q.{{ num }}, null)) as {{ side }}_{{ kind }}_num,
 sum(if(q.service_type='National' and q.month between {{ start }} and {{ end }} and q.{{ mask }}, q.{{ den }}, null)) as {{ side }}_{{ kind }}_den,
 {% endfor %}
 {% endfor %}
 count(*) as joined_rows
 from candidates c cross join windows w
 left join {{ ref('int_tgv_quality_flags') }} q on q.version_id=c.version_id
 and q.departure_station=c.departure_station and q.arrival_station=c.arrival_station
 and (q.month between w.current_start and w.current_end
     or q.month between date_sub(w.current_start, interval 1 year) and date_sub(w.current_end, interval 1 year))
 group by 1,2,3,4,5,6
), actual as (
 select m.*, d.departure_station, d.arrival_station, s.service_type
 from {{ ref('mart_route_priorities') }} m
 join {{ ref('dim_route') }} d using(route_key) join {{ ref('dim_service') }} s using(service_key)
)
select coalesce(e.departure_station,a.departure_station) as departure_station,
    coalesce(e.arrival_station,a.arrival_station) as arrival_station, coalesce(e.comparison_id,a.comparison_id) as comparison_id
from expected e full join actual a using(version_id, departure_station, arrival_station, service_type, comparison_id)
where e.version_id is null or a.version_id is null
or a.services_in_comparison != e.service_count
or a.is_comparison_eligible != (e.current_eligible=e.expected_months and e.previous_eligible=e.expected_months and e.service_count=1)
{% for side in ['current','previous'] %}
or a.{{ side }}_observed_months != e.{{ side }}_observed
or a.{{ side }}_eligible_months != e.{{ side }}_eligible
{% for kind, actual_num, actual_den, rate in [('arrival','arrival_numerator','arrival_denominator','arrival_delay_rate'),('cancellation','cancellation_numerator','cancellation_denominator','cancellation_rate'),('important','over_30_numerator','important_denominator','over_30_delay_rate')] %}
or a.{{ side }}_{{ kind }}_valid_months != e.{{ side }}_{{ kind }}_valid
or a.{{ side }}_{{ actual_num }} is distinct from e.{{ side }}_{{ kind }}_num
or a.{{ side }}_{{ actual_den }} is distinct from e.{{ side }}_{{ kind }}_den
or a.{{ side }}_{{ rate }} is distinct from
    if(e.{{ side }}_{{ kind }}_valid=e.expected_months, safe_divide(cast(e.{{ side }}_{{ kind }}_num as numeric),e.{{ side }}_{{ kind }}_den),null)
{% endfor %}
{% endfor %}
or (not a.is_comparison_eligible and (a.arrival_delay_change_pp is not null or a.change_signal!='ineligible'
    or a.is_deterioration_persistent is not null or a.is_underperformance_persistent is not null))
or ((not a.persistence_applicable) and (a.deterioration_persistence is not null or a.underperformance_persistence is not null
    or a.is_deterioration_persistent is not null or a.is_underperformance_persistent is not null))
or (a.is_comparison_eligible and array_length(a.exclusion_reasons)!=0)
or (not a.is_comparison_eligible and array_length(a.exclusion_reasons)=0)
or (a.is_comparison_eligible and a.eligible_month_pairs!=a.expected_months)
or (a.is_comparison_eligible and (a.arrival_delay_change_pp is null
    or abs(a.arrival_delay_change_pp - 100 *
        (safe_divide(cast(e.current_arrival_num as bignumeric),e.current_arrival_den)
        - safe_divide(cast(e.previous_arrival_num as bignumeric),e.previous_arrival_den))) > 0.000000001))
or (a.is_comparison_eligible and a.persistence_applicable and (
    a.deterioration_persistence is distinct from safe_divide(a.deterioration_months,a.expected_months)
    or a.underperformance_persistence is distinct from safe_divide(a.underperformance_months,a.expected_months)
    or a.is_deterioration_persistent is distinct from (a.deterioration_months >= {{ var('persistence_months') }})
    or a.is_underperformance_persistent is distinct from (a.underperformance_months >= {{ var('persistence_months') }})))
