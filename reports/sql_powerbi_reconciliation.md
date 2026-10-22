# Réconciliation SQL / Power BI — J07

**Qualification du 21 octobre 2026 : 6 286 contrôles réussis, aucun échec.**
Exécution `validation_20261021T143228Z`, terminée à 14:32:52 UTC. Les résultats
proviennent de BigQuery et du moteur tabulaire **réel** de Power BI Desktop
2.159.883.0, interrogé localement par ADOMD. Ce n'est pas une simulation de DAX.

## Version et périmètre

- Version canonique : `e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6`.
- Archive source J03 : `20261007T130103249967Z_bce4ef24`.
- Diagnostic de référence J06 : `20261013T102259Z_d1ed8f73` ; commit amont réel `a937b83`.
- 12 907 observations dans le fait principal, une seule version, dernier mois septembre 2026.
- Lecture des métadonnées de la copie qualifiée : **21 octobre 2026 à 14:28:01 UTC**.
- 12 tables Import, 16 relations actives plusieurs-vers-un à sens simple, 57 mesures prêtes sans erreur.
- Aucun calendrier automatique, aucune sonde de test dans le modèle de livraison.

Les contrôles de préparation ont vérifié les empreintes amont. Les tests dbt J04–J06
historiques ne sont pas présentés comme de nouvelles exécutions J07. Aucun export
source complet ni cache Power BI n'est publié avec les preuves.

## Résultats vérifiés

| Contrôle | Risque couvert et méthode | Résultat / preuve |
|---|---|---|
| Structure réelle du moteur | Relations ambiguës, DirectQuery accidentel, erreur de mesure ; inspection TOM | 12 tables, 16 relations, 57 mesures ; `model_audit.json` |
| Provenance | Mauvaise version ou import incomplet ; SQL et DAX sur version/effectif/mois | Identité exacte ; `metadata_sql.json`, `metadata_dax.json` |
| Sélections temporelles | Moyenne de ratios, mauvais dénominateur, exclusion de mois absents ; SQL indépendant et mesures DAX | 29 cas : mois, semestres, année et période incomplète, cinq couples liaison/service et quatre cas limites ; `cases.json`, `monthly_*.json` |
| Fenêtres fixes | Décalage de périodes, perte d'éligibilité, faux zéro annuel | 232 lignes comparées sur les deux fenêtres ; `comparison_*.json` |
| Populations de priorisation | Confusion entre trains et liaisons, persistance annuelle inventée | Deux synthèses identiques ; `summary_*.json` |
| Rangs J06 | Reclassement silencieux au filtrage | 125 lignes avec au moins un rang concordent avec la preuve figée J06 ; `ranks_dax.json` |
| Causes | Mauvaise échelle ou agrégation de profils | 726 lignes publiées de janvier 2026 : valeur brute, part utilisable et statut SQL concordent ; `causes_*.json` |
| Gardes de contexte | Taux national, service implicite, jours partiels, taux répété par cause | Huit contextes interdits renvoient BLANK ; `guards_dax.json` |
| Expérience Import | Confusion entre donnée entrepôt et cache | BigQuery 1→2 ; DAX reste 1, puis devient 2 après actualisation ; `create_*.json`, `change_*.json`, `verify_*.json` |
| Lecture Desktop | Modèle textuellement valide mais inutilisable | Trois pages ouvertes, valeurs, filtres et provenance examinés ; `manual_review.json` |

Les 6 286 contrôles comprennent les comparaisons de valeurs, de clés, les états
du moteur et les gardes ; ils ne représentent pas 6 286 scénarios métier distincts.
Les ratios utilisent une tolérance absolue de 10⁻⁹, les écarts 1,1×10⁻⁷ point.
Les NULL/BLANK sont comparés explicitement, sans les remplacer par zéro.
Un échec de correspondance invalide la qualification et conserve sa tentative.

### Cas explicatifs

**Dijon Ville → Paris Lyon, National, janvier 2025 :** 60 retards composites pour
422 circulations déduites, soit 14,218009… %, affiché 14,22 %. La couverture centrale
est complète. La couverture des retards importants est nulle : les taux >30 et >60
restent BLANK. La réserve T1 2025 ne supprime donc pas le taux central utilisable.

**Bordeaux St Jean → Tourcoing, mars 2026 :** zéro retard et une population positive
produisent un taux égal à zéro. Une autre sélection réelle de décembre 2020 à
population nulle produit BLANK ; une population absente de juin 2020 reste également
indisponible. Ces cas sont sélectionnés par propriétés et tracés dans `cases.json`.

**Juillet–décembre 2026 :** les mois après septembre restent attendus dans le calendrier.
Une couverture partielle ne devient pas artificiellement 100 %. Le ratio global
de la période est indisponible, même si les mois déjà reçus comportent des données.

| Fenêtre | Candidates | Éligibles | Dégradations ≥2 points | Améliorations ≥2 points | Dégradation persistante | Sous-performance persistante |
|---|---:|---:|---:|---:|---:|---:|
| H1 2026 / H1 2025 | 116 | 102 | 91 | 1 | 69 | 94 |
| 2025 / 2024 | 116 | 88 | 25 | 7 | Indisponible | Indisponible |

## Expérience d'actualisation

Le 21 octobre, `scripts/probe_powerbi_import.py` crée une table isolée
`sncf_test.j07_import_probe`, avec expiration à sept jours. Le scénario ne modifie
aucune table SNCF. Après import de 1, un UPDATE met seulement la sonde à 2.
Deux requêtes DAX encadrent ce changement, avant toute actualisation : elles lisent 1.
Après l'actualisation Desktop, SQL et DAX lisent 2. La partition temporaire est
retirée du modèle ; son fichier et les preuves restent dans le dossier externe.
La table BigQuery expirera selon son TTL, sans purge manuelle des traces.

La date d'import est différente de la date de clôture documentaire du jalon.
La conservation de cette preuve n'entraîne pas une nouvelle actualisation.

## Tentative initiale et revue complémentaire

La tentative `validation_20261021T142147Z` comptait 5 967 contrôles dont un échec :
le test cherchait `DIJON` au lieu de `DIJON VILLE`. Les comparaisons effectivement
exécutées concordaient, mais le jeu de cas requis était incomplet. Le libellé
du test a été corrigé, puis la qualification a été rejouée avec l'audit du moteur.
La première validation est conservée dans `first_attempt_validation.json` ; son
répertoire complet reste disponible localement.

La revue unifiée du plugin s'est terminée le 21 octobre. Elle est **heuristique**,
porte sur le dossier de travail avec ses brouillons, et détecte zéro mesure alors
que TOM en constate 57. Ses appréciations génériques ne prouvent ni l'absence de
risque ni la justesse métier. Les preuves live TOM/ADOMD et SQL ci-dessus font foi.
Les propositions de Fabric, RLS ou gouvernance générées par cet outil ne sont pas
des livrables implémentés et ne changent pas le périmètre J07.

## Reproduction, archivage et limites

Voir les commandes et paramètres du [modèle Power BI](../docs/powerbi_model.md).
Les requêtes exactes, sorties, logs et empreintes restent dans le dossier externe
d'exécution ; `execution_manifest.json` les indexe. Les preuves sélectionnées sont
copiées dans `reports/powerbi_evidence/` puis anonymisées par
`scripts/prepare_publication.py`, sans réexécuter la validation pour la publication.
Les captures originales, contenant l'interface du compte local, restent hors Git.

La qualification ne certifie pas P−A, la population des causes ni les conventions
historiques SNCF. Elle ne démontre pas la causalité, des voyageurs affectés, des coûts
ou des gains. Pas de test de Power BI Service, de refresh planifié, de RLS, de charge
à grande échelle ni de reconstruction complète sur machine neuve. Le modèle doit
être requalifié si les données, les règles SQL, les relations ou les mesures changent.
