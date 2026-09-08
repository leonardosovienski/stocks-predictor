"""Find overlooked filings by issuer and category, including empty subjects."""
import csv
import io
import json
import re
import zipfile
from collections import Counter
from source_utils import ROOT, BASE, OUT, read, norm
from closure_helpers import sha
from stocks_predictor.cash_source_audit import select_cvm_followup_filings
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--output', default='overlooked-filings-index-13-v3.json')
args = parser.parse_args()

cash = read(OUT / 'cash-closure-12.json')['cash_events']
queue = read(ROOT / 'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V5.json')['cash_queue']
issuers = {}
for ticker in sorted({r['ticker'] for r in cash if not r['payment_date']}):
    q = next(q for q in queue if q['ticker'] == ticker)
    code = int(re.search(r'cvm(\d+)', q['source_path'])[1])
    ids = {r['event_id'] for r in cash if r['ticker'] == ticker and not r['payment_date']}
    start = min(r['approval_date'] for r in read(OUT / 'cash-review-cards.json') if r['event_id'] in ids)
    issuers[code] = (ticker, start)
rows = []
for path in sorted(BASE.glob('ipe-*.zip')):
    meta = read(path.with_suffix('.zip.source.json'))
    assert sha(path) == meta['sha256']
    with zipfile.ZipFile(path) as archive:
        reader = csv.DictReader(io.TextIOWrapper(archive.open(archive.namelist()[0]), encoding='latin-1'), delimiter=';')
        for row in select_cvm_followup_filings(reader, {k: v[1] for k, v in issuers.items()}, '2026-09-08'):
            code = int(row['Codigo_CVM'])
            if code not in issuers:
                continue
            ticker, start = issuers[code]
            if not start <= row['Data_Referencia'] <= '2026-09-08':
                continue
            category = norm(row['Categoria'])
            if category != 'relatorio proventos' and not (category == 'aviso aos acionistas' and not row['Assunto'].strip()):
                continue
            rows.append({**row, 'ticker': ticker, 'index_source': {'file': str(path), 'sha256': meta['sha256'], 'url': meta['url']}})
with (OUT / args.output).open('x', encoding='utf-8') as handle:
    json.dump(rows, handle, ensure_ascii=False, indent=2)
print(json.dumps({'records': len(rows), 'by_ticker': Counter(row['ticker'] for row in rows)}, ensure_ascii=False))
for row in rows[:12]:
    print(row['ticker'], row['Data_Referencia'], row['Categoria'], row['Versao'], row['Link_Download'])
