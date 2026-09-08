"""Preserve the candid review and small integrity fix, without replacing history."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(r"C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907")
REPO = ROOT / "work/stocks-predictor"
WORK = ROOT / "work/chat-review-20260908"
CHAT = Path(r"C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2")
OUT = CHAT / "outputs"
ARCH = REPO / "research/session-20260908/chat-review"
DEST = ROOT / "outputs/chat-review-20260908"
ARCH.mkdir(parents=True, exist_ok=False)
DEST.mkdir(parents=True, exist_ok=False)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert "656 passed in 116.37s" in (WORK/"tests.log").read_text(encoding="utf-8")
assert sha(WORK/"h20-checked.json") == "aa184580bf5ba69b515a20cc40115453396bdefa470ac0f5408c0d3ced15e1a3"
assert not (WORK/"must-not-be-written.json").exists()

report = """# Revisão crítica de todo este chat — Stocks Predictor

**Não repetiria tudo da mesma forma.** As contas publicadas se reproduzem e parte importante da engenharia é útil. Houve, porém, uma falha concreta de integridade no último executor, já contornada por uma entrada verificada; também houve excesso de implementação e uma apresentação mais otimista do que a evidência econômica permite.

## O que foi relido e conferido

Li todas as mensagens de usuário e respostas dos quatro turnos concluídos deste chat: continuidade, pesquisa de modelos, implementação H20 e teste de desempenho. A ferramenta de histórico informou não haver página anterior. Li o anexo de continuidade, instruções, protocolos, alterações de código que sustentam as entregas e os relatórios. A revisão cobre este chat e seus artefatos; não é uma releitura de cada documento bruto ou de todas as conversas anteriores.

Revisei a aritmética, a diferença entre simulação e lucro, a contabilidade de fontes e a aderência ao pedido. Reconfirmei fontes externas materiais, mas não reauditei integralmente as 17 referências ou os resultados de cada autor. Uma falha inicial ao chamar a ferramenta de histórico com limite acima do permitido e uma falha de caminho de importação do novo script foram corrigidas; não eram falhas das contas.

## Minha avaliação por etapa

| Etapa | Avaliação | Eu faria novamente? |
|---|---|---|
| Continuidade e correções fiscais | Corrigir bases fiscais por carteira e impedir valores futuros/reutilizados indevidamente foi útil. As compras iniciais medem viabilidade limitada. | Sim, com escopo curto. Não equivale a certificar toda a legislação ou eventos reais. |
| Pesquisa de modelos semelhantes | As referências e a distinção entre receita do fornecedor e retorno do investidor foram adequadas. O mecanismo de valor/rentabilidade é plausível, sem prova de transferência à B3. | Sim. Evitaria chamar uma direção de “a melhor” com base numa pesquisa não exaustiva e em exemplos selecionados. |
| Implementação H20 | Seleção, filtros temporais e tolerâncias funcionam no escopo dos testes. As bandas de 30% e 2,5% são arbitrárias e registradas, não ótimas. | Faria um protótipo menor. Priorizaria antes a viabilidade do livro contínuo e do caixa. |
| Comparação histórica | Os números estão corretos para a marcação sintética especificada. Não testou a estratégia H20 completa em lucro líquido. | Faria apenas como diagnóstico secundário, com a limitação na primeira frase e sem apresentar CAGR como indício forte de rentabilidade futura. |

## Falha concreta encontrada e correção

O executor arquivado `compare_h20.py` conferia o hash do manifesto de execução, mas não verificava todos os arquivos listados nesse manifesto antes de ler `evidence.json`. Também aceitava por argumento um arquivo de status financeiro (`--gate`) sem vincular seu hash à observação congelada.

Reproduzi a falha com um arquivo fictício contendo status de conclusão e lucro 123. O executor copiou esse conteúdo para a seção contextual `h19_gate`. O campo principal de lucro continuou `null`, a seleção não mudou e o teste não autorizou operações. É uma falha de integridade e rastreabilidade dos metadados, não evidência de que o lucro principal foi inventado.

Os resultados anteriores usaram o arquivo legítimo, cujo SHA256 é `585c72395fc2fefc2e0bbd90b6756c516e58d0f1e29ada3d6de196f46ea49c27`. Portanto não há correção numérica das taxas publicadas a fazer por esse defeito.

A nova entrada `reproduce_h20_checked.py` verifica o manifesto congelado, todos os seus arquivos, o status financeiro e o código de medição. Confere a integridade novamente ao terminar e só grava uma observação nova se ela reproduzir os bytes anteriores. O arquivo fictício agora é rejeitado antes de carregar a medição; nenhum resultado é gravado.

O executor, os protocolos, observações e pacotes antigos ficaram preservados como arquivo histórico. Para novas reproduções, usar `REPRODUZIR_VERIFICADO.ps1` do pacote desta revisão. Rodar diretamente o executor antigo não recebe essa proteção adicional.

## O que eu corrigiria na minha interpretação e comunicação

1. **“Melhorou” precisava de qualificação ainda mais forte.** 14,58% ao ano é a taxa composta de marcações históricas com premissas, não lucro do projeto ou previsão. A resposta correta para “melhorou a projeção de lucro?” é: **ainda não sabemos; a comparação parcial ficou melhor em composição, mas não resolveu a projeção líquida**.
2. **Não faltam apenas fontes.** A H20 ainda precisa de integração de carteira contínua, retenção baseada nas posições realmente executadas, tolerância de peso, proventos e apuração/reserva de impostos das novas vendas. O executor H20 delega operações ao RetailBook; não acopla automaticamente a apuração mensal do OrdinaryTaxLedger entre vendas e compras. Essa é uma pendência de código/integração além dos dados ausentes.
3. **27,1% menos substituições não são 27,1% menos custos.** A contagem é de nomes planejados. A comparação histórica aplicou a mesma rotação integral hipotética a todas as alternativas e não executou a banda de peso. Não foi demonstrado que o ganho veio da economia de negociação.
4. **Reprodução não é independência científica.** Houve um segundo caminho de cálculo e conferência dos mesmos dados, pelo mesmo agente. Isso é verificação aritmética, não auditoria por terceiro, fonte independente ou teste fora da amostra. Os intervalos são descritivos e não corrigem a busca adaptativa.
5. **Os limites econômicos deveriam comandar a sequência.** Acrescentei uma hipótese que herdou as lacunas que haviam motivado a pausa da H19. Isso aumentou a complexidade antes de resolver o principal impedimento à decisão sobre lucro. Os testes e os pacotes não substituem esse avanço.

A vantagem média da retenção frente ao controle foi negativa na metade mais recente, e os intervalos das comparações principais incluem zero. A queda máxima entre finais de trimestre chegou a 48,24% no cenário adverso de custo dobrado. Não há base para transformar a melhora composta em uma taxa anual esperada para R$5–10 mil.

O cenário de duas horas mensais a R$25/h está aritmeticamente correto: R$600/ano, equivalentes a 12% de R$5 mil e 6% de R$10 mil. Mas são premissas, não seu custo real medido ou suas preferências. A pausa sugerida é uma decisão sobre esforço e incerteza, não demonstração de que essa estratégia é economicamente inviável.

## Fontes materiais reconferidas

- AVUV: o factsheet oficial de junho/2026 confirma 12,29% a.a. em cinco anos contra 8,23% do Russell 2000 Value e desempenho relativo inferior no ano. Isso confirma a citação anterior, não a capacidade de replicá-lo no Stocks. [Documento oficial](https://res.avantisinvestors.com/docs/avantis-us-small-cap-value-avuv-etf-fact-sheet.pdf).
- AQR: a página confirma que o estudo estima custos usando negociações institucionais reais e que valor/momentum se beneficiam da otimização considerada. Não é auditoria de nossa estratégia. [AQR](https://www.aqr.com/Insights/Research/Working-Paper/Trading-Costs-of-Asset-Pricing-Anomalies).
- Pós-anúncio: o resumo dos autores confirma a conclusão de formação eficiente de preços após 2016 no teste estudado. Não permite generalizar para todo PEAD na B3. [Artigo](https://arxiv.org/abs/2601.08962v2).
- Danelfin: a página confirma cobrança mensal de US$29, US$79 e US$179 nos planos citados. Não comprova margem do fornecedor ou lucro dos assinantes. [Preços](https://danelfin.com/pricing/monthly).
- SPIVA: a página confirma 90,8% de subdesempenho na categoria Brazil Equity em dez anos até 2025, sem representar a probabilidade de fracasso deste projeto. [SPIVA](https://www.spglobal.com/spdji/en/spiva/article/spiva-latin-america/).

A tentativa de reabrir a página NBER nesta revisão recebeu erro interno. Não trato essa tentativa como reconfirmação de seu conteúdo. A leitura anterior e suas limitações permanecem registradas.

## Validação e decisão

**656 testes passaram nesta revisão**, em 116,37 segundos: os 639 testes de produção anteriores, 11 da medição histórica e seis novos de integridade. A nova entrada reproduziu a observação H20 byte a byte, SHA256 `aa184580bf5ba69b515a20cc40115453396bdefa470ac0f5408c0d3ced15e1a3`. Uma entrada financeira fictícia foi rejeitada sem publicar arquivo.

Não houve nova seleção, configuração de retorno, ajuste de parâmetros ou janela. A contagem administrativa anterior de 53 especificações/55 avaliações por cenário foi mantida; esses números não representam configurações ou provas estatisticamente independentes. A revisão não abre o holdout já exposto nem torna verde a cobertura econômica.

Eu repetiria a preservação, os pré-registros, as correções fiscais delimitadas, a pesquisa crítica e a divulgação das limitações. **Não repetiria a mesma sequência e volume de implementação.** Faria primeiro a menor demonstração completa de caixa e execução da regra congelada, com um critério objetivo de custo/benefício para decidir se vale continuar. Uma demonstração pequena validaria o mecanismo contábil, não seria um atalho para escolher um período lucrativo.

O resultado principal permanece **INCONCLUSIVE_NET_PROFIT / OPERATIONAL_NO_GO**. Não encontrei erro aritmético material nos números conferidos; isso não é uma certificação de que todo dado, regra fiscal ou código existente esteja correto. O que ainda falta é uma medição econômica integral e evidência futura independente.
"""

for p in (OUT/"REVISAO_CRITICA_CHAT_STOCKS.md", DEST/"REVISAO_CRITICA_CHAT_STOCKS.md",
          REPO/"docs/research/2026-09-08-chat-review.md", ARCH/"REVISAO_CRITICA_CHAT_STOCKS.md"):
    p.write_text(report, encoding="utf-8", newline="\n")
for name in ("reproduce_h20_checked.py", "test_h20_evidence_integrity.py", "deliver_chat_review.py"):
    shutil.copyfile(CHAT/"work"/name, ARCH/name)
shutil.copyfile(CHAT/"work/chat_review_transcript.json", ARCH/"chat_review_transcript.json")
for name in ("tests.log", "gate-integrity-before.json", "checked-reproduction.log", "checked-reproduction-final.log", "gate-rejected-after.log"):
    shutil.copyfile(WORK/name, ARCH/name)
wrapper = r'''param([Parameter(Mandatory=$true)][string]$OutputFile)
$ErrorActionPreference = 'Stop'
$reviewRoot = 'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907'
$env:PYTHONPATH = "$reviewRoot\work\stocks-predictor;$reviewRoot\work\runtime;$reviewRoot\work\checks"
py -3.13 "$PSScriptRoot\reproduce_h20_checked.py" --root $reviewRoot --gate "$reviewRoot\work\h20-profit-test-20260908\h19-gate-replay.json" --output $OutputFile
exit $LASTEXITCODE
'''
(ARCH/"REPRODUZIR_VERIFICADO.ps1").write_text(wrapper, encoding="utf-8", newline="\n")
review = {"status": "REVIEWED_WITH_INTEGRITY_FIX_AND_METHODOLOGICAL_CORRECTIONS",
          "completed_chat_turns_read": 4, "history_page_complete": True,
          "concrete_defects_reproduced": 1, "previous_numeric_results_changed": False,
          "tests_passed": 656, "new_integrity_tests": 6, "new_return_evaluations": 0,
          "production_strategy_or_tax_runtime_changed": False, "archived_experiments_preserved": True,
          "h20_byte_identical": True, "h20_sha256": sha(WORK/"h20-checked.json"),
          "forged_gate_rejected_before_publication": True, "profit": None,
          "would_repeat_everything_unchanged": False}
for p in (OUT/"REVISAO_CHAT_VALIDACAO.json", DEST/"REVISAO_CHAT_VALIDACAO.json", ARCH/"REVISAO_CHAT_VALIDACAO.json"):
    p.write_text(json.dumps(review, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")

note = """## Revisão crítica de todo o chat (08/09/2026 UTC)

Releitura dos quatro turnos e revisão técnica/metodológica concluída. Contas
anteriores reproduzidas; lucro líquido continua desconhecido. H20 histórica
mediu nomes pretendidos com rotação integral hipotética, sem banda de peso,
livro contínuo ou impostos incrementais integrados ao executor H20.
“Melhorou” deve ser entendido somente como composição de marcações; vantagem
recente e incerteza não sustentam projeção líquida. Sequência de implementação
foi excessiva frente ao gargalo econômico. Não repetir a mesma priorização.

Falha reproduzida: compare_h20 arquivado aceitava --gate sem hash e não conferia
todos os payloads do manifesto de execução. Arquivo fictício contaminava apenas
metadados contextuais; lucro principal continuava null. Arquivos legítimos foram
usados anteriormente, portanto números publicados não mudaram. Nova entrada
research/session-20260908/chat-review/reproduce_h20_checked.py verifica fontes,
gate e código antes de medir, novamente ao terminar e exige resultado idêntico.
Usar REPRODUZIR_VERIFICADO.ps1; executor/pacotes anteriores ficam históricos.

656 testes passaram (639 +11 +6 novos). Resultado H20 aa184580bf5b... byte idêntico;
gate fictício rejeitado sem saída. Nenhuma nova estratégia/avaliação de retorno,
ordem, gasto, instalação, agente, banco protegido escrito ou push. 53/55 é a
contagem administrativa conservadora anterior, não provas independentes.
Relatório: docs/research/2026-09-08-chat-review.md. Artefatos desta revisão em
research/session-20260908/chat-review e outputs/chat-review-20260908 da raiz.

"""
for name in ("HANDOFF.md", "STOCKS_CURRENT_STATE.md", "docs/continuation/UPDATE_20260908.md"):
    p=REPO/name
    p.write_text(note+p.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
readme=REPO/"README.md"
readme.write_text("> Revisão atual: [auditoria crítica do chat](docs/research/2026-09-08-chat-review.md). Para reproduzir H20, usar `research/session-20260908/chat-review/REPRODUZIR_VERIFICADO.ps1`; os executores anteriores permanecem arquivados. Lucro líquido não calculado.\n\n"+readme.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
with (REPO/".gitattributes").open("a", encoding="utf-8", newline="\n") as stream:
    stream.write("\nresearch/session-20260908/chat-review/** whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n")

names=["reproduce_h20_checked.py", "test_h20_evidence_integrity.py", "REPRODUZIR_VERIFICADO.ps1",
       "REVISAO_CRITICA_CHAT_STOCKS.md", "REVISAO_CHAT_VALIDACAO.json", "tests.log",
       "gate-integrity-before.json", "checked-reproduction-final.log", "gate-rejected-after.log"]
manifest={n:sha(ARCH/n) for n in names}
(ARCH/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n", encoding="utf-8", newline="\n")
package=OUT/"REPRODUCAO_H20_VERIFICADA.zip"
with zipfile.ZipFile(package,"x",compression=zipfile.ZIP_DEFLATED) as z:
    for n in [*names,"MANIFEST.json"]:
        z.write(ARCH/n,n)
with zipfile.ZipFile(package) as z:
    for n,d in manifest.items():
        assert hashlib.sha256(z.read(n)).hexdigest()==d
shutil.copyfile(package,DEST/package.name)
print(json.dumps({"status":"REVIEW_SAVED","payloads_verified":len(names),"zip_sha256":sha(package),"tests":656}))
