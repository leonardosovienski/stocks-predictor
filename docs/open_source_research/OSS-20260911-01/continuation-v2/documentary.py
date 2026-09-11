"""Acquisition/manifest first, verification in a separately invoked --verify stage."""
import csv,datetime,hashlib,io,json,pathlib,sys,urllib.request,zipfile
W=pathlib.Path(__file__).parent
URL='https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_2023.zip'
def rows(payload,name):
 with zipfile.ZipFile(io.BytesIO(payload)) as z:
  return list(csv.DictReader(io.StringIO(z.read(name).decode('latin-1')),delimiter=';'))
if '--verify' not in sys.argv:
 with urllib.request.urlopen(URL,timeout=30) as r:payload=r.read(20000001)
 assert len(payload)<=20000000,'download cap20MB'
 (W/'fca2023.zip').write_bytes(payload)
 meta=rows(payload,'fca_cia_aberta_2023.csv');groups={}
 for row in meta:groups.setdefault(row['CNPJ_CIA'],[]).append(row)
 selected=[]
 for cnpj in sorted(groups):
  docs=sorted(groups[cnpj],key=lambda r:(r['DT_REFER'],int(r['VERSAO']),r['ID_DOC']))
  if len(docs)>=4:
   selected.extend(docs[:4])
   if len(selected)==12:break
 assert len(selected)==12
 manifest={'id':'DOC03','url':URL,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'license':'ODbL declared in official FCA catalog','selection':'First three CNPJs lexicographically with >=4 filing rows; first4 sorted ref/version/id each. No price/return selection. Includes non-listed/unsupported records as rejection cases.','protocol':'Compare metadata and links with independent CSV conditions at received_date and received_date+1; exactly12 documents,0 metadata divergence,0 premature link; no tuning. This is FCA identity scope, not full financial/capital-event X01.','availability':'following calendar day is model convention, not observed public timestamp','documents':selected}
 (W/'DOC03-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'bytes':len(payload),'ids':[r['ID_DOC'] for r in selected]},indent=2));sys.exit()
manifest=json.loads((W/'DOC03-manifest.json').read_text(encoding='utf-8'));payload=(W/'fca2023.zip').read_bytes();assert hashlib.sha256(payload).hexdigest()==manifest['sha256']
sys.path.insert(0,'C:/STOCKS/stocks-predictor/stocks_predictor');import source_history
observed=source_history.document_metadata(payload,'fca',2023);issues=[];links=source_history.derive_fca_securities(payload,2023,issues=issues)
out=[]
for r in manifest['documents']:
 doc=r['ID_DOC'];m=observed[doc];cnpj=''.join(x for x in r['CNPJ_CIA'] if x.isdigit());received=r['DT_RECEB'][:10];available=(datetime.date.fromisoformat(received)+datetime.timedelta(days=1)).isoformat()
 assert m=={'cnpj':cnpj,'ref_date':r['DT_REFER'],'version':int(r['VERSAO']),'received_at':received,'available_at':available}
 dl=[x for x in links if x['document_id']==doc]
 assert source_history.security_links_asof(dl,cnpj,received)==[]
 expected=sorted({x['ticker'] for x in dl if x['trading_start']<=available and (not x['trading_end'] or available<=x['trading_end'])})
 assert source_history.security_links_asof(dl,cnpj,available)==expected
 out.append({'document_id':doc,'status':'PASS','cnpj':cnpj,'rows_accepted':len(dl),'tickers_at_model_cutoff':expected})
receipt={'id':'DOC03','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest_sha256':hashlib.sha256((W/'DOC03-manifest.json').read_bytes()).hexdigest(),'runner_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'result':'PASS','documents':out,'all_archive_parser_issues':len(issues),'scope':'C3/E5 LOCAL ENGINEERING; 12 metadata identities and no link before model cutoff, not a financial panel or economic validation'}
(W/'DOC03-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt,indent=2))
