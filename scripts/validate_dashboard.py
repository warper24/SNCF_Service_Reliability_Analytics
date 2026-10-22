"""Qualifier les contextes J08 réels, sans modifier l'entrepôt ni les preuves J07.

Les références fixes viennent des résultats SQL J06 ; les courbes mensuelles
sont comparées directement aux effectifs BigQuery. La revue Desktop et PDF
est complémentaire et n'est jamais déduite de ces assertions automatiques.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

from google.cloud import bigquery
from build_powerbi_dashboard import identity, NAV, MEASURES, VERSION

REPO = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-directory', required=True)
    parser.add_argument('--server', required=True)
    parser.add_argument('--project', default='sncf-reliability-analytics')
    args = parser.parse_args()
    work = Path(args.work_directory).resolve()
    if work.is_relative_to(REPO) or 'onedrive' in str(work).lower():
        raise ValueError('Les preuves doivent rester hors OneDrive et du dépôt.')
    run = work / ('dashboard_validation_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    run.mkdir()
    checks, jobs = [], []

    def dump(name, value):
        (run / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')

    def check(name, actual, expected, tolerance=1e-9):
        passed = (actual is not None and math.isclose(float(actual), float(expected), abs_tol=tolerance, rel_tol=0)
                  if isinstance(expected, (int, float)) and not isinstance(expected, bool) else actual == expected)
        checks.append({'name': name, 'passed': passed, 'actual': actual, 'expected': expected})

    def dax(name, query):
        source, target = run / (name + '.dax'), run / (name + '.json')
        source.write_text(query, encoding='utf-8')
        r = subprocess.run(['pwsh', '-NoProfile', '-File', str(REPO / 'scripts/powerbi_model_tools.ps1'),
            '-Action', 'Query', '-LibraryDirectory', str(work / 'tools'), '-Server', args.server,
            '-InputPath', str(source), '-OutputPath', str(target)], capture_output=True, text=True, timeout=150)
        (run / (name + '.txt')).write_text(r.stdout + r.stderr, encoding='utf-8')
        if r.returncode:
            raise RuntimeError('Échec moteur : ' + name)
        return [{k.split('[')[-1].rstrip(']'): v for k, v in row.items()}
                for row in json.loads(target.read_text(encoding='utf-8-sig'))]

    def q(value):
        return '"' + str(value).replace('"', '""') + '"'

    try:
        pages = work / 'SNCF_Reliability.Report/definition/pages'
        metadata = json.loads((pages / 'pages.json').read_text(encoding='utf-8-sig'))
        expected_pages = [identity(key) for key, _ in NAV]
        check('ordre des quatre pages métier', metadata['pageOrder'][:4], expected_pages)
        check('sept pages avec contrôles J07 conservés', len(metadata['pageOrder']), 7)
        inventory = []
        for pid in metadata['pageOrder']:
            page = json.loads((pages / pid / 'page.json').read_text(encoding='utf-8-sig'))
            if pid not in expected_pages:
                check('contrôle masqué ' + pid, page.get('visibility'), 'HiddenInViewMode')
                continue
            check('format 16:9 ' + pid, [page['width'], page['height']], [1280, 720])
            visuals = {p.parent.name: json.loads(p.read_text(encoding='utf-8-sig')) for p in (pages / pid / 'visuals').glob('*/visual.json')}
            for vid, visual in visuals.items():
                p = visual['position']
                check('visuel dans la page ' + vid, p['x'] >= 0 and p['y'] >= 0 and p['x'] + p['width'] <= 1280 and p['y'] + p['height'] <= 720, True)
                check('texte alternatif ' + vid, bool(visual['visual'].get('visualContainerObjects', {}).get('general')), True)
            for interaction in page.get('visualInteractions', []):
                check('interaction liée ' + interaction['source'] + '/' + interaction['target'], interaction['source'] in visuals and interaction['target'] in visuals, True)
            inventory.append({'page': page['displayName'], 'visuals': len(visuals)})
            if pid == identity('diagnostic'):
                check('drillthrough trois dimensions', len(page['pageBinding']['parameters']), 3)
                check('aucun filtre supplémentaire hérité', page['pageBinding']['acceptsFilterContext'], 'None')
                month = identity('diagnostic_cause_month')
                targets = {identity('diagnostic_causes'), identity('diagnostic_cause_status')}
                actual = {i['target'] for i in page['visualInteractions'] if i['source'] == month and i['type'] == 'DataFilter'}
                check('segment de mois limité aux causes', actual, targets)
        dump('report_inventory.json', inventory)
        live = dax('provenance', 'EVALUATE ROW("version",[source_version],"rows",COUNTROWS(fct_reliability_monthly),"last_month",FORMAT([last_business_month],"yyyy-MM"),"metadata_read",[last_import_utc])')[0]
        check('version figée', live['version'], VERSION)
        check('observations de la version figée', live['rows'], 12907)
        check('dernier mois source de la version figée', live['last_month'], '2026-09')
        # J08 ne doit pas altérer silencieusement les 57 expressions qualifiées.
        baseline = subprocess.run(['git', 'show', '10b1808:powerbi/SNCF_Reliability.SemanticModel/definition/tables/kpi_measures.tmdl'],
            cwd=REPO, capture_output=True, check=True).stdout.decode('utf-8-sig')
        original_expressions = {}
        for match in re.finditer(r'(?m)^\tmeasure (\w+) =[ \t]*([^\n]*)\n((?:\t{3}[^\n]*\n)*)', baseline.replace('\r\n', '\n')):
            parts = [match[2].strip(), *[line.strip() for line in match[3].splitlines()]]
            original_expressions[match[1]] = '\n'.join(part for part in parts if part)
        check('57 expressions J07 retrouvées dans le commit de référence', len(original_expressions), 57)
        expressions = dax('measure_expressions', 'SELECT [Name], [Expression] FROM $SYSTEM.TMSCHEMA_MEASURES')
        live_expressions = {r['Name']: r['Expression'] for r in expressions}
        for name, expression in original_expressions.items():
            normalized = '\n'.join(line.strip() for line in live_expressions.get(name, '').replace('\r\n', '\n').splitlines())
            check('expression J07 inchangée ' + name, normalized, expression)
        check('74 mesures explicites', len(live_expressions), 57 + len(MEASURES))
        cause_label = dax('cause_label', '''EVALUATE CALCULATETABLE(ROW("statut",[dashboard_cause_status]),TREATAS({"PARIS LYON → GRENOBLE"},dim_route[route_label]),TREATAS({"National"},dim_service[service_type]),TREATAS({"2026-06"},dim_date[month_label]))''')[0]
        check('statut métier français', cause_label['statut'], 'Profil 2026-06 : disponible')

        rows = list(csv.DictReader((REPO / 'reports/diagnostic_evidence/route_degradation.csv').open(encoding='utf-8-sig', newline='')))
        actual = dax('fixed_contexts', '''EVALUATE SUMMARIZECOLUMNS(dim_route[route_key],dim_service[service_key],dim_comparison[comparison_id],
"L",[dashboard_current_l],"N",[dashboard_current_n],"deterioration_months",[dashboard_deterioration_months],"underperformance_months",[dashboard_underperformance_months],"status",[dashboard_exclusion_reason],"investigation",[dashboard_investigation])''')
        index = {(r['route_key'], r['service_key'], r['comparison_id']): r for r in actual}
        for row in rows:
            key = row['route_key'], row['service_key'], row['comparison_id']
            a = index[key]
            complete = int(row['current_arrival_valid_months']) == int(row['expected_months'])
            for metric, source in [('L', 'current_l'), ('N', 'current_n')]:
                check('/'.join(key) + metric, a[metric], int(row[source]) if complete else None)
            persistent = row['is_eligible'] == 'True' and row['persistence_applicable'] == 'True'
            for metric in ['deterioration_months', 'underperformance_months']:
                check('/'.join(key) + metric, a[metric], int(row[metric]) if persistent else None)
            if row['comparison_id'] == '2025_vs_2024':
                check('pas de recommandation semestrielle à l’année ' + row['route_key'], a['investigation'], 'Aucune investigation spécifique documentée pour ce contexte.')
        summary = dax('summary', '''EVALUATE SUMMARIZECOLUMNS(dim_comparison[comparison_id],TREATAS({"National"},dim_service[service_type]),"eligible",[eligible_route_count],"excluded",[dashboard_excluded_count],"below",[dashboard_below_threshold_count])''')
        for a in summary:
            ref = [r for r in rows if r['comparison_id'] == a['comparison_id']]
            check('éligibles ' + a['comparison_id'], a['eligible'], sum(r['is_eligible'] == 'True' for r in ref))
            check('exclusions ' + a['comparison_id'], a['excluded'], sum(r['is_eligible'] != 'True' for r in ref))
            check('variations sous seuil ' + a['comparison_id'], a['below'], sum(r['change_signal'] == 'below_project_threshold' for r in ref))

        # Référence indépendante : effectifs et masques dbt du fait mensuel.
        client = bigquery.Client(project=args.project)
        sql = f'''SELECT departure_station,arrival_station,service_type,EXTRACT(YEAR FROM month) AS year,EXTRACT(MONTH FROM month) AS month_number,
IF(is_arrival_delay_rate_usable,SAFE_DIVIDE(arrival_delayed_trains,operated_trains_proxy),NULL) AS delay_rate,
IF(is_cancellation_rate_usable,SAFE_DIVIDE(cancelled_trains,scheduled_trains),NULL) AS cancellation_rate
FROM `{args.project}.sncf_dev.fct_reliability_monthly`
WHERE version_id='{VERSION}' AND departure_station='PARIS LYON' AND arrival_station='GRENOBLE' AND service_type='National' AND EXTRACT(YEAR FROM month) BETWEEN 2024 AND 2026'''
        (run / 'monthly_reference.sql').write_text(sql, encoding='utf-8')
        job = client.query(sql, location='EU', job_config=bigquery.QueryJobConfig(maximum_bytes_billed=100_000_000))
        monthly = [dict(r) for r in job.result(timeout=120)]
        jobs.append({'job_id': job.job_id, 'bytes_processed': job.total_bytes_processed, 'bytes_billed': job.total_bytes_billed})
        dump('monthly_reference.json', monthly)
        by_month = {(r['year'], r['month_number']): r for r in monthly}
        query = '''EVALUATE SUMMARIZECOLUMNS(dim_comparison[comparison_id],dim_date[month_number],TREATAS({"PARIS LYON"},dim_route[departure_station]),TREATAS({"GRENOBLE"},dim_route[arrival_station]),TREATAS({"National"},dim_service[service_type]),'''
        metrics = [f'dashboard_{metric}_{period}_month' for metric in ['delay', 'cancellation'] for period in ['current', 'previous']]
        query += ','.join(q(m) + ',[' + m + ']' for m in metrics) + ')'
        actual_monthly = dax('monthly_contexts', query)
        check('six paires semestrielles et douze annuelles', len(actual_monthly), 18)
        for a in actual_monthly:
            current_year = 2026 if a['comparison_id'].startswith('2026') else 2025
            for metric in ['delay', 'cancellation']:
                for period, year in [('current', current_year), ('previous', current_year - 1)]:
                    check(str((a['comparison_id'], a['month_number'], metric, period)), a[f'dashboard_{metric}_{period}_month'], by_month.get((year, a['month_number']), {}).get(metric + '_rate'))
        guards = dax('presentation_guards', '''EVALUATE ROW("L_total",[dashboard_current_l],"N_total",[dashboard_current_n],"month_total",[dashboard_delay_current_month],"cause_total",[published_cause_share],"annual_persistence",CALCULATE([dashboard_deterioration_months],TREATAS({"2025_vs_2024"},dim_comparison[comparison_id]),TREATAS({"PARIS LYON → GRENOBLE"},dim_route[route_label]),TREATAS({"National"},dim_service[service_type])))''')[0]
        for name, value in guards.items():
            check('contexte interdit ' + name, value, None)
        status = 'passed' if all(c['passed'] for c in checks) else 'failed'
    except Exception as error:
        status = 'error'
        checks.append({'name': 'execution', 'passed': False, 'error': str(error)})
    finally:
        dump('checks.json', checks)
        dump('jobs.json', jobs)
        result = {'status': status, 'checks': len(checks), 'failed': sum(not c['passed'] for c in checks),
            'run_directory': str(run), 'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'source_version': VERSION,
            'code_sha256': {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__), REPO / 'scripts/build_powerbi_dashboard.py']},
            'limitations': ['Navigation, clavier, interactions effectives et exports exigent une revue Desktop séparée.', 'D01–D07 non certifiées par ces contrôles.']}
        dump('validation.json', result)
        print(json.dumps(result, ensure_ascii=False))
    if status != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
