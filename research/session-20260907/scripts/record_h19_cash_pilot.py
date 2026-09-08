"""Preserve the bounded cash-source pilot and its primary evidence; no returns."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
WORK = ROOT / "work"
REPO = WORK / "stocks-predictor"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

pilot = read(OUT / "H19_CAIXA_PRIMEIRAS_CORRECOES.json")
queue = read(OUT / "H19_CAIXA_FILA_DE_VALIDACAO.json")
resolved = pilot["bbas_newly_resolved_cash_cells"]
missing = pilot["jbs_missing_later_declared_events"]
affected = pilot["jbs_affected_h19_quarter_cells"]
assert len(resolved) == 13 and sum(r["selected"] for r in resolved) == 11
assert len(missing) == 11 and len(affected) == 11
assert sum(r["selected"] for r in affected) == 1
assert len(pilot["bbas_remaining_without_date"]) == 3
assert queue["selected_cells_without_candidate_payment_date"] == 100
assert queue["benchmark_cells_without_candidate_payment_date"] == 657
for name, expected in pilot["source_sha256"].items():
    assert sha(WORK / "h19-cash-closure-source" / name) == expected
for path, expected in queue["source_sha256"].items():
    assert sha(Path(path)) == expected

report = """# H19 trimestral: próximo teste e correções de caixa

**Decisão: continuar apenas a correção das fontes para o teste de execução. Não há lucro líquido demonstrado nem promoção para Proof.**

O próximo resultado útil é uma carteira contínua das mesmas seleções H19, com R$ 5 mil e R$ 10 mil, ações inteiras, pagamentos nas datas corretas, custos sobre o giro efetivo e impostos aplicáveis. Esse cálculo ainda não foi executado: os dados de caixa não estão completos.

**O que esta rodada resolveu**

| Achado | Resultado verificado | Limite |
|---|---|---|
| Banco do Brasil | 13 registros de caixa reconciliados, 11 em posições selecionadas | Três registros de atualização monetária ainda não reconciliados; não certifica cobertura integral |
| JBS | 11 dividendos posteriores a 2019 ausentes na consulta B3 por nome histórico | A tabela do RI usa quatro casas decimais; valores arredondados exigem aviso específico |
| JBS, junho de 2023 | Ata e tabela histórica concordam em R$ 1 por ação, ex em 23/06 e pagamento em 29/06 | A ata chama o valor de estimado; a tabela posterior relata o pagamento. Não é comprovante de custódia |

Os 11 dividendos ausentes da JBS afetam 11 células trimestrais: **uma selecionada e dez apenas no universo de comparação**. Não representam 11 ganhos adicionais da estratégia.

No Banco do Brasil, a B3 confirma o crédito de R$ 0,09044686629 por ação em **12/06/2025**; o PDF do RI traz 2024 nessa linha. Outro ajuste distingue a data civil declarada de 24/02/2020 do primeiro pregão ex, 26/02/2020. Rendimentos de atualização foram conciliados separadamente do provento original para evitar dupla contagem.

**O que continua faltando**

A fila inicial tinha 778 células de caixa nos instrumentos originais, 133 em posições selecionadas. Depois das conciliações do BBAS, ainda restam **644 células sem data candidata na fila original, 89 selecionadas**. Essas contagens não incluem os novos eventos da JBS nem proventos dos sucessores. Ter uma data candidata também não prova completude, identidade ou unicidade.

Antes de medir lucro, é necessário:

1. Completar datas e valores das mesmas posições e do universo de comparação, incluindo sucessores; verificar também lacunas sem registros.
2. Distinguir parcelas, atualizações monetárias e pagamentos extraordinários já considerados nas reorganizações.
3. Executar a carteira contínua com crédito efetivo de dinheiro e ações, frações, posições mantidas e lotes negociáveis.
4. Aplicar custos ao giro real, tributação por instrumento e período e comparar com uma alternativa de caixa em bases equivalentes.
5. Encerrar a linha se o ganho plausível não justificar risco e manutenção; nenhum ajuste de fator ou janela para resgatar o resultado histórico.

O custo da reconstrução continua sendo critério de parada. Cobertura insuficiente implica resultado inconclusivo ou pausa; não autoriza substituir proventos desconhecidos por zero e chamar a simulação de lucro líquido. Os R$ 5–10 mil são cenários informados pelo usuário. O lucro mínimo e as horas aceitáveis de manutenção ainda não foram definidos.

**Verificação e rastreabilidade**

Não houve novo cálculo de retorno, mudança de seleção ou alteração dos bancos. Permanecem os mínimos de 32 configurações e 37 avaliações históricas; esta rodada é auditoria de fontes. O código de estratégia permanece no estado anteriormente testado, com 539 testes aprovados; a suíte não foi repetida nesta rodada de dados/documentação. Scripts do piloto concluíram e os hashes das fontes foram conferidos.

O pacote de evidência contém as fontes primárias deste piloto, o histórico BBAS usado, as filas, resultados e scripts. É um arquivo de auditoria; não contém a base completa nem um simulador de lucro pronto. O pacote de validação anterior continua preservado.

Fontes: [histórico oficial JBS](https://ir.jbsglobal.com/shareholder-information/dividends/), [ata JBS de 19/06/2023](https://api.mziq.com/mzfilemanager/v2/d/043a77e1-0127-4502-bc5b-21427b991b22/11a431b2-5282-5345-0234-53fdf7524bfb?origin=1), [B3: crédito de 12/06/2025, página 4](https://arquivos.b3.com.br/bdi/download/bdi/2025-06-12/BDI_05_20250612.pdf), [histórico de pagamentos BBAS](https://api.mziq.com/mzfilemanager/v2/d/5760dff3-15e1-4962-9e81-322a0b3d0bbd/14581997-4233-3b2e-1d82-0d9c766cb7ec?origin=2).

O BDI_05 de 29/06/2023 baixado neste piloto contém somente um quadro de negociação. Foi preservado como tentativa sem evidência de crédito e não comprova pagamento da JBS.
"""
report_path = OUT / "H19_CAIXA_PROXIMO_TESTE.md"
with report_path.open("x", encoding="utf-8") as stream:
    stream.write(report)
repo_report = REPO / "docs/research/2026-09-07-h19-cash-pilot.md"
with repo_report.open("x", encoding="utf-8") as stream:
    stream.write(report)

summary = {
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "phase": "DISCOVERY_SOURCE_REPAIR",
    "decision": "CONTINUE_BOUNDED_SOURCE_REPAIR_ONLY",
    "execution_ready": False,
    "net_profit_demonstrated": False,
    "new_return_evaluations": 0,
    "capital_scenarios_brl": [5000, 10000],
    "bbas_newly_reconciled_cash_cells": 13,
    "bbas_newly_reconciled_selected_cells": 11,
    "bbas_unreconciled_update_cells": 3,
    "jbs_missing_after_2019_declarations": 11,
    "jbs_selected_affected_quarter_cells": 1,
    "original_queue_remaining_without_candidate_payment_date": 644,
    "original_selected_queue_remaining_without_candidate_payment_date": 89,
    "remaining_counts_exclude_new_jbs_and_successor_events": True,
    "search_configurations_minimum": 32,
    "historical_return_evaluations_minimum": 37,
    "strategy_code_last_full_test": {"commit": "28cf87e1819d25eb031067d6c707fa8519171953", "passed": 539, "rerun_this_pilot": False},
    "source_inputs_sha256": {
        str(p.relative_to(ROOT)): sha(p)
        for p in [
            OUT / "H19_CAIXA_PRIMEIRAS_CORRECOES.json",
            OUT / "H19_CAIXA_FILA_DE_VALIDACAO.json",
            OUT / "h18-h19-reorganization-observation.json",
            OUT / "VALIDACAO_PROVENTOS_AMPLIADA_STOCKS_V2.json",
            OUT / "cash-source-matches.jsonl",
            WORK / "source-acquisition/ri-bbas-payments.pdf",
            WORK / "source-acquisition/ri-bbas-payments-extracted.json",
            WORK / "source-acquisition/b3-cvm1023-cash-all.json",
            WORK / "profit-cash-source/raw-name-JBSS3-cash-all.json",
            WORK / "value-measurement-source/quotes.db",
        ]
    },
}
for target in (OUT / "H19_CAIXA_DECISAO.json", REPO / "docs/research/2026-09-07-h19-cash-pilot.json"):
    with target.open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)

handoff = REPO / "HANDOFF.md"
handoff.write_text("""## H19 trimestral: piloto de fontes de caixa, execução ainda pendente (2026-09-07)

Não confundir históricos localizados com históricos completos: consulta B3 por
nome JBS para em 2019; RI revela 11 dividendos posteriores, afetando 11 células
trimestrais, apenas uma selecionada. Valor divulgado com quatro casas decimais
não certifica precisão exata. Ata e RI confirmam termos de junho/2023 com ressalva
de valor estimado na ata. BBAS: 13 células conciliadas (11 selecionadas), três
atualizações monetárias ainda sem conciliação. Pagamento junho/2025 corrigido
por boletim de crédito B3; data civil ex 24/02/2020 separada do pregão 26/02.
Não houve alteração de DB, de retorno, de seleção ou novo trial. Orçamento
>=32 configurações / >=37 avaliações. Runtime mantém os 539 testes anteriores;
nesta rodada foram verificados dados, scripts e hashes, sem repetir a suíte.

Restam 644 células sem data candidata na fila original, 89 selecionadas; valores
excluem novos eventos JBS e caixa de sucessores. Cobertura integral não certificada.
Próximo passo: completar fontes de ambas as carteiras antes de quantidades/caixa,
giro real e impostos para R$5 mil e R$10 mil. Não tunar fator ou período. O custo
de reconstrução é critério de parada; lucro e execução continuam não demonstrados.
Detalhes em docs/research/2026-09-07-h19-cash-pilot.md e respectivo JSON.

""" + handoff.read_text(encoding="utf-8"), encoding="utf-8")

payload = {
    "H19_CAIXA_PROXIMO_TESTE.md": report_path,
    "H19_CAIXA_DECISAO.json": OUT / "H19_CAIXA_DECISAO.json",
    "H19_CAIXA_FILA_DE_VALIDACAO.json": OUT / "H19_CAIXA_FILA_DE_VALIDACAO.json",
    "H19_CAIXA_PRIMEIRAS_CORRECOES.json": OUT / "H19_CAIXA_PRIMEIRAS_CORRECOES.json",
}
for p in (WORK / "h19-cash-closure-source").iterdir():
    if p.is_file():
        payload["sources/pilot/" + p.name] = p
for name in ("ri-bbas-payments.pdf", "ri-bbas-payments-extracted.json", "b3-cvm1023-cash-all.json"):
    payload["sources/prior/" + name] = WORK / "source-acquisition" / name
payload["sources/prior/raw-name-JBSS3-cash-all.json"] = WORK / "profit-cash-source/raw-name-JBSS3-cash-all.json"
for name in ("plan_h19_cash_closure.py", "acquire_h19_cash_pilot.py", "reconcile_h19_cash_pilot.py", "record_h19_cash_pilot.py"):
    payload["scripts/" + name] = WORK / name
manifest = {"purpose": "Source evidence archive, not a standalone profit runner", "files": {name: sha(p) for name, p in sorted(payload.items())}}
archive = OUT / "H19_CAIXA_EVIDENCIAS.zip"
with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as bundle:
    for name, p in payload.items():
        bundle.write(p, name)
    bundle.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
with zipfile.ZipFile(archive) as bundle:
    for name, expected in manifest["files"].items():
        assert hashlib.sha256(bundle.read(name)).hexdigest() == expected
print(json.dumps({"archive": str(archive), "files_verified": len(payload), "sha256": sha(archive), "source_audit_passed": True}, indent=2))
