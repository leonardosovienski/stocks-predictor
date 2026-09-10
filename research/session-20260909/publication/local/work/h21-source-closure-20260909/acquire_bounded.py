"""Single-process, wall-time-bounded public source capture; no credentials."""
import concurrent.futures, datetime, hashlib, json, subprocess, sys, threading, urllib.parse
from pathlib import Path
ROOT=Path(r"C:\STOCKS\work\h21-source-closure-20260909")
RAW=ROOT/"raw"; JOURNAL=ROOT/"acquisition.jsonl"; LOCK=threading.Lock()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def capture(row):
    target=(RAW/row["filename"]).resolve()
    assert target.is_relative_to(RAW.resolve()) and not target.exists()
    record=dict(id=row["id"],url=row["url"],purpose=row["purpose"],started_at_utc=now(),path=str(target),status="attempted")
    with LOCK:
        prior=[json.loads(s) for s in JOURNAL.read_text(encoding="utf-8").splitlines()]
        assert len({r["id"] for r in prior})<80 and not any(r["id"]==row["id"] for r in prior)
        assert sum(r.get("bytes",0) for r in prior if r["status"]=="downloaded")<800000000
        with JOURNAL.open("a",encoding="utf-8") as out: out.write(json.dumps(record)+"\n")
    partial=target.with_name(target.name+".partial")
    headers=target.with_name(target.name+".headers")
    try:
        extra=[]
        if "json_body" in row:
            extra=["--header","Content-Type: application/json","--data-binary",json.dumps(row["json_body"],ensure_ascii=False)]
            record["json_body"]=row["json_body"]
        if "form_body" in row:
            encoded=urllib.parse.urlencode(row["form_body"])
            extra=["--header","Content-Type: application/x-www-form-urlencoded","--data-binary",encoded]
            record["public_form_body_sha256"]=hashlib.sha256(encoded.encode()).hexdigest()
        if "range" in row:
            extra=["--range",row["range"],"--header","If-Range: "+row["if_range"]]
            record.update(range=row["range"],if_range=row["if_range"])
        cp=subprocess.run([r"C:\WINDOWS\system32\curl.exe","--location","--fail","--silent","--show-error","--connect-timeout","12","--max-time","45","--max-filesize",str(row.get("max_bytes",25000000)),"--user-agent","Mozilla/5.0","--dump-header",str(headers),"--output",str(partial),"--write-out","%{json}",*extra,row["url"]],capture_output=True,timeout=50)
        record["curl_exit_code"]=cp.returncode
        if cp.stdout:
            meta=json.loads(cp.stdout)
            record.update(http_status=meta.get("http_code"),final_url=meta.get("url_effective"),content_type=meta.get("content_type"))
        if cp.returncode: raise RuntimeError(cp.stderr.decode("utf-8",errors="replace"))
        if "range" in row and record.get("http_status")!=206: raise ValueError("Range request not honored")
        if target.suffix.lower()==".pdf" and partial.read_bytes()[:5]!=b"%PDF-": raise ValueError("Not PDF")
        with partial.open("rb") as src: digest=hashlib.file_digest(src,"sha256").hexdigest()
        partial.rename(target)
        record.update(status="downloaded",bytes=target.stat().st_size,sha256=digest)
    except Exception as e:
        record.update(status="failed",error_type=type(e).__name__,error=str(e))
        if partial.exists(): record["partial_bytes"]=partial.stat().st_size
    record["completed_at_utc"]=now()
    with LOCK:
        with JOURNAL.open("a",encoding="utf-8") as out: out.write(json.dumps(record,ensure_ascii=False)+"\n")
    target.with_name(target.name+".source.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:record[k] for k in ("id","status","bytes","error") if k in record}),flush=True)
if __name__=="__main__":
    rows=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: list(pool.map(capture,rows))
