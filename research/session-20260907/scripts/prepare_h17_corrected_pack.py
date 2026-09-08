from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
root=Path.cwd();repo=root/'work/stocks-predictor';old=root/'work/h17-run-pack';pack=root/'work/h17-run-pack-v2'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
shutil.copytree(old,pack,ignore=shutil.ignore_patterns('__pycache__'))
(pack/'audit').mkdir()
shutil.copyfile(old/'manifest.json',pack/'audit/first-manifest.json')
shutil.copyfile(old/'code/stocks_predictor/discovery_h17.py',pack/'audit/first-code.py')
shutil.copyfile(root/'outputs/h17-first-observation.json',pack/'audit/first-observation.json')
shutil.copyfile(root/'outputs/h17-first-run.txt',pack/'audit/first-run.txt')
shutil.copyfile(root/'outputs/h17-full-tests.txt',pack/'audit/first-full-tests.txt')
shutil.copyfile(repo/'docs/research/2026-09-07-h17-first-observation.md',pack/'audit/correction.md')
shutil.copyfile(repo/'stocks_predictor/discovery_h17.py',pack/'code/stocks_predictor/discovery_h17.py')
shutil.copyfile(repo/'tests/test_discovery_h17.py',pack/'audit/test_discovery_h17.py')
manifest={'prepared_at_utc':datetime.now(timezone.utc).isoformat(),'stage':'BEFORE_CORRECTED_H17_OBSERVATION_AFTER_DISCLOSED_MEASUREMENT_BUGFIX',
 'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
 'first_observation_sha256':sha(root/'outputs/h17-first-observation.json'),
 'files_sha256':{p.relative_to(pack).as_posix():sha(p) for p in sorted(pack.rglob('*')) if p.is_file() and p!=pack/'manifest.json' and '__pycache__' not in p.parts and 'results' not in p.parts}}
(pack/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('files',len(manifest['files_sha256']),'code',manifest['code_commit'])
