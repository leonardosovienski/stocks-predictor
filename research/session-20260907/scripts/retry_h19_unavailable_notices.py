import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];base=root/'work/h19-cash-expanded-source'
jobs=[];seen=set()
for label in ('complete','corporate','successor'):
    for d in json.loads((base/f'ipe-{label}-notices.json').read_text(encoding='utf-8')):
        if (base/d['local_file']).exists() or d['Link_Download'] in seen:continue
        seen.add(d['Link_Download']);jobs.append([d['local_file'],d['Link_Download']])
(root/'work/h19-notice-retry-batch.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
print(len(jobs))
