from pathlib import Path
import re,json
r=Path(r"C:\STOCKS\work\h21-source-closure-20260909\raw")
s=(r/"b3-funds-detail.js").read_text()
print("\n".join(re.findall(r'from"[^"]+"|import\([^)]*\)|.{0,100}funds-events.{0,180}',s)[:15]))
s=(r/"b3-fees-v5-page.html").read_text(encoding="utf-8",errors="replace")
print("\n".join(re.findall(r'href="([^"]+\.pdf[^"]*)"',s)))
detail=json.loads((r/"b3-bova-detail.json").read_text())
print(type(detail),str(detail)[:5000])
