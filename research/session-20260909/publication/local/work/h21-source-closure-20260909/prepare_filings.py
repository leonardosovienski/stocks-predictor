from pathlib import Path
import json,base64
r=Path(r"C:\STOCKS\work\h21-source-closure-20260909")
rows=[]
def add(endpoint,ident,q):
    rows.append({"id":ident,"filename":ident+".json","url":"https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/"+endpoint+"/"+base64.b64encode(json.dumps(q,separators=(",",":")).encode()).decode(),"purpose":"Read-only fund filings with explicit full date range and pagination counts"})
base={"language":"pt-br","idFNET":"990","typeFund":"ETF","dateInitial":"2018-01-01","dateFinal":"2026-09-08","pageNumber":1,"pageSize":120}
add("GetReportsRelevants","b3-bova-filings-all",dict(base,category=0))
add("GetReportsRelevants","b3-bova-class-filings-all",dict(base,idFNET="19674",category=0))
add("GetTypesReport","b3-bova-report-types",dict(base,dateInitial="2025-01-01",dateFinal="2025-12-31"))
add("GetTypesReport","b3-bova-class-report-types",dict(base,idFNET="19674",dateInitial="2026-01-01"))
(r/"batch-13.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
