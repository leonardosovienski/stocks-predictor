"""Screen econômico READ-ONLY sobre uma série de retornos LÍQUIDOS já medida.

Responde a pergunta que as 16 hipóteses julgadas nunca tiveram que responder:
**se este fator fosse verdadeiro, quanto dinheiro ele daria?**

Motivação (2026-09-07). O domínio julgou 16 hipóteses e gastou 15 tentativas do
denominador do DSR sem que ninguém tivesse declarado, ANTES de rodar, qual
resultado seria economicamente relevante. Isso tem custo irreversível: cada
tentativa registrada sobe a barra da próxima (`E[max SR]` cresce com N), então
uma hipótese rodada sem valer a pena encarece TODAS as seguintes. Um fator pode
ser cientificamente real e ainda assim `REAL_EDGE_BUT_ECONOMICALLY_TOO_SMALL` —
que é um desfecho diferente de `NO_EDGE` e leva a uma decisão diferente.

O que este módulo NÃO faz, de propósito:

- **não altera veredito científico.** `trials_gate.apply_dsr` continua sendo o
  único juiz. Isto aqui é leitura, e roda depois;
- **não inventa o mínimo econômico.** Capital disponível e lucro anual mínimo
  são decisão do operador, não do código. Sem declaração no `config.yaml` o
  screen devolve `NAO_DECLARADO` e diz o que falta — não assume um default,
  porque um default aqui responderia em silêncio a pergunta que o operador
  precisa responder por escrito;
- **não estima capacidade.** Capacidade exige ADV por papel e tamanho de posição,
  que a série de retornos não carrega. Fica declarada como NÃO CALCULADA em vez
  de omitida;
- **não transforma backtest em dinheiro.** A série é in-sample, líquida dos
  custos MODELADOS (`execution.one_way_cost` sobre turnover real). Custo modelado
  não é custo realizado, e o próprio `RESEARCH_FREEZE` registra que a liquidação
  do backtest é close-to-close no dia do sinal. Todo retorno daqui sai rotulado.

Unidade da série: retorno DIÁRIO por pregão (a mesma que `backtest.judge`
anualiza por `sqrt(252)`), líquida do custo de turnover cobrado no rebalance.
"""
import math
import statistics

PERIODS_PER_YEAR = 252

#: Sentinela do `config.yaml`. O mini-parser de `config.py` recusa chave sem
#: valor ("aninhamento >2 níveis não suportado"), então um campo econômico ainda
#: não decidido pelo operador é declarado explicitamente com esta string em vez
#: de ficar ausente — ausência silenciosa vira default silencioso.
UNDECLARED = "NAO_DECLARADO"

#: Estados possíveis do screen.
NAO_DECLARADO = "NAO_DECLARADO"
SEM_SERIE = "SEM_SERIE"
ABAIXO_DO_MINIMO = "REAL_EDGE_BUT_ECONOMICALLY_TOO_SMALL"
ACIMA_DO_MINIMO = "ECONOMICAMENTE_RELEVANTE"


def _declared(value):
    """Valor econômico declarado, ou None. Trata a sentinela e lixo de digitação
    (string não numérica) do mesmo jeito: NÃO declarado. Um campo econômico que
    não é número não pode virar zero por acidente."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else None
    return None


def declared_minimum(cfg):
    """Lê a seção `economics` do config. Devolve os campos declarados (ou None).

    A seção é OPERACIONAL: não entra em nenhum `*_FROZEN_KEYS` e portanto não
    entra em nenhum lacre. Mudar o mínimo econômico não altera o `config_hash`
    de hipótese nenhuma — é decisão de negócio, não parâmetro de experimento,
    e selá-la impediria o operador de revisá-la sem quebrar o pré-registro.
    """
    e = cfg.get("economics", {}) or {}
    return {
        "capital_brl": _declared(e.get("capital_brl")),
        "min_annual_net_profit_brl": _declared(e.get("min_annual_net_profit_brl")),
        "max_acceptable_drawdown": _declared(e.get("max_acceptable_drawdown")),
    }


def required_net_annual_return(cfg):
    """A pergunta do §6 respondida ANTES de gastar evidência: que retorno anual
    líquido este domínio precisa entregar para valer a pena?

    `min_annual_net_profit_brl / capital_brl`. Não precisa de dado nenhum, não
    consome amostra, não incrementa o N do DSR — é aritmética sobre duas
    decisões do operador. None quando qualquer das duas não foi declarada.
    """
    m = declared_minimum(cfg)
    capital, minimo = m["capital_brl"], m["min_annual_net_profit_brl"]
    if capital is None or minimo is None or capital <= 0:
        return None
    return minimo / capital


def max_drawdown(returns):
    """Maior queda pico-a-vale da curva de capital. 0.0 numa série vazia.

    Curva de capital que chega a <= 0 (ruína) devolve 1.0 e para de acumular:
    depois de zerar o capital, "recuperação" no papel é artefato de composição
    de retornos sobre um patrimônio que não existe mais.
    """
    peak = equity = 1.0
    worst = 0.0
    for r in returns:
        equity *= (1.0 + r)
        if equity <= 0.0:
            return 1.0
        peak = max(peak, equity)
        worst = max(worst, (peak - equity) / peak)
    return worst


def screen(strat, periods_per_year=PERIODS_PER_YEAR):
    """Traduz a série líquida medida em termos econômicos anualizados.

    `strat`: retornos por pregão, LÍQUIDOS dos custos modelados (é o que
    `backtest.walk_forward` devolve). Devolve None se não houver série.
    """
    if not strat:
        return None
    n = len(strat)
    total = 1.0
    ruin = False
    for r in strat:
        total *= (1.0 + r)
        if total <= 0.0:
            ruin, total = True, 0.0
            break
    years = n / periods_per_year
    if ruin or total <= 0.0:
        net_annual = -1.0
    else:
        net_annual = total ** (1.0 / years) - 1.0 if years > 0 else 0.0
    sd = statistics.pstdev(strat) if n > 1 else 0.0
    mean = statistics.mean(strat)
    return {
        "n_periods": n,
        "years": years,
        "net_annual_return": net_annual,
        "annual_vol": sd * math.sqrt(periods_per_year),
        "sharpe_annual": (mean / sd * math.sqrt(periods_per_year)) if sd else 0.0,
        "max_drawdown": max_drawdown(strat),
        "ruin": ruin,
        # Declarado como não calculado, não omitido: a série de retornos não
        # carrega tamanho de posição nem ADV por papel.
        "capacity_brl": None,
        "evidence_class": "BACKTEST_IN_SAMPLE_NET_OF_MODELED_COSTS",
    }


def classify(scr, cfg):
    """Compara o medido contra o mínimo DECLARADO. Não julga ciência.

    Devolve `(estado, motivo, detalhe)`. Sem declaração do operador o estado é
    `NAO_DECLARADO` — o screen se recusa a dizer se vale a pena contra um
    critério que ninguém escreveu.
    """
    if scr is None:
        return SEM_SERIE, "série vazia — nada a avaliar", {}
    m = declared_minimum(cfg)
    faltando = [k for k, v in m.items() if v is None]
    capital = m["capital_brl"]
    lucro_esperado = capital * scr["net_annual_return"] if capital is not None else None
    detalhe = {
        "expected_annual_profit_brl": lucro_esperado,
        "required_net_annual_return": required_net_annual_return(cfg),
        **m,
    }
    if faltando:
        return (NAO_DECLARADO,
                "mínimo econômico não declarado no config.yaml (seção `economics`): "
                + ", ".join(faltando),
                detalhe)
    falhas = []
    if lucro_esperado is not None and lucro_esperado < m["min_annual_net_profit_brl"]:
        falhas.append(
            f"lucro anual esperado R$ {lucro_esperado:,.0f} < mínimo "
            f"R$ {m['min_annual_net_profit_brl']:,.0f}")
    if scr["max_drawdown"] > m["max_acceptable_drawdown"]:
        falhas.append(
            f"drawdown máximo {scr['max_drawdown']:.1%} > aceitável "
            f"{m['max_acceptable_drawdown']:.1%}")
    if falhas:
        return ABAIXO_DO_MINIMO, "; ".join(falhas), detalhe
    return (ACIMA_DO_MINIMO,
            "passa o mínimo declarado — em BACKTEST líquido de custos MODELADOS; "
            "não é evidência deployable nem autorização de capital",
            detalhe)


def summary_line(strat, cfg, periods_per_year=PERIODS_PER_YEAR):
    """Uma linha para o fecho de uma rodada. Nunca levanta: um screen econômico
    quebrando não pode derrubar a rodada científica que ele apenas observa."""
    try:
        scr = screen(strat, periods_per_year)
        estado, motivo, detalhe = classify(scr, cfg)
        if scr is None:
            return f"economia: {estado} ({motivo})"
        lucro = detalhe.get("expected_annual_profit_brl")
        dinheiro = f" | lucro anual esperado R$ {lucro:,.0f}" if lucro is not None else ""
        return (f"economia: retorno líquido anual {scr['net_annual_return']:.2%} | "
                f"vol {scr['annual_vol']:.2%} | maxDD {scr['max_drawdown']:.2%}"
                f"{dinheiro} | {estado} ({motivo})")
    except Exception as exc:  # pragma: no cover - guarda de última instância
        return f"economia: INDISPONÍVEL ({type(exc).__name__}: {exc})"
