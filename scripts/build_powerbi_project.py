"""Préparer les définitions J07 ; aucune transformation métier n'est exécutée en Python.

Le projet actif doit être enregistré par Desktop hors OneDrive. Ce générateur
produit un brouillon model.bim (TMSL) à convertir en TMDL, puis ouvrir/actualiser
dans Desktop. Une génération réussie ne constitue jamais une validation J07.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from google.cloud import bigquery

REPO = Path(__file__).resolve().parents[1]
TABLES = ('dim_date', 'dim_route', 'dim_service', 'dim_cause',
          'fct_reliability_monthly', 'fct_delay_causes_monthly',
          'mart_route_trends', 'mart_route_priorities')
TYPE_MAP = {'STRING': 'string', 'DATE': 'dateTime', 'TIMESTAMP': 'dateTime',
            'DATETIME': 'dateTime', 'INTEGER': 'int64', 'INT64': 'int64',
            'BOOLEAN': 'boolean', 'BOOL': 'boolean', 'NUMERIC': 'double',
            'FLOAT': 'double', 'FLOAT64': 'double'}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def mstring(value):
    return '"' + value.replace('"', '""').replace('\r', '').replace('\n', '#(lf)') + '"'


def native(sql):
    return ['let', '    Source = GoogleBigQuery.Database([BillingProject=pBillingProject, UseStorageApi=false]),',
            '    Project = Source{[Name=pProjectId]}[Data],',
            '    Sql = Text.Replace(' + mstring(sql) + ', "sncf-reliability-analytics.sncf_dev.", pProjectId & "." & pDataset & "."),',
            '    Result = Value.NativeQuery(Project, Sql, null, [EnableFolding=true])', 'in', '    Result']


def column(name, kind, description='Champ repris du modèle SQL qualifié.'):
    result = {'name': name, 'dataType': kind, 'sourceColumn': name,
              'summarizeBy': 'none', 'description': description}
    if kind == 'dateTime':
        result['formatString'] = 'yyyy-MM-dd'
    return result


def table(name, columns, expression, hidden=False):
    return {'name': name, 'description': 'J07 — ' + name + ' ; voir docs/powerbi_model.md.',
            'isHidden': hidden, 'columns': columns,
            'partitions': [{'name': name, 'mode': 'import', 'source': {'type': 'm', 'expression': expression}}]}


def measures():
    values = []
    def add(name, expression, description, fmt='0.00%', folder='Fiabilité', hidden=False):
        item = {'name': name, 'expression': expression, 'description': description,
                'displayFolder': folder, 'isHidden': hidden}
        if fmt:
            item['formatString'] = fmt
        values.append(item)
    add('single_route_service', 'HASONEVALUE(dim_route[route_key]) && HASONEVALUE(dim_service[service_key])',
        'Contexte restreint à une liaison orientée et un service.', None, 'Contrôles', True)
    add('complete_month_selection', 'COUNTROWS(dim_date) > 0 && COUNTROWS(dim_date) = SUMX(VALUES(dim_date[month]), DAY(EOMONTH(dim_date[month], 0)))',
        'Refuse les jours partiels ; les sélections doivent contenir tous les jours de chaque mois.', None, 'Contrôles', True)
    add('monthly_context_allowed', '[single_route_service] && [complete_month_selection] && NOT ISFILTERED(dim_cause)',
        'Protège les faits mensuels des agrégations interliaisons/services et de la lecture par cause.', None, 'Contrôles', True)
    add('expected_months', 'IF([monthly_context_allowed], COUNTROWS(VALUES(dim_date[month])))',
        'Nombre de mois sélectionnés dans le calendrier, même absents des faits.', '0', 'Couverture')
    add('observed_months', 'IF([monthly_context_allowed], COALESCE(DISTINCTCOUNT(fct_reliability_monthly[month]), 0))',
        'Mois réellement présents ; zéro signifie ici aucune observation.', '0', 'Couverture')
    add('observation_coverage', 'DIVIDE([observed_months], [expected_months])',
        'Couverture de présence, distincte de la validité propre à chaque indicateur.', '0.0%', 'Couverture')
    f = 'fct_reliability_monthly'
    masks = {'arrival': 'is_arrival_delay_rate_usable', 'cancellation': 'is_cancellation_rate_usable',
             'important': 'is_important_delay_rate_usable', 'important_count': 'is_important_delay_count_usable'}
    for group, mask in masks.items():
        add(group + '_valid_months', f'IF([monthly_context_allowed], COALESCE(CALCULATE(DISTINCTCOUNT({f}[month]), KEEPFILTERS({f}[{mask}] = TRUE())), 0))',
            'Mois utilisables selon le masque dbt ' + mask + '.', '0', 'Couverture')
        add(group + '_coverage', f'DIVIDE([{group}_valid_months], [expected_months])',
            'Couverture valide de l’indicateur, sans suppression des mois attendus.', '0.0%', 'Couverture')
    for name, source, group in [('arrival_delay_count','arrival_delayed_trains','arrival'),
                                ('operated_proxy_count','operated_trains_proxy','arrival'),
                                ('cancelled_count','cancelled_trains','cancellation'),
                                ('scheduled_count','scheduled_trains','cancellation')]:
        add(name, f'IF([monthly_context_allowed] && [{group}_valid_months] = [expected_months], CALCULATE(SUM({f}[{source}]), KEEPFILTERS({f}[{masks[group]}] = TRUE())))',
            'Somme temporelle sur une liaison/service ; indisponible si couverture incomplète. N=P−A non certifié (D01).', '#,0', 'Effectifs')
    add('arrival_delay_rate', 'DIVIDE([arrival_delay_count], [operated_proxy_count])',
        'Σ retards composites publiés / Σ circulations déduites ; D01, population non certifiée.')
    add('cancellation_rate', 'DIVIDE([cancelled_count], [scheduled_count])',
        'Σ annulations publiées / Σ prévus ; convention historique des annulations non certifiée.')
    add('composite_regularity_rate', 'VAR Rate = [arrival_delay_rate] RETURN IF(NOT ISBLANK(Rate), 1 - Rate)',
        'Complément du taux composite ; ne mesure ni les annulations ni une arrivée sans aucune minute de retard.')
    for threshold in (30, 60):
        add(f'over_{threshold}_delay_count', f'IF([monthly_context_allowed], CALCULATE(SUM({f}[over_{threshold}_delay_count]), KEEPFILTERS({f}[is_important_delay_count_usable] = TRUE())))',
            'Somme disponible des mois valides, à lire avec important_count_coverage. Seuils imbriqués non additifs.', '#,0', 'Retards importants')
        add(f'over_{threshold}_delay_rate', f'IF([monthly_context_allowed] && [important_valid_months] = [expected_months], DIVIDE(CALCULATE(SUM({f}[arrival_delayed_over_{threshold}_trains]), KEEPFILTERS({f}[is_important_delay_rate_usable] = TRUE())), CALCULATE(SUM({f}[operated_trains_proxy]), KEEPFILTERS({f}[is_important_delay_rate_usable] = TRUE()))))',
            'Ratio des sommes ; indisponible si un mois invalide, notamment T1 2025. D01.', '0.00%', 'Retards importants')
    add('low_volume_months', f'IF([monthly_context_allowed], COALESCE(CALCULATE(COUNTROWS({f}), KEEPFILTERS({f}[central_counts_compatible] = TRUE()), KEEPFILTERS({f}[operated_trains_proxy] < 30)), 0))',
        'Mois compatibles sous le minimum de classement de 30 ; consultation descriptive permise.', '0', 'Couverture')
    add('monthly_status', 'SWITCH(TRUE(), NOT [single_route_service], "Sélectionner une liaison et un service", NOT [complete_month_selection], "Sélectionner des mois complets", ISFILTERED(dim_cause), "Taux par cause non défini", [observed_months] < [expected_months], "Mois absents", [arrival_valid_months] < [expected_months], "Taux indisponible : population nulle ou effectifs invalides", [low_volume_months] > 0, "Descriptif disponible ; faible volume", "Disponible — population déduite non certifiée D01")',
        'Explique l’indisponibilité ou la réserve métier ; distinct d’un zéro.', None, 'Qualité')
    add('comparison_context_allowed', 'HASONEVALUE(dim_comparison[comparison_id]) && NOT ISFILTERED(dim_date) && NOT ISFILTERED(dim_cause)',
        'Fenêtres fixées par le contrat ; tout filtre direct du calendrier ou des causes invalide leur lecture.', None, 'Contrôles', True)
    p = 'mart_route_priorities'
    for name, flag in [('candidate_route_count',None), ('eligible_route_count','is_comparison_eligible'),
                       ('deteriorating_route_count','deterioration'), ('improving_route_count','improvement'),
                       ('persistent_underperformance_route_count','is_underperformance_persistent'),
                       ('persistent_deterioration_route_count','is_deterioration_persistent')]:
        condition = '' if flag is None else (f', KEEPFILTERS({p}[change_signal] = "{flag}")' if flag in ('deterioration','improvement') else f', KEEPFILTERS({p}[{flag}] = TRUE())')
        applicable = ' && SELECTEDVALUE(dim_comparison[persistence_applicable], FALSE())' if 'persistent' in name else ''
        add(name, f'IF([comparison_context_allowed]{applicable}, COALESCE(CALCULATE(COUNTROWS({p}){condition}), 0))',
            'Nombre de liaisons/service pour une comparaison unique ; jamais un nombre de trains. Persistance annuelle non définie.', '0', 'Comparaisons')
    for side in ('current','previous'):
        for metric in ('arrival_delay_rate','cancellation_rate','composite_regularity_rate','over_30_delay_rate','over_60_delay_rate'):
            add(f'{side}_{metric}', f'IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE({p}[{side}_{metric}]))',
                'Valeur SQL de la fenêtre fixe ' + side + ' ; couverture propre à l’indicateur.', '0.00%', 'Comparaisons')
    add('arrival_delay_change_pp', f'IF([comparison_context_allowed] && [single_route_service] && SELECTEDVALUE({p}[is_comparison_eligible], FALSE()), 100 * ([current_arrival_delay_rate] - [previous_arrival_delay_rate]))',
        'Écart DAX en points entre les ratios de fenêtres ; éligibilité SQL obligatoire.', '0.00 "points"', 'Comparaisons')
    for metric in ('deterioration_persistence','underperformance_persistence'):
        add(metric, f'IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE({p}[{metric}]))',
            'Part de mois selon la règle 4/6 ; valeur SQL, annuelle indisponible.', '0.0%', 'Comparaisons')
    add('change_signal', f'IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE({p}[change_signal]))',
        'Signal SQL comparé avant arrondi ; ±2 points, seuil du portfolio.', None, 'Comparaisons')
    add('comparison_status', 'IF(NOT [comparison_context_allowed], "Choisir une comparaison fixe sans filtre de calendrier ni de cause", "Fenêtres fixes ; minimum 30/mois, seuil 2 points, cible fictive 90 %")',
        'Rappelle que les fenêtres et critères ne suivent pas le calendrier libre.', None, 'Qualité')
    for metric in ('deterioration_rank','underperformance_rank'):
        add(metric, f'IF([comparison_context_allowed] && [single_route_service], SELECTEDVALUE(route_diagnostic[{metric}]))',
            'Rang J06 sur la population initiale ; filtrer une liaison ne reclasse pas les autres. Ex æquo conservés.', '0', 'Priorités')
    c='fct_delay_causes_monthly'
    guard='[single_route_service] && [complete_month_selection] && HASONEVALUE(dim_date[month]) && HASONEVALUE(dim_cause[cause_key])'
    add('published_cause_share', f'IF({guard} && SELECTEDVALUE({c}[is_cause_profile_usable], FALSE()), DIVIDE(SELECTEDVALUE({c}[published_cause_pct]), 100))',
        'Part source convertie de 0–100 à 0–1 pour affichage ; aucun effectif déduit, aucune agrégation.', '0.00%', 'Causes')
    add('published_cause_raw_pct', f'IF({guard}, SELECTEDVALUE({c}[published_cause_pct]))',
        'Valeur source 0–100, y compris profil non exploitable ; à lire avec le statut.', '0.00', 'Causes')
    add('cause_profile_status', f'IF({guard}, SELECTEDVALUE({c}[cause_profile_status]), "Choisir une liaison, un service, un mois et une cause")',
        'Statut SQL du profil ; les anomalies restent consultables.', None, 'Causes')
    for name,col in [('source_version','version_id'),('last_business_month','last_business_month'),('last_import_utc','imported_at_utc')]:
        add(name, f'SELECTEDVALUE(refresh_metadata[{col}])', 'Provenance de la copie importée ; indépendante des sélections métier.', 'yyyy-MM-dd HH:mm:ss' if name=='last_import_utc' else ('yyyy-MM' if name=='last_business_month' else None), 'Provenance')
    return values


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--project',required=True)
    args=parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9-]+',args.project):
        raise ValueError('Identifiant projet invalide.')
    out=Path(args.output).resolve()
    if out.is_relative_to(REPO):
        raise ValueError('Construire le projet actif hors du dépôt et de OneDrive.')
    if 'onedrive' in str(out).lower():
        raise ValueError('Le projet actif doit rester hors OneDrive.')
    reference=json.loads((REPO/'reports/diagnostic_evidence/validation.json').read_text())
    for path,digest in reference['code_sha256'].items():
        if hashlib.sha256((REPO/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('Code amont différent : '+path)
    diagnostic_path=Path(reference['run_directory'])/'route_degradation.sql'
    if hashlib.sha256(diagnostic_path.read_bytes()).hexdigest()!=reference['evidence_sha256']['route_degradation.sql']:
        raise ValueError('SQL compilé J06 différent de sa preuve.')
    diagnostic=diagnostic_path.read_text(encoding='utf-8')
    client=bigquery.Client(project=args.project)
    model={'culture':'fr-FR','defaultPowerBIDataSourceVersion':'powerBI_V3',
           'sourceQueryCulture':'fr-FR', 'discourageImplicitMeasures':True,
           'dataAccessOptions':{'legacyRedirects':True,'returnErrorValuesAsNull':False},
           'tables':[], 'relationships':[], 'expressions':[],
           'annotations':[{'name':'__PBI_TimeIntelligenceEnabled','value':'0'}]}
    for name,value in [('pProjectId',args.project),('pBillingProject',args.project),('pDataset','sncf_dev'),('pExpectedVersion',reference['source']['version_id'])]:
        model['expressions'].append({'name':name,'kind':'m','expression':mstring(value)+' meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]', 'description':'Paramètre de connexion/provenance ; ne contient aucun secret.'})
    objects={}
    for name in TABLES:
        obj=client.get_table(args.project+'.sncf_dev.'+name,timeout=30)
        objects[name]={'rows':obj.num_rows,'modified':obj.modified.isoformat(),'schema':[x.to_api_repr() for x in obj.schema]}
        columns=[]
        for field in obj.schema:
            # Les tableaux de motifs deviennent du texte de présentation, jamais des lignes.
            kind='string' if field.mode=='REPEATED' else TYPE_MAP[field.field_type]
            item=column(field.name,kind,field.description or 'Champ dbt qualifié ; contrat J01–J06 inchangé.')
            item['isHidden']=not name.startswith('dim_') or field.name.endswith('_key') or field.name in ('normalized_field','source_field','is_month_start','date_key','month')
            columns.append(item)
        expression=['let','    Source = GoogleBigQuery.Database([BillingProject=pBillingProject, UseStorageApi=false]),',
                    '    Project = Source{[Name=pProjectId]}[Data],','    Dataset = Project{[Name=pDataset, Kind="Schema"]}[Data],',
                    '    Data = Dataset{[Name="'+name+'", Kind="Table"]}[Data]']
        if any(x.mode=='REPEATED' for x in obj.schema):
            # BigQuery connecteur fournit généralement les champs imbriqués en JSON texte.
            expression[-1]+=','
            conversions = ', '.join('{'+mstring(x.name)+', each if _ = null then null else if Value.Is(_, type list) then Text.Combine(_, "; ") else Text.From(_), type text}' for x in obj.schema if x.mode=='REPEATED')
            expression+=['    Result = Table.TransformColumns(Data, {'+conversions+'})']
        else:
            expression[-1]+=','
            expression+=['    Result = Data']
        if any(x.name=='version_id' for x in obj.schema):
            expression[-1]+=','
            expression+=['    Versions = List.Distinct(Result[version_id]),','    Checked = if List.Count(Versions) = 1 and Versions{0} = pExpectedVersion then Result else error "Version source inattendue ou multiple"','in','    Checked']
        else:
            expression+=['in','    Result']
        model['tables'].append(table(name,columns,expression,hidden=name.startswith('mart_')))
    diagnostic_job=client.query(diagnostic,location='EU',job_config=bigquery.QueryJobConfig(dry_run=True,use_query_cache=False),timeout=30)
    dcolumns=[column(x.name,'string' if x.mode=='REPEATED' else TYPE_MAP[x.field_type]) for x in diagnostic_job.schema]
    for c in dcolumns:c['isHidden']=True
    diagnostic_display = "SELECT * EXCEPT(exclusion_reasons), ARRAY_TO_STRING(exclusion_reasons, '; ') AS exclusion_reasons FROM (\n"+diagnostic+"\n)"
    model['tables'].append(table('route_diagnostic',dcolumns,native(diagnostic_display),True))
    comparison_fields=['comparison_id','current_start','current_end','previous_start','previous_end','expected_months','persistence_applicable']
    ptable=next(t for t in model['tables'] if t['name']=='mart_route_priorities')
    comp_columns=[{**c,'isHidden':c['name']!='comparison_id'} for c in ptable['columns'] if c['name'] in comparison_fields]
    model['tables'].append(table('dim_comparison',comp_columns,['let','    Result = Table.Distinct(Table.SelectColumns(mart_route_priorities, {'+', '.join(mstring(x) for x in comparison_fields)+'}))','in','    Result']))
    metadata_sql='SELECT ANY_VALUE(version_id) AS version_id, MAX(month) AS last_business_month, CURRENT_TIMESTAMP() AS imported_at_utc, COUNT(DISTINCT version_id) AS version_count FROM `sncf-reliability-analytics.sncf_dev.fct_reliability_monthly`'
    model['tables'].append(table('refresh_metadata',[column('version_id','string'),column('last_business_month','dateTime'),column('imported_at_utc','dateTime'),column('version_count','int64')],native(metadata_sql),True))
    measure_table=table('kpi_measures',[column('_anchor','int64')],['#table(type table [_anchor=Int64.Type], {{1}})'])
    measure_table['columns'][0]['isHidden']=True
    measure_table['measures']=measures()
    model['tables'].append(measure_table)
    for target in ('fct_reliability_monthly','fct_delay_causes_monthly','mart_route_trends','mart_route_priorities','route_diagnostic'):
        for dim,key in [('dim_route','route_key'),('dim_service','service_key')]:
            model['relationships'].append({'name':target+'_'+dim,'fromTable':target,'fromColumn':key,'toTable':dim,'toColumn':key,'crossFilteringBehavior':'oneDirection'})
        if target in ('mart_route_priorities','route_diagnostic'):
            dim='dim_comparison';key='comparison_id';to_key=key
        else:
            dim='dim_date';key='month';to_key='date_key'
        model['relationships'].append({'name':target+'_'+dim,'fromTable':target,'fromColumn':key,'toTable':dim,'toColumn':to_key,'crossFilteringBehavior':'oneDirection'})
    model['relationships'].append({'name':'causes_category','fromTable':'fct_delay_causes_monthly','fromColumn':'cause_key','toTable':'dim_cause','toColumn':'cause_key','crossFilteringBehavior':'oneDirection'})
    model_path=out/'draft_model.bim'
    save(model_path,{'name':'SNCF_Reliability','compatibilityLevel':1606,'model':model})
    save(out/'build_evidence.json',{'status':'draft_not_desktop_validated','source_run':reference['run_id'],'objects':objects,'diagnostic_dry_run_bytes':diagnostic_job.total_bytes_processed,'model_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest()})
    save(out/'measure_catalog.json',measures())
    print(json.dumps({'draft':str(model_path),'tables':len(model['tables']),'measures':len(measures()),'relationships':len(model['relationships'])}))


if __name__=='__main__':
    main()
