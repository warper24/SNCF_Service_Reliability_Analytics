{{ config(tags=['j05']) }}
{% for model in ['fct_reliability_monthly','fct_delay_causes_monthly','mart_route_trends','mart_route_priorities'] %}
select '{{ model }}' as model_name, count(*) as row_count from {{ ref(model) }}
having count(*) = 0 or count(distinct version_id) != 1
    or countif(version_id != '{{ var("expected_version_id") }}') > 0
{% if not loop.last %}union all{% endif %}
{% endfor %}
