{{ config(tags=['j04']) }}
select coalesce(s.row_number, r.row_number) as row_number
from {{ ref('stg_tgv_reliability') }} s
full outer join {{ source('sncf_raw', 'tgv_reliability') }} r
    on s.row_number = r.row_number and s.version_id = r.version_id
where s.row_number is null or r.row_number is null
    or s.raw_payload is distinct from r.payload or s.row_sha256 is distinct from r.row_sha256
