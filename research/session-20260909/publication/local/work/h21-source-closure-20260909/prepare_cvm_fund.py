from pathlib import Path
from html.parser import HTMLParser
import json
r=Path(r"C:\STOCKS\work\h21-source-closure-20260909")
class Inputs(HTMLParser):
    def __init__(self): super().__init__(); self.values={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="input" and a.get("type")=="hidden": self.values[a["name"]]=a.get("value","")
h=Inputs();h.feed((r/"raw"/"cvm-legacy-fs-form.html").read_text(encoding="latin-1"))
h.values.update({"txtCNPJNome":"10406511000161","dataRefIni:ddDia":"1","dataRefIni:ddMes":"1","dataRefIni:ddAno":"2017","dataRefFim:ddDia":"8","dataRefFim:ddMes":"9","dataRefFim:ddAno":"2026","btConsulta":"Buscar"})
rows=[{"id":"cvm-bova-fs-query","filename":"cvm-bova-fs-query.html","url":"https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/DemContabeis/CPublicaDemContabeis.aspx","form_body":h.values,"purpose":"Public CVM audit statement lookup by fund CNPJ,2017-cutoff; no user financial data"}]
docs=json.loads((r/"raw"/"b3-bova-audited-docs.json").read_text(encoding="utf-8"))["results"]
for d in docs:
    if "2018" not in d["subject"]:continue
    rows.append({"id":"b3-bova-fs-2018","filename":"bova-fs-2018.pdf","url":"https://documentos-fundos.b3.com.br/documents/d/guest/"+d["urlReport"],"purpose":"Full audited financial statement March2018 includes prior year comparison"})
(r/"batch-17.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
