"""Find source candidates; this file never sets review flags."""
import json
from source_utils import OUT, read, norm, dates, amounts, pages

cards = read(OUT / 'cash-review-cards.json')
jobs = read(OUT / 'additional-notices.json')
result = []
for i, card in enumerate(cards):
    hits = []
    for job in jobs:
        if card['event_id'] not in job['matching_events']:
            continue
        try:
            pp = pages(job['local_file'])
        except FileNotFoundError:
            continue
        for page in pp:
            text = norm(page['text'])
            aa = amounts(text, card['gross_per_share'])
            dd = dates(text)
            if not aa:
                continue
            hits.append({'file': job['local_file'], 'page': page['page'],
                         'received': job['Data_Entrega'], 'amounts': aa,
                         'record_date_present': card['last_cum'] in {d for d, _, _ in dd},
                         'dates': [(d, text[max(0, a-120):b+65]) for d,a,b in dd],
                         'text': text})
    if hits:
        result.append({'card_index': i, **{k:v for k,v in card.items() if k!='candidates'}, 'new_candidates': hits})
with (OUT / 'new-cash-review-cards.json').open('w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
for r in result:
    print(r['card_index'], r['ticker'], r['ex_date'], r['gross_per_share'],
          [(h['file'],h['page'],h['record_date_present']) for h in r['new_candidates']])
print('EVENTS_WITH_NEW_CANDIDATES', len(result))
