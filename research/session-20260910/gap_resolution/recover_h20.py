"""Find exact sealed bytes in all local Git blobs, including text encodings."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def recover(repo, output):
    output.mkdir(parents=True, exist_ok=False)
    original = json.loads((repo / 'docs/audit/2026-09-10-integral/evidence/h20-omissions.json').read_text(encoding='utf-8'))
    wanted = {row['sha256']: row['package_path'] for row in original['remaining_missing']}
    inventory = subprocess.check_output(['git', 'cat-file', '--batch-all-objects', '--batch-check'], cwd=repo, text=True)
    selected = []
    total = 0
    for row in inventory.splitlines():
        oid, kind, size = row.split()
        if kind == 'blob' and int(size) <= 10_000_000:
            selected.append(oid)
            total += int(size)
    if total > 200_000_000:
        raise ValueError(f'Git byte budget exceeded: {total}')
    payload = subprocess.check_output(['git', 'cat-file', '--batch'], cwd=repo, input=('\n'.join(selected) + '\n').encode())
    offset = 0
    found = {}
    trials = 0
    for oid in selected:
        end = payload.index(b'\n', offset)
        size = int(payload[offset:end].split()[2])
        data = payload[end + 1:end + 1 + size]
        offset = end + 1 + size + 1
        variants = {'raw': data}
        if b'\x00' not in data:
            plain = data.removeprefix(b'\xef\xbb\xbf').replace(b'\r\n', b'\n')
            variants.update(lf=plain, crlf=plain.replace(b'\n', b'\r\n'), bom_lf=b'\xef\xbb\xbf' + plain,
                            bom_crlf=b'\xef\xbb\xbf' + plain.replace(b'\n', b'\r\n'))
        for variant, candidate in variants.items():
            trials += 1
            digest = hashlib.sha256(candidate).hexdigest()
            if digest in wanted and digest not in found:
                (output / digest).write_bytes(candidate)
                found[digest] = {'git_blob': oid, 'transform': variant, 'package_path': wanted[digest], 'bytes': len(candidate)}
    report = {'scope': 'All locally stored Git blobs <=10MB, including unreachable objects; exact SHA256 only',
              'git_blobs': len(selected), 'git_bytes': total, 'candidate_hashes': trials, 'recovered': found,
              'remaining': [{'sha256': digest, 'package_path': path} for digest, path in wanted.items() if digest not in found]}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    recover(Path(__file__).resolve().parents[3], args.output)
