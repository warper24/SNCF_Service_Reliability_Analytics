{{ config(tags=['j05']) }}
{% for model, keys in [
('fct_reliability_monthly', 'month, route_key, service_key'),
('fct_delay_causes_monthly', 'month, route_key, service_key, cause_key'),
('mart_route_trends', 'month, route_key, service_key'),
('mart_route_priorities', 'route_key, service_key, comparison_id')] %}
select '{{ model }}' as model_name, count(*) as duplicates
from {{ ref(model) }} group by {{ keys }} having count(*) != 1
{% if not loop.last %}union all{% endif %}
{% endfor %}
