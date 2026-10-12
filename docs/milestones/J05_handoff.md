# J05 — Modèle analytique en étoile et calculs de référence

**État : terminé avec limites explicites le 9 octobre 2026.** Huit tables BigQuery
qualifiées, 76 tests J05 réussis, 18 contrôles J04 réussis et quatre avertissements
J04 conservés. Les 37 tests Python existants réussissent. Aucun travail J06 engagé.

Le fait principal conserve 12 907 observations, le fait des causes 77 442 parts,
les tendances 12 907 lignes et le mart des priorités 232 candidats/comparaisons.
La couverture retrouve 102/116 liaisons National éligibles au semestre et 88/116
à l'année. Aucun de ces effectifs n'est un invariant des extractions futures.

La publication a été reprise le 12 octobre 2026 après interruption : contrôle des
57 empreintes de code qualifié, des preuves locales et des 38 copies publiques,
sans réexécution cloud ni changement des résultats du 9 octobre. Le journal de
clôture Git est dans [publication.md](../publication.md).
La [revue des fichiers indexés](../../reports/publication_evidence/data_model_evidence/git_review.json)
complète les preuves publiques avant envoi ; aucun secret, profil réel, export
complet ou cache n'a été trouvé dans le contenu examiné.

## Présentation, accord et objectif

La préparation en lecture seule a examiné PLAN, AGENTS, le bilan J04, les contrats
métier, le code, Git, l'archive J03, l'environnement et les preuves publiques.
Les 28 empreintes de preuves publiques concordaient. Une présentation détaillée a
couvert objectif, notions, huit tables, fichiers complémentaires, étapes, circulation
des données, choix, alternatives, contrôles, limites, extensions et entretien.
La préparation s'est arrêtée pour attendre l'accord ; aucun fichier n'avait changé.

Accord explicite reçu : **« Ok tu peux implémenter »**. Il couvre J05 présenté,
y compris tests, collecteur, documentation et publication ordinaire du jalon validé.
Branche créée : `codex/j05-model`, depuis le commit réel `8766048` de J01–J04.
Le dépôt était propre et isolé du dossier parent ; aucun autre projet n'est modifié.

Objectif métier : fournir une base cohérente pour comparer les liaisons et préparer
les investigations de J06. Objectif technique : tables communes SQL/Power BI,
grains maîtrisés, effectifs conservés et calculs de référence traçables. Aucun
classement ni score n'est imposé ; DAX et rapport Power BI restent à J07/J08.

## Approche acceptée et déroulement

1. Réutiliser l'archive J03 et sa table brute figée, vérifier payloads et empreintes,
   conserver la localisation EU et la limite de 100 MB par requête.
2. Requalifier les préparations J04 dans la nouvelle exécution J05, sans écraser
   les preuves historiques ni réextraire la source.
3. Construire quatre dimensions partagées : calendrier, liaison orientée, service,
   cause. Les clés déterministes ne fusionnent aucun libellé de gare.
4. Construire deux faits : observations mensuelles et profils de causes longs.
   Conserver NULL, zéro, restrictions par indicateur et provenance.
5. Construire tendances mensuelles et variables de priorisation sur les fenêtres
   J01 ; conserver tous les candidats, leurs couvertures et motifs d'exclusion.
6. Exécuter les tests, réconcilier des cas source, inspecter objets et preuves,
   documenter les résultats et préparer leurs copies publiques.

Les huit modèles finaux sont matérialisés en tables dans `sncf_dev`. Le PC organise
l'exécution ; BigQuery calcule et stocke. Les préparations restent des vues. Les
journaux complets, manifestes dbt, résultats et SQL compilés restent sous
`SNCF_DATA_DIR/model_runs/<run_id>`, hors OneDrive ; aucun export complet des tables
n'est ajouté au dépôt. Un échec conserve ses traces et ne remplace pas la dernière
preuve réussie dans `reports/data_model_evidence/`.

## Livrables, producteurs et utilisateurs

Les fichiers SQL/YAML sont écrits par le développeur et exécutés par dbt/BigQuery.
Les résultats générés servent à la qualification ; les documents transmettent
les choix au porteur du projet, à l'analyste J06 et au concepteur Power BI J07.

| Fichier | Contenu, fonction et liens |
|---|---|
| `dbt/models/marts/dim_date.sql` | Calendrier quotidien continu couvrant source et fenêtres ; dates des faits et grille des comparaisons |
| `dim_route.sql` dans le même dossier | Couples orientés exacts et empreinte stable ; rattachement des deux faits |
| `dim_service.sql` | Services source distincts ; rattachement des faits |
| `dim_cause.sql` | Six codes, libellés français et correspondances SNCF ; fait des causes |
| `fct_reliability_monthly.sql` | Champs utiles J04 intacts, clés, taux et effectifs analytiques masqués ; tendances et priorités |
| `fct_delay_causes_monthly.sql` | Six parts par observation, NULL inclus, sans effectif dérivé ; futur diagnostic des profils |
| `mart_route_trends.sql` | Jointure au mois exact N−1, écarts et signaux mensuels |
| `mart_route_priorities.sql` | Ratio des sommes, éligibilité, couverture, signaux et persistance autorisée ; aucun classement |
| `marts.yml` | Documentation, unités, clés, tests génériques et relations |
| `j05_unit_tests.yml` | Sept suites de cas synthétiques vérifiant les branches métier |
| `dbt/macros/j05_contract.sql` | Expressions communes des clés, ratios et seuils exacts ; définition des fenêtres |
| `dbt/tests/assert_j05_grains.sql` | Unicité des grains des faits et marts |
| `assert_j05_fidelity.sql` | Aucune perte, multiplication ou altération des champs J04 conservés |
| `assert_j05_causes.sql` | Six catégories et égalité de chaque part/statut/provenance |
| `assert_j05_kpis.sql` | Recalcul indépendant des taux depuis les effectifs et conditions brutes |
| `assert_j05_calendar_and_keys.sql` | Continuité, convention mensuelle, clés déterministes |
| `assert_j05_version.sql` | Source non vide, unique et conforme à la version attendue |
| `assert_j05_trends.sql` | Paires calendaires exactes, populations et écart indépendant |
| `assert_j05_periods.sql` | Couverture et ratios de périodes réconciliés depuis J04 |
| `dbt/analyses/j05_model_summary.sql` | Effectifs des huit tables, résultat généré de contrôle |
| `j05_reconciliation.sql` | Huit cas réels, calculs directs depuis les champs JSON SNCF |
| `j05_period_coverage.sql` | Couverture des deux comparaisons, sans export ni classement du mart complet |
| `scripts/validate_data_model.py` | Transport, pilotage, contrôle des objets et collecte ; aucune transformation métier Python |
| `dbt/dbt_project.yml` | Version 0.5.0, tables/tag J05, seuils et fenêtres explicites |
| `scripts/validate_data_quality.py` | Correction de sélection indirecte pour maintenir l'isolation des contrôles J04 |
| `docs/data_model.md` | Schémas, conventions, formules, usages interdits, décisions et limites |
| `reports/data_model_validation.md` | Résultats, revue manuelle, preuves et limites de validation |
| `docs/setup.md`, `docs/architecture.md` | Reproduction et architecture désormais effective |
| `.gitignore`, `scripts/prepare_publication.py` | Originaux J05 ignorés ; copies publiques anonymisées et manifestées |
| `README.md`, `PLAN.md`, `docs/publication.md`, ce bilan | État réel, transmission et publication progressive |

## Définitions, décisions et exemples

Une table de faits représente une observation au grain défini ; une dimension
décrit un axe partagé. Ici le fait principal est mensuel, par liaison orientée et
service. Le fait des causes ajoute la catégorie. Une relation plusieurs-à-un
rattache chaque fait à une description unique. Une matérialisation en table stocke
le résultat ; une vue classique conserve une requête. Un mart prépare une question
analytique, sans fixer son interprétation.

Les clés SHA-256 utilisent les libellés exacts, avec STRUCT JSON pour le couple
orienté. Elles sont reproductibles et évitent l'ambiguïté des séparateurs, sans
constituer des identifiants officiels de gare. Le calendrier contient des jours,
mais `2025-01-01` représente le mois de janvier dans le fait : aucune observation
journalière n'est inventée, aucun mois absent n'est remplacé par zéro.

Le contrat est le ratio des sommes dans une même liaison/service. Exemple fictif :
10/100 puis 5/10 donnent 15/110 ≈ 13,64 %, pas 30 %. Les numérateurs et dénominateurs
portent sur les mêmes mois valides. Les taux sont 0–1, les parts de causes 0–100.
P−A reste un proxy non certifié (D01). La quarantaine du couple >30/>60 au T1 2025
ne retire pas les taux centraux valides. Les profils de causes gardent six lignes,
y compris NULL et zéro, sans renormalisation ni conversion en effectifs.

Une jointure répétant 100 trains sur six causes donnerait artificiellement 600 :
les faits sont séparés et partagent les dimensions. Aucune somme interliaisons ne
devient un total national de trains distincts. Les seuils imbriqués ne s'additionnent
pas. Aucun voyageur, incident, coût ou gain n'est déduit de ces données mensuelles.

Les fenêtres restent janvier–juin 2026/2025 et années 2025/2024. Il faut tous les
mois valides, N≥30 chaque mois et un seul service dans les fenêtres. Le signal de
variation est ±2 points, la cible fictive 90 %, la persistance 4/6. Cette dernière
est indisponible à l'année. Les produits croisés comparent les seuils avant arrondi
des ratios NUMERIC ; le calendrier exact évite l'erreur d'une douzième ligne
précédente en présence d'un trou.

BigQuery et SQL/dbt sont conservés ; Python orchestre et rassemble les preuves.
Les tables finales sont reconstruites intégralement : au volume présent, cela
facilite les corrections/suppressions historiques. Un incrémental, un second moteur
ou une transformation Python parallèle ajouteraient des règles à maintenir sans
besoin démontré. Le calendrier mensuel serait plus compact, mais le calendrier
quotidien est réutilisable sous une convention mensuelle stricte. Un référentiel
de gares reste une extension conditionnée à des clés fiables. Aucun paquet ajouté.

## Incidents et ajustements ordinaires

La première qualification a sélectionné indirectement trois tests J05 dépendant
des vues J04, avant construction des tables J05. Les 18 contrôles J04 ont réussi,
avec leurs quatre warnings habituels ; les trois nouveaux tests ont échoué sur des
tables encore absentes. La correction `--indirect-selection cautious` borne la
sélection aux dépendances disponibles. Elle est appliquée au nouveau collecteur
et à celui de J04 pour conserver sa reproductibilité autonome. Aucun changement
de règle métier ni renouvellement des preuves historiques J04.

La deuxième tentative a construit les huit tables et réussi 73 tests J05 ; trois
assertions comportaient une syntaxe refusée par BigQuery (SELECT filtré sans FROM,
HAVING sans agrégat dans la projection). Les corrections ont porté sur les tests
calendrier, causes et version. Après renforcement de contrôles des signaux et des
types/documentation, la chaîne complète a réussi. Les deux tentatives échouées
restent conservées ; identifiants et explications dans le rapport de validation.

## Validation, versions et reproduction

La qualification définitive est détaillée dans
[le rapport J05](../../reports/data_model_validation.md) et les
[preuves publiques](../../reports/publication_evidence/data_model_evidence/).
Les contrôles ne sont revendiqués qu'après leur exécution réelle.

Qualification finale : `20261009T142236Z_7e5f8893`. J05 : 69 tests de données et
sept unités réussis ; J04 rejoué dans J05 : 16 tests de données et deux unités
réussis, quatre warnings (425 effectifs, 282 profils, 278 moyennes, 84 services).
Total : 94 réussites, quatre warnings, aucun échec ni test ignoré. Les schémas,
types déclarés, documentation de toutes les colonnes et matérialisations ont été
inspectés contre BigQuery. Les huit cas source ont été examinés manuellement.

La réconciliation retrouve notamment 60/422 = 0,142180095 pour Dijon → Paris Lyon
en janvier 2025, avec ses effectifs importants bruts conservés mais KPI NULL.
Une population nulle reste distincte d'un taux nul ; un profil de causes non
exploitable ne retire pas un taux central valide. Les deux comparaisons de retards
importants sont indisponibles car chacune implique le T1 2025 en quarantaine.

Les 28 originaux de preuves historiques concordent toujours avec leurs empreintes.
Quinze fichiers d'ingestion/audit/tests et des modèles J04 ont été comparés au
commit de départ, sans modification. Le changement du collecteur J04 est uniquement
la sélection indirecte documentée. Le collecteur J05 n'écrit pas les anciennes preuves.

Référence source : archive `20261007T130103249967Z_bce4ef24`, version canonique
`e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6`.
Les empreintes d'export/manifeste, versions installées, empreintes du code,
identifiants de jobs, schémas et statut figurent dans la validation J05.
La limite de 100 MB est par requête ; aucune garantie de dépense nulle ou de plafond
cumulé n'en découle. L'alerte budgétaire n'est pas un blocage.

Reproduction : [setup, qualification J05](../setup.md#qualification-j05).
La commande explicite vérifie l'archive et le brut, recrée les vues J04, les teste,
construit les tables J05, les teste, puis collecte les preuves. Les échecs sont
conservés. Les preuves historiques J01/J03/J04 restent intactes. Un nouveau contrôle
produit une nouvelle preuve datée, pas une réécriture du passé.

## Limites et transmission à J06

D01–D07 restent en vigueur. La présence de tables et de tests réussis ne certifie
pas la population des causes ou des circulations assurées. Les changements de
service ne prouvent pas une modification de desserte ; les libellés ne certifient
pas une continuité géographique. Aucun classement de performance, score, diagnostic
causal ou recommandation opérationnelle n'est livré à J05.

Power BI n'est pas actualisé ; aucune mesure DAX, publication dans `sncf_publish`,
automatisation CI, restauration multi-table ou reconstruction depuis une machine
neuve n'est validée ici. Une sauvegarde indépendante des archives locales reste
distincte de leur conservation. `.gitignore` ne désactive pas OneDrive.

J06 pourra interroger les faits et les deux marts, distinguer niveau, évolution,
persistance et volume, et tester les sensibilités prévues sans déplacer les fenêtres
ou choisir les seuils après observation d'un classement. Il conservera les candidats
exclus et la couverture par indicateur. Sa présentation et son accord restent requis.

## Bilan pédagogique

Compétences : modélisation dimensionnelle, clés reproductibles, jointures et grains,
SQL BigQuery, pondération, comparaisons calendaires, dbt, tests, preuves et traçabilité.

Questions d'entretien facultatives :

- Pourquoi deux faits ? Grains distincts et protection contre la multiplication des effectifs.
- Pourquoi conserver les effectifs ? Recalculer les ratios de sommes sur la bonne population.
- Pourquoi pas LAG 12 ? Douze lignes ne garantissent pas douze mois.
- Pourquoi des signaux NULL ? Absence d'éligibilité ou de définition, distincte d'une absence de dégradation.
- Un test vert certifie-t-il D01 ? Non, il contrôle l'implémentation de la convention.
- Pourquoi des clés déterministes ? Reconstruction stable sans ordre arbitraire des lignes, sous réserve des libellés source.

Approfondissements hors périmètre : référentiel officiel de gares (clés fiables,
effort moyen à important), comparaison des versions analytiques (plusieurs versions
qualifiées, effort moyen), optimisation des tables après mesure (effort selon le
besoin). Sensibilité des priorités à J06, modèle sémantique à J07, reprise à J09.
