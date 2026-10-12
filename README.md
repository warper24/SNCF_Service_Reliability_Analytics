# SNCF Service Reliability Analytics

**Projet de portfolio en cours — J01 à J05 validés.**

L'objectif est de comprendre l'évolution de la fiabilité des liaisons TGV et de
fournir un outil d'aide à la priorisation des investigations. Le projet utilise
les données publiques SNCF, Python, BigQuery, dbt et Power BI.

## Avancement par jalon

| Jalon | Ce qui est réalisé ou prévu | État |
|---|---|---|
| J01 — Cadrage et audit | Définir les questions métier, examiner la source et documenter les indicateurs et limites. | Validé |
| J02 — Environnement | Préparer les outils et vérifier les connexions à BigQuery et Power BI. | Validé |
| J03 — Ingestion | Extraire et charger les données en conservant leurs versions et les traces de contrôle. | Validé |
| J04 — Normalisation et qualité | Structurer les champs et identifier les anomalies ainsi que les usages autorisés. | Validé |
| J05 — Modèle analytique | Huit tables de référence, ratios pondérés, comparaisons et éligibilité vérifiés ; 76 tests J05 réussis. | Validé |
| J06 — Diagnostic | Comparer les évolutions des liaisons et justifier les investigations prioritaires. | À réaliser |
| J07 — Modèle Power BI | Connecter les tables et créer les relations et mesures du rapport. | À réaliser |
| J08 — Rapport | Concevoir les pages et le parcours de lecture pour faciliter la décision. | À réaliser |
| J09 — Automatisation et reprise | Assembler les étapes, automatiser les contrôles et vérifier la reprise après échec. | À réaliser |
| J10 — Livraison finale | Finaliser la documentation et les livrables accessibles aux recruteurs. | À réaliser |
| J11 — Extension Intercités | Ajouter une seconde source après publication de la première version TGV. | Facultatif |

Chaque jalon suivant fera l'objet d'un commit et d'un envoi GitHub après validation.
Le premier commit regroupe l'état J01–J04, sans inventer un historique antérieur.

## Résultat actuel

L'ingestion et la préparation portent sur **12 907 observations mensuelles**, de
janvier 2018 à septembre 2026. J05 ajoute quatre dimensions, deux faits et deux marts
BigQuery, vérifiés par 76 tests dbt réussis. Les 18 contrôles J04 et 37 tests Python
réussissent également ; quatre avertissements source restent documentés.
Les comparaisons centrales retrouvent 102 liaisons National éligibles au semestre
et 88 à l'année, selon les fenêtres et critères arrêtés avant diagnostic.
Aucun classement de performance ou rapport métier Power BI n'est encore livré.

Les analyses restent au niveau d'une liaison orientée et d'un service. Les données
ne permettent pas de reconstruire un taux national, de convertir les causes en
effectifs ou de démontrer une causalité. Les anomalies et exclusions sont conservées.

## Pour aller plus loin

- [Plan détaillé](PLAN.md) et [bilans des jalons](docs/milestones/).
- [Contrat de données](docs/data_contract.md) et [définitions des indicateurs](docs/kpi_dictionary.md).
- [Audit de la source](reports/source_audit.md) et [rapport de qualité J04](reports/data_quality.md).
- [Modèle analytique J05](docs/data_model.md) et [validation des calculs](reports/data_model_validation.md).
- [Installation et reproduction](docs/setup.md).
- [Preuves publiques anonymisées](reports/publication_evidence/) et [journal de publication](docs/publication.md).

Les exports complets, secrets et caches restent hors Git. Les preuves publiques
conservent les résultats historiques ; leur [manifeste](reports/publication_evidence/manifest.json)
distingue les empreintes originales des copies anonymisées.

## Source et attribution

Données : **SNCF Voyageurs**, [Régularité mensuelle TGV par liaisons](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/),
sous [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
Les versions utilisées sont identifiées dans les rapports. Ce portfolio est
indépendant de SNCF. La licence de réutilisation du code reste à choisir à J10.
