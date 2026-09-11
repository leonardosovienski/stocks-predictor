"""Independent stdlib research implementations of documented mathematical concepts.

Provenance: Qlib/scikit-learn fit-transform; Qlib/Alphalens date IC;
Zipline group demean; Cvxportfolio participation/turnover constraint equations.
No external implementation copied; no market data, IO, or package runtime imports.
Inputs use ordered integer timestamps in these prototypes. See SOURCE_REVIEW.md.
"""
from dataclasses import dataclass
from math import isfinite, sqrt, fsum
from statistics import mean

def number(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and isfinite(x)

@dataclass(frozen=True)
class FittedNormalizer:
    start:int
    end:int
    decision:int
    center:float
    scale:float
    n:int

    def transform(self,values):
        return [None if not number(x) else (x-self.center)/self.scale for x in values]

def fit_normalizer(rows,start,end,decision):
    if not start<end<=decision:raise ValueError('fit window crosses decision')
    selected=[r for r in rows if start<=r['time']<end]
    if any(r.get('known_at') is None or r['known_at']>=decision for r in selected):raise ValueError('unavailable training observation')
    values=[r['value'] for r in selected]
    if len(values)<2 or not all(map(number,values)):raise ValueError('insufficient/invalid training values')
    center=mean(values);scale=sqrt(fsum((x-center)**2 for x in values)/len(values))
    if scale==0:raise ValueError('constant feature; explicit exclusion required')
    return FittedNormalizer(start,end,decision,center,scale,len(values))

def ranks(values):
    if not all(map(number,values)):raise ValueError('nonfinite rank input')
    out=[0.0]*len(values);order=sorted(range(len(values)),key=values.__getitem__);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and values[order[j]]==values[order[i]]:j+=1
        for k in order[i:j]:out[k]=(i+1+j)/2
        i=j
    return out

def rank_ic(scores,labels):
    if len(scores)!=len(labels):raise ValueError('unaligned pairs')
    if len(scores)<3:return None
    a,b=ranks(scores),ranks(labels);ma,mb=mean(a),mean(b)
    va=fsum((x-ma)**2 for x in a);vb=fsum((y-mb)**2 for y in b)
    if va==0 or vb==0:return None
    return fsum((x-ma)*(y-mb) for x,y in zip(a,b))/sqrt(va*vb)

def ranking_report(rows,quantile=.25):
    if not 0<quantile<=.5:raise ValueError('invalid quantile')
    dates={};seen=set()
    for r in rows:
        key=(r['date'],r['asset'])
        if key in seen:raise ValueError('duplicate asset-date')
        seen.add(key);dates.setdefault(r['date'],[]).append(r)
    report=[]
    for day,group in sorted(dates.items()):
        eligible=[r for r in group if number(r['score'])]
        ranked=sorted(eligible,key=lambda r:(r['score'],r['asset']))
        k=max(1,int(len(ranked)*quantile)) if ranked else 0
        top=ranked[-k:] if k else [];bottom=ranked[:k]
        paired=[r for r in eligible if number(r.get('label'))]
        # Labels never determine portfolio membership. Unknown selected outcomes invalidate spread.
        spread=mean([r['label'] for r in top])-mean([r['label'] for r in bottom]) if top and all(number(r.get('label')) for r in top+bottom) else None
        report.append({'date':day,'eligible':len(eligible),'observed_pairs':len(paired),'missing_labels':len(eligible)-len(paired),'rank_ic':rank_ic([r['score'] for r in paired],[r['label'] for r in paired]),'top':[r['asset'] for r in top],'bottom':[r['asset'] for r in bottom],'spread':spread,'tie_policy':'average ranks for IC; asset ID for quantile membership','ic_scope':'observed pairs; completeness reported, not universe-certified'})
    valid=[r['rank_ic'] for r in report if r['rank_ic'] is not None]
    return {'dates':report,'mean_date_ic':mean(valid) if valid else None,'valid_dates':len(valid),'total_dates':len(report),'inference':'NONE'}

def group_residual(scores,groups,decision,min_group=2):
    collected={}
    for asset,x in scores.items():
        g=groups.get(asset)
        if not number(x) or not g or g.get('known_at') is None or g['known_at']>=decision:raise ValueError('unknown/late group or score')
        collected.setdefault(g['group'],[]).append((asset,x))
    if any(len(v)<min_group for v in collected.values()):raise ValueError('undersized group')
    out={};offsets={}
    for g,entries in collected.items():
        m=mean([x for _,x in entries]);offsets[g]=m
        for asset,x in entries:out[asset]=x-m
    return {'residual':out,'group_means':offsets,'scope':'group demean of score; does not imply neutral portfolio exposure'}

def participation_screen(notional,volume_rows,decision,window=3,max_fraction=.01):
    if not number(notional) or notional<0 or window<1 or not 0<max_fraction<=1:raise ValueError('invalid order/parameters')
    past=[r for r in volume_rows if r['time']<decision and r.get('known_at') is not None and r['known_at']<decision]
    if len({r['time'] for r in past})!=len(past):return {'eligible':False,'reason':'DUPLICATE_VOLUME','participation':None}
    past=sorted(past,key=lambda r:r['time'])[-window:]
    if len(past)<window:return {'eligible':False,'reason':'INSUFFICIENT_AVAILABLE_VOLUME','participation':None}
    if any(not number(r.get('volume_brl')) or r['volume_brl']<=0 for r in past):return {'eligible':False,'reason':'INVALID_VOLUME','participation':None}
    forecast=mean([r['volume_brl'] for r in past]);share=notional/forecast
    return {'eligible':share<=max_fraction,'reason':'OK' if share<=max_fraction else 'PARTICIPATION_LIMIT','participation':share,'volume_forecast_brl':forecast,'assumption':'arithmetic average of supplied lagged observations; no guarantee of next-session liquidity'}

def turnover(old,new):
    return .5*fsum(abs(new.get(k,0)-old.get(k,0)) for k in old.keys()|new.keys() if k!='CASH')

def bounded_rebalance(old,target,budget=.1,fee=.002,max_weight=.5):
    if not number(budget) or budget<0 or not number(fee) or fee<0:raise ValueError('invalid budget/cost')
    for w in [old,target]:
        if not all(number(x) and x>=0 for x in w.values()) or abs(fsum(w.values())-1)>1e-10:raise ValueError('weights must be nonnegative and sum1 including CASH')
        if any(x>max_weight+1e-12 for k,x in w.items() if k!='CASH'):raise ValueError('concentration requires separate feasible transition')
    full=turnover(old,target);alpha=1 if full==0 else min(1,budget/full)
    post={k:old.get(k,0)+alpha*(target.get(k,0)-old.get(k,0)) for k in old.keys()|target.keys()}
    traded=2*turnover(old,post);cost=fee*traded;cash=post.get('CASH',0)-cost
    if cash < -1e-12:raise ValueError('insufficient fee reserve; do not finance from receivables')
    return {'pre_fee_weights':post,'turnover':traded/2,'traded_notional_fraction':traded,'cost_fraction_initial_nav':cost,'cash_fraction_initial_nav_after_fee':cash,'nav_fraction_after_fee':1-cost,'target_completion':alpha,'scope':'feasible radial interpolation, NOT objective-optimal portfolio; caps measured vs pretrade NAV'}
