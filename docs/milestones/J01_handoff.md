# J01 — Cadrage métier et audit de faisabilité

**État : terminé avec limites explicites, le 1er octobre 2026.** BigQuery reste le choix confirmé ; aucun travail de J02 n'a été engagé.

## Accord et approche pédagogique acceptée

Le porteur du projet a d'abord demandé une lecture du plan et une présentation du premier jalon. La présentation a expliqué objectif, API, métadonnées, schéma, grain, clé candidate, couverture, dénominateur, étapes, fichiers, stockage, alternatives, contrôles et limites. Elle s'est terminée par la pause prévue par la section 4.2 du plan.

Le porteur du projet a ensuite donné son accord explicite : « Tu as mon accord pour l'implémentation. » L'approche acceptée a été appliquée : extraction identifiable, audit local reproductible, contrat des indicateurs, choix de périodes, documentation des incertitudes et bilan. Aucune nouvelle autorisation n'a été sollicitée pour les actions ordinaires de J01.

L'audit a demandé quelques fichiers complémentaires utiles : `.gitignore`, tests synthétiques et résultats structurés de contrôle. Ils permettent de préserver le brut hors Git et de vérifier les cas qui pourraient fausser les conclusions ; aucune extension métier n'a été ajoutée.

## Résultat et cheminement

1. Lecture du plan et état du dossier : seul `PLAN.md` existait ; aucune consigne AGENTS préexistante n'a été trouvée dans son ascendance.
2. Consultation des sources SNCF, AQST et de la licence ; documentation des divergences plutôt que déduction à partir du nom des champs.
3. Extraction complète par l'API et capture des métadonnées avant/après ; export, documentation et manifeste conservés hors OneDrive.
4. Contrôles Python sur structure, doublons, valeurs absentes, bornes, calendrier et services. Les anomalies n'ont pas été corrigées dans le brut.
5. Définition des conventions KPI et du périmètre éligible avant tout classement. La source permet une V1 descriptive à condition de respecter les restrictions.
6. Tests synthétiques, vérification des empreintes et rejeu de la version figée sans réseau : mêmes neuf fichiers de résultats, octet pour octet.

## Résultats à retenir

- 12 544 observations, 26 champs, de janvier 2018 à juin 2026.
- 146 combinaisons liaison orientée/service, correspondant à 130 paires orientées ; 116 combinaisons National et 30 International.
- Clé `(date, gare_depart, gare_arrivee, service)` unique et non nulle ; aucun doublon exact.
- 88 trous mensuels internes sur 10 combinaisons. Des débuts et fins d'observation différents ne démontrent pas à eux seuls un changement de desserte.
- 63 observations avec annulations supérieures aux prévus en 2020 ; 43 effectifs >30 négatifs début 2025 ; 361 incohérences d'imbrication des seuils.
- 270 profils de causes entièrement nuls, dont 78 avec retards à l'arrivée. Cinq autres profils ont une somme inférieure à 99,9 %.
- 102 liaisons National éligibles pour janvier–juin 2026 contre janvier–juin 2025 ; 88 pour 2025 contre 2024 après exclusions de périmètre. Ce sont des résultats datés de couverture, pas un classement de performance.

## Décisions, raisons et limites

| Décision | Justification et conséquence |
|---|---|
| Python standard pour J01 | Audit léger et rejouable, sans installation ; notebook possible mais non nécessaire |
| Export complet figé | Volume actuel adapté ; contrôler l'effectif évite une extraction limitée aux premières pages |
| Stockage externe et manifeste | Identifier exactement les données ; éviter de les inclure dans Git/OneDrive |
| BigQuery conservé, sans ressource créée à J01 | L'audit peut être réalisé localement ; configuration et coûts à J02 |
| P−A comme population déduite | Source sans champ de circulations assurées ; convention encadrée, pas taux officiel certifié |
| Causes mensuelles uniquement | Dénominateur/couverture non démontrés ; pas de volumes ni agrégations inventés |
| >15 exclu des KPI génériques | Périmètre aérien particulier dans le schéma |
| >30 au T1 2025 en quarantaine | Négatifs et ruptures d'imbrication ; aucune correction arithmétique conjecturale |
| Services conservés et périodes ambiguës exclues | Paris–Barcelone change de service ; 14 paires ont deux services au T3 2025 |
| Comparaison principale de mêmes mois, 6/6 chacun | Réduire les effets de saison et les changements de couverture |
| Minimum 30 circulations déduites chaque mois | Convention de prudence vis-à-vis des petits volumes ; variantes 15/60 documentées |
| Signal 2 points, cible fictive 90 %, persistance 4/6 | Hypothèses transparentes définies avant J06, sans prétention statistique ou engagement SNCF |

Divergences encore encadrées : préavis d'annulation, limites exactes des seuils de retard, absence de série de circulations assurées permettant une réconciliation, population des causes, sens de certaines moyennes négatives, identité stable des gares. Les solutions de repli figurent dans le contrat D01–D07. Aucune confirmation externe ni prise de contact n'a été réalisée.

## Livrables et utilisateurs

| Fichier | Rôle et utilisation |
|---|---|
| `docs/project_charter.md` | Questions, utilisateurs, périmètre, fenêtres et cibles ; référence de l'analyse et du rapport |
| `docs/data_contract.md` | Schéma des 26 champs, correspondances futures, populations, provenance, licence et restrictions ; référence ingestion/dbt |
| `docs/kpi_dictionary.md` | Formules, unités, filtres, agrégations, absences et exemples ; référence SQL/DAX |
| `scripts/profile_source.py` | Capture et audit reproductibles ; produit les preuves sans altérer la source |
| `tests/test_profile_source.py` | Cas synthétiques de qualité, intégrité et éligibilité ; contrôle des changements du script |
| `reports/source_audit.md` | Lecture humaine des preuves et conclusions de faisabilité |
| `reports/audit_evidence/` | Résultats JSON/CSV générés et preuve de validation ; consultation technique et reprise |
| `.gitignore` | Exclusions locales des secrets, caches et exports accidentels ; sans action sur OneDrive |
| `AGENTS.md` | Conventions et protocole pédagogique complet pour les conversations suivantes |
| `PLAN.md` | État J01 et décisions de référence actualisés |
| Ce bilan | Point de reprise, limites et enseignements |

Ces fichiers existent localement. Aucun commit, push, PR ou release n'a été effectué.

## Validation réellement exécutée

| Critère du plan | Méthode et preuve | Résultat / signification |
|---|---|---|
| Grain, clé, effectifs et bornes datés | Contrôles automatiques ; `summary.json`, `fields.csv` | Clé unique, mois valides, effectifs établis sur cette extraction |
| Doublons, absences, changements de périmètre quantifiés | `routes.csv`, `monthly_coverage.csv`, `service_scope.csv`, `anomalies.csv` ; lecture de cas | Anomalies quantifiées ; aucune identité de gare ou desserte inventée |
| KPI définis ou limités | Revue manuelle des sources et contrat de calcul | Tous disposent d'une formule ou d'une exclusion ; réserve sur N=P−A explicite |
| Usage des causes décidé | Revue sémantique + contrôle des profils | Parts publiées seulement, profils non exploitables signalés |
| Périodes/couverture/volumes arrêtés | Charte + screening automatisé | 102 éligibles au semestre, 88 à l'année ; seuils figés avant classement |
| V1 faisable et BigQuery conservé | Synthèse des champs utilisables et questions mesurables | Faisabilité avec restrictions ; pas de cloud nécessaire à J01 |
| Export identifiable hors du dépôt | Métadonnées avant/après, manifeste, SHA-256 et vérification locale | Export complet pour les métadonnées observées ; documentation archivée |
| Détection des erreurs du programme | 13 tests synthétiques réussis | Directions, doublons contradictoires, nul/zéro/absence, bornes, faibles volumes, services, mois invalides, altération d'archive et extraction incomplète |
| Reproductibilité | Appels réseau interdits pendant le rejeu, comparaison SHA-256 des neuf sorties | Résultats identiques octet pour octet |

La preuve détaillée, le journal des tests, les empreintes du code et des résultats sont dans `reports/audit_evidence/validation.json`. Les contrôles d'anomalies réussissent en **détectant** les incohérences ; un audit terminé ne signifie pas que la source est sans défaut.

Vérifications non effectuées : connexions BigQuery/Power BI, tests dbt, réconciliation de taux officiels et du dénominateur, revue métier par SNCF, diagnostic/rang de performance et causalité. Elles ne sont pas revendiquées dans ce jalon.

## Versions, stockage et reproduction

- Python effectivement utilisé : **3.13.15**, bibliothèque standard ; verrouillage d'environnement à J02.
- Données : version `20261001T140237476619Z` ; SHA-256 `1b18c596c59b38f4feb230a630d5a8b8a3b3f13fa5802407ece9c269c575f24f`.
- Code final identifié par ses empreintes dans `validation.json` ; code de capture initial identifié dans le manifeste. Pas de numéro de commit disponible.
- Emplacement nominal : `C:\Users\<utilisateur>\AppData\Local\SNCF_Service_Reliability_Analytics\data\audit\20261001T140237476619Z`.
- Emplacement résolu sur ce poste : `C:\Users\<utilisateur>\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\SNCF_Service_Reliability_Analytics\data\audit\20261001T140237476619Z`.
- Les deux accès ont été constatés disponibles dans cette session. Le stockage est local, hors OneDrive, sans sauvegarde indépendante ni purge automatique. Préserver ce dossier lors d'un changement d'environnement de l'application.

Depuis le dossier du projet :

```powershell
python -m unittest discover -s tests -v
python scripts/profile_source.py --snapshot "$env:LOCALAPPDATA\SNCF_Service_Reliability_Analytics\data\audit\20261001T140237476619Z"
```

Pour une nouvelle extraction, `python scripts/profile_source.py --fetch --output-dir reports/audit_new_version`. Si `LOCALAPPDATA` diffère dans un autre contexte, utiliser le chemin résolu ci-dessus ou transférer l'archive entière puis passer son chemin à `--snapshot`. `SNCF_DATA_DIR` configure les prochaines extractions ; il ne déplace pas automatiquement une archive existante.

La relance du profilage met à jour neuf résultats, pas le rapport narratif ni `validation.json`. Une modification du script ou des données exige de revoir ces documents et de renouveler la preuve de validation.

## Points d'attention pour J02

1. Présenter J02 puis attendre son accord propre, selon le protocole.
2. Le dossier SNCF est actuellement sous un dépôt Git parent `C:/Users/<utilisateur>/OneDrive/Documenten/DATA PORTFOLIO`, sur `master` sans commit. Aucune branche n'a été créée et aucun fichier d'un autre projet n'a été ajouté. Définir un périmètre Git SNCF adapté avant versionnement/publication.
3. Verrouiller les versions Python/dbt/adaptateur compatibles, configurer `SNCF_DATA_DIR` et confirmer un emplacement stable accessible hors de cette application.
4. Créer/configurer BigQuery, localisation, droits, budget, alertes et limites, puis la table d'essai prévue. Aucun compte ni ressource cloud n'est actuellement configuré par J01.
5. Préserver les limites D01–D07 dans les transformations et la présentation des KPI ; un contrôle arithmétique ne résout pas une incertitude de population.

## Bilan pédagogique et entretien

**API et schéma :** l'interface fournit les données ; le schéma décrit les champs, mais leurs noms seuls ne suffisent pas à leur donner un sens métier.

**Grain et clé :** une ligne est une liaison orientée, un service et un mois. La clé incluant le service évite de confondre 130 paires avec 146 séries. Question possible : « Pourquoi départ et arrivée ne suffisent-ils pas à identifier une observation ? »

**Dénominateur :** avec 100 prévus, 10 annulés et 18 retards, les taux sont 10 % et 20 % si les 90 circulations déduites sont la population pertinente. Question : « Comment justifier ce 90, au-delà d'une soustraction ? » Ici, la réponse doit conserver la réserve documentaire.

**Couverture :** 102 mois dans le jeu ne signifient pas 102 mois pour chaque liaison. Question : « Pourquoi un mois absent ne vaut-il pas zéro retard ? »

**Qualité ciblée :** une valeur >30 négative ne rend pas nécessairement tous les champs de la ligne inutilisables. Question : « Comment exclure un indicateur sans effacer l'observation source ? »

**Agrégation :** raisonner au grain et à la population corrects ; un ratio des sommes temporel ne supprime pas le double comptage interliaisons. Question : « Pourquoi une moyenne pondérée ne reconstitue-t-elle pas un taux national ? »

**Traçabilité :** export, date et empreinte permettent de rejouer l'audit malgré les évolutions de l'API. Question : « Une extraction récente prouve-t-elle que les observations sont récentes ? » Non : dernier mois métier juin 2026, malgré l'extraction d'octobre.

Approfondissements possibles, non réalisés : comparer deux captures pour détecter corrections/suppressions historiques (prévu J03), obtenir une confirmation du dénominateur au même grain, utiliser un référentiel de gares, et étudier la sensibilité des rangs à J06. Chaque piste exige des données ou travaux supplémentaires ; aucune n'a été ajoutée implicitement au périmètre J01.
