"""Find issuer documents for physical delivery, fractions and fiscal basis."""
from datetime import date
import csv
import io
import json
from pathlib import Path
import re
import unicodedata
import zipfile

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'work/h19-cash-expanded-source'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def norm(t):return unicodedata.normalize('NFKD',t).encode('ascii','ignore').decode().lower()
obs=read(ROOT/'outputs/h18-h19-reorganization-observation.json')
trial=next(t for t in obs['trials'] if t['family']=='H19' and t['holding_months']==3)
ids={m['ticker']:m['cnpj'] for p in trial['periods'] for m in p['members']}
gaps=[i for i in read(ROOT/'outputs/H19_CAIXA_EXECUCAO_V3.json')['issues']
      if i['kind'] in ('CORPORATE_TAX_AND_DELIVERY','ORDINARY_STOCK_ACTION_DELIVERY_AND_BASIS')]
docs=[];seen=set()
for archive in sorted(BASE.glob('ipe-*.zip')):
    with zipfile.ZipFile(archive) as z:text=z.read(z.namelist()[0]).decode('latin1')
    for d in csv.DictReader(io.StringIO(text),delimiter=';'):
        if d['Categoria'] not in ('Aviso aos Acionistas','Comunicado ao Mercado','Fato Relevante'):continue
        if d['Link_Download'] in seen:continue
        subject=norm(d['Assunto']+' '+d['Tipo'])
        if not any(w in subject for w in ('fraco','fracio','custo','fisc','grupamento','desdobr','bonifica','incorpor','reorganiz','resgate','convers','combinacao','consumacao','cisao')):continue
        cnpj=re.sub(r'\D','',d['CNPJ_Companhia']);matches=[]
        for g in gaps:
            if ids.get(g['ticker'])!=cnpj:continue
            delta=(date.fromisoformat(d['Data_Referencia'])-date.fromisoformat(g['ex_date'])).days
            if -120<=delta<=550:matches.append(g)
        if not matches:continue
        seen.add(d['Link_Download'])
        docs.append({**d,'local_file':f'cvm-corporate-{len(docs):04d}.pdf','matching_requirements':matches})
(BASE/'ipe-corporate-notices.json').write_text(json.dumps(docs,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'work/h19-corporate-source-batch.json').write_text(json.dumps([[r['local_file'],r['Link_Download']] for r in docs],indent=2),encoding='utf-8')
print(json.dumps({'corporate_requirements':len(gaps),'notice_documents':len(docs)}))
