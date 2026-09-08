"""Exact-version owner earnings/equity; preparation without candidate returns."""
from pathlib import Path
from decimal import Decimal
import collections,csv,hashlib,io,json,sys,unicodedata,zipfile
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'work'))
from fetch_disclosed_capital import jobs
def norm(text):return ''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c))
def key(r):return ''.join(c for c in r['CNPJ_CIA'] if c.isdigit()),r['DT_REFER'],int(r['VERSAO'])
docs={key(r):r for r in jobs()};groups=collections.defaultdict(lambda:collections.defaultdict(dict));sources={}
for year in range(2016,2027):
 path=ROOT/f'work/source-acquisition/dfp_cia_aberta_{year}.zip'
 with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
 sources[path.name]=digest
 with zipfile.ZipFile(path) as z:
  for statement in ('BPP_con','DRE_con'):
   name=f'dfp_cia_aberta_{statement}_{year}.csv'
   if name not in z.namelist():continue
   for r in csv.DictReader(io.TextIOWrapper(z.open(name),encoding='latin-1'),delimiter=';'):
    if key(r) not in docs or r['ORDEM_EXERC']!='ÚLTIMO':continue
    if r['DT_FIM_EXERC']!=r['DT_REFER']:continue
    scale={'MIL':1000,'UNIDADE':1}.get(r['ESCALA_MOEDA'].strip().upper())
    if scale is None or r['MOEDA'].strip().upper()!='REAL':raise ValueError('unknown units')
    v=Decimal(r['VL_CONTA'])*scale
    row={'account':r['CD_CONTA'],'description':r['DS_CONTA'],'value_brl':float(v),'raw_value':r['VL_CONTA'],
         'scale':r['ESCALA_MOEDA'],'period_start':r.get('DT_INI_EXERC'),'period_end':r['DT_FIM_EXERC'],
         'archive':path.name,'archive_sha256':digest}
    old=groups[key(r)][statement].get(r['CD_CONTA'])
    if old and old!=row:raise ValueError(('conflicting account',key(r),r['CD_CONTA']))
    groups[key(r)][statement][r['CD_CONTA']]=row
rows=[]
for identity,doc in sorted(docs.items()):
 bpp=groups[identity]['BPP_con'];dre=groups[identity]['DRE_con']
 from stocks_predictor.disclosed_accounting import owner_accounts
 rows.append({'cnpj':identity[0],'ref_date':identity[1],'document_version':identity[2],'document_id':doc['ID_DOC'],
   'received_at':doc['DT_RECEB'],**owner_accounts(bpp,dre)})

dest=ROOT/'work/value-capital-source/accounting-v2.json'
dest.write_text(json.dumps({'archive_sha256':sources,'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
print('docs',len(rows),'owner_earnings',sum(r['owner_earnings_brl'] is not None for r in rows),'owner_equity',sum(r['owner_equity_brl'] is not None for r in rows))
print('missing',dict(collections.Counter(i for r in rows for i in r['issues'])))
