"""Prove frozen-artifact quality exceptions do not weaken new code gates."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="quality-control-", dir=ROOT) as temporary:
        control = Path(temporary) / "new_non_frozen_file.py"
        control.write_text(
            "import os\nvalue: dict[str, int] = {}\nvalue['wrong'] = 'not-an-int'\n",
            encoding="utf-8",
            newline="\n",
        )
        ruff = _run(["ruff", "check", "--config", str(ROOT / "pyproject.toml"), str(control)])
        pyright = _run(["pyright", "--project", str(ROOT / "pyproject.toml"), str(control)])
        if ruff.returncode == 0 or "F401" not in ruff.stdout + ruff.stderr:
            raise RuntimeError("frozen F401 exception leaked to new non-frozen code")
        if pyright.returncode == 0 or "cannot be assigned" not in pyright.stdout + pyright.stderr:
            raise RuntimeError("frozen Pyright exception leaked to new non-frozen code")
    print("PASS: frozen exceptions are exact and equivalent new code remains gated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
