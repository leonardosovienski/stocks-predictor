import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'work/stocks-predictor/stocks_predictor'),str(ROOT/'work/runtime')]
import cvm_pit

dfp=next((ROOT/'work/raw').glob('*dfp*.zip'))
fre=next((ROOT/'work/raw').glob('*fre*.zip'))
payload=dfp.read_bytes()
rows=cvm_pit.derive_dfp(payload,2023)
report=cvm_pit.summary(payload,2023)
report['examples']=[r for r in rows if r['cnpj'] in ('07526557000100','00864214000106')]
fr=cvm_pit.derive_fre_shares(fre.read_bytes(),2023)
report['fre']={'documents':len(fr),'eligible_basis':sum(bool(r['basis_date'] and r['price_basis_source']) for r in fr),
               'source_sha256':hashlib.sha256(fre.read_bytes()).hexdigest(),
               'bbas':[r for r in fr if 'bco_brasil' in r['company']]}
(ROOT/'outputs/repair-real-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
with zipfile.ZipFile(fre) as z:
    for name in z.namelist():
        if any(s in name.lower() for s in ('capital_social','capital_emitido','distribuicao_capital')):
            with z.open(name) as f:
                print(name, next(csv.reader(io.TextIOWrapper(f,encoding='latin-1'),delimiter=';')))
