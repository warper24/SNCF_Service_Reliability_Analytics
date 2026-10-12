select distinct {{ service_key('service_type') }} as service_key, service_type
from {{ ref('int_tgv_quality_flags') }}
