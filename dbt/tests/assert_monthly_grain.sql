{{ config(tags=['j04']) }}
select month, departure_station, arrival_station, service_type, count(*) as observations
from {{ ref('stg_tgv_reliability') }}
group by 1,2,3,4
having observations != 1 or trim(departure_station) = ''
    or trim(arrival_station) = '' or trim(service_type) = ''
    or extract(day from month) != 1
