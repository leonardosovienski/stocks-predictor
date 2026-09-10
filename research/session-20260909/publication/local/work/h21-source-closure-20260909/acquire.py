"""Bounded public-source capture. Originals and failed requests are retained."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, threading, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(r"C:\STOCKS\work\h21-source-closure-20260909")
RAW=ROOT/"raw"; JOURNAL=ROOT/"acquisition.jsonl"
LOCK=threading.Lock()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def capture(row):
    identifier=row["id"]
    if not identifier.replace("-","").replace("_","").isalnum(): raise ValueError("Invalid source id")
    target=(RAW/row["filename"]).resolve()
    if not target.is_relative_to(RAW.resolve()) or target.exists(): raise ValueError("Unsafe/existing destination")
    record={"id":identifier,"url":row["url"],"purpose":row["purpose"],"started_at_utc":now(),"path":str(target),"status":"attempted"}
    with LOCK:
        prior=[json.loads(x) for x in JOURNAL.read_text(encoding="utf-8").splitlines()] if JOURNAL.exists() else []
        if len({r["id"] for r in prior})>=80: raise ValueError("Acquisition request budget exhausted")
        if any(r["id"]==identifier for r in prior): raise ValueError("ID already attempted")
        if sum(r.get("bytes",0) for r in prior if r["status"]=="downloaded")>=800_000_000: raise ValueError("Byte budget exhausted")
        with JOURNAL.open("a",encoding="utf-8") as journal: journal.write(json.dumps(record)+"\n")
    temporary=target.with_name(target.name+".partial")
    try:
        request=urllib.request.Request(row["url"],headers={"User-Agent":"Mozilla/5.0 (compatible; StocksResearch/1.0; public documentary validation)","Accept":"*/*"})
        limit=row.get("max_bytes",25_000_000); size=0; digest=hashlib.sha256()
        with urllib.request.urlopen(request,timeout=40) as response,temporary.open("xb") as stream:
            record.update({"final_url":response.url,"http_status":response.status,"content_type":response.headers.get("Content-Type"),"last_modified":response.headers.get("Last-Modified")})
            while block:=response.read(1024*1024):
                size+=len(block)
                if size>limit: raise ValueError("Source size exceeds preregistered request limit")
                stream.write(block); digest.update(block)
        if target.suffix.lower()==".pdf" and temporary.read_bytes()[:5]!=b"%PDF-": raise ValueError("Response is not a PDF")
        with temporary.open("rb") as stream:
            if hashlib.file_digest(stream,"sha256").hexdigest()!=digest.hexdigest(): raise ValueError("Written bytes differ")
        os.rename(temporary,target)
        record.update({"status":"downloaded","bytes":size,"sha256":digest.hexdigest()})
    except Exception as error:
        record.update({"status":"failed","error_type":type(error).__name__,"error":str(error)})
        if isinstance(error,urllib.error.HTTPError): record["http_status"]=error.code
        if temporary.exists(): record["partial_bytes"]=temporary.stat().st_size
    record["completed_at_utc"]=now()
    with LOCK:
        with JOURNAL.open("a",encoding="utf-8") as journal: journal.write(json.dumps(record,ensure_ascii=False)+"\n")
    target.with_name(target.name+".source.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:record[k] for k in ("id","status","bytes","sha256","error") if k in record}),flush=True)
    return record
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("batch",type=Path);args=parser.parse_args()
    RAW.mkdir(parents=True,exist_ok=True)
    rows=json.loads(args.batch.read_text(encoding="utf-8-sig"))
    with ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(capture,rows))
    print(json.dumps({"downloaded":sum(r["status"]=="downloaded" for r in results),"failed":sum(r["status"]=="failed" for r in results)}),flush=True)

