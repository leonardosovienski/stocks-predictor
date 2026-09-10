import json,base64
from pathlib import Path
r=Path(r"C:\STOCKS\work\h21-source-closure-20260909")
base={"language":"pt-br","idFNET":"990","idCEM":"BOVA","typeFund":"ETF"}
rows=[]
for endpoint,ident,q in [
("GetDetailFund","b3-bova-detail",base),
("GetCategories","b3-bova-categories",dict(base,dateInitial="2017-01-01",dateFinal="2026-09-08",pageNumber=1,pageSize=20)),
]:
    rows.append({"id":ident,"filename":ident+".json","url":"https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/"+endpoint+"/"+base64.b64encode(json.dumps(q,separators=(",",":")).encode()).decode(),"purpose":"BOVA11 public regulatory document discovery; no returns"})
(r/"batch-09.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
