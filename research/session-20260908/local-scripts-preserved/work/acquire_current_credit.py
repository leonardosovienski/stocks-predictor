"""Acquire the observed 2026 clearing section; content validation is separate."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
import json
from probe_credit_sections import get
from source_utils import OUT

start=date(2026,1,1);end=date(2026,9,7)
jobs=[]
while start<=end:
    if start.weekday()<5:jobs.append((start.isoformat(),'04-1'))
    start+=timedelta(days=1)
results=[]
with ThreadPoolExecutor(max_workers=5) as pool:
    for result in pool.map(get,jobs):
        results.append(result)
        if len(results)%30==0:print('PROGRESS',len(results),len(jobs),flush=True)
with (OUT/'current-credit-acquisition.json').open('x',encoding='utf-8') as f:json.dump(results,f,indent=2)
print('COMPLETE',len(results),sum(r['status']=='DOWNLOADED' for r in results),flush=True)
