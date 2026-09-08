"""Prepare immutable offline inputs; no return calculations or database writes."""
from bisect import bisect_right
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import zipfile

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'work'
OUT = WORK / 'h19-retail-bundle'
(OUT / 'inputs').mkdir(parents=True, exist_ok=True)
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, obj):
    (OUT/'inputs'/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
protocol = read(WORK/'stocks-predictor/docs/research/2026-09-07-h19-retail-protocol.json')
obsfile = ROOT/'outputs/h18-h19-reorganization-observation.json'
assert sha(obsfile) == protocol['source_observation_sha256']
obs = read(obsfile)
trial = next(t for t in obs['trials'] if t['family']=='H19' and t['holding_months']==3)
first = next(p for p in trial['periods'] if any(m['selected'] for m in p['members']))
members = [m for m in first['members'] if m['selected']]
dates = {first['asof'].replace('-',''), first['entry'].replace('-','')}
tickers = {m['ticker'] for m in members}
raw = []
archive = Path(r'C:\Users\Superleo13\stocks-predictor-work\data\COTAHIST_A2018.ZIP')
with zipfile.ZipFile(archive) as z:
    for name in z.namelist():
        with z.open(name) as stream:
            for line in stream:
                s = line.decode('latin1').rstrip('\r\n')
                if s[:2]!='01' or s[2:10] not in dates: continue
                ticker = s[12:24].strip()
                if ticker in tickers and s[24:27]=='010': raw.append(s)
                elif ticker.endswith('F') and ticker[:-1] in tickers and s[24:27]=='020': raw.append(s)
def parsed(s):
    divisor = Decimal(100) * int(s[210:217])
    return dict(ticker=s[12:24].strip(), date=s[2:6]+'-'+s[6:8]+'-'+s[8:10],
                isin=s[230:242], open=str(Decimal(s[56:69])/divisor),
                close=str(Decimal(s[108:121])/divisor), market=s[24:27], raw=s)
records = [parsed(s) for s in raw]
bykey = {(r['ticker'],r['date']): r for r in records}
assert len(bykey)==len(records), 'Ambiguous duplicate source quote'
inputs = []
for m in members:
    t=m['ticker']; signal=bykey[t,first['asof']]; standard=bykey[t,first['entry']]; frac=bykey[t+'F',first['entry']]
    assert signal['isin']==standard['isin']==frac['isin']==m['isin']
    inputs.append(dict(ticker=t,isin=m['isin'],signal_close=signal['close'],
                       quote=dict(date=first['entry'],isin=m['isin'],standard=standard['open'],fractional=frac['open']),
                       raw_records=[signal['raw'],standard['raw'],frac['raw']]))
db=WORK/'value-measurement-source/quotes.db'
with sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True) as conn:
    sessions=[r[0] for r in conn.execute('select distinct date from prices_raw order by date')]
settlement=sessions[bisect_right(sessions,first['entry'])+2]  # Pre-27 May 2019: D+3.
save('entry-fixture.json',dict(asof=first['asof'],entry=first['entry'],settlement=settlement,members=inputs,
    observation_sha256=sha(obsfile), raw_archive_sha256=sha(archive), source='B3 COTAHIST_A2018.ZIP',
    settlement_source='https://www.b3.com.br/pt_br/noticias/liquidacao.htm',
    scope='First frozen eligible entry only; no sale, cash-receipt history, strategy return or profit computed.'))
save('sessions.json',sessions)
for src, name in [(obsfile,'observation.json'),(WORK/'stocks-predictor/docs/research/2026-09-07-h19-retail-protocol.json','protocol.json'),
    (WORK/'h19-cash-expanded-source/reviewed-payment-dates.json','reviewed-payment-dates.json'),
    (WORK/'value-event-terms/reorganizations.json','reorganizations.json'),
    (WORK/'value-measurement-source/events.json','stock-events.json'),
    (ROOT/'outputs/H19_CAIXA_PRIMEIRAS_CORRECOES.json','prior-pilot.json'),
    (ROOT/'outputs/VALIDACAO_FRACIONARIO_STOCKS.json','fractional-audit.json')]:
    shutil.copy2(src,OUT/'inputs'/name)
shutil.copy2(WORK/'stocks-predictor/stocks_predictor/retail_cash.py',OUT/'retail_cash.py')
print(json.dumps({'entry':first['entry'],'members':len(inputs),'settlement':settlement,'raw_records':len(records)}))
