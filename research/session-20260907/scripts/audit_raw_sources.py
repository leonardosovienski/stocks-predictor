import collections
import csv
import io
import json
import pathlib
import sqlite3
import sys
import zipfile
from decimal import Decimal
from inspect_state import ROOT, REPO, CANON, digest

sys.path.insert(0, str(ROOT / 'work/runtime'))
sys.path.insert(0, str(REPO / 'stocks_predictor'))
import ingest_cvm as cvm

def read(z, name):
    with z.open(name) as f:
        return list(csv.DictReader(io.TextIOWrapper(f,encoding='latin-1'),delimiter=';'))

def main():
    result = {'mode':'DATA_FEASIBILITY_ONLY_NO_STRATEGY_RETURNS','raw_sources':{}}
    for kind in ('dfp','fre'):
        p=ROOT / f'work/raw/{kind}_cia_aberta_2023.zip'
        result['raw_sources'][kind]={'sha256':digest(p),'bytes':p.stat().st_size,'url':f'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{kind.upper()}/DADOS/{p.name}'}
    dbytes=(ROOT/'work/raw/dfp_cia_aberta_2023.zip').read_bytes()
    dz=zipfile.ZipFile(io.BytesIO(dbytes))
    main_rows=read(dz,'dfp_cia_aberta_2023.csv')
    drows=read(dz,'dfp_cia_aberta_DRE_con_2023.csv')
    mains=collections.defaultdict(list)
    for r in main_rows:
        mains[(r['CNPJ_CIA'],r['DT_REFER'])].append(r)
    result['dfp_headers']={'main':list(main_rows[0]),'dre':list(drows[0])}
    result['dfp_scales']=dict(collections.Counter(r['ESCALA_MOEDA'] for r in drows))
    result['dfp_main_multiple_versions']=sum(len({r['VERSAO'] for r in rs})>1 for rs in mains.values())
    examples=[]
    affected=set()
    for r in drows:
        if r['ORDEM_EXERC']!='ÚLTIMO': continue
        ms=mains.get((r['CNPJ_CIA'],r['DT_REFER']),[])
        dates=[m['DT_RECEB'] for m in ms if m['VERSAO']==r['VERSAO']]
        if not dates: continue
        oldest=min(m['DT_RECEB'] for m in ms)
        actual=min(dates)
        if actual>oldest:
            affected.add((r['CNPJ_CIA'],r['DT_REFER']))
            if r['CD_CONTA']=='3.01' and len(examples)<5:
                examples.append({k:r[k] for k in ('CNPJ_CIA','DENOM_CIA','DT_REFER','VERSAO','CD_CONTA','VL_CONTA','ESCALA_MOEDA')}|{'assigned_first_date':oldest,'matching_version_date':actual})
    result['dfp_version_date_mismatch_companies']=len(affected)
    result['dfp_version_date_examples']=examples
    result['dfp_scale_example']=next({k:r[k] for k in ('CNPJ_CIA','DENOM_CIA','DT_REFER','VERSAO','CD_CONTA','VL_CONTA','ESCALA_MOEDA')} for r in drows if 'AMBEV' in r['DENOM_CIA'] and r['CD_CONTA']=='3.01' and r['ORDEM_EXERC']=='ÚLTIMO')
    fbytes=(ROOT/'work/raw/fre_cia_aberta_2023.zip').read_bytes()
    fz=zipfile.ZipFile(io.BytesIO(fbytes))
    frows=cvm.parse_fre_float_rows(cvm._open_fre_distribuicao_capital_main(fbytes))
    dates=cvm.parse_received_dates(fbytes,'fre_cia_aberta_')
    groups=collections.defaultdict(list)
    for r in frows:
        if r['shares_outstanding'] and r['doc_id'] in dates:
            groups[(cvm._norm(r['company']),r['ref_date'])].append(r|{'known_at':dates[r['doc_id']]})
    bad=[]
    for key,rs in groups.items():
        earliest=min(r['known_at'] for r in rs)
        maximum=max(r['shares_outstanding'] for r in rs)
        first_values=[r['shares_outstanding'] for r in rs if r['known_at']==earliest]
        if maximum>max(first_values)*1.0001:
            bad.append({'company':key[0],'ref_date':key[1],'earliest_date':earliest,'first_max_shares':max(first_values),'assigned_max_shares':maximum,'max_first_known_at':min(r['known_at'] for r in rs if r['shares_outstanding']==maximum)})
    result['fre_groups']=len(groups)
    result['fre_future_max_assigned_earlier']=len(bad)
    result['fre_future_max_examples']=bad[:8]
    result['fre_bbas_documents']=[r for r in frows if 'BRASIL' in r['company'] and 'BCO' in r['company']]
    conn=sqlite3.connect((CANON/'data/stocks.db').as_uri()+'?mode=ro',uri=True)
    conn.execute('PRAGMA query_only=ON')
    result['real_db_matching_revision_examples']=[]
    map_bytes=(CANON/'ticker_of_2019.json').read_bytes()
    mapping=json.loads(map_bytes.decode('utf-16' if map_bytes.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'))
    result['mapping_shape']=str(type(mapping))
    for x in examples:
        ticker=mapping.get(cvm._norm(x['DENOM_CIA'])) if isinstance(mapping,dict) else None
        if ticker:
            rows=conn.execute('SELECT ticker,ref_date,source,receita_liquida,known_at FROM fundamentals WHERE ticker=? AND ref_date=?',(ticker,x['DT_REFER'])).fetchall()
            result['real_db_matching_revision_examples'].append({'raw':x,'db':rows})
    result['db_ab_ev']=conn.execute("SELECT ticker,ref_date,source,receita_liquida,known_at FROM fundamentals WHERE ticker='ABEV3' AND source='CVM DFP 2023'").fetchall()
    result['db_bbas_shares']=conn.execute("SELECT ticker,ref_date,source,shares_outstanding,known_at FROM fundamentals WHERE ticker='BBAS3' AND source='CVM FRE 2023'").fetchall()
    result['dividend_out_of_plausible_range']=conn.execute("SELECT COUNT(*) FROM dividends WHERE ex_date>'2027-12-31' OR ex_date<'1990-01-01'").fetchone()[0]
    conn.close()
    (ROOT/'outputs/source-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
