from pathlib import Path
import json,base64
from pypdf import PdfReader
r=Path(r"C:\STOCKS\work\h21-source-closure-20260909")
q={"language":"pt-br","typeFund":"ETF","pageNumber":1,"pageSize":20,"keyword":"BOVA"}
u="https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/GetListFunds/"+base64.b64encode(json.dumps(q,separators=(",",":")).encode()).decode()
batch=[{"id":"b3-bova-list","filename":"b3-bova-list.json","url":u,"purpose":"Official BOVA fund identifiers for complete document catalog"}]
for p in PdfReader(r/"raw"/"b3-fee-circular-v5.pdf").pages:
    for a in p.get("/Annots",[]):
        obj=a.get_object()
        if "/A" in obj and "/URI" in obj["/A"]: print(obj["/A"]["/URI"])
(r/"batch-07.json").write_text(json.dumps(batch,indent=2),encoding="utf-8")
