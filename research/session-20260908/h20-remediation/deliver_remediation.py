"""Package this bounded repair and retain the original sources and observations."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

CHAT = Path(r"C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2")
ROOT = Path(r"C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907")
REPO = ROOT / "work/stocks-predictor"
WORK = ROOT / "work/h20-remediation-20260908"
ARCHIVE = REPO / "research/session-20260908/h20-remediation"
OUTPUTS = CHAT / "outputs"
ARCHIVE.mkdir(exist_ok=True)
OUTPUTS.mkdir(exist_ok=True)


def write(path, text):
    path.write_text(text, encoding="utf-8", newline="\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert "687 passed" in (WORK/"full-tests-clean.log").read_text(encoding="utf-8")
validation = json.loads((WORK/"verification.json").read_text(encoding="utf-8"))
validation.update(protocol_commit="38cf95f", tested_runtime_commit="62444c0",
    full_suite={"passed": 687, "seconds": 114.87, "warnings": 0,
                "production_tests": 670, "archived_tests": 17, "new_regular_tests": 31},
    extracted_wheel_tests={"passed": 104, "seconds": .59},
    initial_full_suite={"passed": 669, "failed": 18,
        "cause": "Core requires a clean committed working tree for synthetic trial attestations; repeated after commit without bypassing it. Initial error output also exposed a Windows encoding warning; canonical wrappers set UTF-8."},
    scientific_independence=False, profit=None, future_profit_projection=None)

report = """# Correções da revisão — Stocks Predictor

**Corrigi as pendências de código, integração e rastreabilidade identificadas. A demonstração de lucro líquido continua pendente de fontes e de evidência futura.** Não há base para dizer que todas as questões econômicas foram resolvidas.

| Achado da revisão | Situação após a correção |
|---|---|
| O medidor aceitava status financeiro sem vínculo e não verificava todos os arquivos | **Corrigido no caminho atual.** `stocks_predictor.h20_checked` confere manifesto, todos os arquivos, status financeiro e código; repete a verificação e exige o resultado anterior byte a byte. Está na wheel e na suíte regular. Os executores antigos permanecem arquivados. |
| H20 sem livro contínuo e retenção das compras reais | **Integração implementada e testada.** `H20Policy` usa ticker, ISIN e quantidade efetivamente detida em cada sinal; posições planejadas e não compradas não recebem retenção. |
| Tolerância de peso, proventos e impostos das novas vendas desconectados | **Corrigido na integração contínua.** O mesmo motor processa proventos, entregas, base fiscal, leilões, liquidação e reserva de impostos antes das compras. As bandas são congeladas no sinal; saídas obrigatórias e liquidação final continuam obrigatórias. |
| O auxiliar de ordens podia ser confundido com contabilidade fiscal completa | **Contrato esclarecido.** `execute_rebalance` declara que não apura os impostos incrementais. O caminho para contabilidade contínua H20 é `run_h20_book`; nenhum desses motores de baixo nível certifica a completude das fontes. |
| Usar a cobertura H19 como se bastasse para H20 | **Verificação específica implementada.** O diagnóstico exige revisão H20 vinculada aos sinais, manifesto e intervalos conservadores, com fontes locais identificadas por hash, além das verificações de cada evento. Uma declaração genérica não basta. |
| “Melhorou”, 27,1% menos trocas e verificação “independente” | **Interpretação corrigida.** Marcação composta não é projeção líquida; substituições de nomes não são custos executados; conferência pelo mesmo agente não é auditoria por terceiro ou teste fora da amostra. |
| Ampliar hipóteses antes de resolver o gargalo econômico | **Procedimento corrigido nesta etapa.** Protocolo prévio, regras H20 preservadas, demonstração contábil delimitada e nenhuma nova avaliação de retorno histórico. Não houve busca de parâmetros ou janela lucrativa. |
| Fontes integrais e evidência de rentabilidade | **Pendente.** Código e testes não preenchem inventários de proventos, termos societários, datas ou evidência futura ausentes. |

A integração usa os três braços congelados, o mesmo universo válido, seleção de 20%, retenção até 30% e banda de peso de 2,5%. O caminho H19 padrão foi preservado. Não introduzi modelo, custo otimizado, janela, hipótese ou promessa de retorno.

**Validação:** 687 testes passaram na suíte completa, sem avisos, em 114,87 segundos: 670 de produção e 17 dos arquivos de pesquisa. Há 31 testes novos na suíte regular. Mais 104 testes passaram com a wheel extraída fora do checkout, sem instalação. Ruff e Pyright passaram, incluindo os módulos novos. A primeira tentativa completa parou em 18 testes por alterações ainda sem commit; repeti após registrar o código, mantendo o bloqueio do Core. Os caminhos de reprodução agora fixam UTF-8 para evitar ambiguidade de codificação no Windows.

Os casos sintéticos verificam compras sem saldo, banda de peso, retenção real, dividendo após a saída, recebíveis não pagos, impostos antes de comprar, bonificações, entregas bloqueadas, conversão de posição, leilão de frações, cotações futuras, identidade incorreta, fontes incompletas e liquidação total. Como exemplo contábil fictício: R$5.000 compram posições vendidas por R$10.000; a reserva fiscal de R$750 deixa R$9.250 para recomprar, sem usar o dividendo de R$62,50 ainda não pago. Esse caso testa a conta; não estima o ganho de uma carteira real.

Quatro livros sintéticos da H19 ficaram exatamente iguais ao código anterior `c1bfa15`. O diagnóstico H19 e a comparação antiga H20 também reproduziram os mesmos bytes. A H20 antiga continua sendo marcação com rotação integral hipotética, sem a execução contínua agora implementada. Seus números não se tornaram lucro líquido por causa desta correção. Houve verificação técnica e aritmética pelo mesmo agente, sem auditoria científica externa.

**Dependências ainda abertas, medidas com as fontes preservadas:** foram verificados 31 arquivos e 365.198 registros de cotações. Há 1.217 intervalos do universo comum H20; a união conservadora com requisitos anteriores e sucessores conhecidos contém **1.248 intervalos**, incluindo 11 adicionais. **Nenhum possui certificado completo de inventário de proventos.** Nos 778 registros de eventos há 356 datas de conhecimento ausentes, 356 de pagamento, 357 de disponibilidade e 389 valores líquidos ausentes. Esses grupos se sobrepõem e não devem ser somados como eventos distintos. Faltam também 36 registros societários aprovados e integrados. O diagnóstico JSON lista os demais requisitos de execução, classe, arredondamento, frações e sucessores.

Uma revisão futura precisa documentar a completude das fontes, resolver cada campo/evento com evidência e vincular a nova versão de dados a um protocolo próprio. Não basta marcar `reviewed=true`, preencher zeros ou reutilizar o status antigo. A revisão documental validada por hash identifica os documentos; ela não prova sozinha a sua veracidade ou completude. O comando atual de prontidão apenas audita essas condições, sem executar retornos históricos.

**Lucro histórico líquido e projeção futura: desconhecidos.** Não refiz a contagem de nomes como economia de negociação, não inferi nova taxa esperada e não alterei os resultados expostos. A vantagem incremental permanece inconclusiva; não há holdout intacto. Os custos reais de manutenção também não foram medidos. Mantida a contagem administrativa de 53 especificações/55 avaliações, sem novo retorno histórico; isso não equivale a 55 testes independentes.

Código registrado em `62444c0`, após protocolo `38cf95f`. Fontes e observações anteriores preservadas; testes usam dados temporários. Sem ordens, gastos, instalações, alteração de parâmetros congelados ou uso de agentes adicionais. Os arquivos do pacote permitem revisar e repetir a correção localmente. A pendência de dados está registrada como pendência, não como falha resolvida.
"""
for path in [OUTPUTS/"CORRECOES_STOCKS.md", ARCHIVE/"CORRECOES_STOCKS.md",
             REPO/"docs/research/2026-09-08-h20-remediation-results.md"]:
    write(path, report)

top = """## Correções concluídas da revisão (08/09/2026 UTC)

Protocolo 38cf95f antes da implementação; código 62444c0. H20Policy integrada ao
run_continuous: posições realmente executadas, bandas no sinal, proventos,
entregas, leilões e impostos antes das compras. H19 padrão preservada. O auxiliar
execute_rebalance continua limitado à mecânica de ordens e explicita essa limitação.
Reprodução oficial: python -m stocks_predictor.h20_checked; proteção na wheel e
nos testes regulares, sem alterar o medidor/observações arquivados.

687 testes passaram sem avisos (670 regulares +17 arquivados); 31 novos regulares.
104 testes adicionais na wheel extraída fora do checkout; Ruff/Pyright verdes.
Primeira suíte parou por árvore sem commit; a repetição limpa passou sem bypass.
H19 e H20 anterior reproduzidas byte a byte; quatro livros H19 iguais a c1bfa15.
Conferência pelo mesmo agente, sem independência científica ou novas observações.

Diagnóstico H20 específico: 31 arquivos/365.198 cotações; 1.217 intervalos comuns,
união conservadora de 1.248, zero inventários completos certificados; 36 eventos
societários não integrados. Fontes de caixa/datas/valores ainda faltam. Exigir
revisão H20 vinculada às fontes e intervalos, além do controle de cada evento.
O motor contábil de baixo nível não certifica fontes. O CLI h20_continuous apenas
audita prontidão e retorna 2 enquanto bloqueado; não emite retorno histórico.

Não transformar marcações ou nomes planejados em lucro ou economia real de custo.
Lucro/projeção futura desconhecidos, sem holdout intacto; contagem administrativa
53/55 preservada. Nenhum novo fator, janela, retorno histórico, instalação ou ordem.
Não expandir hipóteses para contornar fontes ausentes. A próxima etapa econômica
depende de inventário documentado e revisão de eventos, não de novos parâmetros.

Relatório: docs/research/2026-09-08-h20-remediation-results.md.
Reprodução e evidências: research/session-20260908/h20-remediation.
Saídas duráveis: work/h20-remediation-20260908; entrega no outputs do chat.

"""
for name in ["HANDOFF.md", "STOCKS_CURRENT_STATE.md", "docs/continuation/UPDATE_20260908.md"]:
    path = REPO / name
    previous = path.read_text(encoding="utf-8")
    if name == "HANDOFF.md":
        previous = previous[previous.index("## Revisão crítica de todo o chat"):]
    write(path, top+previous)
readme = (REPO/"README.md").read_text(encoding="utf-8")
readme = readme.replace("[continuidade das correções](HANDOFF.md)",
    "[correções e validação](docs/research/2026-09-08-h20-remediation-results.md)")
write(REPO/"README.md", readme)

psbase = """param([Parameter(Mandatory=$true)][string]$OutputFile)
$ErrorActionPreference = 'Stop'
$repairRoot = 'C:\\Users\\Superleo13\\stocks-predictor-work\\.local-research\\stocks-session-20260907'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONPATH = "$repairRoot\\work\\stocks-predictor;$repairRoot\\work\\runtime;$repairRoot\\work\\checks"
"""
write(ARCHIVE/"REPRODUZIR_VERIFICADO.ps1", psbase +
      'py -3.13 -m stocks_predictor.h20_checked --root $repairRoot --gate "$repairRoot\\work\\h20-profit-test-20260908\\h19-gate-replay.json" --output $OutputFile\nexit $LASTEXITCODE\n')
write(ARCHIVE/"AUDITAR_PRONTIDAO.ps1", psbase +
      'py -3.13 -m stocks_predictor.h20_continuous --root $repairRoot --output $OutputFile\nexit $LASTEXITCODE\n')
usage = """# Reprodução local das correções

Use o Python 3.13 global e as dependências já disponíveis no projeto. Não instalar a wheel ou criar venv. A wheel fornecida foi extraída e testada como diretório de importação. A cópia dos arquivos `stocks_predictor/` identifica exatamente o código testado.

`AUDITAR_PRONTIDAO.ps1 -OutputFile CAMINHO_NOVO.json` verifica as fontes locais e grava as pendências H20. **Saída 2 é o resultado esperado de cobertura incompleta; lucro não é emitido.** `REPRODUZIR_VERIFICADO.ps1 -OutputFile OUTRO_CAMINHO_NOVO.json` reproduz a comparação antiga protegida; o resultado continua sendo um diagnóstico de marcações.

Ambos usam a raiz durável especificada nos scripts. Se os arquivos da pesquisa original não estiverem disponíveis nessa raiz, a reprodução deve parar; os scripts não baixam, reconstroem ou aprovam fontes. A comparação antiga exige os extratos históricos e seus hashes originais. Os arquivos de saída precisam ser novos.

Para os testes completos no checkout, com PYTHONPATH incluindo o checkout e os diretórios existentes `work/runtime` e `work/checks`, executar:

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
py -3.13 -m pytest tests research/session-20260908/h20-profit-test/test_h20_profit_comparison.py research/session-20260908/chat-review/test_h20_evidence_integrity.py -q
```

A árvore Git precisa estar limpa e commitada, pois o Core vincula os atestados sintéticos à versão do código. Não desativar esse requisito. `verify_remediation.py` registra a validação adicional desta etapa e suas saídas; cria diretórios novos e não deve ser repetido sobre os mesmos nomes já existentes. Os testes em `tests/` são dados sintéticos e podem ser executados contra o código ou a wheel extraída. Não são projeções de lucro.

Os executores anteriores são acervo histórico. Os caminhos indicados acima são os atuais. O protocolo, o relatório, os logs, a observação de prontidão e o manifesto acompanham o pacote.
"""
write(ARCHIVE/"COMO_REPRODUZIR.md", usage)
for name in ["full-tests.log", "full-tests-clean.log", "ruff.log", "pyright.log", "h19-replay.json",
             "h19-replay.log", "h20-checked.json", "h20-checked.log", "readiness-02.json",
             "h20-readiness.log", "readiness-wheel.json", "wheel-tests.log", "wheel-import.log",
             "wheel-readiness.log", "synthetic-accounting.json"]:
    shutil.copyfile(WORK/name, ARCHIVE/name)
shutil.copyfile(CHAT/"work/verify_remediation.py", ARCHIVE/"verify_remediation.py")
shutil.copyfile(CHAT/"work/deliver_remediation.py", ARCHIVE/"deliver_remediation.py")

# Rebuild for the updated README; compare every runtime module to the wheel
# already tested outside the checkout. Metadata changes do not change execution.
env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
       "PYTHONPATH": os.pathsep.join(str(p) for p in [REPO, ROOT/"work/runtime", ROOT/"work/checks"])}
p = subprocess.run([sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(WORK/"final-dist")],
    cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8")
write(ARCHIVE/"final-build.log", p.stdout+p.stderr)
assert p.returncode == 0
wheel, = (WORK/"final-dist").glob("*.whl")
earlier, = (WORK/"dist").glob("*.whl")
with zipfile.ZipFile(earlier) as before, zipfile.ZipFile(wheel) as after:
    modules = [n for n in before.namelist() if n.startswith("stocks_predictor/")]
    assert modules == [n for n in after.namelist() if n.startswith("stocks_predictor/")]
    assert all(before.read(n) == after.read(n) for n in modules)
validation["final_wheel"] = {"file": wheel.name, "sha256": sha(wheel), "unchanged_runtime_files": len(modules)}
write(ARCHIVE/"VALIDACAO_CORRECOES.json", json.dumps(validation, indent=2, ensure_ascii=False)+"\n")
shutil.copyfile(ARCHIVE/"VALIDACAO_CORRECOES.json", OUTPUTS/"VALIDACAO_CORRECOES.json")
shutil.copyfile(ARCHIVE/"readiness-02.json", OUTPUTS/"PRONTIDAO_H20.json")

# Copy a compact source/test snapshot in the delivery package, without the old
# databases, raw data or evidence libraries that must remain at the durable root.
manifest = {str(p.relative_to(ARCHIVE)).replace("\\", "/"): sha(p)
            for p in sorted(ARCHIVE.iterdir()) if p.is_file() and p.name != "MANIFEST.json"}
write(ARCHIVE/"MANIFEST.json", json.dumps(manifest, indent=2)+"\n")
package = OUTPUTS/"CORRECOES_STOCKS_REPRODUZIVEIS.zip"
with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for p in ARCHIVE.iterdir():
        if p.is_file():
            z.write(p, p.name)
    z.write(wheel, wheel.name)
    z.write(REPO/"docs/research/2026-09-08-h20-remediation-protocol.json", "protocol.json")
    for name in ["continuous_cash.py", "retail_cash.py", "continuous_research.py", "buffered_rebalance.py",
                 "h20_continuous.py", "h20_checked.py", "h20_research.py", "value_profitability.py"]:
        z.write(REPO/"stocks_predictor"/name, "stocks_predictor/"+name)
    for p in (WORK/"outside-wheel/tests").glob("*.py"):
        z.write(p, "tests/"+p.name)
print(json.dumps({"package": str(package), "bytes": package.stat().st_size,
                  "sha256": sha(package), "validation": validation}, indent=2))
