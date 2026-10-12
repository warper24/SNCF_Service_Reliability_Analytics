{% macro route_key(departure, arrival) -%}
to_hex(sha256(to_json_string(struct({{ departure }} as departure_station, {{ arrival }} as arrival_station))))
{%- endmacro %}

{% macro service_key(service) -%}
to_hex(sha256({{ service }}))
{%- endmacro %}

{% macro reference_ratio(numerator, denominator, usable) -%}
case when {{ usable }} then safe_divide(cast({{ numerator }} as numeric), cast({{ denominator }} as numeric)) end
{%- endmacro %}

{% macro change_pp(current_l, current_n, previous_l, previous_n) -%}
safe_divide(100 * (cast({{ current_l }} as numeric) * {{ previous_n }}
    - cast({{ previous_l }} as numeric) * {{ current_n }}),
    cast({{ current_n }} as numeric) * {{ previous_n }})
{%- endmacro %}

{% macro deterioration(current_l, current_n, previous_l, previous_n, direction=1) -%}
{{ direction }} * 100 * (cast({{ current_l }} as numeric) * {{ previous_n }}
    - cast({{ previous_l }} as numeric) * {{ current_n }})
    >= {{ var('deterioration_threshold_pp') }} * cast({{ current_n }} as numeric) * {{ previous_n }}
{%- endmacro %}

{% macro comparison_windows() -%}
{% for w in var('comparison_windows') %}
select '{{ w.comparison_id }}' as comparison_id,
    date '{{ w.current_start }}' as current_start, date '{{ w.current_end }}' as current_end,
    {{ w.expected_months }} as expected_months,
    {{ 'true' if w.persistence_applicable else 'false' }} as persistence_applicable
{% if not loop.last %}union all{% endif %}
{% endfor %}
{%- endmacro %}
