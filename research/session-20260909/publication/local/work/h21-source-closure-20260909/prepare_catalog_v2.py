from pathlib import Path
import re,json,base64
r=Path(r"C:\STOCKS\work\h21-source-closure-20260909")
for name in ("b3-funds-detail.js","b3-funds-common.js"):
    s=(r/"raw"/name).read_text(encoding="utf-8")
    print(name)
    print("\n".join(re.findall(r'.{0,130}(?:getCash|getSubscription|GetStock|GetCash|GetProvent|GetShare|GetEvent|eventsService|urlSIGPreviousDocument|idCEM=this).{0,350}',s)[:22]))
rows=[]
for endpoint,ident,q in [
("GetListClassFund","b3-bova-classes",{"language":"pt-br","idFNET":"990","idCEM":"BOVA","typeFund":"ETF"}),
("GetCategories","b3-bova-categories-2026",{"language":"pt-br","idFNET":"990","typeFund":"ETF","dateInitial":"2026-01-01","dateFinal":"2026-09-08","pageNumber":1,"pageSize":20})]:
    rows.append({"id":ident,"filename":ident+".json","url":"https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/"+endpoint+"/"+base64.b64encode(json.dumps(q,separators=(",",":")).encode()).decode(),"purpose":"Verify fund/class identity and narrower official document catalog"})
(r/"batch-11.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
