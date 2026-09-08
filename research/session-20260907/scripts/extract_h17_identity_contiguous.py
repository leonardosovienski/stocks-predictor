from pathlib import Path
import sqlite3,zipfile,hashlib,json,concurrent.futures
root=Path.cwd();raw=Path('C:/Users/Superleo13/stocks-predictor-work/data');dest=root/'work/h17-source-identity-contiguous';dest.mkdir(exist_ok=True)
def extract(year):
 p=raw/f'COTAHIST_A{year}.ZIP';output=dest/f'identity-{year}.jsonl'
 if output.exists():return year,'CACHED'
 records=[];current={};count=0
 with zipfile.ZipFile(p) as z:
  for name in z.namelist():
   with z.open(name) as stream:
    for row in stream:
     if row[:2]!=b'01' or row[24:27]!=b'010' or row[10:12]!=b'02':continue
     if len(row.rstrip(b'\r\n'))!=245:raise ValueError((year,count,'length'))
     tk=row[12:24].strip().decode('ascii');d=row[2:10].decode('ascii');date=d[:4]+'-'+d[4:6]+'-'+d[6:]
     isin=row[230:242].decode('ascii');dist=row[242:245].decode('ascii');spec=row[39:49].decode('latin-1').strip();bdi=row[10:12].decode('ascii')
     key=(tk,isin,dist,spec,bdi)
     if tk not in current or current[tk][0]!=key:
      r={'ticker':tk,'isin':isin,'distribution':dist,'spec':spec,'bdi':bdi,'first_date':date,'last_date':date,'sessions':0};records.append(r);current[tk]=(key,r)
     r=current[tk][1]
     r['last_date']=date;r['sessions']+=1;count+=1
 with output.open('w',encoding='utf-8',newline='\n') as f:
  for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 m={'path':str(p),'sha256':sha,'year':year,'spot_rows':count,'identity_segments':len(records),'layout':'https://www.b3.com.br/data/files/33/67/B9/50/D84057102C784E47AC094EA8/SeriesHistoricas_Layout.pdf','fields':'ISIN bytes 231..242; distribution 243..245; quote specification 40..49; 1-based'}
 output.with_suffix('.source.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
 return year,count,len(records)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for r in pool.map(extract,range(2016,2027)):print(r,flush=True)
