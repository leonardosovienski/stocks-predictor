import sys, json, concurrent.futures
from pathlib import Path
root = Path.cwd()
sys.path.insert(0, str(root / 'work'))
from explore_b3_events import fetch
jobs = json.loads((root / 'outputs/h17-event-source-acquisition.json').read_text(encoding='utf-8'))
jobs = [j for j in jobs if any(r['status'] not in {'ACQUIRED', 'CACHED'} for r in j.get('results', []))]
def collect(j):
    out = {'cnpj': j['cnpj'], 'codeCVM': j['codeCVM']}
    try:
        d = fetch('GetDetail', {'codeCVM': j['codeCVM'], 'language': 'pt-br'}, f"b3-h17-{j['codeCVM']}-detail")
        out['detail'] = d
        if not isinstance(d, dict) or not d.get('issuingCompany'):
            out['status'] = 'NO_DETAIL'
            return out
        name = f"b3-h17-{j['codeCVM']}-current-supplement"
        data = fetch('GetListedSupplementCompany', {'issuingCompany': d['issuingCompany'], 'language': 'pt-br'}, name)
        out.update(status='ACQUIRED', source_file=name+'.json', returned_codes=[r.get('codeCVM') for r in data])
    except Exception as e:
        out.update(status='FAILED', error=str(e))
    return out
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    result = list(pool.map(collect, jobs))
(root/'outputs/h17-event-source-followup.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
for r in result:
    print(r['codeCVM'], r['status'], r.get('detail', {}).get('issuingCompany') if isinstance(r.get('detail'), dict) else '', r.get('returned_codes'))
