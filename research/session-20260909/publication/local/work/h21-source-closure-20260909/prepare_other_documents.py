from pathlib import Path
import re,json,base64
r=Path(r"C:\STOCKS\work\h21-source-closure-20260909")
s=(r/"raw"/"b3-funds-detail.js").read_text(encoding="utf-8")
start=s.index('var Ie=class Ie')
print(s[start:start+7300])
rows=[{"id":"b3-funds-config","filename":"b3-funds-config.json","url":"https://sistemaswebb3-listados.b3.com.br/fundsListedPage/assets/funds.json","purpose":"Official other-document category configuration"}]
q={"language":"pt-br","idCEM":"BOVA","typeFund":"ETF"}
rows.append({"id":"b3-bova-other-categories","filename":"b3-bova-other-categories.json","url":"https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/GetCategoriesDoctoFunds/"+base64.b64encode(json.dumps(q,separators=(",",":")).encode()).decode(),"purpose":"Audit statement document categories"})
(r/"batch-14.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
