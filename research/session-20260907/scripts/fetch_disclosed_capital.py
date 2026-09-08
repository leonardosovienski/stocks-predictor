"""Public CVM document capital pages, with exact issuer/version validation."""
from pathlib import Path
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
import argparse, concurrent.futures, csv, hashlib, http.cookiejar, io, json, re, sys
import urllib.parse, urllib.request, zipfile

ROOT=Path(__file__).resolve().parent.parent
RAW=ROOT/'work/source-acquisition'
DEST=ROOT/'work/value-capital-source'
DEST.mkdir(exist_ok=True)
sys.path[:0]=[str(ROOT/'work/stocks-predictor'),str(ROOT/'work/runtime')]
from stocks_predictor.document_panel import capital_from_viewer

class Form(HTMLParser):
    def __init__(self):
        super().__init__();self.fields={};self.select=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='input' and a.get('type')=='hidden' and a.get('name'):
            self.fields[a['name']]=a.get('value','')
        if tag=='select':self.select=a.get('name')
        if tag=='option' and self.select and ('selected' in a or self.select not in self.fields):
            self.fields[self.select]=a.get('value','')
    def handle_endtag(self,tag):
        if tag=='select':self.select=None

def fetch(doc):
    docid=doc['ID_DOC'];target=DEST/f'capital-{docid}.html'
    metadata={'cnpj':''.join(c for c in doc['CNPJ_CIA'] if c.isdigit()),'ref_date':doc['DT_REFER'],
              'document_version':int(doc['VERSAO']),'document_id':docid,'received_at':doc['DT_RECEB']}
    viewer='https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?CodigoTipoInstituicao=1&NumeroSequencialDocumento='+docid
    try:
        if target.exists():
            source=json.loads(target.with_suffix('.source.json').read_text(encoding='utf-8'))
            payload=target.read_bytes()
            if hashlib.sha256(payload).hexdigest()!=source['sha256']:raise ValueError('cached source changed')
        else:
            opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            headers={'User-Agent':'Mozilla/5.0 (public CVM financial research)'}
            def request(url,data=None):
                with opener.open(urllib.request.Request(url,data=data,headers=headers),timeout=35) as response:
                    return response.read()
            initial=request(viewer);form=Form();form.feed(initial.decode('utf-8-sig'))
            if int(form.fields.get('hdnCodigoCvm','0'))!=int(doc['CD_CVM']):raise ValueError('viewer issuer mismatch')
            if form.fields.get('hdnHabilitaCaptcha')=='S':raise ValueError('interactive CAPTCHA required')
            form.fields.update(__EVENTTARGET='cmbGrupo',__EVENTARGUMENT='',cmbGrupo='201')
            capital_view=request(viewer,urllib.parse.urlencode(form.fields).encode())
            text=capital_view.decode('utf-8-sig')
            matches=re.findall(r"window\.frames\[0\]\.location='([^']+)'",text)
            if len(matches)!=1 or 'frmDadosComposicaoCapitalITR.aspx' not in matches[0]:raise ValueError('no capital page in response')
            url=urllib.parse.urljoin(viewer,unescape(matches[0]));url=urllib.parse.quote(url,safe=':/?=&%+|')
            query=urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            if query.get('NumeroSequencialDocumento')!=[docid] or query.get('Versao')!=[doc['VERSAO']] or query.get('DataReferencia')!=[doc['DT_REFER']]:raise ValueError('document identity mismatch')
            payload=request(url)
            source={'url':url,'viewer_url':viewer,'sha256':hashlib.sha256(payload).hexdigest(),'retrieved_at':datetime.now(timezone.utc).isoformat(),'exact_source_document':doc}
            # Parse before accepting a cached successful response.
            capital_from_viewer(payload,metadata,url)
            target.write_bytes(payload)
            target.with_suffix('.source.json').write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf-8')
        parsed=capital_from_viewer(payload,metadata,source['url'])
        return {'status':'ACQUIRED',**parsed,'file':target.name}
    except Exception as error:
        return {'status':'FAILED',**metadata,'error':str(error)}

def jobs():
    snapshots=json.loads((ROOT/'work/h17-run-pack-v2/data/snapshots.json').read_text(encoding='utf-8'))
    wanted={(r['cnpj'],r['filing']['ref_date'],r['filing']['document_version']) for s in snapshots for r in s['universe'] if r.get('filing')}
    docs={}
    for year in range(2016,2027):
        with zipfile.ZipFile(RAW/f'dfp_cia_aberta_{year}.zip') as z:
            for r in csv.DictReader(io.TextIOWrapper(z.open(f'dfp_cia_aberta_{year}.csv'),encoding='latin-1'),delimiter=';'):
                key=(''.join(c for c in r['CNPJ_CIA'] if c.isdigit()),r['DT_REFER'],int(r['VERSAO']))
                if key in wanted:
                    if key in docs and docs[key]['ID_DOC']!=r['ID_DOC']:raise ValueError('duplicate document identity')
                    docs[key]=r
    return sorted(docs.values(),key=lambda r:(r['DT_REFER'],r['CNPJ_CIA'],int(r['VERSAO'])))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--all',action='store_true');args=parser.parse_args()
    tasks=jobs()
    print('required_documents',len(tasks),flush=True)
    if not args.all:tasks=tasks[:3]
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i,r in enumerate(pool.map(fetch,tasks),1):
            results.append(r)
            if i%25==0 or r['status']=='FAILED' or not args.all:
                print(i,r['status'],r['cnpj'],r['ref_date'],r.get('error',''),flush=True)
    path=DEST/('acquisition-all.json' if args.all else 'acquisition-pilot.json')
    path.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print('complete',len(results),'success',sum(r['status']=='ACQUIRED' for r in results),flush=True)
