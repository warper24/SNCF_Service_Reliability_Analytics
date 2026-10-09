# J02 — Environnement reproductible et connexion BigQuery

**État : terminé avec limites explicites, le 5 octobre 2026.** Présentation pédagogique effectuée, puis accord explicite reçu : « Je te donne mon accord pour l'implémentation de J02 ». Le porteur du projet a accepté les conditions Google Cloud et activé l'essai gratuit. Il a demandé de minimiser la consommation des 264 € de crédits et d'éviter toute dépense supplémentaire. Les contrôles Python, dbt et Power BI sur BigQuery sont réussis. Le porteur du projet a demandé un premier essai dans Brave afin de disposer librement du PC. Brave s'est fermé deux fois à l'étape de connexion Google ; il a ensuite demandé de reprendre dans Power BI Desktop.

## Objectif et résultat à ce stade

J02 établit un environnement Python/dbt reproductible et démontre Python → BigQuery, dbt → BigQuery et BigQuery → Power BI sur une petite table d'essai. Il prépare J03 sans charger l'export SNCF. Le code et les exemples de configuration sont prêts ; l'environnement verrouillé est installé. Le projet Google Cloud `sncf-reliability-analytics` est actif avec BigQuery ; quatre datasets EU et deux objets de contrôle dans `sncf_dev` sont vérifiés. Power BI Desktop a importé `sncf_dev.j02_python_connection_check` le 5 octobre 2026 et affiche une ligne `J02 / 1`.

## Décisions et raisons

| Décision | Raisonnement et limite |
|---|---|
| Dépôt Git propre au dossier SNCF, branche `codex/j02-environment` | La racine Git précédente était le parent `DATA PORTFOLIO`, sans commit, avec d'autres projets. Le dépôt imbriqué évite de les ajouter par inadvertance. Aucun commit ni remote configuré. |
| Python 3.13.15, `uv` 0.12.21, `dbt-bigquery` 1.12.1, `google-cloud-bigquery` 3.45.2 | Versions effectivement résolues et installées. `uv.lock` fige 106 paquets au total ; dbt Core résolu en 1.12.5. Il faudra régénérer le verrou lors d'une montée de version. |
| Environnement sous `%LOCALAPPDATA%` | Évite de placer les dépendances dans le dépôt OneDrive ; les exports J01 y résident déjà séparément. Une nouvelle machine doit recréer l'environnement. |
| `EU` comme localisation J02 | Cohérence vérifiée pour les quatre datasets, la table d'essai, la vue dbt et les jobs. |
| `sncf_dev`, `sncf_test`, `sncf_publish`, `sncf_audit` | Sépare développement, tests transitoires, future version publiée et audit. Les zones brute/analytique restent à détailler aux jalons de données. |
| OAuth local et ADC, sans clé de service dans Git | Google Cloud CLI 587.0.0 et `bq` 2.1.39 sont installés ; `gcloud auth login` et `gcloud auth application-default login` ont abouti. Les jetons restent dans le profil utilisateur hors du dépôt. |
| Test d'une seule ligne, expiration à 7 jours | Vérifie les droits sans utiliser les données SNCF. Les archives et journaux n'ont aucune expiration par défaut. |
| Lancer dbt par `scripts/run_dbt.py` | Sur ce poste, le lanceur `dbt.exe` trouve les versions mais échoue au parsage sur un module pourtant présent. Le même parsage réussit avec l'interpréteur Python verrouillé. Le lanceur de secours évite cette différence de résolution de chemin Windows. |
| Essai gratuit, alerte brute à 1 €, limites par requête | Le compte indique 264 € de crédits et aucun passage au compte payant n'a été demandé. Le budget mensuel du seul projet SNCF alerte à 50 %, 90 % et 100 % de 1 € avant déduction des crédits. Une alerte n'arrête pas les ressources. Python et dbt limitent chaque requête à 100 MB. La modification du quota quotidien `Query usage per day` est désactivée dans la console ; elle n'est pas revendiquée comme appliquée. |
| Power BI Desktop pour le contrôle J02 | Le connecteur web Google BigQuery et le mode Import ont été repérés, mais Brave s'est fermé deux fois lors de l'authentification Google. Le contrôle a donc été achevé dans Power BI Desktop 2.158.1177.0, installé gratuitement. Le porteur du projet a saisi lui-même les paramètres du projet et de l'API Storage, puis autorisé la connexion Google. Le Navigateur a montré le projet SNCF et la table d'essai ; le mode Import a été choisi et vérifié. Aucun rapport SNCF n'est publié à J02. |

BigQuery reste le choix d'entrepôt confirmé. PostgreSQL ajouterait un second chemin de mise en œuvre sans répondre au besoin J02. Google Cloud Storage pourrait fournir un archivage indépendant, mais n'est pas requis pour la V1. Un environnement Python global serait plus simple à démarrer, mais moins reproductible ; le verrou donne une base précise pour J03–J09. Ces alternatives sont pédagogiques, non ajoutées au périmètre.

## Fichiers créés ou modifiés

| Fichier | Nature ; producteur → utilisateur |
|---|---|
| `pyproject.toml`, `uv.lock` | Configuration et verrouillage produits à J02 → installation locale/CI future |
| `.gitignore`, `.env.example`, `config/settings.example.yaml` | Exclusions et paramètres exemples produits à J02 → développeur ; aucune valeur secrète réelle |
| `infra/bootstrap.sql` | Instructions SQL de création des datasets produites à J02 → opérateur BigQuery, après remplacement de `PROJECT_ID` |
| `dbt/dbt_project.yml`, `dbt/profiles.yml.example`, `dbt/models/j02_connection_check.sql` | Projet dbt, profil exemple et vue d'essai → dbt/BigQuery ; aucune logique métier |
| `scripts/check_bigquery.py`, `scripts/run_dbt.py` | Contrôle d'une table Python et lanceur dbt → développeur ; résultats de connexion à conserver ici |
| `docs/setup.md`, `docs/architecture.md` | Instructions et circulation des données → futur mainteneur et lecteur du portfolio |
| `PLAN.md`, ce bilan | Suivi de l'état et preuves → porteur du projet et jalon suivant |

L'export et le manifeste J01, version `20261001T140237476619Z` (SHA-256 source `1b18c596c59b38f4feb230a630d5a8b8a3b3f13fa5802407ece9c269c575f24f`), restent hors du dépôt. J02 n'en produit pas de nouvelle version. `.gitignore` ne coupe pas OneDrive ; les caches et PBIX doivent rester physiquement hors du dépôt quand ils contiennent une copie Import.

La branche locale est `codex/j02-environment` dans le dépôt SNCF isolé. Aucun commit ni publication n'a été effectué : l'identité d'auteur Git n'est pas configurée sur ce poste, et aucune identité n'a été inventée. Les fichiers J02 essentiels sont identifiables par SHA-256 : `uv.lock` `1ff20832f0a2c072b5f950d1baccd0904de26e419b4b85caa974bb16410d7216`, `scripts/check_bigquery.py` `6372dc66b682e0cc70a1d41cc78a734c54dab082bb18ce0f77f983e6b14cdd5c`, `dbt/models/j02_connection_check.sql` `b04971e049a4611058cf1cf95442d218b5e2f0d2c6b3f057764429d2942ab9bb`. Un ajout Git simulé a listé les 33 fichiers prévus, sans export complet, jeton, profil réel ou cache Power BI ; `git diff --cached --check` n'a signalé aucune erreur après mise en index temporaire, puis l'index a été remis à son état initial.

## Contrôles réellement exécutés et preuves

| Critère | Méthode et résultat | Preuve / sens d'un échec |
|---|---|---|
| Installation locale | `python -m uv lock`, puis `python -m uv sync --locked` dans `%LOCALAPPDATA%` : succès, 106 paquets résolus et 105 paquets externes installés | `uv.lock` et sorties de commande de cette session ; un échec indiquerait incompatibilité ou accès aux paquets |
| Compatibilité dbt locale | dbt Core 1.12.5, adaptateur 1.12.1 ; `scripts/run_dbt.py parse --project-dir dbt --no-partial-parse` : succès avec profil exemple et projet fictif | Parsage local réussi ; ne prouve pas une connexion BigQuery |
| Contrôle Python local | Compilation du script et validation d'un identifiant de projet fictif : succès, sans appel cloud | Code du contrôle ; ne prouve pas l'authentification |
| Non-régression J01 | `python -m unittest discover -s tests -v` : 13 tests réussis | Sortie de cette session ; les données J01 n'ont pas été reprofilées ni `validation.json` renouvelé |
| Exclusions Git | `.env`, `dbt/profiles.yml`, `data/example.csv`, `example.pbix` sont ignorés ; inspection des 33 fichiers ajoutables sans secret ni export complet | `git check-ignore -v`, `git add -n .` et contrôle de l'index temporaire ; aucun commit effectué |
| Projet et datasets BigQuery | Facturation activée et API BigQuery activée ; `infra/bootstrap.sql` exécuté le 05/10 ; `sncf_dev`, `sncf_test`, `sncf_publish`, `sncf_audit` relus par l'API en `EU` | Job de bootstrap `bqjob_r3ba7ad346b0d7ee7_000001a10c457754_1` ; `sncf_test` a `default_table_expiration_ms=604800000`, les trois autres n'ont pas d'expiration par défaut |
| Python lecture/écriture BigQuery | `scripts/check_bigquery.py --execute` : une ligne `(1, J02)` écrite et relue dans `sncf_dev.j02_python_connection_check` | Jobs `565b51db-7787-4719-b1e8-8ee811ecec87` (load) et `330a541e-0c1e-4ad5-98aa-eef3e6774cb8` (query) ; expiration de la table le 12/10/2026 à 13:34:49 UTC. Le job SELECT a traité 13 octets et compté 10 Mio facturables, minimum du service observé |
| dbt → BigQuery | `scripts/run_dbt.py debug` : `All checks passed` ; `run --select j02_connection_check` : PASS=1, vue créée, 0 octet traité | La métadonnée BigQuery confirme `VIEW`, `EU` et `select 1 as connection_ok, 'J02' as milestone` |
| Import Power BI | Après deux fermetures de Brave à l'étape Google, le porteur a terminé les paramètres et l'autorisation dans Desktop. Le Navigateur a affiché `sncf_dev.j02_python_connection_check` et son aperçu `J02 / 1`. Seule cette table a été cochée, puis le mode **Importer** a été confirmé. La vue Données de Desktop affiche une ligne `milestone=J02`, `connection_ok=1` ; les types observés sont **Texte** et **Nombre entier**. | Deux captures locales privées sous `%LOCALAPPDATA%\SNCF_Service_Reliability_Analytics\evidence` : `j02_powerbi_milestone.png` (SHA-256 `4a6da09718ca36951c89862e7b1af729efbaeda53e5d886f8fd804164f895860`) et `j02_powerbi_connection_ok.png` (SHA-256 `0c28a2f773b65a9513468362fdf9bde8b4d9734e9ad880226ef560f254506b37`). Les captures montrent la table importée, les valeurs et le type sélectionné. |
| Budget, quotas, droits, rétention cloud | Budget mensuel de 1 € brut ciblé sur le seul projet, alertes 50/90/100 % ; `maximum_bytes_billed=100000000` confirmé dans le profil dbt et le contrôle Python ; quota quotidien non modifiable via l'interface ; OAuth/ADC du compte créateur ont les droits nécessaires | L'alerte observée à 0 €/1 € dans la console au moment de la vérification ne garantit ni un plafond ni une facture finale ; aucune identité supplémentaire ni clé de service créée |

Le porteur du projet a accepté lui-même les conditions Google Cloud et lié l'essai gratuit au projet. Le projet a été créé à J02 sous l'identifiant `sncf-reliability-analytics`. Une première tentative `bq query` échouait parce que le dossier de la CLI Google n'était pas dans le `PATH` de la session PowerShell ; l'ajout temporaire de ce dossier a permis le bootstrap. Aucune suppression des données d'audit J01 n'a été effectuée.

## Reproduction et prochaines vérifications J02

Depuis la racine SNCF, suivre [l'installation](../setup.md). Commandes de contrôle local :

```powershell
$env:UV_PROJECT_ENVIRONMENT = Join-Path $env:LOCALAPPDATA 'SNCF_Service_Reliability_Analytics\venv-j02'
python -m uv sync --locked
python -m unittest discover -s tests -v
$env:GOOGLE_CLOUD_PROJECT = 'sncf-reliability-analytics'
$env:BQ_LOCATION = 'EU'
$env:BQ_DEV_DATASET = 'sncf_dev'
$env:DBT_PROFILES_DIR = Join-Path $env:LOCALAPPDATA 'SNCF_Service_Reliability_Analytics\dbt-profile'
& "$env:UV_PROJECT_ENVIRONMENT\Scripts\python.exe" scripts/run_dbt.py parse --project-dir dbt --profiles-dir $env:DBT_PROFILES_DIR --no-partial-parse
& "$env:UV_PROJECT_ENVIRONMENT\Scripts\python.exe" scripts/check_bigquery.py --execute
& "$env:UV_PROJECT_ENVIRONMENT\Scripts\python.exe" scripts/run_dbt.py debug --project-dir dbt --profiles-dir $env:DBT_PROFILES_DIR
& "$env:UV_PROJECT_ENVIRONMENT\Scripts\python.exe" scripts/run_dbt.py run --project-dir dbt --profiles-dir $env:DBT_PROFILES_DIR --select j02_connection_check
```

Le bootstrap a été exécuté une fois avec `bq --project_id=sncf-reliability-analytics --location=EU query --use_legacy_sql=false --maximum_bytes_billed=100000000`, en transmettant le contenu de `infra/bootstrap.sql` après remplacement de `PROJECT_ID`. `CREATE SCHEMA IF NOT EXISTS` rend sa relance sans duplication, mais les requêtes cloud ci-dessus peuvent générer un coût et ne doivent pas être rejouées sans besoin. La vérification Power BI est terminée. Aucun PBIX n'a été enregistré ni publié : la copie Import testée est dans la session Desktop ouverte, et les deux captures ci-dessus conservent la preuve hors Git.

## Définitions, risques et apprentissage

Un verrou fixe la résolution des dépendances ; il ne garantit pas à lui seul un compte cloud fonctionnel. ADC fournit des identifiants à la bibliothèque Python ; le profil dbt décrit une connexion distincte. Un dataset est un conteneur cloud, sans rapport avec le dossier local. L'alerte budgétaire avertit, le quota restreint l'usage avec ses limites, et `maximum_bytes_billed` borne une requête. Une table d'essai valide une chaîne technique, pas le sens des effectifs SNCF.

Risques encore ouverts : absence de quota quotidien personnalisé et coût final encore soumis au délai des relevés de facturation. La facturation est active sous l'essai gratuit, pas sous un compte payant demandé. L'import Power BI a été vérifié sur une ligne, mais les paramètres avancés saisis par le porteur ne sont pas relus automatiquement après connexion ; leur valeur `false` pour Storage est confirmée par sa saisie, pas par une capture indépendante. La copie dans Desktop n'est pas conservée dans un PBIX et disparaîtra à la fermeture du rapport non enregistré. Les captures de preuve restent locales sur ce PC et ne constituent pas un livrable public. Les droits ont été prouvés fonctionnellement avec le compte créateur ; une identité de travail à privilèges réduits sera utile lors de l'automatisation, sans être créée à J02. Ne pas présenter `P−A` comme circulation assurée certifiée, convertir les causes en volumes ou corriger les anomalies >30 du T1 2025 ; J02 n'apporte aucune preuve nouvelle sur ces sujets.

Question d'entretien : « Pourquoi un `dbt parse` réussi ne démontre-t-il pas que Power BI peut lire les données ? » Parce que le parsage est local, tandis que la création d'une vue, sa lecture par une autre application et l'import sont trois opérations distinctes. Autre question : « Une alerte de 1 € bloque-t-elle les dépenses ? » Non, une alerte classique signale un seuil ; les quotas et limites de requête sont des contrôles différents.

Approfondissements possibles, hors J02 : identité dédiée sans clé locale pour l'automatisation (droits et CI nécessaires), Infrastructure as Code pour les ressources (maintenance supplémentaire), et archive cloud indépendante (stockage et gouvernance additionnels). Aucun de ces travaux n'est commencé.
