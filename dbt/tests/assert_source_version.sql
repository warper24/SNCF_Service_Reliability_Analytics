{{ config(tags=['j04']) }}
select count(*) as observations, count(distinct version_id) as versions
from {{ ref('stg_tgv_reliability') }}
having observations = 0 or versions != 1
{% if var('expected_version_id', '') %}
    or countif(version_id != '{{ var("expected_version_id") }}') > 0
{% endif %}
