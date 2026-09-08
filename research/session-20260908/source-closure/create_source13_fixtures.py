"""Freeze small real source cases for the repaired selector and duplicate review."""
from pathlib import Path
import csv
import io
import json
import zipfile
from source_utils import ROOT, BASE, OUT, read
from closure_helpers import sha

dest=ROOT/'work/stocks-predictor/tests/fixtures/source_closure'
snap=read(OUT/'cash-closure-13.json'); review=snap['duplicate_lineage'][0]
old=read(OUT/'cash-closure-12.json')['cash_events']
ids=[review['canonical_event_id'], *review['duplicate_event_ids']]
rawsource=review['raw_records'][0]['source'];p=Path(rawsource['file'])
assert sha(p)==rawsource['sha256']
f=dict(events=[r for r in old if r['event_id'] in ids], reviews=[review],
    original_b3=read(p), original_sha256=sha(p),
    distinct_installments=[r for r in old if r['ticker']=='IGTA3' and r['ex_date']=='2019-04-22'])
(dest/'hypera-duplicate-review.json').write_text(json.dumps(f,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
selected=read(OUT/'overlooked-filings-index-13-v2.json')
wanted={'1167175','1167313','1135094','1135615','1145284','1074059','1037840','1456495','1187993'}
rows=[r for r in selected if any('numProtocolo='+n+'&' in r['Link_Download'] for n in wanted)]
assert len(rows)==9
# Real ineligible records from the same bulk source, not invented parser rows.
with zipfile.ZipFile(BASE/'ipe-2023.zip') as z:
    more=list(csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='latin-1'),delimiter=';'))
codes={int(r['Codigo_CVM']) for r in rows}
rows += [next(r for r in more if int(r['Codigo_CVM'])==code and r['Categoria']=='Comunicado ao Mercado') for code in sorted(codes) if code in {int(r['Codigo_CVM']) for r in more}]
(dest/'overlooked-cvm-index.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('Created real Hypera and CVM index fixtures',len(rows))
