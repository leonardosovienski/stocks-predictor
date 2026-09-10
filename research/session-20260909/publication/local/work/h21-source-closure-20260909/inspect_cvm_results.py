from pathlib import Path
from html.parser import HTMLParser
import re,json
r=Path(r"C:\STOCKS\work\h21-source-closure-20260909")
class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.links=[]
    def handle_data(self,d):
        if d.strip():self.parts.append(d.strip())
    def handle_starttag(self,t,a):
        a=dict(a)
        if t=="a":self.links.append(a)
h=Text();h.feed((r/"raw"/"cvm-bova-fs-query.html").read_text(encoding="iso-8859-15"))
print("\n".join(h.parts[-100:]))
print(h.links[-20:])
(r/"text"/"cvm-bova-fs-query.txt").write_text("\n".join(h.parts),encoding="utf-8")
