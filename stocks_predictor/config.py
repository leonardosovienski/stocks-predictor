"""Carregador do config.yaml — mini-parser stdlib do subconjunto plano de YAML.

Decisão registrada no HANDOFF (revisão pós-M0): rota stdlib-first. O config usa só
seções de 1 nível com pares chave: valor — não há listas, âncoras, multiline nem
aninhamento profundo. Se o config um dia precisar disso, a decisão de pyyaml volta
ao portão.

Atualização (2026-08-24): o portão foi aberto para o domínio RJ — `config_rj.yaml` tem
3 níveis e é lido com pyyaml (ver HANDOFF, tabela de dependências). Este parser e o
`config.yaml` do domínio de ações seguem stdlib, sem pyyaml.
"""
import pathlib

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
]


def _frozen_hash(config: dict, keys: list, label: str) -> str:
    """Mecanismo comum dos LACRES: hash determinístico só do subconjunto
    congelado de uma hipótese. Golden tests fixam cada hash — mexer num param
    frozen quebra alto; mexer em param operacional (db_path, seed) NÃO."""
    frozen = {f"{s}.{k}": config.get(s, {}).get(k) for s, k in keys}
    missing = [k for k, v in frozen.items() if v is None]
    if missing:
        raise ValueError(f"params {label} ausentes no config: {missing}")
    return infra.config_hash(frozen)


def frozen_config_hash(config: dict) -> str:
    """Hash determinístico SÓ do subconjunto H1-FROZEN — o LACRE da hipótese.

    Responde 'este run usou a H1 exata?' sem ser perturbado por params operacionais
    (db_path, seed, bootstrap.method). É a versão por-máquina do lacre que
    depende da disciplina de não tocar nos comentários [H1-FROZEN]."""
    return _frozen_hash(config, H1_FROZEN_KEYS, "H1-FROZEN")


# Subconjunto H2-FROZEN (pré-registro 2026-07-16, HANDOFF). Inclui os params
# COMPARTILHADOS com a H1 (universo/execução/janela/bootstrap — mesmos valores,
# reuso declarado) + os próprios da H2. bootstrap.method entra aqui porque a H2
# pré-registra stationary explicitamente (na H1 era operacional).
H2_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h2_factor", "name"), ("h2_factor", "lookback_days"),
    ("h2_portfolio", "quantile"), ("h2_portfolio", "weighting"),
    ("h2_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h2_criteria", "dsr_min"),
]


def h2_frozen_config_hash(config: dict) -> str:
    """O LACRE da H2 — mesmo mecanismo do frozen_config_hash da H1."""
    return _frozen_hash(config, H2_FROZEN_KEYS, "H2-FROZEN")


# Subconjunto H4-FROZEN (pré-registro 2026-07-18, HANDOFF). Sizing sobre o
# universo inteiro — não há chaves de quantil/seleção; o resto é o mesmo
# reuso declarado de universo/execução/janela/bootstrap de H1/H2.
H4_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h4_weighting", "name"), ("h4_weighting", "vol_lookback_days"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h4_criteria", "dsr_min"), ("h4_criteria", "require_maxdd_not_worse"),
]


def h4_frozen_config_hash(config: dict) -> str:
    """O LACRE da H4 — mesmo mecanismo dos lacres de H1/H2."""
    return _frozen_hash(config, H4_FROZEN_KEYS, "H4-FROZEN")


# Subconjunto H5-FROZEN (pré-registro 2026-07-18, HANDOFF). Reversão de curto
# prazo (21 pregões, quintil inferior) — mesmo reuso declarado de
# universo/execução/janela/bootstrap das anteriores.
H5_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h5_factor", "name"), ("h5_factor", "lookback_days"), ("h5_factor", "skip_days"),
    ("h5_portfolio", "quantile"), ("h5_portfolio", "weighting"),
    ("h5_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h5_criteria", "dsr_min"),
]


def h5_frozen_config_hash(config: dict) -> str:
    """O LACRE da H5 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H5_FROZEN_KEYS, "H5-FROZEN")


# Subconjunto H6-FROZEN (pré-registro 2026-08-27, HANDOFF). Momentum 6-1 —
# mesma família da H1, janela mais curta — mesmo reuso declarado de
# universo/execução/janela/bootstrap das anteriores.
H6_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h6_factor", "name"), ("h6_factor", "lookback_days"), ("h6_factor", "skip_days"),
    ("h6_portfolio", "quantile"), ("h6_portfolio", "weighting"),
    ("h6_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h6_criteria", "dsr_min"),
]


def h6_frozen_config_hash(config: dict) -> str:
    """O LACRE da H6 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H6_FROZEN_KEYS, "H6-FROZEN")


# Subconjunto H8-FROZEN (pré-registro 2026-08-27, HANDOFF). Filtro duplo
# momentum ∩ baixa vol — reuso declarado de universo/execução/janela/bootstrap.
H8_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h8_factor", "momentum_lookback_days"), ("h8_factor", "momentum_skip_days"),
    ("h8_factor", "vol_lookback_days"),
    ("h8_portfolio", "momentum_quantile"), ("h8_portfolio", "vol_quantile"),
    ("h8_portfolio", "weighting"), ("h8_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h8_criteria", "dsr_min"),
]


def h8_frozen_config_hash(config: dict) -> str:
    """O LACRE da H8 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H8_FROZEN_KEYS, "H8-FROZEN")


# Subconjunto H7-FROZEN (pré-registro 2026-09-03, HANDOFF). Fator de qualidade
# (ROE isolado, quintil superior) — 1ª hipótese sobre dado contábil (DFP da
# CVM), não sobre preço/momentum/vol. Reuso declarado de
# universo/execução/janela/bootstrap das anteriores.
H7_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h7_factor", "name"), ("h7_factor", "disclosure_embargo_days"),
    ("h7_portfolio", "quantile"), ("h7_portfolio", "weighting"),
    ("h7_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h7_criteria", "dsr_min"),
]


def h7_frozen_config_hash(config: dict) -> str:
    """O LACRE da H7 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H7_FROZEN_KEYS, "H7-FROZEN")


# Subconjunto H9-FROZEN (pré-registro 2026-09-04, HANDOFF). Fator de
# qualidade, alavancagem isolada (quintil inferior) — 2ª hipótese sobre dado
# contábil (DFP da CVM), mesma fonte da H7. Reuso declarado de
# universo/execução/janela/bootstrap das anteriores.
H9_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h9_factor", "name"), ("h9_factor", "disclosure_embargo_days"),
    ("h9_portfolio", "quantile"), ("h9_portfolio", "weighting"),
    ("h9_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h9_criteria", "dsr_min"),
]


def h9_frozen_config_hash(config: dict) -> str:
    """O LACRE da H9 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H9_FROZEN_KEYS, "H9-FROZEN")


# Subconjunto H10-FROZEN (pré-registro 2026-09-04, HANDOFF). Filtro duplo
# ROE ∩ baixa alavancagem — mesmo racional da H8 (momentum∩baixa-vol), agora
# sobre as duas variáveis contábeis da H7/H9.
H10_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h10_factor", "roe_disclosure_embargo_days"),
    ("h10_factor", "leverage_disclosure_embargo_days"),
    ("h10_portfolio", "roe_quantile"), ("h10_portfolio", "leverage_quantile"),
    ("h10_portfolio", "weighting"), ("h10_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h10_criteria", "dsr_min"),
]


def h10_frozen_config_hash(config: dict) -> str:
    """O LACRE da H10 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H10_FROZEN_KEYS, "H10-FROZEN")


# Subconjunto H11-FROZEN (pré-registro 2026-09-04, HANDOFF). Momentum 12-1
# (mesmo sinal da H1) sobre RETORNO TOTAL em vez de só-preço, janela
# restrita 2018-2022 (cobertura real de `dividends`). `h11_backtest.
# test_start/test_end` substituem `backtest.test_start`/`purge_embargo_months`
# do reuso padrão porque a janela É diferente por desenho, não por reuso.
H11_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h11_factor", "name"), ("h11_factor", "lookback_days"), ("h11_factor", "skip_days"),
    ("h11_portfolio", "quantile"), ("h11_portfolio", "weighting"),
    ("h11_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"),
    ("h11_backtest", "test_start"), ("h11_backtest", "test_end"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h11_criteria", "dsr_min"),
]


def h11_frozen_config_hash(config: dict) -> str:
    """O LACRE da H11 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H11_FROZEN_KEYS, "H11-FROZEN")


# Subconjunto H12-FROZEN (pré-registro 2026-09-04, HANDOFF). Fator de
# qualidade, margem líquida isolada (top quintile) — 3ª variável contábil
# independente da DFP (depois de ROE/H7 e alavancagem/H9), mesma fonte/
# embargo. Reuso declarado de universo/execução/janela/bootstrap.
H12_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h12_factor", "name"), ("h12_factor", "disclosure_embargo_days"),
    ("h12_portfolio", "quantile"), ("h12_portfolio", "weighting"),
    ("h12_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h12_criteria", "dsr_min"),
]


def h12_frozen_config_hash(config: dict) -> str:
    """O LACRE da H12 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H12_FROZEN_KEYS, "H12-FROZEN")


# Subconjunto H13-FROZEN (pré-registro 2026-09-04, HANDOFF). Crescimento de
# receita líquida YoY (top quintile) — primeira hipótese de CRESCIMENTO
# testada neste domínio, mesma fonte/embargo DFP das anteriores contábeis.
H13_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h13_factor", "name"), ("h13_factor", "disclosure_embargo_days"),
    ("h13_portfolio", "quantile"), ("h13_portfolio", "weighting"),
    ("h13_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h13_criteria", "dsr_min"),
]


def h13_frozen_config_hash(config: dict) -> str:
    """O LACRE da H13 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H13_FROZEN_KEYS, "H13-FROZEN")


# Subconjunto H14-FROZEN (pré-registro 2026-09-04, HANDOFF). Proximidade da
# máxima de 52 semanas (top quintile) — fator de preço distinto de momentum,
# mesma janela/universo/execução/bootstrap de H1.
H14_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h14_factor", "name"), ("h14_factor", "lookback_days"),
    ("h14_portfolio", "quantile"), ("h14_portfolio", "weighting"),
    ("h14_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h14_criteria", "dsr_min"),
]


def h14_frozen_config_hash(config: dict) -> str:
    """O LACRE da H14 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H14_FROZEN_KEYS, "H14-FROZEN")


# Subconjunto H15-FROZEN (pré-registro 2026-09-04, HANDOFF). Volume anormal
# (top quintile) — volume_fin já em prices_raw desde o M1, nunca usado como
# sinal de seleção. Mesma janela/universo/execução/bootstrap de H1.
H15_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h15_factor", "name"), ("h15_factor", "short_lookback_days"),
    ("h15_factor", "long_lookback_days"),
    ("h15_portfolio", "quantile"), ("h15_portfolio", "weighting"),
    ("h15_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h15_criteria", "dsr_min"),
]


def h15_frozen_config_hash(config: dict) -> str:
    """O LACRE da H15 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H15_FROZEN_KEYS, "H15-FROZEN")


# Subconjunto H16-FROZEN (pré-registro 2026-09-04, HANDOFF). Efeito
# virada-de-mês — primeira hipótese de TIMING (não seleção transversal)
# testada neste domínio; mecânica própria (backtest.run_h16), não usa
# walk_forward, por isso não reusa backtest.test_start/purge_embargo_months
# do jeito das anteriores (a mecânica não faz "rebalance mensal seleciona
# quintil" — só reusa o universo/execução como base de custo/composição).
H16_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h16_factor", "name"), ("h16_factor", "last_days_of_month"),
    ("h16_factor", "first_days_of_month"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "test_start"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h16_criteria", "dsr_min"),
]


def h16_frozen_config_hash(config: dict) -> str:
    """O LACRE da H16 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H16_FROZEN_KEYS, "H16-FROZEN")


# Subconjunto H17-FROZEN (pré-registro 2026-09-04, HANDOFF). Accruals
# (Sloan 1996) — quintil INFERIOR. Primeira hipótese com FONTE DE DADO NOVA
# (DFC-MI consolidada) desde o M2. Mesma janela/universo/execução/bootstrap
# de H1; `disclosure_embargo_days` entra no lacre (é parâmetro CIENTÍFICO
# aqui, como em H7/H9/H12/H13 — muda quais linhas contábeis são elegíveis).
H17_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h17_factor", "name"), ("h17_factor", "disclosure_embargo_days"),
    ("h17_portfolio", "quantile"), ("h17_portfolio", "weighting"),
    ("h17_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h17_criteria", "dsr_min"),
]


def h17_frozen_config_hash(config: dict) -> str:
    """O LACRE da H17 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H17_FROZEN_KEYS, "H17-FROZEN")


# Subconjunto H18-FROZEN (pré-registro 2026-09-04, HANDOFF). Earnings yield
# E/P — quintil SUPERIOR. Primeiro fator de VALOR do domínio.
H18_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h18_factor", "name"), ("h18_factor", "disclosure_embargo_days"),
    ("h18_factor", "known_at_policy"), ("h18_factor", "split_base"),
    ("h18_portfolio", "quantile"), ("h18_portfolio", "weighting"),
    ("h18_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h18_criteria", "dsr_min"),
]


def h18_frozen_config_hash(config: dict) -> str:
    """O LACRE da H18 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H18_FROZEN_KEYS, "H18-FROZEN")


# Subconjunto H19-FROZEN (pré-registro 2026-09-04, HANDOFF). Book-to-market
# B/M — quintil SUPERIOR. Hipótese separada da H18 (fluxo vs. estoque).
H19_FROZEN_KEYS = [
    ("universe", "top_n"), ("universe", "lookback_trading_days"),
    ("universe", "min_history_days"), ("universe", "rebalance_frequency"),
    ("h19_factor", "name"), ("h19_factor", "disclosure_embargo_days"),
    ("h19_factor", "known_at_policy"), ("h19_factor", "split_base"),
    ("h19_portfolio", "quantile"), ("h19_portfolio", "weighting"),
    ("h19_portfolio", "direction"),
    ("execution", "price"), ("execution", "b3_fee_pct"),
    ("execution", "brokerage_pct"), ("execution", "spread_slippage_pct"),
    ("backtest", "warmup_end"), ("backtest", "test_start"),
    ("backtest", "purge_embargo_months"),
    ("bootstrap", "n_boot"), ("bootstrap", "block_length"),
    ("bootstrap", "confidence"), ("bootstrap", "method"),
    ("h19_criteria", "dsr_min"),
]


def h19_frozen_config_hash(config: dict) -> str:
    """O LACRE da H19 — mesmo mecanismo dos lacres anteriores."""
    return _frozen_hash(config, H19_FROZEN_KEYS, "H19-FROZEN")
