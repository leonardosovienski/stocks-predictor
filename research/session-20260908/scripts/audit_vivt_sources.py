"""Verify acquired sources and isolate what the auction notice cannot establish."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--sources', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
requirements = {
    'cvm-corporate-0146': ['40 (quarenta)', '80 (oitenta)', '15 de abril de 2025', '13 de março de 2025'],
    'cvm-corporate-0147': ['19 de maio de 2025', '16 de maio de 2025'],
    'cvm-corporate-0148': ['949.354.168,17', '26,64196300439', '28 de maio de 2025', 'ganhos']}
sources = []
for name, fragments in requirements.items():
    pdf = args.sources/(name+'.pdf')
    metadata = json.loads(pdf.with_suffix('.pdf.source.json').read_text(encoding='utf-8'))
    data = pdf.read_bytes()
    assert data.startswith(b'%PDF')
    digest = hashlib.sha256(data).hexdigest()
    assert digest == metadata['sha256']
    extracted = pdf.with_suffix('.complete-text.json')
    text = ' '.join(' '.join(p['text'] for p in json.loads(extracted.read_text(encoding='utf-8'))).split())
    assert all(s in text for s in fragments)
    sources.append({'file': pdf.name, 'sha256': digest, 'url': metadata['url'],
        'extracted_text_sha256': hashlib.sha256(extracted.read_bytes()).hexdigest(),
        'source_integrity_and_relevant_terms_verified': True})

# Hypothetical holdings; no H19 wealth path or new return is observed.
quantity = 39
whole = quantity//40*80
auction_units = quantity*2-whole
fee_net = Decimal(auction_units)*Decimal('26.64196300439')
result = {'status': 'PHYSICAL_TERMS_VERIFIED_PERSONAL_NET_CASH_NOT_CERTIFIED',
    'sources': sources, 'real_action_approved_for_h19': False, 'new_historical_return_evaluations': 0,
    'quantity_example_is_hypothetical_not_the_h19_position': True,
    'original_quantity': quantity, 'delivered_whole_shares': whole, 'auction_units_after_split': auction_units,
    'proceeds_after_auction_fees_before_personal_tax_brl': str(fee_net),
    'hypothetical_original_basis_examples': [
        {'basis_brl': b, 'gain_before_personal_income_tax_brl': str(fee_net-Decimal(b)),
         'personal_income_tax_brl': None} for b in (1170, 1950, 2340)],
    'unresolved_source_fields': ['gross auction proceeds before expenses', 'auction expenses separately',
        'actual withholding allocated to this investor', 'exact custody credit and cent rounding',
        'complete portfolio basis and monthly trades/losses for the historical replay'],
    'dates': {'quantity_terms_announced': '2025-03-13', 'effective_ex_date': '2025-04-15',
              'auction_announced': '2025-05-16', 'auction_and_result_date': '2025-05-19',
              'announced_payment_deadline_not_individual_credit_certificate': '2025-05-28'},
    'interpretation': 'The issuer reports proceeds after auction expenses. That is insufficient for either gross monthly sales thresholds or personal net income tax. Do not substitute zero for the missing components.'}
args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
