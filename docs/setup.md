# Installation, connexions, ingestion, qualité et modèle — J02–J05

## Qualification J05

Accord explicite reçu le 9 octobre 2026 : « Ok tu peux implémenter », après la
présentation complète J05. Réutiliser l'environnement verrouillé et le profil privé.
Aucun paquet supplémentaire n'est requis. Le projet dbt passe à 0.5.0 ; le paquet
Python d'ingestion reste 0.3.0. La version de projet dbt n'est pas une release Git.

Depuis la racine du dépôt SNCF, dans PowerShell :

```powershell
$taskRoot = Join-Path $env:LOCALAPPDATA 'SNCF_Service_Reliability_Analytics'
$taskPython = Join-Path $taskRoot 'venv-j02\Scripts\python.exe'
$taskSnapshot = Join-Path $taskRoot 'data\ingestion\20261007T130103249967Z_bce4ef24'
$env:GOOGLE_CLOUD_PROJECT = 'sncf-reliability-analytics'
$env:BQ_LOCATION = 'EU'
$env:BQ_DEV_DATASET = 'sncf_dev'
$env:BQ_RAW_DATASET = 'sncf_dev'
$env:DBT_PROFILES_DIR = Join-Path $taskRoot 'dbt-profile'
& $taskPython scripts/validate_data_model.py --execute --project $env:GOOGLE_CLOUD_PROJECT --snapshot $taskSnapshot
```

Si `SNCF_DATA_DIR` est configuré, employer le chemin réel de l'archive conservée.
Le collecteur vérifie export/manifeste et les payloads de la table brute figée.
Il crée les vues J04, contrôle J04, crée les huit tables J05, contrôle J05, inspecte
schémas et types d'objets, puis exécute trois requêtes de preuves. L'ordre évite de
qualifier un modèle dont les prérequis ont échoué. Les tests J04 utilisent désormais
`--indirect-selection cautious` pour ne pas entraîner les tests de réconciliation
J05 avant que leurs autres dépendances soient construites. Cette correction est
aussi appliquée au collecteur autonome J04 ; les anciennes preuves restent intactes.

La table brute et `expected_version_id` sont fixées depuis le manifeste, sans
extraction ni promotion de la source courante. Les seuils et fenêtres sont dans
`dbt/dbt_project.yml` ; modifier leur contrat exige une décision tracée. Les sources
plus récentes ne déplacent pas automatiquement les comparaisons.

Chaque tentative conserve `validation.json`, logs, SQL compilé, manifeste dbt et
résultats par étape dans `SNCF_DATA_DIR/model_runs/<run_id>`, hors OneDrive. Seule
une qualification réussie met à jour les preuves ciblées de
`reports/data_model_evidence/`. Aucune purge ni export complet de l'entrepôt.
Les tests unitaires sont exécutés par BigQuery sur des données synthétiques ; ils
ne constituent pas une exécution locale hors cloud. La limite de 100 MB s'applique
par requête, pas à la somme des requêtes. Consulter les jobs et la consommation.

Tests Python de non-régression :

```powershell
& $taskPython -m unittest discover -s tests -v
```

Après contrôle des résultats et de la documentation, préparer les copies publiques :

```powershell
& $taskPython scripts/prepare_publication.py
& $taskPython scripts/prepare_publication.py --check
```

Le script couvre désormais J01, J03, J04 et J05. Il exige les originaux locaux des
quatre groupes ; sur un nouveau clone, les récupérer pour reproduire les copies
historiques. Ne pas rejouer une qualification simplement pour les publier.
Les fichiers publics et leur manifeste sont dans `reports/publication_evidence/`.
La préparation de copies ne renouvelle pas les preuves de validation.

## Qualification J04

L'accord explicite du 8 octobre 2026 couvre J04. Réutiliser l'environnement verrouillé
et le profil privé existants, sans paquet supplémentaire. Le projet dbt est décrit
en version 0.4.0, sans constituer une release Git ; le paquet d'ingestion reste 0.3.0.

```powershell
$taskRoot = Join-Path $env:LOCALAPPDATA 'SNCF_Service_Reliability_Analytics'
$taskPython = Join-Path $taskRoot 'venv-j02\Scripts\python.exe'
$taskSnapshot = Join-Path $taskRoot 'data\ingestion\20261007T130103249967Z_bce4ef24'
$env:GOOGLE_CLOUD_PROJECT = 'sncf-reliability-analytics'
$env:BQ_LOCATION = 'EU'
$env:BQ_DEV_DATASET = 'sncf_dev'
$env:BQ_RAW_DATASET = 'sncf_dev'
$env:DBT_PROFILES_DIR = Join-Path $taskRoot 'dbt-profile'
& $taskPython scripts/validate_data_quality.py --execute --project $env:GOOGLE_CLOUD_PROJECT --snapshot $taskSnapshot
```

Cette commande vérifie entièrement le brut contre l'archive J03, crée les deux vues
J04, exécute les tests de données et les tests unitaires dans BigQuery, compile les
requêtes de contrôle puis conserve leurs résultats. Elle ne télécharge pas une
nouvelle source, ne promeut pas de version brute et ne construit aucun mart J05.
Les commandes dbt ciblent `tag:j04` : la vue technique J02 n'est pas reconstruite.

La source est figée par `raw_tgv_identifier` sur la table du manifeste ;
`expected_version_id` en contrôle l'identité. Le défaut du projet dbt,
`raw_tgv_current`, reste disponible pour un usage courant explicite. Un simple
`dbt run` sans les variables de qualification peut changer la référence des vues :
il ne faut pas le confondre avec un rejeu figé. Après chaque changement de source,
relancer la qualification et ne pas réutiliser ses anciennes preuves. Les vues J04
de cette livraison référencent la table figée J03.

Chaque exécution garde logs, SQL compilé, résultats dbt et validation sous
`SNCF_DATA_DIR\quality_runs\<run_id>`, hors OneDrive. Les échecs sont conservés.
`reports/data_quality_evidence/` reçoit les dernières preuves réussies, sans export
complet ; un échec ne les remplace pas. Son `validation.json` porte la date réelle
de qualification et les empreintes du code. Il est distinct des validations J01/J03.

Le profil doit limiter chaque requête à au plus 100 MB ; ce n'est pas un plafond
cumulé. Les tests unitaires utilisent des entrées statiques dans des requêtes
BigQuery, sans insérer ces lignes dans les vues métier. Les appels cloud peuvent
consommer des crédits. Les caches historiques de J02 et les premiers essais J04
dans `dbt/target/` et `dbt/logs/` restent ignorés par Git ; `.gitignore` ne coupe pas
OneDrive. La commande ci-dessus externalise ses nouveaux artefacts de qualification.

Voir [le rapport de qualité](../reports/data_quality.md) et [le bilan J04](milestones/J04_handoff.md).

## Référence d'installation J02–J03

J03 ajoute l'ingestion et déclare PyYAML 6.0.3 explicitement. Le verrou reste à 106 paquets (105 dépendances externes). Après mise à jour du dépôt, reprendre `uv sync --locked` avec l'environnement externe ci-dessous ; consulter [les commandes d'ingestion](ingestion.md#commandes-de-reproduction). Le nom historique `venv-j02` est conservé pour réutiliser cet environnement, désormais employé aussi à J03. La branche de travail J03 est `codex/j03-ingestion`.

Cette procédure prépare les outils ; les résultats réellement obtenus figurent dans [le bilan J02](milestones/J02_handoff.md). Les paramètres en majuscules ci-dessous sont des exemples, jamais des identifiants à réutiliser tels quels.

## 1. Préparer Git et Python

Le dossier SNCF possède son propre dépôt Git, désormais sur la branche `codex/j03-ingestion` (J02 utilisait `codex/j02-environment`). Le dépôt parent `DATA PORTFOLIO` contient d'autres projets : toujours vérifier `git rev-parse --show-toplevel` avant un ajout ou un commit. Aucun commit ni publication n'est requis pour installer l'environnement.

Installer Python 3.13 et `uv` 0.12.21. Dans PowerShell, depuis le dossier SNCF :

```powershell
python -m pip install --user uv==0.12.21
$env:UV_PROJECT_ENVIRONMENT = Join-Path $env:LOCALAPPDATA 'SNCF_Service_Reliability_Analytics\venv-j02'
python -m uv sync --locked
& "$env:UV_PROJECT_ENVIRONMENT\Scripts\python.exe" --version
& "$env:UV_PROJECT_ENVIRONMENT\Scripts\python.exe" scripts/run_dbt.py --version
```

`pyproject.toml` fixe les dépendances directes et `uv.lock` leurs dépendances transitives. `--locked` refuse une installation incohérente avec le verrou. L'environnement est placé hors OneDrive ; ni lui ni le cache `uv` ne sont ajoutés à Git. Sur un autre poste Windows, employer un chemin local équivalent. `scripts/profile_source.py` de J01 reste exécutable avec la bibliothèque standard Python, indépendamment de cet environnement.

## 2. Préparer Google Cloud et maîtriser la consommation

Il faut un projet Google Cloud dédié, une facturation activée pour la cible durable, BigQuery activé, et un compte autorisé à gérer les datasets. Vérifier le projet et la facturation dans la console avant de lancer une écriture. La localisation retenue pour J02 est `EU` pour tous les datasets et jobs : un choix différent exige une modification cohérente de `infra/bootstrap.sql`, du profil dbt et du contrôle Python, puis une nouvelle vérification.

Un budget mensuel d'alerte de **1 € de consommation brute**, ciblé sur le projet SNCF et excluant crédits et remises du calcul, a été appliqué avec seuils à 50 %, 90 % et 100 %. Il avertit donc aussi lorsque les crédits d'essai absorbent le coût. Une **alerte classique n'arrête pas les services**. Le quota BigQuery `Query usage per day` était affiché, mais l'action « Modifier le quota » était désactivée dans la console sur ce compte le 5 octobre 2026 : aucun quota personnalisé ne doit être considéré comme appliqué. `maximum_bytes_billed=100000000` dans les requêtes Python et le profil dbt fait échouer une requête dont l'estimation dépasse 100 MB. Examiner la facturation et la consommation après chaque essai ; ces limites ne garantissent pas une dépense nulle. L'essai gratuit du compte annonce 264 € de crédits, sans passage demandé à un compte payant.

Créer les quatre datasets à l'aide de `infra/bootstrap.sql` après remplacement de `PROJECT_ID`. `sncf_dev` reçoit les essais et futurs modèles de développement ; `sncf_test` expire par défaut les **tables transitoires** après sept jours ; `sncf_publish` accueille une version figée future ; `sncf_audit` conserve les traces de chargement futures. Aucune expiration par défaut n'est imposée aux archives brutes, aux tables publiées ou aux journaux. Le contrôle Python crée sa propre table d'essai dans `sncf_dev` avec une expiration de sept jours. Ne pas supprimer automatiquement les exports et manifestes J01.

Le compte de création doit disposer de `bigquery.datasets.create` et de `bigquery.jobs.create` sur le projet. Pour les essais courants, séparer les droits : `roles/bigquery.jobUser` sur le projet pour lancer des jobs, `roles/bigquery.dataEditor` seulement sur `sncf_dev` pour Python/dbt, et `roles/bigquery.dataViewer` sur le dataset consulté par Power BI. Le connecteur Power BI peut demander des droits supplémentaires pour l'API BigQuery Storage ; accorder le droit précis après l'erreur observée, plutôt qu'un rôle administrateur global. Documenter les identités et autorisations effectives sans enregistrer leurs secrets.

## 3. Authentifier Python et dbt localement

Installer Google Cloud CLI depuis sa documentation officielle. Dans une session privée, se connecter avec le compte autorisé :

```powershell
gcloud auth login
gcloud auth application-default login
gcloud config set project PROJECT_ID
$env:GOOGLE_CLOUD_PROJECT = 'PROJECT_ID'
$env:BQ_LOCATION = 'EU'
$env:BQ_DEV_DATASET = 'sncf_dev'
```

Le premier accès sert à la CLI et au profil dbt `method: oauth` ; le second fournit les Application Default Credentials (ADC) à la bibliothèque Python. Les fichiers de jetons restent dans le profil utilisateur, jamais dans le dépôt. Une identité de service sans clé locale pourra être étudiée pour l'automatisation à J09.

Copier `dbt/profiles.yml.example` vers un dossier privé hors OneDrive et définir `DBT_PROFILES_DIR` sur ce dossier. Ne pas copier le profil réel dans Git. Exemple :

```powershell
$env:DBT_PROFILES_DIR = Join-Path $env:LOCALAPPDATA 'SNCF_Service_Reliability_Analytics\dbt-profile'
New-Item -ItemType Directory -Force -Path $env:DBT_PROFILES_DIR | Out-Null
Copy-Item dbt/profiles.yml.example (Join-Path $env:DBT_PROFILES_DIR 'profiles.yml')
```

## 4. Vérifier les connexions

Le premier appel vérifie la configuration locale, sans contacter Google ; le second crée une table d'essai de **une ligne**, la relit et affiche les identifiants des deux jobs BigQuery :

```powershell
& "$env:UV_PROJECT_ENVIRONMENT\Scripts\python.exe" scripts/check_bigquery.py
& "$env:UV_PROJECT_ENVIRONMENT\Scripts\python.exe" scripts/check_bigquery.py --execute
& "$env:UV_PROJECT_ENVIRONMENT\Scripts\python.exe" scripts/run_dbt.py debug --project-dir dbt
& "$env:UV_PROJECT_ENVIRONMENT\Scripts\python.exe" scripts/run_dbt.py run --project-dir dbt --select j02_connection_check
```

La vue dbt `j02_connection_check` confirme l'exécution d'un modèle, sans transformation métier. Un `dbt debug` réussi seul vérifie la connexion, mais pas la création d'un objet. Si une commande échoue, relever l'étape et le message expurgé de tout secret ; ne pas transformer cet échec en « test réussi ».

Pour le contrôle J02 dans **Power BI Desktop**, choisir **Obtenir des données → Base de données → Google BigQuery** (sans la variante Microsoft Entra ID), puis ouvrir les options avancées. Saisir `sncf-reliability-analytics` dans **ID de projet de facturation** et **ID de projet**, puis `false` dans **Utiliser l'API de stockage** (une ligne n'en a pas besoin). Valider, puis utiliser le compte Google qui a accès au projet. Le titulaire doit examiner l'autorisation Google avant de l'accorder. Dans le navigateur de données, sélectionner `sncf_dev.j02_python_connection_check`, choisir **Importer** et charger. Vérifier que la ligne `(1, J02)` est visible, que les types sont entier et texte, et noter la date de l'import. Cette copie Import est locale à Power BI Desktop ; elle ne prouve pas une publication ni un partage.

Le premier essai dans Power BI web sur Brave a été interrompu par deux fermetures du navigateur lors de la connexion Google. Power BI Desktop 2.158.1177.0 est installé et le connecteur y est accessible. Si un fichier PBIX en mode Import est enregistré, il contient les données et doit rester hors Git et hors du dépôt OneDrive. `.gitignore` ne désactive pas OneDrive.

## 5. Stockage local

`SNCF_DATA_DIR` est facultatif. Son défaut est `%LOCALAPPDATA%\SNCF_Service_Reliability_Analytics\data`, hors du dépôt OneDrive. Le dossier J01 déjà capturé ne se déplace pas automatiquement si cette variable change. Conserver l'export, ses métadonnées, son manifeste et ses empreintes, ainsi que les traces d'échec. Les CSV de `reports/audit_evidence/` sont des résultats de contrôle, pas l'export source complet. Le fichier `validation.json` de J01 ne se renouvelle pas par un simple reprofilage.

## Références de configuration

- [Authentification des bibliothèques Google Cloud](https://docs.cloud.google.com/docs/authentication/client-libraries)
- [Connexion dbt à BigQuery](https://docs.getdbt.com/docs/local/connect-data-platform/bigquery-setup?version=1.12)
- [Création de datasets BigQuery en SQL](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language)
- [Budgets et alertes](https://docs.cloud.google.com/billing/docs/how-to/budgets)
- [Quotas personnalisés](https://docs.cloud.google.com/bigquery/docs/custom-quotas)
- [Limite par requête](https://docs.cloud.google.com/bigquery/docs/best-practices-costs)
- [Connecteur Google BigQuery pour Power BI](https://learn.microsoft.com/en-us/power-query/connectors/google-bigquery)
- [Créer dans Power BI web avec une licence gratuite](https://learn.microsoft.com/en-us/power-bi/fundamentals/service-get-started)
