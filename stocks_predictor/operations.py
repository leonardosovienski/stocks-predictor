"""Explicit offline operational commands for the installed research package."""
import argparse
from dataclasses import asdict, fields
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sqlite3
import sys
import zipfile

from . import diagnostics, operational_store as store
from .research_profile import ResearchProfile
from .temporal_evidence import DatedOutcome, estimate_asof


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest='command', required=True)
    doctor = commands.add_parser('doctor', help='Offline runtime metadata, no migrations')
    doctor.add_argument('--check', action='store_true')
    doctor.add_argument('--db', type=Path)
    for command in ('init', 'inspect', 'ingest', 'snapshot'):
        command_parser = commands.add_parser(command)
        command_parser.add_argument('--db', type=Path, required=True)
        if command == 'ingest':
            for flag in ('publisher', 'dataset', 'version', 'source-url', 'observed-at', 'sha256'):
                command_parser.add_argument('--' + flag, required=True)
            command_parser.add_argument('--archive', type=Path, required=True)
            command_parser.add_argument('--scratch-dir', type=Path, required=True)
            command_parser.add_argument('--all-markets', action='store_true')
            command_parser.add_argument('--timeout', type=float, default=5)
        elif command == 'snapshot':
            command_parser.add_argument('--destination', type=Path, required=True)
            command_parser.add_argument('--timeout', type=float, default=60)
    restore = commands.add_parser('restore')
    restore.add_argument('--snapshot', type=Path, required=True)
    restore.add_argument('--destination', type=Path, required=True)
    profile = commands.add_parser('profile', help='Validate explicit personal inputs; no profit claim')
    profile.add_argument('--input', type=Path, required=True)
    profile.add_argument('--planned-orders', type=int, default=2)
    evidence = commands.add_parser('evidence', help='Validate dated outcomes before an explicit cutoff')
    evidence.add_argument('--input', type=Path, required=True)
    evidence.add_argument('--asof', required=True)
    evidence.add_argument('--minimum-observations', type=int, default=12)
    return root


def _json_input(path: Path):
    def reject_constant(value: str):
        raise ValueError('non-finite JSON constant: ' + value)

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result

    return json.loads(path.read_text(encoding='utf-8'), parse_constant=reject_constant,
                      object_pairs_hook=unique_object)


def _profile(path: Path, planned_orders: int) -> dict:
    data = _json_input(path)
    if not isinstance(data, dict) or set(data) - {field.name for field in fields(ResearchProfile)}:
        raise ValueError('profile requires an object with known fields')
    if data.get('capital_brl') is None:
        raise ValueError('capital_brl is required')
    for key, value in data.items():
        if value is not None and key not in ('resident_pf_brazil', 'horizon_months'):
            if isinstance(value, bool) or not isinstance(value, (int, float, str)):
                raise ValueError('costs require decimal numbers or strings')
            data[key] = Decimal(str(value))
    return ResearchProfile(**data).assess(planned_orders=planned_orders)


def _evidence(path: Path, asof: str, minimum: int) -> dict:
    data = _json_input(path)
    if not isinstance(data, list):
        raise ValueError('evidence requires a list of dated outcomes')
    outcomes = []
    expected = {field.name for field in fields(DatedOutcome)}
    for row in data:
        if not isinstance(row, dict) or set(row) != expected:
            raise ValueError('each outcome requires exactly the dated outcome fields')
        if (any(not isinstance(row[key], str) for key in expected - {'gross_edge'})
                or isinstance(row['gross_edge'], bool) or not isinstance(row['gross_edge'], (int, float))):
            raise ValueError('outcome dates/identity require strings and gross_edge a number')
        outcomes.append(DatedOutcome(**row))
    estimate = estimate_asof(outcomes, asof, minimum_observations=minimum)
    return {'status': 'INSUFFICIENT_EVIDENCE' if estimate is None else 'DATED_INPUTS_VALID',
            'estimate': None if estimate is None else asdict(estimate), 'capital_enabled': False,
            'scope': 'Supplied chronology only; independence, timestamp truth and profit unverified.'}


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == 'doctor':
            return diagnostics.main((['--check'] if args.check else []) +
                                    (['--db', str(args.db)] if args.db else []))
        if args.command == 'init':
            result = store.initialize(args.db)
        elif args.command == 'inspect':
            result = store.inspect(args.db)
        elif args.command == 'ingest':
            result = store.ingest(args.db, args.archive, publisher=args.publisher, dataset=args.dataset,
                                  version=args.version, source_url=args.source_url, observed_at=args.observed_at,
                                  expected_sha256=args.sha256, scratch_dir=args.scratch_dir,
                                  all_markets=args.all_markets, timeout=args.timeout)
        elif args.command == 'snapshot':
            result = store.snapshot(args.db, args.destination, timeout=args.timeout)
        elif args.command == 'restore':
            result = store.restore(args.snapshot, args.destination)
        elif args.command == 'profile':
            result = _profile(args.input, args.planned_orders)
        else:
            result = _evidence(args.input, args.asof, args.minimum_observations)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, InvalidOperation, sqlite3.Error, zipfile.BadZipFile) as exc:
        code = getattr(exc, 'sqlite_errorcode', None)
        retryable = code is not None and (code & 0xFF) in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED)
        print(json.dumps({'status': 'ERROR', 'error_type': type(exc).__name__, 'message': str(exc),
                          'retryable_lock': retryable, 'capital_enabled': False}), file=sys.stderr)
        return 2
