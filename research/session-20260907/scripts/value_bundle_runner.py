"""Reproduz offline as duas rodadas H18/H19 e verifica as fontes locais."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import argparse
import collections
import csv
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'code'))
from stocks_predictor.discovery_value import run as run_first
from stocks_predictor.discovery_value_repair import run as run_repair
from stocks_predictor.disclosed_accounting import owner_accounts
from stocks_predictor.document_panel import capital_from_viewer


def read(path):return json.loads(path.read_text(encoding='utf-8'))


def verify_sources():
    capitals=read(ROOT/'capital/acquisition-retried.json')
    checked=0
    for row in capitals:
        if row['status']!='ACQUIRED':continue
        payload=(ROOT/'capital'/row['file']).read_bytes()
        assert hashlib.sha256(payload).hexdigest()==row['source_sha256']
        metadata={k:row[k] for k in ('cnpj','ref_date','document_version','document_id','received_at')}
        got=capital_from_viewer(payload,metadata,row['source'])
        for key in ('ordinary','preferred','outstanding_ordinary','outstanding_preferred','basis_date','rounding_unit_shares'):
            if got[key]!=row[key]:raise ValueError('Divergencia no capital original: '+row['document_id'])
        checked+=1
    statements=collections.defaultdict(lambda:collections.defaultdict(dict))
    for path in (ROOT/'accounting-excerpts').glob('*.csv'):
        kind='BPP_con' if 'BPP_con' in path.name else 'DRE_con'
        with path.open(encoding='utf-8',newline='') as stream:
            for row in csv.DictReader(stream,delimiter=';'):
                key=(''.join(c for c in row['CNPJ_CIA'] if c.isdigit()),row['DT_REFER'],int(row['VERSAO']))
                scale={'MIL':1000,'UNIDADE':1}[row['ESCALA_MOEDA']]
                if row['MOEDA']!='REAL':raise ValueError('Moeda desconhecida')
                statements[key][kind][row['CD_CONTA']]={'account':row['CD_CONTA'],'description':row['DS_CONTA'],
                                                        'value_brl':float(Decimal(row['VL_CONTA'])*scale)}
    accounts=read(ROOT/'capital/accounting-v2.json')['rows']
    for row in accounts:
        group=statements[row['cnpj'],row['ref_date'],row['document_version']]
        got=owner_accounts(group['BPP_con'],group['DRE_con'])
        for key in ('owner_earnings_brl','owner_equity_brl'):
            if got[key]!=row[key]:raise ValueError('Divergencia contabil: '+row['document_id'])
    return {'original_capitals_reparsed':checked,'original_accounting_documents_rederived':len(accounts)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    manifest=read(ROOT/'manifest.json')
    for name,expected in manifest['files_sha256'].items():
        path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT):raise ValueError('Caminho fora do pacote')
        with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if actual!=expected:raise ValueError('Arquivo alterado: '+name)
    audit=verify_sources()
    if args.verify_only:
        print(json.dumps({'status':'PASS','source_verification':audit},indent=2));return
    output=args.output_dir or ROOT/'results'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True,exist_ok=False)
    one=output/'first-reproduced.json';two=output/'repair-reproduced.json'
    run_first(ROOT/'original/quotes.db',ROOT/'original/snapshots.json',ROOT/'original/events.json',ROOT/'original/identity',
              ROOT/'capital/acquisition-retried.json',ROOT/'capital/accounting-v2.json',ROOT/'protocols/2026-09-07-value-discovery-protocol.json',one)
    run_repair(ROOT/'observations/h18-h19-first-observation.json',ROOT/'repaired/quotes.db',ROOT/'repaired/identity',
               ROOT/'repaired/events.json',ROOT/'repaired/reviewed-jumps.json',ROOT/'protocols/2026-09-07-value-repair-protocol.json',two)
    for generated,reference in [(one,ROOT/'observations/h18-h19-first-observation.json'),(two,ROOT/'observations/h18-h19-repaired-observation.json')]:
        got,expected=read(generated),read(reference)
        for key in ('protocol_id','features','feature_coverage','trials'):
            if got[key]!=expected[key]:raise ValueError('Reproducao divergente: '+key)
        if generated==two and got['changed_returns']!=expected['changed_returns']:
            raise ValueError('Correcoes divergentes')
    result={'status':'PASS','source_verification':audit,'all_four_trials_identical_in_both_versions':True,
            'new_adaptive_trial':False,'operational_orders':False,'profit_claim':False,
            'result_files':[str(one.resolve()),str(two.resolve())]}
    (output/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
