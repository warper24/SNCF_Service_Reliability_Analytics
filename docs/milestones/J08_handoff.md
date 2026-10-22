# J08 — Rapport Power BI et parcours de décision

**État : terminé le 22 octobre 2026, avec limites explicites.**

Implémentation autorisée le **22 octobre 2026**, après présentation détaillée en
lecture seule : « ok tu as mon accord pour l'implémentation, go ». Le porteur a
ensuite demandé de reprendre au point atteint ; cette reprise conserve le même
jalon et le même périmètre. Aucun travail J09 n'est engagé.

Point de départ : dépôt propre, commit réel `10b1808`, branche
`codex/j07-powerbi`. Les 38 empreintes de livraison J07 concordaient. Branche de
réalisation : `codex/j08-dashboard`. Le PBIX historique et les fichiers de
récupération existants sont préservés.

## Objectif et approche acceptée

Permettre à une équipe fictive de pilotage qualité de passer d'une vue des
signaux à une liaison prioritaire, puis à une investigation justifiée. La
présentation acceptée couvrait quatre pages métier, deux listes distinctes,
navigation et drillthrough, filtres explicites, mesures de présentation limitées,
qualification Desktop, captures, PDF, synthèse, documentation et publication.

Les définitions sont travaillées hors OneDrive. Le modèle J07 et ses gardes
restent la base ; SQL/dbt conserve les règles métier dans BigQuery. Power Query
importe, DAX évalue les mesures sous filtre, PBIR décrit les visuels et leurs
interactions. Le rapport utilise une copie Import, sans requête BigQuery à chaque
clic. Seules les définitions contrôlées reviennent dans Git.

## Livrables et responsabilités

| Fichier ou ensemble | Fonction et utilisateur |
|---|---|
| `powerbi/SNCF_Reliability.pbip`, dossiers `.Report` et `.SemanticModel` | Projet Desktop, quatre pages métier et trois contrôles J07 conservés mais masqués ; définitions examinables par le reviewer |
| `powerbi/theme.json`, thème enregistré dans `.Report/StaticResources/` | Configuration de couleurs et typographie utilisée par Desktop |
| `powerbi/screenshots/` | Quatre rendus publics issus du PDF natif, sans interface de compte |
| `reports/dashboard.pdf` | Lecture autonome des quatre pages, sans connexion ou licence |
| `reports/executive_summary.md` | Synthèse des constats et investigations, reliée aux preuves J06 |
| `docs/dashboard_guide.md` | Pages, filtres, interactions, définitions, parcours, reproduction et limites |
| `docs/measure_catalog.md`, `docs/powerbi_model.md` | Documentation des 17 mesures de présentation, de la colonne de libellé et des gardes conservées |
| `scripts/build_powerbi_dashboard.py` | Générateur des pages/configuration et compléments DAX dans une copie externe ; ne reconstruit pas les tables métier |
| `scripts/validate_dashboard.py` | Validation de la structure, des fenêtres, effectifs, séries, gardes, provenance et invariance des expressions J07 |
| `scripts/validate_powerbi.py` | Réconciliation J07 réutilisée avec l'option explicite `--include-dashboard` |
| `reports/dashboard_evidence/` | Copies locales ignorées des résultats et revues ; originaux d'exécution externes |
| `reports/publication_evidence/dashboard_evidence/` | Copies publiques anonymisées, reliées au manifeste global |
| `.gitignore`, `scripts/prepare_publication.py`, `PLAN.md`, `README.md`, `docs/publication.md` | Exclusions, préparation des preuves et état du projet |

Le code produit les définitions et contrôles ; le thème configure la présentation.
Les observations résident dans BigQuery et dans le cache Import externe. PDF,
images et preuves sont des résultats générés, identifiés par leurs empreintes.
Les définitions Git n'incluent aucun cache autonome.

## Parcours et décisions justifiées

1. **Vue d'ensemble** : population, éligibilité et signaux ; aucun taux national.
2. **Liaisons prioritaires** : rangs J06 de dégradation et de sous-performance,
   avec taux, écarts, mois, L et N. Rang ≤5 conserve les ex æquo à la frontière.
3. **Diagnostic** : fenêtres fixes, deux courbes mensuelles, six parts de causes,
   statut, éligibilité et piste d'investigation bornée au contexte documenté.
4. **Méthode et qualité** : formules, critères, sensibilité et réserves D01–D07.

Un segment est un filtre visible. Le contexte de filtre détermine les lignes
utilisées par un visuel. Le drillthrough est une navigation vers un détail
filtré ; ici trois dimensions sont transmises et les filtres supplémentaires ne
le sont pas. Le segment de comparaison est synchronisé entre les deux premières
pages. Le mois des causes ne filtre que le profil et son statut.

Les deux listes répondent à des questions différentes : hausse récente ou niveau
durablement faible. Un score unique introduirait des pondérations supplémentaires.
Les barres facilitent la comparaison, les courbes la lecture temporelle. Une carte
géographique ne répondrait pas directement à ces questions. Les causes ne sont
pas forcées dans un empilement à 100 %, car leur couverture n'est pas démontrée.
Les visuels natifs et le format 16:9 limitent les dépendances d'export.

Le thème privilégie des contrastes lisibles et accompagne les couleurs de
libellés. Les textes alternatifs et l'ordre de tabulation sont définis ; les
boutons sont activables au clavier dans Desktop par Ctrl+Entrée. Ces vérifications
ne constituent pas une certification complète d'accessibilité.

BigQuery demeure l'entrepôt commun qualifié. Import évite des appels distants à
l'interaction, au prix d'une copie et d'une actualisation explicite. DirectQuery
n'a pas été ajouté. PBIP permet la revue Git ; le repli PBIX n'a pas été nécessaire.
Le PDF complète l'exploration et permet une lecture sans environnement technique.

## Modèle et données

**12 tables Import, 16 relations simples, 74 mesures explicites** : les 57
expressions J07 sont identiques à celles du commit `10b1808`, et 17 compléments
portent les titres, volumes fixes, statuts, annotations et séries alignées. Une
colonne calculée fournit deux libellés français de comparaison. Identifiants,
bornes, populations et rangs SQL restent inchangés ; aucune relation supplémentaire.

Les courbes réévaluent les mesures J07 sur chaque mois complet des deux fenêtres.
Elles n'utilisent pas une moyenne de taux mensuels. Les annotations R01–R06
reprennent les recommandations J06 ; elles ne sont disponibles que pour la
version, le semestre et la liaison documentés. Les codes de statut des causes
restent SQL ; leur présentation est traduite en français.

Source inchangée : archive `20261007T130103249967Z_bce4ef24`, version
`e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6`,
12 907 observations, janvier 2018 à septembre 2026. Fenêtres : janvier–juin
2026/2025 et année 2025/2024. La lecture des métadonnées Import reste celle du
21 octobre 2026 à 14:28:01 UTC ; la date de clôture ne la renouvelle pas.

## Contrôles exécutés et sens des preuves

- **1 405 contrôles J08 réussis**, qualification `dashboard_validation_20261022T125019Z` :
  structure et liens des interactions, quatre pages métier et trois contrôles
  masqués, provenance, effectifs et persistance des 232 contextes J06, deux
  synthèses, 18 paires de contextes mensuels, gardes, statut français et identité
  des 57 expressions J07. Les séries mensuelles sont comparées aux effectifs et
  masques du fait BigQuery ; requête plafonnée à 100 MB.
- **6 321 contrôles de réconciliation réussis**, qualification
  `validation_20261022T125247Z` : reprise des scénarios SQL/DAX J07 et audit réel
  des 74 mesures, partitions Import et relations. Le nombre inclut les assertions
  par valeur ; il ne représente pas autant de scénarios indépendants.
- **37 tests Python réussis**, environnement verrouillé J02, 3,728 secondes.
- **Reconstruction des définitions contrôlée avec le parseur officiel TOM** :
  après régénération depuis les fichiers J08, 12 tables, 16 relations et 74
  mesures uniques. Ce contrôle de fichiers ne démontre pas une reconstruction
  de données sur machine neuve.
- **Revue réelle Desktop** : sélection de Paris Lyon → Grenoble puis Strasbourg
  → Nantes, transmission des trois dimensions, retour, navigation au clavier,
  mois juin→mai avec taux fixes inchangés, effacement du mois avec causes
  indisponibles, sélection annuelle synchronisée et absence de seconde liste.
- **Revue PDF et captures** : export natif Desktop ; contrôle des quatre pages,
  des cinq lignes de chaque liste, des six catégories de causes, des unités,
  périodes, réserves et fraîcheur. Les fichiers de livraison et leurs empreintes
  figurent dans la revue et le manifeste de livraison.

Desktop : **2.159.883.0** ; TOM/ADOMD **19.118.3** hors Git ; compatibilité
tabulaire **1606**. Les captures d'interface avec le compte local restent
externes ; seuls leurs noms, observations et empreintes sont publiés. Les copies
publiques des journaux remplacent le nom de profil Windows, sans changer les
valeurs métier. La preuve Import 1→2 J07 n'a pas été rejouée pour publication.

Un échec numérique empêche la qualification des mesures ; un filtre mal transmis
invalide le parcours même si le SQL est correct ; un export tronqué ou contaminé
par l'interface n'est pas livré. La revue Desktop/PDF est distincte des assertions
automatiques. Les résultats d'essais intermédiaires restent conservés.

## Incidents et corrections

- Le premier test Python utilisait l'interpréteur global, sans `PyYAML` :
  24 erreurs d'environnement. Relance avec le Python J02 verrouillé : 37 réussites ;
  aucune dépendance installée pour contourner l'erreur.
- Le contrôle ajouté pour comparer les expressions J07 supposait du DAX sur la
  ligne suivante ; Desktop sérialise aussi des expressions en ligne. Le test a
  signalé zéro expression retrouvée et a été corrigé pour les deux formes. La
  tentative échouée est conservée ; les 57 expressions concordent ensuite.
- Les tableaux trop courts et marges de boutons tronquaient la lecture. Les
  encarts textuels sont devenus des textes dynamiques natifs et les listes ont
  été agrandies. Les états exportés ne nécessitent pas de défilement pour les
  observations présentées.
- Le premier PDF incluait le bandeau de récupération automatique Desktop. Il
  est écarté de la livraison et conservé localement ; les récupérations ont été
  gardées pour affichage ultérieur, sans suppression.
- Une seconde instance de brouillon conservait l'ancien libellé anglais des
  causes. Elle a été fermée sans écraser les définitions qualifiées. Les preuves
  identifient le moteur validé. Le cache des visuels conservait aussi un statut
  anglais malgré la mesure française déjà évaluée dans DAX : Optimiser →
  Actualiser les visuels, puis enregistrement et nouvel export. Aucune nouvelle
  lecture de BigQuery ni date de fraîcheur artificielle.

- Un export conservait le diagnostic à une échelle réduite malgré un contenu
  textuel correct. Recalcul des visuels à 100 %, enregistrement et nouvel export
  natif : les quatre pages finales ont été inspectées à pleine page. La tentative
  rejetée et son empreinte sont conservées. Le projet s’ouvre sur la vue d’ensemble.

Ces corrections restent dans le périmètre accepté. Aucun changement de source,
de méthode de classement ou d'architecture n'a été engagé.

## Reproduire et transmettre

Les commandes et précautions détaillées sont dans [le guide](../dashboard_guide.md).
Le générateur réinitialise les pages J08 aux états de référence dans la copie
externe ; conserver les changements personnels avant de l'utiliser.

```powershell
python scripts/build_powerbi_dashboard.py --work-directory <copie_externe>
# Ouvrir dans Desktop, vérifier le modèle et relever son port local réel.
python scripts/validate_dashboard.py --work-directory <copie_externe> --server localhost:<port>
python scripts/validate_powerbi.py --project sncf-reliability-analytics `
  --work-directory <copie_externe> --server localhost:<port> --include-dashboard
python -m unittest discover -s tests -v
python scripts/prepare_publication.py
python scripts/prepare_publication.py --check
```

L'exécution utilise le Python J02, les bibliothèques Microsoft externes et les
identités déjà autorisées ; une nouvelle machine doit configurer son accès.
Ne pas ouvrir/actualiser la copie Git dans OneDrive. Un cache ignoré par Git
peut néanmoins être synchronisé par OneDrive.

La clôture prévoit un commit et un envoi sans forçage vers `main` et la branche
de jalon, conformément à l'autorisation du 9 octobre. Le lien du commit de
livraison sera communiqué après sa création et sa vérification distante ; aucun
SHA de livraison n'est inventé dans ce document.

## Limites et prochain jalon

D01–D07 inchangées : N=P−A déduit non certifié, annulations publiées avec limites
de convention, profils de causes sans population démontrée, quarantaine >30/>60
au T1 2025, services et sens distincts, absences préservées. Aucun taux national,
effectif de cause dérivé, causalité, effet voyageurs, coût ou gain.

Les scénarios de sensibilité sont une synthèse J06 figée, pas un simulateur
interactif. Le PDF est un état identifié et ses boutons ne sont pas interactifs.
La copie Import n'a pas été actualisée vers une nouvelle version source. Pas de
Power BI Service, refresh planifié, RLS, essai complet au lecteur d'écran,
machine neuve ni orchestration atomique multi-table. Les schémas JSON publics
ne remplacent pas la validation réelle Desktop et le parseur TOM.

J09 recevra les définitions, validateurs et livrables J08 pour assembler
l'exécution et les scénarios de reprise prévus. Il devra distinguer actualisation
de l'entrepôt, actualisation Import et renouvellement des captures/synthèses.
J10 reste la livraison finale du portfolio.

## Bilan pédagogique

Un rapport correct associe un calcul qualifié à son contexte visible. Le modèle
ne suffit pas : une interaction ou un filtre implicite peut rendre une lecture
trompeuse. Les preuves combinent assertions automatisées et parcours réels.
Une sortie statique demande sa propre revue et ne prouve pas l'interactivité.

Exemples : 10 %→13 % vaut +3 points, ou +30 % relativement. Une liaison peut
s'améliorer tout en restant sous une cible. Un profil matériel à 60 % ne permet
pas de calculer un nombre de trains par cause. Une liaison exclue à N≥60 n'est
pas devenue plus fiable. L/N n'a de sens qu'avec sa population et sa couverture.

Questions d'entretien, sans examen imposé : pourquoi deux listes ? Pourquoi ne
pas déplacer les fenêtres avec le calendrier libre ? Que transmet le drillthrough ?
Pourquoi le mois des causes ne doit-il pas modifier les taux fixes ? Que prouve
la concordance SQL/DAX ? Comment détecter qu'un PDF ne correspond pas au dernier
rapport ouvert ? Pourquoi un succès technique ne certifie-t-il pas D01 ?

Extensions possibles : page mobile (effort modéré), sensibilité interactive
(import et qualification supplémentaires, effort moyen), accessibilité complète
(protocole et essais dédiés), Service/actualisation planifiée (identités et
exploitation à cadrer). Aucune n'est ajoutée au jalon.
