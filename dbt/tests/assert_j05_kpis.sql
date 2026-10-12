{{ config(tags=['j05']) }}
-- Recalcul indépendant des macros de production et des booléens J04.
with populations as (
 select *, coalesce(scheduled_trains > 0 and cancelled_trains between 0 and scheduled_trains, false) as cancellation_ok,
 coalesce(scheduled_trains >= 0 and cancelled_trains between 0 and scheduled_trains
     and scheduled_trains - cancelled_trains > 0
     and arrival_delayed_trains between 0 and scheduled_trains - cancelled_trains, false) as arrival_ok
 from {{ ref('fct_reliability_monthly') }}
), expected as (
 select *,
 arrival_ok and coalesce(arrival_delayed_over_60_trains >= 0
     and arrival_delayed_over_30_trains >= arrival_delayed_over_60_trains
     and arrival_delayed_over_30_trains <= arrival_delayed_trains, false)
     and not (month between date '2025-01-01' and date '2025-03-01') as important_ok
 from populations
)
select version_id, row_number from expected
where cancellation_rate is distinct from if(cancellation_ok, safe_divide(cast(cancelled_trains as numeric), scheduled_trains), null)
or arrival_delay_rate is distinct from if(arrival_ok, safe_divide(cast(arrival_delayed_trains as numeric), scheduled_trains-cancelled_trains), null)
or composite_regularity_rate is distinct from if(arrival_ok, safe_divide(cast(scheduled_trains-cancelled_trains-arrival_delayed_trains as numeric), scheduled_trains-cancelled_trains), null)
or over_30_delay_rate is distinct from if(important_ok, safe_divide(cast(arrival_delayed_over_30_trains as numeric), scheduled_trains-cancelled_trains), null)
or over_60_delay_rate is distinct from if(important_ok, safe_divide(cast(arrival_delayed_over_60_trains as numeric), scheduled_trains-cancelled_trains), null)
or over_30_delay_count is distinct from if(is_important_delay_count_usable, arrival_delayed_over_30_trains, null)
or over_60_delay_count is distinct from if(is_important_delay_count_usable, arrival_delayed_over_60_trains, null)
or denominator_status != 'derived_population_not_certified_D01'
