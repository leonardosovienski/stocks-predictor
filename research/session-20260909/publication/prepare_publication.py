"""Publish authored session artifacts; inventory raw data without redistributing it."""
from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path('C:/STOCKS')
REPO = ROOT / 'stocks-predictor'
WORK = ROOT / 'work/publication-20260909'
PUB = REPO / 'research/session-20260909/publication'
BASE = '7de0ea9ad5e9c34e695c49a2c720561cad283685'


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='')


def selected(path: Path) -> tuple[bool, str]:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    if '__pycache__' in parts or path.suffix in {'.pyc', '.pyo'}:
        return False, 'LOCAL_RUNTIME_CACHE'
    if len(parts) == 1:
        return path.suffix in {'.md', '.json'}, 'ORIGINAL_MIGRATION_BINARY'
    if parts[0] in {'instructions', 'outputs'}:
        return True, ''
    if parts[0] == 'FONTES_WEB_ORIGINAIS':
        return path.suffix in {'.md', '.json', '.txt'}, 'THIRD_PARTY_CAPTURE'
    if parts[0] == 'data':
        return rel.as_posix() in {'data/README.md', 'data/CATALOG.json', 'data/recovery-r2/catalog.json'}, 'LOCAL_MARKET_DATA_OR_RECOVERED_SOURCE'
    if parts[0] == 'work':
        if 'raw' in parts or 'public' in parts:
            return path.name.endswith('.source.json'), 'RAW_SOURCE_OR_HTTP_CAPTURE'
        if any(p in parts for p in ('text', 'visual', 'visual-qa')):
            return False, 'THIRD_PARTY_DOCUMENT_DERIVATIVE'
        if path.suffix.lower() in {'.zip', '.pdf', '.png', '.jpg', '.headers', '.partial'}:
            return False, 'RAW_SOURCE_OR_HTTP_CAPTURE'
        return True, ''
    return False, 'OUTSIDE_AUTHORED_DELIVERY_SCOPE'


def main() -> None:
    PUB.mkdir(parents=True, exist_ok=True)
    prompt = WORK / 'PROMPT_AUDITORIA_INTEGRAL_20260909.md'
    body = prompt.read_text(encoding='utf-8')
    assert len(re.findall(r'^# FRENTE \d+', body, re.M)) == 24
    assert body.endswith('dentro dos limites autorizados.\n')
    for target in (REPO / 'docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md', ROOT / 'instructions/PROMPT_AUDITORIA_INTEGRAL_20260909.md'):
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(prompt, target)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=REPO).decode().split('\0')
    hashes: dict[str, str] = {}
    for rel in tracked:
        path = REPO / rel
        if rel and path.is_file():
            hashes.setdefault(digest(path), rel)
    hashes[digest(prompt)] = 'docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md'
    files = []
    for directory in ROOT.iterdir():
        if directory == REPO:
            continue
        if directory.is_file():
            files.append(directory)
        elif directory.is_dir():
            files.extend(p for p in directory.rglob('*') if p.is_file() and not p.is_relative_to(WORK))
    records = []
    counts = collections.Counter()
    for index, path in enumerate(sorted(files), 1):
        rel = path.relative_to(ROOT).as_posix()
        before = path.stat()
        sha = digest(path)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError(f'Source changed while reading: {rel}')
        include, reason = selected(path)
        entry = {'local_relative_path': rel, 'bytes': before.st_size, 'sha256': sha}
        if include:
            if sha in hashes:
                destination = hashes[sha]
                entry['status'] = 'PUBLISHED_IDENTICAL_CONTENT'
            else:
                target = PUB / 'local' / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
                assert digest(target) == sha
                destination = target.relative_to(REPO).as_posix()
                hashes[sha] = destination
                entry['status'] = 'PUBLISHED_SNAPSHOT'
            entry['repository_path'] = destination
        else:
            entry.update(status='LOCAL_ONLY', reason=reason)
        counts[entry['status']] += 1
        records.append(entry)
        if index % 400 == 0:
            print(json.dumps({'hashed_files': index, 'total_files': len(files)}), flush=True)
    manifest = {
        'schema_version': 1,
        'snapshot_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'base_sha': BASE,
        'local_root': str(ROOT),
        'repository': 'https://github.com/leonardosovienski/stocks-predictor',
        'scope': 'All existing files outside checkout, excluding the transient publication staging directory; Git files retain their existing history.',
        'all_local_bytes_uploaded': False,
        'raw_market_data_uploaded': False,
        'publication_helper': 'prepare_publication.py',
        'counts': dict(counts),
        'files': records,
    }
    write(PUB / 'MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    write(PUB / '.gitattributes', 'local/** -text !eol\nMANIFEST.json -text !eol\nVALIDATION.json -text !eol\n')
    shutil.copyfile(Path(__file__), PUB / 'prepare_publication.py')
    print(json.dumps({'counts': dict(counts), 'snapshot_bytes': sum(r['bytes'] for r in records if r['status'] == 'PUBLISHED_SNAPSHOT'), 'local_only_bytes': sum(r['bytes'] for r in records if r['status'] == 'LOCAL_ONLY'), 'manifest': str(PUB / 'MANIFEST.json')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
