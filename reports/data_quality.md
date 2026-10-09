# Qualité des données — J04

**J04 est terminé avec avertissements documentés, le 8 octobre 2026.** Les 12 907
observations brutes J03 sont conservées dans deux vues SQL. Les 26 champs sont typés
et normalisés selon le contrat ; aucune anomalie source n'est corrigée ou supprimée.
Les tests bloquants réussissent. Ce rapport décrit les usages permis, sans diagnostic
de performance ou classement.

## Version, périmètre et preuves

- Source SNCF Voyageurs : `regularite-mensuelle-tgv-aqst` ; janvier 2018–septembre 2026.
- Archive : `20261007T130103249967Z_bce4ef24` ; 146 combinaisons liaison orientée/service.
- Version : `e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6`.
- SHA-256 source : `8dc2b0a9a3707306c3087f899163465e34b20ed44b4dfc4ad46d5af4686334b2`.
- Vues : `sncf-reliability-analytics.sncf_dev.stg_tgv_reliability` et
  `int_tgv_quality_flags`, dans EU, reliées à la table brute figée J03.
- Qualification réussie : `20261008T100405Z_b0a4b733`, datée dans [validation.json](publication_evidence/data_quality_evidence/validation.json).

Les 12 907 payloads, numéros, versions et empreintes ont été comparés entièrement à
l'archive. Les tests vérifient aussi l'absence de perte, duplication ou modification
entre brut, staging et intermediate. Les types réels des vues correspondent aux YAML.

Preuves : [tests](publication_evidence/data_quality_evidence/tests.txt), [vues](publication_evidence/data_quality_evidence/models.txt),
[compilation](publication_evidence/data_quality_evidence/compile.txt), [synthèse](publication_evidence/data_quality_evidence/quality_summary.csv),
[couverture](publication_evidence/data_quality_evidence/coverage.csv), [fenêtres J01](publication_evidence/data_quality_evidence/period_coverage.csv),
[anomalies ciblées](publication_evidence/data_quality_evidence/anomaly_examples.csv), [cas revus](publication_evidence/data_quality_evidence/manual_cases.csv).
Ces CSV de contrôle ne constituent pas l'export source complet. La [revue finale](publication_evidence/data_quality_evidence/git_review.json) confirme les empreintes, les exclusions Git et les objets cloud.

## Résultats et exclusions

Unité : observations mensuelles de liaison/service, jamais trains physiques distincts.
Dénominateur : 12 907 observations. Les motifs se recouvrent et ne s'additionnent pas.

| Contrôle ou usage | Observations concernées | Conséquence |
|---|---:|---|
| Clé nulle, conversion invalide, champ absent du schéma | 0 | Aucun défaut structurel après correction de notre lecture JSON |
| Doublon de clé métier | 0 | Grain mois × départ × arrivée × service préservé |
| Effectifs centraux incompatibles | 63 | Exclusion de leurs usages incompatibles ; brut conservé |
| Taux d'annulation indisponible | 73 | 12 834 observations utilisables |
| Taux de retard arrivée indisponible | 73 | 12 834 observations utilisables |
| Proxy nul dans une population compatible | 10 | Effectif nul disponible ; ratio indisponible |
| Effectif départ indisponible | 64 | Contrôle propre au départ |
| Effectif négatif | 43 | Champ >30 ; aucune correction inventée |
| Imbrication des seuils invalide | 361 | Couple des retards importants inutilisable |
| Quarantaine janvier–mars 2025 | 363 | Tout le trimestre exclu pour le couple >30/>60 |
| Taux de retards importants indisponible | 443 | Union des restrictions ; 12 464 utilisables |
| Champs >15 hors KPI génériques | 12 907 | Restriction de périmètre D04 |
| Profils de causes entièrement nuls | 272 | Profil non exploitable |
| Profils de causes incomplets / hors bornes | 0 / 0 | États distincts conservés pour les versions futures |
| Profils non nuls hors tolérance de somme | 10 | Parts visibles avec avertissement, sans renormalisation |
| Moyenne arrivée des trains en retard négative | 2 | Cette moyenne exclue, indépendamment des effectifs |
| Moyenne tous trains arrivée / départ négative | 122 / 170 | Valeurs signées conservées |
| Moyenne >15 négative | 8 | Signalement ; champ déjà hors KPI génériques |
| Services simultanés | 84 lignes | Périmètre à examiner, sans dédoublonnage |
| Au moins un motif de qualité dans la vue | 960 | Signal de revue, jamais filtre global d'exclusion |

Les 63 incompatibilités centrales et dix populations compatibles nulles expliquent
les 73 taux centraux indisponibles. Les causes restent mensuelles : 12 635 profils
consultables, dont dix avec avertissement. La tolérance est de 0,1 point autour de
100 %, avec une garde de 1e-9 point contre l'erreur flottante de frontière. Elle ne
prouve pas le dénominateur ou l'exhaustivité. Aucune conversion en effectifs,
moyenne temporelle ou agrégation entre liaisons n'est autorisée.

## Couverture et comparabilité

Dix des 146 combinaisons liaison/service comportent 88 mois absents entre leur
première et dernière observation. Les mois extérieurs ne sont pas assimilés à une
desserte attendue. Aucun mois absent n'est remplacé par une observation à zéro.

Les fenêtres J01 retrouvent **102/116** combinaisons nationales passant le filtre de
couverture pour janvier–juin 2026/2025 et **88/116** pour 2025/2024 : présence complète,
effectifs centraux valides, proxy ≥30 par mois et service unique dans les fenêtres.
Les 116 sont les combinaisons nationales historiques, pas les liaisons actives chaque
mois. Les résultats 102/88 ne sont pas des invariants. Aucun taux, rang ou priorité
n'est calculé ici. La quarantaine T1 2025 interdit de reprendre automatiquement
l'échantillon central pour les comparaisons de retards importants.

## Tests et revue manuelle

La suite finale contient **20 tests de données et deux tests unitaires** :
16 tests de données bloquants et les deux tests unitaires réussissent ; quatre tests
de données produisent des avertissements conservés.

| Avertissement | Observations distinctes | Lecture |
|---|---:|---|
| `warn_source_counts` | 425 | Anomalies d'effectifs et de relations |
| `warn_cause_profiles` | 282 | 272 profils nuls + dix sommes hors tolérance |
| `warn_signed_means` | 278 | Union des moyennes/durées négatives ; pas d'erreur systématique présumée |
| `warn_service_scope` | 84 | Services simultanés, pas doublons de la clé complète |

Les deux suites unitaires couvrent 39 observations : mois malformés, JSON invalide,
null/champ absent, entier fractionnaire, décimal non round-trip, zéro, valeurs
manquantes, populations, seuils, quarantaine, moyennes, tolérance, services et directions.

Huit cas réels ont été examinés dans `manual_cases.csv` :

- Dijon Ville → Paris Lyon, janvier 2025 : P=426, A=4, proxy=422, L=60, >30=−1,
  >60=30. Usages centraux permis selon D01 ; couple important exclu.
- Marseille St Charles → Madrid, août 2020 : P=A=L=0 ; effectif arrivée disponible,
  taux indisponible et profil nul non exploitable.
- Paris Lyon → Aix-en-Provence TGV, avril 2020 : P=0, A=17 ; proxy indisponible.
- Bellegarde (Ain) → Paris Lyon, mai 2018 : L=45, profil entièrement nul ;
  taux central permis, profil indisponible.
- Paris Montparnasse → Vannes, juin 2026 : somme ≈87,5 %, parts conservées avec avertissement.
- Nîmes → Paris Lyon, novembre 2019 : moyenne des seuls trains en retard ≈−40,11 minutes,
  exclue sans supprimer les effectifs centraux.
- Paris Vaugirard → Bordeaux St Jean, avril 2018 : moyenne tous trains ≈−0,161 minute,
  signe conservé ; usages centraux permis.
- Paris Est → Reims, septembre 2018 : cas ordinaire compatible.

Les 37 tests Python existants ont réussi le 8 octobre 2026. Les modules et preuves
J01/J03 n'ont pas été modifiés ; aucun reprofilage n'a remplacé leurs validations.
La revue manuelle porte sur ces cas ; les contrôles automatisés couvrent toute la version.

## Difficultés résolues, consommation et limites

PARSE_JSON en mode exact refusait 138 payloads à cause de décimaux comme 10.25641026.
Le document de structure utilise désormais `wide_number_mode='round'` ; les valeurs
sont extraites directement du STRING brut puis typées, sans sérialisation numérique
intermédiaire. Les 138 fausses absences ont disparu ; un cas unitaire protège la
correction. Le texte brut reste intact ; FLOAT64 ne promet pas une représentation
décimale exacte.

La première requête de synthèse utilisait un alias UNNEST ambigu, traité comme STRUCT.
L'accès est désormais explicite par `check_rule.rule`. Le client BigQuery reçoit
`job_retry=None` pour les requêtes à identifiant explicite. Les échecs et traces
restent conservés hors OneDrive.

Les cinq requêtes de preuves finales comptent 63 963 136 octets facturables cumulés ;
cela n'inclut pas tous les essais/tests J04 et n'est pas une facture en euros.
La relecture finale du brut a bénéficié du cache, avec zéro octet facturable observé.
Les identifiants de jobs et octets figurent dans la validation. La limite de 100 MB
s'applique à chaque requête ; elle ne plafonne pas le cumul. Aucune gratuité ou
vérification de facture finale n'est revendiquée.

D01–D07 restent en vigueur : P−A non certifié, dénominateur des causes inconnu,
restrictions des seuils, services et libellés préservés. Aucun référentiel de gares
n'a été introduit sans correspondance justifiée. Aucune dimension, fait, mesure
SQL/DAX, actualisation Power BI, automatisation, publication ou reconstruction sur
machine neuve n'est réalisée à J04.

## Reproduction et attribution

Utiliser [la qualification J04](../docs/setup.md#qualification-j04). Le script conserve
les preuves sans dupliquer les règles métier SQL en Python. Chaque exécution est
archivée sous `SNCF_DATA_DIR/quality_runs` sans purge. Les vues sont une préparation
de développement ; aucune publication multi-table cohérente J09 n'est revendiquée.

Données : SNCF Voyageurs, [Régularité mensuelle TGV par liaisons](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/),
extraction du 7 octobre 2026, sous [ODbL](https://opendatacommons.org/licenses/odbl/1-0/).
Portfolio indépendant de SNCF.
