"""Signal-only materializer. This module cannot import outcome/evaluation code."""
from __future__ import annotations
import ast, bisect, math, statistics
from pathlib import Path
from common import DETECTORS, canonical_hash, next_session, rank_rows

FORBIDDEN = {"labels", "outcomes", "winner_labels", "future_returns", "winner_cards"}

def assert_outcome_firewall(paths):
    for path in paths:
        value = str(path).replace("\\", "/").lower()
        if any(token in value for token in FORBIDDEN):
            raise PermissionError(f"outcome artifact forbidden: {path}")

def assert_dependency_firewall(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        names = ([a.name for a in node.names] if isinstance(node, ast.Import) else
                 [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
        if any("outcome_stage" in n or "evaluation_stage" in n for n in names):
            raise AssertionError("post-freeze dependency")

def scale_invariant(function, values, scale=7.0):
    a = function(values); b = function([v * scale for v in values])
    return a is not None and b is not None and math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)

def _score(detector, closes, volumes):
    if detector == "MOMENTUM_12_1": return closes[-22] / closes[-253] - 1 if len(closes)>=253 else None
    if detector == "MOMENTUM_6_1": return closes[-22] / closes[-127] - 1 if len(closes)>=127 else None
    if detector == "REVERSAL_21": return closes[-1] / closes[-22] - 1 if len(closes)>=22 else None
    if detector == "LOW_VOL_252":
        if len(closes)<253: return None
        rets=[closes[i]/closes[i-1]-1 for i in range(len(closes)-252,len(closes))]
        return statistics.pstdev(rets)
    if detector == "52W_HIGH": return closes[-1]/max(closes[-253:]) if len(closes)>=253 else None
    if detector == "VOLUME_SURGE":
        if len(volumes)<252: return None
        long=sum(volumes[-252:])/252
        return sum(volumes[-21:])/21/long-1 if long>0 else None
    return None

def adjusted_until(dates, raw, adjustments, asof):
    values=list(raw)
    for ex_date, factor in adjustments:
        if ex_date <= asof:
            values=[v*factor if d < ex_date else v for d,v in zip(dates,values)]
    return values

def historical_universe(asof, sessions, series, quarantines, top_n=60, lookback=126, min_history=252):
    cut=bisect.bisect_left(sessions,asof)
    if cut<lookback: return []
    window=set(sessions[cut-lookback:cut]); start=sessions[cut-lookback]
    candidates=[]
    for ticker,data in series.items():
        dates=data["dates"]; end=bisect.bisect_left(dates,asof)
        if end<min_history or not dates or dates[end-1]<start: continue
        if any(day<asof and (resolved is None or resolved>=asof) for day,resolved in quarantines.get(ticker,())): continue
        vols=[v for d,v in zip(dates[:end],data["volumes"][:end]) if d in window]
        vols += [0.0]*(lookback-len(vols)); med=statistics.median(vols)
        candidates.append((ticker,med))
    best={}
    for ticker,med in sorted(candidates):
        root=ticker[:4]
        if root not in best or med>best[root][1]: best[root]=(ticker,med)
    return [x[0] for x in sorted(best.values(),key=lambda x:(-x[1],x[0]))[:top_n]]

def generate(series, adjustments, quarantines, sessions, asofs, metadata):
    output=[]
    for asof in asofs:
        universe=historical_universe(asof,sessions,series,quarantines)
        base={}
        for ticker in universe:
            data=series[ticker]; end=bisect.bisect_left(data["dates"],asof)
            dates=data["dates"][:end]; raw=data["closes"][:end]; volumes=data["volumes"][:end]
            closes=adjusted_until(dates,raw,adjustments.get(ticker,()),asof)
            base[ticker]=(closes,volumes)
        detector_scores={}
        for detector in DETECTORS:
            if detector=="MOMENTUM_LOW_VOL": continue
            detector_scores[detector]={t:_score(detector,*values) for t,values in base.items()}
        # Historical H8: top 40% momentum, then low-vol ranking; non-qualifiers are unscorable.
        mom=detector_scores["MOMENTUM_12_1"]; vol=detector_scores["LOW_VOL_252"]
        valid=sorted(((-v,t) for t,v in mom.items() if v is not None))
        gate={t for _,t in valid[:math.ceil(.4*len(valid))]}
        detector_scores["MOMENTUM_LOW_VOL"]={t:(-vol[t] if t in gate and vol[t] is not None else None) for t in universe}
        for detector,(direction,fidelity) in DETECTORS.items():
            rows=[]
            for ticker in universe:
                score=detector_scores[detector].get(ticker)
                row={"signal_asof":asof,"execution_time":next_session(asof,sessions),"ticker":ticker,
                    "detector_id":detector,"replay_fidelity":fidelity,
                    "historical_scientific_status":"HISTORICAL_JUDGED_MECHANISM",
                    "universe_eligible":True,"detector_scorable":score is not None,
                    "not_scorable_reason":"" if score is not None else "NOT_SCORABLE_INSUFFICIENT_HISTORY_OR_GATE",
                    "score":score,"input_hash":canonical_hash({"ticker":ticker,"asof":asof,"score":score}),
                    "config_hash":metadata["config_hash"],"code_commit":metadata["code_commit"],
                    "dataset_hash":metadata["dataset_hash"]}
                rows.append(row)
            output.extend(rank_rows(rows,direction))
    return sorted(output,key=lambda r:(r["detector_id"],r["signal_asof"],r["ticker"]))
