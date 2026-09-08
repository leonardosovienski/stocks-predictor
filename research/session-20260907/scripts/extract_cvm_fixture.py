import hashlib
import json
import pathlib
import zipfile
import csv
import io
from inspect_state import ROOT, REPO

out=REPO/'tests/fixtures/cvm_dfp_2023'
out.mkdir(parents=True,exist_ok=True)
src=ROOT/'work/raw/dfp_cia_aberta_2023.zip'
cnpjs={'07.526.557/0001-00','00.864.214/0001-06'}
files=[]
with zipfile.ZipFile(src) as z:
    for name in ('dfp_cia_aberta_2023.csv', 'dfp_cia_aberta_BPA_con_2023.csv', 'dfp_cia_aberta_BPP_con_2023.csv', 'dfp_cia_aberta_DRE_con_2023.csv','dfp_cia_aberta_DFC_MI_con_2023.csv'):
        raw=z.read(name).decode('latin-1')
        rows=list(csv.reader(io.StringIO(raw),delimiter=';'))
        header=rows[0]
        keep=[header]
        for row in rows[1:]:
            r=dict(zip(header,row))
            if r.get('CNPJ_CIA') not in cnpjs: continue
            if 'ORDEM_EXERC' in r and (r['ORDEM_EXERC']!='ÚLTIMO' or r['CD_CONTA'] not in {'1','2','2.03','3.01','6.01'}): continue
            keep.append(row)
        buf=io.StringIO(newline='')
        csv.writer(buf,delimiter=';',lineterminator='\n').writerows(keep)
        payload=buf.getvalue().encode('latin-1')
        (out/name).write_bytes(payload)
        files.append({'name':name,'rows':len(keep)-1,'sha256':hashlib.sha256(payload).hexdigest()})
manifest={'source_url':'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2023.zip',
          'downloaded_at_utc':'2026-09-07','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
          'encoding':'latin-1','selection':'AMBEV and ENERGISA, fixed accounts 1/2/2.03/3.01/6.01, ULTIMO; main includes all versions. Exact field content; CSV quoting/EOL normalized. No price or return data.',
          'files':files}
(out/'provenance.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(files)
