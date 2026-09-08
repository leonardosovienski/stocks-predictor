from pathlib import Path
import zipfile,hashlib,json,concurrent.futures,collections
root=Path.cwd();raw=Path('C:/Users/Superleo13/stocks-predictor-work/data');dest=root/'work/h17-source-identity-v3';dest.mkdir(exist_ok=True)
def extract(year):
 p=raw/f'COTAHIST_A{year}.ZIP';output=dest/f'identity-{year}.jsonl'
 if output.exists():return year,'CACHED'
 by={};duplicates=0
 with zipfile.ZipFile(p) as z:
  for name in z.namelist():
   with z.open(name) as stream:
    for row in stream:
     if row[:2]!=b'01' or row[24:27]!=b'010' or row[10:12]!=b'02':continue
     if len(row.rstrip(b'\r\n'))!=245:raise ValueError('invalid length')
     tk=row[12:24].strip().decode('ascii');d=row[2:10].decode('ascii');date=d[:4]+'-'+d[4:6]+'-'+d[6:];isin=row[230:242].decode('ascii');kind=row[39:49].decode('latin-1').strip().split()[0]
     key=(tk,date);v=(isin,kind)
     if key in by:
      duplicates+=1
      if by[key]!=v:raise ValueError((year,tk,date,'ambiguous identity'))
     by[key]=v
 records=[];current={}
 for (tk,date),(isin,kind) in sorted(by.items()):
  key=(isin,kind)
  if tk not in current or current[tk][0]!=key:
   r={'ticker':tk,'isin':isin,'kind':kind,'first_date':date,'last_date':date,'sessions':0};records.append(r);current[tk]=(key,r)
  r=current[tk][1];r['last_date']=date;r['sessions']+=1
 with output.open('w',encoding='utf-8',newline='\n') as f:
  for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 m={'path':str(p),'sha256':sha,'year':year,'spot_rows':len(by),'duplicates':duplicates,'identity_segments':len(records),'layout':'https://www.b3.com.br/data/files/33/67/B9/50/D84057102C784E47AC094EA8/SeriesHistoricas_Layout.pdf','policy':'Sort all observations by ticker/date before compressing; raw archive order is not chronological.'}
 output.with_suffix('.source.json').write_text(json.dumps(m,indent=2),encoding='utf-8');return year,len(by),len(records)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for r in pool.map(extract,range(2016,2027)):print(r,flush=True)
