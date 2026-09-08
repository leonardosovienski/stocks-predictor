"""Write the observed result and preserve the complete bounded comparison."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(r"C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907")
REPO = ROOT / "work/stocks-predictor"
WORK = ROOT / "work/h20-profit-test-20260908"
CHAT = Path(r"C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2")
OUT = CHAT / "outputs"
ARCHIVE = REPO / "research/session-20260908/h20-profit-test"
DURABLE = ROOT / "outputs/h20-profit-test-20260908"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def pct(value):
    return f"{value*100:.2f}%".replace(".", ",")

result = read(WORK / "observation-01.json")
assert (WORK / "observation-01.json").read_bytes() == (WORK / "observation-reproduced.json").read_bytes()
validation = read(WORK / "independent-verification.json")
validation.update(h20_comparison_byte_identical=True, measured_code_commit="2488171",
                  preregistration_commit="9286129", registered_before_observation=True)
arms = result["protocol"]["arms"]
rows = []
for mode, label in [("open", "Abertura"), ("close", "Fechamento"), ("worst", "Adverso")]:
    for scenario in result["modes"][mode]["scenarios"]:
        groups = scenario["groups"]
        vals = [pct(groups[a]["synthetic_path"]["annualized_geometric_return"]) for a in arms]
        rows.append("| " + " | ".join([label, pct(scenario["one_way_assumed_cost"]), *vals]) + " |")
table = "\n".join(rows)
base = result["modes"]["open"]["scenarios"][0]
buffer_delta = base["comparisons"][1]
worst = result["modes"]["worst"]["scenarios"][1]
decision = {
    "answer": "A composição histórica simulada melhorou, mas a projeção de lucro líquido continua não calculável e a melhora incremental é inconclusiva.",
    "profit": None, "future_profit_projection": None,
    "decision": "INCONCLUSIVE_NET_PROFIT / OPERATIONAL_NO_GO",
    "eligible_quarters": 31, "blocked_signal_dates": ["2018-03-29"],
    "start": "2018-07-02", "end": "2026-04-01",
    "base_annualized_mark_change": {a: base["groups"][a]["synthetic_path"]["annualized_geometric_return"] for a in arms},
    "adverse_double_cost_annualized_mark_change": {a: worst["groups"][a]["synthetic_path"]["annualized_geometric_return"] for a in arms},
    "base_buffer_minus_control": buffer_delta,
    "not_net_profit_or_total_return": True,
    "buffer_is_planned_membership_only": True,
    "new_observed_diagnostic_scenarios": 18, "minimum_configurations": 53, "minimum_return_evaluations": 55,
    "full_suite_passed": 639, "new_measurement_tests_passed": 11,
    "observation_sha256": sha(WORK/"observation-01.json"),
}
report = f"""# Teste do Stocks Predictor: houve melhora no lucro?

**Houve melhora no resultado composto do diagnóstico histórico. Ainda não é possível concluir que a projeção de lucro líquido melhorou.** O histórico mais recente e a incerteza estatística impedem tratar essa diferença como uma vantagem futura demonstrada.

Foram comparados os três conjuntos de ações já congelados na H20, sem ajustar pesos de fatores, cortes de ranking, ativos ou datas depois de observar retornos. O teste cobriu **31 trimestres**, de **02/07/2018 a 01/04/2026**. A data de sinal 29/03/2018 permaneceu registrada e bloqueada por cobertura insuficiente; nenhuma data elegível foi retirada pelo resultado.

## O que os números medem

A tabela mostra **variação geométrica anualizada de uma carteira sintética**, com custos assumidos de negociação. Inclui cotações, fatores e direitos societários do painel anteriormente auditado, mas **omite dividendos/JCP ordinários, impostos, atrasos de pagamento/entrega, arredondamentos e manutenção**. Portanto não é retorno total, lucro líquido executável nem previsão para o próximo ano.

Cada trimestre atribui pesos iguais aos nomes selecionados e supõe liquidação/reinvestimento completo. O custo hipotético é igual para todas as alternativas: `(1 + variação do trimestre) × (1 − custo)/(1 + custo) − 1`. As taxas de 0,18% e 0,36% por lado são as premissas anteriores do projeto. Não representam uma tarifa atual recém-verificada.

| Preço de compra/saída | Custo por lado | Valor — controle comum | Valor + rentabilidade | Com retenção de nomes |
|---|---:|---:|---:|---:|
{table}

O cenário adverso compra pelo maior preço entre abertura e fechamento e vende pelo menor. As seis combinações foram reportadas. Na abertura e custo base, a diferença anualizada entre retenção e controle é **3,58 pontos percentuais**, de 11,00% para 14,58%. No cenário adverso com custo dobrado, é **3,20 pontos**, de 2,05% para 5,25%. A forte queda de nível no cenário adverso mostra a sensibilidade à execução.

O controle usa **exatamente o mesmo universo válido** das duas alternativas H20, isolando melhor o efeito da seleção. A H19 original, com seu universo diferente, teve 10,91% no mesmo cenário de abertura/custo base, contra 11,00% do controle comum; no adverso com custo dobrado, 1,95% contra 2,05%. Esses números H19 são referências de diagnóstico, também sem lucro líquido. O universo comum equiponderado teve 5,60% e −3,21%, respectivamente; não é índice de retorno total ou carteira passiva executada.

## Por que a melhora ainda é incerta

- Na abertura/custo base, a retenção superou o controle na média por apenas **0,197 ponto percentual por trimestre**, vencendo em **16 dos 31**. O intervalo descritivo de 95% vai de **−3,61 a +3,92 pontos por trimestre**; inclui piora expressiva.
- A comparação do valor com rentabilidade, sem retenção, também não excluiu zero. Todos os intervalos das três comparações principais, nos três preços e dois custos, incluem zero. Não são intervalos ajustados pelas tentativas anteriores.
- Na divisão fixada antes da medição, a retenção teve vantagem média bruta de **+0,77 ponto por trimestre nos primeiros 15**, mas **−0,34 ponto nos últimos 16**. Estes últimos correspondem aos sinais de 2022–2025 e encerram em abril de 2026. O sinal dessa vantagem recente também foi negativo no fechamento e no cenário adverso.
- Uma trajetória composta melhor pode coexistir com uma diferença média pequena ou negativa. No fechamento, por exemplo, a retenção teve composição anualizada maior, mas diferença média de **−0,085 ponto por trimestre** contra o controle, com custo base. Nenhuma das duas métricas deve ser ocultada.
- A queda máxima medida somente entre finais de trimestre foi **−40,42%** com retenção na abertura/custo base. No adverso com custo dobrado chegou a **−48,24%**, contra **−45,13%** do controle. Perdas dentro do trimestre podem ter sido maiores.

## O que foi e o que ainda não foi executado

O teste utilizou a **sequência de nomes pretendidos** já arquivada na H20. A tolerância de peso de 2,5% e a retenção baseada no livro real não foram executadas numa carteira contínua. Não foi atribuído nenhum ganho financeiro às 26 substituições de nomes evitadas no diagnóstico anterior. Todas as alternativas receberam o mesmo cenário de rotação integral e custos; a economia real pode ser diferente.

Os capitais de R$5 mil e R$10 mil aparecem no JSON como equivalentes sintéticos de patrimônio, sob reinvestimento integral das marcações. Esses valores **não são lucro e não servem como projeção anual em reais**. Os campos `profit` e `future_profit_projection` permaneceram `null`.

A execução econômica H19 foi repetida e retornou `BLOCKED_MISSING_EVIDENCE`, byte a byte igual à anterior. Continuam 1.237 intervalos H19 sem inventário integral de caixa e 36 registros societários sem integração/aprovação, entre outras lacunas. Para H20, cada seleção requer 231 intervalos de posição trimestral; há **zero certificados integrais de caixa disponíveis**. Estes intervalos não certificam posições mantidas por vários trimestres, sucessores ou seu tratamento fiscal. Fontes da H19 não habilitam automaticamente a H20.

Assim, o impedimento atual é a evidência econômica e a execução contínua da H20. Não é uma falha detectada nos testes nem lucro igual a zero. Uma projeção líquida válida exige aplicar os eventos, caixa e base fiscal ao livro efetivo de cada alternativa, com compras/vendas inteiras e fracionárias e custos de manutenção coerentes.

## Verificação e reprodução

- **639 testes do projeto passaram** em 71,85 segundos; **11 testes novos da medição passaram**. Estes testam médias calculáveis à mão, custo simétrico, identidades, causalidade, falha de entrada, fontes ausentes, períodos faltantes e integridade do protocolo.
- **1.448 arquivos do pacote histórico foram verificados**. A reprodução a partir dos extratos de cotações em SQLite somente leitura reconstruiu **9.732 células, quatro coortes e os 12 cenários antigos**, incluindo seus intervalos, sem diferenças.
- Um segundo cálculo conferiu **465 médias de carteiras**, **30 composições/annualizações/drawdowns** e **54 comparações pareadas com suas metades fixas**. Não reutilizou as funções da nova medição para essas contas.
- A nova observação H20 foi reproduzida **byte a byte**: SHA256 `{sha(WORK/'observation-01.json')}`.
- Protocolo registrado no commit `9286129`, antes de cruzar seleções com retornos; medidor testado em `2488171`. O runtime de produção não foi alterado. Bancos principais, dados brutos, ledgers e quarentenas foram preservados. Nenhuma instalação, ordem, gasto ou push remoto.

O pacote contém o medidor, testes, protocolo, resultado completo, verificação e logs. O comando está em `REPRODUZIR_TESTE.ps1`; exige o Python 3.13 global e reutiliza as fontes preservadas na raiz de pesquisa. As saídas são novas e o resultado financeiro permanece explicitamente desconhecido.

## Decisão registrada

**Melhora histórica aparente, vantagem incremental inconclusiva e lucro líquido não calculável.** Não promover a H20 com base nesses números nem ajustar o histórico para fortalecer a melhora. O desempenho recente não justifica, por si só, uma reconstrução manual extensa para capital de R$5–10 mil. O trabalho seguinte só se justifica com uma rota barata para completar caixa/eventos e validar prospectivamente a execução da regra congelada.

Foram observados 18 cenários novos, contando conservadoramente três seleções × três preços × dois custos: mínimos **53 configurações e 55 avaliações históricas**. São diagnósticos no mesmo histórico já exposto, não 18 provas independentes ou um holdout novo. Estado mantido: `INCONCLUSIVE_NET_PROFIT / OPERATIONAL_NO_GO`.
"""
OUT.mkdir(exist_ok=True)
DURABLE.mkdir(parents=True, exist_ok=False)
for base_path in (OUT, DURABLE):
    (base_path/"H20_TESTE_LUCRO.md").write_text(report, encoding="utf-8", newline="\n")
    (base_path/"H20_TESTE_DECISAO.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    (base_path/"H20_TESTE_VALIDACAO.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    shutil.copyfile(WORK/"observation-01.json", base_path/"H20_TESTE_RESULTADOS.json")
for name in ("H20_TESTE_LUCRO.md", "H20_TESTE_DECISAO.json", "H20_TESTE_VALIDACAO.json", "H20_TESTE_RESULTADOS.json"):
    shutil.copyfile(OUT/name, ARCHIVE/name)
shutil.copyfile(CHAT/"work/verify_h20_profit_comparison.py", ARCHIVE/"verify_h20_profit_comparison.py")
shutil.copyfile(CHAT/"work/deliver_h20_profit_test.py", ARCHIVE/"deliver_h20_profit_test.py")
for name in ("full-suite.log", "comparison-tests.log", "comparison-run.log", "source-reproduction.log", "reproduction-run.log", "h19-gate.log", "h19-gate-replay.json", "independent-verification.json"):
    shutil.copyfile(WORK/name, ARCHIVE/name)
shutil.copyfile(REPO/"docs/research/2026-09-08-h20-profit-test-protocol.json", ARCHIVE/"protocol.json")
shutil.copyfile(OUT/"H20_TESTE_LUCRO.md", REPO/"docs/research/2026-09-08-h20-profit-test-results.md")

wrapper = r'''param([Parameter(Mandatory=$true)][string]$OutputFile)
$ErrorActionPreference = 'Stop'
$researchRoot = 'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907'
$env:PYTHONPATH = "$researchRoot\work\stocks-predictor;$researchRoot\work\runtime;$researchRoot\work\checks"
py -3.13 "$PSScriptRoot\compare_h20.py" --root $researchRoot --protocol "$PSScriptRoot\protocol.json" --gate "$PSScriptRoot\h19-gate-replay.json" --output $OutputFile
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$actualDigest = (Get-FileHash -LiteralPath $OutputFile -Algorithm SHA256).Hash.ToLower()
if ($actualDigest -ne 'aa184580bf5ba69b515a20cc40115453396bdefa470ac0f5408c0d3ced15e1a3') { throw 'Resultado difere da observação preservada.' }
Write-Output 'Reproduzido byte a byte. Lucro líquido permanece desconhecido.'
'''
(ARCHIVE/"REPRODUZIR_TESTE.ps1").write_text(wrapper, encoding="utf-8", newline="\n")

state = """## Teste de desempenho H20 (08/09/2026 UTC)

Pedido: testar se melhorou a projeção de lucro. Protocolo 9286129 anterior ao
cruzamento com retornos; medidor 2488171. 31 trimestres de 2018-07-02 a 2026-04-01,
três seleções congeladas, três preços e dois custos, sem tuning. 29/03/2018 retida
como bloqueada por cobertura; nenhuma data elegível removida pelo desempenho.

Diagnóstico de marcações com rotação integral hipotética, sem caixa ordinário,
impostos ou manutenção: anualização na abertura/custo base 11,00% controle comum,
14,02% valor/rentabilidade, 14,58% retenção. Adverso/custo dobrado 2,05%, 4,74%, 5,25%.
Retenção é a sequência pretendida, sem execução contínua da banda de peso de 2,5%.
Economia real de turnover não foi inferida. Lucro/projeção futura permanecem null.

Diferença média retenção-controle na abertura +0,197 pp/trimestre; IC descritivo
95% [-3,61; +3,92] pp, sem ajuste por seleção. Segunda metade -0,34 pp/trimestre
brutos; vantagem recente também negativa nos outros preços. Drawdown adverso
com custo dobrado -48,24%. Melhora composta aparente, incremento inconclusivo.

639 testes completos +11 testes da medição. Reprodução de 1.448 arquivos,
9.732 células e 12 cenários anteriores, conferência independente de 465 médias,
30 trajetórias e 54 pares. Nova observação byte idêntica aa184580bf5b...;
replay financeiro antigo idêntico e bloqueado. Zero inventários integrais de
caixa disponíveis para os 231 intervalos trimestrais de cada seleção H20.
Runtime de produção inalterado, extratos históricos lidos com mode=ro e hashes
verificados; bancos principais, ledgers, quarentenas e fontes preservados.

18 cenários adicionais registrados/observados, contagem conservadora mínima
53 configurações/55 avaliações históricas; sem holdout ou Proof. Não promover
H20 ou ajustar parâmetros. INCONCLUSIVE_NET_PROFIT / OPERATIONAL_NO_GO mantido.
Relatório: docs/research/2026-09-08-h20-profit-test-results.md. Arquivo reproduzível
em research/session-20260908/h20-profit-test; saídas também na raiz durável,
outputs/h20-profit-test-20260908. Nenhuma ordem, gasto, agente, instalação ou push.

"""
for name in ("HANDOFF.md", "STOCKS_CURRENT_STATE.md", "docs/continuation/UPDATE_20260908.md"):
    path = REPO/name
    path.write_text(state+path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

names = sorted(p.name for p in ARCHIVE.iterdir() if p.is_file())
manifest = {"files": {n: sha(ARCHIVE/n) for n in names}, "observation_sha256": sha(WORK/"observation-01.json"),
            "requires_preserved_sources": str(ROOT), "profit": None}
(ARCHIVE/"MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
zip_path = OUT/"H20_TESTE_LUCRO.zip"
with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED) as z:
    for name in [*names, "MANIFEST.json"]:
        z.write(ARCHIVE/name, name)
with zipfile.ZipFile(zip_path) as z:
    for name, expected in manifest["files"].items():
        assert hashlib.sha256(z.read(name)).hexdigest() == expected
shutil.copyfile(zip_path, DURABLE/zip_path.name)
receipt = {"zip_sha256": sha(zip_path), "payloads_verified": len(names), "bytes": zip_path.stat().st_size,
           "observation_byte_identical": True, "profit": None}
(OUT/"H20_TESTE_PACOTE.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8", newline="\n")
print(json.dumps({"status": "DELIVERED", "report": str(OUT/"H20_TESTE_LUCRO.md"), "package": str(zip_path), **receipt}))
