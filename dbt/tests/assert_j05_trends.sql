{{ config(tags=['j05']) }}
select coalesce(c.row_number, t.row_number) as row_number
from {{ ref('fct_reliability_monthly') }} c
left join {{ ref('fct_reliability_monthly') }} p on c.version_id=p.version_id
 and c.route_key=p.route_key and c.service_key=p.service_key and p.month=date_sub(c.month, interval 1 year)
full join {{ ref('mart_route_trends') }} t on t.version_id=c.version_id and t.row_number=c.row_number
where c.row_number is null or t.row_number is null
or t.previous_month is distinct from p.month
or t.previous_arrival_delayed_trains is distinct from p.arrival_delayed_trains
or t.previous_operated_trains_proxy is distinct from p.operated_trains_proxy
or t.previous_arrival_delay_rate is distinct from p.arrival_delay_rate
or t.is_year_pair_usable is distinct from coalesce(c.is_arrival_delay_rate_usable and p.is_arrival_delay_rate_usable, false)
or t.passes_pair_volume_screen is distinct from coalesce(c.central_counts_compatible and p.central_counts_compatible
 and c.operated_trains_proxy >= {{ var('minimum_monthly_operated_proxy') }}
 and p.operated_trains_proxy >= {{ var('minimum_monthly_operated_proxy') }}, false)
or (t.is_year_pair_usable and abs(t.arrival_delay_change_pp - 100*(safe_divide(cast(c.arrival_delayed_trains as bignumeric),c.operated_trains_proxy)
 - safe_divide(cast(p.arrival_delayed_trains as bignumeric),p.operated_trains_proxy))) > 0.000000001)
or (not t.is_year_pair_usable and t.arrival_delay_change_pp is not null)
or (t.is_year_pair_usable and t.arrival_delay_change_pp is null)
or t.is_monthly_deterioration is distinct from
    case when t.passes_pair_volume_screen then
        100 * (cast(c.arrival_delayed_trains as numeric)*p.operated_trains_proxy
        - cast(p.arrival_delayed_trains as numeric)*c.operated_trains_proxy)
        >= {{ var('deterioration_threshold_pp') }} * cast(c.operated_trains_proxy as numeric)*p.operated_trains_proxy end
or t.is_monthly_underperformance is distinct from
    case when c.central_counts_compatible and c.operated_trains_proxy >= {{ var('minimum_monthly_operated_proxy') }}
        then 100*cast(c.operated_trains_proxy-c.arrival_delayed_trains as numeric)
        < {{ var('regularity_target_pct') }} * cast(c.operated_trains_proxy as numeric) end
