"""H16 — efeito virada-de-mês (pré-registro 2026-09-04).

Primeira hipótese de TIMING testada neste domínio — não usa `walk_forward`
(mecânica própria em `backtest.run_h16`); usa o MESMO pedágio/registro via
`_finalize_hypothesis` (extraído de `_run_hypothesis` nesta mesma sessão).
"""
import datetime

import backtest
import cotahist
import db
import trials_gate


def _dates(n, start=(2016, 7, 1)):
    base = datetime.date(*start)
    return [(base + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]


def _synthetic_conn(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]
    cotahist.load_prices(conn, cotahist.synthetic_cotahist(tickers, _dates(900), seed=11),
                         "COTAHIST_SYNTH.TXT")
    return conn


def test_run_h16_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)     # h1 + h2 no tmp
    v = backtest.run_h16(cfg, conn, trials_path=tp)
    conn.close()

    assert "H16:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3     # h1 + h2 + h16 neste registro tmp
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_h16_frozen_config_hash_golden():
    """Mexeu num param [H16-FROZEN] -> quebra alto AQUI (pré-registro 2026-09-04)."""
    from config import h16_frozen_config_hash, load_config
    assert h16_frozen_config_hash(load_config()) == "584350278798ef6a"


def test_h16_frozen_hash_ignores_operational_params():
    from config import h16_frozen_config_hash, load_config
    cfg = load_config()
    base = h16_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h16_frozen_config_hash(cfg) == base
    cfg["h16_factor"]["last_days_of_month"] = 2       # tocar num FROZEN muda o lacre
    assert h16_frozen_config_hash(cfg) != base


def test_turn_of_month_days_known_calendar():
    dates = [f"2020-01-{d:02d}" for d in range(28, 32)] + \
            [f"2020-02-{d:02d}" for d in range(1, 6)]
    # ["2020-01-28","01-29","01-30","01-31","02-01","02-02","02-03","02-04","02-05"]
    tom = backtest._turn_of_month_days(dates, last_days=1, first_days=3)
    # último pregão de janeiro (01-31) + 3 primeiros de fevereiro (02-01,02,03)
    # + o último pregão do próprio fevereiro (02-05, sem mês seguinte nos
    # dados, mesmo caso de "last_month_has_no_next_window" abaixo).
    assert tom == {"2020-01-31", "2020-02-01", "2020-02-02", "2020-02-03", "2020-02-05"}


def test_turn_of_month_days_last_month_has_no_next_window():
    dates = [f"2020-01-{d:02d}" for d in range(28, 32)]
    tom = backtest._turn_of_month_days(dates, last_days=1, first_days=3)
    # sem mês seguinte nos dados -> só o "last_days" do único mês entra
    assert tom == {"2020-01-31"}


def test_turn_of_month_days_multiple_days_each_side():
    dates = [f"2020-01-{d:02d}" for d in range(29, 32)] + \
            [f"2020-02-{d:02d}" for d in range(1, 4)]
    tom = backtest._turn_of_month_days(dates, last_days=2, first_days=2)
    # + os 2 últimos pregões do próprio fevereiro (02-02, 02-03), mesmo caso
    # do mês final sem mês seguinte nos dados.
    assert tom == {"2020-01-30", "2020-01-31", "2020-02-01", "2020-02-02", "2020-02-03"}
