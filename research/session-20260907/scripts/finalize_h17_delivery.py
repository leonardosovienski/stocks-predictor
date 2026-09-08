from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess,zipfile
root=Path.cwd();repo=root/'work/stocks-predictor';pack=root/'work/h17-run-pack-v2';out=root/'outputs'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
shutil.copyfile(out/'H17_RESULTADO.md',pack/'RESULTADO.md')
shutil.copyfile(out/'h17-reproduction-verification.json',pack/'results/h17-reproduction-verification.json')
subprocess.run(['git','archive','--format=zip','--output='+str(pack/'audit/stocks-code.zip'),'HEAD'],cwd=repo,check=True)
(pack/'audit/changes-from-previous-delivery.patch').write_bytes(subprocess.check_output(['git','diff','8b3c3fcd32ffecdf0bfe328f6f80b247b9800174','HEAD'],cwd=repo))
archive=out/'stocks-h17-pronto-final.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(pack.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:z.write(p,p.relative_to(pack).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 files=z.namelist()
manifest={'packaged_at_utc':datetime.now(timezone.utc).isoformat(),'archive':archive.name,'sha256':sha(archive),
 'bytes':archive.stat().st_size,'files':len(files),'crc_check':'PASS','code_commit':'4f487098e702004a88f02fe65d62a008c6df618b',
 'repository_delivery_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
 'corrected_observation_sha256':sha(out/'h17-corrected-observation.json')}
(out/'h17-final-package-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
template=(root/'work/h17_launch_template.py').read_text(encoding='utf-8')
(out/'RODAR_H17.py').write_text(template.replace('ARCHIVE_SHA256_PLACEHOLDER',manifest['sha256']).replace('stocks-h17-pronto.zip',archive.name),encoding='utf-8')
print(json.dumps(manifest,indent=2))
