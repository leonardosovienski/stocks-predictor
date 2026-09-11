import collections,hashlib,json,pathlib,sys
W=pathlib.Path(__file__).parent;sys.path.insert(0,'C:/STOCKS/stocks-predictor/stocks_predictor');import source_history
b=(W.parent/'continuation-v2/fca2023.zip').read_bytes();meta=source_history.document_metadata(b,'fca',2023);links=source_history.derive_fca_securities(b,2023)
rows=[json.loads(l) for l in (W/'X01-panel.jsonl').read_text().splitlines()];changed=[]
for r in rows:
 accepted=[];asof=r['ex_date']
 for cnpj in r['cnpjs_asof_from_fca2023']:
  eligible=[(doc,m) for doc,m in meta.items() if m['cnpj']==cnpj and m['available_at']<=asof]
  if not eligible:continue
  key=max((m['ref_date'],m['version'],m['available_at']) for doc,m in eligible)
  latest={doc for doc,m in eligible if (m['ref_date'],m['version'],m['available_at'])==key}
  if any(x['document_id'] in latest and x['ticker']==r['ticker'] and x['trading_start']<=asof and (not x['trading_end'] or asof<=x['trading_end']) for x in links):accepted.append(cnpj)
 r['metadata_aware_cnpjs']=accepted;r['mapping_status']='CANDIDATE_PARTIAL_SOURCE' if len(accepted)==1 else 'UNKNOWN_OR_AMBIGUOUS'
 if accepted!=r['cnpjs_asof_from_fca2023']:changed.append(r['event_id'])
out={'run_id':'OSS-20260911-01','experiment':'X01','input_sha256':hashlib.sha256((W/'X01-panel.jsonl').read_bytes()).hexdigest(),'method':'Latest filing metadata chosen before security-row join; latest blank filings do not resurrect older tickers','candidate_rows':sum(len(r['metadata_aware_cnpjs'])==1 for r in rows),'changed_events':changed,'by_asset':{t:sum(r['ticker']==t and len(r['metadata_aware_cnpjs'])==1 for r in rows) for t in sorted({r['ticker'] for r in rows})},'by_issuer':dict(collections.Counter(c for r in rows for c in r['metadata_aware_cnpjs'])),'certified_integrated_rows':0}
(W/'X01-joincheck.json').write_text(json.dumps(out,indent=2));(W/'X01-panel-integrated.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows));print(json.dumps({k:v for k,v in out.items() if k not in ['by_asset','by_issuer']},indent=2))
