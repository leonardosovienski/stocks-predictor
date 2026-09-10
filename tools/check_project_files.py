"""Check tracked Markdown, historical link resolutions and one generated index."""
import argparse
import hashlib
import json
import posixpath
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit, quote

ROOT = Path(__file__).resolve().parents[1]
INDEX = 'docs/DOCUMENTATION_INDEX.md'
HISTORY = 'docs/maintenance/2026-09-10-files/historical-links.json'
CURRENT = {'README.md', 'AGENTS.md', 'CLAUDE.md', 'HANDOFF.md', 'STOCKS_CURRENT_STATE.md', INDEX}
REQUIRED = CURRENT | {'pyproject.toml', 'uv.lock', 'main.py', 'config.yaml', 'config_rj.yaml',
                      '.github/workflows/ci.yml', '.gitattributes', '.gitignore', '.gitleaks.toml',
                      '.gitleaksignore', 'stocks_predictor/__init__.py', 'stocks_predictor/__main__.py',
                      'stocks_predictor/operations.py', 'stocks_predictor/operational_store.py',
                      'tools/build-requirements.txt', 'RESEARCH_FREEZE.md', 'trials.json', 'trials_v2.json',
                      'docs/DESIGN.md', 'docs/RJ_DESIGN.md',
                      'docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md',
                      'docs/continuation/MANDATO_20260909.md',
                      'docs/engineering/2026-09-10-r8/RUNBOOK.md',
                      'docs/continuation/2026-09-10-closure/README.md'}
INLINE = re.compile(r'!?\[[^\]]*\]\((<[^>]*>|[^\s)]*(?:\([^)]*\)[^\s)]*)?)(?:\s+"[^"]*")?\)')
REFERENCE = re.compile(r'^\s{0,3}\[([^\]]+)\]:\s*(<[^>]+>|\S+)')


def tracked(root):
    return set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode('utf-8').split('\0')) - {''}


def markdown_links(content):
    """Inline/image links and explicit reference links, excluding fenced code."""
    fence = None
    references = {}
    lines = []
    for number, line in enumerate(content.splitlines(), 1):
        marker = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if marker:
            if fence is None:
                fence = marker.group(1)
            elif marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        lines.append((number, line))
        definition = REFERENCE.match(line)
        if definition:
            references[definition.group(1).casefold()] = definition.group(2).strip('<>')
    for number, line in lines:
        if REFERENCE.match(line):
            continue
        # Inline code can contain Markdown examples; it does not create links.
        line = re.sub(r'(`+)(.*?)\1', '', line)
        for match in INLINE.finditer(line):
            yield number, match.group(1).strip('<>')
        for match in re.finditer(r'\[([^\]]+)\]\[([^\]]*)\]', line):
            key = (match.group(2) or match.group(1)).casefold()
            if key not in references:
                raise ValueError(f'undefined Markdown reference at line {number}: {key}')
            yield number, references[key]


def destination(document, target, files):
    parsed = urlsplit(target)
    if parsed.scheme or target.startswith('//'):
        return 'EXTERNAL', None
    relative = unquote(parsed.path)
    path = posixpath.normpath(posixpath.join(posixpath.dirname(document), relative)) if relative else document
    if path.startswith('../') or path.startswith('/'):
        return 'OUTSIDE_REPOSITORY', path
    if (path == '.' and files) or path in files or any(name.startswith(path.rstrip('/') + '/') for name in files):
        return 'TRACKED', path
    return 'MISSING_OR_CASE_MISMATCH', path


def classification(name):
    if name in CURRENT:
        return 'ENTRADA_ATUAL'
    if name in {'RESEARCH_FREEZE.md', 'docs/DESIGN.md', 'docs/RJ_DESIGN.md'}:
        return 'PROTOCOLO_PRESERVADO'
    if '/publication/local/' in name or name.startswith('vendor/'):
        return 'COPIA_HISTORICA_PRESERVADA'
    if name.endswith('RUNBOOK.md') or name.endswith('REPRODUCTION.md'):
        return 'REPRODUCAO_COM_ESCOPO_DATADO'
    return 'REGISTRO_DATADO'


def render_index(documents):
    lines = ['# Índice completo dos Markdown', '',
             'Gerado por `python tools/check_project_files.py --write-index` a partir dos arquivos no Git.',
             'A CI confere a população, os destinos locais e a atualização deste índice.', '',
             'Comece por [README](../README.md), [estado atual](../STOCKS_CURRENT_STATE.md),',
             '[HANDOFF](../HANDOFF.md) e [mandato integral](continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md).',
             'A [revisão dos arquivos](maintenance/2026-09-10-files/README.md) explica limpeza,',
             'preservação, dados externos e referências históricas sem destino direto.', '',
             f'{len(documents)} Markdown versionados. Classificação não certifica todas as afirmações históricas.',
             'URLs externas e fragmentos/âncoras não são validados por este verificador.', '',
             '| Documento | Papel |', '|---|---|']
    for name in documents:
        link = quote(posixpath.relpath(name, 'docs'), safe='/.-_')
        lines.append(f'| [{name}]({link}) | {classification(name)} |')
    return '\n'.join(lines) + '\n'


def verify(root=ROOT, write_index=False):
    files = tracked(root)
    missing = REQUIRED - files
    if missing:
        raise ValueError('required tracked files missing: ' + ', '.join(sorted(missing)))
    if {'requirements.txt', 'pytest.ini'} & files:
        raise ValueError('obsolete duplicate configuration restored; pyproject.toml and uv.lock are canonical')
    for name in files:
        if not (root / name).is_file():
            raise ValueError('tracked file absent from checkout: ' + name)
    documents = sorted(name for name in files if name.lower().endswith('.md'))
    rendered = render_index(documents)
    if write_index:
        (root / INDEX).write_text(rendered, encoding='utf-8', newline='\n')
    elif (root / INDEX).read_text(encoding='utf-8') != rendered:
        raise ValueError('Markdown index is stale; run --write-index and review the diff')
    history = json.loads((root / HISTORY).read_text(encoding='utf-8'))
    exceptions = {(x['document'], x['line'], x['target']): x for x in history['links']}
    if len(exceptions) != len(history['links']):
        raise ValueError('duplicate historical exception')
    for row in history['documents']:
        if hashlib.sha256((root / row['path']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('historical Markdown changed: ' + row['path'])
    used = set()
    links = external = 0
    for name in documents:
        content = (root / name).read_text(encoding='utf-8-sig')
        if '\x00' in content or '\ufffd' in content:
            raise ValueError('invalid text content: ' + name)
        for number, target in markdown_links(content):
            state, resolved = destination(name, target, files)
            if state == 'EXTERNAL':
                external += 1
                continue
            links += 1
            if state == 'TRACKED':
                continue
            key = name, number, target
            if key not in exceptions:
                raise ValueError(f'{name}:{number}: missing tracked link {target} ({resolved})')
            exception = exceptions[key]
            if exception['resolution'] == 'TRACKED_CONTEXT_MAPPING':
                mapped = exception['repository_path']
                if mapped not in files and not any(p.startswith(mapped.rstrip('/') + '/') for p in files):
                    raise ValueError('historical mapping target missing: ' + mapped)
            elif exception['resolution'] != 'UNPRESERVED_HISTORICAL_DERIVATIVE':
                raise ValueError('unknown historical resolution')
            used.add(key)
    if used != set(exceptions):
        raise ValueError('historical exception population changed')
    return {'status': 'PASS', 'tracked_files': len(files), 'markdown_files': len(documents),
            'local_links': links, 'historical_context_links': len(used), 'external_links_not_checked': external,
            'unresolved_current_links': 0, 'scope': 'Tracked files and supported Markdown link destinations; not economic completeness.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-index', action='store_true')
    args = parser.parse_args()
    print(json.dumps(verify(write_index=args.write_index), indent=2))
