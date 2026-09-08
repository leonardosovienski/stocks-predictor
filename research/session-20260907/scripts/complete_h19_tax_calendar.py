"""Combine visually reviewed PDF groups with exact Receita DARF rows."""
from datetime import date, timedelta
import hashlib
import json
from acquire_h19_tax_calendar import ROOT, BASE, fetch, norm

target=ROOT/'work/h19-continuous-inputs/tax-calendar.json'
record=json.loads(target.read_text(encoding='utf-8'));calendar=record['calendar']
def add(due,source,rows,method):
    month=(date.fromisoformat(due).replace(day=1)-timedelta(days=1)).isoformat()[:7]
    spec={'assessment_month':month,'due_date':due,'source_review':True,'sources':[source],
          'source_rows':rows,'review_method':method,'irrf_rate':'.00005','irrf_waiver':'1','minimum_darf':'10'}
    if month in calendar:
        assert calendar[month]['due_date']==due
        if source not in calendar[month]['sources']:calendar[month]['sources'].append(source)
    else:calendar[month]=spec
for r in json.loads((BASE/'pdf-date-review.json').read_text(encoding='utf-8'))['candidates']:
    assert hashlib.sha256((BASE/r['file']).read_bytes()).hexdigest()==r['sha256']
    add(r['candidate_due_date'],{k:r[k] for k in ('file','url','sha256','page')},
        [r['page_text']], 'VISUAL_HEADER_DATE_GROUP_AND_DARF_6015_CONTACT_SHEETS_1_TO_6')
for due,url in [
 ('2023-10-31','https://www.gov.br/receitafederal/pt-br/assuntos/agenda-tributaria/2023/10/dia-31-10-2023'),
 ('2024-03-28','https://www.gov.br/receitafederal/pt-br/assuntos/agenda-tributaria/2024/03/dia-28-03-2024'),
 ('2024-01-31','https://www.gov.br/receitafederal/pt-br/assuntos/agenda-tributaria/2024/01/dia-31-01-2023')]:
    parser,source=fetch(url)
    rows=[r for r in parser.rows if r and r[0].strip()=='6015' and 'bolsa' in norm(' '.join(r))]
    assert len(rows)==1,(url,rows)
    add(due,source,rows,'EXACT_OFFICIAL_DARF_6015_ROW')
required=[];y=2018;m=6
while (y,m)<=(2026,4):
    required.append(f'{y}-{m:02}');m+=1
    if m==13:y+=1;m=1
missing=[m for m in required if m not in calendar]
out={'calendar':dict(sorted(calendar.items())),'required_months':required,'missing_months':missing,
     'historical_source_fetch_errors_resolved':record.get('errors',[]),'new_return_evaluations':0}
dest=ROOT/'work/h19-continuous-inputs/tax-calendar-complete.json'
dest.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'resolved':len(calendar),'required':len(required),'missing':missing},indent=2))
