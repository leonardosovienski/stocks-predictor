"""Negative source acceptance checks against real captured data; no returns."""
import importlib.util
import json
from pathlib import Path
import zipfile

root=Path(r'C:\STOCKS\work\h21-source-closure-20260909')
script=Path(r'C:\STOCKS\stocks-predictor\research\session-20260909\source_closure\reconcile_quotes.py')
spec=importlib.util.spec_from_file_location('reconciliation',script)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
checks=[]
out=root/'negative-validation'
out.mkdir(exist_ok=False)
prior=Path(r'C:\STOCKS\work\h21\inputs')
calendar=root/'calendar-2026.json'
raw=root/'raw'/'COTAHIST_A2026.complete.ZIP'

def reject(name, source, cal, expected, message=None):
    destination=out/name
    try:
        module.run(source,prior,cal,destination)
    except expected as error:
        if message: assert message in str(error), str(error)
        assert not destination.exists(), 'Rejected source must not create accepted output'
        checks.append(dict(check=name,result='PASS_REJECTED',exception=type(error).__name__,detail=str(error)))
    else: raise AssertionError(name+' wrongly accepted')

bad=out/'hash-mismatch.ZIP'
bad.write_bytes(b'not the captured bytes')
bad.with_name(bad.name+'.source.json').write_text(raw.with_name(raw.name+'.source.json').read_text(encoding='utf-8'),encoding='utf-8')
reject('hash-mismatch',bad,calendar,ValueError,'Source hash differs')
reject('truncated-transport',root/'raw'/'COTAHIST_A2026.latest.ZIP',calendar,zipfile.BadZipFile)
badcal=json.loads(calendar.read_text(encoding='utf-8'))
badcal['closed_equity_dates'].append('2026-07-09')
calpath=out/'wrong-calendar.json'
calpath.write_text(json.dumps(badcal),encoding='utf-8')
reject('false-july-closure',raw,calpath,ValueError,'Calendar coverage mismatch')
v1=json.loads((root/'normalized-v1'/'quotes-2018-20260908.json').read_text(encoding='utf-8'))
v2=json.loads((root/'normalized-v2'/'quotes-2018-20260908.json').read_text(encoding='utf-8'))
assert v1['records']==v2['records']
checks.append(dict(check='v2-only-provenance-no-price-change',result='PASS',records=len(v2['records'])))
(root/'local-validation.json').write_text(json.dumps(dict(checks=checks,economic_valuations=0),indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks),flush=True)
