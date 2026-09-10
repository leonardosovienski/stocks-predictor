"""Validate the publication snapshot without executing archived scripts."""
from __future__ import annotations

import ast
import collections
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main() -> None:
    manifest = json.loads((PACKAGE / 'MANIFEST.json').read_text(encoding='utf-8'))
    counts = collections.Counter()
    for row in manifest['files']:
        counts[row['status']] += 1
        if row['status'].startswith('PUBLISHED_'):
            path = (ROOT / row['repository_path']).resolve()
            assert path.is_relative_to(ROOT), row['local_relative_path']
            assert path.is_file(), row['repository_path']
            assert path.stat().st_size == row['bytes'], row['repository_path']
            assert sha256(path) == row['sha256'], row['repository_path']
    assert dict(counts) == manifest['counts']
    prompt = ROOT / 'docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md'
    text = prompt.read_text(encoding='utf-8')
    assert [int(n) for n in re.findall(r'^# FRENTE (\d+)', text, re.M)] == list(range(1, 25))
    assert 'valor_das_posicoes + caixa + recebiveis - obrigacoes' in text
    assert 'Trabalhe sozinho, sem agentes auxiliares.' in text
    assert 'não criar venv;' in text
    assert '- envie ordens;' in text
    assert text.startswith('Quero que você faça uma AUDITORIA TÉCNICA INTEGRAL')
    assert text.endswith('dentro dos limites autorizados.\n')
    scripts = list(PACKAGE.rglob('*.py'))
    for script in scripts:
        ast.parse(script.read_text(encoding='utf-8-sig'), filename=str(script))
    patterns = {
        'github_token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
        'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
        'aws_access_key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
        'slack_token': re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{20,}\b'),
        'openai_key': re.compile(r'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}\b'),
    }
    findings = []
    for path in PACKAGE.rglob('*'):
        if not path.is_file():
            continue
        content = path.read_text(encoding='utf-8-sig', errors='replace')
        for rule, pattern in patterns.items():
            if pattern.search(content):
                findings.append({'path': str(path.relative_to(ROOT)), 'rule': rule})
    assert not findings, json.dumps(findings)
    active_documents = ['AGENTS.md', 'README.md', 'HANDOFF.md', 'STOCKS_CURRENT_STATE.md', 'docs/DOCUMENTATION_INDEX.md', 'docs/continuation/PROMPT_NOVO_CHAT.md']
    for rel in active_documents:
        assert 'PROMPT_AUDITORIA_INTEGRAL_20260909.md' in (ROOT / rel).read_text(encoding='utf-8')
    links_checked = 0
    for document in [*(ROOT / rel for rel in active_documents), PACKAGE / 'README.md']:
        content = document.read_text(encoding='utf-8')
        if document != PACKAGE / 'README.md':
            content = '\n'.join(content.splitlines()[:30])
        for link in re.findall(r'\]\(([^)\n]+)\)', content):
            if link.startswith(('https://', 'http://', '#')):
                continue
            target = (document.parent / link.split('#', 1)[0]).resolve()
            assert target.is_file(), f'{document.name}: {link}'
            links_checked += 1
    result = {
        'status': 'passed',
        'manifest_sha256': sha256(PACKAGE / 'MANIFEST.json'),
        'prompt_sha256': sha256(prompt),
        'prompt_fronts': 24,
        'inventory_counts': dict(counts),
        'python_files_syntax_checked_not_executed': len(scripts),
        'entry_point_local_links_checked': links_checked,
        'targeted_secret_pattern_findings': findings,
        'targeted_scan_is_not_exhaustive_secret_audit': True,
        'production_checks': 'Separate Linux GitHub Actions; no production dependencies installed locally',
        'economic_results_recalculated': False,
        'all_local_data_bytes_uploaded': False,
    }
    (PACKAGE / 'VALIDATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
