import collections
import json
from pathlib import Path
m=json.loads(Path(r'C:\STOCKS\work\MANIFESTO_DADOS.json').read_text(encoding='utf-8'))
files=m['files']
dbs=[r for r in files if r['path'].endswith(('.db','.sqlite','.sqlite3'))]
sidecars=[r for r in files if any(r['path']==db['path']+s for db in dbs for s in ('-wal','-shm','-journal'))]
print('SIDECARS',json.dumps(sidecars,ensure_ascii=False))
print('DB unique bytes',sum({r['sha256']:r['size'] for r in dbs}.values()))
select=[]
for r in files:
    p=r['path']
    if p.endswith(('SHA256.json','source-revision.json','expected-audit.json','source-protocol.json','signals.json')) and ('closure' in p or 'FONTES' in p or 'AUDITORIA' in p or 'continuation-14' in p): select.append(r)
print('SOURCE BUNDLE POINTERS',json.dumps(select,ensure_ascii=False))
Path(r'C:\STOCKS\work\data-completion-r2-20260909\needed-file-index.json').write_text(json.dumps(dict(sidecars=sidecars,source_pointers=select),indent=2),encoding='utf-8')
