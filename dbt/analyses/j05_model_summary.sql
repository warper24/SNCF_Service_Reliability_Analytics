{% for model in ['dim_date','dim_route','dim_service','dim_cause','fct_reliability_monthly','fct_delay_causes_monthly','mart_route_trends','mart_route_priorities'] %}
select '{{ model }}' as model_name, count(*) as row_count from {{ ref(model) }}
{% if not loop.last %}union all{% endif %}
{% endfor %}
