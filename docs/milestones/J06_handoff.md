# J06 — Diagnostic SQL et priorisation opérationnelle

**État : terminé avec limites explicites le 13 octobre 2026.** Diagnostic SQL,
deux listes de priorités, sensibilité, constats et recommandations qualifiés.
36 contrôles J06 réussis ; 94 tests amont réussis avec quatre avertissements
conservés ; 37 tests Python réussis. Aucun travail J07 engagé.

## Présentation et approche acceptée

La préparation a lu PLAN, AGENTS, bilan J05, charte, contrat, dictionnaire des KPI,
modèles, collecteurs et preuves. Le dépôt était propre et isolé ; les 57 empreintes
du code J05, les 16 preuves de son exécution et les 39 copies publiques concordaient.
La présentation a couvert objectif, définitions, exemple chiffré, fichiers,
circulation des données, deux listes sans score, sensibilité préspécifiée,
validation, alternatives, limites, extensions et compétences d'entretien.
Aucune modification ni requête cloud avant l'accord.

Accord : « Oui, tu as mon accord pour exécuter l'implémentation du jalon 06. »
Branche `codex/j06-diagnostic`, depuis le commit réel J05 `2f94df2`.
La [méthode](../prioritization_method.md) a été écrite avant le premier classement.
J06 reste borné au diagnostic ; modèle et rapport Power BI à J07/J08.

Le PC pilote, BigQuery calcule, SQL/dbt porte le métier, Python collecte.
Réutilisation de la source J03 figée et des tables qualifiées J05 ; aucun score,
aucune nouvelle source, aucun déplacement opportuniste des fenêtres.

## Résultats et sens métier

Au semestre janvier–juin 2026/2025, 102/116 liaisons National sont éligibles :
91 dégradations ≥2 points, une amélioration et dix variations sous le seuil.
69 liaisons ont au moins quatre paires mensuelles en hausse ≥2 points ; 94 ont
une régularité calculée sous la cible fictive de 90 % pendant au moins quatre mois.
Ces populations peuvent se recouvrir. Aucun résultat n'est un taux national.

Dégradation : Strasbourg → Nantes, Paris Lyon → Grenoble, Nantes → Strasbourg,
Paris Montparnasse → Nantes, Paris Nord → Douai. Trois restent dans les cinq
premières positions dans les 27 scénarios : Grenoble, Paris Montparnasse → Nantes
et Paris Nord → Douai. Les deux sens Strasbourg/Nantes sortent à N≥60 chaque mois.
Le volume faible est visible, sans déplacer après coup la référence N≥30.

Sous-performance persistante : Mâcon Loché → Paris Lyon, Lyon Part Dieu → Marne
la Vallée, Chambéry Challes les Eaux → Paris Lyon, Douai → Paris Nord, Arras →
Paris Nord. Toutes sont sous la cible pendant 6/6 mois et restent dans les cinq
premières positions pour les 27 scénarios. La cible fait néanmoins varier le
nombre de liaisons sous-performantes de 51 à 102 (85 à 95 %, autres paramètres fixés).

À l'année 2025/2024 : 88/116 éligibles, 25 dégradations, sept améliorations,
56 variations sous seuil ; Annecy → Paris Lyon première (+8,31 points).
La persistance annuelle est indisponible. Les 88 liaisons sont communes aux
deux fenêtres, dont 22 franchissent le signal de dégradation dans les deux.

Paris Lyon → Grenoble compte 112 retards supplémentaires malgré une baisse de N :
effet volume −10,47 et effet taux +122,47. Il s'agit d'une identité comptable,
pas de 122 retards évitables ni d'une causalité. Le fait que des résultats
diffèrent selon la fenêtre ou la cible fait partie du diagnostic.

Les [constats F01–F07](../../reports/findings.md) portent périodes, unités,
version, requête et preuve. Les [recommandations R01–R06](../../reports/recommendations.md)
associent constat, hypothèse, investigation, interlocuteur pressenti et suivi.
Aucun contact métier n'a été envoyé ; aucune réparation ou économie n'est promise.

## Livrables et circulation des données

Les SQL et configurations sont écrits dans le dépôt ; dbt les compile sur le PC,
BigQuery exécute les calculs EU sur les tables J05 existantes. Python vérifie les
entrées, pilote et collecte. Aucun calcul métier de production n'est déplacé
en Python. Les vérifications de résultats à partir des CSV et du brut sont des
contrôles d'audit distincts. Les tables J05 sont restées inchangées.

| Fichier | Producteur, contenu et utilisateur |
|---|---|
| `analyses/sql/route_degradation.sql` | Développeur → BigQuery ; tous les candidats, ratios, variations, rangs et exclusions → analyste |
| `persistent_underperformance.sql` dans le même dossier | Niveau et persistance, y compris amélioration éventuelle → deuxième liste |
| `volume_rate_decomposition.sql` | Effets volume/taux et résidu → justification du diagnostic |
| `cause_profiles.sql` | Grille des 12 mois et six parts par liaison sélectionnée, provenance, statuts, commentaires → investigation |
| `priority_sensitivity.sql` | 27 scénarios par fenêtre, rangs et fréquences de présence → robustesse |
| `diagnostic_summary.sql` | Synthèses par scénario, en nombres de liaisons ; indisponibilité annuelle conservée |
| `period_sensitivity.sql` | Intersection des populations, rangs opérationnels et rangs comparables → lecture des périodes |
| `diagnostic_fixtures.sql` | 26 contrôles synthétiques des frontières, absences, pondération, rangs et décomposition |
| `diagnostic_validation.sql` | Dix contrôles réels, réconciliation J05, grains, scénarios, rangs et invariances |
| `dbt/macros/j06_diagnostic.sql` | Grille mensuelle, scénarios préspécifiés, expressions SQL communes ; mêmes règles utilisées par diagnostics et fixtures |
| `dbt/dbt_project.yml` | Version de projet 0.6.0 et raccordement du dossier d'analyses ; variables J05 inchangées |
| `scripts/validate_diagnostic.py` | Collecteur, garde-fous, dry runs, exécution et preuves ; réutilisation amont contrôlée facultative |
| `docs/prioritization_method.md` | Méthode écrite avant classement, définitions, alternatives et limites → analyste puis J07 |
| `reports/findings.md`, `reports/recommendations.md` | Constats F01–F07 et investigations R01–R06 → lecteur métier/recruteur |
| `.gitignore`, `scripts/prepare_publication.py` | Originaux J06 ignorés, copies publiques anonymisées avec manifeste |
| `docs/setup.md` | Reproduction et distinction exécution/réutilisation des tests |
| `PLAN.md`, `README.md`, `docs/publication.md`, ce bilan | État réel, accès aux résultats, transmission et publication |

Le collecteur génère neuf CSV : 26 contrôles synthétiques, dix contrôles réels,
deux listes complètes de 232 candidats/comparaisons chacune, 190 décompositions,
720 parts mensuelles de causes, 6 264 lignes de sensibilité, 54 synthèses et
116 comparaisons de populations. Ces volumes décrivent cette exécution ; aucune
extraction future ne doit être tenue de reproduire les effectifs de la source.

SQL compilés, manifeste dbt, résultats, journaux et tentatives sont conservés
sous `SNCF_DATA_DIR/diagnostic_runs/<run_id>`, hors OneDrive. Les preuves sélectionnées
sont dans `reports/diagnostic_evidence/` (ignoré par Git). Les copies publiques sont
dans [publication_evidence/diagnostic_evidence](../../reports/publication_evidence/diagnostic_evidence/).
Elles ne sont pas un export complet de la source ou de l'entrepôt. Les profils et
caches restent privés ; `.gitignore` ne désactive pas OneDrive.

## Définitions et décisions justifiées

Un taux est un rapport à une population ; un volume est un effectif. Le niveau
décrit une période, l'évolution la compare à une référence, la persistance compte
les mois répondant à une règle. Une saisonnalité est une variation liée au
calendrier : comparer les mêmes mois limite cette confusion sans neutraliser
tous les autres changements. La sensibilité étudie les effets des hypothèses.

Exemple fictif : N0=1000,L0=100,N1=1200,L1=156 donne 10→13 %, soit +3 points
et +30 % relativement ; +56 retards = +20 volume +36 taux. L'interaction est
attribuée à l'effet taux par convention. Une décomposition symétrique serait
possible ; le repère du plan a été conservé. Les contributions peuvent être
fractionnaires et ne représentent ni des incidents ni un gain évitable.

Les ratios sont calculés par sommes compatibles : 10/100 puis 5/10 donnent
15/110≈13,64 %, pas la moyenne 30 %. Le second mois serait sous le minimum du
classement principal. Les mois absents et les NULL ne deviennent jamais zéro.
Les seuils sont comparés avant arrondi ; une baisse de régularité n'inclut pas
automatiquement les annulations, dont le ratio possède un dénominateur distinct.

Deux listes évitent une pondération arbitraire entre évolution et niveau.
RANK conserve les ex æquo ; leur nombre peut dépasser cinq dans les premières
positions. La persistance départage les catégories avant variation, pas le nombre
exact de mois dans la liste dégradation ; la liste sous-performance utilise ce
nombre. Les libellés stabilisent seulement l'ordre de présentation.

Les 27 scénarios croisent volumes 15/30/60, variations 1/2/3 et cibles 85/90/95.
Les redondances sont explicites : la cible n'affecte pas la dégradation et le
seuil de variation n'affecte pas la sous-performance. Une fréquence sur la grille
n'est pas une probabilité. La référence 30/2/90 reste inchangée.

Les profils de causes restent liaison/service/mois, six parts sans effectif
dérivé. La sélection est l'union des deux listes avant examen des causes.
Les illustrations utilisent juin 2026, dernier mois de la fenêtre, avec accès
aux douze mois. Une cause dominante ne devient pas la cause de la dégradation.

BigQuery reste l'entrepôt confirmé ; les calculs SQL utilisent les mêmes faits
que le futur rapport. Une implémentation pandas aurait dupliqué le contrat ; un
score unique aurait ajouté des pondérations ; une fenêtre glissante aurait
changé le comparateur. Aucune de ces alternatives n'est ajoutée à J06.

## Ajustements et incidents

1. Premier lancement interrompu pendant l'import BigQuery par une erreur
   `pandas.core`, avant création de tentative. Imports ensuite réussis ; versions
   installées conformes au verrou, aucun paquet installé ni modifié. Cause racine
   non établie ; incident console documenté, pas présenté comme diagnostic métier.
2. Tentative `20261013T101226Z_4e9ddc7c` : tests amont réussis et 26 contrôles
   synthétiques réussis dans BigQuery, mais collecte échouée : le schéma du job
   était absent. Utilisation du schéma du résultat retourné, sans changer le SQL.
3. Tentative `20261013T101522Z_9d338763` : ambiguïté SQL entre une relation et
   une colonne nommées `expected_rank`. Qualification explicite de la colonne.
   Des dry runs de toutes les analyses ont été ajoutés avant les tests amont
   pour détecter syntaxe/type/estimation sans calculer les résultats métier.
4. Avant le premier classement, précision de la comparaison entre fenêtres :
   les rangs sur la population commune utilisent variation puis volume sur les
   deux fenêtres, puisque la persistance annuelle n'est pas définie. Les rangs
   opérationnels d'origine restent séparés.
5. Revue de la première qualification réussie : COUNTIF de booléens NULL donnait
   zéro dans les synthèses annuelles de persistance. Correction en NULL explicite.
   Les faits et classements n'ont pas changé. Ajout des fréquences de présence
   et tailles de populations communes pour faciliter une lecture traçable.

Ces ajustements ne modifient ni les fenêtres, ni les seuils, ni les priorités
après observation. Les deux tentatives échouées et leurs empreintes restent
conservées. La qualification finale suit ces corrections.

À la publication, le journal de compilation Windows était encodé en cp1252.
La préparation convertit explicitement sa copie publique en UTF-8 et le déclare
dans le manifeste ; les octets originaux et leur empreinte restent intacts.
Aucun test n'a été relancé pour cette conversion.

## Contrôles exécutés et preuves

Qualification finale : **`20261013T102259Z_d1ed8f73`**. Source et archive ci-dessus,
69 empreintes de code/méthode et 23 fichiers de preuve de l'exécution vérifiés.
Versions : Python et dépendances dans `validation.json` ; dbt Core 1.12.5,
adaptateur BigQuery 1.12.1, client BigQuery 3.45.2. Aucun changement du verrou.

| Critère | Contrôle réellement effectué | Résultat et preuve |
|---|---|---|
| Entrées qualifiées et inchangées | Archive/empreintes, brut BigQuery, schémas, versions, état des objets avant/après | Conforme ; `validation.json` et code amont intact |
| Distinctions évolution/niveau/persistance | Frontières ±2 points, cible stricte 90 %, 3/6 vs 4/6 ; référence égale au mart J05 | Conforme ; `diagnostic_fixtures.csv`, `diagnostic_validation.csv` |
| Volume et taux | Exemple +56=20+36, puis 190 identités réelles à 0,01 près | Conforme ; décomposition CSV et revue export |
| Absences, faibles volumes, périmètre | Cas NULL, N=0, mois absent, seuils 15/30/60 et double service ; exclusions visibles | Conforme ; fixtures et candidats détaillés |
| Classements et sensibilité | Ordre vérifié indépendamment, ex æquo au rang 5, 27 scénarios, éligibilité monotone et invariances | Conforme ; dix contrôles réels et sorties sensibilité |
| Profils mensuels fidèles | Sélection des dix liaisons, 720 parts rapprochées des champs bruts SNCF à 1e−10 point près | Conforme ; `manual_review.json`, profils CSV |
| Synthèses et traçabilité | 54 synthèses rapprochées des 6264 lignes ; année NULL, population commune, unité/période/version de chaque constat | Conforme ; 18 contrôles de revue et rapports F01–F07 |
| Recommandations | Relecture de R01–R06 : constat/hypothèse/investigation/interlocuteur/indicateur | Conforme ; rapport et revue manuelle |

Les 94 tests amont réussissent avec quatre avertissements (425 effectifs,
282 profils, 278 moyennes et 84 périmètres). Ils ont été réellement exécutés
dans `20261013T101816Z_2ce63253`, puis réutilisés après contrôle de leurs empreintes,
du code amont, des versions installées et de l'identité des entrées. Le journal
original est conservé ; la qualification finale n'en invente pas une nouvelle
date d'exécution. Les 36 contrôles J06 sont rejoués, certains servis par le cache
BigQuery sur les mêmes entrées. La réutilisation facultative est documentée.

Les 37 tests Python ont réussi, avec journal conservé. Les 39 preuves historiques
originales sont inchangées. Aucun test cloud n'est renouvelé pour la publication.
Les trois analyses modifiées de la qualification finale ont chacune 10 MiB
d'octets facturables ; les six autres sont servies par cache. Ce constat exclut
les essais antérieurs, le contrôle du brut et les tests amont ; il ne décrit pas
la facture totale. La limite de 100 MB par requête n'est pas un plafond cumulé.

Reproduction : [qualification J06](../setup.md#qualification-j06).
Commande principale : `python scripts/validate_diagnostic.py --execute --project
sncf-reliability-analytics --snapshot <archive_figée>`, avec l'environnement et
le profil privés décrits dans setup. Les paramètres de connexion ne sont pas
des fichiers à publier. La revue doit être renouvelée pour toute nouvelle
qualification ; les empreintes historiques restent celles de leur exécution.

## Limites, exclusions et transmission

D01–D07 inchangées : population déduite non certifiée, annulations de périmètre
historique incertain, causes sans population démontrée, couple >30/>60 indisponible
sur les comparaisons impliquant T1 2025, absence de référentiel stable de gares.
Un test vert valide un calcul selon le contrat, pas la vérité de ces hypothèses.

Pas de taux national, moyenne de causes, effectif par cause, addition des seuils
imbriqués, voyageurs, incidents, coûts, gains ou causalité. Pas de réconciliation
SQL/DAX ni d'actualisation Power BI. Pas de reconstruction sur machine neuve,
de transaction/restauration multi-table ou de vérification de la facture finale.
La stabilité des objets avant/après n'est pas une garantie transactionnelle.

J07 recevra les faits/marts J05, les résultats de référence J06 et leurs
paramètres. Il devra afficher dénominateurs, couverture, réserves, sens et service,
distinguer les deux listes et conserver les indisponibilités. Toute actualisation
de données exige une version identifiable ; ne pas déplacer les fenêtres sans
décision. Les résultats Power BI devront être réconciliés avec SQL.

Publication ordinaire autorisée selon AGENTS : copies publiques préparées après
revue, fichiers indexés contrôlés, commit puis envoi sans forçage, vérification
du SHA distant et lien transmis dans la conversation. Voir le [journal](../publication.md)
et l'[historique de la branche J06](https://github.com/warper24/SNCF_Service_Reliability_Analytics/commits/codex/j06-diagnostic).
Le commit `2f94df2` mentionné plus haut est le point de départ réel J05, pas un
identifiant anticipé de livraison J06. J10 reste la release finale.

## Bilan pédagogique

Compétences démontrées : SQL analytique, grilles calendaires, pondération,
classification et RANK, tests de frontières, analyse de sensibilité, contrôle
des populations, traçabilité et formulation de recommandations mesurables.

Questions d'entretien facultatives :

- Pourquoi davantage de retards avec moins de circulations ? Décomposer N et r.
- Pourquoi deux listes ? Niveau et dégradation répondent à deux décisions distinctes.
- Pourquoi Strasbourg → Nantes quitte la liste à 60 ? Changement d'éligibilité,
  pas amélioration ; ne pas cacher le volume mensuel.
- Pourquoi une cible modifie-t-elle le nombre de priorités ? C'est une hypothèse
  de pilotage dont la sensibilité doit être visible, pas un engagement SNCF.
- Pourquoi une part de matériel élevée ne prouve-t-elle rien causalement ?
  Population des causes et événements opérationnels manquent.
- Pourquoi NULL dans la synthèse annuelle ? Le critère de persistance n'est
  pas défini ; zéro signifierait à tort qu'aucune liaison ne le satisfait.
- Pourquoi conserver les résultats échoués et les tests réutilisés ? Pour
  distinguer tentative, preuve réelle et date de qualification sans réécrire le passé.

Approfondissements hors périmètre : incertitude statistique (hypothèses sur les
dépendances, effort moyen à important), investigation causale (données fines,
effort important), référentiel de gares (clés fiables, effort moyen). Les données
mensuelles ne permettent pas d'ajouter ces conclusions par une simple formule.
