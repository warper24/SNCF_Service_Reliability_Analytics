"""Expérience Import isolée dans sncf_test ; aucune table métier n'est modifiée.

create prépare la table et son TMDL temporaire ; actualiser Desktop ensuite.
change vérifie 1 dans le cache, change BigQuery vers 2 et vérifie encore 1.
verify, après une nouvelle actualisation Desktop, exige 2 dans les deux moteurs.
Le TMDL temporaire doit être retiré du projet après la preuve, avant livraison.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from google.cloud import bigquery

REPO = Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=['create','change','verify'],required=True)
    p.add_argument('--project',required=True)
    p.add_argument('--work-directory',required=True)
    p.add_argument('--server',required=True)
    args=p.parse_args()
    work=Path(args.work_directory).resolve()
    if work.is_relative_to(REPO) or 'onedrive' in str(work).lower():
        raise ValueError('Le cache doit rester hors dépôt et OneDrive.')
    proof=work/'import_probe'
    proof.mkdir(exist_ok=True)
    client=bigquery.Client(project=args.project)
    jobs=[]
    def query(sql):
        job=client.query(sql,location='EU',job_config=bigquery.QueryJobConfig(maximum_bytes_billed=100_000_000))
        rows=[dict(r) for r in job.result(timeout=120)]
        jobs.append(dict(job_id=job.job_id,sql=sql,bytes_processed=job.total_bytes_processed))
        return rows
    def local():
        src=proof/'probe.dax'; dst=proof/'probe_latest.json'
        src.write_text('EVALUATE ROW("probe_value",MAX(import_probe[probe_value]))',encoding='utf-8')
        subprocess.run(['pwsh','-NoProfile','-File',str(REPO/'scripts/powerbi_model_tools.ps1'),'-Action','Query',
                        '-LibraryDirectory',str(work/'tools'),'-Server',args.server,'-InputPath',str(src),'-OutputPath',str(dst)],check=True)
        return json.loads(dst.read_text(encoding='utf-8-sig'))[0]['[probe_value]']
    values={}
    table=f'`{args.project}.sncf_test.j07_import_probe`'
    if args.stage=='create':
        query((REPO/'analyses/sql/j07_import_probe.sql').read_text(encoding='utf-8').split('-- Étape')[0].replace('PROJECT_ID',args.project))
        current=query('SELECT probe_value FROM '+table)
        if current!=[{'probe_value':1}]:
            raise ValueError('Expérience déjà utilisée ; conserver les preuves et choisir une nouvelle table explicitement.')
        definition=work/'SNCF_Reliability.SemanticModel/definition'
        target=definition/'tables/import_probe.tmdl'
        if target.exists(): raise ValueError('La définition temporaire existe déjà.')
        target.write_text('''table import_probe
\tisHidden
\tcolumn probe_value
\t\tdataType: int64
\t\tsummarizeBy: none
\t\tsourceColumn: probe_value
\tpartition import_probe = m
\t\tmode: import
\t\tsource =
\t\t\tlet
\t\t\t    Source = GoogleBigQuery.Database([BillingProject=pBillingProject, UseStorageApi=false]),
\t\t\t    Project = Source{[Name=pProjectId]}[Data],
\t\t\t    Dataset = Project{[Name="sncf_test", Kind="Schema"]}[Data],
\t\t\t    Result = Table.SelectColumns(Dataset{[Name="j07_import_probe", Kind="Table"]}[Data], {"probe_value"})
\t\t\tin Result
''',encoding='utf-8')
        with (definition/'model.tmdl').open('a',encoding='utf-8') as f:f.write('\nref table import_probe\n')
        values['sql_initial']=1
    elif args.stage=='change':
        values['dax_before_change']=local()
        if values['dax_before_change']!=1: raise ValueError('Le premier import doit contenir 1.')
        query('UPDATE '+table+' SET probe_value=2,changed_at_utc=CURRENT_TIMESTAMP() WHERE probe_value=1')
        values['sql_after_change']=query('SELECT probe_value FROM '+table)[0]['probe_value']
        values['dax_without_refresh']=local()
        if values!={'dax_before_change':1,'sql_after_change':2,'dax_without_refresh':1}:
            raise ValueError('Le cache Import ne respecte pas le scénario attendu.')
    else:
        values['sql_after_refresh']=query('SELECT probe_value FROM '+table)[0]['probe_value']
        values['dax_after_refresh']=local()
        if set(values.values())!={2}: raise ValueError('La seconde actualisation doit importer 2.')
    result=dict(stage=args.stage,completed_at_utc=datetime.now(timezone.utc).isoformat(),values=values,jobs=jobs)
    target=proof/(args.stage+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()
