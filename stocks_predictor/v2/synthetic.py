"""Dataset SINTÉTICO determinístico no schema ``stocks-pit-dataset/2`` — só para testes e demonstração do protocolo.

Nunca é evidência empírica. Contém de propósito cada armadilha que o protocolo precisa tratar:

    IPO1   lista no meio da amostra (anúncio da listagem dias antes)
    DEL1   deslistada com anúncio prévio; sai pelo último fechamento
    BUST   falência: último pregão em 2020-06-30, saída a R$ 0, deslistagem só conhecida em 2020-07-10
    TCK1   troca de ticker (mesmo emissor) em 2020-05-04
    SPL1   desdobramento 2:1, ex 2020-04-01, anunciado em 2020-03-20
    SPL2   grupamento 10:1, ex 2020-08-03, mas o dataset só soube em 2020-08-10 (disponibilidade atrasada)
    ILLQ   ilíquida: volume baixo e pregões sem negócio
    E01    barra de 2020-02-14 revisada dois pregões depois
    FUN1   lucro de 2019 divulgado em 2020-03-16 e reapresentado em 2020-06-22; 1T20 divulgado em 2020-05-14
    IDX11  fundo de índice (buy-and-hold do índice)
    DIV1   proventos em dinheiro
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date, timedelta

from . import SCHEMA

HOLIDAYS = {"2019-03-04", "2019-03-05", "2019-04-19", "2019-05-01", "2019-11-15", "2019-12-25", "2020-01-01",
            "2020-02-24", "2020-02-25", "2020-04-10", "2020-04-21", "2020-05-01", "2020-09-07", "2020-10-12",
            "2020-11-02", "2020-12-25", "2021-01-01", "2021-02-15", "2021-02-16", "2021-04-02", "2021-04-21"}
BAR_TIME = "T21:30:00Z"


def trading_calendar(start: str = "2019-01-02", end: str = "2021-06-30") -> list[str]:
    day, last, out = date.fromisoformat(start), date.fromisoformat(end), []
    while day <= last:
        if day.weekday() < 5 and day.isoformat() not in HOLIDAYS:
            out.append(day.isoformat())
        day += timedelta(days=1)
    return out


def _after(session: str, days: int, time: str = "T12:30:00Z") -> str:
    return (date.fromisoformat(session) + timedelta(days=days)).isoformat() + time


@dataclass(frozen=True)
class _Spec:
    drift: float
    vol: float
    adv: float
    listed: str | None = None
    delisted: str | None = None
    delisted_known: str = ""
    delisting_value: float | None = None
    gaps: float = 0.0


def build(seed: int = 7, *, end: str = "2021-06-30") -> dict:
    rng = random.Random(seed)
    cal = trading_calendar(end=end)
    first = cal[0]
    specs = {f"E{i:02d}": _Spec(rng.uniform(-0.0002, 0.0009), rng.uniform(0.012, 0.028), rng.uniform(4e6, 4e7))
             for i in range(1, 11)}
    specs |= {
        "IPO1": _Spec(0.0006, 0.03, 1.5e7, listed="2020-03-02"),
        "DEL1": _Spec(0.0001, 0.02, 8e6, delisted="2020-09-30", delisted_known="2020-09-15"),
        "BUST": _Spec(-0.004, 0.04, 6e6, delisted="2020-06-30", delisted_known="2020-07-10", delisting_value=0.0),
        "TCK1": _Spec(0.0003, 0.018, 1.2e7),
        "SPL1": _Spec(0.0005, 0.02, 2e7),
        "SPL2": _Spec(-0.0003, 0.025, 9e6),
        "ILLQ": _Spec(0.0004, 0.03, 5e4, gaps=0.4),
        "DIV1": _Spec(0.0002, 0.015, 1.8e7),
        "FUN1": _Spec(0.0004, 0.02, 1.1e7),
    }
    multipliers = {"SPL1": ("2020-04-01", 2.0, "2020-03-20T21:00:00Z", "desdobramento"),
                   "SPL2": ("2020-08-03", 0.1, "2020-08-10T21:00:00Z", "grupamento")}
    securities, identities, bars, actions, cash_events, fundamentals = [], [], [], [], [], []
    closes: dict[str, dict[str, float]] = {}
    for sid, spec in specs.items():
        listed = spec.listed or first
        delisted = spec.delisted
        securities.append({
            "security_id": sid, "kind": "equity", "listed_on": listed,
            "listing_available_at": (_after(listed, -10) if listed != first else first + "T00:00:00Z"),
            "delisted_on": delisted,
            "delisting_available_at": None if delisted is None else spec.delisted_known + "T21:00:00Z",
            "delisting_value": spec.delisting_value})
        identities.append({"security_id": sid, "ticker": sid + "3", "issuer_id": "ISS-" + sid,
                           "effective_on": listed,
                           "available_at": (_after(listed, -10) if listed != first else first + "T00:00:00Z")})
        price = rng.uniform(8, 60)
        closes[sid] = {}
        for session in cal:
            if session < listed or (delisted is not None and session > delisted):
                continue
            if sid in multipliers and session == multipliers[sid][0]:
                price /= multipliers[sid][1]
            opening = price * math.exp(rng.gauss(0, spec.vol / 3))
            price = opening * math.exp(spec.drift + rng.gauss(0, spec.vol))
            if rng.random() < spec.gaps:
                continue
            closes[sid][session] = price
            bars.append({"security_id": sid, "session": session, "open": round(opening, 6),
                         "close": round(price, 6), "volume_fin": round(spec.adv * math.exp(rng.gauss(0, 0.5)), 2),
                         "available_at": session + BAR_TIME})
    # índice: fundo que replica a média igual das ações listadas desde o início (sem IPO1)
    level, base = 100.0, [s for s in specs if specs[s].listed is None]
    previous = None
    securities.append({"security_id": "IDX11", "kind": "index_fund", "listed_on": first,
                       "listing_available_at": first + "T00:00:00Z", "delisted_on": None,
                       "delisting_available_at": None, "delisting_value": None})
    identities.append({"security_id": "IDX11", "ticker": "IDX11", "issuer_id": "ISS-IDX",
                       "effective_on": first, "available_at": first + "T00:00:00Z"})
    for session in cal:
        if previous is not None:
            moves = [closes[s][session] / closes[s][previous] for s in base
                     if session in closes[s] and previous in closes[s]
                     and not (s in multipliers and session == multipliers[s][0])]
            level *= sum(moves) / len(moves) if moves else 1.0
        bars.append({"security_id": "IDX11", "session": session, "open": round(level * (1 + rng.gauss(0, 0.002)), 6),
                     "close": round(level, 6), "volume_fin": round(5e7 * math.exp(rng.gauss(0, 0.3)), 2),
                     "available_at": session + BAR_TIME})
        previous = session
    for sid, (ex, multiplier, known, kind) in multipliers.items():
        actions.append({"security_id": sid, "ex_session": ex, "kind": kind, "share_multiplier": multiplier,
                        "available_at": known})
    identities.append({"security_id": "TCK1", "ticker": "NOVO3", "issuer_id": "ISS-TCK1",
                       "effective_on": "2020-05-04", "available_at": "2020-04-24T21:00:00Z"})
    for ex in ("2019-06-03", "2019-12-02", "2020-06-01", "2020-12-01"):
        cash_events.append({"security_id": "DIV1", "ex_session": ex, "amount_per_share": 0.45,
                            "available_at": _after(ex, -14, "T21:00:00Z")})
    # revisão de barra: a primeira versão do fechamento de E01 em 2020-02-14 estava errada
    for bar in bars:
        if bar["security_id"] == "E01" and bar["session"] == "2020-02-14":
            bars.append(bar | {"close": round(bar["close"] * 1.5, 6), "available_at": "2020-02-14T21:00:00Z"})
            bar["available_at"] = "2020-02-18T22:00:00Z"
            break
    fundamentals += [
        {"security_id": "FUN1", "field": "net_income", "period_end": "2019-12-31", "version": 1,
         "value": 120.0, "available_at": "2020-03-16T22:00:00Z"},
        {"security_id": "FUN1", "field": "net_income", "period_end": "2019-12-31", "version": 2,
         "value": 95.0, "available_at": "2020-06-22T22:00:00Z"},
        {"security_id": "FUN1", "field": "net_income", "period_end": "2020-03-31", "version": 1,
         "value": 30.0, "available_at": "2020-05-14T22:00:00Z"},
    ]
    return {"schema": SCHEMA, "dataset_version": f"synthetic-seed{seed}-{end}", "data_cutoff": cal[-1] + "T23:59:59Z",
            "calendar": cal, "securities": securities, "identity_events": identities, "bars": bars,
            "corporate_actions": actions, "cash_events": cash_events, "fundamentals": fundamentals}


def riskfree(end: str = "2021-06-30") -> dict:
    """Taxa livre de risco SINTÉTICA no formato da SGS 11 (% ao dia), degraus de 6,5% a.a. (2019), 4,25%
    (até 2020-06), 2% (até 2021-03) e 3,5%. Só teste e demonstração; a política recusa ``SYNTHETIC-RF``."""
    def annual(session: str) -> float:
        if session < "2020-01-01":
            return 0.065
        if session < "2020-07-01":
            return 0.0425
        if session < "2021-04-01":
            return 0.02
        return 0.035
    rates = [{"session": s, "rate": round(((1 + annual(s)) ** (1 / 252) - 1) * 100, 8)}
             for s in trading_calendar(end=end)]
    return {"schema": "stocks-riskfree/1", "series_id": "SYNTHETIC-RF", "unit": "percent_per_day",
            "source": {"kind": "synthetic", "generator": "stocks_predictor.v2.synthetic.riskfree"}, "rates": rates}


__all__ = ["HOLIDAYS", "build", "riskfree", "trading_calendar"]
