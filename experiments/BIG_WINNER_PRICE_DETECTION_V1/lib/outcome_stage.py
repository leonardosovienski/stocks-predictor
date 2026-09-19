"""Post-freeze price-only outcomes; cash distributions never enter the index."""
from __future__ import annotations
import bisect, csv
from pathlib import Path
from common import add_months
from freeze import verify_freeze

def load_frozen(path):
    manifest=verify_freeze(path); target=Path(path).parent/manifest["file"]
    rows=[]
    with target.open(newline="",encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for field in ("universe_eligible","detector_scorable","selected"):
                row[field]=row[field]=="true"
            for field in ("score","percentile"):
                row[field]=float(row[field]) if row[field] else None
            for field in ("rank","universe_size","scorable_size","selection_size"):
                row[field]=int(row[field]) if row[field] else None
            rows.append(row)
    return rows

def price_index(dates, closes, adjustments=(), bonuses=()):
    """PRICE_INDEX_EX_CASH_DISTRIBUTIONS: only share-count continuity events."""
    values=list(closes)
    for ex_date,factor in list(adjustments)+list(bonuses):
        if factor<=0: raise ValueError("invalid continuity factor")
        values=[v*factor if d<ex_date else v for d,v in zip(dates,values)]
    return values

def substitute_continuity(old_dates, old_levels, new_dates, new_levels, conversion_factor):
    """Join an evidenced successor chain without inventing an economic ratio."""
    if not old_dates or not new_dates or old_dates[-1] >= new_dates[0] or conversion_factor <= 0:
        raise ValueError("invalid identity continuation")
    return old_dates+new_dates, [v*conversion_factor for v in old_levels]+list(new_levels)

def terminal_session_status(sessions, last_quote, target, maximum_staleness=5):
    end=bisect.bisect_right(sessions,target)-1
    quote=bisect.bisect_right(sessions,last_quote)-1
    if end<0 or quote<0 or end-quote>maximum_staleness: return "TERMINAL_QUOTE_STALE"
    return "OK"

def calculate_outcome(execution, dates, levels, sessions, unresolved_events=(), terminal_event=None):
    target=add_months(execution,12); start=bisect.bisect_left(dates,execution)
    end=bisect.bisect_right(dates,target)-1
    if start>=len(dates) or dates[start]!=execution: return _unknown("MISSING_EXECUTION_PRICE")
    if end<=start: return _unknown("INCOMPLETE_HORIZON")
    if terminal_session_status(sessions,dates[end],target)!="OK": return _unknown("TERMINAL_QUOTE_STALE")
    if terminal_event and terminal_event not in {"SUCCESSOR_CONTINUITY_RECONSTRUCTED","TERMINAL_CASH_ECONOMICALLY_HANDLED"}:
        return _unknown("TERMINAL_CORPORATE_EVENT_UNRESOLVED")
    if any(execution<day<=target for day in unresolved_events): return _unknown("CORPORATE_ACTION_UNRESOLVED")
    base=levels[start]
    if base<=0: return _unknown("INVALID_EXECUTION_PRICE")
    path=levels[start:end+1]; returns=[v/base-1 for v in path]
    peak=max(path); peak_i=path.index(peak); terminal=path[-1]/base-1
    running=path[0]; drawdown=0.0
    for v in path:
        running=max(running,v); drawdown=min(drawdown,v/running-1)
    def crossing(level):
        return next((dates[start+i] for i,v in enumerate(returns) if v>=level),None)
    six=bisect.bisect_right(dates,add_months(execution,6))-1
    six_return=levels[six]/base-1 if six>start else None
    return {"outcome_estimable":True,"outcome_status":"ESTIMABLE",
        "horizon_target":target,"horizon_end":dates[end],"forward_price_return_12m":terminal,
        "execution_price":base,"peak_price":peak,
        "maximum_price_return_within_12m":max(returns),"time_to_10pct":crossing(.1),
        "time_to_20pct":crossing(.2),"time_to_30pct":crossing(.3),
        "time_to_peak":dates[start+peak_i],"maximum_drawdown_after_execution":drawdown,
        "BIG_WINNER_PRICE_12M":terminal>=.30,"BIG_WINNER_PRICE_6M_30":six_return>=.30 if six_return is not None else None,
        "BIG_WINNER_PRICE_12M_50":terminal>=.50,"BIG_WINNER_PRICE_12M_100":terminal>=1.0}

def _unknown(reason):
    return {"outcome_estimable":False,"outcome_status":reason,"BIG_WINNER_PRICE_12M":None}

def create_episodes(rows, negative_gap=1):
    episodes=[]; by={}
    for row in rows: by.setdefault(row["ticker"],[]).append(row)
    for ticker,items in sorted(by.items()):
        current=[]; negatives=0; boundary_unknown=False
        for row in sorted(items,key=lambda r:r["signal_asof"]):
            label=row.get("BIG_WINNER_PRICE_12M")
            if label is True:
                if current and negatives>=negative_gap:
                    episodes.append(_episode(ticker,current,len(episodes)+1,boundary_unknown)); current=[]; boundary_unknown=False
                current.append(row); negatives=0
            elif label is False and current:
                negatives+=1
            elif label is None and current:
                boundary_unknown=True  # unknown never closes an episode
        if current: episodes.append(_episode(ticker,current,len(episodes)+1,boundary_unknown))
    return episodes

def _episode(ticker,rows,ordinal,uncertain):
    return {"ticker":ticker,"episode_id":f"{ticker}-{ordinal:04d}",
        "episode_start":rows[0]["signal_asof"],"episode_end":rows[-1]["signal_asof"],
        "boundary_uncertain":uncertain}

def classify_episode(episode,signals,reference,peak,signal_value):
    relevant=[r for r in signals if r["ticker"]==episode["ticker"] and episode["episode_start"]<=r["signal_asof"]<=episode["episode_end"] and r["detector_scorable"]]
    if not relevant:return {**episode,"classification":"NOT_SCORABLE_BY_DETECTOR"}
    selected=sorted((r for r in relevant if r["selected"]),key=lambda r:r["signal_asof"])
    if not selected:return {**episode,"classification":"MISS"}
    if signal_value is None or peak<=reference:return {**episode,"classification":"PRECOCITY_NOT_ESTIMABLE"}
    remaining=(peak-signal_value)/(peak-reference)
    return {**episode,"first_qualified_signal":selected[0]["signal_asof"],
        "fraction_of_move_remaining":remaining,"classification":"EARLY_HIT" if remaining>=.5 else "LATE_HIT"}
