"""Materialize a source delta against a verified parent without changing either input."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_file(root, name):
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
        raise ValueError(f'unsafe manifest path: {name}')
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'path escapes input: {name}')
    return path


def materialize(parent, revision, output, parent_sha, revision_sha):
    parent, revision, output = (p.resolve() for p in (parent, revision, output))
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (parent, revision)):
        raise ValueError('output must be a new, separate directory')
    for root, expected in ((parent, parent_sha), (revision, revision_sha)):
        if digest(root / 'SHA256.json') != expected:
            raise ValueError('manifest identity mismatch')
    base = json.loads((parent / 'SHA256.json').read_text(encoding='utf-8'))
    target = json.loads((revision / 'SHA256.json').read_text(encoding='utf-8'))
    for name, expected in base.items():
        if digest(safe_file(parent, name)) != expected:
            raise ValueError('parent payload changed: ' + name)
    selected = {}
    for name, expected in target.items():
        candidate = safe_file(revision, name)
        if not candidate.is_file():
            candidate = safe_file(parent, name)
        if digest(candidate) != expected:
            raise ValueError('revision payload missing or changed: ' + name)
        selected[name] = candidate
    output.mkdir(parents=True, exist_ok=False)
    for name, source in selected.items():
        dest = safe_file(output, name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        if digest(dest) != target[name]:
            raise ValueError('copy integrity mismatch: ' + name)
    shutil.copyfile(revision / 'SHA256.json', output / 'SHA256.json')
    return {'status': 'PASS', 'files': len(selected), 'parent_manifest_sha256': parent_sha,
            'revision_manifest_sha256': revision_sha, 'output': str(output),
            'scope': 'Byte completeness and identity, not economic or historical publication certification.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('parent', 'revision', 'output'):
        parser.add_argument('--' + arg, type=Path, required=True)
    parser.add_argument('--parent-sha', required=True)
    parser.add_argument('--revision-sha', required=True)
    args = parser.parse_args()
    result = materialize(args.parent, args.revision, args.output, args.parent_sha, args.revision_sha)
    args.output.with_suffix('.receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
