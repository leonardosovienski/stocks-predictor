"""Collect R6 reproducibility records and the five recovered original code objects."""
import hashlib
import gzip
import json
from pathlib import Path
import shutil

repo = Path(__file__).resolve().parents[3]
work = Path('C:/STOCKS/work/gap-resolution-r6-20260910')
dest = repo/'docs/research/2026-09-10-r6/evidence'
dest.mkdir(exist_ok=False)
objects = repo/'research/session-20260910/gap_resolution/exact_objects'
objects.mkdir(exist_ok=False)
names = ['h20-restoration.json','h20-complete-numeric-reconciliation.json','quote-refresh.json',
         'source15-audit.json','source15-changes.json']
for name in names:
    shutil.copyfile(work/name,dest/name)
for directory in ('git-recovery','archive-recovery','mixed-recovery','newline-run-recovery'):
    shutil.copyfile(work/directory/'report.json',dest/(directory+'.json'))
    for path in (work/directory).iterdir():
        if len(path.name) == 64 and path.is_file():
            if hashlib.sha256(path.read_bytes()).hexdigest() != path.name:
                raise ValueError('Recovered object name/hash differs')
            shutil.copyfile(path,objects/path.name)
receipts = [json.loads(p.read_text(encoding='utf-8')) for directory in ('raw','raw-02','raw-03','raw-04')
            for p in sorted((work/directory).glob('*.receipt.json'))]
(dest/'acquisitions.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8')
manifest = {p.relative_to(repo).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for directory in (dest,objects) for p in sorted(directory.iterdir()) if p.is_file()}
record_root = repo/'docs/research/2026-09-10-r6'
original_manifest = (json.dumps(manifest,indent=2)+'\n').encode('utf-8')
(record_root/'manifest-v1.json').write_bytes(original_manifest)
key = 'docs/research/2026-09-10-r6/evidence/h20-complete-numeric-reconciliation.json'
original = (repo/key).read_bytes()
compressed = gzip.compress(original,compresslevel=9,mtime=0)
if hashlib.sha256(gzip.decompress(compressed)).hexdigest() != manifest.pop(key):
    raise ValueError('Lossless compression check failed')
(repo/(key+'.gz')).write_bytes(compressed)
(repo/key).unlink()
manifest[key+'.gz'] = hashlib.sha256(compressed).hexdigest()
manifest['docs/research/2026-09-10-r6/manifest-v1.json'] = hashlib.sha256(original_manifest).hexdigest()
(record_root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'evidence_files':len(manifest),'recovered_exact_objects':len(list(objects.iterdir())),
                  'public_attempts':len(receipts),'downloaded_bytes':sum(r.get('bytes',0) for r in receipts)}))
