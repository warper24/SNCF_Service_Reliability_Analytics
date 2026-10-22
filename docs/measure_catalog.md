# Catalogue des mesures J07 et présentation J08

Les 57 mesures J07 et 17 mesures de présentation J08 (74 au total) sont définies dans `powerbi/SNCF_Reliability.SemanticModel/definition/tables/kpi_measures.tmdl`. Ce catalogue décrit leur intention ; la preuve de qualification est dans le rapport SQL/Power BI. Les noms techniques restent en anglais, les descriptions en français.

BLANK signifie indisponible. Les gardes masquées protègent les mesures visibles. Les taux sont stockés en proportion 0–1 et affichés en pourcentage ; les écarts sont en points. Aucune agrégation interliaisons/services de trains ni moyenne des causes.

## `single_route_service`

Contexte restreint à une liaison orientée et un service.

**Dossier :** Contrôles. **Masquée :** oui. **Format :** `texte / booléen`.

```dax
HASONEVALUE(dim_route[route_key]) && HASONEVALUE(dim_service[service_key])
```

## `complete_month_selection`

Refuse les jours partiels ; les sélections doivent contenir tous les jours de chaque mois.

**Dossier :** Contrôles. **Masquée :** oui. **Format :** `texte / booléen`.

```dax
COUNTROWS(dim_date) > 0 && COUNTROWS(dim_date) = SUMX(VALUES(dim_date[month]), DAY(EOMONTH(dim_date[month], 0)))
```

## `monthly_context_allowed`

Protège les faits mensuels des agrégations interliaisons/services et de la lecture par cause.

**Dossier :** Contrôles. **Masquée :** oui. **Format :** `texte / booléen`.

```dax
[single_route_service] && [complete_month_selection] && NOT ISFILTERED(dim_cause)
```

## `expected_months`

Nombre de mois sélectionnés dans le calendrier, même absents des faits.

**Dossier :** Couverture. **Masquée :** non. **Format :** `0`.

```dax
IF([monthly_context_allowed], COUNTROWS(VALUES(dim_date[month])))
```

## `observed_months`

Mois réellement présents ; zéro signifie ici aucune observation.

**Dossier :** Couverture. **Masquée :** non. **Format :** `0`.

```dax
IF([monthly_context_allowed], COALESCE(DISTINCTCOUNT(fct_reliability_monthly[month]), 0))
```

## `observation_coverage`

Couverture de présence, distincte de la validité propre à chaque indicateur.

**Dossier :** Couverture. **Masquée :** non. **Format :** `0.0%`.

```dax
DIVIDE([observed_months], [expected_months])
```

## `arrival_valid_months`

Mois utilisables selon le masque dbt is_arrival_delay_rate_usable.

**Dossier :** Couverture. **Masquée :** non. **Format :** `0`.

```dax
IF([monthly_context_allowed], COALESCE(CALCULATE(DISTINCTCOUNT(fct_reliability_monthly[month]), KEEPFILTERS(fct_reliability_monthly[is_arrival_delay_rate_usable] = TRUE())), 0))
```

## `arrival_coverage`

Couverture valide de l’indicateur, sans suppression des mois attendus.

**Dossier :** Couverture. **Masquée :** non. **Format :** `0.0%`.

```dax
DIVIDE([arrival_valid_months], [expected_months])
```

## `cancellation_valid_months`

Mois utilisables selon le masque dbt is_cancellation_rate_usable.

**Dossier :** Couverture. **Masquée :** non. **Format :** `0`.

```dax
IF([monthly_context_allowed], COALESCE(CALCULATE(DISTINCTCOUNT(fct_reliability_monthly[month]), KEEPFILTERS(fct_reliability_monthly[is_cancellation_rate_usable] = TRUE())), 0))
```

## `cancellation_coverage`

Couverture valide de l’indicateur, sans suppression des mois attendus.

**Dossier :** Couverture. **Masquée :** non. **Format :** `0.0%`.

```dax
DIVIDE([cancellation_valid_months], [expected_months])
```

## `important_valid_months`

Mois utilisables selon le masque dbt is_important_delay_rate_usable.

**Dossier :** Couverture. **Masquée :** non. **Format :** `0`.

```dax
IF([monthly_context_allowed], COALESCE(CALCULATE(DISTINCTCOUNT(fct_reliability_monthly[month]), KEEPFILTERS(fct_reliability_monthly[is_important_delay_rate_usable] = TRUE())), 0))
```

## `important_coverage`

Couverture valide de l’indicateur, sans suppression des mois attendus.

**Dossier :** Couverture. **Masquée :** non. **Format :** `0.0%`.

```dax
DIVIDE([important_valid_months], [expected_months])
```

## `important_count_valid_months`

Mois utilisables selon le masque dbt is_important_delay_count_usable.

**Dossier :** Couverture. **Masquée :** non. **Format :** `0`.

```dax
IF([monthly_context_allowed], COALESCE(CALCULATE(DISTINCTCOUNT(fct_reliability_monthly[month]), KEEPFILTERS(fct_reliability_monthly[is_important_delay_count_usable] = TRUE())), 0))
```

## `important_count_coverage`

Couverture valide de l’indicateur, sans suppression des mois attendus.

**Dossier :** Couverture. **Masquée :** non. **Format :** `0.0%`.

```dax
DIVIDE([important_count_valid_months], [expected_months])
```

## `arrival_delay_count`

Somme temporelle sur une liaison/service ; indisponible si couverture incomplète. N=P−A non certifié (D01).

**Dossier :** Effectifs. **Masquée :** non. **Format :** `#,0`.

```dax
IF([monthly_context_allowed] && [arrival_valid_months] = [expected_months], CALCULATE(SUM(fct_reliability_monthly[arrival_delayed_trains]), KEEPFILTERS(fct_reliability_monthly[is_arrival_delay_rate_usable] = TRUE())))
```

## `operated_proxy_count`

Somme temporelle sur une liaison/service ; indisponible si couverture incomplète. N=P−A non certifié (D01).

**Dossier :** Effectifs. **Masquée :** non. **Format :** `#,0`.

```dax
IF([monthly_context_allowed] && [arrival_valid_months] = [expected_months], CALCULATE(SUM(fct_reliability_monthly[operated_trains_proxy]), KEEPFILTERS(fct_reliability_monthly[is_arrival_delay_rate_usable] = TRUE())))
```

## `cancelled_count`

Somme temporelle sur une liaison/service ; indisponible si couverture incomplète. N=P−A non certifié (D01).

**Dossier :** Effectifs. **Masquée :** non. **Format :** `#,0`.

```dax
IF([monthly_context_allowed] && [cancellation_valid_months] = [expected_months], CALCULATE(SUM(fct_reliability_monthly[cancelled_trains]), KEEPFILTERS(fct_reliability_monthly[is_cancellation_rate_usable] = TRUE())))
```

## `scheduled_count`

Somme temporelle sur une liaison/service ; indisponible si couverture incomplète. N=P−A non certifié (D01).

**Dossier :** Effectifs. **Masquée :** non. **Format :** `#,0`.

```dax
IF([monthly_context_allowed] && [cancellation_valid_months] = [expected_months], CALCULATE(SUM(fct_reliability_monthly[scheduled_trains]), KEEPFILTERS(fct_reliability_monthly[is_cancellation_rate_usable] = TRUE())))
```

## `arrival_delay_rate`

Σ retards composites publiés / Σ circulations déduites ; D01, population non certifiée.

**Dossier :** Fiabilité. **Masquée :** non. **Format :** `0.00%`.

```dax
DIVIDE([arrival_delay_count], [operated_proxy_count])
```

## `cancellation_rate`

Σ annulations publiées / Σ prévus ; convention historique des annulations non certifiée.

**Dossier :** Fiabilité. **Masquée :** non. **Format :** `0.00%`.

```dax
DIVIDE([cancelled_count], [scheduled_count])
```

## `composite_regularity_rate`

Complément du taux composite ; ne mesure ni les annulations ni une arrivée sans aucune minute de retard.

**Dossier :** Fiabilité. **Masquée :** non. **Format :** `0.00%`.

```dax
VAR Rate = [arrival_delay_rate] RETURN IF(NOT ISBLANK(Rate), 1 - Rate)
```

## `over_30_delay_count`

Somme disponible des mois valides, à lire avec important_count_coverage. Seuils imbriqués non additifs.

**Dossier :** Retards importants. **Masquée :** non. **Format :** `#,0`.

```dax
IF([monthly_context_allowed], CALCULATE(SUM(fct_reliability_monthly[over_30_delay_count]), KEEPFILTERS(fct_reliability_monthly[is_important_delay_count_usable] = TRUE())))
```

## `over_30_delay_rate`

Ratio des sommes ; indisponible si un mois invalide, notamment T1 2025. D01.

**Dossier :** Retards importants. **Masquée :** non. **Format :** `0.00%`.

```dax
IF([monthly_context_allowed] && [important_valid_months] = [expected_months], DIVIDE(CALCULATE(SUM(fct_reliability_monthly[arrival_delayed_over_30_trains]), KEEPFILTERS(fct_reliability_monthly[is_important_delay_rate_usable] = TRUE())), CALCULATE(SUM(fct_reliability_monthly[operated_trains_proxy]), KEEPFILTERS(fct_reliability_monthly[is_important_delay_rate_usable] = TRUE()))))
```

## `over_60_delay_count`

Somme disponible des mois valides, à lire avec important_count_coverage. Seuils imbriqués non additifs.

**Dossier :** Retards importants. **Masquée :** non. **Format :** `#,0`.

```dax
IF([monthly_context_allowed], CALCULATE(SUM(fct_reliability_monthly[over_60_delay_count]), KEEPFILTERS(fct_reliability_monthly[is_important_delay_count_usable] = TRUE())))
```

## `over_60_delay_rate`

Ratio des sommes ; indisponible si un mois invalide, notamment T1 2025. D01.

**Dossier :** Retards importants. **Masquée :** non. **Format :** `0.00%`.

```dax
IF([monthly_context_allowed] && [important_valid_months] = [expected_months], DIVIDE(CALCULATE(SUM(fct_reliability_monthly[arrival_delayed_over_60_trains]), KEEPFILTERS(fct_reliability_monthly[is_important_delay_rate_usable] = TRUE())), CALCULATE(SUM(fct_reliability_monthly[operated_trains_proxy]), KEEPFILTERS(fct_reliability_monthly[is_important_delay_rate_usable] = TRUE()))))
```

## `low_volume_months`

Mois compatibles sous le minimum de classement de 30 ; consultation descriptive permise.

**Dossier :** Couverture. **Masquée :** non. **Format :** `0`.

```dax
IF([monthly_context_allowed], COALESCE(CALCULATE(COUNTROWS(fct_reliability_monthly), KEEPFILTERS(fct_reliability_monthly[central_counts_compatible] = TRUE()), KEEPFILTERS(fct_reliability_monthly[operated_trains_proxy] < 30)), 0))
```

## `monthly_status`

Explique l’indisponibilité ou la réserve métier ; distinct d’un zéro.

**Dossier :** Qualité. **Masquée :** non. **Format :** `texte / booléen`.

```dax
SWITCH(TRUE(), NOT [single_route_service], "Sélectionner une liaison et un service", NOT [complete_month_selection], "Sélectionner des mois complets", ISFILTERED(dim_cause), "Taux par cause non défini", [observed_months] < [expected_months], "Mois absents", [arrival_valid_months] < [expected_months], "Taux indisponible : population nulle ou effectifs invalides", [low_volume_months] > 0, "Descriptif disponible ; faible volume", "Disponible — population déduite non certifiée D01")
```

## `comparison_context_allowed`

Fenêtres fixées par le contrat ; tout filtre direct du calendrier ou des causes invalide leur lecture.

**Dossier :** Contrôles. **Masquée :** oui. **Format :** `texte / booléen`.

```dax
HASONEVALUE(dim_comparison[comparison_id]) && NOT ISFILTERED(dim_date) && NOT ISFILTERED(dim_cause)
```

## `candidate_route_count`

Nombre de liaisons/service pour une comparaison unique ; jamais un nombre de trains. Persistance annuelle non définie.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0`.

```dax
IF([comparison_context_allowed], COALESCE(CALCULATE(COUNTROWS(mart_route_priorities)), 0))
```

## `eligible_route_count`

Nombre de liaisons/service pour une comparaison unique ; jamais un nombre de trains. Persistance annuelle non définie.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0`.

```dax
IF([comparison_context_allowed], COALESCE(CALCULATE(COUNTROWS(mart_route_priorities), KEEPFILTERS(mart_route_priorities[is_comparison_eligible] = TRUE())), 0))
```

## `deteriorating_route_count`

Nombre de liaisons/service pour une comparaison unique ; jamais un nombre de trains. Persistance annuelle non définie.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0`.

```dax
IF([comparison_context_allowed], COALESCE(CALCULATE(COUNTROWS(mart_route_priorities), KEEPFILTERS(mart_route_priorities[change_signal] = "deterioration")), 0))
```

## `improving_route_count`

Nombre de liaisons/service pour une comparaison unique ; jamais un nombre de trains. Persistance annuelle non définie.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0`.

```dax
IF([comparison_context_allowed], COALESCE(CALCULATE(COUNTROWS(mart_route_priorities), KEEPFILTERS(mart_route_priorities[change_signal] = "improvement")), 0))
```

## `persistent_underperformance_route_count`

Nombre de liaisons/service pour une comparaison unique ; jamais un nombre de trains. Persistance annuelle non définie.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0`.

```dax
IF([comparison_context_allowed] && SELECTEDVALUE(dim_comparison[persistence_applicable], FALSE()), COALESCE(CALCULATE(COUNTROWS(mart_route_priorities), KEEPFILTERS(mart_route_priorities[is_underperformance_persistent] = TRUE())), 0))
```

## `persistent_deterioration_route_count`

Nombre de liaisons/service pour une comparaison unique ; jamais un nombre de trains. Persistance annuelle non définie.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0`.

```dax
IF([comparison_context_allowed] && SELECTEDVALUE(dim_comparison[persistence_applicable], FALSE()), COALESCE(CALCULATE(COUNTROWS(mart_route_priorities), KEEPFILTERS(mart_route_priorities[is_deterioration_persistent] = TRUE())), 0))
```

## `current_arrival_delay_rate`

Valeur SQL de la fenêtre fixe current ; couverture propre à l’indicateur.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0.00%`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(mart_route_priorities[current_arrival_delay_rate]))
```

## `current_cancellation_rate`

Valeur SQL de la fenêtre fixe current ; couverture propre à l’indicateur.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0.00%`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(mart_route_priorities[current_cancellation_rate]))
```

## `current_composite_regularity_rate`

Valeur SQL de la fenêtre fixe current ; couverture propre à l’indicateur.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0.00%`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(mart_route_priorities[current_composite_regularity_rate]))
```

## `current_over_30_delay_rate`

Valeur SQL de la fenêtre fixe current ; couverture propre à l’indicateur.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0.00%`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(mart_route_priorities[current_over_30_delay_rate]))
```

## `current_over_60_delay_rate`

Valeur SQL de la fenêtre fixe current ; couverture propre à l’indicateur.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0.00%`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(mart_route_priorities[current_over_60_delay_rate]))
```

## `previous_arrival_delay_rate`

Valeur SQL de la fenêtre fixe previous ; couverture propre à l’indicateur.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0.00%`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(mart_route_priorities[previous_arrival_delay_rate]))
```

## `previous_cancellation_rate`

Valeur SQL de la fenêtre fixe previous ; couverture propre à l’indicateur.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0.00%`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(mart_route_priorities[previous_cancellation_rate]))
```

## `previous_composite_regularity_rate`

Valeur SQL de la fenêtre fixe previous ; couverture propre à l’indicateur.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0.00%`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(mart_route_priorities[previous_composite_regularity_rate]))
```

## `previous_over_30_delay_rate`

Valeur SQL de la fenêtre fixe previous ; couverture propre à l’indicateur.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0.00%`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(mart_route_priorities[previous_over_30_delay_rate]))
```

## `previous_over_60_delay_rate`

Valeur SQL de la fenêtre fixe previous ; couverture propre à l’indicateur.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0.00%`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(mart_route_priorities[previous_over_60_delay_rate]))
```

## `arrival_delay_change_pp`

Écart DAX en points entre les ratios de fenêtres ; éligibilité SQL obligatoire.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0.00 "points"`.

```dax
IF([comparison_context_allowed] && [single_route_service] && SELECTEDVALUE(mart_route_priorities[is_comparison_eligible], FALSE()), 100 * ([current_arrival_delay_rate] - [previous_arrival_delay_rate]))
```

## `deterioration_persistence`

Part de mois selon la règle 4/6 ; valeur SQL, annuelle indisponible.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0.0%`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(mart_route_priorities[deterioration_persistence]))
```

## `underperformance_persistence`

Part de mois selon la règle 4/6 ; valeur SQL, annuelle indisponible.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `0.0%`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(mart_route_priorities[underperformance_persistence]))
```

## `change_signal`

Signal SQL comparé avant arrondi ; ±2 points, seuil du portfolio.

**Dossier :** Comparaisons. **Masquée :** non. **Format :** `texte / booléen`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(mart_route_priorities[change_signal]))
```

## `comparison_status`

Rappelle que les fenêtres et critères ne suivent pas le calendrier libre.

**Dossier :** Qualité. **Masquée :** non. **Format :** `texte / booléen`.

```dax
IF(NOT [comparison_context_allowed], "Choisir une comparaison fixe sans filtre de calendrier ni de cause", "Fenêtres fixes ; minimum 30/mois, seuil 2 points, cible fictive 90 %")
```

## `deterioration_rank`

Rang J06 sur la population initiale ; filtrer une liaison ne reclasse pas les autres. Ex æquo conservés.

**Dossier :** Priorités. **Masquée :** non. **Format :** `0`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(route_diagnostic[deterioration_rank]))
```

## `underperformance_rank`

Rang J06 sur la population initiale ; filtrer une liaison ne reclasse pas les autres. Ex æquo conservés.

**Dossier :** Priorités. **Masquée :** non. **Format :** `0`.

```dax
IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(route_diagnostic[underperformance_rank]))
```

## `published_cause_share`

Part source convertie de 0–100 à 0–1 pour affichage ; aucun effectif déduit, aucune agrégation.

**Dossier :** Causes. **Masquée :** non. **Format :** `0.00%`.

```dax
IF([single_route_service] && [complete_month_selection] && HASONEVALUE(dim_date[month]) && HASONEVALUE(dim_cause[cause_key]) && SELECTEDVALUE(fct_delay_causes_monthly[is_cause_profile_usable], FALSE()), DIVIDE(SELECTEDVALUE(fct_delay_causes_monthly[published_cause_pct]), 100))
```

## `published_cause_raw_pct`

Valeur source 0–100, y compris profil non exploitable ; à lire avec le statut.

**Dossier :** Causes. **Masquée :** non. **Format :** `0.00`.

```dax
IF([single_route_service] && [complete_month_selection] && HASONEVALUE(dim_date[month]) && HASONEVALUE(dim_cause[cause_key]), SELECTEDVALUE(fct_delay_causes_monthly[published_cause_pct]))
```

## `cause_profile_status`

Statut SQL du profil ; les anomalies restent consultables.

**Dossier :** Causes. **Masquée :** non. **Format :** `texte / booléen`.

```dax
IF([single_route_service] && [complete_month_selection] && HASONEVALUE(dim_date[month]) && HASONEVALUE(dim_cause[cause_key]), SELECTEDVALUE(fct_delay_causes_monthly[cause_profile_status]), "Choisir une liaison, un service, un mois et une cause")
```

## `source_version`

Provenance de la copie importée ; indépendante des sélections métier.

**Dossier :** Provenance. **Masquée :** non. **Format :** `texte / booléen`.

```dax
SELECTEDVALUE(refresh_metadata[version_id])
```

## `last_business_month`

Provenance de la copie importée ; indépendante des sélections métier.

**Dossier :** Provenance. **Masquée :** non. **Format :** `yyyy-MM`.

```dax
SELECTEDVALUE(refresh_metadata[last_business_month])
```

## `last_import_utc`

Provenance de la copie importée ; indépendante des sélections métier.

**Dossier :** Provenance. **Masquée :** non. **Format :** `yyyy-MM-dd HH:mm:ss`.

```dax
SELECTEDVALUE(refresh_metadata[imported_at_utc])
```

## Compléments de présentation J08

Les 57 expressions J07 restent identiques au commit `10b1808`. Les compléments
ci-dessous exposent les résultats qualifiés et leur contexte ; aucun nouveau
score, population ou classement n’est créé. Dossier : `Rapport J08`.

### `dashboard_comparison_label`

Fenêtre fixe et populations de référence.

Format : `texte`.

```dax
SWITCH(SELECTEDVALUE(dim_comparison[comparison_id]), "2026_h1_vs_2025_h1", "Janvier–juin 2026 / janvier–juin 2025", "2025_vs_2024", "Année 2025 / année 2024", "Choisir une comparaison unique")
```

### `dashboard_coverage_label`

Couverture des candidats ; ne compte pas des trains.

Format : `texte`.

```dax
IF([comparison_context_allowed], FORMAT([eligible_route_count], "0") & " / " & FORMAT([candidate_route_count], "0") & " liaisons/service éligibles")
```

### `dashboard_excluded_count`

Candidats non éligibles ; motifs susceptibles de se recouvrir.

Format : `0`.

```dax
IF([comparison_context_allowed], [candidate_route_count] - [eligible_route_count])
```

### `dashboard_below_threshold_count`

Variation sous le seuil du projet ; aucune stabilité statistique affirmée.

Format : `0`.

```dax
IF([comparison_context_allowed], CALCULATE(COUNTROWS(mart_route_priorities), KEEPFILTERS(mart_route_priorities[change_signal] = "below_project_threshold")))
```

### `dashboard_current_l`

Retards publiés, fenêtre fixe et liaison/service uniques, couverture valide complète.

Format : `#,0`.

```dax
IF([comparison_context_allowed] && [single_route_service] && SELECTEDVALUE(mart_route_priorities[current_arrival_valid_months]) = SELECTEDVALUE(dim_comparison[expected_months]), SELECTEDVALUE(mart_route_priorities[current_arrival_numerator]))
```

### `dashboard_current_n`

Circulations déduites non certifiées D01 ; même garde que le taux courant.

Format : `#,0`.

```dax
IF([comparison_context_allowed] && [single_route_service] && SELECTEDVALUE(mart_route_priorities[current_arrival_valid_months]) = SELECTEDVALUE(dim_comparison[expected_months]), SELECTEDVALUE(mart_route_priorities[current_arrival_denominator]))
```

### `dashboard_deterioration_months`

Nombre de mois en hausse selon la règle SQL ; annuel indisponible.

Format : `0`.

```dax
IF([comparison_context_allowed] && [single_route_service] && SELECTEDVALUE(dim_comparison[persistence_applicable], FALSE()) && SELECTEDVALUE(mart_route_priorities[is_comparison_eligible], FALSE()), SELECTEDVALUE(mart_route_priorities[deterioration_months]))
```

### `dashboard_underperformance_months`

Nombre de mois sous cible fictive ; annuel indisponible.

Format : `0`.

```dax
IF([comparison_context_allowed] && [single_route_service] && SELECTEDVALUE(dim_comparison[persistence_applicable], FALSE()) && SELECTEDVALUE(mart_route_priorities[is_comparison_eligible], FALSE()), SELECTEDVALUE(mart_route_priorities[underperformance_months]))
```

### `dashboard_exclusion_reason`

Motifs SQL de non-éligibilité, sans suppression des candidats.

Format : `texte`.

```dax
IF([comparison_context_allowed] && [single_route_service], IF(SELECTEDVALUE(mart_route_priorities[is_comparison_eligible], FALSE()), "Éligible : couverture complète et N ≥30 chaque mois", COALESCE(SELECTEDVALUE(mart_route_priorities[exclusion_reasons]), "Hors population du classement")))
```

### `dashboard_route_label`

Contexte de la fiche : sens et service explicites.

Format : `texte`.

```dax
IF([single_route_service], SELECTEDVALUE(dim_route[route_label]) & " · " & SELECTEDVALUE(dim_service[service_type]) & " | " & [dashboard_comparison_label], "Sélectionner une liaison orientée et un service")
```

### `dashboard_freshness`

Provenance importée ; heure du SELECT de métadonnées, sans garantie transactionnelle.

Format : `texte`.

```dax
"Source jusqu'à " & FORMAT([last_business_month], "yyyy-MM") & " | Métadonnées lues : " & FORMAT([last_import_utc], "yyyy-MM-dd HH:mm") & " UTC | Version " & LEFT([source_version], 12)
```

### `dashboard_cause_status`

Statut du profil mensuel, indépendant de la catégorie de cause.

Format : `texte`.

```dax
IF([single_route_service] && [complete_month_selection] && HASONEVALUE(dim_date[month]), "Profil " & SELECTEDVALUE(dim_date[month_label]) & " : " & SWITCH(SELECTEDVALUE(fct_delay_causes_monthly[cause_profile_status]), "available", "disponible", "missing", "incomplet", "out_of_bounds", "valeurs hors bornes", "all_zero", "entièrement nul, non exploitable", "sum_warning", "somme hors tolérance, à examiner", "absent"), "Choisir une liaison, un service et un mois")
```

### `dashboard_investigation`

Piste éditoriale R01–R06 ; bornée à la version et au semestre documentés, sans calcul causal.

Format : `texte`.

```dax
VAR Route = SELECTEDVALUE(dim_route[route_label])
VAR Allowed = [single_route_service] && SELECTEDVALUE(dim_service[service_type]) = "National" && SELECTEDVALUE(dim_comparison[comparison_id]) = "2026_h1_vs_2025_h1" && [source_version] = "e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6"
RETURN IF(NOT Allowed, "Aucune investigation spécifique documentée pour ce contexte.", SWITCH(TRUE(),
Route = "PARIS LYON → GRENOBLE", "R01 · Demander les événements datés et rapprocher exploitation, gares, matériel et infrastructure. Hypothèse : plusieurs mécanismes possibles. Suivi : L/N, A/P et mois en hausse ; aucune causalité établie.",
Route = "PARIS MONTPARNASSE → NANTES", "R02 · Examiner préparation et rotations sur des dates documentées. Hypothèse : contraintes répétées possibles, à confronter aux incidents. Suivi : taux, annulations et persistance ; causes mensuelles sans moyenne.",
CONTAINSSTRING(Route, "DOUAI") && CONTAINSSTRING(Route, "PARIS NORD"), "R03 · Examiner chaque sens séparément puis rapprocher dates et périmètres. Hypothèse commune à vérifier. Suivi : deux séries L/N et A/P, avec leurs volumes et couvertures.",
CONTAINSSTRING(Route, "STRASBOURG") && CONTAINSSTRING(Route, "NANTES"), "R04 · Vérifier les six paires mensuelles, les volumes et les incidents. Signal sensible au seuil N≥60. Suivi : taux, couverture et éligibilité ; sortie du classement ≠ amélioration.",
NOT ISBLANK([underperformance_rank]) && [underperformance_rank] <= 5, "R05 · Constituer une fiche d'événements pour cette liaison durablement sous cible. Hypothèse : difficultés récurrentes à documenter. Suivi : régularité mensuelle, mois sous cible, L et N.",
NOT SELECTEDVALUE(mart_route_priorities[is_comparison_eligible], FALSE()), "R06 · Examiner absences, faibles volumes et changements de périmètre avant réintégration. Suivi : couverture valide et motifs d'exclusion.",
"Pas de recommandation spécifique J06 : examiner couverture, évolution et événements datés avant de formuler une hypothèse."))
```

### `dashboard_delay_current_month`

Taux mensuel J07 aligné sur la fenêtre fixe ; mois complets et gardes conservés.

Format : `0.0%`.

```dax
VAR MonthNumber = SELECTEDVALUE(dim_date[month_number])
VAR StartDate = SELECTEDVALUE(dim_comparison[current_start])
VAR EndDate = SELECTEDVALUE(dim_comparison[current_end])
VAR Allowed = [single_route_service] && HASONEVALUE(dim_comparison[comparison_id]) && NOT ISBLANK(MonthNumber) && NOT ISBLANK(StartDate) && MonthNumber >= MONTH(StartDate) && MonthNumber <= MONTH(EndDate)
VAR TargetDate = DATE(YEAR(StartDate), COALESCE(MonthNumber, 1), 1)
RETURN IF(Allowed, CALCULATE([arrival_delay_rate], REMOVEFILTERS(dim_date), DATESBETWEEN(dim_date[date_key], TargetDate, EOMONTH(TargetDate, 0))))
```

### `dashboard_delay_previous_month`

Taux mensuel J07 aligné sur la fenêtre fixe ; mois complets et gardes conservés.

Format : `0.0%`.

```dax
VAR MonthNumber = SELECTEDVALUE(dim_date[month_number])
VAR StartDate = SELECTEDVALUE(dim_comparison[previous_start])
VAR EndDate = SELECTEDVALUE(dim_comparison[previous_end])
VAR Allowed = [single_route_service] && HASONEVALUE(dim_comparison[comparison_id]) && NOT ISBLANK(MonthNumber) && NOT ISBLANK(StartDate) && MonthNumber >= MONTH(StartDate) && MonthNumber <= MONTH(EndDate)
VAR TargetDate = DATE(YEAR(StartDate), COALESCE(MonthNumber, 1), 1)
RETURN IF(Allowed, CALCULATE([arrival_delay_rate], REMOVEFILTERS(dim_date), DATESBETWEEN(dim_date[date_key], TargetDate, EOMONTH(TargetDate, 0))))
```

### `dashboard_cancellation_current_month`

Taux mensuel J07 aligné sur la fenêtre fixe ; mois complets et gardes conservés.

Format : `0.0%`.

```dax
VAR MonthNumber = SELECTEDVALUE(dim_date[month_number])
VAR StartDate = SELECTEDVALUE(dim_comparison[current_start])
VAR EndDate = SELECTEDVALUE(dim_comparison[current_end])
VAR Allowed = [single_route_service] && HASONEVALUE(dim_comparison[comparison_id]) && NOT ISBLANK(MonthNumber) && NOT ISBLANK(StartDate) && MonthNumber >= MONTH(StartDate) && MonthNumber <= MONTH(EndDate)
VAR TargetDate = DATE(YEAR(StartDate), COALESCE(MonthNumber, 1), 1)
RETURN IF(Allowed, CALCULATE([cancellation_rate], REMOVEFILTERS(dim_date), DATESBETWEEN(dim_date[date_key], TargetDate, EOMONTH(TargetDate, 0))))
```

### `dashboard_cancellation_previous_month`

Taux mensuel J07 aligné sur la fenêtre fixe ; mois complets et gardes conservés.

Format : `0.0%`.

```dax
VAR MonthNumber = SELECTEDVALUE(dim_date[month_number])
VAR StartDate = SELECTEDVALUE(dim_comparison[previous_start])
VAR EndDate = SELECTEDVALUE(dim_comparison[previous_end])
VAR Allowed = [single_route_service] && HASONEVALUE(dim_comparison[comparison_id]) && NOT ISBLANK(MonthNumber) && NOT ISBLANK(StartDate) && MonthNumber >= MONTH(StartDate) && MonthNumber <= MONTH(EndDate)
VAR TargetDate = DATE(YEAR(StartDate), COALESCE(MonthNumber, 1), 1)
RETURN IF(Allowed, CALCULATE([cancellation_rate], REMOVEFILTERS(dim_date), DATESBETWEEN(dim_date[date_key], TargetDate, EOMONTH(TargetDate, 0))))
```
