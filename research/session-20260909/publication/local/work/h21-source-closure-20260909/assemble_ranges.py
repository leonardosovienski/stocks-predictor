from pathlib import Path
import hashlib,json,zipfile,datetime,shutil
r=Path(r"C:\STOCKS\work\h21-source-closure-20260909")
a=r/"raw"/"COTAHIST_A2026.latest.ZIP"; b=r/"raw"/"COTAHIST_A2026.tail.bin"; out=r/"raw"/"COTAHIST_A2026.complete.ZIP"
assert not out.exists()
def sha(p):
    with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
for p in (a,b):
    receipt=json.loads(p.with_name(p.name+".source.json").read_text())
    assert sha(p)==receipt["sha256"]
headers=b.with_name(b.name+".headers").read_text()
assert "71736503-74185997/74185998" in headers and '"3ad8b333ef3fdd1:0"' in headers
assert a.stat().st_size==71736503 and b.stat().st_size==2449495
with out.open("xb") as f:
    for p in (a,b):
        with p.open("rb") as src: shutil.copyfileobj(src,f)
assert out.stat().st_size==74185998
receipt={"id":"b3-cotahist-2026-complete","kind":"EXACT_RANGE_REASSEMBLY","url":"https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A2026.ZIP","sha256":sha(out),"bytes":out.stat().st_size,"parts":[{"path":str(p),"sha256":sha(p)} for p in (a,b)],"completed_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"etag":'"3ad8b333ef3fdd1:0"',"source_last_modified":"2026-09-09T00:07:28Z","crc_status":"pending_full_member_read","initial_download_status":"transport completed but truncated; ZIP failed validation; no prices accepted"}
out.with_name(out.name+".source.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
print(json.dumps(receipt))
