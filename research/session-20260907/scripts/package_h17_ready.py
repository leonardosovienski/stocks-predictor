from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess,zipfile
root=Path.cwd();repo=root/'work/stocks-predictor';pack=root/'work/h17-run-pack-v2';out=root/'outputs'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for name in ('2026-09-07-h17-observations.jsonl','2026-09-07-h17-budget-update.json'):
 shutil.copyfile(repo/'docs/research'/name,pack/'audit'/name)
for name in ('h17-build.txt','h17-wheel-smoke.txt'):
 shutil.copyfile(out/name,pack/'results'/name)
shutil.copyfile(out/'H17_RESULTADO.md',pack/'RESULTADO.md')
subprocess.run(['git','archive','--format=zip','--output='+str(pack/'audit/stocks-code.zip'),'HEAD'],cwd=repo,check=True)
patch=subprocess.check_output(['git','diff','8b3c3fcd32ffecdf0bfe328f6f80b247b9800174','HEAD'],cwd=repo)
(pack/'audit/changes-from-previous-delivery.patch').write_bytes(patch)
archive=out/'stocks-h17-pronto.zip'
if archive.exists():raise FileExistsError('Preserve existing delivery; choose a new revision name')
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(pack.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:z.write(p,p.relative_to(pack).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 files=z.namelist()
 archive_hash=sha(archive)
manifest={'packaged_at_utc':datetime.now(timezone.utc).isoformat(),'archive':archive.name,'sha256':archive_hash,
 'bytes':archive.stat().st_size,'files':len(files),'crc_check':'PASS','code_commit':'4f487098e702004a88f02fe65d62a008c6df618b',
 'repository_delivery_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
 'first_observation_preserved':True,'corrected_observation_sha256':sha(out/'h17-corrected-observation.json')}
(out/'h17-package-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
template=root/'work/h17_launch_template.py'
(out/'RODAR_H17.py').write_text(template.read_text(encoding='utf-8').replace('ARCHIVE_SHA256_PLACEHOLDER',archive_hash),encoding='utf-8')
print(json.dumps(manifest,indent=2))
