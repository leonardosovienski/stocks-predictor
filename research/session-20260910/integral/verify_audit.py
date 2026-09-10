"""Verify the published audit evidence identities and cross-references (stdlib)."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(root):
    registry = json.loads((root / 'registry.json').read_text(encoding='utf-8'))
    collections = ('evidence', 'claims', 'issues', 'decisions', 'fronts', 'datasets', 'uses', 'runs')
    ids = []
    for key in collections:
        ids.extend(item['id'] for item in registry[key])
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate registry ID')
    identity = set(ids)
    for item in registry['evidence']:
        target = (root / item['path']).resolve()
        if not target.is_relative_to(root.resolve()):
            raise ValueError('evidence path escapes audit directory')
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != item['sha256']:
            raise ValueError('evidence identity mismatch: ' + item['id'])

    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ('evidence', 'issues', 'claims', 'decisions') and isinstance(child, list):
                    for ref in child:
                        if isinstance(ref, str) and ref not in identity:
                            raise ValueError('unknown registry reference: ' + ref)
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(registry)
    if len(registry['fronts']) != 24 or len(registry['uses']) != 7:
        raise ValueError('mandatory coverage/use count mismatch')
    if '{{' in (root / 'README.md').read_text(encoding='utf-8'):
        raise ValueError('unrendered report placeholder')
    if registry['round']['new_independent_market_evidence'] != 0:
        raise ValueError('replay must not be promoted to new market evidence')
    return {'status': 'PASS_ARTIFACT_INTEGRITY_ONLY',
            'registry_sha256': hashlib.sha256((root / 'registry.json').read_bytes()).hexdigest(),
            'counts': {key: len(registry[key]) for key in collections},
            'limitation': 'Hashes and references are verified, not economic truth or external completeness.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-dir', type=Path, default=Path(__file__).resolve().parents[3] / 'docs/audit/2026-09-10-integral')
    args = parser.parse_args()
    print(json.dumps(verify(args.audit_dir), ensure_ascii=False, indent=2))
