"""Offline JSON interface to the five experimental capabilities.

python tool.py ranking input.json output.json
Input contracts and examples: fixtures.json; no downloading or market execution.
"""
import argparse,importlib.util,json,pathlib,sys,hashlib
W=pathlib.Path(__file__).parent
s=importlib.util.spec_from_file_location('oss_tools',W/'capabilities.py');c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c)
def main():
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['ranking','normalize','neutralize','participation','rebalance']);p.add_argument('input',type=pathlib.Path);p.add_argument('output',type=pathlib.Path);a=p.parse_args()
    if a.output.exists():raise SystemExit('Output exists; use a new receipt path')
    b=a.input.read_bytes();x=json.loads(b)
    if a.operation=='ranking':result=c.ranking_report(x)
    elif a.operation=='normalize':result=vars(c.fit_normalizer(**x))
    elif a.operation=='neutralize':result=c.group_residual(**x)
    elif a.operation=='participation':result=c.participation_screen(**x)
    else:result=c.bounded_rebalance(**x)
    a.output.write_text(json.dumps({'run_id':'OSS-20260911-01','scope':'experimental; no economic certification','input_sha256':hashlib.sha256(b).hexdigest(),'code_sha256':hashlib.sha256((W/'capabilities.py').read_bytes()).hexdigest(),'operation':a.operation,'result':result},ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
if __name__=='__main__':main()
