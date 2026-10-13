# Méthode de priorisation — J06

Méthode arrêtée le 13 octobre 2026, après présentation et accord explicite :
« Oui, tu as mon accord pour exécuter l'implémentation du jalon 06. »
Ce texte est écrit avant le premier classement. Une révision doit être motivée.

## Population et conventions

Source figée J03 `20261007T130103249967Z_bce4ef24`, version
`e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6`.
Les tables qualifiées J05 sont les entrées. National est une valeur source,
pas une certification géographique. Départ → arrivée et service restent distincts.
P = prévus, A = annulés, N = P−A, L = retards composites publiés.
N demeure une population déduite non certifiée (D01).

Comparer janvier–juin 2026 à janvier–juin 2025, puis 2025 à 2024 séparément.
Exiger tous les mois uniques présents, effectifs centraux compatibles, N≥30 chaque
mois dans chaque période et un seul service sur les deux fenêtres de la liaison.
Tous les candidats restent dans les résultats, avec motifs d'exclusion distincts
pour absences, invalidité, faible volume et périmètre. Ces motifs se recouvrent.
La couverture d'un KPI est distincte de la présence d'une observation.

Taux temporel = ΣL/ΣN dans la même liaison/service. Annulations = ΣA/ΣP, avec leur
propre couverture valide. Jamais de moyenne simple des taux mensuels ni de taux
national reconstruit. Les ratios sont sur 0–1, les écarts en points de pourcentage.
NULL, zéro et mois absent restent distincts.

## Signaux et deux listes

Hausse ≥2 points : dégradation ; baisse ≤−2 : amélioration ; sinon variation
inférieure au seuil du projet, sans affirmation de stabilité statistique.
Régularité <90 % : sous-performance par rapport à une cible fictive du portfolio.
Persistance : au moins 4 mois sur 6. Dégradation mensuelle comparée au même mois
N−1 ; sous-performance sur le semestre courant. Persistance annuelle indisponible.

1. Liste dégradation : signal de hausse requis ; persistance décroissante,
   puis hausse du taux décroissante, puis L courant décroissant.
2. Liste sous-performance : persistance requise ; nombre de mois sous cible
   décroissant, puis taux courant décroissant, puis L courant décroissant.

Aucun score composite. Les listes peuvent se recouvrir. Une amélioration peut
coexister avec une sous-performance persistante. Les rangs SQL RANK conservent les
ex æquo métier et les sauts de rang. Présenter les rangs ≤5, donc les cinq premières
positions avec tous les ex æquo à la frontière ; conserver tous les autres rangs.
Les libellés stabilisent seulement l'affichage, sans départager un ex æquo métier.
Les seuils sont évalués par produits croisés avant arrondi ; les ratios NUMERIC
servent au classement (précision 10⁻⁹), l'affichage n'en change pas le calcul.
Les volumes concernent des circulations comptées sur chaque liaison, jamais un
total de trains physiques distincts entre liaisons.

## Sensibilité préspécifiée

Grille complète : N minimum 15/30/60 × variation 1/2/3 points × cible 85/90/95 %,
soit 27 scénarios pour chacune des deux fenêtres. Le scénario 30/2/90 reste la
référence. La cible ne modifie pas la liste dégradation ; la variation ne modifie
pas la liste sous-performance : ces scénarios redondants sont explicitement
conservés, pas présentés comme autant de preuves indépendantes.

Recalculer depuis les effectifs mensuels, pas depuis les drapeaux J05 fixés à 30.
Comparer couverture, catégorie, entrée/sortie des cinq premières positions et
rang parmi les candidats retenus. Les écarts de rang ne sont définis que si la
liaison est classée dans les deux scénarios. Entre fenêtres, dégradation seulement,
comparer les liaisons communes éligibles, en séparant les entrées/sorties de
population. Pour ce seul rang comparatif, utiliser la même règle sur les deux
fenêtres : variation puis volume, sans persistance (non définie à l'année).
Les rangs opérationnels originaux restent visibles séparément.
Le semestre 2025 est aussi une partie de l'année 2025 : les fenêtres
ne sont pas des réplications indépendantes. Ne pas choisir a posteriori la variante
qui soutient un récit. Une liste vide est un résultat recevable.

## Volume, taux et causes

Pour une comparaison éligible : ΔL = (N1−N0)r0 + N1(r1−r0).
Exemple fictif N0=1000, L0=100, N1=1200, L1=156 : +56 = +20 volume +36 taux.
10→13 % vaut +3 points et +30 % relativement. Cette convention attribue
l'interaction à l'effet taux ; elle ne démontre ni causalité ni gain évitable.
Une convention symétrique est possible mais n'est pas retenue pour préserver le
repère du plan. Tolérance du résidu : 0,01 circulation comptable, sans arrondir
les contributions avant la vérification.

Les causes des liaisons dans les premières positions sont présentées pour chaque
mois courant et de référence du semestre : six parts originales sur 0–100,
statuts, avertissements, commentaires disponibles. Aucune moyenne, renormalisation,
conversion en effectif, pondération supposée ou attribution causale. Un mois
absent reste explicitement identifiable par la grille. La sélection est l'union
des deux listes de référence au semestre, sans sélection sur une cause observée.

Quarantaine du couple >30/>60 au T1 2025 maintenue : aucune comparaison de ces
indicateurs sur les deux fenêtres. >15, moyennes de minutes, voyageurs, incidents,
coûts et gains exclus de la priorisation. D01–D07 restent en vigueur.

## Exécution, alternatives et validation

SQL/dbt calcule dans BigQuery EU ; Python pilote et collecte sans calcul métier.
Les analyses SELECT ne reconstruisent pas les tables J05. dbt compile les références ;
le collecteur exécute explicitement le SQL. Limite 100 MB par requête, pas plafond
cumulé. Entrées et dates de modification sont vérifiées avant/après l'exécution ;
pas de garantie transactionnelle multi-table (J09). Tentatives et SQL compilés
conservés sous SNCF_DATA_DIR/diagnostic_runs, hors OneDrive.

Les contrôles couvrent versions, grains, fidélité J05, frontières, absences,
ratios, décomposition, classements, égalités, sensibilité et profils de causes.
La revue humaine rapproche les constats des CSV et distingue constat, hypothèse
et investigation. Chaque recommandation nomme un interlocuteur pressenti et un
indicateur de suivi ; aucun contact externe n'est envoyé.

Pandas aurait facilité l'exploration mais dupliqué le contrat métier. Un score
unique aurait réduit la lecture à un nombre au prix de pondérations arbitraires.
Une fenêtre glissante exigerait un nouveau contrat. Ces options ne sont pas retenues.
Extensions : incertitude statistique (hypothèses de dépendance, effort moyen à
important), causalité (données d'incidents, effort important), référentiel de gares
(clés fiables, effort moyen). Power BI reste à J07/J08.
