"""Validate the prepared source amendment with global Python3.13, offline.

This is source-readiness validation only. It never evaluates strategy returns.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

PARENT_SHA='7c24e093f7a148c3f375fff9fbd23db62f049ba8012e49e6ba7b4413e27a372b'
REVISION_SHA='3b36e2416e44f2b0a30e88d4306e00cdc74a7302c6e9b0e33950a893ea169bda'

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def checked_member(root,name):
    target=(root/name).resolve()
    if not target.is_relative_to(root.resolve()):raise ValueError('Unsafe manifest path')
    return target

def main():
    if sys.version_info[:2] != (3,13):
        raise RuntimeError('Este validador exige Python global3.13; nenhum teste foi executado.')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline13',type=Path,required=True,help='Extracted revision13 package')
    parser.add_argument('--workspace',type=Path,required=True,help='NEW directory for copied inputs and audit')
    args=parser.parse_args()
    root=Path(__file__).resolve().parent;base=args.baseline13.resolve();dest=args.workspace.resolve()
    if dest.exists():raise FileExistsError('Use a new workspace; no audit is overwritten')
    for name,sha in read(root/'COMPLEMENTO_SHA256.json').items():
        if digest(checked_member(root,name))!=sha:raise ValueError('Changed amendment: '+name)
    for name,sha in read(base/'PACKAGE_SHA256.json').items():
        if digest(checked_member(base,name))!=sha:raise ValueError('Changed baseline package: '+name)
    if digest(base/'inputs/SHA256.json')!=PARENT_SHA:raise ValueError('Wrong parent sources')
    if digest(root/'replacement-inputs/SHA256.json')!=REVISION_SHA:raise ValueError('Wrong amendment manifest')
    before=read(base/'inputs/cash-events.json');after=read(root/'replacement-inputs/cash-events.json')
    approved={r['event_id']:r for r in read(root/'source-amendment-14.json')['amendments']}
    if len(before)!=800 or len(after)!=800 or len(approved)!=2:raise ValueError('Lost or duplicated events')
    mutable={'net_per_share','tax_source','sources','source_review','net_rule',
             'net_evidence_review','actual_broker_cent_rounding_not_verified'}
    for original,row in zip(before,after):
        if row['event_id'] not in approved:
            if row!=original:raise ValueError('Unrelated event changed')
        else:
            if {k:v for k,v in row.items() if k not in mutable}!={k:v for k,v in original.items() if k not in mutable}:
                raise ValueError('Entitlement, schedule or knowledge fields changed')
            proof=approved[row['event_id']]
            if (original['net_per_share'] is not None or row['net_per_share']!=proof['gross_per_share']
                    or row['gross_per_share']!=proof['gross_per_share']
                    or row['payment_date']!=proof['payment_date'] or not row['tax_source']):
                raise ValueError('Unproven net amount or revised schedule')
    dest.mkdir(parents=True)
    inputs=dest/'inputs';shutil.copytree(base/'inputs',inputs)
    for name in ('cash-events.json','source-revision.json','SHA256.json'):
        shutil.copyfile(root/'replacement-inputs'/name,inputs/name)
    wheel,=list((base/'wheel').glob('*.whl'))
    sys.path.insert(0,str(wheel))
    from stocks_predictor import source_closure
    if not str(source_closure.__file__).startswith(str(wheel)):
        raise RuntimeError('Source audit did not load the verified wheel')
    result=source_closure.audit(base/'baseline',inputs,base/'signals.json',base/'source-protocol.json')
    if (result['source_manifest_sha256']!=REVISION_SHA or result['missing_net_values']!=52
            or result['missing_payment_dates']!=24 or result['execution_payment_rows']!=800
            or result['profit'] is not None or result['future_profit_projection'] is not None
            or result['new_historical_return_evaluations']!=0):
        raise ValueError('Unexpected source result')
    output=dest/'auditoria-fontes-14.json'
    with output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2,ensure_ascii=False);stream.write('\n')
    print(json.dumps({'source_audit':'VALIDATED','economic_status':result['status'],
        'output':str(output),'output_sha256':digest(output),'new_historical_return_evaluations':0}))
    return 0

if __name__=='__main__':raise SystemExit(main())
