"""Hash original issuer payment-history tables; extracted rows are candidates."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
import urllib.request
from source_utils import OUT

jobs=[
 ('hypera','https://ri.hypera.com.br/mercado-de-capitais/dividendos/'),
 ('carrefour','https://ri.grupocarrefourbrasil.com.br/informacoes-aos-investidores/remuneracao-aos-acionistas/'),
 ('tim','https://ri.tim.com.br/nossas-acoes-e-dividas/remuneracao-aos-acionistas/'),
 ('ser','https://ri.sereducacional.com/informacoes-financeiras/historico-de-dividendos-jcp/'),
 ('telefonica','https://ri.telefonica.com.br/acoes-e-dividendos/informacoes-sobre-dividendos/'),
 ('qualicorp','https://ri.qualicorp.com.br/informacoes-financeiras/proventos/'),
]
class Tables(HTMLParser):
    def __init__(self):super().__init__();self.row=[];self.cell=None;self.rows=[]
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.row=[]
        if tag in ('td','th'):self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.row.append(' '.join(' '.join(self.cell).split()));self.cell=None
        if tag=='tr' and self.row:self.rows.append(self.row);self.row=[]

def get(job):
    name,url=job;p=OUT/'new-primary'/f'issuer-{name}.html'
    if p.exists():raise FileExistsError(p)
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req,timeout=30) as r:b=r.read()
    parser=Tables();parser.feed(b.decode('utf-8',errors='replace'))
    with p.open('xb') as f:f.write(b)
    meta=dict(url=url,sha256=hashlib.sha256(b).hexdigest(),retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
        retrospective_issuer_payment_history=True,not_point_in_time_publication_certificate=True)
    with p.with_suffix('.source.json').open('x',encoding='utf-8') as f:json.dump(meta,f,indent=2)
    with p.with_suffix('.tables.json').open('x',encoding='utf-8') as f:json.dump(parser.rows,f,ensure_ascii=False,indent=2)
    return dict(file=p.name,rows=len(parser.rows),sha256=meta['sha256'])

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(get,j) for j in jobs]
        for f in futures:
            try:print(f.result(),flush=True)
            except Exception as e:print(type(e).__name__,str(e),flush=True)
