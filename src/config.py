"""Carregador do config.yaml — mini-parser stdlib do subconjunto plano de YAML.

Decisão registrada no HANDOFF (revisão pós-M0): rota stdlib-first. O config usa só
seções de 1 nível com pares chave: valor — não há listas, âncoras, multiline nem
aninhamento profundo. Se o config um dia precisar disso, a decisão de pyyaml volta
ao portão.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "vendor"))
from predictor_core import infra

CONFIG_DEFAULT = pathlib.Path(__file__).parent.parent / "config.yaml"


def _strip_comment(line: str) -> str:
    """Remove comentário '#' fora de aspas."""
    in_quotes = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_quotes = not in_quotes
        elif ch == "#" and not in_quotes:
            return line[:i]
    return line


def _parse_scalar(raw: str):
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        return raw[1:-1]
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def parse_simple_yaml(text: str) -> dict:
    """Parseia o subconjunto: seções top-level e pares 'chave: valor' indentados.

    Linhas não reconhecidas (lista, aninhamento >2 níveis, multiline) levantam
    ValueError — falhar alto é melhor que config silenciosamente ignorado.
    """
    result: dict = {}
    section: str | None = None
    for lineno, rawline in enumerate(text.splitlines(), start=1):
        line = _strip_comment(rawline).rstrip()
        if not line.strip():
            continue
        indented = line[0] in (" ", "\t")
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"linha {lineno}: sem ':' — fora do subconjunto suportado: {rawline!r}")
        key = key.strip()
        value = value.strip()
        if key.startswith("-"):
            raise ValueError(f"linha {lineno}: listas não suportadas pelo mini-parser: {rawline!r}")
        if not indented:
            if value:  # chave top-level com valor direto
                result[key] = _parse_scalar(value)
                section = None
            else:
                section = key
                result[section] = {}
        else:
            if section is None:
                raise ValueError(f"linha {lineno}: chave indentada sem seção: {rawline!r}")
            if not value:
                raise ValueError(f"linha {lineno}: aninhamento >2 níveis não suportado: {rawline!r}")
            result[section][key] = _parse_scalar(value)
    return result


def load_config(path: pathlib.Path | str | None = None) -> dict:
    path = pathlib.Path(path) if path else CONFIG_DEFAULT
    return parse_simple_yaml(path.read_text(encoding="utf-8"))


def config_hash(config: dict) -> str:
    """Hash determinístico do config carregado — gravado em runs.config_hash."""
    return infra.config_hash(config)


# Subconjunto H1-FROZEN (design §5–§9), explícito e legível por máquina — o
# mini-parser apaga os comentários '[H1-FROZEN]' do YAML, então a lista vive AQUI.
H1_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("factor", "name"), ("factor", "lookback_days"), ("factor", "skip_days"),
    ("portfolio", "quantile"), ("portfolio", "weighting"), ("portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"), ("bootstrap", "confidence"),
    # Onda 1 (2026-07-02, PRÉ-DADO): o pedágio inteiro entra no lacre — a H1
    # pré-registra stationary; interval/psr_min fixados antes de qualquer rodada real.
    ("bootstrap", "method"), ("bootstrap", "interval"), ("bootstrap", "psr_min"),
]


def frozen_config_hash(config: dict) -> str:
    """Hash determinístico SÓ do subconjunto H1-FROZEN — o LACRE da hipótese.

    Responde 'este run usou a H1 exata?' sem ser perturbado por params operacionais
    (db_path, seed, benchmark.n_random). Um golden test fixa este hash: mexer num param
    frozen quebra alto; mexer no db_path/seed NÃO. É a versão por-máquina do lacre
    que hoje depende da disciplina de não tocar nos comentários [H1-FROZEN].
    """
    frozen = {f"{s}.{k}": config.get(s, {}).get(k) for s, k in H1_FROZEN_KEYS}
    missing = [k for k, v in frozen.items() if v is None]
    if missing:
        raise ValueError(f"params H1-FROZEN ausentes no config: {missing}")
    return infra.config_hash(frozen)
