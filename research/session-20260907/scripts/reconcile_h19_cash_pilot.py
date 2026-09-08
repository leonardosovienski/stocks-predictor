"""Reconcile a bounded set of original-source cash facts, without returns or DB writes."""
from bisect import bisect_left
from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs';WORK=ROOT/'work';SRC=WORK/'h19-cash-closure-source'
sys.path.insert(0,str(WORK/'stocks-predictor'))
from stocks_predictor.cash_source_audit import br_date,br_decimal,next_exchange_session
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with sqlite3.connect((WORK/'value-measurement-source/quotes.db').as_uri()+'?mode=ro',uri=True) as c:
    sessions=[r[0] for r in c.execute('select distinct date from prices_raw order by date')]

class TableRows(HTMLParser):
    def __init__(self):super().__init__();self.rows=[];self.cells=None;self.value=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.cells=[]
        if tag in ('td','th') and self.cells is not None:self.value=[]
    def handle_data(self,data):
        if self.value is not None:self.value.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.value is not None:
            self.cells.append(' '.join(''.join(self.value).split()));self.value=None
        if tag=='tr' and self.cells is not None:self.rows.append(self.cells);self.cells=None

parser=TableRows();parser.feed((SRC/'jbs-dividends.html').read_text(encoding='utf-8'))
jbs=[]
for cells in parser.rows:
    # The six-column BRL table is JBS S.A.; the current N.V. USD table has four.
    if len(cells)!=6 or not re.fullmatch(r'\d{2}/\d{2}/\d{4}',cells[0]):continue
    ex,pay=[datetime.strptime(v,'%m/%d/%Y').date().isoformat() for v in cells[:2]]
    if ex<'2018-01-01':continue
    assert ex in sessions and ex<=pay
    cum=sessions[bisect_left(sessions,ex)-1]
    amount=str(Decimal(cells[4].replace(',','')))
    jbs.append({'ticker':'JBSS3','isin':'BRJBSSACNOR8','cnpj':'02916265000160','last_cum':cum,
                'ex_date':ex,'payment_date':pay,'reported_value_brl':amount,
                'display_precision_brl':'0.0001','precision_is_not_exact_amount_certification':True,
                'source_file':'jbs-dividends.html','source_sha256':sha(SRC/'jbs-dividends.html')})
assert len(jbs)==13
old=read(WORK/'profit-cash-source/raw-name-JBSS3-cash-all.json')
last_old=max(br_date(r['lastDatePriorEx']) for r in old)
missing=[r for r in jbs if r['last_cum']>last_old]
assert len(missing)==11
notice=' '.join(' '.join(p['text'].split()) for p in read(SRC/'jbs-20230619-notice.extracted.json'))
for phrase in ('02.916.265/0001-60','R$ 1,00','22 de junho de 2023','23 de junho de 2023','29 de junho de 2023'):
    assert phrase in notice
confirmed_jbs=next(r for r in jbs if r['ex_date']=='2023-06-23')
confirmed_jbs={**confirmed_jbs,'event_id':'RI:JBS:2023-06-19:DIV','action':'DIVIDENDO','approval_date':'2023-06-19',
               'value_per_share':'1.00','source_files':['jbs-dividends.html','jbs-20230619-notice.pdf'],
               'status':'ISSUER_TERMS_AND_REPORTED_PAYMENT_MATCH','whole_interval_coverage':False,
               'note':'Board resolution calls amount estimated; subsequent issuer historical table reports same amount at four decimal places. Not a broker receipt.'}

pattern=re.compile(r'^\s*(JCP(?:\s*\(complementar\))?|Dividendos)\s+(\S+)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+([\d.,]+)\s+([\d.,]+)(.*)$')
ri=[]
for page in read(WORK/'source-acquisition/ri-bbas-payments-extracted.json'):
    for line_no,line in enumerate(page['text'].splitlines(),1):
        m=pattern.match(line)
        if not m:continue
        kind,period,announcement,cum,declared_ex,pay,total,gross,tail=m.groups()
        tail=tail.strip().split()
        ri.append({'action':'DIVIDENDO' if kind=='Dividendos' else 'JRS CAP PROPRIO',
                   'last_cum':br_date(cum),'declared_ex_date':br_date(declared_ex),'payment_date':br_date(pay),
                   'gross':br_decimal(gross),'updated':br_decimal(tail[0]) if tail and re.fullmatch(r'[\d.,]+',tail[0]) else None,
                   'page':page['page'],'line':line_no,'source_line':line})
queue=read(OUT/'H19_CAIXA_FILA_DE_VALIDACAO.json')['cash_queue']
pending=[r for r in queue if r['ticker']=='BBAS3' and not r['candidate_payment_dates']]
credit=' '.join(read(SRC/'b3-credit-20250612.extracted.json')[3]['text'].split())
assert re.search(r'BCO BRASIL S.A. BRBBASACNOR3 330 JUROS SOBRE CAPITAL PRÓPRIO 14/05/2025 0,09044686629 12/06/2025',credit)
resolved=[];unresolved=[]
for r in pending:
    amount=Decimal(r['value_per_share'])
    candidates=[]
    for p in ri:
        if p['last_cum']!=r['last_cum']:continue
        if r['action']==p['action'] and amount==p['gross']:method='GROSS_ENTITLEMENT'
        elif r['action']=='RENDIMENTO' and p['updated'] is not None and amount==p['updated']-p['gross']:method='SEPARATE_MONETARY_UPDATE'
        else:continue
        assert next_exchange_session(r['last_cum'],sessions)==r['ex_date']
        pay=p['payment_date'];evidence=['ri-bbas-payments.pdf',Path(r['source_path']).name]
        if pay<r['ex_date']:
            if r['ex_date']=='2025-06-03' and amount==Decimal('0.09044686629'):
                pay='2025-06-12';evidence.append('b3-credit-20250612.pdf');method='B3_ACTUAL_CREDIT_CORRECTS_RI_PAYMENT_YEAR'
            else:continue
        candidates.append({'payment_date':pay,'method':method,'source_files':evidence,
                           'ri_declared_ex_date':p['declared_ex_date'],'ri_original_payment_date':p['payment_date'],
                           'ri_page':p['page'],'ri_line':p['line'],'ordinary_gross_and_update_kept_separate':True})
    if len(candidates)==1:resolved.append({**r,**candidates[0],'status':'EXACT_SOURCE_AMOUNT_MATCH_PAYMENT_RESOLVED','whole_interval_coverage':False})
    else:unresolved.append({**r,'candidate_matches':len(candidates)})
assert any(r['ex_date']=='2020-02-26' and r['ri_declared_ex_date']=='2020-02-24' for r in resolved)
obs=read(OUT/'h18-h19-reorganization-observation.json');trial=obs['trials'][-1]
affected=[{'asof':p['asof'],'selected':m['selected'],'cash_ex_date':r['ex_date']} for r in missing for p in trial['periods']
          for m in p['members'] if m['ticker']=='JBSS3' and p['entry']<r['ex_date']<=p['exit']]
result={'stage':'H19_CASH_SOURCE_PILOT','observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'new_strategy_returns_observed':False,'prior_price_only_returns_changed':False,
        'jbs_history_status':'PROVEN_TRUNCATED_B3_NAME_QUERY_NOT_COMPLETE_HISTORY',
        'jbs_old_history_last_cum':last_old,'jbs_missing_later_declared_events':missing,
        'jbs_affected_h19_quarter_cells':affected,'jbs_confirmed_june2023_entitlement':confirmed_jbs,
        'bbas_newly_resolved_cash_cells':resolved,'bbas_remaining_without_date':unresolved,
        'source_sha256':{p.name:sha(p) for p in SRC.iterdir() if p.is_file()},
        'next_step':'Apply the same source reconciliation to the remaining H19 cash queue, including successor instruments and the full benchmark; only then run the fixed R$5000/R$10000 continuous execution comparison.',
        'no_net_profit_claim':True}
out=OUT/'H19_CAIXA_PRIMEIRAS_CORRECOES.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'jbs_missing_after_2019':len(missing),'jbs_affected_quarter_cells':len(affected),
                  'jbs_selected_affected':sum(r['selected'] for r in affected),
                  'bbas_cash_cells_resolved':len(resolved),'bbas_selected_resolved':sum(r['selected'] for r in resolved),
                  'bbas_remaining_without_date':len(unresolved)},indent=2))
