-- Calendrier quotidien continu ; seuls les premiers jours représentent les faits mensuels.
with windows as ({{ comparison_windows() }}), bounds as (
    select least((select min(month) from {{ ref('int_tgv_quality_flags') }}),
        (select date_sub(min(current_start), interval 1 year) from windows)) as first_date,
        greatest((select max(month) from {{ ref('int_tgv_quality_flags') }}),
        (select max(current_end) from windows)) as last_date
)
select date_day as date_key, date_trunc(date_day, month) as month,
    extract(year from date_day) as year, extract(quarter from date_day) as quarter,
    extract(month from date_day) as month_number, format_date('%Y-%m', date_day) as month_label,
    date_day = date_trunc(date_day, month) as is_month_start
from bounds, unnest(generate_date_array(date_trunc(first_date, year), last_day(last_date, year))) as date_day
