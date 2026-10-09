{{ config(tags=['j04']) }}
{{ config(severity='warn') }}
select * from {{ ref('int_tgv_quality_flags') }}
where has_multiple_services_in_month
