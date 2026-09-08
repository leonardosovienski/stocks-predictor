"""Offline readiness audit and actual-source first-entry accounting smoke test.

Exit 2 means required evidence is incomplete, not a Python/runtime failure.
No strategy return is calculated by this program.
"""
import argparse
from bisect import bisect_right
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from retail_cash import RetailBook, execution_readiness, integer_targets

BASE = Path(__file__).resolve().parent
def read(name): return json.loads((BASE/'inputs'/name).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def verify_payload():
    manifest=BASE/'SHA256.json'
    if not manifest.exists(): raise ValueError('Missing package manifest')
    rows=json.loads(manifest.read_text(encoding='utf-8'))
    for name, digest in rows.items():
        path=(BASE/name).resolve()
        if not path.is_relative_to(BASE) or sha(path)!=digest:
            raise ValueError(f'Changed or invalid input: {name}')
    return len(rows)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('H19_CAIXA_EXECUCAO.json'))
    args=parser.parse_args()
    verified=verify_payload()
    protocol=read('protocol.json')
    assert sha(BASE/'inputs/observation.json')==protocol['source_observation_sha256']
    trial=next(t for t in read('observation.json')['trials'] if t['family']=='H19' and t['holding_months']==3)
    periods=[p for p in trial['periods'] if any(m['selected'] for m in p['members'])]
    terms=read('reorganizations.json')['events']
    stocks=read('stock-events.json')['events']
    intervals=set(); selected_intervals=set(); action_gaps=[]; seen_actions={}
    for period in periods:
        for member in period['members']:
            pending=[(member['ticker'],member['isin'],period['entry'])]
            seen=set()
            while pending:
                ticker, isin, start=pending.pop()
                if (ticker,isin,start) in seen: raise ValueError('Cyclic successor terms')
                seen.add((ticker,isin,start))
                actions=[e for e in terms if e['ticker']==ticker and e['isin']==isin and start < e['ex_date'] <= period['exit']]
                finish=min((e['ex_date'] for e in actions if e['removes_original']),default=period['exit'])
                interval=(ticker,isin,start,finish)
                intervals.add(interval)
                if member['selected']: selected_intervals.add(interval)
                for event in actions:
                    identity=(ticker,isin,event['ex_date'])
                    if identity not in seen_actions:
                        gap=dict(kind='CORPORATE_TAX_AND_DELIVERY',ticker=ticker,isin=isin,
                            ex_date=event['ex_date'], selected=member['selected'],
                            missing=['reviewed fiscal basis/disposal treatment',
                                     'integer delivery and fractional-entitlement settlement'],
                            missing_stock_credit_dates=[s['ticker'] for s in event['stocks'] if not s.get('credit_date')])
                        seen_actions[identity]=gap
                        action_gaps.append(gap)
                    else:
                        seen_actions[identity]['selected'] |= member['selected']
                    for leg in event['stocks']:
                        pending.append((leg['ticker'],leg['isin'],event['ex_date']))
    for event in stocks:
        if any(event['ticker']==t and event['isin']==i and a < event['ex_date'] <= b for t,i,a,b in intervals):
            if event['label'] in {'DESDOBRAMENTO','GRUPAMENTO','BONIFICACAO'}:
                action_gaps.append(dict(kind='ORDINARY_STOCK_ACTION_DELIVERY_AND_BASIS',ticker=event['ticker'],
                    ex_date=event['ex_date'],label=event['label'],
                    reason='Price factor is not reviewed integer delivery/fraction/cost-basis evidence.'))
    registry=read('reviewed-payment-dates.json')
    sessions=read('sessions.json')
    cash_rows=[]
    schedule_rows=[]; covered_cash_keys=set()
    for schedule in registry.get('installment_schedule_reviews',[]):
        raw_group=[r for r in registry['cash_queue'] if r['ticker']==schedule['ticker']
                   and r['isin']==schedule['isin'] and r['ex_date']==schedule['ex_date']
                   and r['action']==schedule['action']]
        assert len(raw_group)==len(schedule['installments'])
        total=sum(Decimal(r['value_per_share']) for r in raw_group)
        assert total==Decimal(schedule['declared_total_per_share'])
        assert total==sum(Decimal(r['gross_per_share']) for r in schedule['installments'])
        # Replace the whole economic group, without inventing a relation between
        # the arbitrary B3 row ordering and installment number.
        for raw in raw_group:covered_cash_keys.add((raw['isin'],raw['ex_date'],raw['action'],raw['source_row']))
        for installment in schedule['installments']:
            pay=installment['payment_date']; index=bisect_right(sessions,pay)
            schedule_rows.append(dict(event_id=f"{schedule['isin']}:{schedule['ex_date']}:installment:{installment['number']}",
                ticker=schedule['ticker'],isin=schedule['isin'],ex_date=schedule['ex_date'],payment_date=pay,
                available_on=sessions[index] if index<len(sessions) else None,net_per_share=None,tax_source=None,
                source_review=False,sources=[{'file':schedule['source_file'],'sha256':schedule['source_sha256']}]))
    for row in registry['cash_queue']:
        if (row['isin'],row['ex_date'],row['action'],row['source_row']) in covered_cash_keys:continue
        fact=row['reviewed_payment']; pay=fact['payment_date'] if fact else None
        index=bisect_right(sessions,pay) if pay else len(sessions)
        cash_rows.append(dict(event_id=f"{row['isin']}:{row['ex_date']}:{row['action']}:{row['source_row']}",
            ticker=row['ticker'],isin=row['isin'],ex_date=row['ex_date'],payment_date=pay,
            available_on=sessions[index] if index<len(sessions) else None,
            net_per_share=fact.get('net_per_share_reported') if fact and fact.get('net_amount_reviewed') else None,
            tax_source=fact['sources'] if fact and fact.get('net_amount_reviewed') else None,
            source_review=bool(fact and fact.get('net_amount_reviewed')),
            sources=fact['sources'] if fact else [],
            reason='Payment-date review alone is not complete net-cash evidence.'))
    cash_rows.extend(schedule_rows)
    pilot=read('prior-pilot.json')
    action_gaps.append(dict(kind='JBS_HISTORY_TRUNCATED',missing_declared_events=len(pilot['jbs_missing_later_declared_events']),
        affected_quarter_cells=len(pilot['jbs_affected_h19_quarter_cells']),
        reason='Later JBS declarations and successor ordinary cash are not in the original 778-row queue.'))
    checks={
        'quotes':dict(verified=False,sources=['fractional-audit.json'],
                      reason='Endpoint audit exists; every continuous rebalance/action execution is not yet assembled.'),
        'corporate_actions':dict(verified=False,sources=['reorganizations.json','stock-events.json']),
        'tax_schedule':dict(verified=False,sources=[],reason='Monthly tax kernel is tested; dated tax payments, withholding credits and corporate treatments remain absent.'),
        'cash_coverage_inventory':dict(verified=False,sources=['reviewed-payment-dates.json','prior-pilot.json'])}
    gate=execution_readiness(sorted(intervals),[],cash_rows,action_gaps,checks)
    assert not gate['ready'] and gate['profit'] is None
    # First entry is independently meaningful without future cash data: initial
    # money and ex-ante target quantities only. It is not a partial P&L backtest.
    fixture=read('entry-fixture.json')
    first=periods[0]
    assert fixture['asof']==first['asof'] and fixture['entry']==first['entry']
    assert {m['ticker'] for m in fixture['members']}=={m['ticker'] for m in first['members'] if m['selected']}
    for member in fixture['members']:
        a,b,c=member['raw_records']
        for raw,ticker,day,market in [(a,member['ticker'],fixture['asof'],'010'),
            (b,member['ticker'],fixture['entry'],'010'),(c,member['ticker']+'F',fixture['entry'],'020')]:
            assert raw[:2]=='01' and raw[12:24].strip()==ticker and raw[2:10]==day.replace('-','')
            assert raw[230:242]==member['isin'] and raw[24:27]==market
        assert Decimal(member['signal_close'])==Decimal(a[108:121])/(100*int(a[210:217]))
        assert Decimal(member['quote']['standard'])==Decimal(b[56:69])/(100*int(b[210:217]))
        assert Decimal(member['quote']['fractional'])==Decimal(c[56:69])/(100*int(c[210:217]))
    smoke=[]
    for capital in protocol['capital_brl']:
        for fee in protocol['one_way_cost_rates']:
            book=RetailBook(capital,fixture['entry'])
            targets=integer_targets(capital,{m['ticker']:m['signal_close'] for m in fixture['members']})
            rows=book.rebalance(targets,{m['ticker']:m['quote'] for m in fixture['members']},
                {m['ticker']:{'isin':m['isin'],'lot':100,'tax_class':'equity'} for m in fixture['members']},
                fixture['asof'],fixture['settlement'],fee)
            total_cost=sum(r['costs'] for r in rows)
            gross=sum(r['gross'] for r in rows)
            book.advance(fixture['settlement'])
            assert book.cash>=0 and book.cash+gross+total_cost==Decimal(capital)
            smoke.append(dict(capital_brl=capital,one_way_cost_rate=fee,entry_date=fixture['entry'],
                settlement_date=fixture['settlement'],target_quantities=targets,trades=rows,
                shares={t:h.quantity for t,h in sorted(book.positions.items())},
                gross_purchase_brl=gross,assumed_cost_brl=total_cost,settled_cash_brl=book.cash,
                status='PASS_ACCOUNTING_ONLY',profit=None))
    result=dict(status='BLOCKED_MISSING_EVIDENCE',full_history_executed=False,profit=None,
        protocol=protocol['protocol'],verified_package_files=verified,
        required_cash_intervals=len(intervals),selected_required_intervals=len(selected_intervals),
        supplied_verified_complete_intervals=0,original_queue_summary=registry['summary'],
        original_queue_excludes_later_jbs_and_successor_cash=True,
        normalized_source_installments=len(schedule_rows),
        issue_counts=dict(Counter(r['kind'] for r in gate['issues'])),execution_checks=checks,
        first_entry_smoke=smoke,issues=gate['issues'],new_historical_return_evaluations=0,
        limitations=['First-entry quotes describe a historical fill model, not guaranteed achievable fills.',
                     'No continuous strategy/benchmark or after-tax wealth result has been produced.',
                     'No absent distribution or corporate action was silently treated as zero.'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('status','full_history_executed','profit','required_cash_intervals','selected_required_intervals','issue_counts')},indent=2))
    print('First-entry accounting checks:',len(smoke),'PASS; output:',args.output.resolve())
    return 2

if __name__=='__main__':
    raise SystemExit(main())
