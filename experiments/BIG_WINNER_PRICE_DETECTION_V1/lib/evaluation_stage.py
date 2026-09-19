"""Confirmatory inference on frozen selections."""
from __future__ import annotations
import math, random, statistics
from common import partial_id

def metrics(rows):
    known=[r for r in rows if r.get("BIG_WINNER_PRICE_12M") is not None]
    selected=[r for r in known if r["selected"]]
    p=sum(r["BIG_WINNER_PRICE_12M"] for r in selected)/len(selected) if selected else None
    b=sum(r["BIG_WINNER_PRICE_12M"] for r in known)/len(known) if known else None
    return {"known_n":len(known),"selected_known_n":len(selected),"precision":p,"base_rate":b,
        "precision_minus_base_rate":p-b if p is not None and b is not None else None,
        "lift":p/b if p is not None and b else None,"partial_identification":partial_id([r for r in rows if r["selected"]],rows)}

def matched_random(rows,simulations=10_000,seed=20260919):
    groups={}
    for r in rows:
        if r.get("BIG_WINNER_PRICE_12M") is not None:
            groups.setdefault(r["signal_asof"],[]).append((bool(r["BIG_WINNER_PRICE_12M"]),bool(r["selected"])))
    # Collapse each monthly cross-section to a compact Bernoulli population.
    prepared=[]; total_winners=total_n=0
    for group in groups.values():
        labels=[winner for winner,_selected in group]; k=sum(selected for _winner,selected in group)
        prepared.append((labels,k)); total_winners+=sum(labels); total_n+=len(labels)
    rng=random.Random(seed); distribution=[]; base=total_winners/total_n if total_n else math.nan
    for _ in range(simulations):
        chosen_winners=chosen_n=0
        for labels,k in prepared:
            chosen_winners+=sum(rng.sample(labels,min(k,len(labels)))); chosen_n+=min(k,len(labels))
        distribution.append(chosen_winners/chosen_n-base if chosen_n else math.nan)
    return distribution

def empirical_p(observed,distribution):
    return (1+sum(v>=observed for v in distribution))/(1+len(distribution))

def moving_block(months,statistic,block_length=12,simulations=10_000,seed=20260921):
    if not months or block_length<1: raise ValueError("invalid bootstrap")
    rng=random.Random(seed); n=len(months); out=[]
    for _ in range(simulations):
        sample=[]
        while len(sample)<n:
            start=rng.randrange(n); sample.extend(months[(start+i)%n] for i in range(block_length))
        out.append(statistic(sample[:n]))
    return out

def percentile_interval(values):
    values=sorted(v for v in values if math.isfinite(v)); n=len(values)
    return [values[int(.025*(n-1))],values[int(.975*(n-1))]] if n else [None,None]

def holm(raw):
    ordered=sorted(raw.items(),key=lambda p:p[1]); out={}; running=0
    for i,(name,p) in enumerate(ordered):
        running=max(running,min(1,(len(ordered)-i)*p)); out[name]=running
    return out

def negative_permutation(rows,seed=20260920):
    rng=random.Random(seed); copy=[dict(r) for r in rows]; groups={}
    for r in copy: groups.setdefault(r["signal_asof"],[]).append(r)
    for group in groups.values():
        flags=[r["selected"] for r in group]; rng.shuffle(flags)
        for r,f in zip(group,flags):r["selected"]=f
    return metrics(copy)["precision_minus_base_rate"]

def positive_leakage_control(rows):
    known=[dict(r,selected=bool(r.get("BIG_WINNER_PRICE_12M"))) for r in rows if r.get("BIG_WINNER_PRICE_12M") is not None]
    return metrics(known)["precision_minus_base_rate"]>0
