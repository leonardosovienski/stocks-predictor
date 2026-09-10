import collections
import json
import zipfile
from pathlib import Path
root=Path(r'C:\STOCKS')
manifest=json.loads((root/'work/MANIFESTO_DADOS.json').read_text(encoding='utf-8'))
print('manifest keys',list(manifest))
print('file count',len(manifest['files']))
matches=[]
for row in manifest['files']:
    p=row['path'].lower()
    if p.endswith(('.db','.sqlite','.sqlite3')) and '.git/' not in p:
        matches.append(row)
print('database paths',len(matches),'unique identities',len({r['sha256'] for r in matches}))
for r in matches:
    if 'project/data/' in r['path'] or 'revision-13' in r['path'] or 'rev13' in r['path'] or 'revision-14' in r['path'] or 'rev14' in r['path'] or 'closure' in r['path'] or 'canonical' in r['path']:
        print(json.dumps(r,ensure_ascii=False))
(root/'work/data-completion-r2-20260909/database-candidates.json').write_text(json.dumps(matches,indent=2),encoding='utf-8')
with zipfile.ZipFile(root/'DADOS_STOCKS.zip') as archive:
    print('zip entries',len(archive.infolist()))
    print('first entries',[(r.filename,r.file_size,r.compress_size) for r in archive.infolist()[:12]])
print('manifest top-level db identities',dict(collections.Counter(r['path'].split('/')[0] for r in matches)))
