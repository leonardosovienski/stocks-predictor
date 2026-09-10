"""Reconcile frozen H20 economic fields from sealed consumed inputs.

This separate audit does not certify the entire historical 1,448-file package.
It never disables the original package verifier or modifies its manifest.
"""
import argparse
from datetime import date
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import zipfile

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from stocks_predictor.discovery_h17 import adjustment_map
from stocks_predictor.discovery_reorganizations import merged_market
from stocks_predictor.discovery_value import group_events
from stocks_predictor import profit_validation


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def close(a, b):
    if not math.isclose(a, b, rel_tol=2e-12, abs_tol=2e-12):
        raise ValueError(f'arithmetic mismatch: {a} versus {b}')


def equivalent(actual, expected, path='', differences=None):
    """Exact structure/identities; 2e-12 tolerance only for finite float arithmetic.

    Cross-platform pow differed by 2.22e-16 in one archived annualization.
    This audit comparison is not byte equality and does not change old seals.
    """
    if differences is None:
        differences = []
    if isinstance(actual, dict) and isinstance(expected, dict):
        if actual.keys() != expected.keys():
            raise ValueError('keys differ at ' + path)
        for key in actual:
            equivalent(actual[key], expected[key], path+'/'+key, differences)
    elif isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError('length differs at ' + path)
        for index, (left, right) in enumerate(zip(actual, expected)):
            equivalent(left, right, path+'/'+str(index), differences)
    elif actual != expected:
        if not isinstance(actual, float) or not isinstance(expected, float):
            raise ValueError('exact value differs at ' + path)
        close(actual, expected)
        differences.append({'path': path, 'actual': actual, 'expected': expected,
                            'absolute_error': abs(actual-expected)})
    return differences


def run(root, output):
    output.mkdir(parents=True, exist_ok=False)
    inputs = output / 'inputs'
    inputs.mkdir()
    hashes = {}
    with zipfile.ZipFile(root / 'DADOS_STOCKS.zip') as archive:
        def restore(name, expected):
            path = (inputs / name).resolve()
            if not path.is_relative_to(inputs.resolve()):
                raise ValueError('unsafe input path')
            payload = archive.read('objects/' + expected)
            if hashlib.sha256(payload).hexdigest() != expected:
                raise ValueError('input seal mismatch')
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(payload)
            hashes[name] = expected
            return path

        manifest = read(restore('validation-manifest.json',
            '51eed47cc7985a9d8f0be7ca14527871caeba2d9f8cacfb10d4abf423cb7f7fa'))
        required = ['baseline/base/quotes.db', 'baseline/successors/successors.db',
                    'baseline/base/events.json', 'baseline/terms/reorganizations.json',
                    'baseline/observations/h18-h19-reorganization-observation.json',
                    'results/VALIDACAO_LUCRO_STOCKS.json']
        required += [n for n in manifest['files'] if n.startswith(
            ('baseline/base/identity/', 'baseline/successors/identity/'))]
        for name in required:
            restore(name, manifest['files'][name])
        signal_path = restore('h20-signals.json',
            '13acee7062dddbf96c81356588f36806e758ea9e5c6c8f395e7891620b1f6a8f')

    bootstrap_path = REPO / 'vendor/predictor_core/measurement/bootstrap.py'
    if digest(bootstrap_path) != manifest['files']['validator/bootstrap.py']:
        raise ValueError('frozen bootstrap source differs')
    if digest(Path(profit_validation.__file__)) != manifest['files']['validator/profit_validation.py']:
        raise ValueError('independent entitlement engine differs')
    bootstrap = module('audit_h20_bootstrap', bootstrap_path).bootstrap_ci
    base = inputs / 'baseline'
    bars, _ = merged_market(base/'base/quotes.db', base/'base/identity',
                           base/'successors/successors.db', base/'successors/identity')
    events, legacy = group_events(read(base/'base/events.json'))
    factors = {ticker: adjustment_map(events[ticker], legacy[ticker])[0] for ticker in bars}
    original = read(base/'observations/h18-h19-reorganization-observation.json')
    actual = profit_validation.audit_trials(original, bars, factors,
                                           read(base/'terms/reorganizations.json'), bootstrap)
    expected_source = read(inputs/'results/VALIDACAO_LUCRO_STOCKS.json')
    with (output/'underlying-recomputed.json').open('x', encoding='utf-8') as stream:
        json.dump(actual, stream, ensure_ascii=False, indent=2, allow_nan=False)
    rounding_differences = equivalent(actual, {k: expected_source[k] for k in actual})
    print('Underlying cells reconciled:', actual['independently_verified_cells'], flush=True)

    result_path = REPO/'research/session-20260908/h20-profit-test/H20_TESTE_RESULTADOS.json'
    if digest(result_path) != 'aa184580bf5ba69b515a20cc40115453396bdefa470ac0f5408c0d3ced15e1a3':
        raise ValueError('frozen H20 output differs')
    expected = read(result_path)
    code = REPO/'research/session-20260908/h20-profit-test/compare_h20.py'
    if digest(code) != '359517909d7d3630d8dadef203cfa5df40ec48c5013d407560806ee341de4cba':
        raise ValueError('frozen comparison source differs')
    comparison = module('audit_h20_comparison_functions', code)
    signals = read(signal_path)['periods']
    trial = next(t for t in actual['trials'] if t['family'] == 'H19' and t['holding_months'] == 3)
    originals = {p['asof']: p for p in next(t for t in original['trials']
                 if t['family'] == 'H19' and t['holding_months'] == 3)['periods']}
    mean_checks = path_checks = pair_checks = interval_checks = 0
    for mode, measured in expected['modes'].items():
        underlying = {p['asof']: p for p in trial['modes'][mode]['periods']}
        periods = [comparison.join_period(s, underlying.get(s['asof']), originals.get(s['asof']))
                   for s in signals]
        if periods != measured['periods']:
            raise ValueError('H20 identities, exclusions or mark means differ')
        computed = {}
        for period in periods:
            if not period['eligible_signal']:
                continue
            source = {m['ticker']: m for m in underlying[period['asof']]['members']}
            computed[period['asof']] = {g: math.fsum(source[t]['return'] for t in names)/len(names)
                                       for g, names in period['groups'].items()}
            for group, value in computed[period['asof']].items():
                close(period['returns'][group], value)
                mean_checks += 1
        first, last = min(underlying), max(underlying)
        years = (date.fromisoformat(underlying[last]['exit']) -
                 date.fromisoformat(underlying[first]['entry'])).days / 365.25
        pairs = {(a, b): comparison.compare(periods, a, b, bootstrap) for a, b in comparison.PAIRS}
        for case in measured['scenarios']:
            cost = case['one_way_assumed_cost']
            for group, summary in case['groups'].items():
                reproduced = comparison.summarize(periods, group, cost, expected['protocol']['capital_brl'])
                equivalent(reproduced, summary, f'/{mode}/{cost}/{group}', rounding_differences)
                multipliers = [(1+computed[d][group])*(1-cost)/(1+cost) for d in sorted(computed)]
                total = math.prod(multipliers)
                close(summary['synthetic_path']['terminal_multiple'], total)
                close(summary['synthetic_path']['annualized_geometric_return'], total**(1/years)-1)
                wealth = [1.0]+[math.prod(multipliers[:i]) for i in range(1, len(multipliers)+1)]
                close(summary['synthetic_path']['period_mark_max_drawdown'],
                      min(v/max(wealth[:i+1])-1 for i, v in enumerate(wealth)))
                path_checks += 1
            for pair in case['comparisons']:
                left, right = pair['left'], pair['right']
                values = [computed[d][left]-computed[d][right] for d in sorted(computed)]
                close(pair['mean_quarter_difference_after_assumed_cost'],
                      math.fsum(values)/len(values)*(1-cost)/(1+cost))
                close(pair['fixed_halves'][0]['mean_quarter_difference'], math.fsum(values[:15])/15)
                close(pair['fixed_halves'][1]['mean_quarter_difference'], math.fsum(values[15:])/16)
                replayed = pairs[left, right]
                if replayed['descriptive_unadjusted_bootstrap_95pct'] != pair['descriptive_unadjusted_bootstrap_95pct']:
                    raise ValueError('descriptive interval differs')
                pair_checks += 1
                interval_checks += 1
    for name, expected_hash in hashes.items():
        if digest(inputs/name) != expected_hash:
            raise ValueError('source changed during read-only reconciliation')
    report = {'status': 'PASS_CONSUMED_INPUT_RECONCILIATION', 'input_hashes': hashes,
              'underlying_entitlement_cells': actual['independently_verified_cells'],
              'underlying_scenarios_numerically_reconciled': 12, 'h20_strategy_scenarios_numerically_reconciled': 18,
              'numeric_absolute_and_relative_tolerance': 2e-12,
              'rounding_differences': rounding_differences,
              'independent_cross_section_means': mean_checks, 'independent_paths': path_checks,
              'independent_paired_means_and_halves': pair_checks,
              'bootstrap_interval_comparisons': interval_checks,
              'original_result_sha256': digest(result_path),
              'code_hashes': {str(p.relative_to(REPO)): digest(p) for p in
                              [Path(__file__), code, Path(profit_validation.__file__), bootstrap_path]},
              'full_original_package_verified': False, 'new_hypotheses': 0,
              'new_independent_market_evidence': 0, 'executable_profit': None,
              'limitation': 'Reconciles consumed quotes, terms and frozen selections; omitted package files remain external dependencies for the original whole-package verifier. No original-publication or event-completeness certificate.'}
    with (output/'verification.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'input_hashes','code_hashes'}}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.output.resolve())
