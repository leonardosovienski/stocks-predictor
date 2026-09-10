# Reprodução e uso dos controles R7

Python de produção: 3.13/3.14 com o lock do projeto, na CI Linux autorizada.
Os auxiliares stdlib aqui usados também foram executados no Python 3.12.14 do
Codex, no Windows. Não instalar dependências ou mudar o runtime deste Windows.

## Registro atual e evidências

Na raiz do checkout, executar:

```text
python tools/audit_registry.py
```

O comando confere a base V2 projetada, os 75 itens principais, 50 registros de
caixa, 28 societários, 1.590 ocorrências, 24 frentes e 22 afirmações. Verifica hashes
das evidências locais e se `CONSOLIDADO.md` corresponde ao JSON atual. Recusa perda
de itens e fechamento sem evidência. O verificador confirma estrutura/identidade,
não julga sozinho se uma prova científica é suficiente. Mudanças de estado devem
ser revisadas em Git; ele não permite promover lucro ou habilitar capital.

Para gerar uma cópia em destino novo:

```text
python tools/audit_registry.py --render C:/STOCKS/outputs/consolidado-r7-copia.md
```

A projeção pública mantém os grupos técnicos e seis achados do chat. A conversa
completa e o V2 original ficam preservados localmente; o hash do V2 está na
proveniência da base. Correções de R7 são sobreposições, sem reescrever vereditos.

## Fonte15 a partir do delta

```text
python tools/materialize_source_revision.py --parent C:/STOCKS/data/recovery-r2/source14-inputs --revision C:/STOCKS/work/completion-r7-20260910/source15-delta --output C:/STOCKS/work/source15-replay-new --parent-sha 3b36e2416e44f2b0a30e88d4306e00cdc74a7302c6e9b0e33950a893ea169bda --revision-sha 1c6410bebc9627d6dea8ae6ac4a9034823786fa47c48c26a8632c529c8560c46
```

O destino e o recibo precisam ser novos. `--parent`, `--revision` e `--output`
aceitam outras localizações; os hashes identificam estas revisões específicas.
São necessários a Fonte14 íntegra e seis arquivos alterados mais o manifesto
completo da Fonte15. A execução real R7 produziu 830 arquivos idênticos. O delta
e as respostas completas da coleta estão na entrega local, não todos no Git.

## Ingestão com origem versionada

`stocks_predictor.source_catalog.ingest_version` recebe conexão SQLite já
preparada com `prices_raw`, ZIP original, `publisher`, `dataset`, `version`,
`source_url`, `observed_at` com fuso e diretório temporário explícito. Ela copia
os bytes para um snapshot temporário, calcula a identidade por conteúdo e
política, rejeita preços malformados e realiza catálogo+preços na mesma transação.
Usar nova versão para conteúdo novo. Replay idêntico retorna zero inserções.

Essa API é opt-in. O comando legado não foi redirecionado silenciosamente; as
origens históricas e os bancos existentes não foram migrados. `observed_at`
descreve a observação informada pelo chamador, não uma publicação histórica
certificada por terceiro. A demonstração executável está em
`tests/test_versioned_sources.py` e usa bancos novos.

`stocks_predictor.temporal_evidence.estimate_asof` aceita resultados datados,
com decisão anterior à maturidade, maturidade até a observação e observação
estritamente anterior ao corte. A guarda não demonstra independência estatística
nem a veracidade de datas fornecidas. A API antiga mantém sua semântica.

## Custos pessoais e observação futura

`ResearchProfile(Decimal('5000')).assess()` retorna o capital confirmado e os
campos ainda desconhecidos. Taxas de corretagem/assessoria, custo fixo, implantação,
tempo de manutenção e custo de oportunidade não recebem zero implícito. Reserva
de caixa e custo do trabalho são separados. Tributos e taxas de bolsa exigem
registros aplicáveis. O resultado nunca autoriza ordens nem certifica lucro.

A [prontidão prospectiva](evidence/forward-readiness.json) referencia por SHA o
plano H21 já registrado. Há zero observações futuras concluídas e zero ordens.
O coletor `research/session-20260910/gap_resolution/acquire.py` recebe plano JSON
de pares nome/URL e destino novo; salva corpo, horários UTC reais, URL final,
status e hash. O primeiro checkpoint só cabe após publicação da sessão de entrada.
Data de download, publicação, decisão e liquidação não são intercambiáveis.

Para uma futura comparação econômica adicional, registrar antes de medir:

1. Mesmas datas e capital R$5.000, regras fixas de execução/saída, todos os custos
   e tributos aplicáveis, sobras e recebíveis pendentes reconciliados para cada opção.
2. Benchmark **investível** específico com fontes de preço, reinvestimento e
   despesas; uma série Selic bruta isolada não é esse livro líquido.
3. Lucro nominal `patrimônio final líquido − capital inicial`, lucro em poder de
   compra `patrimônio final líquido / fator de inflação − capital inicial` e
   diferença entre patrimônios finais líquidos, apresentados separadamente.
   O fator precisa ser positivo e cobrir datas equivalentes com fonte oficial.
4. Drawdown, prazo, concentração, alternativas rejeitadas e custos do próprio
   projeto. Dados já vistos permanecem exploração; o holdout exige observação nova.

Isso é especificação de insumos/aceite, sem registrar uma nova estratégia ou
alterar o comparador congelado H21. Não houve nova medição de retorno na R7.

## Desempenho e distribuição

`tools/benchmark_real_ingestion.py` parametriza fontes, revisões, repetições e
saída nova. O recibo publicado contém os hashes dos dois extratos reais e das
linhas de saída, tempos de CPU/parede e pico RSS de processos novos. Antes:
`0e9c48a87ff67bbd8d71fe5b9156799ba9bd8807`; depois:
`e9f6c9f1003828180655662af2f81076fddf2f70`. Três medições por combinação.

No Linux CI, `tools/reproducible_build.py` exige checkout limpo, usa epoch do
commit e dependências de build fixadas, constrói em dois diretórios e compara
wheel/sdist. O `.gitignore` auxiliar do uv não é distribuição. Falhas anteriores
do verificador foram mantidas no histórico. Igualdade no ambiente controlado
não é garantia de identidade entre quaisquer sistemas operacionais.

Os 17 testes arquivados identificados são executados em comando separado da
suíte ativa. Ambos os ambientes fazem instalação da wheel e imports isolados
fora do checkout. Logs completos locais e trechos rastreáveis registram também
as tentativas com falhas anteriores; não há supressões para produzir aprovação.
