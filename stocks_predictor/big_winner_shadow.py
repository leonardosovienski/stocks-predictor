"""Idempotent no-capital shadow runner for the frozen V2 candidate."""
from __future__ import annotations
import bisect, datetime as dt, json, sqlite3, statistics
from pathlib import Path

from .big_winner_v2 import apply_share_count_continuity, generate_decision, sha256_file, verify_selection_freeze
from .prospective_big_winner import append_decision, connect, stable_decision_receipt, write_artifact

def _load(conn, asof):
    series={}; sources=set()
    for day,ticker,close,factor,source in conn.execute("SELECT date,ticker,close,quote_factor,source_file FROM prices_raw WHERE market_type='010' ORDER BY ticker,date"):
        data=series.setdefault(ticker,[[],[]]); data[0].append(day); data[1].append(close/factor); sources.add(source)
    adjustments={}
    for ticker,ex_date,factor in conn.execute("SELECT ticker,ex_date,factor FROM adjustments WHERE approved_by IS NOT NULL AND type IN ('split','grupamento') AND ex_date<=? ORDER BY ticker,ex_date",(asof,)):
        adjustments.setdefault(ticker,[]).append((ex_date,factor))
    for ticker,(dates,closes) in series.items():
        closes[:]=apply_share_count_continuity(dates,closes,adjustments.get(ticker,[]),asof)
    return {k:(v[0],v[1]) for k,v in series.items()},sorted(sources)

def _universe(conn,asof,top_n=60):
    """Strict PIT universe without runtime dependencies outside the stdlib."""
    quarantined={r[0] for r in conn.execute("SELECT DISTINCT ticker FROM quarantine WHERE date<? AND (resolved_at IS NULL OR resolved_at>=?)",(asof,asof))}
    window=[r[0] for r in conn.execute("SELECT DISTINCT date FROM prices_raw WHERE date<? AND market_type='010' ORDER BY date DESC LIMIT 126",(asof,))]
    if len(window)<126:return []
    start=window[-1]
    history={r[0]:(r[1],r[2]) for r in conn.execute("SELECT ticker,COUNT(DISTINCT date),MAX(date) FROM prices_raw WHERE date<? AND market_type='010' GROUP BY ticker",(asof,))}
    volumes={}
    for ticker,_day,volume in conn.execute("SELECT ticker,date,MAX(volume_fin) FROM prices_raw WHERE date>=? AND date<? AND market_type='010' GROUP BY ticker,date",(start,asof)):
        volumes.setdefault(ticker,[]).append(volume)
    best={}
    for ticker,(count,last) in history.items():
        if ticker in quarantined or count<252 or last<start:continue
        values=volumes.get(ticker,[])+[0.0]*(126-len(volumes.get(ticker,[])))
        median=statistics.median(values); root=ticker[:4]
        if root not in best or median>best[root][1]:best[root]=(ticker,median)
    return [ticker for ticker,_median in sorted(best.values(),key=lambda item:(-item[1],item[0]))[:top_n]]

def run_shadow(*,database_path,ledger_path,artifact_directory,selection_freeze_path,
               final_freeze_path,asof,execution_time,code_commit,decision_timestamp=None,
               development_backfill=True):
    selection=verify_selection_freeze(selection_freeze_path)
    final=json.loads(Path(final_freeze_path).read_text(encoding="utf-8"))
    conn=sqlite3.connect(f"file:{Path(database_path)}?mode=ro",uri=True)
    tickers=_universe(conn,asof); all_series,sources=_load(conn,asof); conn.close()
    series={ticker:all_series[ticker] for ticker in tickers if ticker in all_series}
    dataset_hash=sha256_file(database_path)
    decision_timestamp=decision_timestamp or dt.datetime.now(dt.timezone.utc).isoformat()
    decision=generate_decision(asof,execution_time,series,{},
        {"decision_timestamp":decision_timestamp,"code_commit":code_commit,
         "config_hash":selection["config_hash"],"dataset_hash":dataset_hash,
         "source_versions":sources,"development_backfill":bool(development_backfill),
         "prospective_evidence_eligible":False})
    ledger=connect(ledger_path)
    receipt=append_decision(ledger,decision,decision_timestamp=decision_timestamp,
        development_backfill=development_backfill,final_freeze_timestamp=final["finalized_at"],
        final_freeze_commit=final["final_freeze_commit"])
    ledger.close()
    artifact_name=f"{asof}_{decision['decision_payload_hash'][:16]}.json"
    path=write_artifact(Path(artifact_directory)/artifact_name,decision,stable_decision_receipt(receipt))
    return {"decision_artifact":str(path),"ledger_receipt":receipt,
            "shadow_implementation_status":"COMPLETE","shadow_runtime_status":"READY_NOT_SCHEDULED"}
