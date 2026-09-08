from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
root=Path.cwd();out=root/'outputs';repo=root/'work/stocks-predictor';pack=root/'work/h17-run-pack-v2'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
first=json.loads((out/'h17-first-observation.json').read_text(encoding='utf-8'))
final=json.loads((out/'h17-corrected-observation.json').read_text(encoding='utf-8'))
changed=[];same=0
for a,b in zip(first['cross_sections'],final['cross_sections'],strict=True):
 assert a['asof']==b['asof'] and a['factor_names']==b['factor_names']
 for x,y in zip(a['members'],b['members'],strict=True):
  assert all(x[k]==y[k] for k in ('ticker','cnpj','isin','accruals','selected'))
  if x['price_return']!=y['price_return']:
   assert x['price_return'] is None and x['quality_reasons']==['CONFLICTING_CORPORATE_ACTION_FACTORS'] and not y['quality_reasons']
   changed.append({'asof':a['asof'],'ticker':x['ticker'],'previous_status':x['quality_reasons'],'corrected_price_return':y['price_return']})
  else:same+=1
assert len(changed)==4
quality=[{'asof':s['asof'],'entry':s['entry'],'exit':s['exit'],**m} for s in final['cross_sections'] for m in s['members'] if m['price_return'] is None]
(out/'h17-unresolved-outcomes.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2),encoding='utf-8')
verification={'same_hypothesis_selection_and_source_inputs':True,'unchanged_outcomes':same,'changed_measurement_cells':changed,
 'first_observation_sha256':sha(out/'h17-first-observation.json'),'corrected_observation_sha256':sha(out/'h17-corrected-observation.json'),
 'operational_database_unchanged':sha(Path('C:/Users/Superleo13/stocks-predictor-work/data/stocks.db'))=='a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4',
 'source_database_unchanged':sha(root/'work/stocks-tested-real-v2-20260907.db')=='a8238568980d3303890b04590cfb5c55ab2d24c9271edd86820269336b09679a'}
assert verification['operational_database_unchanged'] and verification['source_database_unchanged']
(out/'h17-correction-and-integrity.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
records=[]
for seq,name,commit in [(1,'h17-first-observation.json','00a4a13b649e23a2af1200d4ea8ab69f5ed1094b'),(2,'h17-corrected-observation.json','4f487098e702004a88f02fe65d62a008c6df618b')]:
 r=json.loads((out/name).read_text(encoding='utf-8'))
 records.append({'family':'H17','mode':'DISCOVERY','observation_revision':seq,'observed_at_utc':r['observed_at_utc'],
  'code_commit':commit,'protocol_id':r['protocol_id'],'output_sha256':sha(out/name),'status':r['summary']['status'],
  'prior_nominal_candidates':15,'nominal_candidates_exposed_minimum':16,'historical_return_evaluations_minimum':15+seq,
  'independent_search_denominator':'UNKNOWN','untouched_holdout':False,'canonical_proof_verdict':None,
  'capital_or_spending_authorized':False,'summary':r['summary']})
ledger=repo/'docs/research/2026-09-07-h17-observations.jsonl'
with ledger.open('x',encoding='utf-8') as f:
 for r in records:f.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n')
budget={'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'mode':'DISCOVERY','family':'H17','status':'FIRST_SCREEN_COMPLETED_INCONCLUSIVE_DATA_QUALITY',
 'candidate_outputs_observed':['H17'],'candidate_outputs_still_protected':['H18','H19'],'nominal_candidates_exposed_minimum':16,
 'historical_return_evaluations_minimum':17,'H17_measurement_revisions':2,'hyperparameter_sweeps':0,'independent_search_denominator':'UNKNOWN',
 'capital_brl':[5000,10000],'capital_authorized':False,'spending_authorized':False,'profit_estimate':None,
 'next_economic_evidence_gate':'Resolve remaining event/identity outcomes and total-return data before an executable economic verdict; H18/H19 additionally require historical valuation share bases.'}
(repo/'docs/research/2026-09-07-h17-budget-update.json').write_text(json.dumps(budget,indent=2),encoding='utf-8')
(pack/'results').mkdir(exist_ok=True)
for name in ('h17-corrected-observation.json','h17-corrected-run.txt','h17-corrected-full-tests.txt','h17-unresolved-outcomes.json','h17-correction-and-integrity.json'):
 shutil.copyfile(out/name,pack/'results'/name)
shutil.copyfile(root/'work/h17-manual.md',pack/'LEIA-ME.md')
print(json.dumps({'corrected_cells':changed,'remaining_cells':len(quality),'integrity':'PASS'},indent=2))
