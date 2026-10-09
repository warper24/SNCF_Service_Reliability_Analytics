# Architecture technique et emplacements — J02–J04

## Mise en œuvre J04

Le SQL/dbt s'exécute dans BigQuery `EU`, piloté depuis le PC. Deux vues classiques
dans `sncf_dev` exposent la préparation : `stg_tgv_reliability` extrait les 26 champs
du JSON et applique les noms et types du contrat ; `int_tgv_quality_flags` conserve
toutes ses colonnes et ajoute populations déduites, statuts et motifs de qualité.
Les données complètes ne sont pas exportées localement après transformation.

```text
Archive J03 + manifeste hors OneDrive
              ↕ vérification complète des payloads
BigQuery : raw_tgv_v_<version_id> (table brute)
              ↓ source dbt configurable, figée pour la qualification
BigQuery : stg_tgv_reliability (vue)
              ↓ ref() dbt
BigQuery : int_tgv_quality_flags (vue)
              ↓ tests et requêtes de contrôle BigQuery
Preuves ciblées + rapport de qualité dans le dépôt
```

Une vue stocke sa requête ; consulter les données exécute cette définition. La
qualification fige l'entrée sur la version J03 vérifiée ; le défaut
`raw_tgv_current` permet une actualisation volontaire. `version_id`, `row_number`,
`row_sha256` et `raw_payload` relient le résultat au brut. Le premier jour du mois
représente un mois, sans grain journalier inventé. Gares et services ne sont pas fusionnés.

Le document JSON typé sert au contrôle de structure avec `wide_number_mode='round'` :
BigQuery refusait en mode exact 138 payloads comportant des décimaux non round-trip.
Les valeurs sont extraites directement du texte brut puis converties en `INT64`,
`FLOAT64`, `DATE` ou `STRING`. Les effectifs restent entiers ; les doubles SQL ont
la précision FLOAT64 et le texte d'origine demeure intact. Les conversions invalides
et champs absents du schéma sont distincts des valeurs JSON nulles.

Les statuts séparent effectifs et ratios, annulations, retards arrivée, couple >30/>60,
moyennes et profils publiés de causes. Ils ne calculent pas les taux ou classements.
D01 demeure non certifiée ; quarantaine T1 2025 et réserves D02–D07 sont maintenues.
Un profil hors tolérance de somme reste consultable avec avertissement, sans
renormalisation, conversion en effectifs ou agrégation.

Les preuves ciblées sont dans `reports/data_quality_evidence/`. Chaque qualification,
y compris échouée, est conservée hors OneDrive sous `SNCF_DATA_DIR\quality_runs`.
`sncf_publish`, Power BI et les tables analytiques J05 ne sont pas modifiés à J04.
Voir [les commandes](setup.md#qualification-j04), [le rapport](../reports/data_quality.md)
et [le bilan](milestones/J04_handoff.md).

## Mise en œuvre J03

L'ingestion est désormais implémentée ; ses résultats de validation sont dans [le bilan J03](milestones/J03_handoff.md). Une table `sncf_dev.raw_tgv_v_<version_id>` conserve chaque contenu brut chargé. Elle contient un texte JSON `payload` par observation, avec noms SNCF et valeurs inchangées, plus version, numéro technique et empreinte. `sncf_dev.raw_tgv_current` pointe vers une seule version vérifiée. `sncf_audit.raw_tgv_load_events` conserve les événements des tentatives et le lien vers les manifestes. L'archive locale exacte et le fichier de chargement restent sous `SNCF_DATA_DIR`, hors dépôt et OneDrive, sans purge automatique.

Les contrôles synthétiques J03 créent des objets préfixés `j03_check_` uniquement dans `sncf_test`, qui expire les tables après sept jours. Les versions réelles et le journal réel n'ont pas d'expiration automatique. Aucun objet de publication ni modèle métier n'est créé dans `sncf_publish`. La table brute JSON facilite la conservation fidèle ; J04 extrait et type désormais les champs conformément au contrat. Détails, limites de cohérence source, reprise et alternatives dans [la documentation d'ingestion](ingestion.md).

## Référence historique J02 et architecture cible

```text
API SNCF → Python sur le PC → export + manifeste sous SNCF_DATA_DIR
                              ↓ à J03
                       BigQuery sncf_dev (brut)
                              ↓ SQL/dbt exécuté par BigQuery à J04–J05
                       BigQuery sncf_dev (vues et tables analytiques)
                              ↓ publication figée future
                       BigQuery sncf_publish → Power BI Desktop (copie Import)
```

À J02, une table Python et une vue dbt d'essai ont été créées dans `sncf_dev`. Elles ne contiennent pas les observations SNCF. `sncf_test` sert aux contrôles transitoires, `sncf_audit` aux traces de chargement futures et `sncf_publish` à la version utilisée par le rapport final. Les zones brute, analytique et audit restent distinctes par convention de tables et de responsabilités ; leur structure détaillée sera arrêtée pendant J03–J05. Les versions brutes ne seront pas additionnées comme des observations supplémentaires.

| Élément | Emplacement | Producteur et utilisateur | Conservation |
|---|---|---|---|
| Code, configuration exemple et documentation | Dépôt SNCF sous OneDrive, puis Git | Développeur ; toutes les étapes | Versionnés sans secret |
| Export brut J01, métadonnées, manifeste | `%LOCALAPPDATA%\SNCF_Service_Reliability_Analytics\data` par défaut | Python ; audit et rejeu | Pas de purge automatique ; copie locale sans sauvegarde indépendante |
| Environnement Python et profil dbt réel | `%LOCALAPPDATA%`, hors dépôt | `uv` et utilisateur ; Python/dbt | Recréables, mais jetons privés |
| Données et jobs BigQuery | Cloud Google, localisation `EU` vérifiée | Python charge ; dbt envoie du SQL ; BigQuery exécute | Datasets durables sauf tables transitoires explicites |
| Copie Import d'essai J02 | Session Power BI Desktop sur le PC, import vérifié le 5 octobre 2026 | Connecteur BigQuery ; analyste | Une seule ligne technique ; session non enregistrée en PBIX, preuves privées sous `%LOCALAPPDATA%` |
| Modèle Import cible J07 | PC, dans Power BI Desktop | Connecteur BigQuery ; analyste | Copie actualisable ; cache et PBIX hors Git |

`SNCF_DATA_DIR` peut remplacer le chemin local par défaut. Un chemin sous OneDrive serait contraire au choix de stockage des exports. Le rapport Power BI Import ne sollicite pas BigQuery à chaque clic : seule son actualisation importe une nouvelle copie. Le premier essai J02 dans Brave, demandé pour laisser le PC disponible, a échoué par deux fermetures du navigateur à l'étape de connexion Google. Le contrôle a été achevé dans Power BI Desktop à la demande du porteur du projet. La ligne d'essai y a été importée dans la session ouverte ; aucun PBIX n'a été enregistré. Le rapport métier et sa publication restent au jalon prévu.

Le projet Google Cloud dédié réduit les risques de mélanger coûts et permissions avec d'autres projets. La localisation commune évite les conflits de jobs et de datasets. `sncf_dev` autorise les écritures contrôlées ; `sncf_publish` vise une lecture stable du rapport. Le droit de créer des jobs se donne au projet, l'édition ou la lecture des données au dataset concerné. Le compte personnel qui a créé les ressources possède actuellement les droits nécessaires ; aucune identité de service ni délégation supplémentaire n'a été créée à J02. Le budget mensuel de 1 € de consommation brute est une notification. La limite de 100 MB par requête est appliquée dans les essais Python et le profil dbt. Le quota quotidien personnalisé a été recherché, mais sa modification était désactivée dans la console : il n'est pas présenté comme un contrôle actif.

Les conventions métier de [J01](data_contract.md) restent le contrat des jalons suivants : grain mois × départ × arrivée × service ; pas de total national reconstruit entre liaisons ; `P−A` demeure une population déduite et non certifiée ; causes publiées sans effectifs reconstruits ; absences et anomalies préservées. J02 ne calcule aucun KPI et ne lève aucune de ces réserves.
