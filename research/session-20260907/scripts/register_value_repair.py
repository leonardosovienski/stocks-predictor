from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT=Path(__file__).resolve().parent.parent
REPO=ROOT/'work/stocks-predictor'
SOURCE=ROOT/'work/value-measurement-source'
targets=[('QUAL3','2019-08-08','2019-08-09'),('HGTX3','2021-04-23','2021-04-26'),
         ('AMER3','2023-01-11','2023-01-12'),('PETZ3','2024-04-18','2024-04-19'),
         ('HAPV3','2025-11-12','2025-11-13')]
required={(t,d) for t,prev,day in targets for d in (prev,day)}
required.update({('AMER3','2023-01-02'),('AMER3','2023-01-19'),('AMER3','2023-01-20'),('AMER3','2023-02-01'),('AMER3','2023-04-03')})
quotes={};rawlines=[]
manifest=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
for rawfile in SOURCE.glob('cash-equity-*.txt'):
    for raw in rawfile.read_bytes().splitlines():
        ticker=raw[12:24].strip().decode('ascii');ds=raw[2:10].decode('ascii');day=f'{ds[:4]}-{ds[4:6]}-{ds[6:]}'
        if (ticker,day) not in required:continue
        scale=int(raw[210:217]);quotes[ticker,day]={'open':int(raw[56:69])/100/scale,'close':int(raw[108:121])/100/scale,
                                                 'isin':raw[230:242].decode('ascii'),'raw_line_sha256':hashlib.sha256(raw).hexdigest()}
        rawlines.append(raw)
assert len(quotes)==len(required)
reviews=[]
for ticker,previous,day in targets:
    before,after=quotes[ticker,previous],quotes[ticker,day]
    assert before['isin']==after['isin']
    archive=f'COTAHIST_A{day[:4]}.ZIP'
    reviews.append({'ticker':ticker,'date':day,'previous_date':previous,'isin':after['isin'],
                    'previous_close':before['close'],'next_open':after['open'],'price_factor':1,
                    'decision':'Preserve confirmed primary-source market move, including losses, with an explicit quality note. This does not certify full corporate-action coverage.',
                    'source':f'https://bvmf.bmfbovespa.com.br/InstDados/SerHist/{archive}',
                    'archive_sha256':manifest['archive_sha256'][archive],
                    'previous_raw_line_sha256':before['raw_line_sha256'],'next_raw_line_sha256':after['raw_line_sha256']})
(SOURCE/'reviewed-jumps.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2),encoding='utf-8')
(REPO/'tests/fixtures/value-repair-quotes.txt').write_bytes(b'\n'.join(rawlines)+b'\n')
protocol={'protocol_id':'H18-H19-MEASUREMENT-REPAIR-1','registered_at_utc':datetime.now(timezone.utc).isoformat(),
          'phase':'DISCOVERY','first_outputs_already_observed':True,'repaired_cohort_metrics_observed_before_registration':False,
          'reason':'Source audit found BDI 08 held quotes omitted and two B3 bonuses double-counted as legacy splits; confirmed market jumps must not become missing losses or gains.',
          'fixed_trials':[{'family':f,'holding_months':h} for f,h in [('H18',1),('H18',3),('H19',1),('H19',3)]],
          'frozen':'Use exactly the original first-observation factor values, universe, selections, signal/entry/exit dates, costs, adverse missing scenario and decision rule. No re-ranking, new feature or variant.',
          'repairs':['Quote and identity extract from the same original B3 cash-market 010 archives, across BDI classifications, keeping existing 387101 quote values identical.',
                     'NATU3 2019-09-18 and PSSA3 2021-10-21: one original B3 100% bonus each; preserve legacy source in audit but do not apply it a second time.',
                     'Five exact primary-quote-confirmed price jumps accepted with quality notes; review includes positive and negative moves. Any unreviewed >30% move remains missing.'],
          'reviewed_moves':reviews,
          'unchanged_limits':['Merger/delisting/identity transitions and subscriptions without modeled terms remain unresolved.',
                              'Original feature coverage remains frozen, including historical exclusions induced by the earlier source-quality filter; this is measurement repair of that cohort, not a fully repaired new strategy.',
                              'No dividends/JCP/total return, executable sizing, taxes, cash-rate benchmark, untouched holdout or proof claim.'],
          'search_budget':{'nominal_configurations_minimum':20,'observed_return_evaluations_before_minimum':21,
                            'measurement_reevaluations':4,'observed_return_evaluations_after_minimum':25,'active_discovery_families':['H18','H19'],'proof_trials':0},
          'input_sha256':{}}
paths=[ROOT/'outputs/h18-h19-first-observation.json',SOURCE/'quotes.db',SOURCE/'events.json',SOURCE/'reviewed-jumps.json']
paths+=sorted((SOURCE/'identity').glob('identity-*.jsonl'))
for p in paths:
    with p.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
    protocol['input_sha256'][str(p.relative_to(ROOT)).replace('\\','/')]=sha
dest=REPO/'docs/research/2026-09-07-value-repair-protocol.json'
with dest.open('x',encoding='utf-8') as stream:json.dump(protocol,stream,ensure_ascii=False,indent=2)
sha=hashlib.sha256(json.dumps(protocol,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
module=REPO/'stocks_predictor/discovery_value_repair.py';source=module.read_text(encoding='utf-8');assert source.count('PENDING_REGISTRATION')==1
module.write_text(source.replace('PENDING_REGISTRATION',sha),encoding='utf-8')
print(sha)
