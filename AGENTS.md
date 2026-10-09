# Consignes de travail — SNCF Service Reliability Analytics

## Références et périmètre

- Lire `PLAN.md` avant toute intervention et le compte rendu du dernier jalon concerné dans `docs/milestones/`.
- Une conversation correspond à un jalon. Ne pas avancer au suivant sans demande. Les instructions explicites du porteur du projet priment sur ces consignes ; consigner les changements acceptés.
- Publication autorisée le 9 octobre 2026 : premier commit regroupant l'état validé J01–J04, puis commit et envoi sur `https://github.com/warper24/SNCF_Service_Reliability_Analytics` à la clôture de chaque prochain jalon validé. Cet accord couvre la publication ordinaire des livrables contrôlés, sans redemander à chaque jalon ; il ne dispense pas de sa présentation et de l'accord préalable d'implémentation. J10 reste la livraison finale du portfolio.
- J01 a été présenté puis autorisé explicitement le 1er octobre 2026. Cet accord couvre J01, pas J02 ni les suivants.
- Documents métier et commentaires pédagogiques en français ; noms techniques en anglais. Préserver les noms de champs SNCF dans le brut et les preuves ; utiliser la correspondance du contrat pour la normalisation.
- BigQuery est confirmé pour l'entrepôt V1. Python assure extraction et contrôles de transport ; SQL/dbt porte les transformations métier ; Power BI utilise Import. Pas de PostgreSQL V1 ni de Google Cloud Storage imposé.

## Protocole pédagogique complet

### A. Préparer en lecture seule

Lire plan, consignes applicables et bilan précédent. Examiner les fichiers réels et les modifications en cours ; les livrables annoncés dans le plan ne sont pas supposés exister. Vérifier les prérequis et définir le périmètre. Les lectures utiles sont permises ; les modifications, installations, créations de ressources et exécutions d'implémentation attendent l'accord sur le jalon.

### B. Présenter le jalon avant de l'implémenter

Fournir une explication concrète et complète adaptée à un profil Data Analyst / Data Scientist souhaitant défendre ses choix. Une annonce d'actions ou une liste de fichiers ne suffit pas. Couvrir :

1. Objectif métier et technique, résultat attendu et place dans l'architecture.
2. Définitions des termes et acronymes nécessaires, avec exemples.
3. Étapes dans l'ordre, entrées, opérations, sorties, dépendances, lieux d'exécution et circulation des données.
4. Chaque fichier créé/modifié : contenu, fonction, producteur, utilisateur, liens avec les autres ; distinguer code, configuration, données et résultats générés.
5. Justification des décisions techniques et métier, besoin satisfait, compromis et limites, y compris les choix déjà retenus.
6. Alternatives pertinentes, avantages/inconvénients et raisons de ne pas les retenir.
7. Chaque critère de validation : risque couvert, méthode, résultat attendu, preuve conservée et sens d'un échec ; distinguer automatisation et revue manuelle.
8. Difficultés, hypothèses, incertitudes et cas limites ; préciser ce qui dépend encore de l'audit.
9. Approfondissements possibles avec valeur ajoutée, prérequis et effort, séparés du périmètre.
10. Compétences à retenir et exemples de questions d'entretien.

Les alternatives et extensions sont pédagogiques, pas automatiquement ajoutées au travail.

### C. Attendre le retour

Après la présentation, s'arrêter et attendre les questions ou l'accord explicite du porteur du projet pour implémenter ce jalon. Cette pause a été demandée dans le plan. Une question de compréhension, le silence ou une validation générale du plan ne vaut pas accord d'implémentation.

Un accord acquis couvre les actions ordinaires et fichiers du périmètre décrit : ne pas redemander à chaque étape. Si une découverte exige un changement matériel de périmètre ou d'architecture, expliquer l'écart avant de l'engager et recueillir le retour. Une limitation assortie du repli prévu par le jalon n'est pas, à elle seule, un changement de périmètre.

### D. Implémenter et expliquer

Après accord, utiliser une branche `codex/` si le contexte Git le permet sans modifier un autre projet. Expliquer les étapes importantes, les découvertes, leurs implications, les termes nouveaux et les erreurs résolues. Relier les contrôles aux critères de validation. Ne pas supprimer ni écraser les modifications du porteur du projet. Signaler les corrections indispensables aux prérequis et documenter les décisions.

### E. Clôturer et transmettre

Créer/actualiser `docs/milestones/JXX_handoff.md` avec objectif et état, fichiers, décisions justifiées, présentation et approche acceptée, changements, définitions, exemples, alternatives, commandes de reproduction, contrôles réellement exécutés et preuves, versions du code et des données, limites, exclusions, points pour le prochain jalon et bilan pédagogique. Mentionner un commit seulement s'il existe réellement.

Mettre à jour l'état dans `PLAN.md`. Un jalon terminé exige des livrables, des critères vérifiés, des limites explicites et des choix explicables. Rendre aussi un bilan dans la conversation : résultat, cheminement, rôle des livrables, preuves et limites. Ne pas imposer un examen au porteur du projet. Toute vérification non exécutée doit être annoncée.

Après validation d'un jalon, préparer les preuves publiques avec `scripts/prepare_publication.py`, vérifier les fichiers indexés (aucun secret, export complet, profil réel, cache ni chemin personnel), créer le commit puis l'envoyer au dépôt GitHub autorisé. Préserver l'historique distant : aucun push forcé. Vérifier la présence du commit sur GitHub et transmettre son lien ; ne pas annoncer un envoi réussi sans preuve. Les originaux locaux de contrôle restent dans `reports/*_evidence/`, ignorés par Git ; les copies publiques anonymisées et leur manifeste sont dans `reports/publication_evidence/`. Ne pas renouveler une preuve de validation simplement pour la publier.

## Conventions de données à préserver

- Références : `docs/data_contract.md`, `docs/kpi_dictionary.md`, `docs/project_charter.md`.
- Grain mois × départ × arrivée × service ; sens et services non fusionnés implicitement.
- Pas de régularité nationale ou de total de trains distincts reconstruit entre liaisons.
- P−A est une population déduite, non certifiée ; préserver la réserve D01 jusqu'à preuve documentaire/réconciliation explicite.
- Utiliser les effectifs composites publiés, pas des seuils reconstruits avec une moyenne mensuelle.
- Aucune conversion des parts de causes en effectifs et aucune agrégation des profils sans population démontrée.
- Distinguer zéro, valeur absente et mois absent. Une division par zéro reste indisponible.
- Ratios temporels calculés par ratio des sommes dans la même liaison/service. Ne pas additionner les seuils imbriqués.
- Préserver les anomalies brutes et les exclusions par indicateur, notamment les retards >30 au T1 2025. Ne pas corriger une valeur parce qu'elle paraît improbable.
- Les critères de période et d'éligibilité sont arrêtés avant le classement. Toute révision doit être justifiée et tracée ; cibles du portfolio distinctes des engagements SNCF.
- Séparer constat, hypothèse et recommandation. Pas d'inférence sur les voyageurs, incidents, coûts ou gains sans données adaptées.

## Stockage, exécution et reprise

- Exports hors du dépôt et de OneDrive. `SNCF_DATA_DIR` configurable ; défaut `%LOCALAPPDATA%\SNCF_Service_Reliability_Analytics\data`. Voir le bilan J01 pour le chemin Windows résolu sur ce poste.
- Conserver export, métadonnées, manifeste et empreintes ; ne pas purger automatiquement les versions ni les traces d'échec.
- Ne pas ajouter exports complets, secrets, environnements Python ou caches Power BI à Git. `.gitignore` ne désactive pas OneDrive.
- Les CSV de `reports/audit_evidence/` sont des résultats de contrôle, pas le jeu source complet. `validation.json` est produit par une validation distincte ; le reprofilage seul ne renouvelle pas cette preuve.
- J01 fonctionne en bibliothèque standard Python. Exécuter `python -m unittest discover -s tests -v` après modification du profilage ; rejouer la version figée et examiner les différences. Ne pas figer 12 544 lignes comme invariant des extractions futures.
- Les transformations métier de production et tests BigQuery/dbt viendront aux jalons prévus. Ne pas transformer le script d'audit en pipeline de production sans demande.
- État Git constaté à J01 : racine dans le parent `DATA PORTFOLIO`, branche `master` sans commit. Ne pas initialiser, déplacer ni publier tous les projets du parent par inadvertance. Le réglage du dépôt SNCF sera traité à J02.
