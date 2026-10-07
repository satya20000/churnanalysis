"""Validate analytical edge cases, model references and published PBIR JSON schemas."""
from pathlib import Path
import json, urllib.request, urllib.parse, tempfile, hashlib, subprocess
import pandas as pd
import numpy as np
import jsonschema
from data_processing import ROOT,OUT
from cohort_analysis import kaplan_meier

def verify():
    model=json.loads((ROOT/'powerbi/SaaS.SemanticModel/model.bim').read_text())['model']
    tables={t['name']:{c['name'] for c in t['columns']} for t in model['tables']}
    measures={m['name'] for t in model['tables'] for m in t.get('measures',[])}
    for r in model['relationships']:
        assert r['fromColumn'] in tables[r['fromTable']]
        assert r['toColumn'] in tables[r['toTable']]
        assert r['crossFilteringBehavior']=='oneDirection'
    for t,p,k in [('DimAccount','data/raw/accounts.csv','account_id'),('DimPlan','data/raw/plans.csv','plan_id'),('DimDate','data/processed/dim_date.csv','date')]:
        d=pd.read_csv(ROOT/p,keep_default_na=False);assert d[k].is_unique and not (d[k]=='').any()
    co=pd.read_csv(OUT/'cohort_retention.csv');assert co.loc[co.observable==0,'retention'].isna().all()
    assert co.loc[co.observable==1,'retention'].between(0,1).all()
    # Non-trivial survival edge case: tied event+censoring; final event drives survival to zero.
    km=kaplan_meier([1,1,2],[True,False,True]);assert np.isclose(km.iloc[1].survival,2/3) and km.iloc[-1].survival==0
    for file in (ROOT/'powerbi/SaaS.Report/definition').rglob('visual.json'):
        v=json.loads(file.read_text());pos=v['position'];assert pos['x']>=0 and pos['y']>=0 and pos['x']+pos['width']<=1600 and pos['y']+pos['height']<=1000
        for role in v['visual']['query']['queryState'].values():
            for p in role['projections']:
                kind=next(iter(p['field']));ref=p['field'][kind];table=ref['Expression']['SourceRef']['Entity'];col=ref['Property']
                assert table in tables
                assert col in (measures if kind=='Measure' else tables[table]),(file,col)
    # Microsoft's public schemas can be validated without Power BI Desktop.
    cache=Path(tempfile.gettempdir())/'saas-pbir-schema-cache';cache.mkdir(exist_ok=True)
    schemas={}
    def fetch(url):
        url=urllib.parse.urldefrag(url)[0]
        if url in schemas:return schemas[url]
        path=cache/(hashlib.sha256(url.encode()).hexdigest()+'.json')
        if not path.exists():
            subprocess.run(['curl','-fsSL','--max-time','15',url,'-o',str(path)],check=True, capture_output=True)
        value=json.loads(path.read_text());schemas[url]=value
        if value.get('$id'):schemas[value['$id']]=value
        return value
    checked=[];schema_errors=[]
    for file in sorted((ROOT/'powerbi').rglob('*.json'))+list((ROOT/'powerbi').glob('*.pbip'))+list((ROOT/'powerbi/SaaS.Report').glob('*.pbir')):
        obj=json.loads(file.read_text());url=obj.get('$schema')
        if not url:continue
        try:
            schema=fetch(url)
            resolver=jsonschema.RefResolver(base_uri=url,referrer=schema,handlers={'https':fetch})
            cls=jsonschema.validators.validator_for(schema)
            cls(schema,resolver=resolver).validate(obj)
            checked.append(str(file.relative_to(ROOT)))
        except Exception as e:
            schema_errors.append({'file':str(file.relative_to(ROOT)),'error':str(e)[:1800]})
            break
    result={'model_references':'passed','visual_field_references':'passed','page_geometry':'passed','cohort_censoring':'passed','survival_edge_case':'passed','schema_files_passed':len(checked),'schema_errors':schema_errors,'native_powerbi_desktop':'not available; acceptance pending'}
    (OUT/'validation_receipt.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    if schema_errors:raise ValueError('PBIR schema errors: see validation_receipt.json')
if __name__=='__main__':verify()
