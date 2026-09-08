"""Read original CVM index rows for a bounded issuer/date investigation."""
import csv,io,json,re,sys,zipfile
from source_utils import BASE,read
from closure_helpers import sha

cnpj,start,end=sys.argv[1:4]
for p in BASE.glob('ipe-*.zip'):
    if not any(str(y) in p.name for y in range(int(start[:4]),int(end[:4])+1)):continue
    meta=read(p.with_suffix('.zip.source.json'));assert sha(p)==meta['sha256']
    with zipfile.ZipFile(p) as z:text=z.read(z.namelist()[0]).decode('latin1')
    for r in csv.DictReader(io.StringIO(text),delimiter=';'):
        if re.sub(r'\D','',r['CNPJ_Companhia'])==cnpj and start<=r['Data_Referencia']<=end:
            print(json.dumps(r,ensure_ascii=False))
