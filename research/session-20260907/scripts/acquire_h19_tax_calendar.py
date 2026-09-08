"""Resolve DARF 6015 dates from Receita's actual monthly agenda pages."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import urllib.parse
import urllib.request

from cash_research_fetch import Tables

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'work/h19-tax-source';BASE.mkdir(exist_ok=True)
PREFIX='https://www.gov.br/receitafederal/pt-br/assuntos/agenda-tributaria/'
MONTHS='janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro'.split()
def norm(s):return ' '.join(unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower().split())
def fetch(url):
    stem=hashlib.sha256(url.encode()).hexdigest()[:24];path=BASE/(stem+'.html');meta=BASE/(stem+'.source.json')
    if not path.exists():
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40) as r:data=r.read()
        path.write_bytes(data)
        meta.write_text(json.dumps({'url':url,'sha256':hashlib.sha256(data).hexdigest(),
            'retrieved_at_utc':datetime.now(timezone.utc).isoformat()},indent=2),encoding='utf-8')
    parser=Tables();parser.feed(path.read_text(encoding='utf-8'))
    return parser,{'file':path.name,**json.loads(meta.read_text(encoding='utf-8'))}
def one_year(year):
    result=[];errors=[]
    root=PREFIX+(f'agenda-tributaria-{year}' if year<2022 else str(year))
    p,source=fetch(root);links=list(p.links)
    if year<2022:
        children=[urllib.parse.urljoin(root,u) for u,t in links if norm(t)==f'agenda tributaria {year}' and u.rstrip('/')!=root]
        for u in sorted(set(children)):
            if not u.startswith(root+'/'):continue
            try:q,_=fetch(u);links+=q.links
            except Exception as e:errors.append({'url':u,'error':str(e)})
    for month,name in enumerate(MONTHS,1):
        if (year==2018 and month<7) or (year==2026 and month>5):continue
        candidates=[]
        for url,label in links:
            u=urllib.parse.urljoin(root,url);t=norm(label)
            if u.startswith(root+'/') and (t==name or re.fullmatch(name+r'\s*/?\s*'+str(year),t)):
                candidates.append(u)
        chosen=[]
        for url in sorted(set(candidates)):
            try:
                page,_=fetch(url);days=[]
                for target,label in page.links:
                    u=urllib.parse.urljoin(url+'/',target);tail=u.rstrip('/').split('/')[-1]
                    match=re.match(r'(?:dia-)?(\d{1,2})(?:-|$)',tail)
                    if not match and re.fullmatch(r'\d{1,2}',norm(label)):match=re.match(r'(\d+)',norm(label))
                    if match and int(match[1])>=25 and u.startswith(url.rstrip('/')+'/'):days.append((int(match[1]),u))
                for day,u in sorted(set(days),reverse=True):
                    daypage,evidence=fetch(u)
                    rows=[r for r in daypage.rows if r and '6015' in r[0] and any('bolsa' in norm(c) for c in r)]
                    if rows:
                        assessed_year=year if month>1 else year-1;assessed_month=month-1 if month>1 else 12
                        chosen.append({'assessment_month':f'{assessed_year}-{assessed_month:02}',
                            'due_date':f'{year}-{month:02}-{day:02}','source_review':True,'sources':[evidence],
                            'source_rows':rows,'irrf_rate':'.00005','irrf_waiver':'1','minimum_darf':'10'})
            except Exception as e:errors.append({'url':url,'error':str(e)})
        unique={r['due_date']:r for r in chosen}
        if len(unique)==1:result.append(next(iter(unique.values())))
        else:errors.append({'year':year,'month':month,'found_dates':sorted(unique),'candidate_urls':candidates})
    print(json.dumps({'year':year,'resolved_months':len(result),'errors':len(errors)}),flush=True)
    return result,errors
if __name__=='__main__':
    results=[];errors=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for rows,issues in pool.map(one_year,range(2018,2027)):
            results+=rows;errors+=issues
    target=ROOT/'work/h19-continuous-inputs/tax-calendar.json'
    target.write_text(json.dumps({'calendar':{r['assessment_month']:r for r in sorted(results,key=lambda r:r['assessment_month'])},
        'errors':errors,'new_return_evaluations':0},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'resolved_months':len(results),'unresolved_or_fetch_errors':len(errors)}),flush=True)
