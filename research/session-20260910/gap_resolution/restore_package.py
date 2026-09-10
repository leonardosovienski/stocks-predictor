"""Restore and independently hash every file in the unchanged original H20 manifest."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

root = Path('C:/STOCKS')
work = root/'work/gap-resolution-r6-20260910'
out = work/'h20-complete-package'
out.mkdir(exist_ok=False)
recoveries = [root/'work/audit-integral-20260910/recovered-h20-code-objects']
recoveries += [work/name for name in ('git-recovery','archive-recovery','newline-run-recovery')]
restored = {}
with zipfile.ZipFile(root/'DADOS_STOCKS.zip') as archive:
    name = 'objects/51eed47cc7985a9d8f0be7ca14527871caeba2d9f8cacfb10d4abf423cb7f7fa'
    original_manifest = archive.read(name)
    if hashlib.sha256(original_manifest).hexdigest() != name.split('/')[1]:
        raise ValueError('Manifest seal differs')
    (out/'validation-manifest.json').write_bytes(original_manifest)
    manifest = json.loads(original_manifest)
    available = set(archive.namelist())
    for name, expected in manifest['files'].items():
        path = (out/name).resolve()
        if not path.is_relative_to(out.resolve()):
            raise ValueError('Unsafe original member')
        path.parent.mkdir(parents=True, exist_ok=True)
        if 'objects/' + expected in available:
            with archive.open('objects/' + expected) as src, path.open('xb') as dst:
                shutil.copyfileobj(src,dst,1024*1024)
            origin = 'DADOS_STOCKS.zip'
        else:
            found = next((directory/expected for directory in recoveries if (directory/expected).is_file()),None)
            if found is None:
                raise FileNotFoundError(name)
            with found.open('rb') as src, path.open('xb') as dst:
                shutil.copyfileobj(src,dst)
            origin = str(found)
        with path.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest() != expected:
                raise ValueError('Restored bytes differ: ' + name)
        restored[name] = {'sha256':expected,'origin':origin,'bytes':path.stat().st_size}
result = subprocess.run([sys.executable,str(out/'rodar_validacao.py'),'--output-dir',str(work/'h20-original-verifier-unused'),'--verify-only'],capture_output=True,text=True)
report = {'status':'PASS' if result.returncode == 0 else 'FAIL','files':len(restored),
          'bytes':sum(v['bytes'] for v in restored.values()), 'manifest_sha256':hashlib.sha256(original_manifest).hexdigest(),
          'original_verifier_exit':result.returncode,'original_verifier_stdout':result.stdout,'original_verifier_stderr':result.stderr,
          'outer_original_zip_recreated':False,'profit_certified':False,'restored':restored}
(work/'h20-restoration.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'restored'},indent=2))
raise SystemExit(result.returncode)
