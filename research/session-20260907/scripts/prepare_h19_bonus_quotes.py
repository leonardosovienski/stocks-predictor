"""Read primary PN quotes identified by the issuer's bonus notices."""
from collections import Counter
from decimal import Decimal as D
import hashlib,json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];base=root/'work/h19-continuous-inputs'
windows={'RENT4':'2025-12-30','CYRE4':'2026-01-02'};end='2026-04-01'
rows=[];raw=[];sources=[]
for year in (2025,2026):
    archive=Path(r'C:\Users\Superleo13\stocks-predictor-work\data')/f'COTAHIST_A{year}.ZIP'
    with archive.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    sources.append({'archive':str(archive),'sha256':digest})
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            with z.open(name) as f:
                for line in f:
                    if line[:2]!=b'01' or line[24:27] not in (b'010',b'020'):continue
                    symbol=line[12:24].decode('ascii').strip();market=line[24:27].decode('ascii')
                    ticker=symbol[:-1] if market=='020' and symbol.endswith('F') else symbol
                    if ticker not in windows:continue
                    d=line[2:10].decode('ascii');day=f'{d[:4]}-{d[4:6]}-{d[6:]}'
                    if not windows[ticker]<=day<=end:continue
                    factor=int(line[210:217]);scale=D(100*factor)
                    rows.append({'date':day,'ticker':ticker,'isin':line[230:242].decode('ascii'),
                        'market_type':market,'open':str(D(int(line[56:69]))/scale),
                        'close':str(D(int(line[108:121]))/scale),'quote_factor':factor,
                        'volume_fin':str(D(int(line[170:188]))/100),'quantity':int(line[152:170])})
                    raw.append(line.rstrip(b'\r\n'))
path=base/'quotes-bonus-pn.jsonl';path.write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows),encoding='utf-8')
rawpath=base/'quotes-bonus-pn.cotahist.txt';rawpath.write_bytes(b'\n'.join(raw)+b'\n')
index=json.loads((base/'quote-tape-index.json').read_text(encoding='utf-8'))
found={(r['date'],r['ticker']) for r in rows if r['market_type']=='010'}
missing=[(d,t) for t,start in windows.items() for d in index['sessions'] if start<=d<=end and (d,t) not in found]
result={'sources':sources,'quotes':path.name,'quotes_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'raw_excerpt':rawpath.name,'raw_excerpt_sha256':hashlib.sha256(rawpath.read_bytes()).hexdigest(),
    'identities':sorted({(r['ticker'],r['isin']) for r in rows}),
    'rows_by_market':dict(Counter(r['market_type'] for r in rows)),
    'missing_standard_quotes':missing,'legal_delivery_and_cash_not_integrated':True,'new_returns':0}
(base/'bonus-asset-coverage.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
