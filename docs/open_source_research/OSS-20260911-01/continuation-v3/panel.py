import collections,datetime,hashlib,json,pathlib,sys
W=pathlib.Path(__file__).parent;S=pathlib.Path('C:/STOCKS/work/completion-r7-20260910/source15-materialized');sys.path.insert(0,'C:/STOCKS/stocks-predictor/stocks_predictor');import source_history
manifest=json.loads((S/'SHA256.json').read_text());hashes={}
def read(name):
 p=S/name;b=p.read_bytes();h=hashlib.sha256(b).hexdigest();assert h==manifest[name];hashes[str(p)]=h;return json.loads(b)
cash=read('cash-events.json');corp=read('corporate-actions.json');evidence=read('evidence.json');catalog=read('primary-catalog.json')
fca=W.parent/'continuation-v2/fca2023.zip';payload=fca.read_bytes();hashes[str(fca)]=hashlib.sha256(payload).hexdigest();links=source_history.derive_fca_securities(payload,2023)
primary_hashes={}
def source_ok(r):
 refs=r.get('sources',[])
 if not refs:return False
 for ref in refs:
  name=ref.get('verified_primary_file');h=ref.get('source_sha256',ref.get('sha256'))
  if not name or not h or name not in manifest or manifest[name]!=h:return False
  if name not in primary_hashes:primary_hashes[name]=hashlib.sha256((S/name).read_bytes()).hexdigest()
  if primary_hashes[name]!=h:return False
 return True
rows=[]
for r in cash:
 ticker=r['ticker'];asof=r['ex_date'];eligible=[x for x in links if x['ticker']==ticker and x['available_at']<=asof and x['trading_start']<=asof and (not x['trading_end'] or asof<=x['trading_end'])]
 cnpjs=sorted({x['cnpj'] for x in eligible});pit=[x for x in eligible if ticker in source_history.security_links_asof([a for a in links if a['cnpj']==x['cnpj']],x['cnpj'],asof)]
 cnpjs=sorted({x['cnpj'] for x in pit})
 fields={f:r.get(f) not in [None,''] for f in ['isin','gross_per_share','net_per_share','payment_date','known_on','available_on']}
 temporal=bool(r.get('available_on') and r['available_on']<=asof)
 affected=[x['event_id'] for x in corp if x['ticker']==ticker and x['ex_date']<=asof]
 rows.append({'event_id':r['event_id'],'ticker':ticker,'isin':r.get('isin'),'ex_date':asof,'payment_date':r.get('payment_date'),'cnpjs_asof_from_fca2023':cnpjs,'unique_issuer_mapping':len(cnpjs)==1,'fields_present':fields,'primary_bytes_verified':source_ok(r),'value_known_by_ex_date_recorded':temporal,'same_asset_prior_actions_in_inventory':affected,'net_value_status':'CONDITIONAL_SCENARIO' if fields['net_per_share'] else 'MISSING','cash_fields_reconstructible_conditionally':fields['net_per_share'] and fields['payment_date'],'economic_panel_usable':False,'remaining':['FCA2023 is not full identity/ISIN interval history','financial PIT join and intervening actions not certified','continuous cash-event inventory incomplete','personal net/cost/rounding unverified']})
def aggregate(rs):
 return {'rows':len(rs),'unique_events':len({r['event_id'] for r in rs}),'ex_dates':len({r['ex_date'] for r in rs}),'ex_min':min((r['ex_date'] for r in rs),default=None),'ex_max':max((r['ex_date'] for r in rs),default=None),'field_presence':{f:sum(r['fields_present'][f] for r in rs) for f in ['isin','gross_per_share','net_per_share','payment_date','known_on','available_on']},'verified_primary_bytes':sum(r['primary_bytes_verified'] for r in rs),'one_cnpj_asof_from_partial_fca':sum(r['unique_issuer_mapping'] for r in rs),'recorded_value_available_by_ex':sum(r['value_known_by_ex_date_recorded'] for r in rs),'conditional_cash_fields_complete':sum(r['cash_fields_reconstructible_conditionally'] for r in rs),'certified_integrated_rows':0}
by_asset={t:aggregate([r for r in rows if r['ticker']==t]) for t in sorted({r['ticker'] for r in rows})}
by_issuer={c:aggregate([r for r in rows if c in r['cnpjs_asof_from_fca2023']]) for c in sorted({c for r in rows for c in r['cnpjs_asof_from_fca2023']})}
by_year={y:aggregate([r for r in rows if r['ex_date'][:4]==y]) for y in sorted({r['ex_date'][:4] for r in rows})}
intervals=evidence['required_intervals'];coverage=evidence['cash_coverage']
result={'run_id':'OSS-20260911-01','experiment':'X01','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_hashes':hashes,'source_manifest_sha256':hashlib.sha256((S/'SHA256.json').read_bytes()).hexdigest(),'source_primary_files_checked':len(primary_hashes),'scope':'Source15 event-input population; not all B3 or X05 universe; no price or returns read','summary':aggregate(rows),'by_asset':by_asset,'by_issuer_partial':by_issuer,'by_ex_year':by_year,'required_interval_count':len(intervals),'required_interval_assets':len({x[0] for x in intervals}),'cash_coverage_raw_count':len(coverage),'cash_coverage_raw_type':type(coverage).__name__,'corporate_actions_in_input':len(corp),'raw_coverage':coverage,'limits':['Completeness of fields is not economic correctness','Known/available dates are asserted metadata with source lineage; not intraday publication proof','Absence of mapping in FCA2023 is UNKNOWN outside its coverage, not issuer absence','0 certified rows is a certification status, not proof all800 are economically false','Payment-date and ex-date availability serve different questions: payout reconstruction vs predictive input','Net amounts in preserved data may be historical tax scenarios, not personal cash receipts']}
(W/'X01-coverage.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(W/'X01-panel.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
assert all(hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
print(json.dumps({k:v for k,v in result.items() if k not in ['by_asset','by_issuer_partial','by_ex_year','source_hashes','raw_coverage']},ensure_ascii=False,indent=2))
