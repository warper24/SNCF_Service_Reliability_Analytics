# Guide du rapport Power BI — J08

Ce rapport sert à sélectionner une liaison à examiner et à préparer une
investigation. L'utilisateur métier est une équipe fictive de pilotage qualité.
Les données mensuelles ne démontrent ni une responsabilité causale, ni un gain.

## Accéder aux résultats

- [Rapport PDF](../reports/dashboard.pdf) : quatre pages, consultables sans compte.
- [Synthèse de décision](../reports/executive_summary.md) : constats, priorités et réserves.
- [Captures](../powerbi/screenshots/) : rendus des pages exportées par Desktop.
- [Projet Power BI](../powerbi/SNCF_Reliability.pbip) : définitions textuelles,
  nécessitant Desktop, un accès BigQuery et un import sur une nouvelle machine.

Le PDF présente le scénario de référence : National, janvier–juin 2026 contre
janvier–juin 2025. La fiche illustrée est Paris Lyon → Grenoble et les causes
portent sur juin 2026. Ce choix reprend R01 de J06 ; aucun mois n'est sélectionné
parce qu'une cause y serait particulièrement élevée.

## Les quatre pages

| Page | Question et lecture |
|---|---|
| Vue d'ensemble | Quelle étendue du signal sur quelle population ? Les cartes comptent des liaisons orientées/service ; le graphique compare des écarts en points. |
| Liaisons prioritaires | Quelles liaisons examiner ? Deux listes conservent les rangs J06 : dégradation et sous-performance persistante. Les cinq premières positions incluent les ex æquo à la frontière. |
| Diagnostic d'une liaison | Quels éléments justifient l'investigation ? Taux, effectifs, courbes mensuelles, couverture, profil mensuel de causes et piste J06. |
| Méthode et qualité | Quels calculs et quelles limites ? Populations, critères, sensibilité, restrictions et provenance. |

Les trois pages techniques J07 sont conservées et masquées dans le parcours de
lecture. Elles ne sont pas incluses dans l'export PDF métier.

## Navigation et filtres

Le segment de comparaison des deux premières pages est synchronisé. Il propose
S1 2026/S1 2025 (janvier à juin) ou 2025/2024 (janvier à décembre). National est
un filtre de page visible ; il s'agit de la valeur source du service.

Sélectionner une ligne d'une liste, puis activer « Ouvrir le diagnostic de la
sélection ». Dans Desktop en mode conception, utiliser Ctrl+clic ou sélectionner
le bouton puis Ctrl+Entrée. Les boutons de navigation et de retour acceptent
également cette activation au clavier. Une autre possibilité est le menu
d'extraction du point sélectionné.

Le **drillthrough**, ou extraction vers une page détaillée, transmet trois
dimensions : liaison orientée, service et comparaison. Les filtres supplémentaires
du visuel source ne sont pas hérités. Le bouton Retour revient à la liste source.

Le segment « Mois du profil de causes » filtre seulement les barres et le statut
du profil. Il ne filtre ni les cartes de comparaison fixe, ni les courbes, ni
l'investigation. Les courbes superposent les mois calendaires des deux périodes
nommées dans l'en-tête. Les taux mensuels sont ceux des mesures J07, évaluées sur
chaque mois complet ; aucune nouvelle règle d'éligibilité n'y est inventée.

« Effacer les segments » retire les sélections de segments de la page ; ce
bouton ne signifie pas « restaurer automatiquement le scénario initial ».
Après effacement de la comparaison, choisir à nouveau une comparaison unique.
Après effacement du mois, les causes restent indisponibles jusqu'à sélection
d'un mois. La liaison et la comparaison transmises par extraction demeurent.

Les graphiques et tableaux de synthèse ne modifient pas les compteurs ni la
population de référence par surbrillance implicite. Sélectionner une ligne ne
recalcule pas son rang. Les listes annuelles n'ont pas de sous-performance
persistante : ce critère n'a pas été défini pour douze mois.

## Définitions à lire avec les chiffres

- **P** : circulations prévues publiées ; **A** : annulations publiées.
- **N=P−A** : circulations déduites, population non certifiée (réserve D01).
- **L** : retards composites à l'arrivée publiés, avec leurs seuils SNCF.
- Taux de retard : ΣL/ΣN au sein d'une même liaison/service ; annulation : ΣA/ΣP.
- Écart de 10 % à 13 % : +3 points de pourcentage, ou +30 % relativement.
- Présence : mois observés ; validité : mois utilisables pour un indicateur ;
  éligibilité : respect des critères arrêtés pour la comparaison et le classement.

N≥30 est exigé chaque mois des deux périodes, avec tous les mois attendus et un
périmètre de service non ambigu. Le signal est ±2 points. La persistance
semestrielle exige au moins quatre mois sur six. La cible de régularité de 90 %
est une hypothèse du portfolio, sans engagement SNCF.

Les ratios et effectifs des cartes ne sont disponibles que sous leurs gardes.
Un résultat vide n'est pas remplacé par zéro. Les courbes descriptives peuvent
montrer un mois de faible volume qui n'est pas éligible au classement.

## Exemple de parcours et investigations

Paris Lyon → Grenoble est deuxième dans la liste de dégradation semestrielle :
12,32 % → 22,09 %, soit +9,77 points, avec cinq paires mensuelles sur six en hausse
d'au moins deux points. Les 277 retards sont rapportés à 1 254 circulations
déduites. Le taux d'annulation est de 0,32 % sur sa propre population P.

La fiche reprend R01 : demander des événements datés et rapprocher exploitation,
gares, matériel et infrastructure. Le profil de juin est réparti entre catégories ;
il ne prouve pas laquelle explique l'écart semestriel. L'interlocuteur pressenti
est le responsable qualité de la liaison, avec les équipes concernées selon les
événements retrouvés. Suivi : L/N, A/P, couverture et mois en hausse.

Les annotations R01–R06 sont éditoriales, reprises des
[recommandations J06](../reports/recommendations.md). Elles sont bornées à la
version de données et au semestre documentés. Pour une autre fenêtre, le rapport
indique qu'aucune investigation spécifique n'est documentée. Le sens retour ne
reçoit pas automatiquement la recommandation du sens aller.

## Réserves et interprétations interdites

D01–D07 restent celles du [contrat](data_contract.md). Aucun taux national ou
total de trains distincts n'est reconstruit entre liaisons. Les causes restent
des pourcentages source par liaison/service/mois ; leur population n'est pas
démontrée. Aucune moyenne temporelle, renormalisation ou conversion en effectif.
Un zéro publié ne démontre pas l'absence d'incident.

Le couple >30/>60 du T1 2025 reste en quarantaine ; les comparaisons concernées
sont indisponibles. Les champs >15 et les moyennes de minutes ne déterminent pas
les priorités. Ni voyageurs, ni incidents individuels, ni coûts ou gains ne sont
déduits de ces données.

La sensibilité résume les résultats J06 sur la même version : 27 scénarios par
fenêtre, avec N minimum 15/30/60, variation 1/2/3 points et cible 85/90/95 %.
Ces scénarios ne sont ni indépendants ni équiprobables. Sortir de la liste par
inéligibilité n'est pas une amélioration. La version figée va jusqu'à septembre
2026 ; cette récence ne déplace pas les périodes de diagnostic.

## Stockage et reproduction

BigQuery reste l'entrepôt. Le moteur Import local contient une copie. Le pied de
page distingue dernier mois métier, version et heure UTC de lecture des
métadonnées ; cette heure ne garantit pas l'atomicité de l'import multi-table.
La copie qualifiée conserve la lecture du 21 octobre 2026 à 14:28:01 UTC.

Copier les définitions dans un dossier actif hors dépôt et OneDrive. Ne pas
actualiser le projet dans le dossier synchronisé : `.gitignore` ne désactive pas
OneDrive. Utiliser les paramètres M et la connexion décrits dans
[le modèle Power BI](powerbi_model.md). Aucune identité n'est incluse dans Git.

Le générateur reconstruit les seules pages J08 et mesures de présentation dans
une copie externe. Il réinitialise leurs états aux valeurs de référence ; ne pas
l'exécuter sur une copie contenant des modifications personnelles non conservées.

```powershell
python scripts/build_powerbi_dashboard.py --work-directory <copie_externe>
# Ouvrir ou appliquer les définitions dans Desktop et vérifier la version Import.
python scripts/validate_dashboard.py --work-directory <copie_externe> --server localhost:<port_observe>
python scripts/validate_powerbi.py --project sncf-reliability-analytics `
  --work-directory <copie_externe> --server localhost:<port_observe> --include-dashboard
```

Les commandes Python nécessitent l'environnement verrouillé J02. Le port doit
être celui du moteur de la bonne instance Desktop. Les contrôles produisent des
dossiers horodatés externes ; ils ne remplacent pas la revue réelle des boutons,
des interactions et de l'export. Ne pas rejouer l'expérience Import J07 pour
simplement republier sa preuve historique.

Après modification des définitions ou mesures, utiliser Optimiser → Actualiser les
visuels à une échelle de 100 %, vérifier les textes puis enregistrer. Un export
peut conserver une échelle réduite : contrôler aussi l’occupation de chaque page.
Garder une seule instance du projet actif ouverte pour éviter des brouillons concurrents.

Exporter dans Desktop par Fichier → Exporter → PDF, puis rendre et inspecter
chaque page. Un PDF n'a ni segments interactifs, ni drillthrough. Les états de
lecture doivent donc être explicites et les lignes nécessaires visibles sans
défilement. Les captures publiques proviennent de cet export ; elles n'exposent
pas l'interface du compte local.

## Décisions de conception

Barres pour comparer les écarts, courbes pour le temps et barres de causes
mensuelles : chaque forme répond à une question. Le profil n'est pas un empilement
forcé à 100 %. Deux listes évitent un score à pondérations arbitraires. Des visuels
natifs et un format standard réduisent les dépendances d'export. Les couleurs
s'accompagnent de titres, unités, libellés et textes alternatifs ; les objets
suivent un ordre de tabulation. Cela ne vaut pas certification complète d'accessibilité.

Une carte géographique, des visuels personnalisés, une page mobile ou les
scénarios intégralement interactifs pourraient répondre à d'autres usages,
avec préparation et qualification supplémentaires. Ils ne font pas partie de J08.
Power BI Service, actualisation planifiée et orchestration J09 sont distincts.

Références Microsoft consultées : [drillthrough](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-drillthrough),
[interactions](https://learn.microsoft.com/en-us/power-bi/create-reports/service-reports-visual-interactions),
[accessibilité](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-accessibility-creating-reports),
[export PDF et limites](https://learn.microsoft.com/en-us/power-bi/collaborate-share/end-user-pdf).

Données : **SNCF Voyageurs**, [Régularité mensuelle TGV par liaisons](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/),
extraction du 7 octobre 2026, sous [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
