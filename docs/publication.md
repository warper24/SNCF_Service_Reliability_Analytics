# Publication progressive du projet

Le 9 octobre 2026, le porteur a autorisé un premier commit regroupant l'état validé
J01–J04 et son envoi vers le dépôt public
[warper24/SNCF_Service_Reliability_Analytics](https://github.com/warper24/SNCF_Service_Reliability_Analytics).
Il demande ensuite un commit et un envoi à la clôture de chaque prochain jalon validé.
La présentation et l'accord préalable d'implémentation restent obligatoires ; J10
reste la livraison finale du portfolio. Le README résume brièvement chaque jalon.

## Contenu de la première publication

Code Python, modèles et tests SQL/dbt, configuration exemple, verrou de dépendances,
documentation, plan, bilans et copies publiques des résultats de contrôle jusqu'à J04.
Les exports complets, secrets, profils réels, environnements et caches restent exclus.
Les identifiants de jobs, versions et empreintes de données restent des preuves de
traçabilité ; ils ne donnent pas accès aux identifiants d'authentification.

Les trois dossiers `reports/audit_evidence/`, `reports/ingestion_evidence/` et
`reports/data_quality_evidence/` restent les sorties locales originales, ignorées par
Git. `scripts/prepare_publication.py` produit leurs copies dans
`reports/publication_evidence/`, en remplaçant seulement les noms de profil Windows
dans les chemins. Les valeurs métier et résultats des contrôles ne changent pas.

Sept des 28 fichiers de preuves de cette publication nécessitent une anonymisation.
Le manifeste donne les empreintes originales et publiques. Les empreintes internes
des validations historiques désignent toujours les originaux ; il faut consulter le
manifeste pour vérifier les octets des copies publiques. La publication ne renouvelle
pas les validations. Les documents sont également anonymisés ; leurs versions
intégrales locales sont conservées hors OneDrive.

`.gitattributes` préserve les octets des fichiers lors de l'ajout et du checkout,
malgré `core.autocrlf` sur Windows. Les originaux restent intacts. Sur un nouveau clone,
les copies publiques sont consultables ; les preuves locales originales doivent être
récupérées ou régénérées avant une nouvelle préparation de publication.

## Procédure pour les jalons suivants

1. Présenter le jalon, obtenir l'accord d'implémentation, puis réaliser et valider ses livrables.
2. Actualiser le bilan et le plan ; annoncer les contrôles non exécutés et les limites.
3. Préparer les copies publiques et vérifier le manifeste et les fichiers indexés.
4. Créer un commit décrivant le jalon validé, puis envoyer sans push forcé.
5. Vérifier le SHA distant et transmettre le lien du commit. Consigner une référence
   de commit uniquement après son existence réelle.

```powershell
python scripts/prepare_publication.py
python scripts/prepare_publication.py --check
git diff --cached --check
git diff --cached --stat
```

Ces commandes de préparation ne remplacent pas les tests du jalon. Le dépôt local
est propre au projet SNCF ; ne jamais ajouter les autres projets du dossier parent.
La branche de travail reste préfixée `codex/`. Le dépôt GitHub étant initialement vide,
la première publication crée `main` avec le même commit que `codex/j04-quality`.
Aucun historique antérieur fictif ni release finale n'est créé.

L'identité Git locale utilise le compte GitHub vérifié `warper24` et son adresse
`noreply`, sans publier l'adresse de contact personnelle ni modifier la configuration
Git des autres projets. La licence du code reste à choisir à J10 ; l'attribution
SNCF et la licence déclarée ODbL sont conservées dans le README et les rapports.
