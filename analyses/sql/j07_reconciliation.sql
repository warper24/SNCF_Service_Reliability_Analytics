-- Référence indépendante des mesures DAX, à paramètres nommés BigQuery.
-- Une sélection = une liaison orientée, un service et des mois complets.
WITH selected AS (
  SELECT * FROM `PROJECT_ID.sncf_dev.fct_reliability_monthly`
  WHERE route_key=@route_key AND service_key=@service_key
    AND month BETWEEN @start_month AND @end_month
), aggregated AS (
  SELECT COUNT(DISTINCT month) AS observed_months,
    DATE_DIFF(@end_month,@start_month,MONTH)+1 AS expected_months,
    COUNTIF(is_arrival_delay_rate_usable) AS arrival_valid_months,
    COUNTIF(is_cancellation_rate_usable) AS cancellation_valid_months,
    COUNTIF(is_important_delay_rate_usable) AS important_valid_months,
    SUM(IF(is_arrival_delay_rate_usable,arrival_delayed_trains,NULL)) AS l,
    SUM(IF(is_arrival_delay_rate_usable,operated_trains_proxy,NULL)) AS n,
    SUM(IF(is_cancellation_rate_usable,cancelled_trains,NULL)) AS a,
    SUM(IF(is_cancellation_rate_usable,scheduled_trains,NULL)) AS p,
    SUM(IF(is_important_delay_rate_usable,arrival_delayed_over_30_trains,NULL)) AS l30,
    SUM(IF(is_important_delay_rate_usable,arrival_delayed_over_60_trains,NULL)) AS l60,
    SUM(IF(is_important_delay_rate_usable,operated_trains_proxy,NULL)) AS ni,
    SUM(over_30_delay_count) AS over_30_delay_count,
    SUM(over_60_delay_count) AS over_60_delay_count
  FROM selected
)
SELECT observed_months,expected_months,arrival_valid_months,cancellation_valid_months,important_valid_months,
  SAFE_DIVIDE(observed_months,expected_months) AS observation_coverage,
  IF(arrival_valid_months=expected_months,SAFE_DIVIDE(l,n),NULL) AS arrival_delay_rate,
  IF(arrival_valid_months=expected_months,SAFE_DIVIDE(n-l,n),NULL) AS composite_regularity_rate,
  IF(cancellation_valid_months=expected_months,SAFE_DIVIDE(a,p),NULL) AS cancellation_rate,
  IF(important_valid_months=expected_months,SAFE_DIVIDE(l30,ni),NULL) AS over_30_delay_rate,
  IF(important_valid_months=expected_months,SAFE_DIVIDE(l60,ni),NULL) AS over_60_delay_rate,
  over_30_delay_count,over_60_delay_count
FROM aggregated
