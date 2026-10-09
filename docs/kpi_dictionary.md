# Dictionnaire des KPI — contrat J01

Version du 1er octobre 2026. Ces règles guident l'implémentation SQL de J05 et DAX de J07 ; J01 réalise des contrôles et des exemples, pas les marts analytiques. Références et restrictions : [contrat de données](data_contract.md), notamment D01–D07.

## Règles communes à tous les indicateurs

- Grain élémentaire : mois × liaison orientée × service. Filtre principal : `service = 'National'` avec contrôle des changements de périmètre.
- Notation : **P** = `nb_train_prevu`, **A** = `nb_annulation`, **L** = `nb_train_retard_arrivee`, **N** = P − A. N est une population **déduite**, dont l'équivalence avec les circulations assurées n'a pas été certifiée au grain source.
- Effectifs : entiers non négatifs ; A ≤ P et L ≤ N. Rejeter les calculs incompatibles sans altérer le brut. Chaque indicateur dispose de sa couverture valide propre.
- Ratios : valeur calculée sur 0–1, affichage en %. Un dénominateur nul/négatif, un numérateur absent ou une incohérence produit une valeur indisponible, jamais 0 %.
- Agrégation temporelle dans une seule liaison/service : ratio des sommes, sur les mêmes observations valides au numérateur et dénominateur. Toute période incomplète est signalée et exclue des comparaisons principales.
- Pas de ratio agrégé entre liaisons ; nombre de liaisons et distribution de leurs résultats autorisés, avec population éligible explicite.
- L'affichage détaillé d'un mois valide de faible volume est possible avec avertissement ; l'accès au classement nécessite toutes les conditions de la [charte](project_charter.md).

## Indicateurs et populations

| Nom technique / question | Formule, numérateur et dénominateur | Unité et agrégation | État et limites |
|---|---|---|---|
| `cancellation_rate` — quelle part des circulations prévues publiées est annulée ? | A / P | % ; ΣA / ΣP dans une liaison/service | Exploitable sous contrôles ; conventions d'annulation historiques non certifiées ; ne mesure pas toutes les déprogrammations |
| `arrival_delay_rate` — quelle part est en retard à l'arrivée ? | L / N | % ; ΣL / ΣN | Convention analytique encadrée D01 ; libeller le dénominateur comme circulations déduites |
| `composite_regularity_rate` — quelle part n'est pas comptée en retard composite ? | (N − L) / N = 1 − L/N | % ; 1 − ΣL/ΣN | Même restriction ; ne décrit pas les trains annulés et ne garantit pas zéro minute de retard |
| `over_30_delay_count`, `over_60_delay_count` — quels volumes de retards importants sont publiés ? | Champs source >30 et >60 ; pas de dénominateur | Circulations comptées sur la liaison ; sommes temporelles des seuls mois valides | D04 : quarantaine >30 pour T1 2025, contrôle d'imbrication pour le couple, couverture affichée ; ne pas additionner >30 et >60 |
| `over_30_delay_rate`, `over_60_delay_rate` | Effectif du seuil / N, sur mêmes mois valides | % ; ratio des sommes | Même restriction que les effectifs et D01 ; ne pas publier une comparaison impliquant un mois invalide |
| `arrival_delay_change_pp` — détérioration récente ? | 100 × (ΣL courant / ΣN courant − ΣL référence / ΣN référence) | Points de pourcentage ; calcul après agrégation de chaque période | Périodes et liaison identiques ; hausse ≥2 points = signal de détérioration, baisse ≤−2 = signal d'amélioration ; seuil du projet, pas test statistique |
| `deterioration_persistence` — combien de mois montrent une dégradation ? | Nombre de paires mensuelles avec écart ≥2 points / nombre de paires éligibles | % des paires mensuelles ; recomptage des mois, pas moyenne des ratios de persistance | Comparer chaque mois au même mois N−1 ; semestre complet de 6 paires pour classer ; ≥4/6 = persistante |
| `underperformance_persistence` — la sous-performance est-elle durable ? | Nombre de mois avec régularité calculée <90 % / nombre de mois éligibles | % de mois ; recomptage sur période | Cible fictive du projet ; ≥4/6 sur le semestre complet = persistante ; ne pas appeler cela un SLA SNCF |
| `published_cause_profile` — quels motifs sont déclarés ce mois-là ? | Six parts `prct_cause_*` reprises telles quelles ; numérateurs/dénominateur de référence non établis | % source sur 0–100 ; aucune agrégation temporelle ou interliaisons | Profil liaison/service/mois seulement ; D03 ; pas d'effectifs estimés ni de contribution aux minutes de retard |
| `observation_coverage` — quelle part du calendrier est disponible ? | Mois uniques présents / mois attendus | % par liaison/service/période | Présence seule : distinguer de la couverture valide de chaque KPI ; un doublon ne vaut pas deux mois |
| `eligible_route_count` — combien de liaisons sont comparables ? | Nombre de clés liaison/service passant tous les critères ; pas de dénominateur | Nombre de liaisons, avec effectif de la population candidate affiché | Unité = liaisons, jamais trains distincts ; sélection propre à chaque période |

Les champs >15 minutes sont conservés et documentés, mais leur périmètre ne permet pas de définir un KPI générique V1. Les moyennes de minutes de retard restent exploratoires et ne sont pas utilisées pour la priorisation. Les effectifs par cause et un taux national reconstruit sont interdits par ce contrat.

## Fenêtres et éligibilité

Principale : janvier–juin 2026 contre janvier–juin 2025. Complémentaire : année 2025 contre année 2024. Six ou douze mois uniques, complets et valides dans **chacune** des périodes ; N ≥ 30 par mois. Exclure de la comparaison les paires dont le service est ambigu ou change dans les fenêtres considérées. Une rupture de libellé ne peut pas être réparée sans correspondance justifiée.

Les 102 liaisons éligibles au semestre et les 88 éligibles à l'année sont des résultats de l'audit daté, pas des constantes de calcul. Les faibles volumes sont examinés avec les variantes 15 et 60 ; la sensibilité du classement relève de J06. Ne pas additionner les motifs d'exclusion, qui peuvent se recouvrir.

## Exemples de référence à reprendre en SQL/DAX

Ces exemples sont fictifs et distincts des résultats SNCF.

1. P=100, A=10, L=18 : N=90 ; annulation=10 %, retard=20 %, régularité=80 %.
2. Mois 1 : L=10, N=100 ; mois 2 : L=5, N=10. Taux combiné=15/110≈13,64 %, alors que la moyenne simple de 10 % et 50 % vaut 30 %. Cet exemple illustre l'agrégation ; le second mois serait sous le seuil de volume du classement principal.
3. Passage de 10 % à 13 % : +3 points, +30 % relativement. Le signal de détérioration du projet est activé ; aucune causalité n'en découle.
4. N=0 et L=0 : taux indisponible. L absent et N=100 : taux indisponible. Mois absent : couverture incomplète.
5. >30=30 et >60=10 : le nombre >30 reste 30 ; leur somme compterait deux fois les dix retards les plus longs.
6. Une cause à 40 % : son effectif reste inconnu tant que sa population de référence l'est. Un total de parts à 100 % ne résout pas cette question.

## Preuves et validation future

Le script vérifie clé, couverture, types, bornes et anomalies. Les tests synthétiques de J01 couvrent notamment ratios indisponibles, doublons, directions, faibles volumes et changements de service. Les définitions ont été relues contre S1–S4 ; D01 reste explicitement une convention non certifiée. La réconciliation des KPI SQL/DAX n'a pas encore été exécutée : elle appartient à J05/J07, à partir de ces cas et de cas réels valides.
