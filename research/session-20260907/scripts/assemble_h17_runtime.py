from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
root=Path.cwd();repo=root/'work/stocks-predictor';pack=root/'work/h17-run-pack'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
(pack/'code/stocks_predictor').mkdir(parents=True,exist_ok=True)
for name in ('__init__.py','discovery_h17.py'):
 shutil.copyfile(repo/'stocks_predictor'/name,pack/'code/stocks_predictor'/name)
primary=pack/'sources';primary.mkdir(exist_ok=True)
panel=json.loads((pack/'data/events.json').read_text(encoding='utf-8'))
for row in panel['sources']:
 source=root/'work/source-acquisition'/row['path']
 if sha(source)!=row['sha256']:raise ValueError('source changed')
 shutil.copyfile(source,primary/source.name)
 metadata=source.with_suffix('.source.json')
 if metadata.exists():shutil.copyfile(metadata,primary/metadata.name)
 alias=row.get('alias')
 if alias:
  source=root/'work/source-acquisition'/alias['detail_source'];shutil.copyfile(source,primary/source.name)
  metadata=source.with_suffix('.source.json')
  if metadata.exists():shutil.copyfile(metadata,primary/metadata.name)
prep=pack/'preparation-record';prep.mkdir(exist_ok=True)
for name in ('extract_h17_identity_v3.py','prepare_h17_sources.py','build_h17_event_panel.py','fetch_h17_crosscheck.py','fetch_h17_alias_actions.py','merge_h17_secondary_actions.py','prepare_h17_run_pack.py'):
 shutil.copyfile(root/'work'/name,prep/name)
for name in ('h17-event-source-acquisition.json','h17-event-source-followup.json','h17-secondary-action-acquisition.json','h17-secondary-alias-acquisition.json'):
 shutil.copyfile(root/'outputs'/name,prep/name)
shutil.copyfile(repo/'docs/research/2026-09-07-h17-registration.md',pack/'registration.md')
manifest={'prepared_at_utc':datetime.now(timezone.utc).isoformat(),'stage':'BEFORE_FIRST_H17_CANDIDATE_RETURN_OBSERVATION',
 'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
 'files_sha256':{p.relative_to(pack).as_posix():sha(p) for p in sorted(pack.rglob('*')) if p.is_file() and p.name!='manifest.json' and '__pycache__' not in p.parts and 'results' not in p.parts}}
(pack/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('files',len(manifest['files_sha256']),'bytes',sum(p.stat().st_size for p in pack.rglob('*') if p.is_file()),'code',manifest['code_commit'])
