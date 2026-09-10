"""Recreate recorded git-archive commands; accept only the original exact hash."""
import hashlib
import json
from pathlib import Path
import subprocess

repo = Path(__file__).resolve().parents[3]
output = Path('C:/STOCKS/work/gap-resolution-r6-20260910/archive-recovery')
output.mkdir(exist_ok=False)
targets = [
    ('f9987faa06d53a273e080719c9cf35a1fc48ca53', '1cb585bac0c331d166460ae4cbd8b7c2279d7dbdb7cb059e565d6e90ef7850ef'),
    ('b7435087c593af0544cedc9b58c97a312a88d0ac', '1b305395c835a206c9a2f153eea8fd4f85a43d3f172f284c63524e95f619a230'),
]
attempts = []
for commit, expected in targets:
    for compression in ('default', *map(str, range(10))):
        command = ['git', 'archive', '--format=zip']
        if compression != 'default':
            command.append('-' + compression)
        command.append(commit)
        data = subprocess.check_output(command, cwd=repo)
        digest = hashlib.sha256(data).hexdigest()
        attempts.append({'commit': commit, 'compression': compression, 'bytes': len(data), 'sha256': digest, 'match': digest == expected})
        if digest == expected:
            (output / digest).write_bytes(data)
            break
(output / 'report.json').write_text(json.dumps(attempts, indent=2) + '\n', encoding='utf-8')
print(json.dumps(attempts, indent=2))
