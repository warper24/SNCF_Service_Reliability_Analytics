-- Cas indépendants construits avant lecture des résultats réels.
with cases as (
    select * from unnest([
        struct('up_exact' as name,100 as n,10 as l0,12 as l1),
        ('down_exact',100,12,10),('target_equal',100,10,10),
        ('persistent_3',100,5,15),('persistent_4',100,5,15),
        ('zero',0,0,0),('null_delay',100,10,cast(null as int64)),
        ('missing',100,10,20),('low15',15,1,3),('low30',30,3,6),('low60',60,6,12),
        ('scope',100,10,20),('weighted',100,10,20)
    ])
), source_values as (
    select 'fixture' as version_id,name as route_key,'National' as service_key,
        name as departure_station,'Destination' as arrival_station,'National' as service_type,m as month,
        case when name='weighted' and extract(month from m)=6 then 1000 else n end as n,
        case when extract(year from m)=2025 then l0
            when name='persistent_3' and extract(month from m)>3 then 5
            when name='persistent_4' and extract(month from m)>4 then 5
            when name='weighted' and extract(month from m)=6 then 500 else l1 end as l
    from cases cross join unnest(generate_date_array(date '2025-01-01',date '2026-06-01',interval 1 month)) m
    where extract(month from m)<=6 and not(name='missing' and m=date '2026-01-01')
    union all select 'fixture','scope','International','scope','Destination','International',date '2026-01-01',100,20
), fixture_source as (
    select * except(n,l),n as operated_trains_proxy,l as arrival_delayed_trains,n as scheduled_trains,0 as cancelled_trains,
        coalesce(l>=0 and l<=n,false) as central_counts_compatible,
        coalesce(n>0 and l>=0 and l<=n,false) as is_arrival_delay_rate_usable,
        n>0 as is_cancellation_rate_usable from source_values
), diagnostic as ({{ j06_diagnostic('fixture_source',true) }}),
base as (select * from diagnostic where is_reference and comparison_id='2026_h1_vs_2025_h1'),
expectations as (
    select * from unnest([
        struct('up_exact' as route_key,true as eligible,'deterioration' as signal,true as persistent,false as underperformance_unused),
        ('down_exact',true,'improvement',false,false),('target_equal',true,'below_project_threshold',false,false),
        ('persistent_3',true,'deterioration',false,false),('persistent_4',true,'deterioration',true,false),
        ('zero',false,'ineligible',cast(null as bool),false),('null_delay',false,'ineligible',null,false),
        ('missing',false,'ineligible',null,false),('low15',false,'ineligible',null,false),
        ('low30',true,'deterioration',true,false),('low60',true,'deterioration',true,false),
        ('scope',false,'ineligible',null,false),('weighted',true,'deterioration',true,false)
    ])
), tie_values as (
    select 'fixture' as version_id,'tie' as comparison_id,'base' as scenario_id,
        i as route_id,'deterioration' as change_signal,true as is_deterioration_persistent,
        true as is_underperformance_persistent,6 as underperformance_months,
        cast(if(i in (5,6),5,10-i) as numeric) as change_pp,
        cast(if(i in (5,6),5,10-i) as numeric)/100 as current_rate,100 as current_l
    from unnest([1,2,3,4,5,6,7]) i
), ties as ({{ j06_rank('tie_values') }}),
decomp_values as (
    select true as is_eligible,1000 as previous_n,100 as previous_l,1200 as current_n,156 as current_l
), decomposition as ({{ j06_decomposition('decomp_values') }})
select concat('case_',e.route_key) as check_name,
    if(b.route_key is null or b.is_eligible is distinct from e.eligible or b.change_signal is distinct from e.signal
        or b.is_deterioration_persistent is distinct from e.persistent,1,0) as failures
from expectations e left join base b using(route_key)
union all select 'exact_two_points',countif(change_pp is distinct from numeric '2') from base where route_key='up_exact'
union all select 'strict_target_90',countif(is_underperformance_persistent is distinct from false) from base where route_key='target_equal'
union all select 'underperformance_four_of_six',countif(is_underperformance_persistent is distinct from (route_key='persistent_4'))
    from base where route_key in ('persistent_3','persistent_4')
union all select 'weighted_ratio',countif(abs(current_rate-numeric '0.4')>numeric '0.000000001') from base where route_key='weighted'
union all select 'zero_not_zero_rate',countif(current_rate is not null) from base where route_key='zero'
union all select 'null_not_zero_rate',countif(current_rate is not null) from base where route_key='null_delay'
union all select 'missing_not_zero',countif(current_observed_months!=5 or current_rate is not null) from base where route_key='missing'
union all select 'volume_threshold_boundaries',countif(is_eligible is distinct from
    (minimum_volume<=cast(substr(route_key,4) as int64))) from diagnostic
    where starts_with(route_key,'low') and comparison_id='2026_h1_vs_2025_h1'
union all select 'annual_persistence_null',countif(is_deterioration_persistent is not null or is_underperformance_persistent is not null)
    from diagnostic where comparison_id='2025_vs_2024'
union all select 'tie_boundary_rank_five',countif(deterioration_rank!=5 or underperformance_rank!=5) from ties where route_id in (5,6)
union all select 'tie_rank_skip',countif(deterioration_rank!=7 or underperformance_rank!=7) from ties where route_id=7
union all select 'tie_six_rows_in_top_five',if(countif(deterioration_rank<=5)!=6,1,0) from ties
union all select 'decomposition_example',countif(delta_l!=56 or volume_effect!=20 or rate_effect!=36 or reconciliation_residual!=0) from decomposition
