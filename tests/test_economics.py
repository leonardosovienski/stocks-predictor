"""Screen econômico — o mínimo economicamente interessante (charter §6).

Cobre a disciplina central do módulo: ele NÃO inventa o critério. Sem declaração
do operador no `config.yaml`, o screen se recusa a dizer se um resultado vale a
pena, em vez de assumir um default que responderia em silêncio a pergunta que
custou 15 tentativas do DSR nunca ter sido feita.
"""
import math

import economics
from config import load_config


def _cfg(capital=None, minimo=None, dd=None):
    return {"economics": {
        "capital_brl": capital if capital is not None else economics.UNDECLARED,
        "min_annual_net_profit_brl": minimo if minimo is not None else economics.UNDECLARED,
        "max_acceptable_drawdown": dd if dd is not None else economics.UNDECLARED,
    }}


# ---------- declaração ----------

def test_sentinela_nao_vira_zero():
    """`NAO_DECLARADO` é ausência de decisão, não um mínimo de zero. Se virasse
    0.0, qualquer lucro positivo passaria e o screen aprovaria tudo."""
    m = economics.declared_minimum(_cfg())
    assert m == {"capital_brl": None, "min_annual_net_profit_brl": None,
                 "max_acceptable_drawdown": None}


def test_texto_livre_tambem_conta_como_nao_declarado():
    """Erro de digitação num campo econômico não pode virar número por acidente."""
    assert economics.declared_minimum(
        {"economics": {"capital_brl": "R$ 100k"}})["capital_brl"] is None


def test_booleano_nao_e_capital():
    """`True` é `int` em Python; sem a guarda viraria capital de R$ 1,00."""
    assert economics.declared_minimum(
        {"economics": {"capital_brl": True}})["capital_brl"] is None


def test_secao_ausente_nao_quebra():
    assert economics.declared_minimum({})["capital_brl"] is None


# ---------- a pergunta que se responde ANTES de gastar evidência ----------

def test_retorno_exigido_none_sem_declaracao():
    assert economics.required_net_annual_return(_cfg()) is None


def test_retorno_exigido_e_aritmetica_simples():
    """R$ 30k/ano sobre R$ 200k = 15% ao ano líquidos. Não consome amostra, não
    incrementa o N do DSR: é a conta que decide se vale rodar a hipótese."""
    cfg = _cfg(capital=200_000.0, minimo=30_000.0, dd=0.25)
    assert economics.required_net_annual_return(cfg) == 0.15


def test_capital_zero_nao_divide():
    assert economics.required_net_annual_return(_cfg(0.0, 30_000.0, 0.25)) is None


# ---------- medição da série ----------

def test_screen_de_serie_vazia_e_none():
    assert economics.screen([]) is None
    assert economics.screen(None) is None


def test_screen_anualiza_geometricamente():
    """252 pregões de +0,1% compõem ~28,6% no ano, não 25,2% (soma simples)."""
    scr = economics.screen([0.001] * 252)
    assert scr["n_periods"] == 252
    assert math.isclose(scr["years"], 1.0)
    assert math.isclose(scr["net_annual_return"], 1.001 ** 252 - 1, rel_tol=1e-9)
    assert scr["max_drawdown"] == 0.0
    assert scr["ruin"] is False


def test_screen_declara_capacidade_como_nao_calculada():
    """Capacidade exige ADV e tamanho de posição, que a série não carrega. Fica
    declarada como não calculada — omitir deixaria o leitor supor que coube."""
    scr = economics.screen([0.001] * 30)
    assert "capacity_brl" in scr and scr["capacity_brl"] is None
    assert scr["evidence_class"] == "BACKTEST_IN_SAMPLE_NET_OF_MODELED_COSTS"


def test_drawdown_pico_a_vale():
    # sobe 20%, cai 50% do pico, recupera parte
    dd = economics.max_drawdown([0.20, -0.50, 0.10])
    assert math.isclose(dd, 0.5, rel_tol=1e-9)


def test_drawdown_de_serie_so_de_alta_e_zero():
    assert economics.max_drawdown([0.01] * 10) == 0.0


def test_ruina_nao_recupera_no_papel():
    """Depois de zerar o capital, retorno positivo não reconstrói patrimônio."""
    scr = economics.screen([-1.0, 5.0, 5.0])
    assert scr["ruin"] is True
    assert scr["net_annual_return"] == -1.0
    assert scr["max_drawdown"] == 1.0


# ---------- classificação ----------

def test_sem_declaracao_o_screen_se_recusa_a_julgar():
    estado, motivo, _ = economics.classify(economics.screen([0.001] * 252), _cfg())
    assert estado == economics.NAO_DECLARADO
    assert "capital_brl" in motivo


def test_edge_real_mas_pequeno_demais_e_desfecho_proprio():
    """O ponto do charter §6: isto NÃO é `NO_EDGE`. O fator entrega retorno
    positivo e mesmo assim não paga o que o operador declarou precisar."""
    cfg = _cfg(capital=100_000.0, minimo=50_000.0, dd=0.50)
    estado, motivo, detalhe = economics.classify(economics.screen([0.0001] * 252), cfg)
    assert estado == economics.ABAIXO_DO_MINIMO
    assert "lucro anual esperado" in motivo
    assert 0 < detalhe["expected_annual_profit_brl"] < 50_000.0


def test_drawdown_acima_do_aceitavel_reprova_mesmo_com_lucro():
    cfg = _cfg(capital=1_000_000.0, minimo=1_000.0, dd=0.05)
    estado, motivo, _ = economics.classify(economics.screen([0.20, -0.50, 0.60]), cfg)
    assert estado == economics.ABAIXO_DO_MINIMO
    assert "drawdown" in motivo


def test_acima_do_minimo_ainda_nao_e_autorizacao_de_capital():
    cfg = _cfg(capital=1_000_000.0, minimo=10_000.0, dd=0.50)
    estado, motivo, _ = economics.classify(economics.screen([0.001] * 252), cfg)
    assert estado == economics.ACIMA_DO_MINIMO
    assert "não é evidência deployable" in motivo


def test_serie_vazia_classifica_como_sem_serie():
    estado, _, _ = economics.classify(None, _cfg())
    assert estado == economics.SEM_SERIE


# ---------- o fecho da rodada ----------

def test_summary_line_nunca_derruba_a_rodada():
    """Um screen econômico quebrando não pode matar a rodada científica que ele
    apenas observa."""
    assert "economia:" in economics.summary_line([0.001] * 252, _cfg())
    assert "economia:" in economics.summary_line([], _cfg())
    assert "economia:" in economics.summary_line([0.001] * 10, {"economics": None})


def test_summary_line_mostra_dinheiro_quando_ha_capital():
    linha = economics.summary_line([0.001] * 252, _cfg(200_000.0, 10_000.0, 0.5))
    assert "lucro anual esperado R$" in linha
    assert economics.ACIMA_DO_MINIMO in linha


# ---------- o config real ----------

def test_config_real_declara_a_secao_e_segue_sem_resposta():
    """Guarda contra alguém preencher um default no lugar do operador. Quando
    estes números forem decididos DE VERDADE, este teste deve ser atualizado
    conscientemente — é o momento em que o domínio ganha um critério econômico,
    e isso merece uma linha no HANDOFF, não um commit silencioso."""
    cfg = load_config()
    assert "economics" in cfg, "a seção econômica sumiu do config.yaml"
    assert economics.required_net_annual_return(cfg) is None, (
        "o mínimo econômico foi declarado no config.yaml — atualize este teste e "
        "registre a decisão (capital e lucro mínimo) no HANDOFF")


def test_secao_economica_nao_entra_em_nenhum_lacre():
    """Se um campo econômico entrasse num `*_FROZEN_KEYS`, revisar o mínimo de
    negócio quebraria o pré-registro de uma hipótese. Não pode."""
    import config as config_mod

    for nome in dir(config_mod):
        if nome.endswith("_FROZEN_KEYS"):
            secoes = {s for s, _ in getattr(config_mod, nome)}
            assert "economics" not in secoes, f"{nome} selou a seção econômica"
