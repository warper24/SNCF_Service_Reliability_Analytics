# J07 — Modèle Power BI, Power Query et DAX

**État : qualification réussie le 21 octobre 2026 ; clôture le 22 octobre 2026.**
Implémentation autorisée le 16 octobre 2026.

Accord explicite : « ok tu peux implémenter le jalon ». Il couvre la présentation
détaillée du 13 octobre : Import depuis BigQuery, modèle en étoile, mesures
protégées, réconciliation SQL/DAX, expérience d'actualisation isolée, validation
dans Desktop, documentation et publication du jalon validé. Aucun travail J08.

Point de départ : commit réel `a937b83`, branche `codex/j06-diagnostic`, dépôt
propre. Branche de réalisation : `codex/j07-powerbi`. Le PBIX historique présent
dans `Power BI/`, ignoré par Git, est préservé. Nouveau projet actif hors OneDrive.

La préparation a vérifié 69 empreintes de code J06, 23 preuves d'exécution,
54 copies publiques, l'archive source et son manifeste. Aucun test historique
n'a été renouvelé pour cette vérification. La source figée couvre janvier 2018
à septembre 2026 ; les comparaisons restent H1 2026/H1 2025 et 2025/2024.

## Approche acceptée

Le PC pilote et conserve une copie Import ; BigQuery calcule le SQL et reste
l'entrepôt de référence. Power Query assure connexion, sélection et types ;
dbt conserve les règles métier. DAX agrège sous contexte de filtre et contrôle
les usages autorisés. Les deux faits ne sont jamais joints pour sommer les trains.
Les comparaisons fixes ont leur propre dimension ; les jours partiels sont refusés.
Les ratios exigent une seule liaison/service, une couverture valide complète et
un dénominateur positif. Les causes restent liaison/service/mois/cause.

Import est adapté au volume et aux données mensuelles, au prix d'une actualisation
explicite. DirectQuery ajouterait des requêtes distantes aux interactions. PBIP
permet de relire les changements ; un PBIX de livraison demeure le repli prévu.
Le projet actif et ses caches sont hors OneDrive ; seuls les fichiers de définition
contrôlés rejoignent Git. `.gitignore` ne désactive pas OneDrive.

## Contrôles et preuves

Le modèle final comporte **12 tables Import, 16 relations actives à sens simple
et 57 mesures explicites**. Les trois pages PBIR sont des tableaux techniques
de contrôle : comparaisons fixes, sélection mensuelle et causes publiées.

La qualification `validation_20261021T143228Z` réussit **6 286 contrôles** :
29 sélections temporelles/cas limites, 232 lignes de comparaison, 726 parts de
causes d'un mois, 125 lignes portant au moins un rang J06, deux synthèses,
huit contextes interdits, provenance et états réels du moteur. Le nombre de
contrôles inclut les assertions par valeur et les états ; il ne représente pas
autant de scénarios métier indépendants. Les 37 tests Python locaux réussissent
également le 22 octobre en 14,871 secondes ; aucun test cloud amont n'est rejoué.

Preuve Import isolée : BigQuery 1→2, DAX conserve 1 avant actualisation et lit 2
après. Aucun fait SNCF modifié. La table de test est dans `sncf_test`, expire
après sept jours et n'est plus référencée par le modèle final. Ses preuves et
sa définition temporaire sont conservées hors dépôt.

Les données sont inchangées : archive `20261007T130103249967Z_bce4ef24`, version
`e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6`,
12 907 observations et dernier mois septembre 2026. Les métadonnées importées
portent l'horodatage du 21 octobre à 14:28:01 UTC. La clôture n'actualise pas
artificiellement cette date.

Desktop utilisé pour la qualification : **2.159.883.0** ; bibliothèque officielle
Microsoft TOM/ADOMD **19.118.3** hors Git. La préparation du 16 octobre avait
commencé avec Desktop 2.158.1304.0. Les définitions sont au niveau de compatibilité
tabulaire 1606. Le modèle a été ouvert, actualisé, inspecté, enregistré puis
soumis au contrôle de réouverture décrit dans `manual_review.json`.

Le [rapport de réconciliation](../../reports/sql_powerbi_reconciliation.md)
détaille risques, méthodes, résultats et preuves. Les originaux d'exécution
restent hors OneDrive ; les copies de contrôle sont dans `reports/powerbi_evidence/`,
ignorées par Git, et leurs copies publiques anonymisées dans
`reports/publication_evidence/powerbi_evidence/`. Aucune preuve n'est renouvelée
simplement pour être publiée. Les captures d'interface restent locales.

## Livrables et responsabilités

| Fichiers | Fonction et utilisateur |
|---|---|
| `powerbi/SNCF_Reliability.pbip`, dossiers `.SemanticModel` et `.Report` | Définitions Desktop versionnées ; base de travail J08, à copier hors OneDrive avant import |
| `docs/powerbi_model.md` | Architecture, populations, filtres, stockage, alternatives et reproduction pour l'auteur du rapport |
| `docs/measure_catalog.md` | Description, dossier, visibilité, format et DAX des 57 mesures pour le reviewer |
| `scripts/build_powerbi_project.py` | Générateur initial : schémas BigQuery et SQL compilé J06 → brouillon TMSL |
| `scripts/powerbi_model_tools.ps1` | Conversion TMSL/TMDL, lecture TOM et exécution DAX sur le moteur local |
| `scripts/build_powerbi_control_pages.py` | Génération des pages techniques PBIR, sans storytelling J08 |
| `scripts/validate_powerbi.py`, `analyses/sql/j07_reconciliation.sql` | Qualification indépendante SQL/DAX, résultats et traces d'échecs |
| `analyses/dax/j07_reconciliation.dax` | Exemple reproductible Dijon Ville → Paris Lyon en janvier 2025 |
| `scripts/probe_powerbi_import.py`, `analyses/sql/j07_import_probe.sql` | Expérience de cache isolée en trois étapes, sans mutation métier |
| `reports/sql_powerbi_reconciliation.md` et preuves | Résultats audités, périmètre et limites pour le lecteur du portfolio |
| `.gitignore`, `.gitattributes`, `scripts/prepare_publication.py`, `PLAN.md`, `README.md` | Exclusions des caches/preuves locales, conservation des octets TMDL générés par Desktop, anonymisation et état du jalon |

Le code produit les définitions et les contrôles ; les paramètres M configurent
la connexion ; les données sont stockées dans BigQuery et dans le cache externe ;
les preuves sont des résultats générés. Les définitions Git ne contiennent pas le
cache et ne constituent donc pas un rapport autonome sans accès aux données.

## Décisions et incidents résolus

- Table de mesures nommée `kpi_measures` : `measures` était réservé et refusé
  par Desktop lors du brouillon. Aucun contournement binaire du PBIX.
- Champs BigQuery répétés convertis en texte de présentation dans Power Query,
  sans multiplier les lignes du fait. Les règles métier restent SQL/dbt.
- Chemin de travail Windows virtualisé résolu avant ouverture dans Desktop ;
  l'alias `%LOCALAPPDATA%` du processus ne correspondait pas au chemin visible
  par l'application Store. Les données/cache restent hors OneDrive.
- Autorisation des SELECT natifs effectuée par le porteur du projet le 21 octobre,
  après affichage de la demande Desktop. Aucun secret saisi ou publié par le code.
- Calendriers automatiques Desktop détectés puis désactivés ; l'annotation
  correcte est `__PBI_TimeIntelligenceEnabled=0`. Les relations automatiques
  ont aussi été désactivées dans la session de travail. Conserver ces réglages
  lors d'une nouvelle configuration du fichier.
- Premier jeu de cas incomplet car le test cherchait `DIJON`, pas `DIJON VILLE`.
  La tentative échouée est conservée ; le libellé de test a été corrigé.
- Revue unifiée du plugin exécutée, mais heuristique et trop large : elle inclut
  les brouillons et ne reconnaît pas les mesures TMDL. Son score n'est pas utilisé
  comme validation. Ses propositions non exécutées et son journal restent externes.

Ces corrections restent dans le périmètre présenté ; aucun changement d'architecture
ni règle métier nouvelle n'a été introduit. Les conventions D01–D07 restent intactes.

## Reproduction

Les instructions détaillées figurent dans [le modèle](../powerbi_model.md).
À partir des définitions qualifiées copiées hors OneDrive, ouvrir le PBIP dans
Desktop, configurer l'identité BigQuery et les paramètres M, actualiser, puis :

```powershell
python scripts/validate_powerbi.py --project sncf-reliability-analytics `
  --server localhost:<port_observe> --work-directory <dossier_actif>
```

Pour la sonde, sur une table de test non déjà utilisée : exécuter successivement
`scripts/probe_powerbi_import.py --stage create`, actualiser Desktop,
`--stage change`, actualiser de nouveau, puis `--stage verify`, avec les mêmes
arguments de projet, dossier et serveur. Retirer ensuite la référence et la
définition temporaire du modèle, en les conservant avec les preuves. Ne pas
réinitialiser une preuve passée ni conserver cette dépendance TTL dans la livraison.

La préparation publique utilise `python scripts/prepare_publication.py`, puis
`--check`. Elle anonymise les copies et conserve les empreintes des originaux.
Les fichiers indexés doivent être revus avant commit et push sans forçage.

## Limites et transmission

D01–D07 inchangées : P−A déduit non certifié, causes sans population démontrée,
quarantaine du couple >30/>60 au T1 2025, services et sens distincts, aucune
inférence voyageurs/coûts/causalité. La qualification prouve l'implémentation du
contrat, pas la certification de ces hypothèses.

Pas de rapport métier J08, publication Power BI Service/Fabric, refresh planifié,
RLS, test de grande charge, machine neuve ni atomicité multi-table. La date du
SELECT de provenance n'est pas une garantie de transaction. La copie PBIP a été
vérifiée dans Desktop ; le repli PBIX n'a pas été nécessaire et n'est pas livré.

J08 recevra un modèle qualifié et trois pages de contrôle. Il devra construire
son propre parcours de décision sans supprimer les couvertures, réserves, filtres,
indisponibilités ou les distinctions entre rang, taux et volume. Il n'est pas engagé.
La publication GitHub ordinaire est autorisée par AGENTS ; le SHA de livraison
sera communiqué seulement après création et vérification distante du commit.

## Bilan pédagogique

Un **modèle sémantique** associe structure et sens aux données. **Power Query/M**
importe et prépare leur présentation ; **DAX** évalue des mesures sous un contexte
de filtre. **Import** conserve une copie indépendante jusqu'au prochain refresh.
**PBIP** référence les définitions textuelles ; **PBIX** est un fichier binaire
pouvant embarquer les données. **TMDL** décrit le modèle, **PBIR** décrit le rapport.

L'exemple 60/422 à Dijon illustre pourquoi on teste un numérateur, un dénominateur
et la couverture ensemble. Deux mois à 10/100 et 90/300 donnent 25 % par ratio
des sommes, pas 20 % par moyenne simple. Un mois absent et un mois de taux zéro
ne conduisent pas au même résultat. Le test 1→2 montre concrètement le rôle du cache.

Alternatives : DirectQuery évite une copie complète mais ajoute une dépendance
réseau à l'interaction ; une grande table unique simplifie l'apparence mais répète
les effectifs avec les causes ; tout recalculer en DAX dupliquerait le contrat SQL.
Ces options n'ont pas été retenues pour les raisons détaillées dans le modèle.

Questions d'entretien possibles, sans examen imposé :

- Pourquoi le total d'un taux peut-il être BLANK ? La population entre liaisons n'est pas certifiée.
- Pourquoi un calendrier quotidien pour des faits mensuels ? Pour conserver les mois attendus et refuser les jours partiels.
- Pourquoi une relation simple ? Pour éviter les chemins ambigus et la répétition des faits par cause.
- Pourquoi SQL et DAX peuvent-ils différer de quelques décimales ? Types numériques et arrondi du ratio SQL ; tolérance explicite, pas correction métier.
- Pourquoi l'année n'a-t-elle pas de persistance ? Le critère 4/6 n'y a pas été défini ; zéro inventerait un constat.
- Que prouve une réconciliation réussie ? La concordance avec le contrat, pas une causalité ou une population source certifiée.

Extensions hors périmètre : automatisation du refresh et supervision (identités,
environnement d'exécution, effort moyen), tests de performance à plus grande échelle
(données et objectifs de latence, effort moyen), sécurité par population (besoin réel
et matrice d'habilitations, effort moyen), orchestration transactionnelle de versions
(contrat de promotion, effort important). J08 garde la priorité prévue dans le plan.
