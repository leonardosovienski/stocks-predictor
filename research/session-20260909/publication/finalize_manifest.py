"""Finalize current entry points and resolve deduplicated paths after doc edits."""
import collections
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path('C:/STOCKS')
REPO = ROOT / 'stocks-predictor'
PUB = REPO / 'research/session-20260909/publication'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    entry = ROOT / 'COMECE_AQUI.md'
    original = entry.read_text(encoding='utf-8')
    notice = ('> Continuidade consolidada: leia o [prompt integral final](stocks-predictor/docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md) '
              'e o [pacote publicado](stocks-predictor/research/session-20260909/publication/README.md). '
              'A auditoria ainda não foi executada. O documento anterior de revisão abaixo é contexto; '
              'o novo prompt contém as 24 frentes e os critérios finais.\n\n')
    if not original.startswith(notice):
        entry.write_text(notice + original, encoding='utf-8', newline='')
    manifest_path = PUB / 'MANIFEST.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    repaired = []
    for row in manifest['files']:
        if not row['status'].startswith('PUBLISHED_'):
            continue
        local = ROOT / row['local_relative_path']
        target = REPO / row['repository_path']
        if row['local_relative_path'] == 'COMECE_AQUI.md':
            row['sha256'] = digest(local)
            row['bytes'] = local.stat().st_size
        if not target.is_file() or digest(target) != row['sha256']:
            assert digest(local) == row['sha256'], row['local_relative_path']
            target = PUB / 'local' / row['local_relative_path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(local, target)
            row['repository_path'] = target.relative_to(REPO).as_posix()
            row['status'] = 'PUBLISHED_SNAPSHOT'
            repaired.append(row['local_relative_path'])
    manifest['counts'] = dict(collections.Counter(row['status'] for row in manifest['files']))
    manifest['current_entry_points_updated_after_inventory'] = ['COMECE_AQUI.md']
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    shutil.copyfile(Path(__file__), PUB / 'finalize_manifest.py')
    print(json.dumps({'resolved_paths': repaired, 'counts': manifest['counts']}))


if __name__ == '__main__':
    main()
