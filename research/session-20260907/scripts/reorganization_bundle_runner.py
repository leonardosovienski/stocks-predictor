"""Reproduz offline o diagnóstico registrado de reorganizações societárias."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'code'))
from stocks_predictor.discovery_reorganizations import run

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    manifest=read(ROOT/'manifest.json')
    for name,sha in manifest['files_sha256'].items():
        path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT):raise ValueError('Caminho fora do pacote')
        with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if actual!=sha:raise ValueError('Arquivo alterado: '+name)
    if args.verify_only:
        print(json.dumps({'status':'PASS','verified_files':len(manifest['files_sha256'])},indent=2));return
    output=args.output_dir or ROOT/'results'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True,exist_ok=False)
    target=output/'reorganization-reproduced.json'
    run(ROOT/'observations/h18-h19-repaired-observation.json',ROOT/'base/quotes.db',ROOT/'base/identity',
        ROOT/'successors/successors.db',ROOT/'successors/identity',ROOT/'base/events.json',
        ROOT/'base/reviewed-jumps.json',ROOT/'terms/reorganizations.json',ROOT/'protocol.json',target)
    got=read(target);expected=read(ROOT/'observations/h18-h19-reorganization-observation.json')
    for key in ('protocol_id','trials','changed_returns','unchanged_selection_and_factor_values'):
        if got[key]!=expected[key]:raise ValueError('Reproducao divergente: '+key)
    record={'status':'PASS','all_four_trials_and_members_identical':True,'verified_files':len(manifest['files_sha256']),
            'new_independent_evidence':False,'operational_orders':False,'profit_claim':False,
            'result_file':str(target.resolve())}
    (output/'verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
