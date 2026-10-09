# Ingestion fiable et traçable — J03

## Objectif et périmètre accepté

Après la présentation pédagogique dans cette conversation, le porteur du projet a donné son accord le 7 octobre 2026 : « Ok parfait implémente ! ». J03 extrait complètement le jeu TGV, conserve une archive vérifiable et charge des versions brutes BigQuery avant leur mise à disposition. Les transformations métier, modèles dbt, calculs KPI, publication et actualisation Power BI appartiennent aux jalons suivants.

Python s'exécute sur le PC ; BigQuery conserve les tables et exécute le SQL technique de contrôle et de journalisation. Le SQL de J03 ne transforme aucun indicateur métier. Les noms SNCF et les valeurs source sont conservés dans `payload`. Le script d'audit J01 et ses résultats ne sont pas modifiés.

## Définitions et circulation des données

Une **API REST** est une interface appelée par HTTP. Un **endpoint** est l'adresse d'une opération. La **pagination** fournit des pages de résultats ; elle n'assure pas à elle seule l'exhaustivité. L'endpoint `exports/json` est utilisé sans filtre pour l'ensemble de l'historique, avec métadonnées avant et après.

Une **extraction** produit une copie locale. Un **chargement** envoie des observations dans BigQuery. Un **manifeste** décrit une extraction et ses contrôles. Une **empreinte SHA-256** identifie un contenu ; elle ne certifie pas sa qualité métier. L'**idempotence** signifie qu'une relance identique ne double pas les données courantes. Une **promotion** rend une version validée accessible par la vue courante. **ELT** signifie extraire, charger, transformer : la transformation analytique SQL/dbt vient après J03.

```text
API SNCF : métadonnées avant → export JSON complet → métadonnées après
     ↓ Python sur le PC : contrôles de transport, schéma, effectifs et stabilité
SNCF_DATA_DIR/ingestion/<snapshot_id>/ : archive locale figée
     ↓ chargement direct, fichier technique NDJSON local
BigQuery sncf_dev.raw_tgv_v_<version_id> : table brute d'une version
     ↓ relecture complète et comparaison de chaque payload avec l'archive
BigQuery sncf_dev.raw_tgv_current : vue sur une seule version validée

Chaque tentative → journal local durable → sncf_audit.raw_tgv_load_events
```

Les données restent dans le cloud quand le PC est éteint ; une nouvelle extraction locale exige que le PC fonctionne. Google Cloud Storage n'est pas requis. Les archives locales ne sont pas des sauvegardes indépendantes du PC. Une archive distribuée avec une release sera un livrable distinct à J10 ; aucune release n'est créée ici.

## Responsabilités des fichiers

| Fichier | Nature ; producteur → utilisateur ; liens |
|---|---|
| `src/sncf_reliability/__init__.py` | Organisation du module Python → lanceurs et tests |
| `api_client.py` | Code HTTP → `ingest.py` ; délais, reprises limitées, téléchargements partiels |
| `ingest.py` | Code d'archives, contrôles, empreintes, comparaison et journal → CLI, entrepôt et validations |
| `warehouse.py` | Code BigQuery → CLI ; tables de version, relecture, vue courante et audit |
| `cli.py` | Code d'interface → utilisateur ; appelle les autres modules |
| `scripts/run_ingestion.py` | Lanceur depuis le dépôt → interpréteur verrouillé J02 |
| `config/datasets.yaml` | Configuration exécutée → ingestion ; identifiant, URL, champs/types et réseau |
| `.env.example`, `config/settings.example.yaml` | Exemples documentaires → opérateur ; pas de secret ni de chargement automatique `.env` |
| `tests/test_ingestion.py`, `tests/fixtures/ingestion_rows.json` | Tests et petites données synthétiques → `unittest` ; aucun export SNCF complet |
| `scripts/validate_ingestion_cloud.py` | Code de validation explicite → opérateur ; crée des objets synthétiques dans `sncf_test` |
| `scripts/validate_ingestion_local.py` | Code de validation locale → opérateur ; tests, empreintes et comparaison sans réseau |
| `scripts/validate_ingestion_warehouse.py` | Code de validation cloud en lecture → opérateur ; compare tous les payloads et événements locaux avec BigQuery |
| `reports/ingestion_evidence/` | Résultats générés → lecteur ; preuves locales/cloud et comparaison source |
| `docs/ingestion.md`, `docs/milestones/J03_handoff.md` | Documentation → mainteneur, porteur du projet et prochain jalon |
| `pyproject.toml`, `uv.lock` | Dépendances directes/verrou → installation ; version projet 0.3.0 et PyYAML déclaré explicitement |
| `docs/setup.md`, `docs/architecture.md`, `PLAN.md` | Documentation mise à jour → reprise et suivi du projet |

## Archives et identités

`SNCF_DATA_DIR` remplace le défaut `%LOCALAPPDATA%\SNCF_Service_Reliability_Analytics\data`. Le programme refuse un emplacement résolu dans le dépôt ou OneDrive. Le chemin Windows peut être redirigé par l'application ; utiliser celui renvoyé dans `snapshot_path`, pas une hypothèse sur son emplacement physique.

Pour une extraction : `ingestion/<snapshot_id>/source.json`, `metadata_before.json`, `metadata_after.json` et `manifest.json`. Le manifeste indique statut, dates UTC, effectifs attendus/reçus, couverture mensuelle observée, empreintes des fichiers, schéma et identité du contenu. Les nouvelles captures incluent les empreintes des modules Python utilisés. Une archive `complete` n'est plus réécrite ; une capture échouée conserve les pièces reçues et un manifeste `failed`. Une interruption brutale peut laisser `in_progress`, statut refusé au rejeu.

Pour une tentative : `attempts/<attempt_id>/attempt.json`, `events.jsonl`, éventuellement `load.ndjson` et `result.json`. Les événements sont écrits et synchronisés sur disque avant les opérations suivantes. Une erreur laisse ses traces. Aucun nettoyage automatique n'est effectué. Le fichier de verrou OS peut rester après une exécution : seule la possession du verrou, pas son existence, indique une exécution en cours.

Les identifiants ont des fonctions différentes :

- `snapshot_id` : capture datée, même si le contenu n'a pas changé ;
- `attempt_id` : tentative distincte, y compris un rejeu ou un échec ;
- `source_sha256` : empreinte des octets du JSON reçu ;
- `manifest_sha256` : empreinte du manifeste associé ;
- `version_id` : SHA-256 du jeu source, du schéma et de la liste triée des représentations JSON canoniques des observations.

La représentation canonique trie les clés JSON et retire la mise en forme superflue ; elle ne modifie aucune valeur métier. L'ordre des observations ne change donc pas `version_id`. Les doublons, les zéros, les valeurs nulles, les signes et les différences de représentation numérique restent pris en compte. Deux captures de mêmes observations peuvent avoir des empreintes d'octets différentes et une même identité de version.

Le manifeste J01 est reconnu explicitement : ses pièces et empreintes sont vérifiées, les contrôles sont recalculés et son identité de contenu est dérivée sans réécrire cette archive.

## Contrôles avant promotion

1. Vérifier identifiant du jeu et schéma attendu ; refuser les champs ajoutés, supprimés ou de type déclaré incompatible.
2. Vérifier métadonnées avant/après : schéma complet, effectif, `modified` et `data_processed` stables et présents.
3. Vérifier JSON strict : pas de constante non finie ou de clé répétée ; tableau non vide, effectif exact, mêmes champs et types compatibles. Les champs nuls restent nuls.
4. Conserver l'archive et vérifier ses empreintes. Un mois absent/invalide est compté séparément dans la couverture sans correction des observations.
5. Charger le NDJSON dans une table propre à la version avec `WRITE_EMPTY`, schéma explicite, zéro mauvaise ligne tolérée et aucun champ inconnu ignoré.
6. Vérifier type de table, schéma, absence d'expiration durable, nombre de lignes, puis relire chaque `payload`, son empreinte, son numéro et sa version.
7. Synchroniser les preuves dans l'audit, puis remplacer la définition de la vue courante et relire ses métadonnées. Une table existante à la place de la vue n'est pas écrasée.

Les valeurs numériques négatives et les contradictions métier passent ces contrôles lorsqu'elles ont une représentation compatible : J03 certifie le transport d'une observation, pas sa validité pour un KPI. Un changement de schéma est bloquant jusqu'à une révision expliquée de la configuration ; aucun nouveau champ n'est silencieusement ignoré.

Les métadonnées ne garantissent pas un instantané transactionnel chez SNCF. Une révision qui ne change aucun marqueur pourrait échapper à cette vérification. Les empreintes définissent précisément le fichier reçu, sans prétendre résoudre cette limite.

## BigQuery, idempotence et reprise

Les tables `raw_tgv_v_<version_id>` contiennent `version_id STRING`, `row_number INTEGER`, `row_sha256 STRING` et `payload STRING`, tous requis. `row_number` ordonne techniquement les payloads canoniques ; ce n'est pas la clé métier. La future normalisation utilisera les champs JSON source à J04. Les anciennes versions ne sont jamais additionnées dans la vue courante.

Une version déjà présente est entièrement vérifiée puis réutilisée. Une suppression source disparaît de la nouvelle version courante ; l'ancienne archive garde l'observation. Exemple synthétique : deux lignes deviennent une ligne, avec `nb_annulation` corrigé de 2 à 7 ; la vue n'affiche que la nouvelle ligne tandis que la première table conserve ses deux lignes.

Le journal cloud expose `attempt_id`, `sequence`, `event_at`, `event`, `event_json`. Ce dernier conserve notamment source, version, manifeste, table et jobs quand ces informations sont disponibles. Les événements locaux sont synchronisés par une transaction `ASSERT` + `MERGE` sur `(attempt_id, sequence)` : les mêmes événements ne se dupliquent pas et un historique déjà enregistré différent est refusé. Cette idempotence ne dépend pas uniquement de la durée de conservation des métadonnées des jobs Google.

Les jobs ont des identifiants prévisibles rattachés à la tentative. Une réponse perdue déclenche une recherche du même job, sans soumission sous une nouvelle identité. Le chargement BigQuery est atomique. La promotion d'une vue et sa journalisation finale sont toutefois deux opérations distinctes : une interruption peut laisser une version valide promue et une trace finale encore locale.

`sync-audit` relit la vue, synchronise les événements manquants, ajoute une observation `reconciled` puis la synchronise. Il ne recharge pas de données et ne déplace pas la vue. `current_points_to_attempt_version=false` peut simplement signifier qu'une version plus récente est devenue courante. Il ne faut pas restaurer automatiquement une ancienne version pour résoudre un retard de journal.

Principaux événements : `capture_validated`, `capture_failed`, `load_started`, `raw_loaded`, `raw_reused`, `version_validated`, `promotion_requested`, `promoted`, `current_unchanged`, `load_failed`, `promotion_uncertain`, `audit_pending`, `attempt_error`, `reconciled`. Un échec avant promotion ne déclenche aucun remplacement de la vue. Une promotion dont le résultat est incertain exige une relecture ; l'état réel prime sur l'absence de réponse réseau.

La V1 protège les exécutions partageant le même dossier local et la même destination par verrou OS. Plusieurs machines ou racines de stockage indépendantes ne sont pas coordonnées. Les tables sont immuables par convention du programme, pas par interdiction IAM pour le compte propriétaire.

## Réseau et consommation

Par défaut : trois tentatives, délai socket de 60 secondes, contrôle de durée entre blocs reçus, attente exponentielle de 2 puis 4 secondes. Les erreurs HTTP 408, 429, 500, 502, 503, 504 et les incidents de transport sont repris ; les autres erreurs HTTP sont terminales. Un `Retry-After` numérique est honoré avec un maximum de 30 secondes. Les fichiers partiels sont distincts par tentative et conservés. Ce mécanisme borne les opérations, sans promettre un chronomètre global strict au niveau du système d'exploitation.

Les appels de métadonnées BigQuery ont un délai et une politique de reprise bornés ; les uploads emploient `num_retries=2`, conformément à la bibliothèque verrouillée. Les attentes de jobs sont bornées à 120 secondes. Une expiration d'attente n'est pas une preuve d'échec du job : consulter son identifiant et l'état courant avant de relancer.

Chaque requête SQL utilise `maximum_bytes_billed=100000000`. Cette limite ne plafonne ni le nombre de requêtes, ni le stockage, ni la facture totale. Les essais utilisent `sncf_test` avec expiration de sept jours ; les tables durables et le journal réel n'ont pas d'expiration automatique. Le budget d'alerte J02 demeure une notification. Aucun quota quotidien supplémentaire, compte payant, service de stockage ou identité de service n'a été créé à J03.

## Commandes de reproduction

Depuis la racine SNCF, après l'installation J02 :

```powershell
$taskPython = Join-Path $env:LOCALAPPDATA 'SNCF_Service_Reliability_Analytics\venv-j02\Scripts\python.exe'
$env:GOOGLE_CLOUD_PROJECT = 'sncf-reliability-analytics'
$env:BQ_LOCATION = 'EU'
$env:BQ_DEV_DATASET = 'sncf_dev'
$env:BQ_AUDIT_DATASET = 'sncf_audit'

# Extraction et validation locales ; aucune écriture cloud.
& $taskPython scripts/run_ingestion.py fetch

# Extraction complète puis chargement contrôlé.
& $taskPython scripts/run_ingestion.py fetch --load

# Remplacer les chemins par ceux renvoyés par les commandes ou le bilan.
& $taskPython scripts/run_ingestion.py verify --snapshot 'C:\archive\snapshot'
& $taskPython scripts/run_ingestion.py replay --snapshot 'C:\archive\snapshot'
& $taskPython scripts/run_ingestion.py replay --snapshot 'C:\archive\snapshot' --load
& $taskPython scripts/run_ingestion.py compare --previous 'C:\archive\ancienne' --snapshot 'C:\archive\nouvelle'
& $taskPython scripts/run_ingestion.py sync-audit --attempt 'C:\data\attempts\identifiant'

# Tests hors réseau et validation locale ; aucune actualisation des preuves J01.
& $taskPython -m unittest discover -s tests -v
& $taskPython scripts/validate_ingestion_local.py --previous 'C:\archive\J01' --snapshot 'C:\archive\J03'

# Vérification cloud en lecture ; requêtes bornées, sans nouvelle extraction.
& $taskPython scripts/validate_ingestion_warehouse.py --project $env:GOOGLE_CLOUD_PROJECT --snapshot 'C:\archive\J03'

# Écritures synthétiques explicites, isolées dans sncf_test.
& $taskPython scripts/validate_ingestion_cloud.py --execute --project $env:GOOGLE_CLOUD_PROJECT
```

`verify`, `replay` sans `--load`, `compare` et la validation locale n'appellent ni SNCF ni BigQuery. Les commandes chargées ou de synchronisation utilisent ADC ; aucune clé n'est demandée dans le dépôt. Les exemples YAML de paramètres généraux et `.env.example` sont documentaires ; les variables sont à définir dans la session.

## Validation, limites et apprentissage

Les tests locaux vérifient succès, exhaustivité, dérive de source/schéma, valeurs nulles, absence de correction du brut, empreintes, doublons, réseau, verrou, contenu cloud corrompu, relance, réponses perdues et reprise du journal. Les doubles du client vérifient aussi les signatures des méthodes de la version BigQuery installée. Ils ne remplacent pas les contrôles réels : `cloud_scenarios.json` contient les résultats synthétiques exécutés dans BigQuery et les jobs ; `live_warehouse.json` conserve la vérification réelle du brut SNCF et de l'audit. Le bilan relie chaque critère à sa preuve. `validation.json` de ce dossier est produit par une validation distincte ; il ne remplace pas `reports/audit_evidence/validation.json`.

La comparaison source est descriptive : elle distingue ajouts, suppressions et changements des clés communes uniques. Une clé commune répétée est signalée ambiguë, sans appariement forcé. Les noms de champs dans les différences restent ceux de SNCF. Les résultats J01 de couverture et d'éligibilité ne sont pas automatiquement recalculés sur la nouvelle source.

Les réserves D01–D07 demeurent : `P−A` déduit non certifié, retards composites publiés, causes sans effectifs reconstruits ni agrégation injustifiée, restrictions >15 et >30 au T1 2025, services et directions conservés, distinction zéro/nul/mois absent. Aucun indicateur national, classement, effet voyageurs, incident, coût opérationnel ou gain n'est inféré ici.

Questions d'entretien : pourquoi HTTP 200 ne prouve-t-il pas l'exhaustivité ? Comment traiter une suppression de 2024 ? Pourquoi distinguer tentative et version ? Comment réagir après une réponse perdue ? Pourquoi une donnée négative doit-elle rester dans le brut ? Les réponses reposent sur les contrôles et les preuves, pas seulement sur le choix des outils.

Extensions non engagées : stockage cloud indépendant pour la résilience (ressources et rétention supplémentaires, effort modéré), coordination multi-machine (verrou distribué et tests de concurrence, effort supérieur), automatisation/identité dédiée à J09 (droits et CI), table brute typée si un besoin mesuré le justifie. Un incrémental réduirait les transferts mais devrait démontrer la gestion des corrections et suppressions. PostgreSQL créerait une seconde architecture sans besoin V1 ; GCS reste facultatif. L'extraction complète et les versions séparées privilégient ici simplicité, traçabilité et reprise au prix d'un stockage croissant.

Références techniques : [API Explore — exports](https://help.opendatasoft.com/apis/ods-explore-v2/), [BigQuery — chargements par lots](https://docs.cloud.google.com/bigquery/docs/batch-loading-data), [GoogleSQL — DDL](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language). Les résultats effectivement obtenus sont documentés dans [le bilan J03](milestones/J03_handoff.md).
