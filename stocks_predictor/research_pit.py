"""Point-in-time panel of the stocks research circuit (dataset ``stocks-pit-panel/1``).

The operator provisions one immutable panel per ``as_of`` (the request cutoff). Every
record carries ``available_at`` (UTC, when the fact became knowable). This module builds
the view an investor had at a decision instant and nothing else:

* a record is usable at decision ``d`` only if ``available_at <= d`` (late delivery,
  backfill and later source revisions are invisible before they exist);
* a bar republished/revised keeps every revision; at ``d`` the latest revision with
  ``available_at <= d`` wins;
* identity is the ``security_id``; the ticker and the issuer CNPJ are time-varying labels
  resolved from ticker/identity events known at ``d`` (a ticker or CNPJ change never
  breaks the history of a security);
* a security enters the universe only after its listing is known and effective, leaves
  only after its delisting is known and effective, and is present while it existed
  (delisted securities are never dropped retroactively);
* bars dated before the listing (IPO before the listing date) are ignored.

Fail-closed checks, before any statistic:
* ``TemporalViolation``: a record available after ``as_of``, a malformed or missing
  ``available_at``, a bar available before its own session closed, or a panel whose
  cutoff differs from the request;
* ``DataQualityProblem``: conflicting duplicate records, identity conflicts (one security
  with two issuers at the same instant, one ticker on two securities), unknown security
  references, non-finite or non-positive prices, PIT class below the admitted minimum.

The liquidity ranking follows ``universe.rank_universe`` (median financial volume over the
last N sessions of the calendar, missing sessions counted as zero, minimum history) with
two PIT corrections: availability filtering and issuer identity by CNPJ instead of the
4-letter ticker prefix.
"""

from __future__ import annotations

import math
from bisect import bisect_right
from datetime import datetime

from .research_contract import canonical, content_hash
from .universe import _median

PANEL_SCHEMA = "stocks-pit-panel/1"
PIT_ORDER = {"HISTORICAL_ONLY": 0, "PIT_RECONSTRUCTED": 1, "PIT_STRICT": 2}
RECORD_TYPES = ("securities", "ticker_events", "identity_events", "bars")
# A B3 cash-market session never closes before 20:00 UTC; a bar cannot be known earlier.
BAR_EARLIEST_AVAILABLE = "T20:00:00Z"
# Decisions for a rebalance session are taken before that session opens (09:00 BRT).
DECISION_TIME = "T12:00:00Z"
_FIELDS = {
    "securities": {"security_id", "listed_on", "listing_available_at", "delisted_on", "delisting_available_at"},
    "ticker_events": {"security_id", "ticker", "effective_on", "available_at"},
    "identity_events": {"security_id", "issuer_cnpj", "effective_on", "available_at", "source"},
    "bars": {"security_id", "session", "close", "volume_fin", "available_at"},
}


class TemporalViolation(ValueError):
    pass


class DataQualityProblem(ValueError):
    pass


def ts(value, field: str) -> str:
    """Normalize a UTC instant to YYYY-MM-DDTHH:MM:SSZ or raise TemporalViolation."""
    if type(value) is not str or not value.endswith("Z"):
        raise TemporalViolation(f"{field}: available_at/instant missing or not UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TemporalViolation(f"{field}: malformed instant {value!r}") from exc
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise TemporalViolation(f"{field}: not UTC")
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def day(value, field: str) -> str:
    if type(value) is not str or len(value) != 10:
        raise DataQualityProblem(f"{field}: date must be YYYY-MM-DD")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise DataQualityProblem(f"{field}: invalid date {value!r}") from exc
    return value


def decision_at(session: str) -> str:
    return session + DECISION_TIME


def _number(value, field: str, *, positive: bool) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise DataQualityProblem(f"{field}: not a finite number")
    if (value <= 0) if positive else (value < 0):
        raise DataQualityProblem(f"{field}: {'non-positive' if positive else 'negative'} value")
    return float(value)


class Panel:
    """Validated, indexed PIT panel. Construction never looks at a decision instant."""

    def __init__(self, raw: dict, *, as_of: str, minimum_pit_class: str):
        if type(raw) is not dict or raw.get("schema") != PANEL_SCHEMA:
            raise DataQualityProblem("dataset is not a stocks-pit-panel/1 object")
        self.as_of = ts(as_of, "as_of")
        if ts(raw.get("data_cutoff"), "data_cutoff") != self.as_of:
            raise TemporalViolation("dataset data_cutoff differs from the requested as_of")
        classes = raw.get("pit_classes")
        if type(classes) is not dict or set(classes) != set(RECORD_TYPES):
            raise DataQualityProblem("pit_classes must declare every record type")
        for kind, cls in classes.items():
            if cls not in PIT_ORDER:
                raise DataQualityProblem(f"pit_classes.{kind}: unknown class")
            if PIT_ORDER[cls] < PIT_ORDER[minimum_pit_class]:
                raise DataQualityProblem(f"PIT_CLASS_BELOW_MINIMUM: {kind} is {cls} < {minimum_pit_class}")
        self.pit_classes = dict(classes)
        self.dataset_version = raw.get("dataset_version")
        if type(self.dataset_version) is not str or not self.dataset_version:
            raise DataQualityProblem("dataset_version")
        self.counters = {"duplicate_records_collapsed": 0}
        self.available: list[str] = []  # every availability instant (checked by Core replay)
        self.securities = self._securities(raw.get("securities"))
        self.tickers = self._events(raw.get("ticker_events"), "ticker_events", "ticker")
        self.identities = self._events(raw.get("identity_events"), "identity_events", "issuer_cnpj")
        self.bars = self._bars(raw.get("bars"))
        self._identity_conflicts()
        self.calendar = sorted({session for rows in self.bars.values() for session, _ in rows})
        self.rows_for_fingerprint = self._fingerprint_rows()

    # -- loading -------------------------------------------------------------------
    def _records(self, rows, kind):
        if type(rows) is not list:
            raise DataQualityProblem(f"{kind} must be a list")
        seen: dict[str, dict] = {}
        out = []
        for index, row in enumerate(rows):
            if type(row) is not dict or set(row) != _FIELDS[kind]:
                raise DataQualityProblem(f"{kind}[{index}]: fields")
            key = canonical(row).decode("utf-8")
            if key in seen:
                self.counters["duplicate_records_collapsed"] += 1  # identical official record twice
                continue
            seen[key] = row
            out.append(row)
        return out

    def _securities(self, rows):
        out = {}
        for row in self._records(rows, "securities"):
            sid = row["security_id"]
            if type(sid) is not str or not sid:
                raise DataQualityProblem("security_id")
            if sid in out:
                raise DataQualityProblem(f"conflicting duplicate security record {sid}")
            listed = day(row["listed_on"], f"{sid}.listed_on")
            listing_at = ts(row["listing_available_at"], f"{sid}.listing_available_at")
            self.available.append(listing_at)
            delisted, delisting_at = row["delisted_on"], row["delisting_available_at"]
            if (delisted is None) != (delisting_at is None):
                raise DataQualityProblem(f"{sid}: delisting date and availability go together")
            if delisted is not None:
                delisted = day(delisted, f"{sid}.delisted_on")
                delisting_at = ts(delisting_at, f"{sid}.delisting_available_at")
                self.available.append(delisting_at)
                if delisted < listed:
                    raise DataQualityProblem(f"{sid}: delisted before listed")
            out[sid] = {"listed_on": listed, "listing_available_at": listing_at,
                        "delisted_on": delisted, "delisting_available_at": delisting_at}
        return out

    def _events(self, rows, kind, label):
        by_security: dict[str, list[tuple[str, str, str]]] = {}
        for row in self._records(rows, kind):
            sid = row["security_id"]
            if sid not in self.securities:
                raise DataQualityProblem(f"{kind}: unknown security {sid!r}")
            value = row[label]
            if type(value) is not str or not value:
                raise DataQualityProblem(f"{kind}: {label}")
            effective = day(row["effective_on"], f"{kind}.effective_on")
            available = ts(row["available_at"], f"{kind}.available_at")
            self.available.append(available)
            by_security.setdefault(sid, []).append((effective, available, value))
        for events in by_security.values():
            events.sort()
            for (e1, a1, v1), (e2, a2, v2) in zip(events, events[1:]):
                if e1 == e2 and a1 == a2 and v1 != v2:
                    raise DataQualityProblem(f"IDENTITY_CONFLICT: {kind} {v1!r} and {v2!r} at the same instant")
        return by_security

    def _bars(self, rows):
        by_security: dict[str, dict[str, list[tuple[str, float, float]]]] = {}
        for row in self._records(rows, "bars"):
            sid = row["security_id"]
            if sid not in self.securities:
                raise DataQualityProblem(f"bars: unknown security {sid!r}")
            session = day(row["session"], "bars.session")
            available = ts(row["available_at"], f"bars[{sid},{session}].available_at")
            if available < session + BAR_EARLIEST_AVAILABLE:
                raise TemporalViolation(f"bar {sid} {session} available before its session closed")
            self.available.append(available)
            close = _number(row["close"], f"bars[{sid},{session}].close", positive=True)
            volume = _number(row["volume_fin"], f"bars[{sid},{session}].volume_fin", positive=False)
            revisions = by_security.setdefault(sid, {}).setdefault(session, [])
            for other_available, other_close, other_volume in revisions:
                if other_available == available and (other_close, other_volume) != (close, volume):
                    raise DataQualityProblem(f"conflicting duplicate bar {sid} {session}")
            revisions.append((available, close, volume))
        out = {}
        for sid, sessions in by_security.items():
            out[sid] = sorted((session, sorted(revs)) for session, revs in sessions.items())
        return out

    def _identity_conflicts(self):
        # One ticker must never label two securities from the same effective instant.
        owners: dict[tuple[str, str], str] = {}
        for sid, events in self.tickers.items():
            for effective, _available, ticker in events:
                other = owners.setdefault((ticker, effective), sid)
                if other != sid:
                    raise DataQualityProblem(f"IDENTITY_CONFLICT: ticker {ticker!r} on {other} and {sid}")

    def _fingerprint_rows(self):
        rows = []
        for sid in sorted(self.bars):
            for session, revisions in self.bars[sid]:
                for available, close, volume in revisions:
                    rows.append({"kind": "bar", "security_id": sid, "at": session, "available_at": available,
                                 "value": [close, volume]})
        for kind, table in (("ticker", self.tickers), ("identity", self.identities)):
            for sid in sorted(table):
                for effective, available, value in table[sid]:
                    rows.append({"kind": kind, "security_id": sid, "at": effective, "available_at": available,
                                 "value": value})
        for sid in sorted(self.securities):
            s = self.securities[sid]
            rows.append({"kind": "security", "security_id": sid, "at": s["listed_on"],
                         "available_at": s["listing_available_at"], "value": [s["delisted_on"], s["delisting_available_at"]]})
        return rows

    # -- PIT view ------------------------------------------------------------------
    def label_at(self, table, sid: str, session: str, decision: str) -> str | None:
        """Latest label effective on/before `session` among events known at `decision`."""
        value = None
        for effective, available, label in table.get(sid, ()):
            if effective <= session and available <= decision:
                value = label
        return value

    def listed(self, sid: str, session: str, decision: str) -> bool:
        s = self.securities[sid]
        if s["listing_available_at"] > decision or s["listed_on"] >= session:
            return False
        if s["delisted_on"] is not None and s["delisting_available_at"] <= decision and s["delisted_on"] < session:
            return False
        return True

    def closes_known(self, sid: str, before_session: str, decision: str):
        """(sessions, closes, volumes) of bars strictly before `before_session`, as known at
        `decision`: latest revision available by then; bars before the listing ignored."""
        listed_on = self.securities[sid]["listed_on"]
        sessions, closes, volumes = [], [], []
        excluded_late = 0
        for session, revisions in self.bars.get(sid, ()):
            if session >= before_session:
                break
            if session < listed_on:
                continue
            known = [r for r in revisions if r[0] <= decision]
            if not known:
                excluded_late += 1
                continue
            _available, close, volume = known[-1]
            sessions.append(session)
            closes.append(close)
            volumes.append(volume)
        return sessions, closes, volumes, excluded_late

    def label_close(self, sid: str, session: str) -> float | None:
        """Close used to MEASURE an outcome after the decision (as known at as_of):
        last bar on/before `session` since listing (a delisted security keeps its last price)."""
        listed_on = self.securities[sid]["listed_on"]
        value = None
        for day_, revisions in self.bars.get(sid, ()):
            if day_ > session:
                break
            if day_ >= listed_on:
                value = revisions[-1][1]
        return value

    def universe(self, session: str, config: dict) -> dict:
        """PIT universe for a rebalance on `session` (decision before the session opens)."""
        decision = decision_at(session)
        lookback, min_history, top_n = (config["liquidity_lookback_sessions"], config["min_history_sessions"],
                                        config["top_n"])
        excluded = {"not_yet_listed_or_unknown": 0, "delisting_known": 0, "unknown_issuer": 0,
                    "late_bars_ignored": 0, "insufficient_history": 0, "stale": 0}
        views = {}
        calendar_known = set()
        for sid in sorted(self.securities):
            if not self.listed(sid, session, decision):
                s = self.securities[sid]
                if s["delisted_on"] is not None and s["delisting_available_at"] <= decision and s["delisted_on"] < session:
                    excluded["delisting_known"] += 1
                else:
                    excluded["not_yet_listed_or_unknown"] += 1
                continue
            sessions, closes, volumes, late = self.closes_known(sid, session, decision)
            excluded["late_bars_ignored"] += late
            calendar_known.update(sessions)
            views[sid] = (sessions, closes, volumes)
        window = sorted(calendar_known)[-lookback:]
        if len(window) < lookback:
            return self._universe_doc(session, decision, [], excluded, views)
        window_start = window[0]
        ranked = []
        for sid, (sessions, _closes, volumes) in views.items():
            if len(sessions) < min_history:
                excluded["insufficient_history"] += 1
                continue
            if sessions[-1] < window_start:
                excluded["stale"] += 1
                continue
            issuer = self.label_at(self.identities, sid, session, decision)
            if issuer is None:
                excluded["unknown_issuer"] += 1
                continue
            in_window = [v for s, v in zip(sessions, volumes) if s >= window_start]
            median = _median(in_window + [0.0] * (lookback - len(in_window)))
            ranked.append((sid, issuer, median))
        best: dict[str, tuple[str, str, float]] = {}
        for sid, issuer, median in sorted(ranked):
            if issuer not in best or median > best[issuer][2]:
                best[issuer] = (sid, issuer, median)
        members = sorted(best.values(), key=lambda item: (-item[2], item[0]))[:top_n]
        return self._universe_doc(session, decision, members, excluded, views)

    def _universe_doc(self, session, decision, members, excluded, views):
        entries = []
        for rank, (sid, issuer, median) in enumerate(members, 1):
            entries.append({"rank": rank, "security_id": sid, "issuer_cnpj": issuer,
                            "ticker": self.label_at(self.tickers, sid, session, decision),
                            "median_volume_fin": median})
        identity = [e["security_id"] for e in entries]
        used = [a for sid in identity for a in self._availability_used(sid, session, decision)]
        return {
            "session": session,
            "decision_at": decision,
            "members": entries,
            "universe_identity_hash": content_hash(identity),
            "universe_view_hash": content_hash(entries),
            "excluded": excluded,
            "max_available_used": max(used) if used else None,
            "series": {sid: (views[sid][0], views[sid][1]) for sid in identity},
        }

    def _availability_used(self, sid, session, decision):
        s = self.securities[sid]
        yield s["listing_available_at"]
        for table in (self.tickers, self.identities):
            for effective, available, _ in table.get(sid, ()):
                if effective <= session and available <= decision:
                    yield available
        for day_, revisions in self.bars.get(sid, ()):
            if day_ >= session:
                break
            known = [r for r in revisions if r[0] <= decision]
            if known:
                yield known[-1][0]


def rebalance_sessions(calendar: list[str], every: int, warmup: int) -> list[str]:
    """Deterministic schedule from the exchange calendar: every `every` sessions after warmup."""
    if every < 1 or warmup < 0:
        raise ValueError("invalid rebalance schedule")
    return calendar[warmup::every]


def session_index(calendar: list[str], session: str) -> int:
    return bisect_right(calendar, session) - 1


__all__ = [
    "PANEL_SCHEMA",
    "PIT_ORDER",
    "DECISION_TIME",
    "Panel",
    "TemporalViolation",
    "DataQualityProblem",
    "decision_at",
    "rebalance_sessions",
    "session_index",
    "ts",
]
