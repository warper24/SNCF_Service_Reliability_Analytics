-- La jointure porte sur la date exacte, jamais sur une position de ligne (LAG 12).
with pairs as (
    select c.*, p.month as previous_month,
        p.arrival_delayed_trains as previous_arrival_delayed_trains,
        p.operated_trains_proxy as previous_operated_trains_proxy,
        p.arrival_delay_rate as previous_arrival_delay_rate,
        coalesce(c.is_arrival_delay_rate_usable and p.is_arrival_delay_rate_usable, false)
            as is_year_pair_usable,
        coalesce(c.central_counts_compatible and p.central_counts_compatible
            and c.operated_trains_proxy >= {{ var('minimum_monthly_operated_proxy') }}
            and p.operated_trains_proxy >= {{ var('minimum_monthly_operated_proxy') }}, false)
            as passes_pair_volume_screen
    from {{ ref('fct_reliability_monthly') }} c
    left join {{ ref('fct_reliability_monthly') }} p
        on c.route_key = p.route_key and c.service_key = p.service_key
        and c.version_id = p.version_id and p.month = date_sub(c.month, interval 1 year)
)
select *,
    case when is_year_pair_usable then
        {{ change_pp('arrival_delayed_trains', 'operated_trains_proxy', 'previous_arrival_delayed_trains', 'previous_operated_trains_proxy') }}
    end as arrival_delay_change_pp,
    case when passes_pair_volume_screen then
        {{ deterioration('arrival_delayed_trains', 'operated_trains_proxy', 'previous_arrival_delayed_trains', 'previous_operated_trains_proxy') }}
    end as is_monthly_deterioration,
    case when central_counts_compatible and operated_trains_proxy >= {{ var('minimum_monthly_operated_proxy') }}
        then 100 * cast(operated_trains_proxy - arrival_delayed_trains as numeric)
            < {{ var('regularity_target_pct') }} * cast(operated_trains_proxy as numeric)
    end as is_monthly_underperformance
from pairs
