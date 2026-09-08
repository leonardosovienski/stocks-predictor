"""Small checked primary-source fixtures; no database, return or raw-source writes."""
import json
from source_utils import ROOT, BASE, OUT, read, pages

repo=ROOT/'work/stocks-predictor';target=repo/'tests/fixtures/source_closure'
target.mkdir(exist_ok=True)
snap=read(OUT/'cash-closure-04.json')
fixture=dict(parents=snap['raw_parent_rows'],schedules=snap['schedules'],corporate_actions=snap['corporate_actions'])
with (target/'reviewed-payments.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(fixture,f,indent=2,ensure_ascii=False);f.write('\n')
cases=[]
for filename,day,pp in [('b3-credit-20230531.pdf','2023-05-31',[1]),
                        ('b3-section-04-1-2026-04-14.pdf','2026-04-14',[2]),
                        ('b3-credit-20220531.pdf','2022-05-31',[15])]:
    if filename.startswith('b3-credit'):
        p=BASE/filename;text=read(p.with_suffix('.credit-pages.json'));meta=read(p.with_suffix('.pdf.source.json'))
    else:
        p=OUT/'new-primary'/filename;text=pages(filename);meta=read(p.with_suffix('.source.json'))
    selected=[v for v in text if v['page'] in pp]
    cases.append(dict(file=filename,day=day,sources=[meta],pages=selected))
with (target/'b3-credit-pages.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(cases,f,indent=2,ensure_ascii=False);f.write('\n')
print('WROTE',target)
