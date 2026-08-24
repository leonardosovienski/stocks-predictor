"""Runner integrado do domínio RJ: universo -> episódios -> famílias -> judge.

Fecha a lacuna entre a mecânica validada em dado sintético (power gate) e a
hipótese real: dado o banco SQLite com `rj_universe` preenchido (coleta manual
aprovada — a mesma disciplina de `source`+`approved_by` dos ajustes), este
módulo executa o protocolo de ponta a ponta e grava a trilha:

    rj_universe (empresas em RJ, com rally ou não — universo PRIMEIRO)
      -> point_in_time_candidates + select_primary/secondary (rj_episodes)
      -> classify_episode nas janelas PRIMÁRIA e SECUNDÁRIA, separadas
      -> scores das 9 famílias por episódio (rj_family_scores)
      -> judge.run_all_families sobre os episódios PRIMÁRIOS não-censurados
      -> relatório JSON em reports/

Disciplina de escopo (fail-closed, sem exceção silenciosa):
- empresa sem preço no banco, sem candidato point-in-time, ou episódio
  primário censurado: fora da análise primária, com o MOTIVO contado no
  relatório — nunca reclassificada para caber no teste;
- `liquidity` exige free float externo (CVM/RI): se o chamador não fornecer
  o mapa ticker->ações em circulação, a família fica inteira como
  "dado indisponível" (reportada como tal), NÃO estimada de mentirinha;
- famílias cujo score é None para um episódio simplesmente não entram nas
  units daquela família — o judge já lida com N pequeno por família;
- nenhum parâmetro [RJ-FROZEN] é redefinido aqui: tudo vem do config;
- fila de revisão humana (regra 5, fail-closed): TODA leitura de
  `rj_universe` e `rj_events` filtra `approved_by IS NOT NULL` — linhas
  pendentes de revisão não existem para a análise (o ingest CVM grava
  deliberadamente com approved_by NULL; aprovar é ato humano explícito).

Uso (CLI):
    python src/rj_pipeline.py --db data/stocks.db --config config_rj.yaml \
        --asof 2026-08-24 --out reports/rj_run.json \
        [--free-float-csv free_float.csv]   # colunas: ticker,shares_outstanding
"""
import argparse
import json
import logging
import sqlite3
from datetime import date

import rj_episodes as episodes
import rj_families as families
import rj_judge as judge
from adjust import adjusted_series

logger = logging.getLogger(__name__)

_VOL = "volume_fin"


def _load_price_series(conn: sqlite3.Connection, ticker: str,
                       asof: str) -> tuple[list[str], list[float]]:
    """Série ajustada de fechamentos TRUNCADA em asof (point-in-time: o
    runner de hoje não pode ver pregão de amanhã ao classificar censura)."""
    dates, closes = adjusted_series(conn, ticker)
    idx = [i for i, d in enumerate(dates) if d <= asof]
    return ([dates[i] for i in idx], [closes[i] for i in idx])


def _load_volumes(conn: sqlite3.Connection, ticker: str,
                  asof: str) -> tuple[list[str], list[float]]:
    rows = conn.execute(
        f"SELECT date, MAX({_VOL}) FROM prices_raw "
        "WHERE ticker=? AND date<=? GROUP BY date ORDER BY date",
        (ticker, asof)).fetchall()
    return ([r[0] for r in rows], [r[1] for r in rows])


def _load_events(conn: sqlite3.Connection, ticker: str) -> list[dict]:
    """Eventos discretos da empresa; o FILTRO por known_at é das famílias
    (anti-lookahead informacional vive lá, não aqui)."""
    # fila de revisão humana (regra 5): evento sem approved_by NÃO entra —
    # fail-closed. Evento pendente de revisão não existe para a análise.
    cols = ["event_date", "published_at", "known_at", "event_type"]
    rows = conn.execute(
        f"SELECT {', '.join(cols)} FROM rj_events "
        "WHERE ticker=? AND approved_by IS NOT NULL", (ticker,))
    return [dict(zip(cols, r)) for r in rows]


def _pre_rj_high(dates: list[str], closes: list[float],
                 rj_request_date: str) -> str | None:
    """Data da máxima ajustada ANTES do pedido de RJ (insumo de drawdown)."""
    idx = [i for i, d in enumerate(dates) if d < rj_request_date]
    if not idx:
        return None
    return dates[max(idx, key=lambda i: closes[i])]


def build_episodes(conn: sqlite3.Connection, cfg: dict, asof: str) -> dict:
    """Universo -> episódios classificados. Retorna
    {"episodes": [...], "excluded": {ticker: motivo}}.

    Cada episódio: ticker, trough_date, is_primary, outcome_primaria,
    outcome_secundaria (calculadas e guardadas SEPARADAS — nunca fundidas,
    protocolo §4) e os metadados que as famílias precisam."""
    rcfg = cfg["rally"]
    lookback = rcfg["point_in_time_backward_lookback_days"]
    min_sep = rcfg["primary_window_trading_days"]
    out, excluded = [], {}
    # fila de revisão humana (regra 5): só empresas APROVADAS entram no
    # universo analisado — uma linha pendente (approved_by NULL) é candidata
    # a universo, não universo. Fail-closed: na dúvida, fica de fora.
    universe = conn.execute(
        "SELECT ticker, rj_request_date, plan_presented_date, "
        "plan_approved_date, rj_end_date FROM rj_universe "
        "WHERE approved_by IS NOT NULL ORDER BY ticker"
    ).fetchall()
    for ticker, rj_date, plan_pres, plan_appr, rj_end in universe:
        dates, closes = _load_price_series(conn, ticker, asof)
        if not dates:
            excluded[ticker] = "sem serie de precos no banco"
            continue
        candidates = episodes.point_in_time_candidates(
            dates, closes, rj_date, backward_lookback=lookback)
        primary = episodes.select_primary_episode(candidates)
        if primary is None:
            excluded[ticker] = ("nenhum candidato point-in-time "
                                "(historico insuficiente ou nunca foi minima)")
            continue
        kept = episodes.select_secondary_episodes(candidates, dates, min_sep)
        for k, trough_date in enumerate(kept):
            trough_idx = dates.index(trough_date)
            ep = {
                "ticker": ticker, "trough_date": trough_date,
                "trough_price": closes[trough_idx],
                "is_primary": 1 if k == 0 else 0,
                "rj_request_date": rj_date,
                "plan_presented_date": plan_pres,
                "plan_approved_date": plan_appr,
                "rj_end_date": rj_end,
                "primary": episodes.classify_episode(
                    dates, closes, trough_date, cfg, asof,
                    window_key="primary_window_trading_days"),
                "secondary": episodes.classify_episode(
                    dates, closes, trough_date, cfg, asof,
                    window_key="secondary_window_trading_days"),
                "dates": dates, "closes": closes,
            }
            out.append(ep)
    return {"episodes": out, "excluded": excluded}


def compute_family_scores(conn: sqlite3.Connection, ep: dict, cfg: dict,
                          free_float: dict | None, asof: str) -> dict:
    """Scores das 9 famílias para UM episódio. None = família sem dado para
    este episódio (fica fora das units, não vira zero)."""
    ticker, trough = ep["ticker"], ep["trough_date"]
    dates, closes = ep["dates"], ep["closes"]
    vdates, vols = _load_volumes(conn, ticker, asof)
    events = _load_events(conn, ticker)
    pre_high = _pre_rj_high(dates, closes, ep["rj_request_date"])

    scores = {
        "drawdown": (families.drawdown(dates, closes, trough, pre_high)
                     if pre_high else None),
        "liquidity": (families.liquidity(vols, vdates, trough, free_float[ticker])
                      if free_float and ticker in free_float else None),
        "volume_dynamics_antecedent":
            families.volume_dynamics_antecedent(vols, vdates, trough),
        "volume_dynamics_contemporaneous":
            families.volume_dynamics(vols, vdates, trough),
        "rj_stage": families.rj_stage(trough, ep["plan_presented_date"],
                                      ep["plan_approved_date"], ep["rj_end_date"]),
        "ownership": families.ownership(events, trough),
        "momentum_volatility": families.momentum_volatility(dates, closes, trough),
        "time_since_rj": families.time_since_rj(ep["rj_request_date"], trough, dates),
        "info_trigger": families.info_trigger(events, trough),
    }
    return scores


def persist_run(conn: sqlite3.Connection, built: dict, asof: str) -> None:
    """Grava episódios + scores. Re-rodar no MESMO asof é idempotente
    (INSERT OR IGNORE + nada diverge). Re-rodar com asof POSTERIOR atualiza
    a linha existente quando o outcome diverge (ex.: censored -> rally) —
    manter o outcome velho gravado deixaria o banco contradizer a trilha
    mais recente da observação. Scores de família (PK episode_id+family)
    divergentes também são atualizados."""
    for ep in built["episodes"]:
        cols = (ep["ticker"], ep["trough_date"], ep["trough_price"], ep["is_primary"],
                ep["primary"]["outcome"], ep["primary"]["rally_pct"],
                ep["primary"]["rally_date"], ep["primary"]["trading_days_to_rally"],
                ep["primary"]["censored"])
        conn.execute(
            "INSERT OR IGNORE INTO rj_episodes(ticker, trough_date, trough_price,"
            " is_primary, outcome, rally_pct, rally_date, trading_days_to_rally,"
            " censored) VALUES(?,?,?,?,?,?,?,?,?)", cols)
        old = conn.execute(
            "SELECT trough_price, is_primary, outcome, rally_pct, rally_date,"
            " trading_days_to_rally, censored FROM rj_episodes"
            " WHERE ticker=? AND trough_date=?",
            (ep["ticker"], ep["trough_date"])).fetchone()
        new = cols[2:]
        if tuple(old) != tuple(new):
            conn.execute(
                "UPDATE rj_episodes SET trough_price=?, is_primary=?, outcome=?,"
                " rally_pct=?, rally_date=?, trading_days_to_rally=?, censored=?"
                " WHERE ticker=? AND trough_date=?",
                (*new, ep["ticker"], ep["trough_date"]))
        episode_id = conn.execute(
            "SELECT id FROM rj_episodes WHERE ticker=? AND trough_date=?",
            (ep["ticker"], ep["trough_date"])).fetchone()[0]
        for fam, val in ep["scores"].items():
            if isinstance(val, str):      # rj_stage categórico: guarda hash-free
                continue                  # (tabela é REAL; categórico vive no relatório)
            conn.execute(
                "INSERT OR IGNORE INTO rj_family_scores(episode_id, family, value)"
                " VALUES(?,?,?)", (episode_id, fam, val))
            conn.execute(
                "UPDATE rj_family_scores SET value=?"
                " WHERE episode_id=? AND family=? AND value IS NOT ?",
                (val, episode_id, fam, val))
    conn.commit()


def run_pipeline(conn: sqlite3.Connection, cfg: dict, asof: str,
                 free_float: dict | None = None) -> dict:
    """Executa o protocolo RJ de ponta a ponta. Retorna o relatório completo
    (também serializável em JSON): exclusões com motivo, episódios, vereditos
    pós-FDR e contagens de dados faltantes por família."""
    built = build_episodes(conn, cfg, asof)
    for ep in built["episodes"]:
        ep["scores"] = compute_family_scores(conn, ep, cfg, free_float, asof)

    # análise primária: episódios PRIMÁRIOS, janela PRIMÁRIA, sem censurados
    # e sem dado inválido (preço de fundo <= 0 = dado quebrado: conta como
    # excluído/missing, NUNCA como controle — viraria denominador falso).
    primary = [ep for ep in built["episodes"]
               if ep["is_primary"] == 1 and ep["primary"]["censored"] == 0
               and ep["primary"]["outcome"] != "invalid_data"]
    units_by_family = {name: [] for name in families.REGISTRY}
    for ep in primary:
        group = 1 if ep["primary"]["outcome"] == "rally" else 0
        for name, val in ep["scores"].items():
            if val is None:
                continue
            if name in families.CATEGORICAL_FAMILIES:
                units_by_family[name].append((ep["ticker"], val, group))
            else:
                units_by_family[name].append((ep["ticker"], float(val), group))

    verdicts = judge.run_all_families(units_by_family, cfg)

    # checagem secundária (config: secondary_episodes_as_separate_check):
    # todos os episódios (primário+secundários) na janela SECUNDÁRIA (252
    # pregões), julgados como verificação separada — nunca somados ao
    # veredito primário nem ao FDR oficial; robustez, não hipótese.
    secondary_eps = [ep for ep in built["episodes"]
                     if ep["secondary"]["censored"] == 0
                     and ep["secondary"]["outcome"] != "invalid_data"]
    units_secondary = {name: [] for name in families.REGISTRY}
    for ep in secondary_eps:
        group = 1 if ep["secondary"]["outcome"] == "rally" else 0
        for name, val in ep["scores"].items():
            if val is None:
                continue
            if name in families.CATEGORICAL_FAMILIES:
                units_secondary[name].append((ep["ticker"], val, group))
            else:
                units_secondary[name].append((ep["ticker"], float(val), group))
    verdicts_secondary = (judge.run_all_families(units_secondary, cfg)
                          if secondary_eps else None)

    n_universe = conn.execute(
        "SELECT COUNT(*) FROM rj_universe WHERE approved_by IS NOT NULL"
    ).fetchone()[0]
    n_rally = sum(1 for ep in primary if ep["primary"]["outcome"] == "rally")
    missing = {name: sum(1 for ep in primary if ep["scores"][name] is None)
               for name in families.REGISTRY}
    report = {
        "asof": asof,
        # universo é contado em EMPRESAS (uma linha de rj_universe cada),
        # não em episódios — uma empresa pode gerar vários episódios.
        "universe_size": n_universe,
        "excluded": built["excluded"],
        "n_primary_analyzed": len(primary),
        "n_rally": n_rally,
        "n_control": len(primary) - n_rally,
        "n_censored_excluded": sum(
            1 for ep in built["episodes"]
            if ep["is_primary"] == 1 and ep["primary"]["censored"] == 1),
        # preço de fundo <= 0 = dado quebrado: excluído/missing, não controle
        "n_invalid_data_excluded": sum(
            1 for ep in built["episodes"]
            if ep["primary"]["outcome"] == "invalid_data"
            or ep["secondary"]["outcome"] == "invalid_data"),
        "missing_scores_by_family": missing,
        "verdicts": verdicts,
        "verdicts_secondary_check": verdicts_secondary,
        "n_secondary_check": len(secondary_eps),
        "episodes": [
            {"ticker": ep["ticker"], "trough_date": ep["trough_date"],
             "is_primary": ep["is_primary"],
             "outcome_primary_window": ep["primary"]["outcome"],
             "outcome_secondary_window": ep["secondary"]["outcome"],
             "scores": ep["scores"]}
            for ep in built["episodes"]],
    }
    persist_run(conn, built, asof)
    return report


def load_free_float_csv(path: str) -> dict:
    """CSV ticker,shares_outstanding — fonte externa (CVM/RI), obrigatória
    para a família liquidity; sem ele ela é reportada como indisponível."""
    import csv
    with open(path, newline="", encoding="utf-8") as f:
        return {r["ticker"]: float(r["shares_outstanding"]) for r in csv.DictReader(f)}


def main(argv=None) -> int:
    import pathlib
    import sys
    import yaml

    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from db import get_connection  # noqa: E402

    ap = argparse.ArgumentParser(description="Runner integrado do predictor-rj")
    ap.add_argument("--db", default=None, help="caminho do SQLite (default: db.DB_DEFAULT)")
    ap.add_argument("--config", default=str(
        pathlib.Path(__file__).parent.parent / "config_rj.yaml"))
    ap.add_argument("--asof", default=date.today().isoformat(),
                    help="data de corte point-in-time (default: hoje)")
    ap.add_argument("--out", default=None, help="caminho do relatório JSON")
    ap.add_argument("--free-float-csv", default=None)
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    ff = load_free_float_csv(args.free_float_csv) if args.free_float_csv else None
    if ff is None:
        logger.warning("sem --free-float-csv: familia 'liquidity' ficara indisponivel")

    conn = get_connection(args.db)
    report = run_pipeline(conn, cfg, args.asof, free_float=ff)

    out = args.out or f"reports/rj_run_{args.asof}.json"
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(f"universo: {report['universe_size']} | analisados: "
          f"{report['n_primary_analyzed']} (rally={report['n_rally']}, "
          f"controle={report['n_control']}) | censurados fora: "
          f"{report['n_censored_excluded']} | excluidos: {len(report['excluded'])}")
    print(f"relatorio: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
