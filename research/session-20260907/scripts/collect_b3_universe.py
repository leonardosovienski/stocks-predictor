"""Public source acquisition only; no security mapping is promoted into signals."""
import concurrent.futures
import csv
import io
import json
from pathlib import Path
import sys
import zipfile

from explore_b3_events import fetch

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'work/source-acquisition'
sys.path[:0] = [str(ROOT / 'work/stocks-predictor'), str(ROOT / 'work/stocks-predictor/stocks_predictor')]
from tools.build_h7_ticker_of import load_universe

universe = load_universe(Path(r'C:\Users\Superleo13\stocks-predictor-work\universo_2018_2026.txt'))
links = {}
codes = {}
for year in range(2016, 2027):
    with zipfile.ZipFile(RAW / f'fca_cia_aberta_{year}.zip') as archive:
        def rows(member):
            return list(csv.DictReader(io.TextIOWrapper(archive.open(member), encoding='latin-1'), delimiter=';'))
        main = rows(f'fca_cia_aberta_{year}.csv')
        for row in main:
            codes[row['CNPJ_CIA']] = str(int(row['CD_CVM']))
        for row in rows(f'fca_cia_aberta_valor_mobiliario_{year}.csv'):
            ticker = row['Codigo_Negociacao'].strip()
            if ticker in universe:
                links.setdefault(row['CNPJ_Companhia'], set()).add(ticker)

jobs = [{'cnpj': cnpj, 'codeCVM': codes[cnpj], 'tickers': sorted(tickers)} for cnpj, tickers in sorted(links.items())]
(ROOT / 'outputs/b3-acquisition-universe.json').write_text(json.dumps({'universe': sorted(universe), 'issuers': jobs, 'not_linked': sorted(set(universe) - set().union(*links.values()))}, indent=2), encoding='utf-8')

def collect(job):
    result = dict(job)
    code = job['codeCVM']
    try:
        detail = fetch('GetDetail', {'codeCVM': code, 'language': 'pt-br'}, f'b3-cvm{code}-detail')
        if ''.join(c for c in detail['cnpj'] if c.isdigit()) != ''.join(c for c in job['cnpj'] if c.isdigit()):
            raise ValueError('B3/CVM issuer identity mismatch')
        supplement = fetch('GetListedSupplementCompany', {'issuingCompany': detail['issuingCompany'], 'language': 'pt-br'}, f'b3-cvm{code}-supplement')
        trading = detail['tradingName'].upper().strip()
        for char in (' ', '-', '_', '/'):
            trading = trading.replace(char, '', 1)
        cash, total, page = [], None, 1
        while True:
            payload = fetch('GetListedCashDividends', {'tradingName': trading, 'language': 'pt-br', 'pageNumber': page, 'pageSize': 20}, f'b3-cvm{code}-cash-{page}')
            if total is None:
                total = payload['page']['totalRecords']
            if total != payload['page']['totalRecords']:
                raise ValueError('cash history changed during pagination')
            cash.extend(payload['results'])
            if page >= payload['page']['totalPages']:
                break
            page += 1
        if len(cash) != total:
            raise ValueError('incomplete pagination')
        (RAW / f'b3-cvm{code}-cash-all.json').write_text(json.dumps(cash, ensure_ascii=False, indent=2), encoding='utf-8')
        result.update(status='ACQUIRED', historical_rows=len(cash), pages=page, payment_dates_in_history=False,
                      supplement_cash_rows=sum(len(r.get('cashDividends', [])) for r in supplement),
                      current_detail_codes=detail.get('otherCodes'))
    except Exception as exc:
        result.update(status='FAILED', error=repr(exc))
    return result

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    for result in pool.map(collect, jobs):
        results.append(result)
        print(json.dumps({k: v for k, v in result.items() if k != 'current_detail_codes'}), flush=True)
        (ROOT / 'outputs/b3-historical-acquisition.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
