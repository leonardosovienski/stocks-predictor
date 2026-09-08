from pathlib import Path
import sys,sqlite3,json,bisect,collections,statistics,csv,io,zipfile
root=Path.cwd();sys.path[:0]=[str(root/'work/stocks-predictor'),str(root/'work/runtime')]
from stocks_predictor import source_history,document_panel
raw=root/'work/source-acquisition';dest=root/'work/h17-preparation';dest.mkdir(exist_ok=True)
c=sqlite3.connect((root/'work/stocks-tested-real-v2-20260907.db').as_uri()+'?mode=ro',uri=True)
sec=[json.loads(r[0]) for r in c.execute("select payload_json from research_source_documents where kind='FCA_SECURITY'")];fin=[json.loads(r[0]) for r in c.execute("select payload_json from research_source_documents where kind='DFP'")]
meta=[];codes={}
for y in range(2016,2027):
 p=raw/f'fca_cia_aberta_{y}.zip';payload=p.read_bytes();md=source_history.document_metadata(payload,'fca',y);meta.extend({'document_id':doc,**r} for doc,r in md.items())
 with zipfile.ZipFile(io.BytesIO(payload)) as z:
  for r in csv.DictReader(io.TextIOWrapper(z.open(f'fca_cia_aberta_{y}.csv'),encoding='latin-1'),delimiter=';'):codes[''.join(x for x in r['CNPJ_CIA'] if x.isdigit())]=str(int(r['CD_CVM']))
secb=collections.defaultdict(list);mb=collections.defaultdict(list)
for r in sec:secb[r['document_id']].append(r)
for r in meta:mb[r['cnpj']].append(r)
ids=collections.defaultdict(list)
for p in (root/'work/h17-source-identity-v3').glob('identity-*.jsonl'):
 for line in p.read_text(encoding='utf-8').splitlines():
  r=json.loads(line);ids[r['ticker']].append(r)
for r in ids.values():r.sort(key=lambda x:x['first_date'])
prices=collections.defaultdict(list)
for d,t,o,cl,v,q in c.execute("select date,ticker,open,close,volume_fin,quote_factor from prices_raw where market_type='010' order by ticker,date"):
 prices[t].append((d,o/q,cl/q,v))
dates=sorted({r[0] for rows in prices.values() for r in rows});di={t:[r[0] for r in rows] for t,rows in prices.items()};months={d[:7]:d for d in dates if '2018-01-01'<=d<='2025-12-31'}
snapshots=[];needed=collections.defaultdict(set)
for asof in months.values():
 mapping={}
 for cnpj,rows in mb.items():
  eligible=[r for r in rows if r['available_at']<=asof]
  if not eligible:continue
  key=max((r['ref_date'],r['version'],r['available_at']) for r in eligible)
  for doc in [r['document_id'] for r in eligible if (r['ref_date'],r['version'],r['available_at'])==key]:
   for r in secb[doc]:
    if r['trading_start']<=asof and (not r['trading_end'] or asof<=r['trading_end']):
     if r['ticker'] in mapping and mapping[r['ticker']]!=cnpj:raise ValueError('ambiguous ticker')
     mapping[r['ticker']]=cnpj
 wi=bisect.bisect_left(dates,asof);ws=dates[wi-126];eligible=[]
 for t,cnpj in mapping.items():
  if t not in prices:continue
  ix=bisect.bisect_left(di[t],asof)
  if ix<252 or ix>=len(di[t]) or di[t][ix]!=asof:continue
  obs=[r for r in ids[t] if r['first_date']<=asof];identity=max(obs,key=lambda r:r['first_date']) if obs else None
  if not identity or identity['kind'] not in {'ON','PN','PNA','PNB','PNC','PND','UNT'}:continue
  low=bisect.bisect_left(di[t],ws);vol=[r[3] for r in prices[t][low:ix]];median=statistics.median(vol+[0]*(126-len(vol)))
  if median<=0:continue
  eligible.append({'ticker':t,'cnpj':cnpj,'median_volume':median,'isin':identity['isin']})
 eligible.sort(key=lambda r:(-r['median_volume'],r['ticker']));chosen=[];cnpjs=set()
 for r in eligible:
  if r['cnpj'] in cnpjs:continue
  cnpjs.add(r['cnpj']);chosen.append(r)
  if len(chosen)==60:break
 panel=document_panel.fundamentals_asof(fin,sec,asof,security_metadata=meta)
 for r in chosen:
  filing=panel.get(r['ticker'],{})
  r['accruals']=filing.get('accruals')
  r['filing']=filing
  eligible_meta=[m for m in mb[r['cnpj']] if m['available_at']<=asof]
  newest=max((m['ref_date'],m['version'],m['available_at']) for m in eligible_meta)
  r['security_documents']=[m for m in eligible_meta if (m['ref_date'],m['version'],m['available_at'])==newest]
  needed[r['cnpj']].add(r['ticker'])
 snapshots.append({'asof':asof,'universe':chosen})
(dest/'snapshots-before-event-gates.json').write_text(json.dumps(snapshots,ensure_ascii=False,indent=2),encoding='utf-8')
(dest/'needed-issuers.json').write_text(json.dumps([{'cnpj':c,'codeCVM':codes[c],'tickers':sorted(ts)} for c,ts in sorted(needed.items())],indent=2),encoding='utf-8')
print('snapshots',len(snapshots),'issuers',len(needed),'tickers',len(set().union(*needed.values())),'min/median universe',min(len(s['universe']) for s in snapshots),statistics.median(len(s['universe']) for s in snapshots))
