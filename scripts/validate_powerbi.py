"""Réconcilier le moteur DAX Desktop avec BigQuery, sans modifier les données.

Les résultats et requêtes restent dans un dossier d'exécution externe. Un échec
est conservé et interdit de déclarer le jalon validé. L'authentification Google
et le premier chargement Desktop doivent avoir été effectués auparavant.
"""
import argparse
import calendar
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import subprocess

from google.cloud import bigquery

REPO = Path(__file__).resolve().parents[1]


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')


def dax_string(value):
    return '"' + str(value).replace('"', '""') + '"'


def dax_date(value):
    d = date.fromisoformat(str(value)[:10])
    return f'DATE({d.year},{d.month},{d.day})'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--server', required=True)
    parser.add_argument('--work-directory', required=True)
    parser.add_argument('--include-dashboard', action='store_true', help='Qualifier également les mesures de présentation J08.')
    args = parser.parse_args()
    work = Path(args.work_directory).resolve()
    if work.is_relative_to(REPO) or 'onedrive' in str(work).lower():
        raise ValueError('Les exécutions doivent rester hors du dépôt et de OneDrive.')
    run = work / ('validation_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    run.mkdir()
    checks, jobs = [], []
    client = bigquery.Client(project=args.project)

    def sql(name, query):
        query = query.replace('PROJECT_ID', args.project)
        (run / (name + '.sql')).write_text(query, encoding='utf-8')
        job = client.query(query, location='EU', timeout=30,
                           job_config=bigquery.QueryJobConfig(maximum_bytes_billed=100_000_000))
        rows = [dict(row) for row in job.result(timeout=120)]
        jobs.append(dict(name=name, job_id=job.job_id, bytes_processed=job.total_bytes_processed,
                         bytes_billed=job.total_bytes_billed, cache_hit=job.cache_hit))
        dump(run / (name + '_sql.json'), rows)
        return rows

    def dax(name, query):
        source = run / (name + '.dax')
        target = run / (name + '_dax.json')
        source.write_text(query, encoding='utf-8')
        result = subprocess.run(['pwsh', '-NoProfile', '-File', str(REPO / 'scripts/powerbi_model_tools.ps1'),
                                 '-Action', 'Query', '-LibraryDirectory', str(work / 'tools'),
                                 '-Server', args.server, '-InputPath', str(source), '-OutputPath', str(target)],
                                capture_output=True, text=True, timeout=150)
        (run / (name + '_query.txt')).write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode:
            raise RuntimeError(f'Échec DAX {name} ; voir le journal de cette tentative.')
        return [{key.split('[')[-1].rstrip(']'): value for key, value in row.items()}
                for row in json.loads(target.read_text(encoding='utf-8-sig'))]

    def check(name, actual, expected, tolerance=1e-9):
        if isinstance(expected, (float, int, Decimal)) and not isinstance(expected, bool):
            passed = actual is not None and math.isclose(float(actual), float(expected), abs_tol=tolerance, rel_tol=0)
        else:
            passed = actual == expected
        checks.append(dict(name=name, passed=passed, actual=actual, expected=expected, tolerance=tolerance))

    def compare(name, actual, expected, keys):
        a = {tuple(row[k] for k in keys): row for row in actual}
        e = {tuple(row[k] for k in keys): row for row in expected}
        check(name + ': clés uniques DAX', len(a), len(actual), 0)
        check(name + ': clés uniques SQL', len(e), len(expected), 0)
        check(name + ': mêmes clés', sorted(a), sorted(e))
        for key in e.keys() & a.keys():
            for metric, value in e[key].items():
                if metric not in keys:
                    check(name + ':' + '|'.join(map(str, key)) + ':' + metric,
                          a[key].get(metric), value, 1.1e-7 if metric.endswith('_pp') else 1e-9)

    try:
        audit_path=run/'model_audit.json'
        subprocess.run(['pwsh','-NoProfile','-File',str(REPO/'scripts/powerbi_model_tools.ps1'),
                        '-Action','Audit','-LibraryDirectory',str(work/'tools'),'-Server',args.server,
                        '-OutputPath',str(audit_path)],check=True,capture_output=True,text=True,timeout=60)
        audit=json.loads(audit_path.read_text(encoding='utf-8-sig'))
        check('structure:12 tables',len(audit['tables']),12,0)
        check('structure:16 relations',len(audit['relationships']),16,0)
        expected_measures = 57
        if args.include_dashboard:
            from build_powerbi_dashboard import MEASURES
            expected_measures += len(MEASURES)
            actual_names = {m['name'] for t in audit['tables'] for m in t['measures']}
            check('mesures de présentation J08 présentes', set(MEASURES).issubset(actual_names), True)
        check('structure:nombre de mesures explicites',sum(len(t['measures']) for t in audit['tables']),expected_measures,0)
        for table in audit['tables']:
            for partition in table['partitions']:
                check('Import:'+table['name'],partition['mode'],'Import')
                check('Partition prête:'+table['name'],partition['state'],'Ready')
            for measure in table['measures']:
                check('Mesure prête:'+measure['name'],measure['state'],'Ready')
                check('Mesure sans erreur:'+measure['name'],measure['errorMessage'],'')
        for relation in audit['relationships']:
            check('Relation active:'+relation['name'],relation['isActive'],True)
            check('Relation *:1:'+relation['name'],[relation['fromCardinality'],relation['toCardinality']],['Many','One'])
            check('Filtrage simple:'+relation['name'],relation['crossFilteringBehavior'],'OneDirection')
        metadata = sql('metadata', '''SELECT COUNT(*) AS fact_rows, COUNT(DISTINCT version_id) AS versions,
          ANY_VALUE(version_id) AS version_id, CAST(MAX(month) AS STRING) AS last_month
          FROM `PROJECT_ID.sncf_dev.fct_reliability_monthly`''')[0]
        live = dax('metadata', 'EVALUATE ROW("fact_rows", COUNTROWS(fct_reliability_monthly), "versions", DISTINCTCOUNT(fct_reliability_monthly[version_id]), "version_id", [source_version], "last_month", FORMAT([last_business_month],"yyyy-MM-dd"), "imported_at_utc", [last_import_utc])')[0]
        for key in metadata:
            check('provenance:' + key, live[key], metadata[key], 0)
        expected_version = json.loads((REPO / 'reports/diagnostic_evidence/validation.json').read_text())['source']['version_id']
        check('version figée J06', live['version_id'], expected_version)
        check('une seule version', live['versions'], 1, 0)

        # Cas métier réels et cas limites choisis par propriétés, pas par numéro de ligne.
        routes = sql('routes', '''SELECT route_key,service_key,departure_station,arrival_station,service_type
          FROM `PROJECT_ID.sncf_dev.fct_reliability_monthly`
          WHERE (departure_station='DIJON VILLE' AND arrival_station='PARIS LYON')
            OR (departure_station='PARIS LYON' AND arrival_station='GRENOBLE')
            OR (departure_station='STRASBOURG' AND arrival_station='NANTES')
            OR (departure_station='GRENOBLE' AND arrival_station='PARIS LYON')
          GROUP BY ALL ORDER BY departure_station,arrival_station,service_type''')
        check('au moins quatre liaisons réelles', len(routes) >= 4, True)
        cases = []
        for route in routes:
            for start, end in [('2025-01-01','2025-01-01'), ('2025-01-01','2025-06-01'),
                               ('2026-01-01','2026-06-01'), ('2025-01-01','2025-12-01'),
                               ('2026-07-01','2026-12-01')]:
                cases.append(dict(route, start=start, end=end, case_id=f'period_{len(cases):02}'))
        edges = sql('edge_cases', '''WITH cases AS (
          SELECT *, CASE WHEN operated_trains_proxy=0 THEN 'zero_denominator'
            WHEN operated_trains_proxy IS NULL THEN 'null_population'
            WHEN arrival_delayed_trains=0 AND is_arrival_delay_rate_usable THEN 'zero_rate'
            WHEN operated_trains_proxy BETWEEN 1 AND 29 AND is_arrival_delay_rate_usable THEN 'low_volume'
            END AS edge_type
          FROM `PROJECT_ID.sncf_dev.fct_reliability_monthly`)
          SELECT route_key,service_key,CAST(month AS STRING) AS month,edge_type FROM cases
          WHERE edge_type IS NOT NULL
          QUALIFY ROW_NUMBER() OVER(PARTITION BY edge_type ORDER BY month DESC,route_key)=1''')
        for edge in edges:
            cases.append(dict(edge, case_id=edge['edge_type'], start=edge['month'], end=edge['month']))
        check('cas zéro réellement disponible', 'zero_rate' in {e['edge_type'] for e in edges}, True)
        check('cas dénominateur nul réellement disponible', 'zero_denominator' in {e['edge_type'] for e in edges}, True)
        dump(run / 'cases.json', cases)
        reference = (REPO / 'analyses/sql/j07_reconciliation.sql').read_text(encoding='utf-8')
        metric_names = ['observed_months','expected_months','arrival_valid_months','cancellation_valid_months',
                        'important_valid_months','observation_coverage','arrival_delay_rate','composite_regularity_rate',
                        'cancellation_rate','over_30_delay_rate','over_60_delay_rate','over_30_delay_count','over_60_delay_count']
        sql_parts, dax_parts = [], []
        for case in cases:
            query = reference
            for key in ['route_key','service_key']:
                query = query.replace('@' + key, "'" + case[key] + "'")
            for key in ['start','end']:
                query = query.replace('@' + key + '_month', "DATE '" + case[key] + "'")
            sql_parts.append("SELECT '" + case['case_id'] + "' AS case_id, r.* FROM (\n" + query + '\n) r')
            last = date.fromisoformat(case['end'])
            last = last.replace(day=calendar.monthrange(last.year,last.month)[1])
            projection = ', '.join(dax_string(m) + ', [' + m + ']' for m in metric_names)
            filters = f'TREATAS({{{dax_string(case["route_key"])}}},dim_route[route_key]),TREATAS({{{dax_string(case["service_key"])}}},dim_service[service_key]),DATESBETWEEN(dim_date[date_key],{dax_date(case["start"])},{dax_date(last)})'
            dax_parts.append(f'CALCULATETABLE(ROW("case_id",{dax_string(case["case_id"])},{projection}),{filters})')
        expected = sql('monthly', '\nUNION ALL\n'.join(sql_parts))
        actual = dax('monthly', 'EVALUATE UNION(\n' + ',\n'.join(dax_parts) + '\n)')
        compare('mensuel', actual, expected, ['case_id'])

        metrics = [side + '_' + metric for side in ['current','previous'] for metric in
                   ['arrival_delay_rate','cancellation_rate','composite_regularity_rate','over_30_delay_rate','over_60_delay_rate']]
        metrics += ['arrival_delay_change_pp','deterioration_persistence','underperformance_persistence','change_signal']
        expected = sql('comparison', '''SELECT route_key,service_key,comparison_id,''' + ','.join(
            'IF(is_comparison_eligible,100*(current_arrival_delay_rate-previous_arrival_delay_rate),NULL) AS arrival_delay_change_pp'
            if m == 'arrival_delay_change_pp' else m for m in metrics) + ' FROM `PROJECT_ID.sncf_dev.mart_route_priorities`')
        actual = dax('comparison', 'EVALUATE SUMMARIZECOLUMNS(dim_route[route_key],dim_service[service_key],dim_comparison[comparison_id],'
                     + ','.join(dax_string(m) + ',[' + m + ']' for m in metrics) + ')')
        compare('comparaisons', actual, expected, ['route_key','service_key','comparison_id'])

        counts = {'candidate_route_count':'COUNT(*)','eligible_route_count':'COUNTIF(is_comparison_eligible)',
                  'deteriorating_route_count':"COUNTIF(change_signal='deterioration')",
                  'improving_route_count':"COUNTIF(change_signal='improvement')",
                  'persistent_underperformance_route_count':'IF(LOGICAL_OR(persistence_applicable),COUNTIF(is_underperformance_persistent),NULL)',
                  'persistent_deterioration_route_count':'IF(LOGICAL_OR(persistence_applicable),COUNTIF(is_deterioration_persistent),NULL)'}
        expected = sql('summary','SELECT comparison_id,' + ','.join(v+' AS '+k for k,v in counts.items()) + ' FROM `PROJECT_ID.sncf_dev.mart_route_priorities` GROUP BY comparison_id')
        actual = dax('summary','EVALUATE SUMMARIZECOLUMNS(dim_comparison[comparison_id],'+','.join(dax_string(m)+',['+m+']' for m in counts)+')')
        compare('synthèse',actual,expected,['comparison_id'])

        # Totaux abusifs : jamais transformer BLANK en un taux national.
        route = routes[0]
        rf = f'TREATAS({{{dax_string(route["route_key"])}}},dim_route[route_key])'
        sf = f'TREATAS({{{dax_string(route["service_key"])}}},dim_service[service_key])'
        mf = 'DATESBETWEEN(dim_date[date_key],DATE(2026,1,1),DATE(2026,1,31))'
        guard_cases = [('all_routes','arrival_delay_rate',[sf,mf]),
                       ('all_services','arrival_delay_rate',[rf,mf]),
                       ('partial_days','arrival_delay_rate',[rf,sf,'DATESBETWEEN(dim_date[date_key],DATE(2026,1,1),DATE(2026,1,15))']),
                       ('cause_filter','arrival_delay_rate',[rf,sf,mf,'TOPN(1,ALL(dim_cause),dim_cause[cause_key])']),
                       ('comparison_total','current_arrival_delay_rate',[]),
                       ('comparison_calendar','current_arrival_delay_rate',[rf,sf,mf,'TREATAS({"2026_h1_vs_2025_h1"},dim_comparison[comparison_id])']),
                       ('causes_multiple_months','published_cause_share',[rf,sf,'DATESBETWEEN(dim_date[date_key],DATE(2026,1,1),DATE(2026,2,28))','TOPN(1,ALL(dim_cause),dim_cause[cause_key])']),
                       ('causes_total','published_cause_share',[rf,sf,mf])]
        expressions = []
        for name, measure, filters in guard_cases:
            expr = '[' + measure + ']'
            if filters: expr = 'CALCULATE(' + expr + ',' + ','.join(filters) + ')'
            expressions.append('ROW("case_id",'+dax_string(name)+',"value",'+expr+')')
        for row in dax('guards','EVALUATE UNION('+','.join(expressions)+')'):
            check('garde:'+row['case_id'],row['value'],None)

        # Les parts restent au grain publié ; contrôler un mois, plusieurs causes et liaisons.
        expected = sql('causes', '''SELECT route_key,service_key,cause_key,published_cause_pct AS published_cause_raw_pct,
          IF(is_cause_profile_usable,published_cause_pct/100,NULL) AS published_cause_share,cause_profile_status
          FROM `PROJECT_ID.sncf_dev.fct_delay_causes_monthly` WHERE month=DATE '2026-01-01' ''')
        actual = dax('causes','EVALUATE SUMMARIZECOLUMNS(dim_route[route_key],dim_service[service_key],dim_cause[cause_key],'+mf+',"published_cause_raw_pct",[published_cause_raw_pct],"published_cause_share",[published_cause_share],"cause_profile_status",[cause_profile_status])')
        # SUMMARIZECOLUMNS écarte les combinaisons sans fait si toutes les mesures sont BLANK.
        compare('causes',actual,expected,['route_key','service_key','cause_key'])

        # Les rangs proviennent du diagnostic J06 figé, sans nouveau classement sous filtre.
        import csv
        with (REPO/'reports/diagnostic_evidence/route_degradation.csv').open(encoding='utf-8-sig',newline='') as handle:
            expected = [{k:(int(row[k]) if row[k] else None) if k.endswith('_rank') else row[k]
                         for k in ['route_key','service_key','comparison_id','deterioration_rank','underperformance_rank']}
                        for row in csv.DictReader(handle)]
        actual = dax('ranks','EVALUATE SUMMARIZECOLUMNS(dim_route[route_key],dim_service[service_key],dim_comparison[comparison_id],"deterioration_rank",[deterioration_rank],"underperformance_rank",[underperformance_rank])')
        expected = [r for r in expected if r['deterioration_rank'] is not None or r['underperformance_rank'] is not None]
        compare('rangs J06',actual,expected,['route_key','service_key','comparison_id'])
        status = 'passed' if checks and all(c['passed'] for c in checks) else 'failed'
    except Exception as exc:
        status = 'error'
        checks.append(dict(name='execution',passed=False,error=str(exc)))
    finally:
        dump(run/'checks.json',checks)
        dump(run/'jobs.json',jobs)
        result = dict(status=status,run_directory=str(run),checked_at_utc=datetime.now(timezone.utc).isoformat(),
                      checks=len(checks),failed=sum(not x['passed'] for x in checks),
                      limitations=['Test Import avant/après et revue Desktop à consigner séparément.',
                                   'Les hypothèses métier D01–D07 ne sont pas certifiées par la réconciliation.'],
                      code_sha256={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                                   [Path(__file__).resolve(),REPO/'scripts/build_powerbi_project.py',REPO/'scripts/powerbi_model_tools.ps1',REPO/'analyses/sql/j07_reconciliation.sql']})
        dump(run/'validation.json',result)
        print(json.dumps(result,ensure_ascii=False))
    if status!='passed': raise SystemExit(1)


if __name__ == '__main__':
    main()
