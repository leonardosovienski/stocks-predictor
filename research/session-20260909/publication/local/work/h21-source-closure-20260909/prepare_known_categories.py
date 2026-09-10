from pathlib import Path
import json,base64
r=Path(r"C:\STOCKS\work\h21-source-closure-20260909")
print((r/"raw"/"b3-bova-other-categories.json").read_text(encoding="utf-8"))
rows=[]
for ident,categories in (("990",[1,2,5,7,11]),("19674",[2,3,11])):
    for category in categories:
        q={"language":"pt-br","idFNET":ident,"typeFund":"ETF","category":category,"dateInitial":"2018-01-01","dateFinal":"2026-09-08","pageNumber":1,"pageSize":120}
        name=f"b3-filings-{ident}-{category}"
        rows.append({"id":name,"filename":name+".json","url":"https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/GetReportsRelevants/"+base64.b64encode(json.dumps(q,separators=(",",":")).encode()).decode(),"purpose":"All documented categories across 2018-2026; check count against per-year inventory"})
(r/"batch-15.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
