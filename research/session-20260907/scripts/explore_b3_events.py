import base64
import csv
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parent.parent
RAW=ROOT/'work/source-acquisition'
BASE='https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/'

def fetch(method,params,cache_name):
    url=BASE+method+'/'+base64.b64encode(json.dumps(params,separators=(',',':')).encode()).decode()
    path=RAW/(cache_name+'.json')
    if not path.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (public-source research)'})
        with urllib.request.urlopen(req,timeout=45) as response:
            data=response.read()
        json.loads(data)
        path.write_bytes(data)
        (RAW/(cache_name+'.source.json')).write_text(json.dumps({'url':url,'params':params,'retrieved_at':datetime.now(timezone.utc).isoformat(),
                                                                  'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()},indent=2),encoding='utf-8')
    return json.loads(path.read_text(encoding='utf-8-sig'))

if __name__=='__main__':
    with zipfile.ZipFile(RAW/'dfp_cia_aberta_2023.zip') as z:
        rows=list(csv.DictReader(io.TextIOWrapper(z.open('dfp_cia_aberta_2023.csv'),encoding='latin-1'),delimiter=';'))
    wanted={'00.000.000/0001-91':'BBAS3','07.526.557/0001-00':'ABEV3','00.864.214/0001-06':'ENGI11'}
    codes={wanted[r['CNPJ_CIA']]:str(int(r['CD_CVM'])) for r in rows if r['CNPJ_CIA'] in wanted}
    for ticker,code in codes.items():
        try:
            detail=fetch('GetDetail',{'codeCVM':code,'language':'pt-br'},'b3-'+ticker+'-detail')
            print(ticker,'DETAIL',detail,flush=True)
            supplement=fetch('GetListedSupplementCompany',{'issuingCompany':detail['issuingCompany'],'language':'pt-br'},'b3-'+ticker+'-supplement')
            print(ticker,'SUPPLEMENT',str(supplement)[:6500],flush=True)
            trading=detail['tradingName'].upper().strip()
            for char in (' ','-','_','/'):
                trading=trading.replace(char,'',1)
            cash=fetch('GetListedCashDividends',{'tradingName':trading,'language':'pt-br','pageNumber':1,'pageSize':20},'b3-'+ticker+'-cash-1')
            print(ticker,'CASH',{'page':cash.get('page'),'first':cash.get('results',[])[:2],'last':cash.get('results',[])[-1:]},flush=True)
        except Exception as e:
            print(ticker,'FAILED',repr(e),flush=True)
