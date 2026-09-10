"""Bounded public capture. Failed transfers stay visible; no credentials."""
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import urllib.parse
ROOT=Path(r'C:\STOCKS\work\data-completion-r2-20260909')
RAW=ROOT/'raw'
LOCK=threading.Lock()
JOURNAL=ROOT/'acquisition.jsonl'

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()

def capture(row):
    RAW.mkdir(exist_ok=True)
    path=(RAW/row['filename']).resolve()
    if not path.is_relative_to(RAW.resolve()) or path.exists(): raise ValueError('Unsafe/existing output')
    record=dict(id=row['id'],url=row['url'],purpose=row['purpose'],path=str(path),started_at_utc=now(),status='attempted')
    with LOCK:
        previous=[json.loads(line) for line in JOURNAL.read_text(encoding='utf-8').splitlines()] if JOURNAL.exists() else []
        if len({r['id'] for r in previous})>=140 or any(r['id']==row['id'] for r in previous): raise ValueError('Attempt budget/duplicate')
        if sum(r.get('bytes',0)+r.get('partial_bytes',0) for r in previous if r['status']!='attempted')>=1000000000: raise ValueError('Download budget')
        if now()>='2026-09-09T22:40:00': raise ValueError('Collection deadline')
        with JOURNAL.open('a',encoding='utf-8') as stream: stream.write(json.dumps(record)+'\n')
    partial=path.with_name(path.name+'.partial')
    headers=path.with_name(path.name+'.headers')
    try:
        args=[]
        if row.get('ipv4'): args+=['--ipv4']
        if 'json_body' in row:
            args+=['--header','Content-Type: application/json','--data-binary',json.dumps(row['json_body'])]
            record['json_body']=row['json_body']
        if 'form_body' in row:
            body=urllib.parse.urlencode(row['form_body'])
            args+=['--header','Content-Type: application/x-www-form-urlencoded','--data-binary',body]
            record['public_form_body_sha256']=hashlib.sha256(body.encode()).hexdigest()
        cp=subprocess.run([r'C:\WINDOWS\system32\curl.exe','--location','--fail','--silent','--show-error','--connect-timeout','10','--max-time','35','--max-filesize',str(row.get('max_bytes',30000000)),'--user-agent','Mozilla/5.0','--dump-header',str(headers),'--output',str(partial),'--write-out','%{json}',*args,row['url']],capture_output=True,timeout=40)
        record['curl_exit_code']=cp.returncode
        if cp.stdout:
            meta=json.loads(cp.stdout)
            record.update(http_status=meta.get('http_code'),final_url=meta.get('url_effective'),content_type=meta.get('content_type'))
        if cp.returncode: raise RuntimeError(cp.stderr.decode('utf-8',errors='replace'))
        if not partial.stat().st_size: raise ValueError('Empty response')
        if path.suffix.lower()=='.pdf' and partial.read_bytes()[:5]!=b'%PDF-': raise ValueError('Not PDF')
        if path.suffix.lower()=='.json': json.loads(partial.read_text(encoding='utf-8-sig'))
        with partial.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
        partial.rename(path)
        record.update(status='downloaded',bytes=path.stat().st_size,sha256=digest)
    except Exception as exc:
        record.update(status='failed',error_type=type(exc).__name__,error=str(exc))
        if partial.exists(): record['partial_bytes']=partial.stat().st_size
    record['completed_at_utc']=now()
    with LOCK:
        with JOURNAL.open('a',encoding='utf-8') as stream: stream.write(json.dumps(record,ensure_ascii=False)+'\n')
    path.with_name(path.name+'.source.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:record[k] for k in ('id','status','bytes','error') if k in record}),flush=True)

if __name__=='__main__':
    rows=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: list(pool.map(capture,rows))
