from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT/'work/stocks-predictor'
P = {
    'protocol_id': 'H18-H19-DISCOVERY-DISCLOSED-CAPITAL-1',
    'registered_at_utc': datetime.now(timezone.utc).isoformat(),
    'phase': 'DISCOVERY',
    'candidate_results_observed_before_registration': False,
    'previous_shared_price_history_exposed': True,
    'untouched_historical_holdout_claim': False,
    'reason_for_revision': 'User authorizes changes. Test an explicitly stale observable valuation proxy before paying for exact dynamic capitalization and full return reconstruction.',
    'fixed_trials_in_order': [{'family': f, 'holding_months': h} for f,h in [('H18',1),('H18',3),('H19',1),('H19',3)]],
    'hypothesis': {'H18': 'Higher consolidated earnings attributable to parent shareholders divided by disclosed-capital price proxy predicts higher subsequent price returns.',
                   'H19': 'Higher consolidated equity net of noncontrolling interests divided by disclosed-capital price proxy predicts higher subsequent price returns.'},
    'source_universe': 'Existing 96 PIT CNPJ-deduplicated monthly top-60 snapshots, January 2018 through December 2025. No current-provider survival screen.',
    'source_metadata': 'Exact CNPJ, fiscal date, DFP version, original receipt date and document id. Both FCA security and DFP already public by signal; date-only receipt usable the next calendar day.',
    'capital': 'Original CVM document capital HTML, own Unidade or Mil scale, issued minus treasury ordinary shares. Preferred issued shares must equal zero. Unknown capital/treasury remains missing.',
    'accounting': 'Consolidated DRE unique parent-company attribution below net income; BPP consolidated equity root minus explicit NCI. No individual-statement, obsolete-version or zero fallback. Monetary amounts in BRL. Annual earnings duration 330 through 400 days.',
    'capital_proxy': 'Reported outstanding ordinary shares divided by product of mechanical price adjustment factors with fiscal_date < ex_date <= signal, multiplied by raw signal close normalized by quote factor.',
    'proxy_limitations': ['Not exact live market capitalization; buybacks and unrecorded issuances after the fiscal date are not fully covered.',
                          'Known intervening unsupported capital events, factor conflicts and unexplained adjusted overnight moves over 30% cause causal feature abstention.',
                          'Corporate-action archives acquired today are retrospective reconstructions; date filtering is not a complete historical publication audit.',
                          'Treasury and financial numerators may be stale; rounded share disclosures retain their precision.',
                          'Price screens omit dividends, JCP, taxes, cash payment timing, execution sizing and a cash-rate opportunity benchmark.'],
    'causal_eligibility': {'report_max_age_days': 550, 'median_daily_volume_min_brl': 1000000,
                           'same_ordinary_ISIN_from_fiscal_date_to_signal': True,
                           'fiscal_date_prior_quote_max_calendar_days': 10, 'minimum_factor_names': 20},
    'portfolio': 'Highest floor(N/5) signed ratios, equal weights, ties by ascending ticker. Cohort universe benchmark equal weights over every eligible factor name.',
    'execution_intervals': 'Signal at month end, enter first market open strictly after signal, exit first market open after the end of month signal_month+holding_months. Quarterly signals March/June/September/December.',
    'outcomes': 'Reuse corrected H17 price measurement: splits/groups/bonus mathematical units; no cash returns. Exact entry/exit quotes and instrument continuity required. Unsupported noncash actions and unexplained adjusted overnight moves >30% stay missing.',
    'missingness': 'Keep every selected and unselected member. Report available-case IC and complete-period spread as conditional statistics. Additionally evaluate all eligible periods with missing selected returns -100%, missing other returns +100%; identical assigned outcome in strategy and benchmark. This is an adverse scenario, not a mathematical bound; upside is unbounded.',
    'cost_scenarios': 'Subtract 36bp and stress 72bp from cohort spread per holding period; benchmark incremental cost treated as zero, conservatively. Haircuts are hurdles, not calibrated executable net P&L. Divide arithmetic spread by holding months only for comparability.',
    'resource_decision_rule': {'minimum_periods': '36 monthly or 12 quarterly, and >=12 monthly or >=4 quarterly in each fixed half',
                               'fixed_halves': ['2018-2021','2022-2025'],
                               'stability': 'Positive available-case mean IC and positive mean adverse-missing spread after 72bp in BOTH fixed halves',
                               'materiality': 'Overall adverse-missing mean spread after 72bp >=0.0042 per month equivalent',
                               'economic_scale': '0.42%/month is an approximate R$500/year incremental research hurdle on R$10k, not a forecast. User only confirmed R$5-10k capital; profit floor and maintenance budget remain unconfirmed.',
                               'pass': 'PRIORITIZE_TOTAL_RETURN_AND_EXECUTION_REPAIR',
                               'fail': 'NO_PRIORITY_UPGRADE, or INSUFFICIENT_DISCOVERY_COVERAGE; neither proves absence of total-return edge'},
    'search_budget': {'previous_legacy_candidates_minimum': 15, 'previous_H17_candidates': 1,
                      'previous_observed_return_evaluations_minimum': 17, 'new_configurations': 4,
                      'nominal_configurations_after_minimum': 20, 'observed_evaluations_after_minimum': 21,
                      'active_discovery_families': ['H18','H19'], 'proof_trials': 0,
                      'unknown_historical_adaptive_search': True, 'frequency_variants_are_counted': True,
                      'post_result_parameter_tuning_authorized_by_this_protocol': False},
    'input_sha256': {}
}
inputs = [ROOT/'work/h17-run-pack-v2/data'/p for p in ('quotes.db','snapshots.json','events.json')]
inputs += sorted((ROOT/'work/h17-run-pack-v2/data/identity').glob('identity-*.jsonl'))
inputs += [ROOT/'work/value-capital-source'/p for p in ('acquisition-retried.json','accounting-v2.json')]
for path in inputs:
    with path.open('rb') as stream:
        P['input_sha256'][str(path.relative_to(ROOT)).replace('\\','/')] = hashlib.file_digest(stream,'sha256').hexdigest()
path = REPO/'docs/research/2026-09-07-value-discovery-protocol.json'
with path.open('x',encoding='utf-8') as stream:
    json.dump(P,stream,ensure_ascii=False,indent=2)
sha = hashlib.sha256(json.dumps(P,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
module = REPO/'stocks_predictor/discovery_value.py'
text = module.read_text(encoding='utf-8')
assert text.count('PENDING_REGISTRATION') == 1
module.write_text(text.replace('PENDING_REGISTRATION',sha),encoding='utf-8')
shutil.copy2(ROOT/'outputs/REVISAO_H1_H16_APOS_CORRECOES.json',REPO/'docs/research/2026-09-07-prior-hypotheses-review.json')
print(sha)
