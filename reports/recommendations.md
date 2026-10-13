# Investigations proposées — J06

Ces recommandations s'adressent à une équipe **fictive** de pilotage qualité.
Elles proposent des vérifications, pas des réparations démontrées ni des gains
réalisés. Aucun interlocuteur n'a été contacté.

Référence de tous les constats : version
`e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6`, extraction
du 7 octobre 2026, qualification J06 `20261013T102259Z_d1ed8f73`.
Fenêtre principale janvier–juin 2026/2025 ; National, sens distincts, scénario
N≥30 / 2 points / cible fictive 90 %. Les taux reposent sur N=P−A non certifié.
Les identifiants F renvoient aux [constats, requêtes et preuves](findings.md).

| Priorité d'investigation | Constat établi | Hypothèse à vérifier | Investigation proposée | Interlocuteur métier pressenti | Indicateurs de suivi |
|---|---|---|---|---|---|
| R01 — Paris Lyon → Grenoble, dégradation robuste | F02/F04/F05 : +9,77 points, 5/6 mois en hausse ; +112 retards malgré N en baisse ; première liste dans 27/27 scénarios | Plusieurs mécanismes d'exploitation pourraient contribuer ; le profil de juin est réparti entre catégories | Examiner les mois concernés et demander des données datées de circulation/incidents ; rapprocher gares, matériel et infrastructure sans leur attribuer a priori la hausse | Responsable qualité de la liaison, exploitation et équipes concernées selon les incidents retrouvés | L/N et A/P séparés, écart face au même mois N−1, mois éligibles et mois avec hausse ≥2 points |
| R02 — Paris Montparnasse → Nantes, hausse persistante et volume visible | F02/F04 : +9,21 points, 6/6 mois, L de 339 à 636 ; effet volume −16,91 et effet taux +313,91 | Des contraintes répétées de préparation ou de rotation pourraient intervenir ; hypothèse suggérée comme piste, non démontrée par la part « gestion en gare » de juin (39,58 %) | Revoir les séquences de préparation et de rotation sur des dates documentées, confronter aux autres catégories et aux annulations ; vérifier la population couverte par les causes | Pilotage exploitation, gestion en gare, gestion du matériel | Taux mensuel L/N, annulation A/P, persistance ; profils mensuels sans moyenne ni effectifs reconstitués |
| R03 — Paris Nord → Douai et sens retour, deux diagnostics séparés | F02/F03 : aller +9,11 points et 6/6 mois en hausse ; retour 27,60 % de retards et 6/6 mois sous cible ; A/P courant 3,40 % à l'aller et 5,19 % au retour | Des facteurs communs ou distincts selon le sens pourraient expliquer ces constats | Examiner chaque sens séparément, puis comparer les dates et périmètres avant toute hypothèse commune ; intégrer les annulations publiées | Responsable qualité et exploitation du périmètre concerné | Deux séries distinctes L/N, A/P, volumes N et couverture ; aucun total de trains aller+retour |
| R04 — Strasbourg ↔ Nantes, signal fort dépendant de l'éligibilité | F02/F05 : +12,96 et +9,55 points, respectivement 63/326 et 66/328 ; les deux sens sortent à N≥60 | Le signal peut être substantiel mais sensible à une petite population mensuelle ; matériel à 60 % dans le profil Strasbourg → Nantes de juin, sans effectif de référence connu | Vérifier les effectifs et l'offre publiés, examiner les six paires mensuelles et demander les incidents associés ; maintenir le scénario de référence et afficher la sensibilité | Analyste qualité de données, responsable de liaison, matériel si les faits opérationnels le justifient | Volumes mensuels, taux et couverture, statut d'éligibilité à 15/30/60 ; ne pas traiter la sortie du classement comme une amélioration |
| R05 — Sous-performance persistante, commencer par Mâcon Loché → Paris Lyon | F03/F05 : 30,98 % de retards et 6/6 mois sous cible ; avec Lyon → Marne la Vallée, Chambéry → Paris Lyon, Douai → Paris Nord, Arras → Paris Nord, les cinq restent prioritaires dans 27/27 scénarios | Une difficulté récurrente mérite investigation même lorsque la hausse est moins forte que sur d'autres liaisons | Constituer une fiche par liaison et examiner la récurrence des situations ; pour Mâcon, confronter les incidents au profil de juin (matériel 41,38 %, infrastructure 24,14 %) sans extrapoler au semestre | Pilotage qualité, exploitation ; maintenance ou infrastructure après examen des incidents | Régularité calculée mensuelle, nombre de mois sous cible explicite, L et N ; indicateurs par liaison, pas de profil de causes moyen |
| R06 — Revue de qualité préalable pour les candidats exclus | F01/F05 : 14 exclusions au semestre ; 106 éligibles à N≥15 contre 102 à N≥30 ; changements de service/absences également visibles | Certaines exclusions peuvent refléter une faible desserte ou une rupture de libellé/périmètre ; aucune de ces explications n'est établie | Documenter les mois absents et faibles volumes, rechercher un référentiel ou une confirmation métier pour les changements de service ; ne réintégrer qu'avec une décision tracée | Référent données et connaissance de l'offre | Nombre de liaisons éligibles par fenêtre/scénario, couverture valide par KPI, motifs d'exclusion non additionnés |

## Comment utiliser ces recommandations

R01–R03 combinent des signaux robustes aux hypothèses étudiées et des éléments de
diagnostic explicables. R04 conserve un signal fort sous la convention principale,
avec son incertitude de sélection visible. R05 traite le niveau durablement faible,
qui répond à une autre question que la dégradation récente. R06 protège la qualité
des décisions. Cette organisation ne prétend pas représenter une allocation
optimale de ressources : aucun coût, capacité d'équipe ou bénéfice n'est connu.

Le suivi conservera les mêmes définitions et des mois calendaires comparables.
La disponibilité de nouveaux mois n'autorise pas à déplacer discrètement la
fenêtre de référence. La cible de 90 % est celle du portfolio, sans engagement SNCF.
Une amélioration ultérieure ne prouverait pas à elle seule l'efficacité d'une
action : il faudrait un dispositif d'évaluation et des données adaptés.

Avant d'utiliser quantitativement une cause, obtenir sa population de référence
et sa couverture. Avant de conclure à une responsabilité, obtenir les événements
opérationnels correspondants. Aucune conversion en voyageurs, incidents, coûts,
économies ou retards évitables n'est effectuée.

Données : **SNCF Voyageurs**, [Régularité mensuelle TGV par liaisons](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/),
extraction du 7 octobre 2026, sous [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
