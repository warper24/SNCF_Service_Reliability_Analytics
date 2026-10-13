# Diagnostic des liaisons TGV — J06

**Au premier semestre 2026, 91 des 102 liaisons National éligibles franchissent
le signal de dégradation de 2 points face au premier semestre 2025.** Trois
liaisons restent dans les cinq premières positions de dégradation pour tous
les scénarios étudiés : Paris Lyon → Grenoble, Paris Montparnasse → Nantes et
Paris Nord → Douai. Strasbourg → Nantes arrive première dans le scénario de
référence, mais son éligibilité dépend du seuil de volume mensuel.

Ce constat porte sur des **liaisons orientées**, sans taux national reconstruit.
Les taux de retard utilisent les circulations **déduites** des effectifs publiés,
dont l'équivalence avec les circulations assurées n'est pas certifiée (D01).

## Référence commune à tous les constats

- Source : SNCF Voyageurs, extraction J03 du 7 octobre 2026,
  archive `20261007T130103249967Z_bce4ef24`.
- Version : `e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6`.
- Qualification finale J06 : `20261013T102259Z_d1ed8f73`, le 13 octobre 2026.
- Population : valeur source National, sens et service séparés ; mois complets,
  effectifs centraux compatibles, un seul service dans les fenêtres, N≥30 par mois.
- Scénario de référence : `n30_d2_t90`. La [méthode](../docs/prioritization_method.md)
  a été arrêtée avant le classement. Les décimales ci-dessous sont arrondies pour
  lecture ; les CSV conservent les valeurs de calcul.
- Fraîcheur : la source figée va jusqu'à septembre 2026 ; le diagnostic principal
  reste volontairement janvier–juin 2026/2025. L'extraction récente ne déplace pas
  les fenêtres décidées à J01.

Chaque identifiant F ci-dessous référence une requête et son résultat public.
La version commune ci-dessus s'applique à tous les tableaux et exemples.

## F01 — Couverture et évolution, selon la fenêtre

| Comparaison | Candidats | Éligibles | Dégradation ≥2 points | Amélioration ≤−2 points | Variation inférieure au seuil |
|---|---:|---:|---:|---:|---:|
| Janvier–juin 2026 / janvier–juin 2025 | 116 | 102 | 91 | 1 | 10 |
| Année 2025 / année 2024 | 116 | 88 | 25 | 7 | 56 |

Unité : nombre de liaisons orientées/service. Au semestre, 69 liaisons présentent
une hausse mensuelle ≥2 points sur au moins quatre paires de mois ; 94 sont sous
la cible fictive de régularité de 90 % pendant au moins quatre mois. Ces deux
dimensions se recouvrent et ne doivent pas être additionnées. La persistance
annuelle est **indisponible**, pas nulle.

Lille → Lyon Part Dieu constitue l'amélioration au semestre : −2,95 points,
pour un taux courant de 15,21 %. Elle n'est pas sous la cible pendant au moins
quatre mois : niveau pondéré sur le semestre et répétition mensuelle répondent
à deux questions différentes. Les variations inférieures au seuil ne prouvent
pas une stabilité statistique.

Les 14 candidats exclus au semestre restent visibles : par exemple Bordeaux
St Jean → Tourcoing pour faible volume, Paris Lyon → Barcelona pour absence
dans le service de référence et ambiguïté de périmètre. Les raisons se recouvrent.
Ni la suppression d'un libellé ni un changement de service ne démontrent une
modification de desserte. Aucune exclusion ne se transforme en taux nul.

Preuves : [requête de synthèse](../analyses/sql/diagnostic_summary.sql),
[synthèse CSV](publication_evidence/diagnostic_evidence/diagnostic_summary.csv),
[requête détaillée](../analyses/sql/route_degradation.sql),
[candidats et exclusions](publication_evidence/diagnostic_evidence/route_degradation.csv).

## F02 — Premières priorités de dégradation récente

Janvier–juin 2026 contre les mêmes mois de 2025, scénario de référence.
Tri : dégradation persistante d'abord, puis variation du taux, puis volume L.

| Rang | Liaison | Taux 2025 | Taux 2026 | Écart en points | Mois en hausse ≥2 points | Retards L / N déduit en 2026 |
|---|---|---:|---:|---:|---:|---:|
| 1 | Strasbourg → Nantes | 6,36 % | 19,33 % | +12,96 | 5/6 | 63 / 326 |
| 2 | Paris Lyon → Grenoble | 12,32 % | 22,09 % | +9,77 | 5/6 | 277 / 1 254 |
| 3 | Nantes → Strasbourg | 10,57 % | 20,12 % | +9,55 | 5/6 | 66 / 328 |
| 4 | Paris Montparnasse → Nantes | 9,45 % | 18,65 % | +9,21 | 6/6 | 636 / 3 410 |
| 5 | Paris Nord → Douai | 14,39 % | 23,50 % | +9,11 | 6/6 | 180 / 766 |

La première liaison n'est pas celle qui compte le plus de retards. Le classement
privilégie la dégradation selon une règle explicite ; le volume reste visible.
Les deux sens Strasbourg/Nantes sont deux observations métier distinctes.
La liste réelle n'a pas d'ex æquo à la frontière ; la règle les conserve et a été testée.

Annulations sur la même période courante, avec leur dénominateur P propre :
2,10 % pour Strasbourg → Nantes ; 0,32 % pour Paris Lyon → Grenoble ; 2,67 %
pour Nantes → Strasbourg ; 2,49 % pour Paris Montparnasse → Nantes ; 3,40 %
pour Paris Nord → Douai. Elles complètent la lecture des retards sans entrer
dans un score ou être assimilées à toutes les déprogrammations.

Preuves : [route_degradation.sql](../analyses/sql/route_degradation.sql),
[résultats](publication_evidence/diagnostic_evidence/route_degradation.csv).

## F03 — Sous-performance persistante : une autre liste

Semestre courant janvier–juin 2026. Toutes les liaisons ci-dessous ont une
régularité calculée <90 % pendant **6 mois sur 6** et franchissent aussi le
signal agrégé de dégradation. Leur ordre dépend du niveau, pas de la seule hausse.

| Rang | Liaison | Taux de retard courant | Écart 2026/2025 en points | Retards L / N déduit |
|---|---|---:|---:|---:|
| 1 | Mâcon Loché → Paris Lyon | 30,98 % | +3,78 | 426 / 1 375 |
| 2 | Lyon Part Dieu → Marne la Vallée | 30,21 % | +8,33 | 628 / 2 079 |
| 3 | Chambéry Challes les Eaux → Paris Lyon | 29,39 % | +3,92 | 487 / 1 657 |
| 4 | Douai → Paris Nord | 27,60 % | +7,47 | 252 / 913 |
| 5 | Arras → Paris Nord | 25,76 % | +4,06 | 687 / 2 667 |

Ces cinq liaisons restent dans les cinq premières positions de sous-performance
dans les 27 scénarios semestriels. Cela décrit une stabilité aux hypothèses
testées, pas une causalité ni une garantie hors de cette grille. Au seuil de
référence, aucune liaison ne combine amélioration ≥2 points et sous-performance
persistante ; la variante avec une cible de 95 % comporte une telle coexistence.

Preuves : [persistent_underperformance.sql](../analyses/sql/persistent_underperformance.sql),
[résultats](publication_evidence/diagnostic_evidence/persistent_underperformance.csv),
[sensibilité](publication_evidence/diagnostic_evidence/priority_sensitivity.csv).

## F04 — La hausse du nombre de retards ne vient pas ici d'un trafic accru

Même liaison et même service, semestres calendaires complets. Unités : N et L
en circulations comptées sur la liaison ; effets en circulations comptables.

| Liaison | N 2025 → 2026 | L 2025 → 2026 | ΔL | Effet volume | Effet taux |
|---|---:|---:|---:|---:|---:|
| Strasbourg → Nantes | 330 → 326 | 21 → 63 | +42 | −0,25 | +42,25 |
| Paris Lyon → Grenoble | 1 339 → 1 254 | 165 → 277 | +112 | −10,47 | +122,47 |
| Paris Montparnasse → Nantes | 3 589 → 3 410 | 339 → 636 | +297 | −16,91 | +313,91 |

L'identité retenue est ΔL=(N1−N0)r0+N1(r1−r0). Pour ces trois cas, N diminue :
l'effet taux compense la contribution négative du volume et explique comptablement
la hausse de L. La convention n'identifie ni des incidents, ni des retards évitables,
ni un gain à promettre. Les contributions ne sont jamais additionnées entre liaisons.
Les 190 comparaisons éligibles ont été réconciliées à la tolérance de 0,01.

Preuves : [volume_rate_decomposition.sql](../analyses/sql/volume_rate_decomposition.sql),
[résultats](publication_evidence/diagnostic_evidence/volume_rate_decomposition.csv).

## F05 — Ce qui résiste aux hypothèses, ce qui change

Au semestre, en ne changeant qu'un paramètre à la fois :

| Hypothèse | Éligibles | Dégradations | Sous-performances persistantes | Premières positions de dégradation communes avec la référence |
|---|---:|---:|---:|---:|
| Référence : N≥30, variation 2 points, cible 90 % | 102 | 91 | 94 | 5/5 |
| N≥15 | 106 | 92 | 97 | 5/5 |
| N≥60 | 100 | 89 | 92 | 3/5 |
| Variation 1 point | 102 | 98 | 94 | 5/5 |
| Variation 3 points | 102 | 73 | 94 | 5/5 |
| Cible 85 % | 102 | 91 | 51 | 5/5 |
| Cible 95 % | 102 | 91 | 102 | 5/5 |

Sur la grille complète, Paris Lyon → Grenoble, Paris Montparnasse → Nantes et
Paris Nord → Douai restent dans les premières positions de dégradation dans
27/27 scénarios. Strasbourg → Nantes et Nantes → Strasbourg y figurent dans
18/27 : elles sont inéligibles dans les neuf scénarios N≥60. Leur sortie ne
constitue pas une amélioration. À N≥60, Paris Lyon → Mâcon Loché et Paris Nord
→ Arras entrent dans les cinq premières positions.

Le nombre de sous-performances dépend fortement de la cible : 51 à 85 %, 94 à
90 %, 102 à 95 %, malgré une première liste de cinq stable. La cible est une
hypothèse de pilotage, jamais un engagement SNCF. Les scénarios ne sont ni
indépendants ni équiprobables : leur fréquence n'est pas une probabilité de priorité.
La cible ne change pas le classement de dégradation ; le seuil de variation ne
change pas celui de sous-performance. Ces invariances ont été contrôlées.

Preuves : [priority_sensitivity.sql](../analyses/sql/priority_sensitivity.sql),
[6 264 lignes candidat/scénario](publication_evidence/diagnostic_evidence/priority_sensitivity.csv),
[54 synthèses scénario/fenêtre](publication_evidence/diagnostic_evidence/diagnostic_summary.csv).

## F06 — Le choix de la fenêtre change le diagnostic

La comparaison annuelle 2025/2024 place Annecy → Paris Lyon en tête :
14,36 % → 22,67 %, soit +8,31 points. Suivent Perpignan → Paris Lyon
(+4,32), Toulon → Paris Lyon (+4,14), Le Creusot Montceau Montchanin → Paris
Lyon (+4,14 avant distinction aux décimales de calcul) et Montpellier → Paris
Lyon (+4,10). Ces rangs ne constituent pas une persistance annuelle.

Il existe 88 liaisons éligibles communes aux deux fenêtres, 14 uniquement au
semestre et aucune uniquement à l'année. Parmi les 88 communes, 22 franchissent
le signal de dégradation dans les deux comparaisons. Strasbourg → Nantes,
première au semestre, présente −0,64 point à l'année, sous le seuil de variation.

Le fichier de comparaison conserve les rangs opérationnels et calcule aussi
des rangs sur la population commune selon **la même règle** (variation puis
volume), sans persistance. Le semestre 2025 appartient également à l'année 2025 :
les deux fenêtres se recouvrent et ne sont pas des confirmations indépendantes.
Aucune période de remplacement n'a été choisie après lecture des résultats.

Preuves : [period_sensitivity.sql](../analyses/sql/period_sensitivity.sql),
[population commune et rangs](publication_evidence/diagnostic_evidence/period_sensitivity.csv),
[classement annuel](publication_evidence/diagnostic_evidence/route_degradation.csv).

## F07 — Les causes orientent une investigation mensuelle

Les profils des dix liaisons retenues dans l'union des deux listes de référence
au semestre sont conservés pour chacun des six mois courants et des six mois de
référence : 720 parts, avec statuts et provenance. Ce sont des pourcentages
source, pas des parts calculées sur N ou L dans ce projet.

Illustrations sur le dernier mois de la fenêtre, **juin 2026**, en % publiés :

| Liaison | Externes | Infrastructure | Trafic | Matériel | Gestion en gare | Prise en charge voyageurs |
|---|---:|---:|---:|---:|---:|---:|
| Strasbourg → Nantes | 20 | 0 | 0 | 60 | 0 | 20 |
| Paris Lyon → Grenoble | 25 | 20 | 0 | 25 | 30 | 0 |
| Paris Montparnasse → Nantes | 27,12 | 0 | 0 | 22,82 | 39,58 | 10,48 |
| Mâcon Loché → Paris Lyon | 17,24 | 24,14 | 6,90 | 41,38 | 6,90 | 3,45 |

Ces quatre profils sont disponibles sans avertissement de somme. Le tableau
n'est ni un profil semestriel ni une explication de l'écart annuel. Un zéro
publié ne prouve pas l'absence d'incident réel. La part de matériel à 60 % sur
Strasbourg → Nantes ne permet pas de calculer un nombre de trains par cause.
Les profils des autres mois restent accessibles ; aucun mois n'a été choisi
parce qu'il présentait une cause particulièrement élevée.

Preuves : [cause_profiles.sql](../analyses/sql/cause_profiles.sql),
[profils mensuels complets de la sélection](publication_evidence/diagnostic_evidence/cause_profiles.csv).

## Validation et limites de lecture

Les 36 contrôles J06 réussissent (26 cas synthétiques, 10 contrôles sur données).
Les 94 tests amont et quatre avertissements ont été exécutés dans la qualification
J06 `20261013T101816Z_2ce63253`, puis leurs preuves réutilisées pour la qualification
finale après vérification de l'identité des entrées, du code amont et des versions.
Les 37 tests Python existants ont également réussi. La revue des tableaux, des
arrondis, des cas et des limites est conservée avec les preuves.

Les comparaisons >30/>60 restent indisponibles à cause du T1 2025 en quarantaine.
Les moyennes de minutes et >15 ne servent pas à prioriser. Aucune conclusion sur
voyageurs, incidents individuels, coûts, gains ou causalité. Aucun taux national.
Le modèle Power BI et sa réconciliation SQL/DAX restent à J07.

Voir les [recommandations](recommendations.md), la
[validation](publication_evidence/diagnostic_evidence/validation.json) et le
[bilan J06](../docs/milestones/J06_handoff.md).

Données : **SNCF Voyageurs**, [Régularité mensuelle TGV par liaisons](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/),
extraction du 7 octobre 2026, sous [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
Ce diagnostic de portfolio est indépendant de SNCF.
