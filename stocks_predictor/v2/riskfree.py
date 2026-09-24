"""Taxa livre de risco versionada (schema ``stocks-riskfree/1``) e retorno em excesso.

A série cobre cada pregão avaliado. Pregão sem taxa levanta ``RiskFreeError``: nunca um zero silencioso, que
transformaria o Sharpe em excesso num Sharpe com rf = 0.

Unidades aceitas (séries SGS do Banco Central):
    percent_per_day        % ao dia        (SGS 11 Selic, SGS 12 CDI)       → r / 100
    percent_per_year_252   % ao ano, 252   (SGS 1178 Selic, SGS 4389 CDI)    → (1 + r/100) ** (1/252) − 1

A taxa do pregão ``s`` remunera o caixa de ``s`` para ``s+1``; o retorno em excesso do pregão ``s`` é
``r_s − rf_s``.
"""

from __future__ import annotations

import hashlib
import math

from .dataset import DatasetError, _day, canonical

SCHEMA = "stocks-riskfree/1"
UNITS = ("percent_per_day", "percent_per_year_252")


class RiskFreeError(ValueError):
    """Série livre de risco inválida ou sem taxa para um pregão avaliado."""


class RiskFreeSeries:
    def __init__(self, raw: dict):
        if type(raw) is not dict or raw.get("schema") != SCHEMA:
            raise RiskFreeError(f"série livre de risco não é {SCHEMA}")
        if set(raw) != {"schema", "series_id", "unit", "source", "rates"}:
            raise RiskFreeError("campos exatos: schema, series_id, unit, source, rates")
        if type(raw["series_id"]) is not str or not raw["series_id"] or raw["unit"] not in UNITS:
            raise RiskFreeError(f"series_id vazio ou unit fora de {UNITS}")
        if type(raw["source"]) is not dict or not raw["source"]:
            raise RiskFreeError("source (proveniência) é obrigatório")
        self.series_id, self.unit = raw["series_id"], raw["unit"]
        self.hash = hashlib.sha256(canonical(raw)).hexdigest()
        self._daily: dict[str, float] = {}
        previous = None
        for row in raw["rates"]:
            if type(row) is not dict or set(row) != {"session", "rate"}:
                raise RiskFreeError("rates: {session, rate}")
            try:
                session = _day(row["session"], "rates.session")
            except DatasetError as exc:
                raise RiskFreeError(str(exc)) from exc
            rate = row["rate"]
            if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate <= -100:
                raise RiskFreeError(f"taxa inválida em {session}")
            if previous is not None and session <= previous:
                raise RiskFreeError("rates ordenadas e sem repetição")
            previous = session
            self._daily[session] = rate / 100 if self.unit == "percent_per_day" else (1 + rate / 100) ** (1 / 252) - 1
        if not self._daily:
            raise RiskFreeError("série vazia")

    def daily(self, session: str) -> float:
        try:
            return self._daily[session]
        except KeyError as exc:
            raise RiskFreeError(f"{self.series_id}: sem taxa para o pregão {session}") from exc

    def compounded(self, sessions: list[str]) -> float:
        total = 1.0
        for session in sessions:
            total *= 1 + self.daily(session)
        return total - 1

    def to_dict(self) -> dict:
        sessions = sorted(self._daily)
        return {"series_id": self.series_id, "unit": self.unit, "hash": self.hash, "first": sessions[0],
                "last": sessions[-1], "sessions": len(sessions)}


def excess_returns(sessions: list[str], returns: list[float], rf: RiskFreeSeries) -> list[float]:
    if len(sessions) != len(returns):
        raise RiskFreeError("pregões e retornos com tamanhos diferentes")
    return [r - rf.daily(s) for s, r in zip(sessions, returns)]


__all__ = ["RiskFreeError", "RiskFreeSeries", "SCHEMA", "UNITS", "excess_returns"]
