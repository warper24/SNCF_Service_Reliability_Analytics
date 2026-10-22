"""Pages techniques J07 en PBIR, à ouvrir et vérifier dans Desktop.

Ce script utilise la structure tableEx enregistrée par Desktop 2.159.883.0.
Il refuse d'écraser un rapport contenant d'autres pages que celles du contrôle.
La conception du rapport métier reste au jalon J08.
"""
import argparse
import hashlib
import json
from pathlib import Path


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')


def identity(value):
    return hashlib.sha256(value.encode()).hexdigest()[:20]


def field(table, name, measure=False):
    return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':name}}


def literal(value):
    return {'expr':{'Literal':{'Value':"'"+value.replace("'","''")+"'"}}}


def filters(items):
    result=[]
    for table,name,value in items:
        result.append({'name':identity(table+name),'field':field(table,name),'type':'Categorical',
                       'filter':{'Version':2,'From':[{'Name':'d','Entity':table,'Type':0}],
                                 'Where':[{'Condition':{'In':{'Expressions':[{'Column':{'Expression':{'SourceRef':{'Source':'d'}},'Property':name}}],
                                                             'Values':[[{'Literal':{'Value':"'"+value+"'"}}]]}}}]}})
    return {'filters':result}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-directory',required=True)
    args=parser.parse_args()
    work=Path(args.work_directory).resolve()
    if 'onedrive' in str(work).lower(): raise ValueError('Utiliser le projet actif hors OneDrive.')
    pages=work/'SNCF_Reliability.Report/definition/pages'
    initial='95123be04912a2df40e9'
    names=[initial,identity('j07_monthly'),identity('j07_causes')]
    if any(p.is_dir() and p.name not in names for p in pages.iterdir()):
        raise ValueError('Des pages extérieures au contrôle J07 existent : ne pas les écraser.')

    def visual(page, name, title, columns, measures, y, height, width=1500, vid=None):
        vid=vid or identity(name)
        projections=[]
        for table,col,label in columns:
            projections.append({'field':field(table,col),'queryRef':table+'.'+col,'nativeQueryRef':label,'displayName':label})
        for measure,label in measures:
            projections.append({'field':field('kpi_measures',measure,True),
                                'queryRef':'kpi_measures.'+measure,'nativeQueryRef':label,'displayName':label})
        value={'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json',
               'name':vid,'position':{'x':30,'y':y,'z':y,'height':height,'width':width,'tabOrder':y},
               'visual':{'visualType':'tableEx','query':{'queryState':{'Values':{'projections':projections}}},
                         'drillFilterOtherVisuals':False,
                         'objects':{'total':[{'properties':{'totals':{'expr':{'Literal':{'Value':'false'}}}}}],
                                    'values':[{'properties':{'fontSize':{'expr':{'Literal':{'Value':'12D'}}}}}],
                                    'columnHeaders':[{'properties':{'fontSize':{'expr':{'Literal':{'Value':'12D'}}}}}]},
                         'visualContainerObjects':{'title':[{'properties':{'show':{'expr':{'Literal':{'Value':'true'}}},'text':literal(title)}}]}}}
        save(pages/page/'visuals'/vid/'visual.json',value)

    for name,label in zip(names,['J07 · Comparaisons fixes','J07 · Contrôle mensuel','J07 · Causes publiées']):
        page={'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json',
              'name':name,'displayName':label,'displayOption':'FitToPage','height':900,'width':1560}
        if name!=initial:
            page['filterConfig']=filters([('dim_route','departure_station','DIJON VILLE'),('dim_route','arrival_station','PARIS LYON'),
                                          ('dim_service','service_type','National'),('dim_date','month_label','2025-01')])
        save(pages/name/'page.json',page)
    save(pages/'pages.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json',
                           'pageOrder':names,'activePageName':initial})
    visual(initial,'summary','Populations de liaisons/service — fenêtres fixées avant classement',
           [('dim_comparison','comparison_id','Comparaison')],
           [('candidate_route_count','Candidates'),('eligible_route_count','Éligibles'),('deteriorating_route_count','Dégradations ≥2 points'),
            ('improving_route_count','Améliorations ≥2 points'),('persistent_underperformance_route_count','Sous-performance persistante')],
           30,180,vid='4a44c3bb8861ec962bc5')
    visual(initial,'detail','Contrôle des taux et rangs J06 — population déduite non certifiée (D01)',
           [('dim_comparison','comparison_id','Comparaison'),('dim_route','route_label','Liaison orientée'),('dim_service','service_type','Service')],
           [('previous_arrival_delay_rate','Retard précédent'),('current_arrival_delay_rate','Retard courant'),('arrival_delay_change_pp','Écart (points)'),
            ('change_signal','Signal SQL'),('deterioration_rank','Rang dégradation'),('underperformance_rank','Rang sous-performance')],230,500)
    for page in names:
        visual(page,'provenance_'+page,'Copie Import — relire après actualisation ; réserves D01–D07 inchangées',[],
               [('source_version','Version source'),('last_business_month','Dernier mois métier'),('last_import_utc','Lecture métadonnées UTC')],740,150)
    visual(names[1],'monthly','Dijon Ville → Paris Lyon · National · janvier 2025 — filtres de page modifiables',
           [('dim_date','month_label','Mois')],
           [('arrival_delay_count','Retards composites'),('operated_proxy_count','Circulations déduites'),('arrival_delay_rate','Taux de retard'),
            ('cancellation_rate','Annulations'),('composite_regularity_rate','Régularité composite')],30,180)
    visual(names[1],'coverage','Présence et validité sont distinctes — un taux indisponible n’est pas zéro',[],
           [('expected_months','Mois attendus'),('observed_months','Mois observés'),('arrival_coverage','Couverture retards'),
            ('important_coverage','Couverture >30/>60'),('over_30_delay_rate','Taux >30'),('over_60_delay_rate','Taux >60')],230,180)
    visual(names[1],'status','Statut de lecture',[],[('monthly_status','Statut')],440,200)
    visual(names[2],'causes','Dijon Ville → Paris Lyon · National · janvier 2025 — aucune conversion en effectifs',
           [('dim_cause','cause_label','Cause publiée')],
           [('published_cause_raw_pct','Valeur source (0–100)'),('published_cause_share','Part utilisable'),('cause_profile_status','Statut SQL')],30,500)
    print(json.dumps({'pages':names,'status':'generated_requires_desktop_review'}))


if __name__=='__main__':main()
