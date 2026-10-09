{{ config(tags=['j04']) }}
{{ config(severity='warn') }}
select * from {{ ref('int_tgv_quality_flags') }}
where cause_profile_status != 'available'
