# Modèle sémantique Power BI — J07

Le modèle donne un sens aux tables, relations et mesures utilisées par un rapport.
BigQuery reste la référence ; le fichier Power BI conserve une **copie Import**.
Les pages de contrôle J07 servent à vérifier les résultats. Le parcours de décision,
les graphiques métier et la mise en forme du portfolio relèvent de J08.

## Architecture et circulation des données

1. Python a extrait et contrôlé le transport de la version source figée à J03.
2. SQL/dbt a construit les faits, dimensions et marts qualifiés à J04–J05.
3. Le diagnostic SQL J06 a arrêté les populations, fenêtres, signaux et rangs.
4. Power Query lit les tables `sncf_dev` et le SELECT du diagnostic J06 dans BigQuery.
   Il paramètre la connexion, vérifie la version des tables portant `version_id`
   et transforme les listes de motifs en texte de présentation. Il ne recalcule
   ni les masques qualité ni les règles d'éligibilité.
5. Le moteur tabulaire charge ces résultats en mémoire/disque local. DAX calcule
   sous les filtres du rapport ; il ne consulte pas BigQuery à chaque clic.
6. Une actualisation relit BigQuery. Les mesures de provenance indiquent version,
   dernier mois métier et horodatage UTC de lecture des métadonnées.

`last_import_utc` est l'heure du SELECT de métadonnées, pas une garantie d'atomicité
multi-table ni l'heure de fin du chargement. La qualification compare aussi les
versions et effectifs réels du moteur. La V1 suppose les tables amont stables
pendant une actualisation ; une orchestration transactionnelle reste hors périmètre.

## Tables et relations

| Table | Grain et rôle | Filtrage entrant |
|---|---|---|
| `dim_date` | Un jour, calendrier complet 2018–2026 ; faits au premier jour du mois | Aucun |
| `dim_route` | Une liaison orientée, avec départ et arrivée distincts | Aucun |
| `dim_service` | Un service ; National et International restent distincts | Aucun |
| `dim_cause` | Une catégorie de cause publiée | Aucun |
| `dim_comparison` | Une fenêtre fixe, extraite des paramètres du mart | Aucun |
| `fct_reliability_monthly` | Mois × liaison × service ; effectifs, masques, anomalies | Date, liaison, service |
| `fct_delay_causes_monthly` | Mois × liaison × service × cause ; pourcentage publié | Date, liaison, service, cause |
| `mart_route_trends` | Mois × liaison × service ; comparaisons mensuelles SQL | Date, liaison, service |
| `mart_route_priorities` | Comparaison × liaison × service ; fenêtres et éligibilité SQL | Comparaison, liaison, service |
| `route_diagnostic` | Même grain ; deux rangs J06, sans score composite | Comparaison, liaison, service |
| `refresh_metadata` | Une ligne de provenance | Aucun |
| `kpi_measures` | Conteneur des mesures explicites ; ancre technique masquée | Aucun |

Les 16 relations sont actives, plusieurs-vers-un, avec propagation simple depuis
la dimension. Aucune relation fait-vers-fait ni relation bidirectionnelle.
`dim_date[date_key]` filtre `month` dans les trois tables mensuelles. Les comparaisons
fixes ont une dimension séparée : un calendrier libre ne doit pas déplacer leurs
fenêtres. Les relations et calendriers automatiques sont désactivés dans le fichier.

Les clés et colonnes numériques des faits sont masquées aux auteurs du rapport.
`summarizeBy: none` et les mesures explicites limitent les sommes/moyennes accidentelles.
Ce sont des garde-fous de conception, pas une sécurité d'accès : un auteur du
modèle peut toujours modifier les définitions. Pas de RLS ajouté sur des données publiques.

Le fichier de culture TMDL contient le vocabulaire et les relations linguistiques
générés par Desktop ; ce volumineux catalogue technique n'est pas un export des
observations SNCF. Les suggestions de synonymes générées ne constituent pas une
interface Q&A métier qualifiée. Les octets et fins de ligne produits par Desktop
sont conservés dans Git pour correspondre au manifeste de livraison.

## Contexte de filtre et populations

Un contexte de filtre est l'ensemble des lignes encore visibles après les choix
de page, de segment ou de ligne de tableau. `CALCULATE` évalue une expression dans
un contexte ajusté ; `KEEPFILTERS` conserve l'intersection avec le masque qualité.
`HASONEVALUE` exige une seule liaison et un seul service. `DIVIDE` renvoie BLANK
si le dénominateur est nul ; BLANK signifie indisponible, pas zéro.

Les mesures mensuelles exigent **tous les jours des mois sélectionnés** dans le
calendrier. Un filtre du 1er au 15 janvier est rejeté, car les faits sont mensuels.
Sélectionner `month_label`, `year` ou un trimestre complet est approprié. Un trimestre
sans observations reste attendu dans la couverture : on ne réduit pas silencieusement
le dénominateur temporel aux seules lignes reçues.

Pour une seule liaison/service, le taux de retard est `ΣL / ΣN`, avec `N=P−A`.
Le numérateur et le dénominateur utilisent exactement les mêmes mois valides.
Un ratio portant sur plusieurs mois nécessite une couverture valide complète.
Exemple pédagogique : 10/100 puis 90/300 donnent 100/400 = 25 %, et non la moyenne
20 % des deux taux. Une sélection de plusieurs liaisons ne produit jamais un taux national.

Les comptes >30 et >60 peuvent montrer la somme des mois utilisables, accompagnée
de `important_count_coverage` ; leurs taux exigent la couverture complète. Les seuils
sont imbriqués et ne s'additionnent pas. Le couple est indisponible au T1 2025.
Les effectifs bruts restent conservés dans l'entrepôt ; aucun chiffre improbable
n'est corrigé dans Power Query ou DAX.

Les causes exigent une liaison, un service, **un mois et une cause**. Le pourcentage
source 0–100 est divisé par 100 uniquement pour l'affichage en pourcentage.
`published_cause_raw_pct` permet d'examiner un profil invalide avec son statut ;
`published_cause_share` n'affiche que les profils utilisables. Aucun effectif de
trains par cause ni moyenne de profils n'est reconstruit.

## Fenêtres fixes et priorités

Les comparaisons sont H1 2026/H1 2025 et année 2025/2024. Les fenêtres, couvertures,
seuils et signaux viennent de SQL. Le critère exige notamment N≥30 chaque mois,
une couverture complète et un service non ambigu. Les ±2 points et la cible de
régularité 90 % sont des hypothèses de portfolio, pas des engagements SNCF.

Les rangs de dégradation et de sous-performance restent ceux de J06 : filtrer
une liaison ne la transforme pas artificiellement en rang 1. Une mesure de
nombre de liaisons peut être totalisée dans une comparaison unique ; un taux de
trains ne le peut pas. La persistance annuelle reste BLANK, car la règle 4/6
n'y est pas définie. Tout filtre direct de date ou de cause invalide les mesures
de comparaison pour rendre le conflit de périmètre visible.

## Connexion, fichiers et exécution

| Élément | Nature, producteur et utilisateur |
|---|---|
| `powerbi/SNCF_Reliability.pbip` | Point d'entrée texte écrit par Desktop, ouvert par l'auteur du rapport |
| `SNCF_Reliability.SemanticModel/definition/` | TMDL : tables, colonnes, partitions M, relations et DAX ; lu par Desktop |
| `SNCF_Reliability.Report/definition/` | PBIR : pages et visuels techniques de contrôle, liés au modèle |
| `scripts/build_powerbi_project.py` | Générateur initial fondé sur les schémas BigQuery et la preuve SQL J06 ; ne prouve pas la validité Desktop |
| `scripts/build_powerbi_control_pages.py` | Générateur des trois pages PBIR de contrôle, vérifiées ensuite à l'écran ; aucun parcours métier J08 |
| `scripts/powerbi_model_tools.ps1` | Sérialisation TOM et lecture ADOMD du moteur local ; bibliothèques Microsoft hors dépôt |
| `scripts/validate_powerbi.py` | Producteur des preuves SQL/DAX et de l'audit des relations/partitions |
| `scripts/probe_powerbi_import.py` | Expérience isolée de persistance du cache Import dans `sncf_test` |
| `analyses/sql/j07_reconciliation.sql` | Référence SQL des sélections mensuelles, indépendante des mesures DAX |
| `analyses/dax/j07_reconciliation.dax` | Exemple lisible à exécuter dans la vue de requête DAX ou via ADOMD |
| `reports/powerbi_evidence/` | Copies locales contrôlées des preuves ; originaux d'exécution conservés hors dépôt |
| `reports/publication_evidence/powerbi_evidence/` | Copies publiques anonymisées, liées au manifeste de publication |

Les paramètres M sont `pProjectId`, `pBillingProject`, `pDataset` et `pExpectedVersion`.
Ils ne contiennent aucun secret. Le connecteur Google BigQuery utilise le mode
Import, `UseStorageApi=false`, et l'authentification enregistrée par l'utilisateur
dans Desktop. L'identité ADC des scripts Python est distincte de l'identité Desktop.
Les requêtes SQL natives doivent être approuvées dans Desktop par l'utilisateur.

Le projet **actif** est copié dans un dossier hors OneDrive, par exemple
`%LOCALAPPDATA%/SNCF_Service_Reliability_Analytics/powerbi-j07`. Sur une installation
virtualisée, résoudre le chemin effectif et ouvrir celui-ci dans Desktop.
Seules les définitions reviennent dans le dépôt. `.pbi/cache.abf`, les paramètres
locaux, PBIX, profils, identités et bibliothèques téléchargées restent exclus de Git.
**Une exclusion Git ne désactive pas la synchronisation OneDrive.** Ne pas ouvrir
et actualiser la copie versionnée à l'intérieur du dossier synchronisé.

## Choix, compromis et alternatives

- Import convient aux données mensuelles et à ce volume ; il permet des interactions
  locales rapides, mais exige une actualisation explicite et une provenance lisible.
  DirectQuery ajouterait des appels BigQuery à l'interaction et ne dispense pas
  des contrôles de population. Il n'est pas retenu pour cette V1.
- PBIP/TMDL/PBIR permet la revue Git. Le cache ne voyage pas avec les définitions :
  une nouvelle machine doit se connecter et importer. PBIX reste le repli de livraison
  si une incompatibilité Desktop empêche PBIP ; son contenu binaire n'est jamais édité.
- Les données métier et critères restent SQL/dbt ; reproduire toute cette logique
  en DAX créerait deux implémentations à maintenir. DAX porte l'agrégation et les gardes.
- Une constellation de faits évite une grande table où les six causes répéteraient
  les effectifs. Les relations simples évitent les chemins de filtre ambigus.
- Les marts importés facilitent la lecture et la preuve J06, au prix d'une petite
  duplication. Leur suppression ou une optimisation mesurée peut être étudiée ensuite.

## Reproduction et validation

Dans l'environnement Python J02 et PowerShell 7, avec BigQuery autorisé :

```powershell
# Après ouverture et actualisation du projet actif hors OneDrive :
python scripts/validate_powerbi.py --project sncf-reliability-analytics `
  --server localhost:<port_observe> --work-directory <dossier_actif>
```

Le port est celui du moteur Desktop de la session courante, jamais une valeur
historique recopiée sans contrôle. Les DLL officielles Microsoft AMO/TOM et ADOMD
19.118.3 se trouvent dans `tools/tom/lib/net8.0/` et `tools/adomd/lib/net8.0/` sous le
dossier actif. Le générateur initial et la sérialisation ne sont nécessaires que
pour reconstruire un brouillon ; utiliser les définitions qualifiées pour poursuivre J08.

Le validateur conserve requêtes, réponses, identifiants des jobs, octets traités,
empreintes du code et échecs. Chaque requête de validation SQL est plafonnée à
100 MB ; ce plafond par requête ne représente pas un budget global ni celui du
connecteur Desktop. Les tolérances sont 10⁻⁹ pour les ratios et 1,1×10⁻⁷ point
pour les écarts, afin de tenir compte des ratios SQL arrondis à neuf décimales.
Les NULL/BLANK, textes, clés, effectifs et cardinalités doivent correspondre.

Voir le [rapport de réconciliation](../reports/sql_powerbi_reconciliation.md)
et le [bilan J07](milestones/J07_handoff.md) pour les contrôles réellement exécutés,
leurs versions et leurs limites. Une définition textuelle valide, un modèle chargé
ou une batterie SQL seule ne suffisent pas à qualifier les mesures Power BI.

## Limites et prolongements

D01–D07 demeurent : population P−A déduite non certifiée, conventions historiques
d'annulation, anomalies et quarantaines, population des causes non démontrée,
absence de données voyageurs/incidents/coûts. Une concordance SQL/DAX valide
l'implémentation du contrat, pas ces hypothèses sur le monde réel.

Hors J07 : mise en page métier et storytelling (J08), orchestration complète (J09),
publication Power BI Service/Fabric, refresh planifié, RLS, optimisation de grande
volumétrie, reconstruction sur machine neuve. Leur valeur et leur effort doivent
être évalués selon un besoin explicite ; ils ne sont pas ajoutés automatiquement.

## Compléments J08 — rapport et contexte de présentation

J08 conserve les 12 tables Import et les 16 relations. Les 57 expressions de
mesures J07 sont inchangées ; 17 mesures de présentation portent le total à 74.
Le catalogue décrit les titres, effectifs de fenêtres fixes, statuts, annotations
d'investigation et quatre séries mensuelles alignées. La colonne calculée
`dim_comparison[comparison_label]` expose deux libellés français ; les identifiants
et bornes SQL restent inchangés. Aucune relation ni population nouvelle.

Les séries mensuelles réévaluent les taux J07 sur un mois complet de chaque
fenêtre. Le segment de mois du profil de causes est isolé par les interactions
PBIR ; il ne filtre pas les comparaisons ou courbes. Le drillthrough transmet
liaison, service et comparaison, sans filtre supplémentaire hérité.

Les textes R01–R06 sont éditoriaux, rattachés à leur version et semestre ; ils
ne constituent pas des faits opérationnels nouveaux. Les statuts de causes
présentés sont traduits en français ; les codes SQL restent conservés.

Voir [le guide](dashboard_guide.md) et [le bilan J08](milestones/J08_handoff.md).
La commande J07 reçoit `--include-dashboard` pour vérifier les 74 mesures : les
contrôles des populations, ratios, rangs et relations restent exécutés. Le contrôle
J08 compare en outre les 57 expressions réelles avec le commit J07 et les séries
mensuelles avec les effectifs BigQuery. La preuve Import 1→2 historique est
réutilisée sans être réinitialisée ; les données et la date de lecture restent
identiques. Les définitions et caches gardent la séparation hors OneDrive.
