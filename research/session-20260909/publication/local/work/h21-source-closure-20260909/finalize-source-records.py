"""Seal documentary findings; never computes an investment return."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(r'C:\STOCKS\work\h21-source-closure-20260909')
REPO = Path(r'C:\STOCKS\stocks-predictor')
DOCS = REPO/'docs'/'research'
NOW = dt.datetime.now(dt.timezone.utc).isoformat()

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def write(path, obj):
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def source(name, pages=None):
    path = ROOT/'raw'/name
    receipt = json.loads(path.with_name(path.name+'.source.json').read_text(encoding='utf-8'))
    assert digest(path) == receipt['sha256'], name
    return dict(file=name, sha256=receipt['sha256'], url=receipt['url'], pages_pdf_1_based=pages)

journal = [json.loads(x) for x in (ROOT/'acquisition.jsonl').read_text(encoding='utf-8').splitlines()]
head = dict(id='b3-cotahist-head-recovery', status='head_verified', url='https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A2026.ZIP',
            observed_at_utc='2026-09-09T19:28:26Z', recorded_at_utc=NOW, record_kind='LATE_AUTHORED_RECEIPT_FROM_TOOL_OUTPUT',
            content_length=74185998, etag='"3ad8b333ef3fdd1:0"', last_modified='2026-09-09T00:07:28Z',
            note='One HEAD request used to recover exact missing range. Original header output was observed, not saved as raw source.')
assert head['id'] not in {r['id'] for r in journal}
with (ROOT/'acquisition.jsonl').open('a',encoding='utf-8') as stream:
    stream.write(json.dumps(head)+'\n')
journal.append(head)
latest = {r['id']:r for r in journal}
inventory=[]
wrong_scope = {'b3-bova-filings-all.json','b3-bova-class-filings-all.json'}
for identifier,r in latest.items():
    row = {k:r[k] for k in ('id','url','purpose','status','started_at_utc','completed_at_utc','http_status','error','bytes','partial_bytes','sha256') if k in r}
    path = Path(r['path']) if 'path' in r else None
    if path and path.is_file():
        row['local_relative_path'] = str(path.relative_to(ROOT)).replace('\\','/')
        row['bytes_on_disk'] = path.stat().st_size
        row['hash_verified'] = bool(r.get('sha256')) and digest(path)==r['sha256']
        if r.get('sha256'): assert row['hash_verified'], path
        row['content_acceptance'] = 'CAPTURED_NOT_A_COMPLETENESS_CERTIFICATE'
        if path.stat().st_size == 0: row['content_acceptance']='REJECTED_EMPTY_BODY'
        elif path.name == 'COTAHIST_A2026.latest.ZIP': row['content_acceptance']='REJECTED_TRUNCATED_ZIP_TRANSPORT_STATUS_NOT_ACCEPTANCE'
        elif path.name in wrong_scope or path.name.startswith('b3-filings-'): row['content_acceptance']='REJECTED_MULTIYEAR_QUERY_SILENT_EMPTY_RESULTS'
    else:
        row['content_acceptance']='NO_ACCEPTED_FILE'
    inventory.append(row)
reconciliation = json.loads((ROOT/'normalized-v2'/'reconciliation.json').read_text(encoding='utf-8'))
sources = dict(
    calendar=source('b3-calendar-2026.html'), quotes=source('COTAHIST_A2026.complete.ZIP'),
    b3_current_fees=source('b3-fees-v5.pdf',[9,11,19,20,33]),
    b3_previous_fees=source('b3-equities-fees-v4.pdf'), b3_current_spot=source('b3-fees-spot.html'),
    b3_current_lot_and_events=source('b3-bova-events.json'), b3_fund_classes=source('b3-bova-classes.json'),
    fs_2018=source('bova-fs-2018.pdf',[7]), fs_2026=source('bova-fs-2026-retry.pdf',[9,16,18,20]),
    rules_2021=source('bova-regulamento-legacy.pdf',[28]), rules_2026=source('bova-regulamento-2026.pdf',[19]),
    proposed_merger=source('bova-merger-notice-retry.pdf',[1,2]), merger_decision=source('bova-merger-decisions-3-retry.pdf',[1]),
    cvm_legacy_catalog=source('cvm-bova-fs-query.html'), b3_archived_statements=source('b3-bova-audited-docs.json'),
    b3_retail_program=source('b3-retail-program.pdf'))
profile = dict(
    schema_version=1, kind='DOCUMENTED_RESEARCH_INPUTS_NOT_BROKER_EXECUTION_CONFIGURATION',
    reviewed_at_utc=NOW, source_information_cutoff='2026-09-08',
    personal_profile=dict(broker_preference='XP', alternatives_allowed=True, compared_alternative='Rico',
                          horizon=None, maximum_acceptable_loss=None, actual_capital_brl=None,
                          account_channel=None, has_assessor=None, other_custodied_assets_brl=None,
                          capital_5000_10000_are_scenarios=True),
    instrument=dict(ticker='BOVA11', isin='BRBOVACTF003', cnpj='10406511000161', b3_fund_id=990,
                    b3_class_id=19674, current_secondary_trading_lot=1, original_h21_lot=10,
                    historical_lot_change_effective_date=None, original_lot_preserved=True),
    broker_comparison=dict(
        xp=dict(url='https://www.xpi.com.br/custos-operacionais/', evidence_kind='PUBLIC_BROWSER_OBSERVATION_AND_WEB_TEXT_NOT_RAW_HTML',
                secondary_bova11_brokerage_brl=None, conditional_listed_funds_selfservice_brokerage_brl='0.00',
                condition='Page Fundos Listados: independent client without adviser; ETF mapping and account eligibility not certified.',
                own_exchange_custody_brl='0.00', operational_surcharge_percent='5.9',
                surcharge_base='Brokerage, emoluments and settlement fee; mapping of current CCP/transfer nomenclature to actual note remains to reconcile.',
                primary_creation_redemption_only=dict(percent='0.04', fixed_brl_per_request='276.09', applies_to_secondary_trade=False),
                taxes_percent=dict(ISS='5',PIS='0.65',COFINS='4'), full_cost_certified=False),
        rico=dict(url='https://www.rico.com.vc/custos/', evidence_kind='PUBLIC_BROWSER_OBSERVATION_AND_WEB_TEXT_NOT_RAW_HTML',
                  explicit_etf_selfservice_brokerage_brl='0.00', condition='Orders placed by client on digital platforms; desk/assessor conditions excluded.',
                  etf_zero_requires_rlp_in_observed_row=False, operational_surcharge_percent='5.9',
                  surcharge_base='Brokerage, emoluments and settlement fee; note-level mapping remains to reconcile.',
                  taxes_percent=dict(ISS='5',PIS='0.65',COFINS='4'), taxes_method='gross-up on brokerage and operating fees per published page',
                  same_xp_group=True, full_cost_certified=False),
        decision='Keep XP preference. Rico is a conditional fee alternative if actual XP ETF brokerage is positive; no general superiority or switch concluded.'),
    exchange_costs=dict(
        schedule='B3 equities V5.0', effective_from='2026-09-01', valid_until=None,
        scope='Regular non-day-trade BOVA11, first monthly investor ADTV bracket through BRL 3 million; no incentive enrollment assumed.',
        units='Percent of financial volume PER SIDE; not fraction, not round trip, and not full transaction cost.',
        continuous=dict(negotiation_percent='0.00500',ccp_percent='0.02240',transfer_percent='0.00260',b3_total_percent='0.03000'),
        opening_closing_auction=dict(negotiation_percent='0.00700',ccp_percent='0.02240',transfer_percent='0.00260',b3_total_percent='0.03200'),
        transfer_basis='Current spot page 0.00260%; annual market-wide non-day ADTV mechanism, not account ADTV.',
        rounding='V5 section1.4: consolidate at stated precision, allocate by price/phase proportions, daily fee-type totals truncated to cents; no order-level approximation promoted as exact.',
        retroactive_application_to_2018_prohibited=True, historical_fee_schedule_complete=False,
        custody=dict(exemption_if_aggregate_brl_below='26471.77', aggregation='All accounts of same investor document at same custodian',
                     progressive_first_bracket_annual_percent='0.0500', first_bracket_ceiling_brl='115000.00',
                     actual_account_exemption_confirmed=False, actual_cost_brl=None),
        retail_relationship_program_20260908='Futures only; no BOVA11 spot discount applied.'),
    execution_unknowns=['Actual spread/slippage and opening auction fills','Broker note fee bases and rounding','Current XP ETF category/eligibility','Historical fee schedules for original book','User tax offsets/other operations and post-sale rights'],
    fund_internal_costs=dict(current_global_fee_annual_percent='0.10', source='fs_2026 note10',
                             treatment='Already charged inside fund NAV; do not subtract again from observed ETF prices as a second management charge.'),
    events=dict(
        full_interval_certified=False, cash_events=None, unit_adjustment_events=None, post_sale_rights_certified=False,
        empty_b3_event_response='No cash/stock/subscription entries returned; response has no explicit historical retention window and is insufficient to certify absence.',
        policy='FS2026 note14 incorporates results in NAV; fund portfolio dividends are not additional investor cash distributions.',
        amortization_permission='Legacy article34 and current6.6 permit proportional cash amortization without reducing units. Current6.7 also permits compulsory redemption; permissions do not prove occurrences.',
        financial_statement_evidence=[
            dict(source='fs_2018', intervals=['2017-12-04/2018-03-31','2017-04-01/2017-12-01','year ended 2017-03-31'], result='No separate amortization line in evolution table; creations/redemptions are primary-market fund flows, not forced changes to each secondary holder.'),
            dict(source='fs_2026', intervals=['2025-04-01/2026-03-31','comparative 2024-04-01/2025-03-31'], result='No separate amortization line in evolution table; note8 permits it. Limited documentary support, not full historical absence certificate.')],
        merger=dict(proposal_document_date='2025-11-24', proposed_absorbed_fund_cnpj='11455378000104',
                    final_notice_body_date='2026-01-21', meeting_date='2026-01-08', result='MEETING_NOT_INSTALLED_NO_WRITTEN_VOTES',
                    executed_merger_proven=False, applied_unit_adjustment=None),
        known_regulatory_changes=[dict(effective_date='2025-04-23',kind='CVM175 adaptation'),dict(effective_date='2026-03-04',kind='ANBIMA fee transparency'),dict(effective_date='2026-05-21',kind='Maximum custody fee disclosure')],
        unresolved=['Continuous annual originals April2018-March2024','Fund/class filings not all read in full','April2026-cutoff actual cash/rights coverage','Historical lot effective date','Rights after original sale']),
    source_discrepancies=[
        'Legacy regulation labeled 20May2024 on issuer page has 30Aug2021 in PDF; body date retained.',
        'Third merger decision label 23Dec2025 differs from actual21Jan2026 PDF and FNET delivery21Jan2026.',
        'November2025 incorporation call contains internally inconsistent 2025 effective/third-call dates; no silent correction or execution date inferred.',
        'CVM pre-July2018 catalog returns2017/2018 only due publication-system migration; not absence of later reports.',
        'Multiyear B3 filing query returned empty while correct annual scope returns known filings; those empty responses rejected.'],
    source_review_notes='FS2026 signed/approved29May2026; issuer availability14Aug2026. Publication/reference/acquisition dates are distinct. Marketing tables and FS performance were incidentally observed; no intact holdout.',
    ready_for_full_net_backtest=False, executable_full_net_profit=None, expected_future_profit=None,
    new_economic_variants=0, new_economic_valuations=0, original_h21_book_changed=False,
    sources=sources)
write(DOCS/'2026-09-09-h21-operational-inputs.json', profile)
write(DOCS/'2026-09-09-h21-source-inventory.json', dict(
    kind='SOURCE_CAPTURE_AND_VALIDATION_RECEIPT', generated_at_utc=NOW, local_root=str(ROOT),
    direct_capture_attempts_including_late_head=len(latest),
    request_counter_scope='Direct acquisition jobs plus one HEAD; browser/search discovery and redirects are not counted. This is not a bound on every HTTP request.',
    total_retained_transport_bytes=sum(r.get('bytes',0)+r.get('partial_bytes',0) for r in latest.values()),
    source_normalization_revisions=2, failed_truncated_attempt_accepted=False,
    original_h21_protocol_sha256=digest(DOCS/'2026-09-09-h21-protocol.json'),
    original_h21_result_sha256=digest(Path(r'C:\STOCKS\work\h21\result-01.json')),
    final_quote_reconciliation=reconciliation, exact_assembled_source=sources['quotes'],
    attempts=inventory))
write(ROOT/'browser-observations.json', dict(kind='AUTHORED_OBSERVATION_RECEIPT_NOT_ORIGINAL_HTML', recorded_at_utc=NOW,
    browsing_date='2026-09-09', brokers=profile['broker_comparison'],
    access='Public pages only; direct curl403 but ordinary browser usable; no broker login, messages, orders, or enrollment.',
    methodological_note='No machine-preserved original broker HTML. Observed UI used to disambiguate tabs flattened in web extraction.',
    incidental_performance_exposure=True, holdout_intact=False))
write(ROOT/'visual-review.json',dict(reviewed_at_utc=NOW,method='pypdf extraction plus pdftoppm visual inspection',
    font_render_warnings='Poppler Symbol/ArialUnicode font warnings retained; reviewed table numbers and relevant paragraphs readable.',
    pages=[dict(path=str(p.relative_to(ROOT)).replace('\\','/'),sha256=digest(p)) for p in (ROOT/'visual-qa').glob('*.png')],
    unsupported_claims_rejected=['Empty event response proves no events','Merger subject means completed merger','Primary ETF creation fee applies to ordinary purchase','Brokerage zero means total cost zero']))
print(json.dumps(dict(attempts=len(latest), bytes=sum(r.get('bytes',0)+r.get('partial_bytes',0) for r in latest.values()), reconciliation=reconciliation, data_work_closed_at_utc=NOW)))
