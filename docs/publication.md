# Publication progressive du projet

## Clôture J06 — 13 octobre 2026

Accord explicite reçu après présentation. La branche `codex/j06-diagnostic`
part du commit réel J05 `2f94df2fb6f8471e32c400225038785e431b8296`.
Elle livre diagnostic SQL, méthode préspécifiée, deux listes sans score,
sensibilité, constats, recommandations, collecteur et preuves. Qualification
finale : `20261013T102259Z_d1ed8f73`, avec 36 contrôles J06 réussis.
Les tests amont (94 réussites, quatre avertissements) proviennent de l'exécution
J06 `20261013T101816Z_2ce63253` et sont réutilisés après vérification des entrées,
du code, des versions et des empreintes. Les 37 tests Python ont aussi réussi.

Les 39 preuves historiques originales restent intactes. Le cinquième groupe
`reports/diagnostic_evidence/` contient les originaux sélectionnés de J06, ignorés
par Git. Les copies publiques préservent les chiffres, les périodes et les versions ;
les profils Windows sont anonymisés et le journal de compilation cp1252 est
converti en UTF-8 dans sa copie, avec encodages déclarés au manifeste et original
inchangé. Le résultat de sensibilité contient
des candidats/scénarios dérivés, pas l'export complet de la source. Les validations
cloud ne sont pas renouvelées pour préparer leur publication.

La [revue des fichiers indexés J06](../reports/publication_evidence/diagnostic_evidence/git_review.json)
consigne les contrôles du contenu à publier. Le commit est créé après cette revue,
puis envoyé sans forçage sur `main` et la branche de jalon ; son SHA distant est
vérifié avant d'annoncer l'envoi. La référence exacte est transmise dans la
conversation ; l'[historique J06](https://github.com/warper24/SNCF_Service_Reliability_Analytics/commits/codex/j06-diagnostic)
permet de retrouver la livraison. Aucune release finale J10 n'est créée ici.

## Clôture J05 — 9 octobre 2026

Reprise de la publication le **12 octobre 2026**, après interruption de la session.
Les empreintes des 57 fichiers de code qualifiés et les preuves locales concordent
avec la qualification du 9 octobre ; les 38 copies publiques et leur manifeste
ont été vérifiés. Aucun test cloud n'est relancé pour cette seule publication.
La date de qualification reste le 9 octobre, distincte de la clôture Git du 12.

Le jalon J05 a reçu l'accord explicite « Ok tu peux implémenter », après sa
présentation complète. La branche `codex/j05-model` part du commit réel
`8766048e2a9c4cd921d4e52470c3ea807921e794` et rassemble huit modèles analytiques,
leurs tests, la documentation et les preuves de qualification. Résultat : 76 tests
J05 réussis, 18 contrôles J04 réussis et quatre avertissements conservés, 37 tests
Python réussis. Qualification : `20261009T142236Z_7e5f8893`.

Le script de préparation inclut maintenant `reports/data_model_evidence/`, ignoré
par Git comme les trois groupes précédents. Les copies publiques comprennent la
validation, les logs des cinq étapes, trois résultats CSV ciblés et la revue
manuelle. Les 28 originaux historiques ont été vérifiés inchangés avant préparation.
Les contrôles cloud ne sont pas rejoués pour publier leurs copies.

La [revue des fichiers indexés](../reports/publication_evidence/data_model_evidence/git_review.json)
consigne le contrôle des noms, tailles et contenus, des liens locaux et des motifs
de secrets/chemins personnels. Son ajout porte le manifeste à 39 copies publiques.
Les fichiers les plus volumineux restent des fixtures synthétiques, le verrou de
dépendances et les preuves ciblées ; aucun export source complet n'est indexé.

L'accord du 9 octobre couvre l'envoi de cette clôture contrôlée vers le dépôt
autorisé. La procédure reste un envoi sans forçage vers `main` et la branche de
jalon, suivi d'une vérification du SHA distant ; le lien du commit réel est transmis
dans la conversation. La branche est consultable dans
[l'historique J05](https://github.com/warper24/SNCF_Service_Reliability_Analytics/commits/codex/j05-model).
Cette publication ne constitue pas la release finale J10.

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
