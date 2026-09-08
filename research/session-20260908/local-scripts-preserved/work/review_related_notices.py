"""Show original notices by issuer/event identity, without nominal-only filtering."""
import sys
from datetime import date
from source_utils import BASE, OUT, read, pages, norm

cards = read(OUT / 'cash-review-cards.json')
docs = read(BASE / 'ipe-complete-notices.json')
for index in map(int, sys.argv[1:]):
    c = cards[index]
    print('\nCARD', index, c['ticker'], c['ex_date'], c['gross_per_share'])
    for d in docs:
        if not -3 <= (date.fromisoformat(d['Data_Referencia']) - date.fromisoformat(c['approval_date'])).days <= 100:
            continue
        if not any(r['ticker'] == c['ticker'] and r['ex_date'] == c['ex_date']
                   for r in d.get('matching_cash_requirements', [])):
            continue
        print('FILE', d['local_file'], d['Data_Entrega'], d['Assunto'])
        try:
            pp = pages(d['local_file'])
        except FileNotFoundError:
            print('MISSING_FILE', d['Link_Download'])
            continue
        for p in pp[:1]:
            print('PAGE', p['page'], norm(p['text']))
