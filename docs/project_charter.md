# Charte du projet — J01

Décisions arrêtées le 1er octobre 2026, après présentation pédagogique et accord explicite du porteur du projet. Voir [le bilan J01](milestones/J01_handoff.md).

## Utilisateur et décision attendue

L'utilisateur métier fictif est une équipe de pilotage de la qualité de service ferroviaire. Elle souhaite sélectionner les liaisons à examiner, distinguer détérioration récente et sous-performance durable, puis orienter une investigation avec des éléments chiffrés traçables.

La question initiale sur les « causes responsables » est reformulée en question observable : **quelles liaisons présentent une détérioration mesurée et quels motifs y sont déclarés ?** Des données mensuelles agrégées ne démontrent pas la responsabilité causale d'un motif. Une amélioration ou l'absence de dégradation est un résultat recevable.

Décisions possibles : sélectionner une liaison pour examen, demander des informations sur des incidents ou sur une rupture de desserte, et choisir un indicateur de suivi. Aucune économie, réparation précise ou efficacité d'action n'est déduite automatiquement.

## Périmètre V1

- Jeu SNCF Voyageurs `regularite-mensuelle-tgv-aqst` ; historique complet conservé pour l'audit.
- Unité : liaison orientée × service × mois ; les sens aller et retour sont distincts.
- Vue principale : valeur source `National`, avec exclusions explicites des périmètres incertains. Cette valeur n'est pas une certification géographique : Paris–Barcelone y apparaît depuis octobre 2025.
- International conservé dans le brut, hors classement principal. Ne pas fusionner les services pour combler une absence.
- Lecture récente : janvier 2023 à juin 2026. Les années 2018–2022 restent accessibles pour la qualité et le contexte, sans être le comparateur principal.
- Comparaison principale : janvier–juin 2026 contre janvier–juin 2025.
- Comparaison complémentaire : janvier–décembre 2025 contre janvier–décembre 2024, avec son propre ensemble de liaisons éligibles. Ne pas comparer ces deux classements comme s'ils avaient le même périmètre.

Les décisions de période sont liées à la version auditée, pas à la date courante de la machine. Une nouvelle extraction ne déplace pas automatiquement ces fenêtres.

## Règles de sélection fixées avant le diagnostic

Pour chaque comparaison, exiger exactement une observation par mois attendu dans les deux périodes : 6/6 + 6/6 mois pour le semestre, 12/12 + 12/12 pour l'année. Aucun mois manquant n'est remplacé par zéro.

Les trois effectifs centraux doivent être entiers, renseignés et compatibles : `0 ≤ annulés ≤ prévus` et `0 ≤ retards arrivée ≤ prévus − annulés`. Exiger au moins **30 circulations déduites par mois**, dans chaque période. Il s'agit d'un seuil pratique du projet, pas d'une garantie statistique. Il évite qu'un taux très instable à très faible volume domine le diagnostic ; les volumes demeurent visibles. La couverture sous seuils 15/30/60 est conservée, et leur effet sur le classement sera étudié à J06.

Une liaison présentant plusieurs valeurs de service dans l'une des fenêtres examinées est exclue du classement jusqu'à revue du périmètre. Cette prudence n'affirme pas que ces observations sont erronées : des trains internationaux peuvent desservir des gares françaises. Aucune correspondance de noms de gare n'est inventée.

Les observations exclues restent consultables comme informations de qualité, avec leurs motifs. Les exclusions des retards importants ou des causes ne retirent pas automatiquement une observation dont les effectifs centraux sont valides.

## Hypothèses de pilotage

- Signal de détérioration : hausse d'au moins **2 points** du taux de retard calculé entre périodes comparables. Une variation intermédiaire sera libellée « variation inférieure au seuil du projet », sans affirmer une stabilité statistique.
- Signal d'amélioration : baisse d'au moins 2 points.
- Cible pédagogique de régularité calculée : **90 %**, sans valeur d'engagement SNCF.
- Sous-performance persistante : régularité sous cette cible pendant au moins 4 des 6 mois éligibles du semestre courant.
- Dégradation persistante : hausse mensuelle d'au moins 2 points face au même mois de l'année précédente pendant au moins 4 des 6 paires de mois éligibles.

À J06, tester les seuils de variation 1/2/3 points, de volume 15/30/60 et les cibles 85/90/95 %. Les comparer ne donne pas le droit de retenir après coup celui qui produit le récit souhaité. Aucun classement de performance n'est produit à J01.

## Architecture et lieux d'exécution

J01 : API → Python exécuté sur le PC → export et manifeste hors OneDrive → contrôles et synthèses dans le dossier projet. Python 3.13.15 et sa bibliothèque standard suffisent à cet audit ; aucune dépendance supplémentaire installée.

BigQuery demeure l'entrepôt confirmé pour les jalons suivants : versions brutes, audit et tables analytiques, calculs SQL exécutés dans le cloud. Il n'est pas nécessaire de créer cet environnement pour vérifier les données. dbt pilotera ensuite les transformations et Power BI utilisera une copie Import. La configuration cloud, le budget et le verrouillage des dépendances appartiennent à J02.

Un examen manuel seul ne serait pas reproductible sur toutes les observations. Un notebook aurait été possible ; le script et les rapports séparés rendent la relance et la reprise plus simples. PostgreSQL ne fait pas partie de la V1. Google Cloud Storage n'est pas requis.

## Exclusions et succès attendu

Pas de taux national reconstruit par somme des liaisons, de nombre de voyageurs touchés, de prédiction, de NLP, de météo, ni de démonstration causale. Les causes restent des profils publiés, sans volumes reconstitués ni agrégation temporelle/interliaisons.

J01 réussit si les questions mesurables, les populations, les exclusions et les preuves sont écrites et rejouables. La faisabilité est confirmée **avec réserves explicites** : les taux fondés sur les circulations déduites sont des conventions analytiques, et les indicateurs de retards importants ont des restrictions de qualité. Voir [le contrat](data_contract.md), [les KPI](kpi_dictionary.md) et [l'audit](../reports/source_audit.md).
