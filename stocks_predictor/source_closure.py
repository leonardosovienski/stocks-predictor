"""Audit additive primary-source revisions without running historical returns.

The original H19/H20 observations retain their frozen inputs. This separate
entry point measures source completeness after a documented source revision.
"""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from stocks_predictor.continuous_research import inspect_inputs, load_quotes, read, verify_manifest
from stocks_predictor.h20_continuous import SIGNALS_SHA, make_plans
from stocks_predictor.h20_checked import MANIFEST_SHA

SOURCE_PROTOCOL_SHA = 'da8b91a7a263d9870822c58af85b4a47f2c051e932ecb3099fea986ba4456c49'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def without_local_references(value):
    if isinstance(value, list):
        return [without_local_references(v) for v in value]
    if isinstance(value, dict):
        return {k: without_local_references(v) for k, v in value.items() if k != 'verified_primary_file'}
    return value


def audit(base, revised, signals_path, protocol_path):
    if digest(base / 'SHA256.json') != MANIFEST_SHA or digest(protocol_path) != SOURCE_PROTOCOL_SHA:
        raise ValueError('frozen baseline or source protocol changed')
    before, after = verify_manifest(base), verify_manifest(revised)
    source_manifest = digest(revised / 'SHA256.json')
    if digest(signals_path) != SIGNALS_SHA:
        raise ValueError('frozen H20 signals changed')
    required = {'source-revision.json', 'source-lineage.json', 'primary-catalog.json'}
    if not required <= set(after):
        raise ValueError('source revision metadata outside manifest')
    revision = read(revised / 'source-revision.json')
    if (revision['base_manifest_sha256'] != MANIFEST_SHA
            or revision['source_protocol_sha256'] != SOURCE_PROTOCOL_SHA):
        raise ValueError('revision does not bind the registered baseline')
    mutable = {'cash-events.json', 'corporate-actions.json', 'evidence.json', 'tax-calendar.json'}
    if any(after.get(k) != v for k, v in before.items() if k not in mutable):
        raise ValueError('source revision changed frozen plans, quotes or registration')
    if without_local_references(read(revised / 'tax-calendar.json')) != read(base / 'tax-calendar.json'):
        raise ValueError('source revision changed the tax-calendar rules')
    catalog = read(revised / 'primary-catalog.json')
    if any(after.get(k) != v['sha256'] for k, v in catalog.items()):
        raise ValueError('primary source absent from input manifest')

    def check_sources(value):
        if isinstance(value, list):
            for row in value:
                check_sources(row)
        elif isinstance(value, dict):
            if ('file' in value or 'source_file' in value) and ('sha256' in value or 'source_sha256' in value):
                key = value.get('verified_primary_file')
                if key not in catalog or after.get(key) != value.get('sha256', value.get('source_sha256')):
                    raise ValueError('unbound primary-source reference')
            for row in value.values():
                check_sources(row)

    _, index, cash, actions, tax, gate, files = inspect_inputs(revised)
    check_sources([cash, actions, tax, read(revised / 'source-lineage.json')])
    raw = {r['event_id']: r for r in read(base / 'cash-events.json')}
    lines = read(revised / 'source-lineage.json')
    parents = {r['parent_event_id']: r for r in lines}
    if len(parents) != len(lines):
        raise ValueError('duplicate lineage parent')
    child_ids = [eid for line in lines for eid in line['child_event_ids']]
    actual = {r['event_id']: r for r in cash}
    if (len(actual) != len(cash) or len(child_ids) != len(set(child_ids))
            or not set(parents) <= set(raw) or set(raw) & set(child_ids)
            or set(actual) != (set(raw) - set(parents)) | set(child_ids)):
        raise ValueError('source revision lost or duplicated an entitlement')
    for event_id, row in actual.items():
        original = raw[row['parent_event_id']] if event_id in child_ids else raw[event_id]
        keys = ('ticker', 'isin', 'action', 'ex_date')
        if any(row[k] != original[k] for k in keys):
            raise ValueError('revised cash identity changed')
        if event_id not in child_ids and Decimal(row['gross_per_share']) != Decimal(original['gross_per_share']):
            raise ValueError('single-payment nominal amount changed')
    for parent_id, line in parents.items():
        parts = [actual[eid] for eid in line['child_event_ids']]
        total = sum(Decimal(r['gross_per_share']) for r in parts)
        delta = total - Decimal(raw[parent_id]['gross_per_share'])
        if (any(r.get('parent_event_id') != parent_id for r in parts)
                or total != Decimal(line['payment_total']) or abs(delta) > Decimal('0.000000001')
                or delta != Decimal(line['published_rounding_delta'])):
            raise ValueError('lineage does not reconcile installment values')
    old_ev, new_ev = read(base / 'evidence.json'), read(revised / 'evidence.json')
    removed = revision['removed_action_gaps']
    expected = {**old_ev, 'action_gaps': [r for r in old_ev['action_gaps'] if r not in removed]}
    if new_ev != expected or any((r['ticker'], r['ex_date']) not in
                                {(a['ticker'], a['ex_date']) for a in actions} for r in removed):
        raise ValueError('source revision improperly cleared evidence gaps')
    _, quote_count = load_quotes(revised, index)
    plans, _, omitted = make_plans(read(signals_path), index)
    common = [[m['ticker'], m['isin'], p['entry'], nxt['entry']]
              for p, nxt in zip(plans, plans[1:]) for m in p['members']]
    union = {tuple(i) for i in common + new_ev['required_intervals']}
    inherited = {tuple(i) for i in new_ev['required_intervals']}
    issues = gate['issues'] + [{'kind': 'H20_ADDITIONAL_CASH_INTERVAL', 'interval': list(i)}
                              for i in sorted(union - inherited)]
    issues.append({'kind': 'H20_CONTINUOUS_SOURCE_ATTESTATION_MISSING'})
    verify_manifest(revised)
    if digest(revised / 'SHA256.json') != source_manifest:
        raise ValueError('source revision changed during audit')
    return {'status': 'BLOCKED_MISSING_EVIDENCE', 'profit': None, 'future_profit_projection': None,
        'new_historical_return_evaluations': 0, 'administrative_counts': [53, 55],
        'source_manifest_sha256': source_manifest, 'verified_input_files': files,
        'verified_primary_files': len(catalog), 'validated_quote_records': quote_count,
        'raw_entitlements_preserved': len(raw), 'execution_payment_rows': len(cash),
        'complete_installment_schedules': len(lines), 'corporate_actions_integrated': len(actions),
        'missing_payment_dates': sum(not r['payment_date'] for r in cash),
        'missing_net_values': sum(r.get('net_per_share') is None for r in cash),
        'conservative_required_intervals': len(union), 'unavailable_signal_dates': omitted,
        'issue_counts': dict(Counter(r['kind'] for r in issues)), 'issues': issues}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'inputs', 'signals', 'protocol', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError('source audits are append-only')
    result = audit(args.baseline, args.inputs, args.signals, args.protocol)
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, default=str)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'issues'}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
