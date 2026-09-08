"""Replay explicit primary-notice reviews; never infer dates from deadlines."""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'work/h19-cash-expanded-source'
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
queue = read(ROOT / 'outputs/H19_CAIXA_FILA_DE_VALIDACAO.json')['cash_queue']
indexes = [d for suffix in ('selected', 'later', 'followup') for d in read(BASE / f'ipe-{suffix}-notices.json')]
index = {d['local_file']: d for d in indexes}

# This table is the review decision, not a generic date extractor. Each row
# identifies the exact B3 economic key; notices with several payments are split.
# Values are compared with decimal boundaries, not substring search.
REVIEW = '''
notice-0001|BRML3|2018-11-27|2018-12-07
notice-0002|BRML3|2018-12-26|2019-01-10
notice-0003|EMBR3|2018-12-27|2019-01-11
notice-0005|VLID3|2018-09-27|2018-10-11
notice-0017|BRML3|2019-03-29|2019-05-31
notice-0018|BRML3|2019-08-08|2019-08-19
notice-0023|CAML3|2019-07-02|2019-07-16
notice-0024|CAML3|2019-09-03|2019-09-12
notice-0031|CIEL3|2020-12-30|2021-02-17
notice-0035|TIMP3|2020-01-20|2020-01-29
notice-0048|CIEL3|2021-02-02|2021-02-17
notice-0049|CIEL3|2021-05-03|2021-05-13
notice-0050|CIEL3|2021-08-06|2021-08-19
notice-0051|CIEL3|2021-11-09|2021-11-26
notice-0057|JHSF3|2021-04-05|2021-04-12
notice-0058|JHSF3|2021-10-15|2021-10-25
notice-0060|EZTC3|2021-04-30|2021-05-21
notice-0061|MRVE3|2021-01-19|2021-01-28
notice-0062|MRVE3|2021-04-30|2021-05-11
notice-0063|MRVE3|2021-12-07|2021-12-16
notice-0066|CAML3|2021-09-02|2021-09-13
notice-0067|HGTX3|2021-04-30|2021-05-26
notice-0076|VIVT3|2022-04-27|2022-10-18
notice-0081|MDIA3|2022-06-17|2022-06-30
notice-0100|CIEL3|2023-11-08|2023-11-23
notice-0124|CIEL3|2024-03-18|2024-04-30
notice-0129|ANIM3|2024-08-14|2024-08-21
notice-0130|PETZ3|2024-05-02|2024-05-27
notice-0142|ALOS3|2025-01-24|2025-02-04
notice-0145|ALOS3|2025-03-24|2025-04-02
notice-0148|ALOS3|2025-06-18|2025-07-02
notice-0152|AZZA3|2025-11-24|2025-12-01
notice-0154|AURE3|2025-04-25|2025-05-05
notice-0155|MGLU3|2025-04-28|2025-05-05
later-0000|CSMG3|2018-09-25|2018-11-16
later-0001|CSMG3|2019-03-27|2019-05-20
later-0002|CSMG3|2019-06-24|2019-08-13
later-0004|CSMG3|2020-03-26|2020-05-19|0.3597155687
later-0005|CSMG3|2020-06-24|2020-08-17
later-0006|CSMG3|2020-09-23|2020-11-16
later-0008|HGTX3|2020-07-07|2020-11-18
later-0012|NEOE3|2022-01-06|2022-03-30
later-0016|VIVT3|2022-05-02|2023-04-18
later-0016|VIVT3|2022-07-01|2023-04-18
later-0016|VIVT3|2023-01-02|2023-04-18|0.42980199393
later-0016|VIVT3|2023-01-02|2023-07-18|0.60112166983
followup-0000|LIGT3|2019-04-30|2019-12-20
followup-0001|ENBR3|2019-01-02|2019-07-01
followup-0001|ENBR3|2019-04-17|2019-07-01
followup-0005|ENBR3|2020-01-02|2020-09-23
followup-0005|ENBR3|2020-04-01|2020-09-23
followup-0010|LIGT3|2021-04-30|2021-07-30
followup-0029|ENBR3|2022-04-06|2022-05-27
followup-0032|MYPK3|2021-12-28|2022-03-23
followup-0035|CYRE3|2022-04-25|2022-12-14
followup-0051|CYRE3|2023-05-03|2023-08-21
followup-0091|MOVI3|2024-12-30|2025-05-02
'''

def key(row):
    return row['ticker'], row['ex_date'], row['action'], str(Decimal(row['value_per_share']).normalize())

facts = {}
warnings = []
for line in REVIEW.strip().splitlines():
    parts = line.split('|')
    name, ticker, ex, pay = parts[:4]
    pdf = BASE / f'cvm-{name}.pdf'
    pages = read(pdf.with_suffix('.extracted.json'))
    text = ' '.join(' '.join(p['text'].split()) for p in pages)
    # Truncation allowance is bounded by the final reported B3 decimal place;
    # e.g. BRML notices retain more decimals than the B3 history.
    tokens = [(m.group(), Decimal(m.group().replace(',', '.'))) for m in
              re.finditer(r'(?<![\d.,])\d+[.,]\d+(?!\d|[.,]\d)', text)]
    rows = [r for r in queue if r['ticker'] == ticker and r['ex_date'] == ex
            and (len(parts) == 4 or Decimal(r['value_per_share']) == Decimal(parts[4]))]
    if not rows:
        warnings.append({'review': line, 'issue': 'not in frozen queue; not added'})
    for row in rows:
        value = Decimal(row['value_per_share'])
        tolerance = Decimal(1).scaleb(value.as_tuple().exponent)
        matches = [raw for raw, v in tokens if abs(v - value) < tolerance]
        if not matches:
            warnings.append({'review': line, 'issue': 'amount not extracted; not added', 'value': str(value)})
            continue
        metadata = read(pdf.with_suffix('.pdf.source.json'))
        assert sha(pdf) == metadata['sha256']
        k = key(row)
        fact = dict(ticker=ticker, isin=row['isin'], ex_date=ex, last_cum=row['last_cum'],
                    action=row['action'], value_per_share=row['value_per_share'], payment_date=pay,
                    payment_date_reviewed=True, review_method='PRIMARY_NOTICE_SPECIFIC_PAYMENT_DATE',
                    sources=[{'file': pdf.name, 'sha256': sha(pdf), 'url': metadata['url'],
                              'amount_tokens': matches, 'pages': [p['page'] for p in pages if any(m in p['text'] for m in matches)]}],
                    interval_complete=False, net_per_share=None,
                    source_review_scope='Reviewed payment declaration and matching amount; not proof of actual broker receipt or complete interval.')
        if k in facts and facts[k]['payment_date'] != pay:
            raise ValueError(f'conflicting approved payment {k}')
        facts[k] = fact

def reviewed_extra(ticker, ex, value, pay, files, note, **extra):
    rows=[r for r in queue if r['ticker']==ticker and r['ex_date']==ex and Decimal(r['value_per_share'])==Decimal(value)]
    assert len(rows)==1
    row=rows[0]
    facts[key(row)]={k:row[k] for k in ('ticker','isin','ex_date','last_cum','action','value_per_share')}
    sources=[]
    for name, page in files:
        p=BASE/name; meta=read(p.with_suffix('.pdf.source.json'))
        assert sha(p)==meta['sha256']
        sources.append({'file':name,'page':page,'sha256':sha(p),'url':meta['url']})
    facts[key(row)].update(payment_date=pay,payment_date_reviewed=True,
        review_method='EXPLICIT_CROSS_DOCUMENT_OR_VISUAL_REVIEW',sources=sources,
        interval_complete=False,net_per_share=None,source_review_scope=note,**extra)

reviewed_extra('EZTC3','2022-03-23','0.460337585','2022-03-31',
    [('eztec-2022-proposal.pdf',3)],'Page 3 states amount, record date, ex date and 31 March payment, superseding the initial deadline.')
reviewed_extra('EZTC3','2022-05-18','0.11269711721','2022-05-31',
    [('eztec-2023-proposal.pdf',6),('cvm-notice-0088.pdf',1)],
    'Paid-date table rounds the amount to nine decimals; final amount comes from the explicit 25 May correction and B3, not from the rounded table.')
reviewed_extra('EZTC3','2022-08-17','0.09050459394','2022-08-31',
    [('eztec-2023-proposal.pdf',6)],
    'Paid-date table identifies the 11 August declaration and displays a truncated nine-decimal amount; amount remains the B3 value and is not certified exact by this table alone.')
for ex, gross, net in [('2023-08-01','0.24425856212','0.2076197781'),
                       ('2023-09-01','0.15997040299','0.13597484254'),
                       ('2023-09-25','0.12073237961','0.10262252267')]:
    reviewed_extra('VIVT3',ex,gross,'2024-04-23',[('cvm-later-0019.pdf',1)],
        'Scanned primary table visually reviewed on rendered page 1: gross/net/record dates and payment. Text extraction is empty; values are explicit transcription.',
        net_per_share_reported=net,net_amount_reviewed=True)

# Keep strong RI rows, but never silently promote weak undated amount matches.
ri = read(BASE / 'reconciliation.json')
for row in ri['reconciled_queue_rows']:
    if not row['evidence']['dated_amount_reconciled'] or key(row) in facts:
        continue
    source = row['evidence']['source_file']
    facts[key(row)] = dict(ticker=row['ticker'], isin=row['isin'], ex_date=row['ex_date'],
        last_cum=row['last_cum'], action=row['action'], value_per_share=row['value_per_share'],
        payment_date=row['payment_date'], payment_date_reviewed=True,
        review_method='B3_AND_DATED_RI_ROW', sources=[{'file': source, 'sha256': sha(BASE / source),
        'row': row['evidence']['source_row'], 'url': read((BASE / source).with_suffix(Path(source).suffix + '.source.json'))['url']}],
        interval_complete=False, net_per_share=None, source_review_scope='Payment date/amount reconciliation only.')

pilot = read(ROOT / 'outputs/H19_CAIXA_PRIMEIRAS_CORRECOES.json')
for row in pilot['bbas_newly_resolved_cash_cells']:
    facts[key(row)] = {k: row[k] for k in ('ticker', 'isin', 'ex_date', 'last_cum', 'action', 'value_per_share', 'payment_date')}
    facts[key(row)].update(payment_date_reviewed=True, review_method='PRIOR_IMMUTABLE_BBAS_PILOT',
        sources=[{'file':'H19_CAIXA_PRIMEIRAS_CORRECOES.json', 'sha256':sha(ROOT/'outputs/H19_CAIXA_PRIMEIRAS_CORRECOES.json')}],
        interval_complete=False, net_per_share=None, source_review_scope='Preserves prior pilot distinctions between gross and monetary update.')

prior_matches = [json.loads(line) for line in (ROOT/'outputs/cash-source-matches.jsonl').read_text(encoding='utf-8').splitlines()]
for row in queue:
    if key(row) in facts: continue
    matches = [m for m in prior_matches if m.get('reconciliation')=='MATCHED' and key(m)==key(row)]
    if len(matches)!=1: continue  # Installments need their own complete entitlement schedule.
    match=matches[0]
    source=ROOT/'work/source-acquisition'/match['source_file']
    assert sha(source)==match['source_sha256']
    facts[key(row)]={k:row[k] for k in ('ticker','isin','ex_date','last_cum','action','value_per_share')}
    facts[key(row)].update(payment_date=match['payment_date'],payment_date_reviewed=True,
        review_method='PRIOR_EXACT_DATED_RI_RECONCILIATION',
        sources=[{'file':source.name,'sha256':sha(source),'url':match['source_url'],'locator':match['locator']}],
        interval_complete=False,net_per_share=None,source_review_scope='Preserves prior reconciled dated row; no full-interval certification.')

rows = []
for row in queue:
    fact = facts.get(key(row))
    weak = [m['payment_date'] for m in ri['reconciled_queue_rows'] if key(m)==key(row)
            and not m['evidence']['dated_amount_reconciled']]
    rows.append({**row, 'reviewed_payment': fact, 'payment_date_reviewed': fact is not None,
                 'candidate_payment_dates': sorted(set(row['candidate_payment_dates']) |
                    set(weak) | ({fact['payment_date']} if fact else set())),
                 'weak_ri_candidate_dates':weak})
count = Counter()
for r in rows:
    count['queue_rows'] += 1
    count['selected_rows'] += r['selected']
    count['reviewed_payment_rows'] += r['payment_date_reviewed']
    count['selected_reviewed_payment_rows'] += r['selected'] and r['payment_date_reviewed']
    count['without_candidate_date'] += not r['candidate_payment_dates']
    count['selected_without_candidate_date'] += r['selected'] and not r['candidate_payment_dates']
result = dict(schema='H19_REVIEWED_PAYMENT_DATES_1', summary=dict(count), facts=list(facts.values()), cash_queue=rows,
    warnings=warnings, source_conflicts=ri['source_conflicts'], new_historical_return_evaluations=0,
    includes_full_successor_cash=False, includes_new_jbs_events=False, full_cash_coverage_verified=False,
    negative_control={'ticker':'COGN3','ex_date':'2025-12-26','amount':'0.04858806025',
       'declared_payment_date':'2028-12-20','source':'cvm-notice-0140.pdf','page':3,
       'note':'Unpaid at test end; amount described as estimated. No immediate cash or final amount certification.'},
    reviewed_input_sha256={'queue':sha(ROOT/'outputs/H19_CAIXA_FILA_DE_VALIDACAO.json'),
                           'prior_pilot':sha(ROOT/'outputs/H19_CAIXA_PRIMEIRAS_CORRECOES.json')})
result['installment_schedule_reviews']=[dict(ticker='ALSO3',isin='BRALSOACNOR5',ex_date='2023-05-02',
    last_cum='2023-04-28',action='DIVIDENDO',declared_total_per_share='0.51901441592',
    installments=[{'number':1,'gross_per_share':'0.25950720796','payment_date':'2023-05-24'},
                  {'number':2,'gross_per_share':'0.25950720796','payment_date':'2023-07-26'}],
    source_file='cvm-notice-0110.pdf',source_sha256=sha(BASE/'cvm-notice-0110.pdf'),page=1,
    status='SOURCE_SCHEDULE_REVIEWED_RAW_ROW_TO_INSTALLMENT_MAPPING_NOT_INFERRED',
    note='Two equal values are installments, not duplicate garbage and not both immediately available.')]
(BASE/'reviewed-payment-dates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'summary':dict(count),'warnings':warnings},ensure_ascii=False,indent=2))
