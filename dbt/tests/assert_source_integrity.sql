{{ config(tags=['j04']) }}
select * from {{ ref('stg_tgv_reliability') }}
where invalid_json or array_length(conversion_error_fields) > 0
    or array_length(missing_schema_fields) > 0
    or row_number < 1 or not regexp_contains(row_sha256, r'^[a-f0-9]{64}$')
    or not regexp_contains(version_id, r'^[a-f0-9]{64}$')
