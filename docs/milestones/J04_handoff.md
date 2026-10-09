# J04 — Normalisation et qualité avec dbt

**État : terminé avec limites explicites, le 8 octobre 2026.** Deux vues BigQuery

exposent les 12 907 observations J03, les 26 champs normalisés et les usages permis.

Seize tests de données bloquants et deux tests unitaires réussissent ; quatre

avertissements sont quantifiés et expliqués. Aucun travail J05 n'est engagé.

## Présentation, accord et périmètre accepté

La préparation a lu le plan, AGENTS, les bilans J02/J03, le contrat, les KPI, la charte,

le code réel, Git, les preuves et le manifeste. La présentation a détaillé objectif,

staging, typage, normalisation, vues, grain, null/zéro/mois absent, sévérité, étapes,

stockage, chaque famille de fichiers, décisions, alternatives, critères, risques,

extensions et entretien. Le protocole de pause a été respecté ; les relances

automatiques de l'objectif n'ont pas été interprétées comme une autorisation.

Accord explicite reçu : **« J’autorise l’implémentation de J04 »**. Il couvre les vues,

tests, requêtes de preuves, collecteur, rapport et transmission présentés. La branche

`codex/j04-quality` a été créée dans le dépôt SNCF isolé ; les fichiers préexistants

non suivis ont été préservés. Aucun commit, remote, push, PR ou publication n'a été créé.

L'objectif métier est d'éviter qu'une analyse techniquement correcte exploite une

population incohérente. Le résultat technique est une préparation SQL traçable,

sans correction arbitraire du brut. Les transformations restent SQL/dbt ; Python

vérifie le transport et rassemble les preuves.

Les compléments ordinaires de validation sont deux analyses supplémentaires,

`j04_period_coverage.sql` et `j04_manual_cases.sql` : elles prouvent le maintien des

fenêtres J01 et matérialisent les cas de revue humaine. Elles ne calculent pas de

taux ou classement et ne constituent pas les marts J05.

## Résultat et déroulement

1. Vérification de la connexion, des datasets EU et de la référence courante J03 ;

   versions installées conformes au verrou.

2. Déclaration de la source dbt configurable, avec qualification sur la table brute

   figée du manifeste et contrôle de son `version_id`.

3. Création de `stg_tgv_reliability` : extraction de 26 champs, conversion contrôlée,

   noms contractuels et provenance complète. Aucune fusion de gare ou service.

4. Création de `int_tgv_quality_flags` : effectifs source intacts, population proxy

   encadrée, usages distincts et motifs de qualité cumulables.

5. Premiers tests : détection d'un défaut de notre parsing JSON sur 138 payloads.

   Diagnostic, correction et test unitaire de régression ; aucune source modifiée.

6. Qualification complète : relecture des 12 907 payloads, création des vues, tests

   BigQuery, vérification des types réels et cinq requêtes de preuves.

7. Revue de huit cas réels, contrôle de la couverture, documentation et revue Git.

Le [rapport de qualité](../../reports/data_quality.md) donne les résultats détaillés.

73 observations sont indisponibles pour chacun des taux centraux ; 443 pour les taux

du couple >30/>60. 272 profils de causes sont entièrement nuls ; dix profils non nuls

ont une somme hors tolérance. Les 146 combinaisons liaison/service gardent 88 trous

internes sur dix combinaisons. Les contrôles des fenêtres J01 retrouvent 102/116

combinaisons nationales admissibles au semestre et 88/116 à l'année, sans classement.

## Définitions et circulation des données

- **dbt (data build tool)** organise modèles SQL, dépendances, tests et documentation.

  Le PC soumet les requêtes ; BigQuery exécute le SQL.

- **Staging** : couche de correspondance entre JSON source et champs typés.

- **Normalisation** : conventions techniques communes, sans assimilation de populations.

- **Typage** : INT64 pour les effectifs, FLOAT64 pour moyennes/parts, STRING pour

  libellés/commentaires et DATE au premier jour pour le mois.

- **Vue classique** : définition SQL enregistrée, sans copie persistante de son résultat.

  Une consultation peut scanner les tables sous-jacentes.

- **Grain et clé candidate** : mois × gare de départ × gare d'arrivée × service.

  Deux directions ou deux services ne sont pas fusionnés.

- **Test de données** : SELECT des lignes contredisant une assertion ; zéro résultat

  vaut normalement réussite. **Test unitaire** : entrées statiques et sorties attendues

  pour vérifier les branches du SQL.

- **Sévérité** : erreur bloquante pour structure/fidélité/usages incorrects ;

  avertissement pour défauts source détectés et encadrés.

- **Couverture** : présence des observations et disponibilité par indicateur,

  distinctes. Un champ null, zéro et un mois absent sont trois situations différentes.

Exemple : le mois source `2025-01` devient DATE `2025-01-01` ; cela ne crée aucune

observation journalière. Pour P=100, A=10 et L=18, le proxy vaut 90, mais sa validité

arithmétique ne certifie pas la définition officielle de population. Si P=A=L=0,

l'effectif nul reste disponible et le futur taux sera indisponible.

Les exports et manifestes J03 restent hors OneDrive. BigQuery garde le brut et

exécute les vues. Le dépôt conserve SQL/YAML, documentation et preuves ciblées.

Chaque qualification garde logs, manifest dbt, résultats, SQL compilé et erreurs

dans `SNCF_DATA_DIR/quality_runs/<run_id>`, sans purge.

## Décisions et alternatives

| Choix | Besoin, compromis et limite |

|---|---|

| BigQuery EU conservé | Entrepôt confirmé et connecté ; pas de seconde plateforme |

| Source figée pour qualification | Reproduction et absence de mélange de versions ; actualisation volontaire ultérieure |

| Source courante configurable | Prépare le rejeu d'une nouvelle version ; un run sans variables peut changer la référence |

| Vues staging/intermediate | Préparation lisible et conforme au plan ; consultations recalculées, coût à surveiller |

| Extraction directe du STRING JSON | Évite une sérialisation numérique intermédiaire ; brut conservé |

| PARSE_JSON de structure en mode round | Accepte les décimaux non round-trip ; valeurs analytiques en FLOAT64, précision finie |

| Aucun renommage de gare inventé | Pas d'identifiant stable prouvant une correspondance ; aucun seed inutile |

| Usages par indicateur | Une anomalie >30 ne supprime pas l'effectif central ; davantage de statuts à documenter |

| D01 maintenue | P−A est un proxy contrôlé, pas une population certifiée |

| Causes publiées uniquement | Absence de dénominateur traçable ; pas d'effectifs ou d'agrégations |

| Tolérance de somme 0,1 point + garde 1e-9 | Diagnostic du contrat et gestion de frontière FLOAT64 ; aucune renormalisation |

| Tests natifs et SQL spécifiques | Aucun paquet ajouté ; les assertions métier restent inspectables |

| Collecteur Python limité aux preuves | Pas de deuxième implémentation des transformations métier |

Pandas aurait facilité une exploration locale, avec risque de deuxième chaîne métier.

Des tables de préparation limiteraient les recalculs, mais stockeraient des copies

supplémentaires ; aucune mesure ne justifie ce changement. Un drapeau global de ligne

valide serait simple, mais perdrait des usages légitimes. Une suppression ou correction

automatique des anomalies ferait disparaître la preuve. Un référentiel officiel de

gares serait utile après acquisition de clés fiables. Aucun de ces ajouts n'est engagé.

## Fichiers, fonctions et utilisateurs

| Fichier | Nature et fonction ; producteur → utilisateur |

|---|---|

| `dbt/dbt_project.yml` | Configuration 0.4.0, vues, tags et variables ; développeur → dbt |

| `dbt/models/staging/sources.yml` | Source brute configurable ; développeur → dbt et mainteneur |

| `dbt/models/staging/stg_tgv_reliability.sql` | Code de typage et provenance ; développeur → BigQuery et intermediate |

| `dbt/models/staging/stg_tgv_reliability.yml` | Descriptions des 26 champs, types et tests génériques ; développeur → dbt/lecteur |

| `dbt/models/intermediate/int_tgv_quality_flags.sql` | Code des populations et statuts D01–D07 ; développeur → BigQuery/J05 |

| `dbt/models/intermediate/int_tgv_quality_flags.yml` | Documentation des statuts et types ; développeur → dbt/mainteneur |

| `dbt/models/intermediate/j04_unit_tests.yml` | 39 observations de fixture et attentes ; développeur → tests dbt |

| `dbt/tests/assert_source_integrity.sql` | JSON, conversions, champs attendus et provenance ; développeur → test bloquant |

| `dbt/tests/assert_source_version.sql` | Source non vide, version unique/attendue ; développeur → test bloquant |

| `dbt/tests/assert_monthly_grain.sql` | Clé composite unique, libellés non vides, convention du mois ; développeur → test bloquant |

| `dbt/tests/assert_staging_fidelity.sql` | Correspondance complète brut/staging ; développeur → test bloquant |

| `dbt/tests/assert_intermediate_fidelity.sql` | Toutes les colonnes staging intactes ; développeur → test bloquant |

| `dbt/tests/assert_quality_usability.sql` | Aucune utilisation incompatible et booléens définis ; développeur → test bloquant |

| `dbt/tests/warn_source_counts.sql` | Effectifs et relations atypiques ; développeur → avertissement |

| `dbt/tests/warn_cause_profiles.sql` | Profils non disponibles ou hors somme ; développeur → avertissement |

| `dbt/tests/warn_signed_means.sql` | Moyennes/durée négatives ; développeur → avertissement |

| `dbt/tests/warn_service_scope.sql` | Plusieurs services simultanés ; développeur → avertissement |

| `dbt/analyses/j04_quality_summary.sql` | Décomptes par règle et indicateur ; développeur → collecteur/rapport |

| `dbt/analyses/j04_coverage.sql` | Couverture par liaison/service et trous internes ; développeur → collecteur/rapport |

| `dbt/analyses/j04_anomaly_examples.sql` | Jusqu'à 100 exemples de contrôle ; développeur → revue |

| `dbt/analyses/j04_period_coverage.sql` | Fenêtres J01, complétude, seuil et service ; développeur → contrôle de couverture |

| `dbt/analyses/j04_manual_cases.sql` | Huit cas réels déterministes ; développeur → revue humaine |

| `scripts/validate_data_quality.py` | Vérification du brut, pilotage dbt, schémas et collecte ; développeur → opérateur |

| `reports/data_quality_evidence/` | Validation, logs, synthèse, couverture, cas et revue Git ; outils/revue → lecteur |

| `reports/data_quality.md` | Résultats, restrictions et limites ; développeur → analyste/lecteur |

| `docs/setup.md`, `docs/architecture.md` | Commandes et circulation réelle ; développeur → mainteneur |

| `PLAN.md`, ce bilan | État, décisions et transmission ; développeur → porteur/J05 |

Aucun `station_name_mapping.csv` : condition non démontrée. Aucun export complet,

environnement, jeton ou profil réel ajouté à Git. `.gitignore` ne coupe pas OneDrive ;

les caches des premiers essais sous dbt/target et dbt/logs sont ignorés, les nouveaux

artefacts de qualification sont externalisés.

## Critères exécutés, résultats et preuves

| Critère / risque couvert | Méthode et résultat attendu/obtenu | Preuve et sens d'un échec |

|---|---|---|

| Version source et transport | 12 907 payloads/empreintes/positions identiques à l'archive ; obtenu | `raw_verification` de validation ; écart interdit la qualification |

| Clés et types | Non-nullité, unicité composite et technique, mois strict, types réels conformes ; obtenu | Tests et schémas dans validation ; échec structurel bloquant |

| Fidélité des couches | Aucune ligne perdue/multipliée et colonnes intactes ; obtenu | Deux tests de fidélité ; échec = transformation incorrecte |

| Effectifs et populations | Anomalies détectées, aucun usage déclaré compatible à tort ; obtenu | Test usability, warning 425, 27 cas métier ; défaut source conservé, défaut de statut bloquant |

| Causes et tolérance | Nulls, zéros, bornes et somme distingués ; obtenu | Warning 282, tests de frontières, synthèse ; aucun dénominateur déduit |

| Exclusions et couverture | Volumes par usage, trous et fenêtres J01 mesurés ; obtenu | Cinq CSV et requêtes conservées ; échec rend la couverture non démontrée |

| Tests bloquants | 16 tests de données + deux unités réussis ; obtenu | `tests.txt` et validation ; aucun WARN reclassé arbitrairement |

| Revue manuelle | Huit cas réels examinés, notamment Dijon, zéro, moyenne négative et causes ; obtenu | `manual_cases.csv` et rapport ; revue ciblée distincte des tests exhaustifs |

| Non-régression et Git | 37 tests Python réussis, anciens modules/preuves intacts ; obtenu | Sortie de commande, revue d'empreintes/Git ; aucun commit revendiqué |

La [revue finale du dépôt](../../reports/publication_evidence/data_quality_evidence/git_review.json) confirme que seuls PLAN, la configuration dbt et les deux documents techniques ont changé parmi les 56 fichiers préexistants ; aucune suppression, aucun changement du code ou des preuves J01/J03. Les 88 fichiers ajoutables ne comprennent ni source complète, profil réel, environnement ou cache.

Les quatre warnings sont `warn_source_counts=425`, `warn_cause_profiles=282`,

`warn_signed_means=278`, `warn_service_scope=84`. Leurs populations se recouvrent.

Le compteur des motifs cumulés de la vue n'est pas un masque général de validité.

Les tests unitaires s'exécutent sur BigQuery avec entrées statiques ; ils ne prouvent

pas une exécution locale hors cloud. Les cas et données réelles sont complémentaires.

## Versions, jobs, reproduction

- Python 3.13.15 ; dbt Core 1.12.5 ; dbt-bigquery 1.12.1 ;

  google-cloud-bigquery 3.45.2. Verrou de J03 inchangé.

- Projet dbt 0.4.0 ; paquet Python d'ingestion 0.3.0 inchangé.

- Branche `codex/j04-quality` ; aucun commit ou publication.

- Qualification : `20261008T100405Z_b0a4b733` ; code identifié par SHA-256 dans

  [validation.json](../../reports/publication_evidence/data_quality_evidence/validation.json).

- Archive : `20261007T130103249967Z_bce4ef24` ; version canonique

  `e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6`.

- SHA-256 source : `8dc2b0a9a3707306c3087f899163465e34b20ed44b4dfc4ad46d5af4686334b2`.

- SHA-256 manifeste : `1cca3fcbf6e4a94343866eedec4badf35d1ef2961cac75550cc0d666ea03b5cd`.

- Objets réels : table brute `sncf_dev.raw_tgv_v_<version_id>`, deux vues J04 ;

  `raw_tgv_current` et journal J03 non modifiés.

- Relecture complète finale du brut : `sncf_j04_raw_7747a599b4784b99bb2e82a93ad290a2` ; zéro octet facturable observé grâce au cache.

- Les cinq jobs de contrôle, leurs octets et les jobs des tests figurent dans la validation.

- Répertoire externe final : `C:\Users\<utilisateur>\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\SNCF_Service_Reliability_Analytics\data\quality_runs\20261008T100405Z_b0a4b733`.

Reproduction complète : suivre [setup, qualification J04](../setup.md#qualification-j04).

La commande explicite `--execute` vérifie la version, recrée les vues, teste, compile

et rassemble les preuves. Elle peut consommer des crédits ; le profil limite chaque

requête à 100 MB, sans plafond cumulé ni facture finale vérifiée. Pour les tests

Python : `python -m unittest discover -s tests -v` avec l'interpréteur verrouillé.

Les logs et SQL compilés montrent le trajet : le fichier local utilise source()/ref(),

dbt résout les relations et produit SQL de création/contrôle, BigQuery exécute, puis

dbt et le collecteur conservent les résultats. Aucun export local systématique de

l'entrepôt n'est produit.

## Erreurs résolues et limites

Le parsing JSON exact refusait 138 payloads, dont un contenant 10.25641026 ; job

diagnostique `2a419a37-c1d0-4e5a-97d7-e4ab024d8984`. La solution préserve le texte

original et lit les valeurs directement, avec document de structure en mode round.

Les fausses clés nulles ont disparu. Un test de régression couvre ce nombre.

La première synthèse avait un alias de STRUCT ambigu, corrigé en `check_rule.rule` ;

job échoué `sncf_j04_e003274a104941fc884db62583476956`. La tentative

`20261008T120121_08b25492` et les premiers résultats de tests sont conservés hors

OneDrive. Aucun échec n'a été présenté comme réussite.

Les limites métier D01–D07 restent entières. Les moyennes FLOAT64 ont une précision

finie. Des tests arithmétiques ne certifient ni dénominateur, ni préavis d'annulation,

ni population des causes. Les trous de couverture ne démontrent pas une suppression

de desserte ; les services multiples ne démontrent pas des doublons.

Pas de nouvelle extraction, correction du brut, seed de gares, dimension/fait/mart,

calcul de taux de référence, classement, mesure DAX, actualisation Power BI,

automatisation, publication, ni reconstruction sur machine neuve. La sûreté de

publication multi-table et de reprise complète reste à J09. Les archives locales ne

sont pas une sauvegarde indépendante ; aucune purge n'est engagée.

## Transmission et bilan pédagogique

J05 pourra s'appuyer sur la version figée, les 26 champs et les statuts documentés

pour construire dimensions et faits, puis les calculs SQL de référence. Il devra

préserver le grain, les directions/services, les dénominateurs et les exclusions par

indicateur ; séparer les faits de causes pour éviter de multiplier les effectifs.

Les fenêtres et seuils J01 restent inchangés. J05 nécessite sa propre présentation

et son accord ; aucune implémentation anticipée.

À retenir : une source correctement transportée peut rester impropre à certains

usages ; une erreur technique de parsing peut imiter une absence métier ; null,

zéro et mois absent ne se remplacent pas ; un avertissement correctement encadré

peut coexister avec un jalon validé. Un jeu mensuel n'autorise ni total national

de trains distincts, ni inférence sur voyageurs/incidents/coûts.

Compétences démontrées : SQL BigQuery, JSON, typage, dbt, dépendances, tests de données

et unitaires, règles métier, qualité, couverture, preuve reproductible et documentation.

Questions d'entretien, facultatives :

- Pourquoi conserver −1 dans >30 ? Fidélité du brut et exclusion tracée, sans correction inventée.

- Pourquoi ne pas supprimer toute la ligne ? Les effectifs centraux et le couple important ont des usages distincts.

- Un test vert certifie-t-il P−A ? Non : compatibilité arithmétique, convention D01 maintenue.

- Pourquoi des warnings dans une livraison validée ? Anomalies source détectées, quantifiées et encadrées.

- Où s'exécute dbt ? Le PC organise les requêtes, BigQuery exécute le SQL.

- Comment reproduire ? Version brute figée, empreintes du code, profil privé et commande de qualification.

Approfondissements hors périmètre : référentiel de gares (clés fiables, effort modéré

à important), suivi de qualité entre versions (historique qualifié, effort modéré),

fraîcheur automatisée (rythme source observé, J09), matérialisation après mesure

de coût/performance. Aucun n'est ajouté automatiquement.

## Publication progressive — décision du 9 octobre 2026

Après clôture technique de J04, le porteur a demandé : « un premier commit couvrant
l'état validé jusqu'à J04 » et son envoi GitHub, puis une publication à chaque prochain
jalon. Cet accord complète le plan sans implémenter J05 ni réaliser la release J10.

La préparation de cette publication ajoute README, règles Git dans AGENTS/PLAN,
préservation des octets par .gitattributes et copies publiques anonymisées des
preuves. Les originaux ne sont pas écrasés : les trois dossiers locaux de preuves
sont ignorés par Git ; leurs copies sont dans reports/publication_evidence, avec
un manifeste portant les empreintes originales et publiques. Les liens des rapports
pointent les copies publiques. Les chemins personnels des documents sont également
anonymisés ; les versions intégrales locales sont conservées hors OneDrive.

Les mentions « aucun commit/publication » ci-dessus décrivent la clôture du
8 octobre. Le premier commit du 9 octobre regroupe l'état J01–J04, sans reconstitution
fictive de commits pour les étapes antérieures. Le journal de publication est
[docs/publication.md](../publication.md). Les tests et contrôles cloud historiques
ne sont pas renouvelés par la préparation de copies publiques.
