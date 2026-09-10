"""Recover mixed-newline copies by retaining original lines across recorded revisions."""
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

repo = Path(__file__).resolve().parents[3]
out = Path('C:/STOCKS/work/gap-resolution-r6-20260910/mixed-recovery')
out.mkdir(exist_ok=False)
targets = {'discovery_value.py': 'f50bd2aa0ae3e78cb509ad9d158f8fcaacd6e90123a42eb2c7d180a50078cb40',
           'discovery_reorganizations.py': '0fa6d8c3c4c5b1cec8023ddc3b3b913631d95cb551f16d7f14e8ae564d492c69'}
revisions = subprocess.check_output(['git', 'rev-list', '--all', '--reflog'], cwd=repo, text=True).splitlines()
report = {}
for name, expected in targets.items():
    blobs = {}
    for revision in revisions:
        result = subprocess.run(['git', 'rev-parse', revision + ':stocks_predictor/' + name], cwd=repo, capture_output=True, text=True)
        if result.returncode == 0:
            blobs.setdefault(result.stdout.strip(), revision)
    versions = {oid: subprocess.check_output(['git','cat-file','blob',oid],cwd=repo).replace(b'\r\n',b'\n').splitlines(keepends=True) for oid in blobs}
    tries = 0
    found = None
    for old_oid, old in versions.items():
        for new_oid, new in versions.items():
            blocks = difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes()
            # Each edit hunk can come from an LF-writing editor or a Windows rewrite.
            if len(blocks) > 18:
                continue
            for mask in range(1 << len(blocks)):
                candidate = b''.join(b''.join(new[j:k]).replace(b'\n',b'\r\n') if mask & (1 << n) else b''.join(new[j:k])
                                     for n, (_, _, _, j, k) in enumerate(blocks))
                tries += 1
                if hashlib.sha256(candidate).hexdigest() == expected:
                    (out / expected).write_bytes(candidate)
                    found = {'old_git_blob': old_oid, 'new_git_blob': new_oid, 'newline_block_mask': mask,
                             'blocks': len(blocks), 'bytes': len(candidate), 'sha256': expected}
                    break
            if found:
                break
        if found:
            break
    report[name] = {'versions':len(versions), 'candidate_hashes':tries, 'recovered':found}
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n',encoding='utf-8')
print(json.dumps(report, indent=2))
