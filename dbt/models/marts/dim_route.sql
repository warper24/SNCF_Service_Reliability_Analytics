-- La direction et les libellés exacts déterminent la clé ; aucun rapprochement inventé.
select distinct
    {{ route_key('departure_station', 'arrival_station') }} as route_key,
    departure_station, arrival_station,
    concat(departure_station, ' → ', arrival_station) as route_label
from {{ ref('int_tgv_quality_flags') }}
