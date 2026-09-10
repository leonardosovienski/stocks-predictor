from pathlib import Path
import json,base64
r=Path(r"C:\STOCKS\work\h21-source-closure-20260909")
rows=[]
def add(endpoint,ident,q):
    rows.append({"id":ident,"filename":ident+".json","url":"https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/"+endpoint+"/"+base64.b64encode(json.dumps(q,separators=(",",":")).encode()).decode(),"purpose":"BOVA official fund/class filings and investor-level corporate action inventory"})
add("GetEventsCorporateActions","b3-bova-events",{"language":"pt-br","idCEM":"BOVA"})
for year in range(2017,2026):
    add("GetCategories",f"b3-bova-categories-{year}",{"language":"pt-br","idFNET":"990","typeFund":"ETF","dateInitial":f"{year}-01-01","dateFinal":f"{year}-12-31","pageNumber":1,"pageSize":20})
add("GetCategories","b3-bova-class-categories-2026",{"language":"pt-br","idFNET":"19674","typeFund":"ETF","dateInitial":"2026-01-01","dateFinal":"2026-09-08","pageNumber":1,"pageSize":20})
(r/"batch-12.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
print("Attempts prior:",len({json.loads(s)["id"] for s in (r/"acquisition.jsonl").read_text(encoding="utf-8").splitlines()}))
