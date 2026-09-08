"""Cached public-source download and plain HTML inspection, no strategy writes."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

BASE=Path(__file__).resolve().parent/'h19-cash-expanded-source'
BASE.mkdir(exist_ok=True)
class Tables(HTMLParser):
    def __init__(self):super().__init__();self.rows=[];self.links=[];self.row=None;self.cell=None;self.link=None;self.text=[]
    def handle_starttag(self,t,a):
        a=dict(a)
        if t=='tr':self.row=[]
        if t in ('td','th') and self.row is not None:self.cell=[]
        if t=='a':self.link=[a.get('href',''),[]]
        if t in ('script','iframe') and a.get('src'):self.links.append([a['src'],t])
    def handle_data(self,d):
        self.text.append(d)
        if self.cell is not None:self.cell.append(d)
        if self.link is not None:self.link[1].append(d)
    def handle_endtag(self,t):
        if t in ('td','th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()));self.cell=None
        if t=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
        if t=='a' and self.link is not None:
            self.links.append([self.link[0],' '.join(''.join(self.link[1]).split())]);self.link=None

def fetch(job):
    name,url=job;path=BASE/name
    if not path.exists():
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40) as r:
            data=r.read();ctype=r.headers.get('Content-Type','')
        if name.endswith('.pdf') and not data.startswith(b'%PDF'):raise ValueError('Not PDF')
        with path.open('xb') as f:f.write(data)
        path.with_suffix(path.suffix+'.source.json').write_text(json.dumps({'url':url,'bytes':len(data),'content_type':ctype,'sha256':hashlib.sha256(data).hexdigest(),'retrieved_at_utc':datetime.now(timezone.utc).isoformat()},indent=2),encoding='utf-8')
    if name.endswith('.html'):
        p=Tables();p.feed(path.read_text(encoding='utf-8'))
        path.with_suffix('.tables.json').write_text(json.dumps(p.rows,ensure_ascii=False,indent=2),encoding='utf-8')
        path.with_suffix('.links.json').write_text(json.dumps(p.links,ensure_ascii=False,indent=2),encoding='utf-8')
        return {'file':name,'rows':len(p.rows),'links':len(p.links)}
    return {'file':name,'bytes':path.stat().st_size}
if __name__=='__main__':
    jobs=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    def safe(job):
        try:return fetch(job)
        except Exception as e:return {'file':job[0],'error':str(e)}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(safe,jobs):print(json.dumps(result),flush=True)
