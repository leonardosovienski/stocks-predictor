"""Explicit catalog selection for reproducible, read-only measurement inputs.

observed_before is catalog knowledge, never an assertion of historical public
availability. No source wins implicitly when two selected versions disagree.
"""
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import sqlite3

from . import operational_store, simulation, source_catalog


@dataclass(frozen=True)
class DatasetSelection:
    source_ids: tuple[str, ...]
    observed_before: str
    start: str
    end: str

    def __post_init__(self):
        if (not self.source_ids or len(set(self.source_ids)) != len(self.source_ids)
                or any(not isinstance(item, str) or not item.strip() for item in self.source_ids)):
            raise ValueError('source_ids must be explicit, nonempty and unique')
        if date.fromisoformat(self.start).isoformat() != self.start:
            raise ValueError('start must be an ISO date')
        if date.fromisoformat(self.end).isoformat() != self.end or self.start > self.end:
            raise ValueError('invalid selection period')
        cutoff = source_catalog.utc_timestamp(self.observed_before)
        if self.end > cutoff[:10]:
            raise ValueError('selection end exceeds observation cutoff')
        object.__setattr__(self, 'source_ids', tuple(sorted(self.source_ids)))
        object.__setattr__(self, 'observed_before', cutoff)


def materialize(path: Path, selection: DatasetSelection) -> dict:
    """Read one SQLite snapshot and return selected normalized bars plus receipt."""
    with closing(operational_store._open(path)) as source, closing(sqlite3.connect(':memory:')) as view:
        source.execute('BEGIN')
        placeholders = ','.join('?' for _ in selection.source_ids)
        versions = source.execute(
            'SELECT source_id,sha256,observed_at FROM source_versions WHERE source_id IN ('
            + placeholders + ') ORDER BY source_id', selection.source_ids).fetchall()
        if len(versions) != len(selection.source_ids):
            raise ValueError('selected source version is missing')
        cutoff = datetime.fromisoformat(selection.observed_before)
        if any(datetime.fromisoformat(source_catalog.utc_timestamp(row[2])) > cutoff for row in versions):
            raise ValueError('selected source was observed after the cutoff')
        rows = source.execute(
            'SELECT date,ticker,market_type,open,close,quote_factor,source_file FROM prices_raw '
            'WHERE source_file IN (' + placeholders + ') AND date>=? AND date<=? '
            'ORDER BY date,ticker,source_file', (*selection.source_ids, selection.start, selection.end)).fetchall()
        if not rows:
            raise ValueError('selected dataset has no prices')
        if any(date.fromisoformat(row[0]).isoformat() != row[0] for row in rows):
            raise ValueError('selected prices contain a noncanonical session date')
        view.execute('CREATE TABLE prices_raw(date,ticker,market_type,open,close,quote_factor,source_file)')
        view.executemany('INSERT INTO prices_raw VALUES (?,?,?,?,?,?,?)', rows)
        bars = {ticker: simulation.load_bars(view, ticker) for ticker in sorted({row[1] for row in rows})}
        bars = {ticker: values for ticker, values in bars.items() if values}
        if not bars:
            raise ValueError('selected dataset has no spot prices')
    manifest = {'schema_version': 'stocks-dataset-selection/1', 'selection': asdict(selection),
                'versions': versions, 'rows': rows}
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':'),
                                       allow_nan=False).encode()).hexdigest()
    return {'bars': bars, 'selection_sha256': digest, 'selection': asdict(selection),
            'versions': versions, 'row_count': len(rows), 'capital_enabled': False}


def simulate_selected(path: Path, selection: DatasetSelection, targets: dict, *,
                      corporate_actions: dict, cost_per_side: float = 0.0018,
                      price_mode: str = 'next_open') -> dict:
    """Connect selected inputs to the existing causal engine, without legacy writes.

    Explicit corporate-action inputs are required, even when the caller declares
    empty events. Their completeness and historical availability are unverified.
    """
    if set(corporate_actions) != {'reference', 'splits', 'cash_events', 'stock_events'}:
        raise ValueError('explicit corporate-action inputs and reference are required')
    if not isinstance(corporate_actions['reference'], str) or not corporate_actions['reference'].strip():
        raise ValueError('corporate-action reference is required')
    selected = materialize(path, selection)
    bars = selected.pop('bars')
    dates = sorted({day for values in bars.values() for day in values})
    for signal, weights in targets.items():
        if date.fromisoformat(signal).isoformat() != signal or not selection.start <= signal <= selection.end:
            raise ValueError('signal outside selected period')
        if set(weights) - set(bars):
            raise ValueError('target ticker absent from selected dataset')
    result = simulation.simulate_portfolio(
        dates, bars, targets, cost_per_side=cost_per_side, price_mode=price_mode,
        **{key: corporate_actions[key] for key in ('splits', 'cash_events', 'stock_events')})
    inputs = {'targets': targets, 'corporate_actions': corporate_actions,
              'cost_per_side': cost_per_side, 'price_mode': price_mode,
              'engine': simulation.ENGINE_VERSION, 'selection_sha256': selected['selection_sha256']}
    inputs_hash = hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(',', ':'),
                                           allow_nan=False).encode()).hexdigest()
    return {**selected, 'simulation': result, 'inputs_sha256': inputs_hash,
            'engine': simulation.ENGINE_VERSION, 'scope': 'Engineering measurement; source availability '
            'and corporate-action completeness are unverified; no economic verdict.'}
