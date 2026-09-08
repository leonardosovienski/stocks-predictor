"""Verify shell-wrapper outputs and every delivered package payload."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

CHAT = Path(r"C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2")
ROOT = Path(r"C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907")
WORK = ROOT / "work/h20-remediation-20260908"
ARCHIVE = ROOT / "work/stocks-predictor/research/session-20260908/h20-remediation"
OUT = CHAT/"outputs"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


assert (WORK/"readiness-wrapper.json").read_bytes() == (WORK/"readiness-02.json").read_bytes()
assert (WORK/"h20-wrapper.json").read_bytes() == (WORK/"h20-checked.json").read_bytes()
validation = json.loads((ARCHIVE/"VALIDACAO_CORRECOES.json").read_text(encoding="utf-8"))
validation["powershell_wrappers"] = {"readiness_exit_code": 2, "reproduction_exit_code": 0,
                                     "both_byte_identical": True}
raw = (json.dumps(validation, indent=2, ensure_ascii=False)+"\n").encode("utf-8")
for path in [ARCHIVE/"VALIDACAO_CORRECOES.json", OUT/"VALIDACAO_CORRECOES.json"]:
    path.write_bytes(raw)
shutil.copyfile(__file__, ARCHIVE/"finalize_remediation.py")
manifest = {p.name: sha(p.read_bytes()) for p in sorted(ARCHIVE.iterdir())
            if p.is_file() and p.name != "MANIFEST.json"}
(ARCHIVE/"MANIFEST.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8", newline="\n")
target = OUT/"CORRECOES_STOCKS_REPRODUZIVEIS.zip"
with zipfile.ZipFile(target) as z:
    payloads = {n: z.read(n) for n in z.namelist() if n != "PACKAGE_SHA256.json"}
payloads.update({p.name: p.read_bytes() for p in ARCHIVE.iterdir() if p.is_file()})
package_manifest = {n: sha(raw) for n, raw in sorted(payloads.items())}
payloads["PACKAGE_SHA256.json"] = (json.dumps(package_manifest, indent=2)+"\n").encode("utf-8")
temp = WORK/"final-package.zip"
with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for name, raw in payloads.items():
        z.writestr(name, raw)
with zipfile.ZipFile(temp) as z:
    assert z.testzip() is None
    received = json.loads(z.read("PACKAGE_SHA256.json"))
    assert set(received) == set(z.namelist()) - {"PACKAGE_SHA256.json"}
    assert all(sha(z.read(n)) == expected for n, expected in received.items())
assert target.resolve().parent == OUT.resolve()
temp.replace(target)
print(json.dumps({"verified_payloads": len(package_manifest), "package_sha256": sha(target.read_bytes()),
                  "bytes": target.stat().st_size}))
