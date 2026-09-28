"""Dataset point-in-time (schema ``stocks-pit-dataset/2``) e a visão de um instante de decisão.

Tudo o que chega a um sinal passa por ``PITView``, construída para um pregão de decisão ``D``: o instante
da decisão é ``D`` às 12:00 UTC (09:00 em São Paulo, antes da abertura) e a visão só contém registros com
``available_at <= decisão`` e barras de pregões anteriores a ``D``. Não há referência ao dataset inteiro
dentro da visão: um sinal não tem como alcançar o futuro.

Registros (listas de objetos, campos exatos):
    securities        security_id, kind ("equity" | "index_fund"), listed_on, listing_available_at,
                      delisted_on (último pregão), delisting_available_at, delisting_value
                      (os três None enquanto listado; delisting_value = R$ por ação recebido na saída,
                      None = último fechamento negociado)
    identity_events   security_id, ticker, issuer_id, effective_on, available_at
    bars              security_id, session, open, close, volume_fin, available_at   (preço NEGOCIADO, sem ajuste)
    corporate_actions security_id, ex_session, kind, share_multiplier, available_at
                      (desdobramento/grupamento/bonificação: ações × multiplicador na data ex)
    cash_events       security_id, ex_session, amount_per_share, available_at
    fundamentals      security_id, field, period_end, version, value, available_at
                      (available_at = data de DIVULGAÇÃO/recebimento; reapresentação = versão maior)

Validação fechada (``DatasetError``): calendário ordenado, único, sem fim de semana e sem pregão em que nada
negociou; barra só em pregão do calendário e disponível só depois do fechamento; todo ``available_at`` UTC e
<= ``data_cutoff``; fundamento nunca disponível antes do fim do período; conflito de registro duplicado; preço
não positivo ou não finito.
"""

from __future__ import annotations

import hashlib
import json
import math
from bisect import bisect_left
from dataclasses import dataclass
from datetime import date, datetime

from . import SCHEMA

DECISION_TIME = "T12:00:00Z"        # 09:00 America/Sao_Paulo: antes da abertura do pregão
BAR_EARLIEST_AVAILABLE = "T20:00:00Z"  # um pregão da B3 à vista nunca fecha antes das 17:00 BRT
KINDS = ("equity", "index_fund")
_FIELDS = {
    "securities": {"security_id", "kind", "listed_on", "listing_available_at", "delisted_on", "delisting_available_at",
                   "delisting_value"},
    "identity_events": {"security_id", "ticker", "issuer_id", "effective_on", "available_at"},
    "bars": {"security_id", "session", "open", "close", "volume_fin", "available_at"},
    "corporate_actions": {"security_id", "ex_session", "kind", "share_multiplier", "available_at"},
    "cash_events": {"security_id", "ex_session", "amount_per_share", "available_at"},
    "fundamentals": {"security_id", "field", "period_end", "version", "value", "available_at"},
}


class DatasetError(ValueError):
    """O dataset viola o contrato point-in-time (falha fechada)."""


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def _day(value, field: str) -> str:
    if type(value) is not str or len(value) != 10:
        raise DatasetError(f"{field}: data deve ser YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise DatasetError(f"{field}: data inválida {value!r}") from exc
    return value


def _instant(value, field: str) -> str:
    if type(value) is not str or not value.endswith("Z"):
        raise DatasetError(f"{field}: instante ausente ou não UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DatasetError(f"{field}: instante inválido {value!r}") from exc
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise DatasetError(f"{field}: instante não UTC")
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def _positive(value, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise DatasetError(f"{field}: número positivo e finito exigido")
    return float(value)


def _non_negative(value, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise DatasetError(f"{field}: número não negativo e finito exigido")
    return float(value)


def decision_instant(session: str) -> str:
    return session + DECISION_TIME


@dataclass(frozen=True)
class Bar:
    session: str
    open: float
    close: float
    volume_fin: float
    available_at: str


@dataclass(frozen=True)
class Fundamental:
    value: float
    period_end: str
    version: int
    available_at: str


class PITDataset:
    """Dataset validado e indexado. ``hash`` identifica exatamente o conteúdo (sha256 canônico)."""

    def __init__(self, raw: dict):
        if type(raw) is not dict or raw.get("schema") != SCHEMA:
            raise DatasetError(f"dataset não é {SCHEMA}")
        self.hash = hashlib.sha256(canonical(raw)).hexdigest()
        self.version = raw.get("dataset_version")
        if type(self.version) is not str or not self.version:
            raise DatasetError("dataset_version")
        self.cutoff = _instant(raw.get("data_cutoff"), "data_cutoff")
        calendar = raw.get("calendar")
        if type(calendar) is not list or not calendar:
            raise DatasetError("calendar")
        self.calendar = [_day(s, "calendar") for s in calendar]
        if self.calendar != sorted(set(self.calendar)):
            raise DatasetError("calendar deve ser ordenado e sem repetição")
        weekend = [s for s in self.calendar if date.fromisoformat(s).weekday() >= 5]
        if weekend:
            raise DatasetError(f"calendar: fim de semana não é pregão da B3 ({weekend[0]})")
        self._position = {s: i for i, s in enumerate(self.calendar)}
        self.securities = self._securities(self._rows(raw, "securities"))
        self.identities: dict[str, list[tuple[str, str, str, str]]] = {}
        for row in self._rows(raw, "identity_events"):
            sid = self._known(row["security_id"], "identity_events")
            if type(row["ticker"]) is not str or not row["ticker"] or type(row["issuer_id"]) is not str or not row["issuer_id"]:
                raise DatasetError("identity_events: ticker/issuer_id")
            entry = (_day(row["effective_on"], "identity_events.effective_on"),
                     self._available(row["available_at"], "identity_events"), row["ticker"], row["issuer_id"])
            self.identities.setdefault(sid, []).append(entry)
        for events in self.identities.values():
            events.sort()
            for a, b in zip(events, events[1:]):
                if a[:2] == b[:2] and a != b:
                    raise DatasetError("identity_events: conflito no mesmo instante")
        self.bars: dict[str, dict[str, list[Bar]]] = {}
        for row in self._rows(raw, "bars"):
            sid = self._known(row["security_id"], "bars")
            session = _day(row["session"], "bars.session")
            if session not in self._position:
                raise DatasetError(f"bars: {sid} em {session}, fora do calendário de pregões")
            available = self._available(row["available_at"], f"bars[{sid},{session}]")
            if available < session + BAR_EARLIEST_AVAILABLE:
                raise DatasetError(f"bars: {sid} {session} disponível antes do fechamento do pregão")
            bar = Bar(session, _positive(row["open"], "bars.open"), _positive(row["close"], "bars.close"),
                      _non_negative(row["volume_fin"], "bars.volume_fin"), available)
            revisions = self.bars.setdefault(sid, {}).setdefault(session, [])
            if any(r.available_at == available and r != bar for r in revisions):
                raise DatasetError(f"bars: revisão conflitante {sid} {session}")
            if bar not in revisions:
                revisions.append(bar)
        for sessions in self.bars.values():
            for revisions in sessions.values():
                revisions.sort(key=lambda b: b.available_at)
        traded = {session for sessions in self.bars.values() for session in sessions}
        silent = [s for s in self.calendar if s not in traded]
        if silent:
            raise DatasetError(f"calendar: pregão sem nenhum negócio no dataset ({silent[0]})")
        self.actions: dict[str, list[tuple[str, float, str, str]]] = {}
        for row in self._rows(raw, "corporate_actions"):
            sid = self._known(row["security_id"], "corporate_actions")
            ex = _day(row["ex_session"], "corporate_actions.ex_session")
            if ex not in self._position:
                raise DatasetError("corporate_actions: ex_session fora do calendário")
            multiplier = _positive(row["share_multiplier"], "corporate_actions.share_multiplier")
            if multiplier == 1.0 or type(row["kind"]) is not str:
                raise DatasetError("corporate_actions: multiplicador neutro ou tipo inválido")
            self.actions.setdefault(sid, []).append((ex, multiplier, self._available(row["available_at"], "corporate_actions"), row["kind"]))
        for events in self.actions.values():
            events.sort()
        self.cash: dict[str, list[tuple[str, float, str]]] = {}
        for row in self._rows(raw, "cash_events"):
            sid = self._known(row["security_id"], "cash_events")
            ex = _day(row["ex_session"], "cash_events.ex_session")
            if ex not in self._position:
                raise DatasetError("cash_events: ex_session fora do calendário")
            self.cash.setdefault(sid, []).append(
                (ex, _non_negative(row["amount_per_share"], "cash_events.amount_per_share"),
                 self._available(row["available_at"], "cash_events")))
        self.fundamentals: dict[tuple[str, str], list[tuple[str, int, float, str]]] = {}
        for row in self._rows(raw, "fundamentals"):
            sid = self._known(row["security_id"], "fundamentals")
            period = _day(row["period_end"], "fundamentals.period_end")
            available = self._available(row["available_at"], "fundamentals")
            if available < period + "T00:00:00Z":
                raise DatasetError("fundamentals: disponível antes do fim do período")
            version = row["version"]
            if type(version) is not int or version < 1 or type(row["field"]) is not str:
                raise DatasetError("fundamentals: versão/campo")
            value = row["value"]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise DatasetError("fundamentals: valor não finito")
            key = (sid, row["field"])
            entries = self.fundamentals.setdefault(key, [])
            clash = [e for e in entries if e[0] == period and e[1] == version]
            if clash and clash[0] != (period, version, float(value), available):
                raise DatasetError("fundamentals: versão duplicada conflitante")
            if not clash:
                entries.append((period, version, float(value), available))

    # -- carga -----------------------------------------------------------------------------------
    @staticmethod
    def _rows(raw: dict, kind: str) -> list[dict]:
        rows = raw.get(kind, [])
        if type(rows) is not list:
            raise DatasetError(f"{kind} deve ser lista")
        for index, row in enumerate(rows):
            if type(row) is not dict or set(row) != _FIELDS[kind]:
                raise DatasetError(f"{kind}[{index}]: campos")
        return rows

    def _available(self, value, field: str) -> str:
        instant = _instant(value, field + ".available_at")
        if instant > self.cutoff:
            raise DatasetError(f"{field}: disponível depois do data_cutoff")
        return instant

    def _known(self, sid, kind: str) -> str:
        if sid not in self.securities:
            raise DatasetError(f"{kind}: security_id desconhecido {sid!r}")
        return sid

    def _securities(self, rows: list[dict]) -> dict[str, dict]:
        out = {}
        for row in rows:
            sid = row["security_id"]
            if type(sid) is not str or not sid or sid in out:
                raise DatasetError("securities: security_id vazio ou repetido")
            if row["kind"] not in KINDS:
                raise DatasetError("securities: kind")
            listed = _day(row["listed_on"], "listed_on")
            delisted, delisting_at = row["delisted_on"], row["delisting_available_at"]
            value = row["delisting_value"]
            if (delisted is None) != (delisting_at is None) or (delisted is None and value is not None):
                raise DatasetError("securities: deslistagem, disponibilidade e valor andam juntos")
            if delisted is not None:
                delisted = _day(delisted, "delisted_on")
                if delisted < listed or delisted not in self._position:
                    raise DatasetError("securities: deslistagem antes da listagem ou fora do calendário")
                delisting_at = self._available(delisting_at, "delisting")
                if value is not None:
                    value = _non_negative(value, "delisting_value")
            out[sid] = {"kind": row["kind"], "listed_on": listed,
                        "listing_available_at": self._available(row["listing_available_at"], "listing"),
                        "delisted_on": delisted, "delisting_available_at": delisting_at, "delisting_value": value}
        return out

    # -- verdade realizada (execução e marcação), como conhecida no data_cutoff ------------------
    def position(self, session: str) -> int:
        try:
            return self._position[session]
        except KeyError as exc:
            raise DatasetError(f"{session} não é pregão do calendário") from exc

    def realized_bar(self, sid: str, session: str) -> Bar | None:
        """Barra efetivamente negociada (última revisão até o cutoff). Só o motor usa, nunca um sinal."""
        revisions = self.bars.get(sid, {}).get(session)
        return revisions[-1] if revisions else None

    def realized_actions(self, sid: str, session: str) -> list[float]:
        return [m for ex, m, _available, _kind in self.actions.get(sid, ()) if ex == session]

    def realized_cash(self, sid: str, session: str) -> float:
        return sum(amount for ex, amount, _available in self.cash.get(sid, ()) if ex == session)

    def view(self, session: str) -> "PITView":
        return PITView(self, session)


class PITView:
    """O que um investidor sabia antes da abertura de ``session``. Única entrada dos sinais e do universo."""

    def __init__(self, dataset: PITDataset, session: str):
        self._ds = dataset
        self.session = session
        self.index = dataset.position(session)
        self.decision_at = decision_instant(session)
        self.calendar = tuple(dataset.calendar[: self.index])  # pregões anteriores à decisão
        self.signal_session = self.calendar[-1] if self.calendar else None  # último fechamento visível
        self._history: dict[str, tuple[list[str], list[float], list[float], list[float]]] = {}

    def _known(self, available_at: str) -> bool:
        return available_at <= self.decision_at

    def listed(self, sid: str) -> bool:
        s = self._ds.securities[sid]
        if not self._known(s["listing_available_at"]) or s["listed_on"] >= self.session:
            return False
        if s["delisted_on"] is not None and self._known(s["delisting_available_at"]) and s["delisted_on"] < self.session:
            return False
        return True

    def listed_ids(self, kind: str = "equity") -> list[str]:
        return sorted(sid for sid, s in self._ds.securities.items() if s["kind"] == kind and self.listed(sid))

    def _label(self, sid: str, position: int) -> str | None:
        """Ticker/emissor vigente no pregão da decisão, se a mudança já era conhecida."""
        value = None
        for effective, available, ticker, issuer in self._ds.identities.get(sid, ()):
            if effective <= self.session and self._known(available):
                value = (ticker, issuer)[position]
        return value

    def ticker(self, sid: str) -> str | None:
        return self._label(sid, 0)

    def issuer(self, sid: str) -> str | None:
        return self._label(sid, 1)

    def _known_actions(self, sid: str) -> list[tuple[str, float]]:
        return [(ex, m) for ex, m, available, _kind in self._ds.actions.get(sid, ())
                if ex < self.session and self._known(available)]

    def history(self, sid: str) -> tuple[list[str], list[float], list[float], list[float]]:
        """(pregões, aberturas ajustadas, fechamentos ajustados, volume financeiro) conhecidos na decisão.

        Ajuste só por eventos já conhecidos e com data ex anterior à decisão; volume financeiro não se ajusta.
        Barras antes da listagem são ignoradas; revisões posteriores à decisão são invisíveis.
        """
        if sid not in self._history:
            self._history[sid] = self._build_history(sid)
        sessions, opens, closes, volumes = self._history[sid]
        return list(sessions), list(opens), list(closes), list(volumes)

    def _build_history(self, sid: str) -> tuple[list[str], list[float], list[float], list[float]]:
        listed_on = self._ds.securities[sid]["listed_on"]
        actions = self._known_actions(sid)
        sessions, opens, closes, volumes = [], [], [], []
        for session, revisions in sorted(self._ds.bars.get(sid, {}).items()):
            if session >= self.session or session < listed_on:
                continue
            known = [r for r in revisions if self._known(r.available_at)]
            if not known:
                continue
            bar = known[-1]
            factor = 1.0
            for ex, multiplier in actions:
                if session < ex:
                    factor /= multiplier
            sessions.append(session)
            opens.append(bar.open * factor)
            closes.append(bar.close * factor)
            volumes.append(bar.volume_fin)
        return sessions, opens, closes, volumes

    def average_daily_value(self, sid: str, lookback: int, statistic: str = "mean") -> float:
        """Volume financeiro diário dos últimos ``lookback`` pregões do calendário (sem negócio = 0)."""
        if lookback < 1:
            raise ValueError("lookback >= 1")
        window = self.calendar[-lookback:]
        if len(window) < lookback:
            return 0.0
        sessions, _o, _c, volumes = self.history(sid)
        by_session = dict(zip(sessions, volumes))
        values = [by_session.get(s, 0.0) for s in window]
        if statistic == "mean":
            return sum(values) / lookback
        if statistic == "median":
            ordered = sorted(values)
            mid = lookback // 2
            return ordered[mid] if lookback % 2 else (ordered[mid - 1] + ordered[mid]) / 2
        raise ValueError("statistic: mean | median")

    def fundamental(self, sid: str, field: str, period_end: str | None = None) -> Fundamental | None:
        """Maior versão já divulgada do período pedido (padrão: o período mais recente já divulgado).

        Uma reapresentação só substitui o valor original a partir da sua própria data de divulgação.
        """
        known = [e for e in self._ds.fundamentals.get((sid, field), ())
                 if self._known(e[3]) and (period_end is None or e[0] == period_end)]
        if not known:
            return None
        period = max(e[0] for e in known)
        period_end, version, value, available = max((e for e in known if e[0] == period), key=lambda e: e[1])
        return Fundamental(value, period_end, version, available)

    def sessions_since(self, session: str) -> int:
        return len(self.calendar) - bisect_left(self.calendar, session)


__all__ = ["Bar", "DatasetError", "Fundamental", "PITDataset", "PITView", "canonical", "decision_instant"]
