import concurrent.futures
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'work/source-acquisition'
OUT.mkdir(exist_ok=True)

def fetch(name,url):
    path=OUT/name
    if not path.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (public-source research)'})
        with urllib.request.urlopen(req,timeout=45) as r:
            data=r.read()
        path.write_bytes(data)
        (OUT/(name+'.source.json')).write_text(json.dumps({'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()},indent=2),encoding='utf-8')
    return path

urls=[('b3-index.html','https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/'),
      ('fca_cia_aberta_2023.zip','https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_2023.zip')]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    futures={pool.submit(fetch,*item):item for item in urls}
    for f in concurrent.futures.as_completed(futures):
        try: print('FETCH',f.result().name,flush=True)
        except Exception as e: print('FAILED',futures[f],repr(e),flush=True)
index=OUT/'b3-index.html'
if index.exists():
    html=index.read_text(encoding='utf-8')
    scripts=re.findall(r'<script[^>]+src="([^"]+)"',html)
    print('SCRIPTS',scripts,flush=True)
    for script in scripts:
        if 'main' in script:
            path=fetch('b3-main.js',urllib.parse.urljoin(urls[0][1],script))
            text=path.read_text(encoding='utf-8')
            for pattern in ('GetListedCashDividends','GetDetail','GetListedSupplement','GetCapital','GetCorporateActions','GetListedStockDividends'):
                pos=0
                for _ in range(3):
                    pos=text.find(pattern,pos)
                    if pos<0: break
                    print('API',pattern,text[max(0,pos-220):pos+330],flush=True)
                    pos+=len(pattern)
fca=OUT/'fca_cia_aberta_2023.zip'
if fca.exists():
    with zipfile.ZipFile(fca) as z:
        for name in z.namelist():
            if 'valor_mobiliario' in name:
                with z.open(name) as f:
                    reader=csv.DictReader(io.TextIOWrapper(f,encoding='latin-1'),delimiter=';')
                    print('FCA_HEADER',name,reader.fieldnames,flush=True)
                    for r in reader:
                        if r.get('Codigo_Negociacao') in ('BBAS3','ABEV3','ENGI11'):
                            print('FCA_ROW',r,flush=True)
