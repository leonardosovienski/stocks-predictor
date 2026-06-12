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
