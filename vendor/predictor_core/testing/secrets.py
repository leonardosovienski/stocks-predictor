"""Guard de vazamento de segredos na telemetria (predictor_core.testing.secrets).

A telemetria (`obs.emit_event`) é append-only e commitada como trilha de auditoria. Um
segredo que caia no `metadata` de um evento vira credencial pública para sempre. Este
módulo varre texto/eventos por padrões de segredo conhecidos e transforma um vazamento
acidental em falha de pytest ANTES do commit.

stdlib-only (regex). Conservador por construção: cada padrão exige um marcador literal
forte (`sk-`, `AKIA`, `xox…`, cabeçalho de chave privada, ou uma atribuição explícita
`token=…`) — números, tickers e scores da telemetria normal NÃO disparam.
"""
import json
import re
from pathlib import Path

# (nome, regex). Cada padrão exige um marcador forte para não gerar falso-positivo
# na telemetria numérica normal ({"psr": 0.96, "asset": "PETR4"}).
_PATTERNS = [
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z\-_]{20,}")),
    ("private_key_header", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    # atribuição explícita: senha/segredo/token/apikey = "<>=16 chars não-triviais"
    ("secret_assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|passphrase|"
        r"authorization|auth[_-]?token|access[_-]?token|client[_-]?secret)"
        r"['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9/+=_\-]{16,})")),
]


def find_secrets(text) -> list:
    """Retorna [(nome_padrão, trecho)] para cada segredo detectado em `text`.

    Lista vazia = limpo. Entrada não-str é serializada (JSON) antes da varredura, para
    aceitar um dict de metadata direto.
    """
    if text is None:
        return []
    if not isinstance(text, str):
        try:
            text = json.dumps(text, ensure_ascii=False, sort_keys=True, default=str)
        except (TypeError, ValueError):
            text = str(text)
    hits = []
    for name, pat in _PATTERNS:
        for m in pat.finditer(text):
            hits.append((name, m.group(0)))
    return hits


def assert_no_secrets_in_events(path) -> int:
    """Varre um JSONL de eventos (obs.emit_event) por segredos. No-op se o arquivo não
    existe (telemetria ainda não gerada). Levanta AssertionError com a trilha se achar.
    Retorna o nº de eventos varridos."""
    p = Path(path)
    if not p.exists():
        return 0
    n = 0
    leaks = []
    for lineno, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not ln.strip():
            continue
        n += 1
        try:
            record = json.loads(ln)
        except json.JSONDecodeError:
            record = ln  # varre a linha crua mesmo se não for JSON válido
        hits = find_secrets(record)
        if hits:
            names = ", ".join(sorted({name for name, _ in hits}))
            leaks.append(f"  linha {lineno}: {names}")
    if leaks:
        raise AssertionError(
            f"segredo(s) vazado(s) na telemetria {p}:\n" + "\n".join(leaks))
    return n
