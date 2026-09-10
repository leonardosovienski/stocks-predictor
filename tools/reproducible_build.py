"""Build twice from one clean revision, compare all distribution bytes, keep a receipt."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def distribution_hashes(directory):
    wheels = list(directory.glob('*.whl'))
    sources = list(directory.glob('*.tar.gz'))
    if len(wheels) != 1 or len(sources) != 1:
        raise ValueError('expected exactly one wheel and one source distribution')
    # uv also writes a .gitignore. It is not a Python distribution.
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in wheels + sources}


def main():
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
        raise ValueError('build requires a clean committed checkout')
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    epoch = subprocess.check_output(['git', 'show', '-s', '--format=%ct', 'HEAD'], cwd=ROOT, text=True).strip()
    env = {**os.environ, 'SOURCE_DATE_EPOCH': epoch, 'PYTHONHASHSEED': '0'}
    first = ROOT / 'dist'
    if first.exists():
        raise ValueError('dist already exists; build in a fresh checkout')
    with tempfile.TemporaryDirectory(prefix='stocks-build-') as scratch:
        second = Path(scratch) / 'dist'
        outputs = []
        for dest in (first, second):
            subprocess.run(['uv', 'build', '--no-build-isolation', '--offline', '--out-dir', str(dest)],
                           cwd=ROOT, env=env, check=True)
            outputs.append(distribution_hashes(dest))
        if outputs[0] != outputs[1]:
            raise ValueError(f'non-reproducible distributions: {outputs}')
    receipt = {'status': 'PASS', 'head': sha, 'source_date_epoch': epoch,
               'python': sys.version, 'distributions': outputs[0],
               'scope': 'Two isolated output directories, same controlled environment; not a cross-OS identity claim.'}
    (ROOT / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
