import hashlib
import json
from pathlib import Path

import pytest

from stocks_predictor import discovery_value_repair as repair
from stocks_predictor.discovery_h17 import adjustment_map


def protocol():
    path = Path(__file__).parents[1]/"docs/research/2026-09-07-value-repair-protocol.json"
    return json.loads(path.read_text(encoding="utf-8"))


def raw_quotes():
    path = Path(__file__).parent/"fixtures/value-repair-quotes.txt"
    result = {}
    for raw in path.read_bytes().splitlines():
        ticker = raw[12:24].strip().decode("ascii")
        d = raw[2:10].decode("ascii")
        day = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        scale = int(raw[210:217])
        result[ticker, day] = {"prices": (int(raw[56:69])/100/scale, int(raw[108:121])/100/scale),
                              "bdi": raw[10:12].decode("ascii"), "isin": raw[230:242].decode("ascii"),
                              "sha256": hashlib.sha256(raw).hexdigest()}
    return result


def test_remeasurement_is_separately_sealed_and_counted():
    p = protocol()
    canonical = json.dumps(p, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assert hashlib.sha256(canonical).hexdigest() == repair.PROTOCOL_SHA256
    assert p["first_outputs_already_observed"]
    assert p["search_budget"]["observed_return_evaluations_after_minimum"] == 25


@pytest.mark.parametrize("ticker", ["QUAL3", "HGTX3", "AMER3", "PETZ3", "HAPV3"])
def test_review_is_tied_to_exact_original_b3_quote_lines(ticker):
    r = next(r for r in protocol()["reviewed_moves"] if r["ticker"] == ticker)
    data = raw_quotes()
    before, after = data[ticker, r["previous_date"]], data[ticker, r["date"]]
    assert r["previous_raw_line_sha256"] == before["sha256"]
    assert r["next_raw_line_sha256"] == after["sha256"]
    assert r["previous_close"] == before["prices"][1]
    assert r["next_open"] == after["prices"][0]
    assert before["isin"] == after["isin"] == r["isin"]


def test_americanas_crash_and_change_to_bdi_08_are_retained():
    data = raw_quotes()
    assert data["AMER3", "2023-01-19"]["bdi"] == "02"
    assert data["AMER3", "2023-01-20"]["bdi"] == "08"
    quotes = {day: row["prices"] for (ticker, day), row in data.items() if ticker == "AMER3"}
    member = {"ticker": "AMER3", "isin": "BRAMERACNOR6"}
    identity = {"AMER3": [{"first_date": "2023-01-02", "last_date": "2023-04-03", "isin": member["isin"]}]}
    reviews = {(r["ticker"], r["date"]): r for r in protocol()["reviewed_moves"]}
    result = repair.score(member, "2023-01-02", "2023-02-01", {"AMER3": quotes}, identity, [], [], reviews)
    assert result["price_return"] == pytest.approx(1.97/9.47-1)
    assert result["price_return"] < -0.79
    assert result["quality_notes"][0]["overnight_return"] < -0.76
    assert not result["quality_reasons"]
    missing_review = repair.score(member, "2023-01-02", "2023-02-01", {"AMER3": quotes}, identity, [], [], {})
    assert missing_review["price_return"] is None


def test_confirmed_jump_does_not_clear_other_unresolved_events():
    ticker = "PETZ3"
    r = next(r for r in protocol()["reviewed_moves"] if r["ticker"] == ticker)
    data = raw_quotes()
    bars = {ticker: {day: row["prices"] for (name, day), row in data.items() if name == ticker}}
    identity = {ticker: [{"first_date": r["previous_date"], "last_date": r["date"], "isin": r["isin"]}]}
    member = {"ticker": ticker, "isin": r["isin"]}
    event = {"ex_date": r["date"], "label": "INCORPORACAO", "price_factor": None}
    result = repair.score(member, r["previous_date"], r["date"], bars, identity, [event], [], {(ticker, r["date"]): r})
    assert result["price_return"] is None
    assert result["quality_reasons"] == ["UNMODELLED_INCORPORACAO"]
    assert result["quality_notes"]


def test_mismatched_review_cannot_clear_a_different_price_move():
    r = next(r for r in protocol()["reviewed_moves"] if r["ticker"] == "PETZ3")
    bars = {"PETZ3": {r["previous_date"]: (3.52, 3.50), r["date"]: (6.0, 6.0)}}
    identity = {"PETZ3": [{"first_date": r["previous_date"], "last_date": r["date"], "isin": r["isin"]}]}
    result = repair.score({"ticker": "PETZ3", "isin": r["isin"]}, r["previous_date"], r["date"], bars,
                          identity, [], [], {("PETZ3", r["date"]): r})
    assert result["price_return"] is None


@pytest.mark.parametrize("ticker,day", [("NATU3", "2019-09-18"), ("PSSA3", "2021-10-21")])
def test_original_bonus_credited_once_after_explicit_legacy_source_supersession(ticker, day):
    event = {"ticker": ticker, "ex_date": day, "label": "BONIFICACAO", "price_factor": 0.5}
    factors, issues = adjustment_map([event], [])
    assert factors[day] == 0.5
    assert not issues
