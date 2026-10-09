-- Contrôle de couverture des fenêtres J01, sans taux ni classement (J05/J06).
with windows as (
    select '2026_h1_vs_2025_h1' as comparison, date '2026-01-01' as current_start,
        date '2026-06-01' as current_end, 6 as expected_months
    union all
    select '2025_vs_2024', date '2025-01-01', date '2025-12-01', 12
), candidates as (
    select distinct version_id, departure_station, arrival_station, service_type
    from {{ ref('int_tgv_quality_flags') }} where service_type = 'National'
), coverage as (
    select c.*, w.comparison, w.expected_months,
        count(distinct if(q.service_type = 'National'
            and q.month between w.current_start and w.current_end, q.month, null))
            as current_observed_months,
        count(distinct if(q.service_type = 'National'
            and q.month between date_sub(w.current_start, interval 1 year)
            and date_sub(w.current_end, interval 1 year), q.month, null)) as previous_observed_months,
        countif(q.service_type = 'National' and q.central_counts_compatible
            and q.operated_trains_proxy >= 30
            and q.month between w.current_start and w.current_end) as current_valid_months,
        countif(q.service_type = 'National' and q.central_counts_compatible
            and q.operated_trains_proxy >= 30
            and q.month between date_sub(w.current_start, interval 1 year)
            and date_sub(w.current_end, interval 1 year)) as previous_valid_months,
        count(distinct q.service_type) as services_in_comparison
    from candidates c cross join windows w
    left join {{ ref('int_tgv_quality_flags') }} q
        on q.departure_station = c.departure_station and q.arrival_station = c.arrival_station
        and q.version_id = c.version_id
        and (q.month between w.current_start and w.current_end
            or q.month between date_sub(w.current_start, interval 1 year)
                and date_sub(w.current_end, interval 1 year))
    group by 1,2,3,4,5,6
)
select *, current_valid_months = expected_months and previous_valid_months = expected_months
    and services_in_comparison = 1 as passes_j01_coverage_screen
from coverage
order by comparison, departure_station, arrival_station
