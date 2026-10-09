# J03 — Ingestion Python fiable et traçable

**État : terminé avec limites explicites, le 7 octobre 2026.** Les 12 907 observations de l'export réel sont vérifiées dans BigQuery ; la relance du même contenu réutilise une seule table brute et conserve chaque tentative. Les scénarios synthétiques de correction, suppression, schéma incompatible et chargement invalide ont été exécutés dans `sncf_test`. Les tests locaux et preuves détaillées sont dans `reports/ingestion_evidence/`.

## Présentation et accord

La conversation a commencé par la lecture du plan, des bilans J01/J02, du contrat de données, du code et de Git. La présentation a expliqué objectif, API REST, export/pagination, ELT, manifeste, empreintes, idempotence, étapes, fichiers, stockage, alternatives, contrôles, limites et compétences. La pause prévue par AGENTS et le plan a été respectée ; les reprises automatiques de l'objectif n'ont pas été interprétées comme un accord d'implémentation.

Le porteur du projet a ensuite autorisé l'approche : **« Ok parfait implémente ! »**. Cet accord a couvert l'ingestion complète TGV, les archives externes, les tables brutes de version, la vue courante, les journaux, les tests, les contrôles cloud isolés et cette transmission. Aucun jalon J04 ou suivant n'a été implémenté.

Les compléments utiles au périmètre sont trois scripts de validation : scénarios cloud opt-in, preuve locale séparée et relecture du brut/journal réels. Ils rendent les critères démontrables et reproductibles ; ils ne constituent pas l'orchestration complète de J09.

## Résultat et cheminement

1. Création de `codex/j03-ingestion` dans le dépôt SNCF déjà isolé ; aucune modification du dépôt parent, aucun commit ni publication.
2. Implémentation du transport borné, des archives vérifiées, des journaux persistants et du rejeu sans appel SNCF.
3. Implémentation de versions brutes séparées, d'une relecture complète des payloads et d'une promotion par vue après validation.
4. Extraction réelle : métadonnées avant/après stables, effectif attendu/reçu de 12 907, 26 champs, couverture janvier 2018–septembre 2026. Source déclarée modifiée et traitée le 2 octobre 2026 à 10:10:31 UTC ; extraction le 7 octobre.
5. Première tentative de chargement interrompue par une erreur locale de paramètre ; archive et journal préservés. Correction puis rejeu de l'archive, chargement et promotion réussis.
6. Nouvelle capture avec le code final : même contenu, table réutilisée, aucune nouvelle version active et aucun déplacement de la vue. Les métadonnées et tous les payloads ont été revérifiés.
7. Scénarios synthétiques dans `sncf_test`, validation locale distincte, comparaison J01/J03 et vérification finale du journal cloud.

La source réelle compte **363 nouvelles clés**, réparties en juillet, août et septembre 2026 (121 par mois), **aucune clé supprimée**, 12 301 clés communes strictement inchangées et **243 clés communes présentant des différences numériques** entre janvier et juin 2026. La revue technique précise que ces différences concernent les moyennes et parts décimales : écarts de l'ordre de 10⁻¹⁴, aucun changement des effectifs sur les clés communes. Ce sont des différences strictes de valeurs reçues, pas des corrections métier significatives démontrées. Voir `source_comparison.json` et `numeric_precision_review.json`.

Ces résultats ne renouvellent ni l'audit métier, ni les critères d'éligibilité, ni les preuves J01. Les 363 ajouts ne sont pas assimilés à des trains physiques supplémentaires : le grain reste mois × départ × arrivée × service.

## Architecture, décisions et alternatives

| Décision | Besoin satisfait, compromis et limite |
|---|---|
| Export JSON complet, sans filtre | Évite les limites des pages `records` et couvre les révisions du passé ; transfère tout l'historique à chaque capture |
| Python pour transport et chargement | Délais, reprises, archives et contrôles techniques ; les transformations métier restent SQL/dbt |
| BigQuery en `EU`, datasets J02 conservés | Entrepôt déjà confirmé et connecté ; aucune nouvelle plateforme ou localisation |
| Une table brute par `version_id`, vue `raw_tgv_current` | Historique conservé et remplacement complet de l'état courant ; stockage croissant sans purge automatique |
| `payload STRING` JSON source et enveloppe technique | Préserve noms SNCF, valeurs nulles, signes et anomalies ; extraction/typage des champs à J04 |
| Empreinte d'octets et identité canonique distinctes | Archive exacte d'un côté, reconnaissance des mêmes observations de l'autre ; aucune déduplication des lignes source |
| Archives et tentatives séparées | Archive complète figée, journaux prolongés par les reprises ; plusieurs tentatives peuvent référencer une seule version |
| `ASSERT` + `MERGE` pour le journal | Synchronisation sans doublon sur tentative/séquence, refus d'un événement historique différent ; SQL technique sans calcul KPI |
| Identifiants de jobs stables et relecture de leur état | Réponse perdue distinguée d'un échec effectif ; une attente expirée exige une reprise informée |
| Verrou OS local | Évite deux exécutions concurrentes vers la même destination depuis un même stockage ; pas de coordination multi-machine |
| Validation réelle isolée dans `sncf_test` | Prouve correction/suppression/échec sans altérer le brut SNCF courant ; objets synthétiques conservés jusqu'à leur expiration prévue |
| PyYAML 6.0.3 déclaré directement, projet 0.3.0 | Configuration YAML exécutée explicitement ; verrou toujours à 106 paquets, dont 105 dépendances externes |

Une ingestion incrémentale diminuerait les transferts mais demanderait une preuve de gestion des révisions et suppressions. La pagination vérifiée reste possible si l'export n'est plus adapté, avec davantage de contrôles. Une table unique écrasée simplifierait la structure mais supprimerait l'historique. Un brut immédiatement typé faciliterait les requêtes au prix de conversions plus précoces. GCS apporterait un archivage indépendant mais aussi des ressources, permissions et règles de conservation supplémentaires. PostgreSQL ne répond pas à un besoin de cette V1 BigQuery. Ces alternatives n'ont pas été ajoutées au travail.

## Fichiers et utilisateurs

| Livrable | Nature, producteur → utilisateur |
|---|---|
| `src/sncf_reliability/__init__.py`, `api_client.py` | Code d'organisation/transport → ingestion, CLI et tests |
| `src/sncf_reliability/ingest.py` | Code de capture, validation, empreintes, comparaison et journal → opérateur et validations |
| `src/sncf_reliability/warehouse.py` | Code BigQuery → CLI ; versions brutes, vérification, promotion et audit |
| `src/sncf_reliability/cli.py`, `scripts/run_ingestion.py` | Interface et lanceur → utilisateur de l'environnement verrouillé |
| `config/datasets.yaml` | Configuration source exécutée → ingestion ; 26 champs, types et réseau |
| `.env.example`, `config/settings.example.yaml` | Paramètres documentaires complétés → opérateur ; aucune valeur secrète |
| `pyproject.toml`, `uv.lock` | Dépendances et verrou mis à jour → installation locale/future CI |
| `tests/test_ingestion.py`, `tests/fixtures/ingestion_rows.json` | Scénarios et données synthétiques → tests hors réseau |
| `scripts/validate_ingestion_local.py` | Générateur de preuve locale → tests, versions du code, archives et comparaison |
| `scripts/validate_ingestion_cloud.py` | Générateur opt-in → scénarios réels dans `sncf_test` |
| `scripts/validate_ingestion_warehouse.py` | Vérification cloud en lecture → tous les payloads réels et événements d'audit |
| `reports/ingestion_evidence/` | Résultats générés → lecteur : tests, validation, scénarios cloud, état réel, différences source et revue Git |
| `docs/ingestion.md` | Documentation de conception et d'exploitation → mainteneur ; définitions, exemples, commandes, reprise et alternatives |
| `docs/setup.md`, `docs/architecture.md` | Documentation mise à jour → installation et circulation des données |
| `PLAN.md`, ce bilan | État, décisions acceptées et transmission → porteur du projet et J04 |

Les exports complets, manifestes, fichiers NDJSON et journaux locaux restent hors dépôt/OneDrive sous `SNCF_DATA_DIR`. Les objets cloud ne sont pas des fichiers du dépôt. Les preuves synthétiques versionnables ne constituent pas le jeu SNCF complet. `.gitignore` n'agit pas sur OneDrive ; les chemins sont contrôlés physiquement. Les fichiers J01 et leur `validation.json` restent inchangés.

## Critères réellement vérifiés et preuves

| Critère / risque couvert | Méthode, résultat attendu et résultat obtenu | Preuve / sens d'un échec |
|---|---|---|
| Exhaustivité, sans troncature silencieuse | Métadonnées avant/après = lignes reçues ; 12 907 = 12 907 = 12 907 ; troncature synthétique rejetée | Manifeste, `validation.json`, tests ; un écart interdit le chargement |
| Cohérence de version pendant l'extraction | Effectif, marqueurs et schéma stables ; modification synthétique à effectif constant détectée | Métadonnées archivées, tests ; instabilité invalide la capture |
| Réseau borné | Erreurs temporaires reprises, erreurs terminales/épuisement signalés, partiels conservés | `tests.txt` ; aucun essai illimité ni fichier partiel accepté |
| Relance sans duplication active | Rejeu réel puis nouvelle capture identique : même table ; seconde capture `reused=true`, `promotion_changed=false` | `live_warehouse.json` ; une nouvelle duplication active serait un échec |
| Journal des tentatives conservé | Relecture finale : 31 événements cloud, exactement conformes aux 31 événements locaux des trois tentatives réelles ; aucun doublon | `live_warehouse.json` ; une trace manquante ou différente exige synchronisation/revue |
| Correction/suppression historiques | Deux observations synthétiques deviennent une observation corrigée ; ancienne table toujours à deux lignes, courante à une | `cloud_scenarios.json` ; une observation supprimée encore courante serait un échec |
| Échec de chargement sans perte de l'état valide | Entier volontairement invalide : rejet BigQuery `BadRequest`, aucune ligne partielle visible, vue précédente intacte | Jobs et erreurs dans `cloud_scenarios.json` ; aucune promotion d'un fichier invalide |
| Schéma incompatible signalé | Métadonnées synthétiques incompatibles refusées avant chargement ; version courante intacte | Tests et `cloud_scenarios.json` ; révision explicite du schéma nécessaire |
| Rejeu figé | Archive J01 vérifiée sans modification ; archive J03 rejouée jusqu'au cloud ; tests interdisant les appels SNCF pendant le rejeu | `validation.json`, `tests.txt`, tentatives réelles ; empreinte différente = archive refusée |
| Chargement direct et lien au manifeste | Relecture complète des 12 907 payloads, numéros, versions et empreintes ; contexte d'audit portant manifeste et source SHA-256 | `live_warehouse.json`, journal cloud ; effectif seul insuffisant |
| Synchronisation/reprise | Répétition de la synchronisation sans doublon, observation `reconciled` conservée ; réponses perdues et audit temporairement indisponible simulés | Scénarios cloud et tests ; une promotion incertaine appelle une relecture |
| Non-régression | 37 tests réussis : 24 J03 et 13 J01 ; scripts de profilage non modifiés | `tests.txt`, `validation.json` ; tests J01 préservés |
| Dépôt et stockage | Revue des chemins, exclusions, fichiers ajoutables et espaces de fin de ligne ; aucune source complète ou clé dans le périmètre Git | `git_review.json` ; `.gitignore` seul ne prouve pas un stockage externe |

Les tests locaux utilisent des doubles pour les réponses perdues, les indisponibilités et les interruptions ; aucune panne réelle de Google ou coupure forcée du processus n'est revendiquée. Les échecs de chargement et de schéma synthétiques ont, eux, été exécutés avec les vrais services BigQuery. La revue de précision des différences et la revue Git sont des vérifications techniques distinctes de l'audit métier.

## Versions du code, des données et objets

- Code : projet **0.3.0**, Python **3.13.15**, `uv` **0.12.21**, `google-cloud-bigquery` **3.45.2**, PyYAML **6.0.3** ; environnement externe `venv-j02` réutilisé. Les versions dbt verrouillées J02 restent inchangées.
- Branche : **`codex/j03-ingestion`**, dépôt propre au dossier SNCF. **Aucun commit, remote, push, PR ou release n'a été créé.** Les versions du code sont identifiées par SHA-256 dans `validation.json` ; le scénario cloud conserve aussi les empreintes des modules exécutés.
- Archive de référence J03 finale : **`20261007T130103249967Z_bce4ef24`**.
- `version_id` : **`e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6`**.
- SHA-256 des octets source : **`8dc2b0a9a3707306c3087f899163465e34b20ed44b4dfc4ad46d5af4686334b2`**.
- SHA-256 du manifeste final : **`1cca3fcbf6e4a94343866eedec4badf35d1ef2961cac75550cc0d666ea03b5cd`**.
- Table réelle : `sncf-reliability-analytics.sncf_dev.raw_tgv_v_e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6` ; vue : `sncf_dev.raw_tgv_current` ; audit : `sncf_audit.raw_tgv_load_events`.
- Première capture conservée : `20261007T125529945750Z_cdc81d27`, même contenu, manifeste distinct ; tentative échouée `cdc81d27c313482384a7f224406814f1`, rejeu réussi `0f7603991487438583d51395ed4db56a`, capture/rejeu idempotent final `bce4ef2494e5460d9da4b9dd27f1397a`.
- Job de première vérification du brut : `sncf_check_raw_tgv_0f7603991487438583d51395ed4db56a` ; 12 963 445 octets traités et 13 631 488 octets facturables observés. Les relectures suivantes ont bénéficié du cache ; ne pas supposer un coût nul permanent.
- Scénarios cloud finaux : préfixe **`j03_check_54a857fcde`**, dans `sncf_test`. La première série `j03_check_da7c0d7d12` et sa preuve initiale restent conservées ; une seconde série a vérifié le code final, notamment la réconciliation durable.

Chemin nominal : `%LOCALAPPDATA%\SNCF_Service_Reliability_Analytics\data\ingestion\20261007T130103249967Z_bce4ef24`.

Chemin résolu sur ce poste :

```text
C:\Users\<utilisateur>\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\SNCF_Service_Reliability_Analytics\data\ingestion\20261007T130103249967Z_bce4ef24
```

La source J01 `20261001T140237476619Z`, ses documents et son empreinte `1b18c596c59b38f4feb230a630d5a8b8a3b3f13fa5802407ece9c269c575f24f` sont conservés. Aucun fichier de référence J01 n'a été remplacé par les nouvelles observations.

## Commandes de reproduction

Depuis la racine du dépôt SNCF :

```powershell
$taskPython = Join-Path $env:LOCALAPPDATA 'SNCF_Service_Reliability_Analytics\venv-j02\Scripts\python.exe'
$taskData = Join-Path $env:LOCALAPPDATA 'SNCF_Service_Reliability_Analytics\data'
$taskSnapshot = Join-Path $taskData 'ingestion\20261007T130103249967Z_bce4ef24'
$taskPrevious = Join-Path $taskData 'audit\20261001T140237476619Z'
$env:GOOGLE_CLOUD_PROJECT = 'sncf-reliability-analytics'
$env:BQ_LOCATION = 'EU'

& $taskPython -m unittest discover -s tests -v
& $taskPython scripts/run_ingestion.py verify --snapshot $taskSnapshot
& $taskPython scripts/run_ingestion.py compare --previous $taskPrevious --snapshot $taskSnapshot
& $taskPython scripts/validate_ingestion_local.py --previous $taskPrevious --snapshot $taskSnapshot

# Commandes cloud : requêtes bornées, pas de garantie de gratuité.
& $taskPython scripts/run_ingestion.py replay --snapshot $taskSnapshot --load
& $taskPython scripts/validate_ingestion_warehouse.py --project $env:GOOGLE_CLOUD_PROJECT --snapshot $taskSnapshot
& $taskPython scripts/run_ingestion.py sync-audit --attempt (Join-Path $taskData 'attempts\cdc81d27c313482384a7f224406814f1')
& $taskPython scripts/validate_ingestion_cloud.py --execute --project $env:GOOGLE_CLOUD_PROJECT

# Nouvelle extraction, uniquement lorsqu'une actualisation est voulue.
& $taskPython scripts/run_ingestion.py fetch --load
```

Si `LOCALAPPDATA` résout un autre dossier dans un autre contexte, utiliser le chemin physique constaté ci-dessus ou transférer l'archive complète, puis renseigner `--snapshot`. Une archive rejouée ne relit pas SNCF. Une nouvelle validation locale renouvelle ses tests/empreintes, mais pas l'état cloud ; celui-ci est vérifié séparément. Le dossier `reports/audit_evidence/` de J01 n'est pas une entrée source.

## Erreurs résolues et limites

Le premier chargement réel a échoué avant soumission du fichier : `load_table_from_file` n'accepte pas `retry` dans la version verrouillée. Le paramètre a été remplacé par `num_retries=2` et les doubles de tests vérifient désormais les signatures réelles du client. L'archive validée a été rejouée, les traces d'échec sont conservées et synchronisées. Une erreur initiale du double de test utilisait `full_table_id` avant création ; il utilise maintenant la référence de table, sans effet sur les données cloud.

Les limites restantes sont explicites :

- Les métadonnées avant/après ne prouvent pas une transaction côté fournisseur ; aucun marqueur source ne garantit à lui seul toutes les révisions possibles.
- L'exécution concurrente depuis plusieurs machines ou racines de stockage n'est pas coordonnée ; la V1 vise une exécution locale à la fois.
- La promotion et sa trace finale sont distinctes. Les événements et jobs permettent une réconciliation, sans prétendre qu'une réponse perdue est un échec certain.
- Les versions sont immuables par le comportement du programme ; le compte propriétaire peut techniquement modifier les objets. Une identité dédiée à droits limités viendra avec le besoin d'automatisation.
- Les archives locales ne sont pas une sauvegarde indépendante ; l'application peut rediriger leur chemin. Aucune purge automatique n'est effectuée.
- Les objets synthétiques expirent dans `sncf_test` après sept jours ; leurs preuves, identifiants de jobs et archives locales restent disponibles. La durée de disponibilité des métadonnées Google est distincte de celle des preuves locales.
- La limite de 100 MB s'applique à chaque requête, pas à la facture totale. L'alerte de 1 € J02 reste une notification ; aucun quota quotidien bloquant ni facture finale n'est revendiqué. La facturation reste soumise aux relevés Google et aux crédits existants.
- Les tests dbt, transformations de production, modèle en étoile, calculs SQL/DAX, actualisation Power BI, publication, automatisation et reconstruction sur une machine neuve ne sont pas effectués à J03.
- Les réserves métier D01–D07 sont intégralement maintenues. En particulier, les écarts décimaux observés ne justifient aucune révision des exclusions >30 du T1 2025, ni des populations des causes ou du dénominateur déduit.

## Transmission à J04 et bilan pédagogique

J04 pourra déclarer la vue `sncf_dev.raw_tgv_current` comme source dbt, extraire les champs de `payload`, appliquer les noms cibles du contrat et conserver `version_id` comme provenance. Les contrôles de grain, clés, mois, bornes et exclusions restent à produire dans SQL/dbt. La source récente va jusqu'à septembre 2026 ; les fenêtres métier et seuils J01 ne doivent pas être révisés opportunément. Toute nouvelle période analytique devra être justifiée et tracée au jalon concerné.

À retenir : une réponse HTTP réussie n'assure pas l'exhaustivité ; une archive complète n'assure pas la qualité métier ; une extraction récente n'assure pas des observations récentes ; une relance n'est pas nécessairement une nouvelle version ; un échec d'observation réseau n'est pas nécessairement un échec d'écriture. Les trois dates — extraction, modification source, dernier mois métier — répondent à trois questions différentes.

Compétences démontrées : API REST, Python structuré, gestion des erreurs, ELT, BigQuery, schéma explicite, empreintes, tests de comportements, versionnement des données, idempotence, reprise et documentation de preuves.

Questions d'entretien et réponses défendables :

- « Comment garantir que tu n'as pas chargé seulement la première page ? » Export complet, égalité des effectifs et contrôles de stabilité avant/après.
- « Comment répercuter une suppression ancienne ? » Nouvelle version complète et remplacement de la référence courante ; historique conservé séparément.
- « Que faire si le chargement a réussi mais que la réponse est perdue ? » Rechercher le job connu et vérifier les données, sans créer une écriture sous une nouvelle identité.
- « Pourquoi ne pas corriger une valeur négative à l'ingestion ? » Parce que la fidélité du brut et les exclusions propres à chaque indicateur doivent rester séparées.
- « Les 243 différences prouvent-elles une révision de performance ? » Non : leur ampleur observée est de l'ordre de la précision numérique ; la comparaison brute ne démontre pas une évolution métier.

Approfondissements possibles, non engagés : archivage cloud indépendant (résilience, ressources/rétention nécessaires, effort modéré), coordination distribuée (concurrence multi-machine, tests supplémentaires, effort supérieur), automatisation et identité dédiée à J09 (CI et droits adaptés), éventuelle ingestion incrémentale après preuve de gestion des révisions et suppressions. Le jalon suivant nécessite sa présentation et son accord propres.
