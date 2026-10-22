"""Construire les quatre pages J08 depuis les définitions qualifiées J07.

Écriture dans une copie externe uniquement. Les règles métier SQL/J07 restent
intactes ; les mesures ajoutées exposent les résultats et leur contexte.
Une ouverture et une qualification Desktop restent obligatoires après génération.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import uuid

REPO = Path(__file__).resolve().parents[1]
SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'
NAV = [('overview', "Vue d'ensemble"), ('priorities', 'Liaisons prioritaires'),
       ('diagnostic', "Diagnostic d'une liaison"), ('method', 'Méthode et qualité')]
BLUE, INK, MUTED, AMBER, TEAL = '#1C4E80', '#152C43', '#526579', '#A45B08', '#087E82'
VERSION = 'e4c3c2853a9692acb327fd37bbccc713349e5b33b66c1fe1f0e53d5cb0f12ce6'


def identity(value):
    return hashlib.sha256(('j08_' + value).encode()).hexdigest()[:20]


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def lit(value):
    if isinstance(value, bool):
        value = str(value).lower()
    elif isinstance(value, (int, float)):
        value = str(value) + 'D'
    else:
        value = "'" + value.replace("'", "''") + "'"
    return {'expr': {'Literal': {'Value': value}}}


def color(value):
    return {'solid': {'color': lit(value)}}


def obj(**properties):
    return [{'properties': properties}]


def field(table, name, measure=False, source=None):
    return {('Measure' if measure else 'Column'): {
        'Expression': {'SourceRef': {('Source' if source else 'Entity'): source or table}}, 'Property': name}}


def projection(table, name, label=None, measure=False):
    return {'field': field(table, name, measure), 'queryRef': table + '.' + name,
            'nativeQueryRef': label or name, 'displayName': label or name}


def measure(name, label):
    return projection('kpi_measures', name, label, True)


def condition(table, name, values):
    return {'Version': 2, 'From': [{'Name': 'd', 'Entity': table, 'Type': 0}],
            'Where': [{'Condition': {'In': {'Expressions': [field(table, name, source='d')],
                'Values': [[lit(value)['expr']] for value in values]}}}]}


def categorical(owner, table, name, values=None, drill=False):
    result = {'name': 'Filter' + identity(owner + table + name), 'field': field(table, name), 'type': 'Categorical'}
    if values is not None:
        result['filter'] = condition(table, name, values)
    if drill:
        result['howCreated'] = 'Drillthrough'
    return result


MEASURES = {
    'dashboard_comparison_label': ('Fenêtre fixe et populations de référence.', '', '''SWITCH(SELECTEDVALUE(dim_comparison[comparison_id]), "2026_h1_vs_2025_h1", "Janvier–juin 2026 / janvier–juin 2025", "2025_vs_2024", "Année 2025 / année 2024", "Choisir une comparaison unique")'''),
    'dashboard_coverage_label': ('Couverture des candidats ; ne compte pas des trains.', '', '''IF([comparison_context_allowed], FORMAT([eligible_route_count], "0") & " / " & FORMAT([candidate_route_count], "0") & " liaisons/service éligibles")'''),
    'dashboard_excluded_count': ('Candidats non éligibles ; motifs susceptibles de se recouvrir.', '0', 'IF([comparison_context_allowed], [candidate_route_count] - [eligible_route_count])'),
    'dashboard_below_threshold_count': ('Variation sous le seuil du projet ; aucune stabilité statistique affirmée.', '0', '''IF([comparison_context_allowed], CALCULATE(COUNTROWS(mart_route_priorities), KEEPFILTERS(mart_route_priorities[change_signal] = "below_project_threshold")))'''),
    'dashboard_current_l': ('Retards publiés, fenêtre fixe et liaison/service uniques, couverture valide complète.', '#,0', '''IF([comparison_context_allowed] && [single_route_service] && SELECTEDVALUE(mart_route_priorities[current_arrival_valid_months]) = SELECTEDVALUE(dim_comparison[expected_months]), SELECTEDVALUE(mart_route_priorities[current_arrival_numerator]))'''),
    'dashboard_current_n': ('Circulations déduites non certifiées D01 ; même garde que le taux courant.', '#,0', '''IF([comparison_context_allowed] && [single_route_service] && SELECTEDVALUE(mart_route_priorities[current_arrival_valid_months]) = SELECTEDVALUE(dim_comparison[expected_months]), SELECTEDVALUE(mart_route_priorities[current_arrival_denominator]))'''),
    'dashboard_deterioration_months': ('Nombre de mois en hausse selon la règle SQL ; annuel indisponible.', '0', '''IF([comparison_context_allowed] && [single_route_service] && SELECTEDVALUE(dim_comparison[persistence_applicable], FALSE()) && SELECTEDVALUE(mart_route_priorities[is_comparison_eligible], FALSE()), SELECTEDVALUE(mart_route_priorities[deterioration_months]))'''),
    'dashboard_underperformance_months': ('Nombre de mois sous cible fictive ; annuel indisponible.', '0', '''IF([comparison_context_allowed] && [single_route_service] && SELECTEDVALUE(dim_comparison[persistence_applicable], FALSE()) && SELECTEDVALUE(mart_route_priorities[is_comparison_eligible], FALSE()), SELECTEDVALUE(mart_route_priorities[underperformance_months]))'''),
    'dashboard_exclusion_reason': ('Motifs SQL de non-éligibilité, sans suppression des candidats.', '', '''IF([comparison_context_allowed] && [single_route_service], IF(SELECTEDVALUE(mart_route_priorities[is_comparison_eligible], FALSE()), "Éligible : couverture complète et N ≥30 chaque mois", COALESCE(SELECTEDVALUE(mart_route_priorities[exclusion_reasons]), "Hors population du classement")))'''),
    'dashboard_route_label': ('Contexte de la fiche : sens et service explicites.', '', '''IF([single_route_service], SELECTEDVALUE(dim_route[route_label]) & " · " & SELECTEDVALUE(dim_service[service_type]) & " | " & [dashboard_comparison_label], "Sélectionner une liaison orientée et un service")'''),
    'dashboard_freshness': ('Provenance importée ; heure du SELECT de métadonnées, sans garantie transactionnelle.', '', '''"Source jusqu'à " & FORMAT([last_business_month], "yyyy-MM") & " | Métadonnées lues : " & FORMAT([last_import_utc], "yyyy-MM-dd HH:mm") & " UTC | Version " & LEFT([source_version], 12)'''),
    'dashboard_cause_status': ('Statut du profil mensuel, indépendant de la catégorie de cause.', '', '''IF([single_route_service] && [complete_month_selection] && HASONEVALUE(dim_date[month]), "Profil " & SELECTEDVALUE(dim_date[month_label]) & " : " & SWITCH(SELECTEDVALUE(fct_delay_causes_monthly[cause_profile_status]), "available", "disponible", "missing", "incomplet", "out_of_bounds", "valeurs hors bornes", "all_zero", "entièrement nul, non exploitable", "sum_warning", "somme hors tolérance, à examiner", "absent"), "Choisir une liaison, un service et un mois")'''),
    'dashboard_investigation': ('Piste éditoriale R01–R06 ; bornée à la version et au semestre documentés, sans calcul causal.', '', '''VAR Route = SELECTEDVALUE(dim_route[route_label])
VAR Allowed = [single_route_service] && SELECTEDVALUE(dim_service[service_type]) = "National" && SELECTEDVALUE(dim_comparison[comparison_id]) = "2026_h1_vs_2025_h1" && [source_version] = "''' + VERSION + '''"
RETURN IF(NOT Allowed, "Aucune investigation spécifique documentée pour ce contexte.", SWITCH(TRUE(),
Route = "PARIS LYON → GRENOBLE", "R01 · Demander les événements datés et rapprocher exploitation, gares, matériel et infrastructure. Hypothèse : plusieurs mécanismes possibles. Suivi : L/N, A/P et mois en hausse ; aucune causalité établie.",
Route = "PARIS MONTPARNASSE → NANTES", "R02 · Examiner préparation et rotations sur des dates documentées. Hypothèse : contraintes répétées possibles, à confronter aux incidents. Suivi : taux, annulations et persistance ; causes mensuelles sans moyenne.",
CONTAINSSTRING(Route, "DOUAI") && CONTAINSSTRING(Route, "PARIS NORD"), "R03 · Examiner chaque sens séparément puis rapprocher dates et périmètres. Hypothèse commune à vérifier. Suivi : deux séries L/N et A/P, avec leurs volumes et couvertures.",
CONTAINSSTRING(Route, "STRASBOURG") && CONTAINSSTRING(Route, "NANTES"), "R04 · Vérifier les six paires mensuelles, les volumes et les incidents. Signal sensible au seuil N≥60. Suivi : taux, couverture et éligibilité ; sortie du classement ≠ amélioration.",
NOT ISBLANK([underperformance_rank]) && [underperformance_rank] <= 5, "R05 · Constituer une fiche d'événements pour cette liaison durablement sous cible. Hypothèse : difficultés récurrentes à documenter. Suivi : régularité mensuelle, mois sous cible, L et N.",
NOT SELECTEDVALUE(mart_route_priorities[is_comparison_eligible], FALSE()), "R06 · Examiner absences, faibles volumes et changements de périmètre avant réintégration. Suivi : couverture valide et motifs d'exclusion.",
"Pas de recommandation spécifique J06 : examiner couverture, évolution et événements datés avant de formuler une hypothèse."))'''),
}

# Aligner les mois calendaires sans réécrire les taux J07. Le calendrier est
# remplacé par un mois complet ; aucune modification de la comparaison fixe.
for prefix, base in [('delay', 'arrival_delay_rate'), ('cancellation', 'cancellation_rate')]:
    for period in ['current', 'previous']:
        MEASURES[f'dashboard_{prefix}_{period}_month'] = (
            'Taux mensuel J07 aligné sur la fenêtre fixe ; mois complets et gardes conservés.', '0.0%', f'''VAR MonthNumber = SELECTEDVALUE(dim_date[month_number])
VAR StartDate = SELECTEDVALUE(dim_comparison[{period}_start])
VAR EndDate = SELECTEDVALUE(dim_comparison[{period}_end])
VAR Allowed = [single_route_service] && HASONEVALUE(dim_comparison[comparison_id]) && NOT ISBLANK(MonthNumber) && NOT ISBLANK(StartDate) && MonthNumber >= MONTH(StartDate) && MonthNumber <= MONTH(EndDate)
VAR TargetDate = DATE(YEAR(StartDate), COALESCE(MonthNumber, 1), 1)
RETURN IF(Allowed, CALCULATE([{base}], REMOVEFILTERS(dim_date), DATESBETWEEN(dim_date[date_key], TargetDate, EOMONTH(TargetDate, 0))))''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-directory', required=True)
    args = parser.parse_args()
    work = Path(args.work_directory).resolve()
    if work.is_relative_to(REPO) or 'onedrive' in str(work).lower():
        raise ValueError('Utiliser une copie active hors dépôt et OneDrive.')
    report = work / 'SNCF_Reliability.Report'
    pages = report / 'definition/pages'
    # Repartir des octets qualifiés, jamais d'un modèle reconstruit par le générateur initial.
    original = (REPO / 'powerbi/SNCF_Reliability.SemanticModel/definition/tables/kpi_measures.tmdl').read_text(encoding='utf-8-sig')
    # Desktop peut déplacer les mesures avant les colonnes/partitions à la
    # sauvegarde. Retirer seulement nos blocs, en conservant toute la structure.
    for name in MEASURES:
        original = re.sub(r'\n(?:\t///[^\n]*\n)*\tmeasure ' + re.escape(name)
            + r' =.*?(?=\n\t(?:///|measure |column |partition )|\Z)', '', original, flags=re.S)
    original = original.rstrip() + '\n'
    for name, (description, fmt, expression) in MEASURES.items():
        original += '\n\t/// J08 — ' + description + '\n\tmeasure ' + name + ' =\n'
        original += '\n'.join('\t\t\t' + line for line in expression.splitlines()) + '\n'
        if fmt:
            original += '\t\tformatString: ' + fmt + '\n'
        original += '\t\tdisplayFolder: Rapport J08\n\t\tlineageTag: ' + str(uuid.uuid5(uuid.NAMESPACE_URL, 'sncf-j08-' + name)) + '\n'
    (work / 'SNCF_Reliability.SemanticModel/definition/tables/kpi_measures.tmdl').write_text(original, encoding='utf-8')

    comparison = (REPO / 'powerbi/SNCF_Reliability.SemanticModel/definition/tables/dim_comparison.tmdl').read_text(encoding='utf-8-sig')
    comparison = re.sub(r'\n(?:\t///[^\n]*\n)*\tcolumn comparison_label =.*?(?=\n\t(?:///|measure |column |partition )|\Z)', '', comparison, flags=re.S)
    comparison += '\n\t/// Libellé de présentation J08 ; identifiant et fenêtres SQL inchangés.\n\tcolumn comparison_label = SWITCH([comparison_id], \"2026_h1_vs_2025_h1\", \"S1 2026 / S1 2025\", \"2025_vs_2024\", \"2025 / 2024\", [comparison_id])\n\t\tdataType: string\n\t\tsummarizeBy: none\n'
    (work / 'SNCF_Reliability.SemanticModel/definition/tables/dim_comparison.tmdl').write_text(comparison, encoding='utf-8')

    theme = {'name': 'SNCF Reliability · J08', 'dataColors': [BLUE, AMBER, TEAL, '#8396A8', '#8764A4', '#516348'],
             'background': '#F3F6FA', 'foreground': INK, 'tableAccent': BLUE,
             'textClasses': {'title': {'fontFace': 'Segoe UI Semibold', 'fontSize': 14, 'color': INK},
                             'label': {'fontFace': 'Segoe UI', 'fontSize': 11, 'color': INK},
                             'callout': {'fontFace': 'Segoe UI Semibold', 'fontSize': 30, 'color': BLUE}}}
    save(work / 'theme.json', theme)
    theme_path = report / 'StaticResources/RegisteredResources/SNCF_Reliability_J08.json'
    save(theme_path, theme)
    config = json.loads((report / 'definition/report.json').read_text(encoding='utf-8-sig'))
    config['themeCollection']['customTheme'] = {'name': 'SNCF_Reliability_J08', 'type': 'RegisteredResources',
        'reportVersionAtImport': {'visual': '2.13.0', 'report': '3.4.0', 'page': '2.3.1'}}
    config['resourcePackages'] = [r for r in config.get('resourcePackages', []) if r['name'] != 'RegisteredResources'] + [
        {'name': 'RegisteredResources', 'type': 'RegisteredResources', 'items': [
            {'name': 'SNCF_Reliability_J08', 'path': 'SNCF_Reliability_J08.json', 'type': 'CustomTheme'}]}]
    save(report / 'definition/report.json', config)
    technical = []
    for page in pages.glob('*/page.json'):
        definition = json.loads(page.read_text(encoding='utf-8-sig'))
        if definition['displayName'].startswith('J07'):
            definition['visibility'] = 'HiddenInViewMode'
            save(page, definition)
            technical.append(definition['name'])

    inventory = []
    for index, (key, label) in enumerate(NAV):
        pid = identity(key)
        page_dir = pages / pid
        page = {'$schema': SCHEMA + 'page/2.1.0/schema.json', 'name': pid, 'displayName': label,
                'displayOption': 'FitToPage', 'height': 720, 'width': 1280,
                'objects': {'background': obj(color=color('#F3F6FA'), transparency=lit(0))}}
        visuals = []

        def visual(name, typ, x, y, w, h, title=None, roles=None, objects=None, filters=None):
            vid = identity(key + '_' + name)
            v = {'$schema': SCHEMA + 'visualContainer/2.14.0/schema.json', 'name': vid,
                 'position': {'x': x, 'y': y, 'z': 1000 * (len(visuals) + 1), 'width': w, 'height': h, 'tabOrder': len(visuals)},
                 'visual': {'visualType': typ, 'drillFilterOtherVisuals': False,
                    'visualContainerObjects': {'background': obj(show=lit(True), color=color('#FFFFFF'), transparency=lit(0)),
                        'border': obj(show=lit(False)),
                        'general': obj(altText=lit(title or name)),
                        'title': obj(show=lit(bool(title)), text=lit(title or ''), fontSize=lit(12), fontColor=color(INK)),
                        'padding': obj(top=lit(8), bottom=lit(8), left=lit(10), right=lit(10))}}}
            if roles:
                v['visual']['query'] = {'queryState': {role: {'projections': p} for role, p in roles.items()}}
            if objects:
                v['visual']['objects'] = objects
            if filters:
                v['filterConfig'] = {'filters': filters}
            visuals.append(v)
            return v

        def text(name, value, x, y, w, h, size=15, ink=INK, bg=None):
            v = visual(name, 'textbox', x, y, w, h)
            v['visual']['visualContainerObjects']['padding'] = obj(top=lit(0), bottom=lit(0), left=lit(0), right=lit(0))
            v['visual']['objects'] = {'general': obj(paragraphs=[{'textRuns': [{'value': line,
                'textStyle': {'fontFamily': 'Segoe UI', 'fontSize': str(size) + 'px', 'color': ink}}]} for line in value.split('\n')])}
            v['visual']['visualContainerObjects']['background'] = obj(show=lit(bool(bg)), color=color(bg or '#FFFFFF'))
            return v

        def button(name, caption, x, y, w, target=None, action='PageNavigation'):
            v = visual(name, 'actionButton', x, y, w, 40)
            v['visual']['objects'] = {
                'text': [*obj(show=lit(True)), {'selector': {'id': 'default'}, 'properties': {'text': lit(caption), 'fontSize': lit(11), 'fontColor': color('#FFFFFF'), 'horizontalAlignment': lit('center')}}],
                'icon': obj(show=lit(False)), 'outline': obj(show=lit(False)),
                'fill': [*obj(show=lit(True)), {'selector': {'id': 'default'}, 'properties': {'fillColor': color(BLUE)}}]}
            props = {'show': lit(True), 'type': lit(action), 'tooltip': lit(caption)}
            if target:
                props['drillthroughSection' if action == 'Drillthrough' else 'navigationSection'] = lit(identity(target))
            v['visual']['visualContainerObjects']['padding'] = obj(top=lit(0), bottom=lit(0), left=lit(0), right=lit(0))
            v['visual']['visualContainerObjects']['visualLink'] = obj(**props)
            v['visual']['visualContainerObjects']['background'] = obj(show=lit(False))
            return v

        def dynamic_text(name, title, metric, x, y, w, h, size=14):
            v = text(name, title or '', x, y, w, h, size)
            paragraphs = []
            if title:
                paragraphs.append({'textRuns': [{'value': title, 'textStyle': {'fontFamily': 'Segoe UI Semibold', 'fontSize': '12px', 'color': BLUE}}]})
            paragraphs.append({'textRuns': [{'value': {'propertyIdentifier': {'objectName': 'values', 'propertyName': 'expr'}, 'selector': {'id': 'J08Value'}}, 'textStyle': {'fontFamily': 'Segoe UI', 'fontSize': str(size) + 'px', 'color': INK}}]})
            v['visual']['objects']['general'] = obj(paragraphs=paragraphs)
            v['visual']['objects']['values'] = [{'selector': {'id': 'J08Value'}, 'properties': {'expr': {'expr': field('kpi_measures', metric, True)}}}]
            return v

        def table(name, title, projections, x, y, w, h, filters=None, size=11):
            if len(projections) == 1 and 'Measure' in projections[0]['field']:
                return dynamic_text(name, title or projections[0]['displayName'], projections[0]['field']['Measure']['Property'], x, y, w, h, 12 if name == 'freshness' else 14)
            v = visual(name, 'tableEx', x, y, w, h, title, {'Values': projections}, {
                'total': obj(totals=lit(False)), 'values': obj(fontSize=lit(size), wordWrap=lit(True)),
                'columnHeaders': obj(fontSize=lit(size), fontColor=color(BLUE)),
                'grid': obj(gridVertical=lit(False), gridHorizontal=lit(True), rowPadding=lit(3))}, filters)
            v['visual']['visualContainerObjects']['padding'] = obj(top=lit(2), bottom=lit(2), left=lit(8), right=lit(8))
            return v

        def slicer(name, table_name, col, title, default, x, y, w, sync=False):
            v = visual(name, 'slicer', x, y, w, 76, roles={'Values': [projection(table_name, col, title)]}, objects={
                'data': obj(mode=lit('Dropdown')), 'header': obj(show=lit(True), text=lit(title), textSize=lit(11)),
                'selection': obj(singleSelect=lit(True), selectAllCheckboxEnabled=lit(False)),
                'items': obj(textSize=lit(11)), 'general': obj(filter={'filter': condition(table_name, col, [default])})})
            if sync:
                v['visual']['syncGroup'] = {'groupName': 'J08Comparison', 'fieldChanges': True, 'filterChanges': True}
            return v

        def chart(name, typ, title, category, metrics, x, y, w, h, filters=None):
            v = visual(name, typ, x, y, w, h, title, {'Category': [category], 'Y': metrics}, {
                'categoryAxis': obj(fontSize=lit(10), showAxisTitle=lit(False)),
                'valueAxis': obj(fontSize=lit(10), showAxisTitle=lit(False)),
                'legend': obj(show=lit(len(metrics) > 1), fontSize=lit(10)),
                'labels': obj(show=lit(typ != 'lineChart'), fontSize=lit(10), labelDisplayUnits=lit(1))}, filters)
            return v

        def rank_filter(owner, name, maximum=5):
            def comparison(kind, value):
                return {'Comparison': {'ComparisonKind': kind,
                    'Left': field('kpi_measures', name, True, 'm'),
                    'Right': {'Literal': {'Value': str(value) + 'L'}}}}
            return {'name': 'Filter' + identity(owner), 'field': field('kpi_measures', name, True), 'type': 'Advanced',
                'filter': {'Version': 2, 'From': [{'Name': 'm', 'Entity': 'kpi_measures', 'Type': 0}],
                'Where': [{'Condition': {'And': {'Left': comparison(2, 1), 'Right': comparison(4, maximum)}}}]}}

        text('eyebrow', 'SNCF / FIABILITÉ DES LIAISONS TGV', 24, 12, 690, 25, 12, BLUE)
        text('title', label, 24, 38, 1150, 45, 28)
        for n, (nav_key, nav_label) in enumerate(NAV):
            button('nav_' + nav_key, str(n + 1) + ' · ' + nav_label, 24 + n * 308, 86, 296, nav_key)
        table('freshness', None, [measure('dashboard_freshness', 'Provenance de la copie Import')], 24, 664, 1232, 48, size=9)

        if key in ['overview', 'priorities', 'diagnostic']:
            button('clear', 'Effacer les segments', 1080, 42, 176, action='ClearAllSlicers')

        if key in ['overview', 'priorities']:
            page['filterConfig'] = {'filters': [categorical(key, 'dim_service', 'service_type', ['National'])]}
            slicer('comparison', 'dim_comparison', 'comparison_label', 'Comparaison fixe', 'S1 2026 / S1 2025', 24, 130, 420, True)
            if key == 'priorities':
                dynamic_text('context', 'Population de la comparaison', 'dashboard_coverage_label', 456, 130, 370, 76)
            else:
                table('context', None, [measure('dashboard_comparison_label', 'Périodes'), measure('dashboard_coverage_label', 'Couverture')], 456, 130, 800, 76)

        if key == 'overview':
            visual('headlines', 'cardVisual', 24, 218, 1232, 110, roles={'Data': [measure('eligible_route_count', 'Liaisons éligibles'), measure('deteriorating_route_count', 'Hausse ≥2 points'), measure('improving_route_count', 'Baisse ≥2 points'), measure('dashboard_excluded_count', 'Candidates exclues'), measure('dashboard_below_threshold_count', 'Sous le seuil ±2 points')]}, objects={
                'value': [{'selector': {'id': 'default'}, 'properties': {'fontSize': lit(30)}}],
                'label': [{'selector': {'id': 'default'}, 'properties': {'fontSize': lit(11)}}]})
            c = chart('changes', 'clusteredBarChart', 'Premières positions · écart du taux de retard (points)', projection('dim_route', 'route_label', 'Liaison orientée'), [measure('arrival_delay_change_pp', 'Écart en points')], 24, 340, 776, 242, [rank_filter(key, 'deterioration_rank')])
            c['visual']['query']['sortDefinition'] = {'sort': [{'field': field('kpi_measures', 'arrival_delay_change_pp', True), 'direction': 'Descending'}], 'isDefaultSort': True}
            text('reading', 'LIRE LE SIGNAL\nDégradation et niveau durablement faible : deux questions.\n\nLes listes et les volumes sont accessibles page 2.\nLa sortie d’un classement peut venir d’une exclusion.\n\nLa comparaison annuelle possède sa propre population.', 816, 340, 440, 242, 16, INK, '#E6EEF6')
            text('warning', 'Unité : liaison orientée/service. Aucun taux national ni total de trains distincts entre liaisons.\nTaux calculés sur N=P−A, population déduite non certifiée (D01). Seuil du projet : ±2 points.', 24, 594, 1232, 60, 14, MUTED)

        elif key == 'priorities':
            common = [projection('dim_route', 'route_label', 'Liaison orientée'), projection('dim_service', 'service_type', 'Service'), projection('dim_comparison', 'comparison_label', 'Comparaison')]
            for y, rank, caption, persistence in [(218, 'deterioration_rank', 'DÉGRADATION · semestre : persistance, hausse, volume ; année : hausse, volume', 'dashboard_deterioration_months'), (438, 'underperformance_rank', 'SOUS-PERFORMANCE · semestre : mois sous cible, niveau, volume ; année : indisponible', 'dashboard_underperformance_months')]:
                t = table(rank, caption, [measure(rank, 'Rang J06'), *common, measure('previous_arrival_delay_rate', 'Taux précédent'), measure('current_arrival_delay_rate', 'Taux courant'), measure('arrival_delay_change_pp', 'Écart (points)'), measure(persistence, 'Mois / 6'), measure('dashboard_current_l', 'L'), measure('dashboard_current_n', 'N déduit')], 24, y, 1232, 208, [rank_filter(key + rank, rank)], 10)
                t['visual']['query']['sortDefinition'] = {'sort': [{'field': field('kpi_measures', rank, True), 'direction': 'Ascending'}], 'isDefaultSort': True}
            button('extract', 'Ouvrir le diagnostic de la sélection', 840, 152, 416, 'diagnostic', 'Drillthrough')
            text('instructions', 'Sélectionner une ligne, puis activer le diagnostic (Ctrl+clic ou Ctrl+Entrée). Rangs J06 et ex æquo conservés ; cible fictive 90 %, N≥30/mois ; D01.', 24, 640, 1232, 24, 12, MUTED)

        elif key == 'diagnostic':
            bound = [categorical(key, 'dim_route', 'route_label', ['PARIS LYON → GRENOBLE'], True), categorical(key, 'dim_service', 'service_type', ['National'], True), categorical(key, 'dim_comparison', 'comparison_label', ['S1 2026 / S1 2025'], True)]
            page['filterConfig'] = {'filters': bound}
            page['pageBinding'] = {'name': 'J08Diagnostic', 'type': 'Drillthrough', 'acceptsFilterContext': 'None',
                'parameters': [{'name': 'Param_' + f['name'], 'boundFilter': f['name'], 'fieldExpr': f['field']} for f in bound]}
            dynamic_text('route', 'Liaison orientée · service · comparaison fixe', 'dashboard_route_label', 24, 130, 640, 65)
            button('back', 'Retour à la sélection', 680, 143, 188, action='Back')
            table('fixed', 'Comparaison fixe · taux sur N déduit non certifié (D01)', [measure('previous_arrival_delay_rate', 'Retard précédent'), measure('current_arrival_delay_rate', 'Retard courant'), measure('arrival_delay_change_pp', 'Écart (points)'), measure('dashboard_current_l', 'L courant'), measure('dashboard_current_n', 'N courant'), measure('current_cancellation_rate', 'Annulations A/P')], 24, 203, 1232, 96)
            for x, prefix, caption in [(24, 'delay', 'Retards composites · taux mensuel'), (452, 'cancellation', 'Annulations publiées · taux mensuel')]:
                c = chart(prefix, 'lineChart', caption, projection('dim_date', 'month_number', 'Mois calendaire'), [measure(f'dashboard_{prefix}_current_month', 'Courant'), measure(f'dashboard_{prefix}_previous_month', 'Référence')], x, 303, 416, 203)
                c['visual']['query']['sortDefinition'] = {'sort': [{'field': field('dim_date', 'month_number'), 'direction': 'Ascending'}], 'isDefaultSort': True}
            month = slicer('cause_month', 'dim_date', 'month_label', 'Mois du profil de causes', '2026-06', 880, 126, 376)
            cause = chart('causes', 'clusteredBarChart', 'Parts publiées · aucune moyenne ni conversion', projection('dim_cause', 'cause_label', 'Motif déclaré'), [measure('published_cause_share', 'Part publiée')], 880, 303, 376, 295)
            status = table('cause_status', None, [measure('dashboard_cause_status', 'Statut du profil')], 880, 605, 376, 51, size=9)
            table('eligibility', None, [measure('dashboard_exclusion_reason', 'Couverture et éligibilité')], 24, 514, 844, 58, size=10)
            table('investigation', 'CONSTAT → HYPOTHÈSE → INVESTIGATION · pistes J06', [measure('dashboard_investigation', 'Investigation et suivi')], 24, 580, 844, 76, size=10)
            # Seul le profil mensuel reçoit le segment de date. Aucune sélection
            # de cause ne filtre les taux, ni les autres catégories du profil.
            page['visualInteractions'] = [{'source': source['name'], 'target': target['name'], 'type': 'DataFilter' if source is month and target in [cause, status] else 'NoFilter'}
                for source in [month, cause] for target in visuals if target is not source]

        else:
            text('contract', '01 / POPULATIONS ET CALCULS\nGrain : mois × départ × arrivée × service. Sens distincts.\nRetards : ΣL / ΣN ; N = prévus − annulés, déduit non certifié.\nAnnulations : ΣA / ΣP. Pas de moyenne simple des taux.\nComparaisons : H1 2026/2025 et année 2025/2024 séparées.\nPrésence, validité et éligibilité sont trois informations distinctes.\nDivision par zéro, mois absent et zéro publié restent distincts.', 24, 138, 608, 216, 17, INK, '#FFFFFF')
            text('rules', '02 / CRITÈRES AVANT CLASSEMENT\nMois complets des deux périodes ; N≥30 chaque mois.\nHausse ≥2 points : dégradation ; baisse ≤−2 : amélioration.\nSinon : variation inférieure au seuil du projet.\nPersistance : au moins 4/6 mois ; annuelle indisponible.\nCible de régularité 90 % : hypothèse du portfolio.\nDeux rangs J06, aucun score ; ex æquo conservés.', 648, 138, 608, 216, 17, INK, '#FFFFFF')
            text('limits', '03 / RÉSERVES D01–D07\nCauses : parts publiées par liaison/service/mois, population\nnon démontrée ; aucune agrégation ni attribution causale.\n>30/>60 : T1 2025 en quarantaine ; pas de comparaison.\n>15 et moyennes de minutes hors priorisation.\nNational : valeur source ; changements de service visibles.\nAucune inférence voyageurs, incidents, coûts ou gains.', 24, 366, 608, 216, 17, INK, '#FFFFFF')
            text('sensitivity', '04 / ROBUSTESSE ET LECTURE\n27 scénarios J06 par fenêtre : N=15/30/60, variation=1/2/3,\ncible=85/90/95 %. Référence maintenue à 30/2/90.\nStrasbourg ↔ Nantes sort à N≥60 : exclusion, pas amélioration.\nLes cinq premières sous-performances restent dans les cinq\npremières positions dans 27/27 scénarios semestriels.\nCes fréquences ne sont pas des probabilités.', 648, 366, 608, 216, 17, INK, '#FFFFFF')
            text('source', 'Données : SNCF Voyageurs · Régularité mensuelle TGV par liaisons · extraction du 7 octobre 2026 · ODbL 1.0.\nPortfolio indépendant de SNCF. Sources, requêtes, conventions et preuves : guide du rapport et documentation du dépôt.', 24, 596, 1232, 60, 14, MUTED)

        # Les graphiques de synthèse ne changent pas les compteurs ou la sélection
        # de comparaison ; seules les interactions intentionnelles sont permises.
        if key in ['overview', 'priorities']:
            page['visualInteractions'] = [{'source': source['name'], 'target': target['name'], 'type': 'NoFilter'}
                for source in visuals if source['visual']['visualType'] in ['clusteredBarChart', 'tableEx']
                for target in visuals if target is not source]
        save(page_dir / 'page.json', page)
        for v in visuals:
            save(page_dir / 'visuals' / v['name'] / 'visual.json', v)
        inventory.append({'page': pid, 'label': label, 'visuals': len(visuals)})
    save(pages / 'pages.json', {'$schema': SCHEMA + 'pagesMetadata/1.1.0/schema.json',
        'pageOrder': [identity(key) for key, _ in NAV] + sorted(technical), 'activePageName': identity('overview')})
    save(work / 'dashboard_build.json', {'status': 'draft_requires_desktop_qualification', 'pages': inventory,
        'added_measures': list(MEASURES), 'source_version': VERSION})
    print(json.dumps({'pages': inventory, 'added_measures': len(MEASURES)}))


if __name__ == '__main__':
    main()
