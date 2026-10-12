-- Huit cas source J04 ; calculs directs à partir des noms SNCF, indépendants des macros.
with selected as (
 select 'ordinary_usable' as label, date '2018-09-01' as month, 'PARIS EST' as departure_station, 'REIMS' as arrival_station
 union all select 'real_dijon', date '2025-01-01', 'DIJON VILLE', 'PARIS LYON'
 union all select 'zero_population', date '2020-08-01', 'MARSEILLE ST CHARLES', 'MADRID'
 union all select 'incompatible_counts', date '2020-04-01', 'PARIS LYON', 'AIX EN PROVENCE TGV'
 union all select 'negative_late_mean', date '2019-11-01', 'NIMES', 'PARIS LYON'
 union all select 'cause_sum_warning', date '2026-06-01', 'PARIS MONTPARNASSE', 'VANNES'
 union all select 'signed_mean', date '2018-04-01', 'PARIS VAUGIRARD', 'BORDEAUX ST JEAN'
 union all select 'zero_cause_profile', date '2018-05-01', 'BELLEGARDE (AIN)', 'PARIS LYON'
), raw_counts as (
 select version_id, row_number,
    cast(json_value(payload, '$.nb_train_prevu') as int64) as nb_train_prevu,
    cast(json_value(payload, '$.nb_annulation') as int64) as nb_annulation,
    cast(json_value(payload, '$.nb_train_retard_arrivee') as int64) as nb_train_retard_arrivee
 from {{ source('sncf_raw', 'tgv_reliability') }}
)
select s.label, f.version_id, f.row_number, f.month, f.departure_station, f.arrival_station, f.service_type,
    r.nb_train_prevu, r.nb_annulation, r.nb_train_retard_arrivee, f.operated_trains_proxy,
    f.cancellation_rate, f.arrival_delay_rate, f.composite_regularity_rate,
    case when r.nb_train_prevu > 0 and r.nb_annulation between 0 and r.nb_train_prevu
        then safe_divide(cast(r.nb_annulation as numeric), r.nb_train_prevu) end as source_cancellation_rate,
    case when r.nb_annulation between 0 and r.nb_train_prevu
        and r.nb_train_prevu > r.nb_annulation
        and r.nb_train_retard_arrivee between 0 and r.nb_train_prevu-r.nb_annulation
        then safe_divide(cast(r.nb_train_retard_arrivee as numeric), r.nb_train_prevu-r.nb_annulation) end as source_arrival_delay_rate,
    f.arrival_delayed_over_30_trains, f.arrival_delayed_over_60_trains, f.over_30_delay_count,
    f.over_30_delay_rate, f.over_60_delay_rate, f.cause_profile_status, f.quality_reasons
from selected s join {{ ref('fct_reliability_monthly') }} f using(month, departure_station, arrival_station)
join raw_counts r using (version_id, row_number) order by label
