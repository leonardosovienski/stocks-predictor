"""Find successor issuer notices omitted by a predecessor-only CNPJ lookup."""
from datetime import date
import csv, io, json, re, unicodedata, zipfile
from pathlib import Path

root=Path(__file__).resolve().parents[1];base=root/'work/h19-cash-expanded-source'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
norm=lambda t:unicodedata.normalize('NFKD',t).encode('ascii','ignore').decode().lower()
obs=read(root/'outputs/h18-h19-reorganization-observation.json')
ids={m['ticker']:m['cnpj'] for t in obs['trials'] for p in t['periods'] for m in p['members']}
terms=read(root/'work/value-event-terms/reorganizations.json')['events']
existing={d['Link_Download'] for d in read(base/'ipe-corporate-notices.json')}
docs=[];seen=set(existing)
for archive in sorted(base.glob('ipe-*.zip')):
    with zipfile.ZipFile(archive) as z:text=z.read(z.namelist()[0]).decode('latin1')
    for d in csv.DictReader(io.StringIO(text),delimiter=';'):
        if d['Categoria'] not in ('Aviso aos Acionistas','Comunicado ao Mercado','Fato Relevante'):continue
        if d['Link_Download'] in seen:continue
        subject=norm(d['Assunto']+' '+d['Tipo'])
        if not any(w in subject for w in ('fraco','fracio','custo','fisc','grupamento','desdobr','bonifica','incorpor','reorganiz','resgate','convers','combinacao','consumacao','cisao','conclusao','concluida','fechamento')):continue
        cnpj=re.sub(r'\D','',d['CNPJ_Companhia']);matches=[]
        for e in terms:
            candidates={ids.get(e['ticker']),*(ids.get(s['ticker']) for s in e['stocks'])}
            if cnpj not in candidates:continue
            delta=(date.fromisoformat(d['Data_Referencia'])-date.fromisoformat(e['ex_date'])).days
            if -120<=delta<=550:matches.append({'ticker':e['ticker'],'ex_date':e['ex_date']})
        if not matches:continue
        seen.add(d['Link_Download'])
        docs.append({**d,'local_file':f'cvm-successor-{len(docs):04d}.pdf','matching_requirements':matches})
(base/'ipe-successor-notices.json').write_text(json.dumps(docs,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'work/h19-successor-source-batch.json').write_text(json.dumps([[r['local_file'],r['Link_Download']] for r in docs],indent=2),encoding='utf-8')
print(json.dumps({'documents':len(docs),'successor_cnpj_missing':sorted({s['ticker'] for e in terms for s in e['stocks'] if s['ticker'] not in ids})}))
