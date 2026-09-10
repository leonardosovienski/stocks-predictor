from pathlib import Path
import json,base64
r=Path(r"C:\STOCKS\work\h21-source-closure-20260909")
q={"language":"pt-br","idFNET":"990","typeFund":"ETF","category":7,"dateInitial":"2018-01-01","dateFinal":"2018-12-31","pageNumber":1,"pageSize":20}
rows=[{"id":"b3-bova-report-2018","filename":"b3-bova-report-2018.json","url":"https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/GetReportsRelevants/"+base64.b64encode(json.dumps(q,separators=(",",":")).encode()).decode(),"purpose":"Annual date filter consistent with official UI; verify 2018 report"}]
rows.append({"id":"b3-bova-audited-docs","filename":"b3-bova-audited-docs.json","url":"https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/GetListDocsFunds","json_body":{"language":"pt-br","idCEM":"BOVA","typeFund":"ETF","category":"DemonstrativosFinanceirosERelatorios","dateInitial":"2017-01-01","dateFinal":"2026-09-08","pageNumber":1,"pageSize":60,"keyword":""},"purpose":"Official B3 archive of audited financial statements"})
(r/"batch-16.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
