# Fiabilité des liaisons TGV — Synthèse de décision

Le premier semestre 2026 présente une hausse du taux de retard calculé d'au moins
deux points sur **91 des 102 liaisons orientées/service éligibles**, face aux mêmes
mois de 2025. Ce diagnostic permet de prioriser des investigations. Il ne mesure
ni un taux national de régularité, ni l'effet sur les voyageurs.

[Voir le rapport en quatre pages](dashboard.pdf) et [son guide](../docs/dashboard_guide.md).

## Population et portée

Les 116 candidats du service source National donnent 102 comparaisons éligibles :
mois complets dans les deux périodes, effectifs compatibles, au moins 30
circulations déduites par mois et périmètre de service non ambigu. Les 14
exclusions restent documentées. Parmi les 102, une liaison s'améliore d'au moins
deux points et dix restent sous le seuil de variation du projet. Cette dernière
catégorie ne démontre pas une stabilité statistique.

Les taux utilisent N=P−A, circulations déduites des effectifs publiés, **population
non certifiée D01**. Les annulations utilisent leur dénominateur propre P.
Le sens inverse et les services restent distincts. Les sources et calculs de
chaque constat sont dans [les résultats J06](findings.md), F01–F07.

## Deux questions, deux listes

| Question | Premières priorités et justification |
|---|---|
| Où le signal se dégrade-t-il récemment ? | Strasbourg → Nantes : +12,96 points, puis Paris Lyon → Grenoble : +9,77, Nantes → Strasbourg : +9,55, Paris Montparnasse → Nantes : +9,21 et Paris Nord → Douai : +9,11. Les rangs combinent la persistance, puis la hausse et le volume, sans score composite. |
| Où le niveau reste-t-il durablement sous la cible du projet ? | Mâcon Loché → Paris Lyon : 30,98 % de retards ; Lyon Part Dieu → Marne la Vallée : 30,21 % ; Chambéry Challes les Eaux → Paris Lyon : 29,39 % ; Douai → Paris Nord : 27,60 % ; Arras → Paris Nord : 25,76 %. Chacune est sous la cible fictive de régularité de 90 % pendant six mois sur six. |

Les listes peuvent se recouvrir et leurs effectifs ne s'additionnent pas.
La première liaison classée en dégradation n'est pas celle qui porte le plus de
retards. À l'inverse, Lille → Lyon Part Dieu s'améliore de 2,95 points au semestre.

## Par où commencer l'investigation ?

**Paris Lyon → Grenoble constitue un cas de départ documenté.** Le taux passe de
12,32 % à 22,09 %, avec cinq mois sur six en hausse d'au moins deux points.
L passe de 165 à 277 alors que N diminue de 1 339 à 1 254. La décomposition
comptable attribue −10,47 à l'effet volume et +122,47 à l'effet taux, pour +112
retards comptés sur cette liaison. Ce calcul ne démontre ni causalité ni retards
évitables. La liaison reste dans les cinq premières positions de dégradation
dans les 27 scénarios semestriels étudiés.

R01 propose de demander les événements datés et de rapprocher exploitation,
gares, matériel et infrastructure selon les faits retrouvés. L'interlocuteur
pressenti est le responsable qualité de la liaison, avec les équipes concernées.
Suivi : L/N et A/P séparés, couverture et nombre de mois en hausse. Le profil de
causes de juin est réparti entre catégories ; il n'attribue pas la hausse à une
responsabilité précise. Aucun interlocuteur n'a été contacté.

Paris Montparnasse → Nantes et Paris Nord → Douai présentent également une
priorité de dégradation robuste aux scénarios testés. Les deux sens Strasbourg/
Nantes gardent un signal fort sous la référence, avec une sensibilité importante
au minimum mensuel : ils deviennent inéligibles à N≥60. Cette sortie ne constitue
pas une amélioration. Les cinq premières sous-performances restent dans les cinq
premières positions dans les 27 scénarios semestriels.

Les investigations complètes R01–R06 distinguent constat, hypothèse,
interlocuteur pressenti et indicateur de suivi dans
[les recommandations](recommendations.md). Elles ne constituent pas une
allocation optimale des ressources : coûts, capacités d'équipe et bénéfices
ne sont pas disponibles.

## Ce qui change avec la période

La comparaison annuelle 2025/2024 possède sa propre population : 88 éligibles,
25 dégradations, sept améliorations et 56 variations sous le seuil. Annecy → Paris
Lyon y est première en dégradation (+8,31 points). La persistance annuelle est
indisponible. Les deux fenêtres se recouvrent ; elles ne constituent pas des
confirmations indépendantes. Les périodes n'ont pas été déplacées après lecture
des résultats.

## Limites et traçabilité

Les causes sont des pourcentages publiés par liaison/service/mois dont la
population de référence n'est pas démontrée : aucun effectif reconstitué,
profil semestriel moyen ou lien causal. >30/>60 au T1 2025 reste en quarantaine.
Les exclusions propres à un indicateur ne suppriment pas les observations brutes.
Zéro, valeur absente et mois absent restent distincts.

Référence commune : extraction du **7 octobre 2026**, archive
`20261007T130103249967Z_bce4ef24`, version
`e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6`.
Elle contient 12 907 observations jusqu'à septembre 2026 ; le diagnostic principal
reste janvier–juin 2026/2025. La copie Import affiche la lecture des métadonnées
du 21 octobre 2026 à 14:28:01 UTC, sans garantie d'atomicité multi-table.

Le rapport expose les calculs J06/J07 et conserve les réserves D01–D07.
Ses contrôles et sa revue sont détaillés dans [le bilan J08](../docs/milestones/J08_handoff.md).
Le PDF et les captures présentent des états identifiés ; ils ne remplacent pas
l'exploration interactive ni les informations opérationnelles à demander.

Données : **SNCF Voyageurs**, [Régularité mensuelle TGV par liaisons](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/),
extraction du 7 octobre 2026, sous [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
Projet de portfolio indépendant de SNCF ; aucun gain opérationnel réalisé n'est revendiqué.
