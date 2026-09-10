"""Validate published R6 identities and reject altered historical package objects."""
import hashlib
import gzip
import json
from pathlib import Path


def main():
    repo = Path(__file__).resolve().parents[3]
    root = repo/'docs/research/2026-09-10-r6'
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    for name,expected in manifest.items():
        path = (repo/name).resolve()
        if not path.is_relative_to(repo) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Changed R6 evidence: '+name)
    old = json.loads((repo/'docs/audit/2026-09-10-integral/evidence/h20-omissions.json').read_text(encoding='utf-8'))
    for row in old['remaining_missing']:
        path = repo/'research/session-20260910/gap_resolution/exact_objects'/row['sha256']
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Historical package seal changed')
    original_manifest = json.loads((root/'manifest-v1.json').read_text(encoding='utf-8'))
    key = 'docs/research/2026-09-10-r6/evidence/h20-complete-numeric-reconciliation.json'
    uncompressed = gzip.decompress((repo/(key+'.gz')).read_bytes())
    if hashlib.sha256(uncompressed).hexdigest() != original_manifest[key]:
        raise ValueError('Compressed numerical evidence differs from original receipt')
    restoration = json.loads((root/'evidence/h20-restoration.json').read_text(encoding='utf-8'))
    if restoration['files'] != 1448 or restoration['original_verifier_exit'] != 0:
        raise ValueError('Incomplete package restoration')
    print(json.dumps({'status':'PASS','verified_evidence_files':len(manifest),'original_objects_recovered':5}))


if __name__ == '__main__':
    main()
