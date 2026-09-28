"""Protocolo v2 — camada de dados point-in-time: fundamentos pela divulgação, ajuste só com evento conhecido,
revisões invisíveis antes de conhecidas, sobrevivência (deslistados no universo enquanto negociaram),
calendário e hash do dataset."""

import copy
import json

import pytest

from stocks_predictor.v2 import synthetic
from stocks_predictor.v2.dataset import DatasetError, PITDataset, decision_instant

RAW = synthetic.build()
DS = PITDataset(RAW)


def raw_copy():
    return copy.deepcopy(RAW)


# -- obrigatório: PIT de fundamentos --------------------------------------------------------------
def test_fundamental_disclosed_at_d_never_appears_before_d():
    records = RAW["fundamentals"]
    checked = 0
    for session in DS.calendar:
        view = DS.view(session)
        for record in records:
            seen = view.fundamental(record["security_id"], record["field"], record["period_end"])
            latest = view.fundamental(record["security_id"], record["field"])
            for got in (seen, latest):
                if got is not None:
                    assert got.available_at <= view.decision_at
            if view.decision_at < record["available_at"]:
                checked += 1
                for got in (seen, latest):
                    assert got is None or (got.period_end, got.version) != (record["period_end"], record["version"])
    assert checked > 100


def test_restatement_replaces_value_only_from_its_disclosure():
    before = DS.view("2020-06-22").fundamental("FUN1", "net_income", "2019-12-31")
    after = DS.view("2020-06-23").fundamental("FUN1", "net_income", "2019-12-31")
    assert (before.value, before.version) == (120.0, 1)
    assert (after.value, after.version) == (95.0, 2)
    assert DS.view("2020-03-16").fundamental("FUN1", "net_income") is None  # divulgado às 22h do dia 16
    assert DS.view("2020-03-17").fundamental("FUN1", "net_income").value == 120.0
    assert DS.view("2020-05-15").fundamental("FUN1", "net_income").period_end == "2020-03-31"


# -- preços ajustados só com o que era conhecido ---------------------------------------------------
def _ratio(view, sid, before, after):
    sessions, _o, closes, _v = view.history(sid)
    return closes[sessions.index(after)] / closes[sessions.index(before)]


def test_reverse_split_adjusts_history_only_after_it_is_known():
    # grupamento 10:1 com data ex 2020-08-03, conhecido só em 2020-08-10 21h
    unknown = _ratio(DS.view("2020-08-05"), "SPL2", "2020-07-31", "2020-08-03")
    known = _ratio(DS.view("2020-08-11"), "SPL2", "2020-07-31", "2020-08-03")
    assert 7 < unknown < 14
    assert 0.7 < known < 1.4
    # desdobramento 2:1 anunciado antes da data ex: a visão seguinte já ajusta
    assert 0.7 < _ratio(DS.view("2020-04-02"), "SPL1", "2020-03-31", "2020-04-01") < 1.4


def test_future_split_never_adjusts_a_past_view():
    early = DS.view("2020-03-02")
    sessions, _o, closes, _v = early.history("SPL1")
    raw = {b["session"]: b["close"] for b in RAW["bars"] if b["security_id"] == "SPL1"}
    assert all(abs(closes[i] - raw[s]) < 1e-12 for i, s in enumerate(sessions))


def test_bar_revision_is_invisible_until_published():
    before = DS.view("2020-02-17").history("E01")
    after = DS.view("2020-02-19").history("E01")
    i, j = before[0].index("2020-02-14"), after[0].index("2020-02-14")
    assert before[2][i] / after[2][j] == pytest.approx(1.5, abs=1e-6)  # preços com 6 casas
    assert DS.realized_bar("E01", "2020-02-14").close == after[2][j]


def test_view_never_contains_the_decision_session_or_later():
    for session in DS.calendar[1:: 37]:
        view = DS.view(session)
        assert view.decision_at == decision_instant(session)
        assert view.signal_session < session
        for sid in view.listed_ids("equity") + view.listed_ids("index_fund"):
            sessions = view.history(sid)[0]
            assert not sessions or sessions[-1] < session


def test_adv_counts_sessions_without_trades_as_zero():
    view = DS.view("2021-03-01")
    sessions, _o, _c, volumes = view.history("ILLQ")
    window = view.calendar[-63:]
    traded = dict(zip(sessions, volumes))
    assert view.average_daily_value("ILLQ", 63) == pytest.approx(sum(traded.get(s, 0.0) for s in window) / 63)
    assert sum(1 for s in window if s not in traded) > 10


# -- obrigatório: sobrevivência -------------------------------------------------------------------
def test_delisted_securities_are_in_the_universe_while_they_traded():
    for session in DS.calendar[1:]:
        listed = DS.view(session).listed_ids("equity")
        assert ("DEL1" in listed) == (session <= "2020-09-30")  # deslistagem anunciada antes: sai no dia seguinte
        assert ("BUST" in listed) == (session <= "2020-07-10")  # deslistagem só conhecida em 2020-07-10 21h
        assert ("IPO1" in listed) == (session > "2020-03-02")   # entra depois do primeiro pregão
    view = DS.view("2020-06-30")
    assert "BUST" in view.listed_ids() and view.history("BUST")[0][-1] == "2020-06-29"


def test_identity_is_point_in_time():
    assert DS.view("2020-04-30").ticker("TCK1") == "TCK13"
    assert DS.view("2020-05-04").ticker("TCK1") == "NOVO3"
    assert DS.view("2020-05-04").issuer("TCK1") == "ISS-TCK1"
    assert DS.view("2020-04-24").ticker("TCK1") == "TCK13"  # anunciada, mas ainda não vigente


# -- calendário, disponibilidade e hash ------------------------------------------------------------
def test_dataset_hash_is_content_addressed():
    assert PITDataset(json.loads(json.dumps(RAW))).hash == DS.hash
    changed = raw_copy()
    changed["bars"][0]["volume_fin"] += 1
    assert PITDataset(changed).hash != DS.hash


@pytest.mark.parametrize("mutate, message", [
    (lambda r: r["calendar"].append("2021-07-03"), "fim de semana"),
    (lambda r: r["calendar"].insert(5, r["calendar"][5]), "ordenado"),
    (lambda r: r["bars"].append(r["bars"][0] | {"session": "2019-03-04"}), "fora do calendário"),
    (lambda r: r["bars"].__setitem__(0, r["bars"][0] | {"available_at": r["bars"][0]["session"] + "T15:00:00Z"}),
     "antes do fechamento"),
    (lambda r: r["fundamentals"].__setitem__(0, r["fundamentals"][0] | {"available_at": "2019-12-30T12:00:00Z"}),
     "antes do fim do período"),
    (lambda r: r["fundamentals"].__setitem__(0, r["fundamentals"][0] | {"available_at": "2030-01-01T00:00:00Z"}),
     "data_cutoff"),
    (lambda r: r["bars"].__setitem__(0, r["bars"][0] | {"close": -1.0}), "positivo"),
    (lambda r: r["securities"][0].__setitem__("delisted_on", "2020-01-02"), "andam juntos"),
    (lambda r: r["calendar"].append("2021-07-01"), "sem nenhum negócio"),
    (lambda r: r["bars"].__setitem__(0, r["bars"][0] | {"available_at": "2019-01-02T21:30:00"}), "UTC"),
    (lambda r: r.__setitem__("schema", "stocks-pit-dataset/1"), "não é"),
])
def test_dataset_validation_fails_closed(mutate, message):
    raw = raw_copy()
    mutate(raw)
    with pytest.raises(DatasetError, match=message):
        PITDataset(raw)


def test_conflicting_duplicates_are_rejected():
    raw = raw_copy()
    raw["fundamentals"].append(raw["fundamentals"][0] | {"value": 1.0})
    with pytest.raises(DatasetError, match="conflitante"):
        PITDataset(raw)
    raw = raw_copy()
    raw["bars"].append(raw["bars"][0] | {"close": raw["bars"][0]["close"] + 1})
    with pytest.raises(DatasetError, match="conflitante"):
        PITDataset(raw)
