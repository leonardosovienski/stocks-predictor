"""Find exact historical mixed newlines, constrained by the preserved file size."""
import hashlib
import json
from pathlib import Path
import subprocess

repo = Path(__file__).resolve().parents[3]
out = Path('C:/STOCKS/work/gap-resolution-r6-20260910/newline-run-recovery')
out.mkdir(exist_ok=False)
targets = [('discovery_value.py',19089,'f50bd2aa0ae3e78cb509ad9d158f8fcaacd6e90123a42eb2c7d180a50078cb40'),
           ('discovery_reorganizations.py',16175,'0fa6d8c3c4c5b1cec8023ddc3b3b913631d95cb551f16d7f14e8ae564d492c69')]
report = []
for name, target_size, expected in targets:
    ref = 'f9987faa06d53a273e080719c9cf35a1fc48ca53:stocks_predictor/' + name
    oid = subprocess.check_output(['git','rev-parse',ref],cwd=repo,text=True).strip()
    data = subprocess.check_output(['git','cat-file','blob',oid],cwd=repo)
    lines = data.splitlines(keepends=True)
    plain_count = len(data) + data.count(b'\n') - target_size
    attempts = 0
    found = None
    for first_count in range(plain_count, 0, -1):
        second_count = plain_count - first_count
        for start in range(len(lines) - first_count + 1):
            for second in (range(start + first_count, len(lines) - second_count + 1) if second_count else [len(lines)]):
                candidate = b''.join(line if start <= i < start + first_count or second <= i < second + second_count
                                     else line.replace(b'\n',b'\r\n') for i,line in enumerate(lines))
                attempts += 1
                if hashlib.sha256(candidate).hexdigest() == expected:
                    (out/expected).write_bytes(candidate)
                    found = {'sha256':expected,'git_blob':oid,'bytes':len(candidate),
                             'lf_lines_1based':list(range(start+1,start+first_count+1)) + list(range(second+1,second+second_count+1))}
                    break
            if found:
                break
        if found:
            break
    report.append({'name':name,'attempts':attempts,'recovered':found})
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
