-- Couverture seulement ; aucun classement ou export complet du mart.
select version_id, comparison_id, expected_months, count(*) as candidate_routes,
    countif(is_comparison_eligible) as eligible_routes,
    countif(current_observed_months != expected_months) as incomplete_current_routes,
    countif(previous_observed_months != expected_months) as incomplete_previous_routes,
    countif(services_in_comparison != 1) as service_scope_excluded_routes,
    countif(current_important_valid_months = expected_months) as complete_current_important_routes,
    countif(previous_important_valid_months = expected_months) as complete_previous_important_routes,
    countif(deterioration_persistence is not null) as available_deterioration_persistence_routes
from {{ ref('mart_route_priorities') }} group by 1,2,3 order by comparison_id
