"""Append-only public issuer documents for the resumed source review."""
from concurrent.futures import ThreadPoolExecutor
import json
from acquire_issuer_originals import get as get_pdf
from acquire_issuer_tables import get as get_html
from source_utils import OUT

JOBS = [
    ('pdf', ('13-iguatemi-dfp2019', 'https://ri.iguatemi.com.br/Download.aspx?Arquivo=sLiSCOqsP13DAhCjY6+wMw%3D%3D')),
    ('pdf', ('13-radl-agm2021-doe', 'https://diariooficial.imprensaoficial.com.br/doflash/prototipo/2021/Maio/06/empresarial/pdf/pg_0033.pdf')),
    ('pdf', ('13-totvs-agm2020', 'https://api.mziq.com/mzfilemanager/v2/d/d3be5d49-62e7-4def-a3e1-ab25ff09f153/a3258756-17dd-1705-8d9c-95ad82c485f1?origin=1')),
    ('pdf', ('13-hapvida-agm2022', 'https://api.mziq.com/mzfilemanager/v2/d/6bbd1770-f9f4-44e8-a1b1-d26b7585eec1/1035ce92-900b-bfa9-4853-2d5bd675fbc5?origin=1')),
    ('pdf', ('13-hapvida-itr1t2022', 'https://vipfiles.valor.com.br/BDEmpresas/623349.pdf')),
    ('pdf', ('13-radl-agm2023', 'https://ri.rd.com.br/Download.aspx?Arquivo=FDXJlrq7W8iws8XbFM5j3A%3D%3D&IdCanal=M9eciSyHCkOXeOE9W1JJeA%3D%3D')),
    ('html', ('13-totvs-history', 'https://ri.totvs.com/informacoes-financeiras/dividendos-e-jcp/')),
    ('html', ('13-renner-history', 'https://ri.lojasrenner.com.br/info-aos-investidores/eventos-societarios/')),
]

def fetch(job):
    kind, args = job
    try:
        return {'kind': kind, 'name': args[0], **(get_pdf(args) if kind == 'pdf' else get_html(args))}
    except Exception as exc:
        return {'kind': kind, 'name': args[0], 'url': args[1], 'error': str(exc)}

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(fetch, JOBS))
    with (OUT / 'followup-acquisition-13.json').open('x', encoding='utf-8') as handle:
        json.dump(rows, handle, ensure_ascii=False, indent=2)
    for row in rows:
        print(row, flush=True)
