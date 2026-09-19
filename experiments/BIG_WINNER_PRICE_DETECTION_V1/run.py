"""Reproduce BIG_WINNER_PRICE_DETECTION_V1 in its mandatory stage order."""
from __future__ import annotations
import argparse, bisect, csv, json, sqlite3, subprocess, sys
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
LIB=ROOT/"lib"; sys.path.insert(0,str(LIB))
from common import DETECTORS, add_months, canonical_hash, sha256_file
import evaluation_stage as evaluation
import freeze, outcome_stage, signal_stage

DEFAULT_DB=Path(r"C:\STOCKS\data\recovery-r2\objects\a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4")

def dump_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")

def source_commit():
    return subprocess.check_output(["git","rev-parse","HEAD"],cwd=REPO,text=True).strip()

def load_market(db):
    conn=sqlite3.connect(f"file:{db}?mode=ro",uri=True)
    series=defaultdict(lambda:{"dates":[],"closes":[],"opens":[],"volumes":[]})
    sessions=[]; seen=set()
    for day,ticker,op,close,volume,factor in conn.execute(
        "select date,ticker,open,close,volume_fin,quote_factor from prices_raw where market_type='010' order by date,ticker"):
        if day not in seen: sessions.append(day); seen.add(day)
        data=series[ticker]; data["dates"].append(day); data["opens"].append(op/factor)
        data["closes"].append(close/factor); data["volumes"].append(volume)
    adjustments=defaultdict(list)
    for ticker,day,factor in conn.execute("select ticker,ex_date,factor from adjustments where approved_by is not null and type in ('split','grupamento') order by ticker,ex_date"):
        adjustments[ticker].append((day,factor))
    quarantines=defaultdict(list)
    for ticker,day,resolved in conn.execute("select ticker,date,resolved_at from quarantine order by ticker,date"):
        quarantines[ticker].append((day,resolved[:10] if resolved else None))
    conn.close(); return dict(series),dict(adjustments),dict(quarantines),sessions

def month_ends(sessions):
    return [day for i,day in enumerate(sessions) if i==len(sessions)-1 or sessions[i+1][:7]!=day[:7]]

def signal_command(db):
    if (ROOT/"frozen_signals").exists() and any((ROOT/"frozen_signals").iterdir()):
        raise FileExistsError("one-time signal freeze already exists")
    series,adjustments,quarantines,sessions=load_market(db)
    ends=month_ends(sessions)
    asofs=[d for d in ends if d>="2017-01-01" and d<sessions[-1] and add_months(signal_stage.next_session(d,sessions),12)<=sessions[-1]]
    metadata={"code_commit":source_commit(),"config_hash":canonical_hash({"detectors":DETECTORS,"top_n":60,"top20":"ceil","execution":"next-open"}),"dataset_hash":sha256_file(db)}
    signal_stage.assert_dependency_firewall(LIB/"signal_stage.py")
    rows=signal_stage.generate(series,adjustments,quarantines,sessions,asofs,metadata)
    manifest=freeze.freeze_rows(rows,ROOT/"frozen_signals",{"code_commit":metadata["code_commit"],"config_hash":metadata["config_hash"],"dataset_hashes":{"market_db":metadata["dataset_hash"]}})
    freeze.verify_freeze(manifest)
    dump_json(ROOT/"audit"/"signal_generation_receipt.json",{"asofs":len(asofs),"rows":len(rows),"detectors":list(DETECTORS),"freeze":str(manifest),"FREEZE_VALID":True})

def outcome_command(db):
    frozen=outcome_stage.load_frozen(ROOT/"frozen_signals"/"MANIFEST.json")
    series,adjustments,quarantines,sessions=load_market(db)
    cache={}
    for ticker,data in series.items():
        cache[ticker]=outcome_stage.price_index(data["dates"],data["closes"],adjustments.get(ticker,()))
    rows=[]
    for signal in frozen:
        data=series[signal["ticker"]]; unresolved=[d for d,_ in quarantines.get(signal["ticker"],())]
        outcome=outcome_stage.calculate_outcome(signal["execution_time"],data["dates"],cache[signal["ticker"]],sessions,unresolved)
        rows.append({**signal,**outcome})
    fields=sorted({key for row in rows for key in row})
    target=ROOT/"labels"/"price_outcomes.csv"; target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader()
        for row in rows: writer.writerow({k:"" if v is None else "true" if v is True else "false" if v is False else v for k,v in row.items()})
    dump_json(ROOT/"labels"/"MANIFEST.json",{"file":target.name,"sha256":sha256_file(target),"row_count":len(rows),"signal_manifest_sha256":sha256_file(ROOT/"frozen_signals"/"MANIFEST.json")})

def load_labels():
    with (ROOT/"labels"/"price_outcomes.csv").open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    for r in rows:
        for field in ("universe_eligible","detector_scorable","selected","outcome_estimable","BIG_WINNER_PRICE_12M"):
            r[field]=None if r.get(field,"")=="" else r[field]=="true"
        for field in ("score","forward_price_return_12m","maximum_price_return_within_12m","execution_price","peak_price"):
            r[field]=float(r[field]) if r.get(field) else None
        for field in ("rank","selection_size"):
            r[field]=int(r[field]) if r.get(field) else None
    return rows

def _block_stat(months):
    sk=sn=wk=wn=0
    for a,b,c,d in months: sk+=a; sn+=b; wk+=c; wn+=d
    return sk/sn-wk/wn if sn and wn else float("nan")

def evaluate_command():
    rows=load_labels(); by_detector={d:[r for r in rows if r["detector_id"]==d and r["detector_scorable"]] for d in DETECTORS}
    unique={}
    for r in rows: unique.setdefault((r["signal_asof"],r["ticker"]),r)
    episodes=outcome_stage.create_episodes(list(unique.values()))
    raw={}; scorecards={}
    for detector,items in by_detector.items():
        main=evaluation.metrics(items); observed=main["precision_minus_base_rate"]
        random_dist=evaluation.matched_random(items); raw[detector]=evaluation.empirical_p(observed,random_dist) if observed is not None else 1.0
        groups=defaultdict(list)
        for r in items: groups[r["signal_asof"]].append(r)
        monthly=[]
        for month in sorted(groups):
            known=[r for r in groups[month] if r["BIG_WINNER_PRICE_12M"] is not None]
            selected=[r for r in known if r["selected"]]
            monthly.append((sum(bool(r["BIG_WINNER_PRICE_12M"]) for r in selected),len(selected),sum(bool(r["BIG_WINNER_PRICE_12M"]) for r in known),len(known)))
        ci=evaluation.percentile_interval(evaluation.moving_block(monthly,_block_stat))
        tail_asofs=sorted(groups)[-24:]; tail=evaluation.metrics([r for r in items if r["signal_asof"] in tail_asofs])
        full=evaluation.metrics(items)
        episode_results=[]
        for episode in episodes:
            if episode["boundary_uncertain"]:
                episode_results.append({**episode,"classification":"BOUNDARY_UNCERTAIN_EXCLUDED"}); continue
            start=unique.get((episode["episode_start"],episode["ticker"]))
            relevant=[r for r in items if r["ticker"]==episode["ticker"] and episode["episode_start"]<=r["signal_asof"]<=episode["episode_end"] and r["selected"]]
            signal_value=relevant[0].get("execution_price") if relevant else None
            episode_results.append(outcome_stage.classify_episode(episode,items,start.get("execution_price") if start else None,start.get("peak_price") if start else None,signal_value))
        counts={name:sum(r["classification"]==name for r in episode_results) for name in ("EARLY_HIT","LATE_HIT","MISS","NOT_SCORABLE_BY_DETECTOR","PRECOCITY_NOT_ESTIMABLE","BOUNDARY_UNCERTAIN_EXCLUDED")}
        scorable=counts["EARLY_HIT"]+counts["LATE_HIT"]+counts["MISS"]+counts["PRECOCITY_NOT_ESTIMABLE"]
        detected=counts["EARLY_HIT"]+counts["LATE_HIT"]+counts["PRECOCITY_NOT_ESTIMABLE"]
        episode_summary={"winner_episodes":len(episodes),"scorable_episodes":scorable,"boundary_uncertain":counts["BOUNDARY_UNCERTAIN_EXCLUDED"],"detected":detected,"early_hits":counts["EARLY_HIT"],"late_hits":counts["LATE_HIT"],"misses":counts["MISS"],"episode_recall":detected/scorable if scorable else None,"early_hit_recall":counts["EARLY_HIT"]/scorable if scorable else None}
        scorecards[detector]={"detector":detector,"historical_scientific_status":"HISTORICAL_JUDGED_MECHANISM",
            "replay_fidelity":DETECTORS[detector][1],"evaluation_period":[min(r["signal_asof"] for r in items),max(r["signal_asof"] for r in items)],
            "scorable_observations":len(items),"selected_observations":sum(r["selected"] for r in items),
            "outcome_coverage":sum(r["BIG_WINNER_PRICE_12M"] is not None for r in items)/len(items),
            "FULL_HISTORY":full,"HISTORICAL_MAIN_BLOCK":main,"CONFIRMATORY_TAIL":tail,
            "WINNER_EPISODES":episode_summary,
            "temporal_95_ci":ci,"matched_random_mean":sum(random_dist)/len(random_dist),
            "observed_test_statistic":observed,"raw_empirical_p":raw[detector],
            "negative_control":evaluation.negative_permutation(items),"positive_leakage_control_pass":evaluation.positive_leakage_control(items)}
    adjusted=evaluation.holm(raw)
    for detector,card in scorecards.items():
        card["holm_adjusted_p"]=adjusted[detector]
        effect=card["observed_test_statistic"]; ci=card["temporal_95_ci"]; tail=card["CONFIRMATORY_TAIL"]["precision_minus_base_rate"]
        if effect is None: verdict="INCONCLUSIVE_DATA_QUALITY"
        elif adjusted[detector]<=.05 and effect>0 and ci[0] is not None and ci[0]>0 and tail is not None and tail>0: verdict="PRICE_DETECTION_SIGNAL_PRESENT"
        elif effect>0 and raw[detector]<=.10: verdict="WEAK_PRICE_DETECTION_SIGNAL"
        else: verdict="NO_EVIDENCE_OF_PRICE_DETECTION"
        card["scientific_verdict"]=verdict
        dump_json(ROOT/"metrics"/"cross_sectional"/f"{detector}.json",card)
        dump_json(ROOT/"metrics"/"episode_detection"/f"{detector}.json",{"summary":episode_summary,"episodes":episode_results})
        dump_json(ROOT/"metrics"/"temporal_blocks"/f"{detector}.json",{"block_length":12,"simulations":10000,"percentile_95_ci":ci})
        dump_json(ROOT/"metrics"/"confirmatory_tail"/f"{detector}.json",{"asofs":tail_asofs,"metrics":tail})
        dump_json(ROOT/"metrics"/"partial_identification"/f"{detector}.json",main["partial_identification"])
        dump_json(ROOT/"winner_cards"/f"{detector}.json",[r for r in episode_results if r["classification"] in {"EARLY_HIT","LATE_HIT"}])
        dump_json(ROOT/"miss_analysis"/f"{detector}.json",[r for r in episode_results if r["classification"] in {"MISS","NOT_SCORABLE_BY_DETECTOR","BOUNDARY_UNCERTAIN_EXCLUDED"}])
        dump_json(ROOT/"baselines"/"matched_random_complete_case"/f"{detector}.json",{"simulations":10000,"mean_statistic":card["matched_random_mean"],"raw_p":raw[detector]})
        dump_json(ROOT/"baselines"/"matched_random_partial_id"/f"{detector}.json",card["HISTORICAL_MAIN_BLOCK"]["partial_identification"])
    common_keys=None
    for items in by_detector.values():
        keys={(r["signal_asof"],r["ticker"]) for r in items}; common_keys=keys if common_keys is None else common_keys&keys
    common={d:evaluation.metrics([r for r in items if (r["signal_asof"],r["ticker"]) in common_keys]) for d,items in by_detector.items()}
    dump_json(ROOT/"metrics"/"cross_sectional"/"common_scorable_population.json",{"population_n":len(common_keys),"detectors":common})
    dump_json(ROOT/"controls"/"positive_leakage_control"/"result.json",{"PASS":all(c["positive_leakage_control_pass"] for c in scorecards.values())})
    dump_json(ROOT/"baselines"/"negative_control"/"result.json",{d:c["negative_control"] for d,c in scorecards.items()})
    dump_json(ROOT/"baselines"/"simple_baselines"/"result.json",{d:{"base_rate":c["HISTORICAL_MAIN_BLOCK"]["base_rate"]} for d,c in scorecards.items()})
    dump_json(ROOT/"FINAL_SCORECARD.json",{"experiment":"BIG_WINNER_PRICE_DETECTION_V1","system_level":{"status":"NOT_DEFINED","reason":"No pre-existing deterministic PIT system-level aggregation rule existed."},"detectors":scorecards,"common_scorable_population":common,"methods":{"random_simulations":10000,"bootstrap_simulations":10000,"block_length":12,"multiple_testing":"HOLM_FWER","alpha":.05}})

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("stage",choices=["signals","outcomes","evaluate"]); parser.add_argument("--db",type=Path,default=DEFAULT_DB); args=parser.parse_args()
    {"signals":signal_command,"outcomes":outcome_command,"evaluate":lambda _db:evaluate_command()}[args.stage](args.db)
if __name__=="__main__":main()
