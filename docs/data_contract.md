# Contrat de données — J01, version 1

Établi le 1er octobre 2026 sur l'export `20261001T140237476619Z`. Les effectifs et anomalies décrits ci-dessous caractérisent cette version, jamais des constantes à imposer aux futures extractions.

## Provenance et références

- **S1** : [fiche SNCF du jeu TGV par liaisons](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/).
- **S2** : [métadonnées et schéma API](https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/regularite-mensuelle-tgv-aqst).
- **S3** : [définitions AQST](https://www.qualitetransports.gouv.fr/definition-des-indicateurs-et-chiffres-de-la-a460.html).
- **S4** : [bilan AQST 2022, page imprimée 16](https://www.qualitetransports.gouv.fr/IMG/pdf/bilan_aqst_2022_ok.pdf), repère historique sur les conventions.
- **S5** : [conditions SNCF](https://ressources.data.sncf.com/pages/cgu/) et [texte ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
- **S6** : [API Explore, documentation de l'éditeur](https://help.opendatasoft.com/apis/ods-explore-v2/).

Les copies S1/S3/S4/S5 et le schéma S2 sont conservés dans le dossier d'extraction ; leurs URL, dates et empreintes figurent dans `reports/audit_evidence/provenance.json`. S6 a été consulté en ligne. Aucun contact avec SNCF ou l'AQST n'a été effectué.

Producteur déclaré : **SNCF Voyageurs**. Licence déclarée : **Open Database License (ODbL)**. Les futurs résultats distribués devront attribuer le jeu et renvoyer à sa licence ; la redistribution d'une base dérivée doit tenir compte du partage à l'identique et de l'accès aux données ou transformations prévu par cette licence. La licence du code sera traitée séparément à J10. Le lien de licence historique des métadonnées est conservé, même si la page de conditions actuelle est plus facile à consulter. Pas de publication externe à J01.

Mention à reprendre : « Données : SNCF Voyageurs, Régularité mensuelle TGV par liaisons, extraction du 1er octobre 2026, sous ODbL », avec liens S1 et S5.

## Grain, clés et format

Un enregistrement représente un mois, une gare de départ, une gare d'arrivée et un service. La clé candidate `(date, gare_depart, gare_arrivee, service)` est non nulle et unique sur 12 544 lignes. Les 146 combinaisons liaison/service correspondent à **130 paires orientées** ; les 16 paires restantes ont plusieurs services dans l'historique. Le service fait donc partie de la clé.

`date` est déclarée `date` par l'API mais exportée en chaîne `YYYY-MM`. Le contrat impose un mois valide ; la future date SQL pourra être le premier jour du mois comme convention de représentation, sans créer de données journalières. Les libellés source sont conservés ; il n'existe pas ici d'identifiant gare stable permettant de certifier un renommage.

## Dictionnaire des 26 champs

Les noms anglais ci-dessous sont les cibles de normalisation pour J04 ; J01 conserve les noms source dans les preuves. `int` et `double` désignent respectivement entier et nombre décimal déclarés par l'API. Les contraintes décrivent les calculs autorisés, pas une correction du brut.

| Champ source | Type API → nom technique cible | Sens et règle |
|---|---|---|
| `date` | date → `month` | Mois métier, `YYYY-MM`, obligatoire dans la clé |
| `service` | text → `service_type` | Valeur source National/International ; aucune reclassification implicite |
| `gare_depart` | text → `departure_station` | Gare de départ ; direction conservée |
| `gare_arrivee` | text → `arrival_station` | Gare d'arrivée |
| `duree_moyenne` | int → `scheduled_duration_minutes` | Durée moyenne prévue ; ne permet pas de retrouver les seuils individuels |
| `nb_train_prevu` | int → `scheduled_trains` | Circulations prévues publiées ; entier ≥ 0 |
| `nb_annulation` | int → `cancelled_trains` | Annulations publiées ; entier ≥ 0, ≤ prévus pour le ratio |
| `commentaire_annulation` | text → `cancellation_comment` | Facultatif ; entièrement nul dans cet export |
| `nb_train_depart_retard` | int → `departure_delayed_trains` | Effectif publié ; contrôle de borne, pas KPI principal |
| `retard_moyen_depart` | double → `mean_departure_delay_late_minutes` | Moyenne publiée des trains en retard au départ |
| `retard_moyen_tous_trains_depart` | double → `mean_departure_delay_all_minutes` | Moyenne tous trains ; valeurs signées à interpréter, pas de mise à zéro |
| `commentaire_retards_depart` | text → `departure_delay_comment` | Facultatif ; entièrement nul dans cet export |
| `nb_train_retard_arrivee` | int → `arrival_delayed_trains` | Effectif composite publié ; ne pas le recalculer à partir des moyennes |
| `retard_moyen_arrivee` | double → `mean_arrival_delay_late_minutes` | Moyenne des trains en retard ; valeurs négatives exclues de son usage |
| `retard_moyen_tous_trains_arrivee` | double → `mean_arrival_delay_all_minutes` | Moyenne tous trains ; signe et valeurs extrêmes à examiner |
| `commentaires_retard_arrivee` | text → `arrival_delay_comment` | Commentaire facultatif, 698 valeurs renseignées ; aucune analyse NLP |
| `nb_train_retard_sup_15` | int → `arrival_delayed_over_15_trains` | Schéma : périmètre des liaisons concurrencées par avion ; exclu des KPI génériques |
| `retard_moyen_trains_retard_sup15` | double → `mean_arrival_delay_over_15_minutes` | Même restriction ; ne pas généraliser à tous les trains |
| `nb_train_retard_sup_30` | int → `arrival_delayed_over_30_trains` | Effectif publié ; valeurs négatives et ruptures d'imbrication début 2025 |
| `nb_train_retard_sup_60` | int → `arrival_delayed_over_60_trains` | Effectif publié ; doit être compatible avec >30 et retards arrivée |
| `prct_cause_externe` | double → `external_cause_pct` | Part publiée : météo, obstacles et autres facteurs externes |
| `prct_cause_infra` | double → `infrastructure_cause_pct` | Part publiée : infrastructure |
| `prct_cause_gestion_trafic` | double → `traffic_management_cause_pct` | Part publiée : gestion du trafic |
| `prct_cause_materiel_roulant` | double → `rolling_stock_cause_pct` | Part publiée : matériel roulant |
| `prct_cause_gestion_gare` | double → `station_management_cause_pct` | Part publiée : gestion en gare et réutilisation du matériel |
| `prct_cause_prise_en_charge_voyageurs` | double → `passenger_handling_cause_pct` | Part publiée : prise en charge voyageurs |

Les pourcentages des causes sont exprimés sur **0–100**, pas 0–1. Toutes les colonnes numériques sont renseignées dans cette version, mais cette observation ne permet ni d'interdire les valeurs manquantes futures, ni de considérer tous les zéros comme fiables.

## Populations et décisions sémantiques

### D01 — Circulations déduites : convention encadrée

S3 définit les taux d'annulation sur les circulations programmées et les retards sur les circulations assurées. S2 ne fournit pas de champ « circulations assurées », ni d'équation explicite reliant ses deux effectifs. Nous retenons `operated_trains_proxy = scheduled_trains − cancelled_trains` **comme convention analytique**, uniquement sur les observations compatibles avec les contrôles. Ce calcul n'a pas été réconcilié avec une série officielle de circulations assurées au même grain.

Cette distinction doit apparaître dans les définitions et le futur rapport : « taux calculé sur les circulations déduites des effectifs publiés ». Ne pas le présenter comme un taux officiel SNCF certifié. Si une confirmation de population l'invalide, suspendre ces ratios et conserver les effectifs publiés, plutôt que changer silencieusement le dénominateur.

S4 indique un préavis de trois jours pour les annulations TGV, tandis que la page générale S3 mentionne la veille à 16 h. Cette divergence ne permet pas de dater une évolution applicable à tout l'export. Conserver le nombre d'annulations publié ; ne pas assimiler cet indicateur à toutes les suppressions de l'offre commerciale initiale. Les déprogrammations anticipées et les annulations partielles limitent cette interprétation. La continuité de cette convention dans l'historique n'est pas certifiée.

### D02 — Retard composite : utiliser les effectifs fournis

S1 décrit des seuils de 5/10/15 minutes selon la durée du trajet. Sa formulation sur les limites n'est pas identique à celle de S3/S4, qui évoquent un dépassement strict et des minutes entières. Il serait injustifié de reconstruire les retards individuels ou la règle exacte aux frontières avec la durée moyenne mensuelle. Les effectifs source font foi pour le calcul du projet ; la divergence est documentée, pas arbitrée par invention.

### D03 — Causes : profils uniquement

Les descriptions de S2 parlent de pourcentages de trains en retard par cause, sans fournir un effectif de référence traçable et sa couverture pour chaque profil. Une somme proche de 100 ne prouve pas cette population. **Aucun effectif de cause dérivé, aucune moyenne temporelle ou entre liaisons, aucune part des minutes attribuée aux causes.**

Chaque part est conservée par mois, liaison et service. Les profils entièrement nuls sont signalés « profil non exploitable » : 78 coexistent avec des retards à l'arrivée. Les cinq profils non nuls dont la somme s'écarte de 100 de plus de 0,1 point restent visibles avec avertissement de couverture, sans renormalisation. Le seuil de 0,1 point est une tolérance de diagnostic, pas une preuve d'exhaustivité.

### D04 — Retards importants : restrictions par indicateur

Les champs >15 minutes et leur moyenne sont exclus des KPI génériques faute de marqueur explicite du périmètre aérien. Pour >30 minutes, mettre en quarantaine analytique **janvier–mars 2025 dans son ensemble**, où 43 effectifs sont négatifs et 354 observations violent l'imbrication >60 ≤ >30. Ne pas supposer qu'une valeur positive de la période est correcte.

En dehors de cette période, un couple >30/>60 n'est utilisable que si `0 ≤ >60 ≤ >30 ≤ retards arrivée ≤ circulations déduites`. Si l'imbrication échoue, les KPI de retards importants de cette observation sont indisponibles. Les valeurs brutes sont toujours conservées. Pas de correction par valeur absolue, somme ou échange de colonnes sans preuve source. Les KPI centraux restent possibles si leurs propres effectifs sont valides.

### D05 — Service et gares

Paris–Barcelone dans les deux sens passe d'International à National en octobre 2025. Quatorze autres paires possèdent les deux services en juillet–septembre 2025. Il s'agit de faits de périmètre observés, pas de changements de desserte démontrés. L'audit trouve 42 couples mois/paire à deux services, avec des contenus différents. Aucun regroupement automatique.

Les 59 libellés de gare ne présentent pas de collision après suppression des accents, espaces et ponctuation et passage en minuscules. Ce contrôle ne démontre pas l'absence de renommages réels ; un référentiel stable serait nécessaire pour les confirmer. L'apparition ou disparition d'un libellé reste un signal à examiner.

### D06 — Valeurs absentes, négatives et qualité

Ne jamais remplacer un mois absent, un champ nul ou une division par zéro par zéro. Les moyennes tous trains négatives peuvent refléter des avances ou une anomalie de source ; elles sont signalées sans correction et ne servent pas à la priorisation V1. Une moyenne négative portant explicitement sur les trains en retard est exclue de son indicateur. Les commentaires sont facultatifs et ne déterminent pas l'éligibilité.

### D07 — Agrégation et limites d'inférence

Sommer des effectifs compatibles dans le temps pour **une même liaison et un même service** ; calculer ensuite le ratio. Ne jamais présenter la somme interliaisons comme un nombre de trains distincts ou un taux national. Ne pas sommer les seuils imbriqués. Les observations ne mesurent ni les voyageurs, ni les incidents individuels, ni les coûts. Les motifs déclarés orientent une investigation sans prouver la causalité.

## Contrôles et conservation

Les preuves de transport sont l'égalité des effectifs exportés avec les métadonnées avant/après et la stabilité du schéma et des horodatages source pendant l'extraction. Ce contrôle ne garantit pas une transaction côté fournisseur si une correction ne modifie pas ses métadonnées ; l'empreinte identifie précisément les octets reçus.

L'export JSON, les métadonnées et les pièces documentaires sont gardés hors du projet et de OneDrive, sans purge. Les résultats synthétiques sont dans `reports/audit_evidence/`. Une relecture vérifie les empreintes avant de profiler ; une extraction ratée garde son état d'échec et les traces disponibles. Le script J01 n'est pas le système d'ingestion fiable de J03 : pas de reprise réseau automatique, d'historisation BigQuery ou de détection entre deux versions à ce stade.

Les divergences D01–D06 ont des replis explicites et ne nécessitent pas de cloud pour être encadrées. Leur statut doit être préservé à J04–J08, jusqu'à preuve justifiant leur révision.
