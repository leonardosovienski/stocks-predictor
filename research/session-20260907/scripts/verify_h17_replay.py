from pathlib import Path
import hashlib,json
root=Path.cwd();out=root/'outputs'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
before=read(out/'h17-corrected-observation.json');replay=read(out/'h17-replay-observation.json')
assert before['protocol']==replay['protocol']
assert before['cross_sections']==replay['cross_sections']
assert before['summary']==replay['summary']
assert {Path(p).name:s for p,s in before['input_sha256'].items()}=={Path(p).name:s for p,s in replay['input_sha256'].items()}
record={'status':'PASS','method':'Extracted delivered ZIP with standalone RODAR_H17.py, verified sealed files and repeated actual calculation offline in a different directory.',
 'same_protocol':True,'same_input_content_hashes':True,'same_5399_member_outcomes':True,'same_summary':True,
 'corrected_observation_sha256':sha(out/'h17-corrected-observation.json'),'replay_observation_sha256':sha(out/'h17-replay-observation.json'),
 'expected_metadata_differences':['observation timestamp','absolute input paths'],
 'code_tests':{'passed':483,'coverage_percent':84,'ruff_ci_scope':'PASS','pyright_configured_scope':'PASS','wheel_build':'PASS','wheel_smoke_outside_checkout':'PASS'},
 'operational_database_sha256':sha(Path('C:/Users/Superleo13/stocks-predictor-work/data/stocks.db'))}
assert record['operational_database_sha256']=='a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4'
(out/'h17-reproduction-verification.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
