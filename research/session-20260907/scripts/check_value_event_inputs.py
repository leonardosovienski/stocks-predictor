from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent/'stocks-predictor'))
from stocks_predictor.discovery_reorganizations import merged_market,validate_terms
from stocks_predictor.discovery_h17 import identity_at
BASE=Path(__file__).resolve().parent
terms=json.loads((BASE/'value-event-terms/reorganizations.json').read_text(encoding='utf-8'))
validate_terms(terms)
bars,ids=merged_market(BASE/'value-measurement-source/quotes.db',BASE/'value-measurement-source/identity',BASE/'value-successor-source/successors.db',BASE/'value-successor-source/identity')
panel=json.loads((BASE/'value-measurement-source/events.json').read_text(encoding='utf-8'))
for event in terms['events']:
    matches=identity_at(ids,event['ticker'],event['last_cum'])
    print(event['ticker'],'old identity',matches,'expected',event['isin'],'match',matches==event['isin'])
    for stock in event['stocks']:
        print(' successor',stock['ticker'],identity_at(ids,stock['ticker'],event['ex_date']),stock['isin'])
    print(' panel',[(e['label'],e['price_factor']) for e in panel['events'] if e['ticker']==event['ticker'] and e['ex_date']==event['ex_date']])
    print(' legacy',[(e['type'],e['factor']) for e in panel['legacy_adjustments'] if e['ticker']==event['ticker'] and e['ex_date']==event['ex_date']])
# Small golden source fixture: complete real raw quotes over three actual intervals.
windows={'GNDI3':('2022-02-01','2022-02-11'),'HAPV3':('2022-02-14','2022-03-02'),
         'SOMA3':('2024-07-01','2024-07-31'),'AZZA3':('2024-08-01','2024-09-02'),
         'CRFB3':('2025-04-01','2025-05-30'),'NTCO3':('2025-07-01','2025-07-01'),
         'NATU3':('2025-07-02','2025-08-01')}
selected={t:{d:q for d,q in bars[t].items() if a<=d<=b} for t,(a,b) in windows.items()}
fixture={'bars':selected,'identities':{t:ids[t] for t in windows},
         'events':[e for e in terms['events'] if e['ticker'] in windows], 'subscriptions':[],
         'raw_archive_provenance':'COTAHIST_A2022/2024/2025.ZIP; exact source records in adjacent golden file.'}
target=BASE/'stocks-predictor/tests/fixtures/reorganization_source_cases.json'
target.write_text(json.dumps(fixture,ensure_ascii=False,indent=2),encoding='utf-8')
rawtarget=target.with_suffix('.txt')
written=set()
with rawtarget.open('wb') as output:
    for folder,pattern in [(BASE/'value-measurement-source','cash-equity-*.txt'),(BASE/'value-successor-source','successors-*.txt')]:
        for file in folder.glob(pattern):
            with file.open('rb') as stream:
                for raw in stream:
                    ticker=raw[12:24].strip().decode('ascii')
                    if ticker not in windows: continue
                    ds=raw[2:10].decode('ascii');day=f'{ds[:4]}-{ds[4:6]}-{ds[6:]}'
                    a,b=windows[ticker]
                    if a<=day<=b and (ticker,day) not in written:
                        output.write(raw);written.add((ticker,day))
print('golden raw lines',len(written))
