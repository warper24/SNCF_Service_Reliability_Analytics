# Validation du modèle analytique — J05

**J05 qualifié le 9 octobre 2026, avec les limites métier conservées.** La
qualification `20261009T142236Z_7e5f8893` a construit huit tables BigQuery EU,
réussi les 76 tests J05 et retrouvé les 18 contrôles J04 réussis avec leurs quatre
avertissements. Aucun classement de performance ni rapport métier Power BI livré.

Preuves : [validation complète](publication_evidence/data_model_evidence/validation.json),
[tests J05](publication_evidence/data_model_evidence/tests.txt),
[tests J04 exécutés dans J05](publication_evidence/data_model_evidence/upstream_tests.txt),
[objets construits](publication_evidence/data_model_evidence/models.txt),
[revue manuelle](publication_evidence/data_model_evidence/manual_review.json).
La [revue Git du 12 octobre](publication_evidence/data_model_evidence/git_review.json)
contrôle séparément le contenu destiné à la publication, sans renouveler les tests.
Les originaux locaux sont dans `reports/data_model_evidence/` ; les copies publiques
sont anonymisées et reliées aux originaux par le
[manifeste de publication](publication_evidence/manifest.json). La copie publique
ne renouvelle pas la date ni la portée de la validation.

## Source, code et exécution

- Archive : `20261007T130103249967Z_bce4ef24` ; janvier 2018 à septembre 2026.
- Version : `e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6`.
- Les 12 907 payloads bruts, leurs positions et empreintes ont été comparés à
  l'archive locale ; aucune nouvelle extraction ni promotion de `raw_tgv_current`.
- Python 3.13.15, dbt Core 1.12.5, dbt-bigquery 1.12.1,
  google-cloud-bigquery 3.45.2 ; verrou de dépendances inchangé.
- Projet dbt 0.5.0 ; paquet d'ingestion 0.3.0 inchangé.
- Invocation de construction des huit tables : `cb98c616-8ac2-46ef-ad1e-af365083238b`.
- Les empreintes du code sont vérifiées inchangées entre début et fin de qualification.
  Les dates ISO des preuves portent leur décalage horaire ; le nom d'exécution est UTC.
- Les schémas réels, types déclarés et documentation de toutes les colonnes ont été
  vérifiés ; deux vues J04 et huit tables J05, dans `sncf_dev`.

Le collecteur pilote les étapes ; les transformations métier et assertions sont
SQL/dbt. Aucun export complet des tables analytiques. Les logs, artefacts dbt,
résultats par étape et SQL compilés sont conservés hors OneDrive sous
`SNCF_DATA_DIR/model_runs/20261009T142236Z_7e5f8893`.

## Tables et couverture

| Table | Lignes obtenues | Interprétation |
|---|---:|---|
| `dim_date` | 3 287 | Calendrier 2018–2026 en années complètes, sans fait quotidien inventé |
| `dim_route` | 130 | Couples départ → arrivée distincts |
| `dim_service` | 2 | Services source distincts |
| `dim_cause` | 6 | Catégories du contrat |
| `fct_reliability_monthly` | 12 907 | Une ligne par observation mensuelle J04 |
| `fct_delay_causes_monthly` | 77 442 | Six catégories par observation, NULL conservés |
| `mart_route_trends` | 12 907 | Même grain, comparaison exacte au mois N−1 |
| `mart_route_priorities` | 232 | 116 candidats National × deux comparaisons, exclusions conservées |

Ces effectifs décrivent cette version ; ils ne sont pas codés comme invariants des
extractions futures. [Résultat de contrôle des tables](publication_evidence/data_model_evidence/j05_model_summary.csv).

| Comparaison | Candidats | Éligibles centraux | Fenêtre courante incomplète | Référence incomplète | Périmètre service exclu |
|---|---:|---:|---:|---:|---:|
| Janvier–juin 2026 / 2025 | 116 | 102 | 7 | 9 | 9 |
| Années 2025 / 2024 | 116 | 88 | 9 | 9 | 23 |

Les motifs se recouvrent : leurs nombres ne s'additionnent pas. Les résultats
retrouvent J04 sans figer 102/88 dans le SQL. Les fenêtres et critères restent
ceux de J01 malgré la présence de juillet–septembre 2026 dans la source.
[Preuve de couverture](publication_evidence/data_model_evidence/j05_period_coverage.csv).

La persistance semestrielle est disponible pour les 102 liaisons éligibles ; elle
reste indisponible pour la comparaison annuelle. Le couple >30/>60 possède une
couverture complète pour 109 candidats au semestre 2026, mais aucun au semestre
2025. À l'année, 107 candidats sont complets en 2024, aucun en 2025. **Les deux
comparaisons des retards importants ne sont donc pas disponibles**, conformément
à la quarantaine T1 2025. Cela ne supprime pas les comparaisons des taux centraux.

## Contrôles automatisés

| Critère et risque | Contrôle exécuté et résultat | Preuve ; sens d'un échec |
|---|---|---|
| Fidélité et version | Archive/brut vérifiés, une seule version attendue, contenu J04 conservé | Validation et tests de fidélité ; écart bloque la qualification |
| Grain et directions | Unicité des faits/marts, clés non nulles, aller/retour et séparateurs ambigus couverts | Tests SQL, génériques et unité des clés ; duplication ou fusion bloque |
| Relations | Toutes les clés étrangères trouvent leur dimension, clés de dimension uniques | Tests `relationships`, `unique`, `not_null` ; orphelin ou dimension ambiguë bloque |
| Calendrier | Continuité, attributs, premier jour dans les faits, paire exacte N−1 | Tests calendrier/tendances ; un trou n'est pas remplacé par un décalage de ligne |
| Causes | Six catégories, parts/statuts/provenance fidèles, NULL distinct de zéro | Test exhaustif et unité avec une part absente ; omission ou transformation injustifiée bloque |
| KPI | Recalcul indépendant depuis les effectifs, garde des divisions, restrictions par usage | Test des KPI et unité de cinq observations ; usage invalide ou taux erroné bloque |
| Pondération | Exemple synthétique 15/110 = 0,136363636, sans moyenne simple | Unité du mart ; taux 0,30 serait un échec |
| Éligibilité | Recalcul depuis J04, mois attendus/présents/valides, N≥30, service sur les fenêtres | Test des périodes, neuf situations synthétiques ; comparaison inéligible rendue disponible bloque |
| Seuils et persistance | +2 points inclus, valeur sous le seuil, exactement 90 %, 4/6, amélioration, année sans règle semestrielle | Unités et assertions ; frontière ou extension annuelle incorrecte bloque |
| Matérialisation et types | Huit tables finales, deux vues de préparation ; schémas réels et colonnes documentées vérifiés | `objects` et `schema_types_verified` ; objet/type inattendu bloque |

J05 : **69 tests de données et sept tests unitaires réussis**, aucun avertissement
J05. Requalification J04 : **16 tests de données et deux tests unitaires réussis**,
quatre contrôles au statut warning. Total : 94 réussites et quatre warnings,
aucun échec ni test ignoré. Les unités s'exécutent dans BigQuery sur des entrées
synthétiques ; elles ne constituent pas des tests locaux sans cloud.

Les warnings J04 restent : effectifs 425, profils de causes 282, moyennes signées
278, services 84. Ils décrivent des populations qui se recouvrent et ne sont pas
un nombre total de lignes invalides. Les défauts source restent présents et leurs
usages encadrés. Les 37 tests Python existants ont également réussi en 3,756 s ;
leur sortie a été examinée dans la console, avec synthèse dans la revue manuelle.
Les scripts d'audit/ingestion, leurs tests et les modèles staging/intermediate
restent identiques au commit de départ ; 15 fichiers contrôlés. Les 28 originaux
de preuves historiques correspondent toujours à leurs empreintes de publication.

## Revue manuelle des huit cas réels

La requête de réconciliation relit les champs JSON SNCF `nb_train_prevu`,
`nb_annulation`, `nb_train_retard_arrivee` et les compare aux KPI du fait.
[Huit observations examinées](publication_evidence/data_model_evidence/j05_reconciliation.csv).

| Cas | Résultat et interprétation |
|---|---|
| Paris Est → Reims, septembre 2018 | P=206, A=1, N=205, L=27 : retard 0,131707317 ; résultat source et fait identiques |
| Dijon Ville → Paris Lyon, janvier 2025 | P=426, A=4, N=422, L=60 : retard 0,142180095 ; >30 brut −1 et >60 brut 30 conservés, KPI importants NULL |
| Marseille St Charles → Madrid, août 2020 | P=A=L=N=0 : ratios NULL, effectif analytique >30 nul disponible ; zéro et indisponibilité distincts |
| Paris Lyon → Aix-en-Provence TGV, avril 2020 | P=0, A=17 : population incompatible, proxy et ratios indisponibles |
| Nîmes → Paris Lyon, novembre 2019 | Moyenne des seuls trains en retard négative signalée ; taux central 63/215 disponible, sans suppression globale |
| Paris Montparnasse → Vannes, juin 2026 | Profil hors tolérance signalé ; taux central 56/258 disponible, aucune renormalisation des causes |
| Paris Vaugirard → Bordeaux, avril 2018 | Moyenne tous trains signée préservée ; taux 2/42, taux importants égaux à zéro et disponibles |
| Bellegarde → Paris Lyon, mai 2018 | Profil entièrement nul non exploitable malgré L=45 ; taux central 45/171 disponible |

Ces exemples valident des comportements, sans constituer un diagnostic de priorité
ou une explication causale. La réserve D01 accompagne tous les taux sur N.

## Exécutions et corrections

Deux tentatives échouées sont conservées dans `model_runs/` :

1. `20261009T141525Z_34a5814c` : sélection indirecte de trois tests J05 pendant J04,
   avant création de leurs tables ; correction par sélection `cautious` dans les
   deux collecteurs. Les 18 contrôles J04 avaient réussi avec quatre warnings.
2. `20261009T141732Z_895b3525` : huit tables créées, 73 tests J05 réussis, trois
   erreurs de syntaxe des assertions. BigQuery exigeait une source pour les SELECT
   filtrés et un agrégat dans la projection pour le contrôle HAVING. Corrections
   des tests calendrier, causes et version ; aucune correction de valeur source.

La qualification finale a repris la chaîne complète après corrections et ajouté
le contrôle explicite de documentation/types et des valeurs indisponibles attendues.
Aucune tentative échouée n'a été présentée comme une réussite ni supprimée.

Les trois requêtes de preuves finales sont identifiées dans la validation :

- synthèse : `sncf_j05_96499ad6609c421a9d8ecbef81b5c6df` ; 0 octet facturable déclaré ;
- réconciliation : `sncf_j05_7720d19766fe40dcaa481ee88a0d967a` ; 20 971 520 octets ;
- couverture : `sncf_j05_3d0af3c044d541e8bd9c6d9d6cf9262d` ; 10 485 760 octets.

Ces volumes ne représentent pas la consommation totale du jalon : constructions,
tests et tentatives précédentes sont distincts. La limite est de 100 MB par
requête ; la facture finale et un plafond quotidien bloquant n'ont pas été vérifiés.

## Limites et reproduction

Voir [le modèle](../docs/data_model.md), [la commande complète](../docs/setup.md#qualification-j05)
et [le bilan pédagogique](../docs/milestones/J05_handoff.md).
D01–D07 sont conservées ; les tests ne certifient pas le dénominateur ni la causalité.
Aucun taux national, effectif par cause, agrégation de profils, indicateur voyageurs
ou promesse de gain. Aucun classement J06, réconciliation SQL/DAX, actualisation
Power BI, publication dans `sncf_publish`, orchestration CI ou reprise multi-table
n'est revendiqué. La reconstruction depuis une machine neuve reste non exécutée.
