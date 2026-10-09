# Audit de faisabilité de la source TGV — J01

**Conclusion : la V1 est réalisable avec des limites documentées.** La clé est unique et les effectifs centraux permettent une analyse descriptive sur un périmètre sélectionné. Les taux utilisent une population déduite, les causes restent des profils mensuels et certains champs de retards importants sont impropres à une comparaison sans exclusion.

Le jalon ne démontre aucune dégradation ; aucun classement de performance n'a été calculé.

## Version examinée et preuves

| Élément | Valeur |
|---|---|
| Jeu | `regularite-mensuelle-tgv-aqst`, SNCF Voyageurs |
| Version locale | `20261001T140237476619Z` |
| Export terminé | 1er octobre 2026, 14:02:43 UTC, soit 16:02:43 à Paris |
| Modification des données déclarée | 27 juillet 2026, 14:51:45 UTC |
| Traitement des métadonnées | 1er octobre 2026, 04:30:11 UTC |
| Dernier mois métier | Juin 2026 |
| Format / taille | JSON, 11 518 814 octets |
| Empreinte SHA-256 | `1b18c596c59b38f4feb230a630d5a8b8a3b3f13fa5802407ece9c269c575f24f` |

L'export complet provient de l'endpoint `/exports/json`, sans filtre. Les effectifs des métadonnées avant/après sont égaux au nombre de lignes exportées ; le schéma et les dates de modification des données sont stables pendant cette extraction. Il s'agit d'une vérification de transport, pas d'une preuve de validité de chaque valeur métier.

La métadonnée personnalisée annonce une périodicité **semestrielle** ; le grain mensuel ne justifie donc pas une actualisation mensuelle automatique. Une seule extraction ne suffit pas à mesurer le rythme réel de publication. Celui-ci sera observé avant la décision d'ordonnancement.

Preuves générées : [résumé](publication_evidence/audit_evidence/summary.json), [provenance](publication_evidence/audit_evidence/provenance.json), [profils des champs](publication_evidence/audit_evidence/fields.csv), [couverture des liaisons](publication_evidence/audit_evidence/routes.csv), [couverture mensuelle](publication_evidence/audit_evidence/monthly_coverage.csv), [anomalies détaillées](publication_evidence/audit_evidence/anomalies.csv), [périmètres de service](publication_evidence/audit_evidence/service_scope.csv), [éligibilité principale](publication_evidence/audit_evidence/eligibility.csv), [éligibilité annuelle](publication_evidence/audit_evidence/eligibility_2025_vs_2024.csv), [validation](publication_evidence/audit_evidence/validation.json).

## Structure et couverture

- 12 544 observations, 26 champs, janvier 2018 à juin 2026 : 102 mois distincts, sans mois totalement absent du jeu.
- 146 combinaisons liaison orientée/service : 116 nationales, 30 internationales ; respectivement 11 012 et 1 532 observations.
- 130 paires origine/destination distinctes et 59 libellés de gare.
- Zéro doublon exact, zéro doublon de `(date, gare_depart, gare_arrivee, service)` et aucune composante de clé manquante.
- 10 combinaisons liaison/service présentent au total **88 mois absents à l'intérieur de leur intervalle observé**.
- 16 commencent après janvier 2018 ; 25 finissent avant juin 2026. Ces nombres ne prouvent pas l'ouverture ou la fermeture d'une desserte.

Le tableau `routes.csv` distingue trous internes, mois précédant la première observation et mois suivant la dernière. Les absences hors intervalle ne sont pas automatiquement des données manquantes attendues. La couverture complète du jeu global ne doit pas être confondue avec celle de chaque liaison.

## Périmètre et libellés

Paris–Barcelone dans les deux sens est étiqueté International jusqu'en septembre 2025, puis National d'octobre 2025 à juin 2026. Aucune correction géographique n'est appliquée au brut ; ces deux combinaisons National n'ont pas de référence nationale au premier semestre 2025 et sont exclues de la comparaison principale.

Quatorze autres paires présentent simultanément National et International en juillet–septembre 2025, soit 42 couples mois/paire. Leurs contenus diffèrent : ne pas les traiter comme des doublons exacts. Leur périmètre demeure à expliquer. Les comparaisons annuelles qui les recouvrent sont exclues par prudence ; le premier semestre principal ne recouvre pas ces mois.

Le contrôle simplifié des libellés (casse, accents, ponctuation) trouve zéro collision. Il ne peut pas reconnaître un renommage sémantique ni prouver qu'il n'y en a pas. Un référentiel de gares apporterait cette capacité ; il n'est pas ajouté à J01.

## Champs manquants et zéros

Les champs numériques et la clé sont tous renseignés dans cet export. En revanche :

- `commentaire_annulation` et `commentaire_retards_depart` : 12 544 valeurs nulles chacun ; leur caractère facultatif est documenté.
- `commentaires_retard_arrivee` : 11 846 valeurs nulles, 698 renseignées.
- 73 observations ont zéro circulation prévue ; 63 d'entre elles présentent néanmoins des annulations positives.
- Les six parts de causes valent toutes zéro dans 270 profils, dont **78 avec des retards à l'arrivée positifs**. « Renseigné » ne signifie donc pas « interprétable ».

Les zéros sont conservés, jamais convertis globalement en valeurs manquantes. Le statut analytique indique séparément si l'indicateur est exploitable.

## Anomalies quantifiées et conséquences

Une même observation peut déclencher plusieurs contrôles. Les occurrences ne doivent pas être additionnées pour compter des observations distinctes.

| Contrôle | Occurrences | Observations distinctes | Décision |
|---|---:|---:|---|
| Annulations > prévus | 63 | 63 | Toutes en 2020 ; exclure les ratios incompatibles |
| Effectif de retard > circulations déduites | 318 | 66 | Contrôle par champ ; garder une couverture propre à chaque KPI |
| Effectif négatif | 43 | 43 | Champ >30, T1 2025 ; quarantaine analytique du champ sur cette période |
| Imbrication des seuils incohérente | 361 | 361 | 354 fois >60 > >30 en 2025 ; 7 fois >30 > retards arrivée en 2020 |
| Moyenne/durée négative | 301 | 277 | Examiner le sens des moyennes ; aucune correction automatique |
| Somme des parts différente de 100 à plus de 0,1 point | 275 | 275 | 270 profils à zéro et 5 profils non nuls incomplets |
| Population déduite nulle | 10 | 10 | Taux de retard indisponible |
| Circulations prévues nulles | 73 | 73 | Taux d'annulation indisponible |

Les contrôles de types, de clé et de bornes individuelles 0–100 des causes ne détectent pas d'autre violation. Les bornes sont des contrôles de plausibilité, pas une certification sémantique.

**Exemple réel à conserver pour les futurs tests de qualité :** Dijon Ville → Paris Lyon, National, janvier 2025 : 426 prévus, 4 annulés, 60 retards à l'arrivée, **−1 retard >30 minutes**, 30 retards >60 minutes. Les effectifs centraux peuvent être utilisés selon leur convention ; le couple des retards importants est incohérent. Remplacer −1 par zéro ne résoudrait pas le problème.

Les cinq profils non nuls dont la somme est inférieure à 99,9 % datent de juin 2026 : Paris Montparnasse → Laval, Marseille St Charles → Lille, Paris Montparnasse → Vannes, Lyon Part Dieu → Lille et Paris Montparnasse → Quimper. Aucune renormalisation à 100 %.

12 481 observations satisfont les relations centrales P ≥ A ≥ 0 et 0 ≤ L ≤ P−A ; dix ont une population déduite nulle. Un contrôle arithmétique réussi ne certifie pas que P−A est identique à la population officielle de circulations assurées.

## Comparaisons arrêtées

La comparaison principale porte sur **janvier–juin 2026 contre janvier–juin 2025**, avec 6 mois uniques valides dans chaque période, au moins 30 circulations déduites chaque mois, même liaison/service et pas de pluralité de services dans les fenêtres étudiées.

**102 des 116 combinaisons nationales présentes dans l'historique sont éligibles.** Le dénominateur 116 comprend des liaisons historiques disparues et les deux combinaisons National apparues fin 2025 ; il ne correspond pas à 116 liaisons actives chaque mois. Les motifs détaillés de chaque exclusion sont dans `eligibility.csv`.

La sensibilité de couverture au minimum mensuel est 106 liaisons avec 15 circulations, 102 avec 30, 100 avec 60. Ce contrôle n'a calculé aucun rang de performance. Le seuil 30 est une convention pratique, pas une taille garantissant une précision statistique.

La comparaison complémentaire 2025/2024 compte **88 liaisons éligibles** après les mêmes contrôles sur 12 mois et l'exclusion des périmètres de service incertains. Elle ne peut pas être assimilée au même échantillon que la comparaison semestrielle.

La charte fixe aussi, avant J06, un signal à 2 points, une cible pédagogique de régularité de 90 % et une persistance à 4/6 mois. Ces hypothèses ne constituent pas des engagements SNCF.

## Définitions non résolues et replis

1. Population assurée non disponible directement : P−A est un dénominateur déduit, documenté comme tel, avec contrôles et interdiction de présenter les taux comme officiellement certifiés.
2. Préavis d'annulation contradictoire entre deux publications AQST : préserver l'effectif publié et ne pas prétendre mesurer toutes les suppressions ou certifier la stabilité historique de sa définition.
3. Frontières des seuils formulées différemment dans SNCF/AQST : utiliser les effectifs publiés, sans reconstruction individuelle.
4. Population des causes insuffisamment documentée : profils mensuels uniquement, aucun volume reconstitué ni agrégation.
5. Champs >15 limités à un périmètre particulier, >30 incohérents début 2025 : restrictions du contrat D04.
6. Services et gares sans référentiel stable : signaler les ruptures et exclure les comparaisons ambiguës, sans fusion arbitraire.

Les références consultées et les décisions complètes figurent dans le [contrat de données](../docs/data_contract.md). Les définitions ne sont pas déduites du nom des champs ni d'une somme de pourcentages.

## Reproduire l'audit

Depuis le dossier du projet, avec Python et sans dépendance tierce :

```powershell
# Rejouer exactement la version J01, sans accès réseau.
python scripts/profile_source.py --snapshot "$env:LOCALAPPDATA\SNCF_Service_Reliability_Analytics\data\audit\20261001T140237476619Z"

# Lancer les tests synthétiques hors réseau.
python -m unittest discover -s tests -v

# Créer une NOUVELLE version, sans écraser la précédente.
python scripts/profile_source.py --fetch --output-dir reports/audit_new_version
```

L'emplacement nominal de l'export est `C:\Users\<utilisateur>\AppData\Local\SNCF_Service_Reliability_Analytics\data\audit\20261001T140237476619Z`. Sur ce poste, Windows résout cet accès sous `C:\Users\<utilisateur>\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\SNCF_Service_Reliability_Analytics\data\audit\20261001T140237476619Z`. Les deux chemins ont été vérifiés accessibles pendant J01 ; l'emplacement résolu est indiqué pour la reprise si le contexte de l'application change. Il s'agit d'un stockage local hors OneDrive, pas d'une sauvegarde indépendante du PC.

`--data-dir` prime sur `SNCF_DATA_DIR`, qui prime sur le dossier LOCALAPPDATA par défaut. `--snapshot` lit le chemin explicitement donné ; il n'a pas besoin de `SNCF_DATA_DIR`. Les sorties peuvent être séparées avec `--output-dir`. La fenêtre principale est paramétrable ; les valeurs par défaut sont celles du contrat J01, et l'export de contrôle annuel reste fixé à 2025/2024.

Le manifeste conserve l'empreinte du script de capture initial. Le résumé conserve l'empreinte de la version finale du script de profilage : ces versions sont distinctes car les contrôles ont été enrichis après l'extraction. La validation finale enregistre les empreintes des fichiers de code et des résultats générés.

Une relance sur la version figée donne des résultats identiques, vérifiés sans réseau. Les conditions de complétude d'extraction et les cas limites sont testés ; les transformations dbt, les connexions BigQuery et Power BI ne sont pas encore implémentées ni validées.

## Attribution

Résultats calculés à partir des données **SNCF Voyageurs — [Régularité mensuelle TGV par liaisons](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/)**, extraction du 1er octobre 2026, sous [ODbL](https://opendatacommons.org/licenses/odbl/1-0/). Ce portfolio est indépendant de SNCF.
