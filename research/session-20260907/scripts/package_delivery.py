import hashlib
import json
import pathlib
import zipfile
from inspect_state import ROOT,REPO,CANON,digest

out=ROOT/'outputs'
manifest={'commit':'13184fb24ad44b5b94f2653d467e7ebba92881b4','branch':'audit/stocks-readiness-20260906',
          'base_commit':'d48d05dc590c7e14a9186e7097c048c3020a6a53','pushed':False,
          'tests':{'passed':385,'seconds':94.56,'python':'3.13.14','core':'3.2.0','ruff':'0.16.5','ruff_result':'PASS','migration_check':'PASS'},
          'readiness_audit':{'status':'NOT_READY','expected_exit_code':2,'monetary_unit_mismatched_rows':69024,'version_date_company_periods':80},
          'operational_database_modified':False,'real_trials_executed':0,'protected_hypotheses':['H17','H18','H19'],
          'files':{p.name:digest(p) for p in out.iterdir() if p.is_file() and p.suffix in ('.md','.json','.txt','.patch','.zip')}}
(out/'delivery-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with zipfile.ZipFile(out/'stocks-research-evidence.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!='stocks-research-evidence.zip':
            z.write(p,'deliverables/'+p.name)
    for p in sorted((ROOT/'work/raw').glob('*.zip')):
        z.write(p,'raw/'+p.name)
    for i in (14,15,16):
        p=CANON/f'reports/h{i}_verdict_adhoc.md'
        z.write(p,'original-reports/'+p.name)
with zipfile.ZipFile(out/'stocks-research-evidence.zip') as z:
    assert z.testzip() is None
    assert 'deliverables/stocks-readiness.patch' in z.namelist()
print(json.dumps({'package_bytes':(out/'stocks-research-evidence.zip').stat().st_size,'sha256':digest(out/'stocks-research-evidence.zip')},indent=2))
