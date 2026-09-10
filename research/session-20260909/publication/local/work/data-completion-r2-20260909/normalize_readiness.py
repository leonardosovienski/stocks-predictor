"""Build a source-readiness snapshot from preserved files; no prices or returns recomputed."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(r'C:\STOCKS')
REPO = ROOT / 'stocks-predictor'
WORK = ROOT / 'work/data-completion-r2-20260909'
PREV = ROOT / 'work/h21-source-closure-20260909'
OUT = WORK / 'normalized-v1'
OUT.mkdir(exist_ok=False)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


now = dt.datetime.now(dt.timezone.utc).isoformat()
captures = [json.loads(line) for line in (WORK / 'acquisition.jsonl').read_text(encoding='utf-8').splitlines()]
attempts = {x['id'] for x in captures if x['status'] == 'attempted'}
finals = {x['id']: x for x in captures if x['status'] != 'attempted'}
assert attempts == set(finals) and len(attempts) <= 140
files = []
pdfs = []
for item in finals.values():
    if item['status'] != 'downloaded':
        continue
    p = Path(item['path'])
    assert p.is_relative_to(ROOT) and p.stat().st_size == item['bytes'] and sha(p) == item['sha256']
    files.append(item)
    if p.suffix == '.pdf':
        reader = PdfReader(p)
        texts = [page.extract_text() or '' for page in reader.pages]
        pdfs.append({'path': str(p), 'sha256': sha(p), 'pages': len(texts),
                     'text_characters': sum(map(len, texts)), 'parse_status': 'PASS',
                     'interpretation': 'Extraction and hash verification alone do not certify financial completeness.'})
assert sum(x.get('bytes', 0) + x.get('partial_bytes', 0) for x in finals.values()) < 1_000_000_000

recovery = ROOT / 'data/recovery-r2'
db_catalog = read(recovery / 'catalog.json')
assert db_catalog['database_unique_objects'] == 12 and db_catalog['database_paths'] == 37
for d in db_catalog['databases']:
    assert d['inspection']['status'] == 'INTEGRITY_PASS' and sha(Path(d['local_path'])) == d['sha256']
restored_bytes = sum(p.stat().st_size for p in recovery.rglob('*') if p.is_file())
assert restored_bytes < 6_000_000_000
audits = read(WORK / 'reproduced-source-audits.json')['audits']
assert audits['13'] == read(recovery / 'bundles/source13/expected-audit.json')
assert audits['14']['missing_net_values'] == 52 and audits['14']['missing_payment_dates'] == 24
assert all(a['new_historical_return_evaluations'] == 0 for a in audits.values())

table_sources = []
for year, pdf, page, policy_page, start, end in [
    (2019, WORK/'raw/fnet-fs-2019.pdf',9,20,'2017-12-04','2019-03-31'),
    (2021, WORK/'raw/fnet-fs-2021.pdf',11,22,'2019-04-01','2021-03-31'),
    (2023, WORK/'raw/fnet-fs-2023.pdf',9,19,'2021-04-01','2023-03-31'),
    (2025, WORK/'raw/fnet-fs-2025.pdf',10,19,'2023-04-01','2025-03-31'),
    (2026, PREV/'raw/bova-fs-2026-retry.pdf',9,18,'2024-04-01','2026-03-31')]:
    table_sources.append({'statement_year':year,'path':str(pdf),'sha256':sha(pdf),
                          'evolution_pdf_page':page,'nav_distribution_policy_pdf_page':policy_page,
                          'fiscal_periods_from':start,'fiscal_periods_through':end,
                          'comparatives_included':True,'evolution_page_visually_reviewed':True,
                          'finding':'No separately reported cash amortization line in the reviewed evolution table. Portfolio dividends are internal NAV returns. Primary creation/redemption flows are not investor-wide events.'})
notice_meta = read(WORK/'bova-filing-metadata.json')
notices = []
seen = set()
fallbacks = {'1067482':WORK/'raw/bnp-102637.pdf','1058699':WORK/'raw/bnp-102385.pdf',
             '1045450':PREV/'raw/bova-merger-notice-retry.pdf'}
for item in notice_meta:
    id = item['urlFundosNet'].split('id=')[1]
    if id in seen:
        continue
    seen.add(id)
    candidates = [WORK/'raw'/f'fnet-{id}.pdf',WORK/'raw'/f'fnet-view-retry-{id}.pdf',WORK/'raw'/f'fnet-exibir-{id}.pdf']
    p = next((x for x in candidates if x.exists()), None)
    source_kind = 'FNET_ORIGINAL'
    if p is None and id in fallbacks:
        p = fallbacks[id]
        source_kind = 'OFFICIAL_ISSUER_EQUIVALENT_BODY_NOT_FNET_BYTE_EQUIVALENCE'
    status = 'RETAINED_DOCUMENT_NOT_EVENT_CERTIFICATE' if p else 'BODY_UNAVAILABLE'
    if 'Cancelado' in item['status']:
        status = 'REJECTED_CANCELLED_FILING'
    if id == '483971':
        status = 'REJECTED_CANCELLED_AND_WRONG_CNPJ_10406600000108'
    notices.append(dict(item,filing_id=id,local_path=str(p) if p else None,
                        sha256=sha(p) if p else None,source_kind=source_kind,review_status=status))
events = {'schema_version':1,'observed_at_utc':now,'ticker':'BOVA11','cnpj':'10406511000161',
          'basis':'Documentary source recovery, not economic revaluation or a complete event absence certificate',
          'annual_evolution_tables_cover_h21_start_through':'2026-03-31',
          'financial_statement_sources':table_sources,
          'specific_fy2024_pdf_status':'NOT_RECOVERED; 2024 evolution and comparative amounts available in original FY2025 statement',
          'official_annual_catalog':{'path':str(WORK/'fnet-financial-catalog-observed.json'),
                                     'sha256':sha(WORK/'fnet-financial-catalog-observed.json'),'records':8},
          'notice_catalog_count':len(notices),'notice_original_fnet_bodies':sum(n['source_kind']=='FNET_ORIGINAL' and n['local_path'] is not None for n in notices),
          'notice_official_equivalent_bodies':sum(n['source_kind'].startswith('OFFICIAL_ISSUER') for n in notices),
          'notice_bodies_unavailable':[n['filing_id'] for n in notices if n['local_path'] is None],
          'notices':notices,
          'public_fnet_cash_queries':{'kind':'PUBLIC_BROWSER_OBSERVATION_NOT_RAW_RESPONSE','observed_at_utc':now,
             'cnpj':'10406511000161','delivery_from':'2018-01-01','delivery_through':'2026-09-09','status_filter':'Todos',
             'types_filter_value':'0','category4_Aviso_aos_Cotistas_records':0,
             'category14_Aviso_aos_Cotistas_Estruturado_records':0,
             'limitation':'Zero records in these explicit categories. Does not exclude filings in other categories, omissions, pre-FNET documents or future rights.'},
          'merger_findings':{'meetings_not_installed':['2025-12-08','2025-12-22','2026-01-08'],
             'proposal_is_not_execution':True,'cash_or_units_from_this_proposal_booked':False},
          'structural_changes_documented':['2019-06 shareholder approval of lower fund fee and securities-lending limits',
             '2021-08-30 global annual fund fee reduced from 0.30% to 0.10%',
             '2025-04-23 CVM175 class and limited-liability adaptation',
             '2026-03-04 fee transparency link changes','2026-05-21 maximum custody fee disclosure; issuer states no additional cost'],
          'full_event_interval_certified':False,'cash_event_records_for_economic_use':None,'unit_event_records_for_economic_use':None,
          'remaining_scope':['2026-04-01/2026-09-08 continuous cash/unit event reconciliation and post-sale rights',
                             'FY2024 standalone original and 2025 AGO summary (941503) unavailable after tested official routes',
                             'Documentary inference must be separately reviewed before changing the frozen H21 economic inputs']}
write(OUT/'bova-event-review.json',events)

operational=read(REPO/'docs/research/2026-09-09-h21-operational-inputs.json')
operational['schema_version']=2
operational['reviewed_at_utc']=now
operational['previous_version']='docs/research/2026-09-09-h21-operational-inputs.json'
operational['events']['r2_review']='docs/research/2026-09-09-bova-event-review-r2.json'
operational['events']['financial_statement_evidence']=table_sources
operational['events']['full_interval_certified']=False
fee=WORK/'raw/b3-fees-177-2020.pdf'
operational['exchange_costs']['historical_documents']=[{
    'document':'B3 177/2020-PRE','path':str(fee),'sha256':sha(fee),
    'effective_from':'2021-02-02','repeal_reference':'017/2023-VPC, 2023-10-05; depositary annex separately repealed in2022',
    'secondary_equity_etfs_explicitly_included':True,'continuous_percent':'0.0300','auction_percent':'0.0320',
    'settlement_percent':'0.0250','regular_non_day_trade_retail':True,
    'coverage_limit':'Not applicable to2018 entry; not a complete historical fee/rounding/custody time series.'}]
operational['personal_profile']['account_channel_question_status']='ASKED_AWAITING_USER; no eligibility inferred'
write(OUT/'operational-inputs.json',operational)

databases=[]
for d in db_catalog['databases']:
    role='PRESERVED_RESEARCH_VERSION'
    if 'project/data/stocks.db' in d['original_aliases']:
        role='ORIGINAL_PROJECT_DATABASE_READ_ONLY_REFERENCE'
    if d['sha256'].startswith('071972'):
        role='REPAIRED_EXAMPLE_NOT_CANONICAL'
    if d['sha256'].startswith(('e713af','56c0c7','396f9a')):
        role='SMOKE_OR_TEST_FIXTURE_NOT_MARKET_DATA'
    tables={k:{q:v[q] for q in ('rows','date_ranges','distinct_tickers') if q in v}
            for k,v in d['inspection']['tables'].items() if k in ('prices_raw','cash_events','cash_event_coverage','fundamentals','fundamentals_pit','quarantine','adjustments')}
    databases.append({'sha256':d['sha256'],'path':d['local_path'],'original_aliases':d['original_aliases'],
                       'role':role,'integrity_status':'PASS','sqlite_open_policy':'mode=ro&immutable=1; all archived transaction journals were empty',
                       'tables':tables,'production_activation':False,'economic_completeness_certified':False})
price=PREV/'normalized-v2/quotes-2018-20260908.json'
assert sha(price)=='813a21aa335a84fb4288f125613dd3aab40b30d1c32a53e4e96c065431bc7adb'
readiness={'schema_version':1,'observed_at_utc':now,'local_project_root':str(ROOT),'all_data_ready':False,
           'ready_components':['All12 unique archived SQLite databases restored, hashes and integrity verified',
                               'Source13 and additive source14 datasets available and source audits reproduced',
                               'BOVA11 quote source:2159 observations through2026-09-08 (R1 unchanged)',
                               'Annual BOVA11 evolution tables cover fiscal periods2018 throughMarch2026 with original documents and comparatives'],
           'migration':{'archive':str(ROOT/'DADOS_STOCKS.zip'),'archive_sha256':db_catalog['archive_sha256'],
                        'database_paths':37,'unique_databases':12,'restored_unique_objects':db_catalog['restored_unique_objects'],
                        'recovery_total_bytes_including_copies_and_catalog':restored_bytes,'catalog_path':str(recovery/'catalog.json'),
                        'catalog_sha256':sha(recovery/'catalog.json'),'full_60023_path_tree_materialized':False},
           'databases':databases,
           'sources13_14':{'canonical13':str(recovery/'bundles/source13/inputs'),'additive14':str(recovery/'source14-inputs'),
                'canonical13_not_silently_replaced':True,'revision13_exact_audit_reproduction':True,
                'revision14_missing_payment_dates':24,'revision14_missing_net_payment_values':52,
                'corporate_event_inputs_pending':28,'required_intervals':1248,'fully_certified_intervals':0,
                'counts_overlap':True,'line':'H20 broad reconstruction remains parked',
                'audit_path':str(WORK/'reproduced-source-audits.json'),'audit_sha256':sha(WORK/'reproduced-source-audits.json')},
           'bova_quotes':{'path':str(price),'sha256':sha(price),'records':2159,'through':'2026-09-08',
                          'source_round':'R1 unchanged','new_economic_valuations':0},
           'bova_event_review':'docs/research/2026-09-09-bova-event-review-r2.json',
           'operational_inputs':'docs/research/2026-09-09-operational-inputs-r2.json',
           'remaining_external_or_research_dependencies':['Continuous ETF event/right reconciliation after2026-03-31',
              'Historical entry-date brokerage/B3 fees and actual broker fee bases/rounding',
              'XP account channel/adviser status and personal investment constraints',
              'Actual fills/spread/slippage require observed execution; no orders authorized',
              'Broad-stock history source gaps remain quantified under source14'],
           'economic_returns_recalculated':False,'original_economic_inputs_modified':False,'orders_or_broker_authentication':False,
           'acquisition_summary':{'jobs':len(attempts),'downloaded':len(files),'failed':len(attempts)-len(files),
                 'downloaded_bytes':sum(x['bytes'] for x in files),'retained_partial_bytes':sum(x.get('partial_bytes',0) for x in finals.values()),
                 'pdfs_parsed':len(pdfs),'journal_path':str(WORK/'acquisition.jsonl'),'journal_sha256':sha(WORK/'acquisition.jsonl')},
           'validation':{'local_auxiliary_python':'3.12.14','database_recovery_regressions_passed':9,
                         'production_ci':'Record exact commit/run in final delivery receipt; not inferred from local tests'},
           'normalization_revision':1,'frozen_hypotheses_preserved':True}
write(OUT/'readiness.json',readiness)
write(OUT/'source-inventory.json',{'observed_at_utc':now,'acquisitions':list(finals.values()),'pdf_structure_checks':pdfs})
for source,target in [('readiness.json','2026-09-09-data-readiness.json'),('bova-event-review.json','2026-09-09-bova-event-review-r2.json'),('operational-inputs.json','2026-09-09-operational-inputs-r2.json')]:
    dest=REPO/'docs/research'/target
    with dest.open('xb') as stream:stream.write((OUT/source).read_bytes())
write(ROOT/'data/CATALOG.json',readiness)
write(OUT/'SHA256.json',{p.name:sha(p) for p in OUT.iterdir() if p.is_file()})
print(json.dumps(readiness['acquisition_summary']))
