"""Apply two individually reviewed B3 credit records to a new source revision."""
from datetime import date, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil
import sys

repo = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(repo))
from stocks_predictor.source_closure import audit

root = Path('C:/STOCKS')
work = root/'work/gap-resolution-r6-20260910'
parent = root/'data/recovery-r2/source14-inputs'
target = work/'source15-inputs'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


parent_sha = digest(parent/'SHA256.json')
if parent_sha != '3b36e2416e44f2b0a30e88d4306e00cdc74a7302c6e9b0e33950a893ea169bda':
    raise ValueError('Changed source14 manifest')
for name, expected in read(parent/'SHA256.json').items():
    if digest(parent/name) != expected:
        raise ValueError('Changed source14 file: '+name)
shutil.copytree(parent,target)
cash = read(target/'cash-events.json')
catalog = read(target/'primary-catalog.json')
tax_source = next(r['tax_source'] for r in cash if r.get('net_rule') == 'RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION' and r['action'] == 'DIVIDENDO')
patches = [
    ('BRRECVACNOR3:2024-04-25:DIVIDENDO:8','2024-05-15','0.05928343241','bdi-2024-05-15-ch05.pdf',9,'294e9456a56ca7923875515c91ae362862a24108138f09b2467eb9445776720b'),
    ('BRRADLACNOR0:2024-04-18:DIVIDENDO:13','2024-05-31','0.049150927','bdi-2024-05-31-ch05.pdf',5,'9afdb7a78f0f41259daa2f85f70725e5fa52484e534a5ebd907edc7853f9f6bf'),
]
changes = []
for event_id, payment_date, gross, name, page, sha in patches:
    row = next(r for r in cash if r['event_id'] == event_id)
    if row['payment_date'] is not None or row['net_per_share'] is not None or Decimal(row['gross_per_share']) != Decimal(gross):
        raise ValueError('Unexpected parent event state')
    source = work/'raw-04'/name
    receipt = read(source.with_suffix('.pdf.receipt.json'))
    if digest(source) != sha or receipt['sha256'] != sha:
        raise ValueError('Changed B3 credit source')
    key = 'primary/'+sha+'-'+name
    shutil.copyfile(source,target/key)
    catalog[key] = {'sha256':sha,'source_kind':'PRIMARY_SOURCE_RECORD','url':receipt['url'],
                    'source_file':name,'captured_at_utc':receipt['completed_at_utc']}
    prior_candidate = row.get('unresolved_payment_evidence')
    row.update(payment_date=payment_date,net_per_share=gross,source_review=True,
               # The acquisition is observed now. Do not invent historical publication.
               known_on='2026-09-10',available_on=(date.fromisoformat(payment_date)+timedelta(days=1)).isoformat(),
               tax_source=tax_source,net_rule='RESIDENT_PF_PRE_2026_ORDINARY_DISTRIBUTION',
               actual_broker_cent_rounding_not_verified=True,
               historical_publication_time_verified=False,
               payment_evidence_kind='B3_REPORTED_CREDIT_RECONSTRUCTED_LATER',
               source_observed_at_utc=receipt['completed_at_utc'])
    row['sources'] = row.get('sources',[]) + (prior_candidate or {}).get('sources',[]) + [
        {'file':name,'sha256':sha,'url':receipt['url'],'pages':[page],'verified_primary_file':key}]
    if prior_candidate:
        row['resolved_prior_payment_candidate'] = row.pop('unresolved_payment_evidence')
    changes.append({'event_id':event_id,'payment_date':payment_date,'net_per_share':gross,
                    'primary_sha256':sha,'page':page,'historical_pit_certified':False})
write(target/'cash-events.json',cash)
write(target/'primary-catalog.json',catalog)
revision = read(target/'source-revision.json')
revision.update(parent_source_manifest_sha256=parent_sha,revision=15,
                r6_changes=changes,complete_inventory_certified=False)
revision['counts'].update(missing_payment_after=22,missing_net_after=50)
write(target/'source-revision.json',revision)
write(target/'r6-review.json',{'changes':changes,'reviewed_by':'same research assistant, not an external auditor',
     'scope':'Historical payment accounting; the two later-acquired sources do not certify historical signal availability.'})
manifest = {p.relative_to(target).as_posix():digest(p) for p in sorted(target.rglob('*')) if p.is_file() and p.name != 'SHA256.json'}
write(target/'SHA256.json',manifest)
source13 = root/'data/recovery-r2/bundles/source13'
result = audit(source13/'baseline',target,source13/'signals.json',source13/'source-protocol.json')
write(work/'source15-audit.json',result)
write(work/'source15-changes.json',{'parent_manifest_sha256':parent_sha,'manifest_sha256':digest(target/'SHA256.json'),'changes':changes})
print(json.dumps({k:result[k] for k in ('status','missing_payment_dates','missing_net_values','verified_primary_files','issue_counts')},indent=2))
