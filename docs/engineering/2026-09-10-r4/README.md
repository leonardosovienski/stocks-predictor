# Engenharia R4 — integridade, memória e infraestrutura

Rodada de 10/09/2026 UTC, posterior à auditoria integral R3. Base:
`0e9c48a87ff67bbd8d71fe5b9156799ba9bd8807` (PR74 integrado).
Pedido: corrigir erros e melhorar infraestrutura e desempenho.
[PR75](https://github.com/leonardosovienski/stocks-predictor/pull/75) registra a
integração e os checks por commit. Trabalho individual, na raiz `C:\STOCKS`.

O resultado é uma carga com memória limitada por lote e garantias transacionais
mais fortes, validação de entradas e CI mais abrangente. Não é uma declaração de
ausência de todo defeito possível. A [auditoria R3](../../audit/2026-09-10-integral/README.md)
e suas pendências econômicas I10–I16 permanecem registros preservados.

## Correções verificáveis

| ID | Defeito anterior | Comportamento corrigido | Evidência |
|---|---|---|---|
| R4-01 | Todo COTAHIST convertido em listas antes do filtro | Iteração contínua, filtro imediato e lotes de até 1.000 registros | Benchmark antes/depois com hashes iguais |
| R4-02 | Retorno contava duplicatas ignoradas como novas linhas | Retorna apenas inserções efetivas; replay idêntico retorna zero | `test_idempotent_replay_reports_zero_new_rows`, duplicatas no mesmo lote |
| R4-03 | Conteúdo diferente sob a mesma chave era silenciosamente ignorado | Comparação das 12 colunas; conflito de `(date,ticker,source_file)` desfaz a carga | Conflitos no lote, entre lotes e contra dado persistido |
| R4-04 | Carga confirmava transação do chamador e podia deixar linhas parciais | Savepoint preserva a transação externa; falha de fluxo, restrição ou commit desfaz a carga | Fluxo interrompido depois de 1.500 registros, CHECK e commit bloqueado |
| R4-05 | Snapshot deixava transação pendente quando seu commit era bloqueado | Rollback completo quando a transação pertence ao snapshot | Teste com dois clientes SQLite e bloqueio real |
| R4-06 | Datas inválidas podiam abrir/migrar banco antes da rejeição | Datas canônicas e calendário válido; contagens inteiras positivas; validação antecipada | Testes de entradas e escritor não chamado |
| R4-07 | ZIP ausente/ambíguo abria escritor; falha de migração vazava conexão | Validação do contêiner antes do escritor; fechamento em falha de migração | Testes de arquivo ausente, ZIP ambíguo e conexão fechada |
| R4-08 | Diagnóstico de status exigia Core disponível | Novo `doctor` stdlib com JSON, metadados e SQLite opcional | Windows sem Core; banco ausente não criado; banco de teste inalterado |
| R4-09 | CI aceitava lock desatualizado, cobertura zero e não testava Python 3.14 | Lock obrigatório na instalação; duas versões; piso 77%; timeout, concorrência e artefatos | Workflow e execuções vinculadas abaixo |
| R4-10 | Erros de tipos de argumentos estavam suprimidos | Diagnóstico habilitado; perdas monetárias aceitam Decimal; adaptador bootstrap atende contrato float | Pyright e igualdade do IC com o descarte histórico de amostras |

Regressões: [ingestão](../../../tests/test_ingestion_integrity.py),
[entradas/snapshot](../../../tests/test_input_contracts.py),
[entry points](../../../tests/test_entrypoint_integrity.py),
[diagnóstico](../../../tests/test_diagnostics.py) e
[bootstrap](../../../tests/test_bootstrap_contract.py).
Na base, sete dos dez testes iniciais de ingestão falharam. O bloqueio de commit
da carga e o do snapshot foram reproduzidos separadamente antes das correções.
Os três logs de falhas estão preservados em `evidence/`; não foram convertidos em
sucessos retrospectivos. Os testes adicionados usam bancos sintéticos isolados.

O parser público `parse_lines` continua retornando lista e contagem de linhas
malformadas. A otimização está em `load_prices`. Linhas individuais malformadas
ainda são puladas e contabilizadas; fonte sem cotações ou inteiramente inválida
falha. Essa compatibilidade não certifica completude do arquivo. A identidade
legada baseada em nome do arquivo não foi substituída por um sistema de versões:
conteúdo divergente exige investigação e uma origem versionada legítima.

## Medição de desempenho

O [escopo registrado antes das mudanças](evidence/scope.md) fixou 100.000 registros
sintéticos, 95% fora do filtro à vista, 5.000 inserções e três repetições por versão.
O mesmo gerador alimentou a base e a versão final. Não foram usados retornos para
escolher parâmetros de engenharia.

| Medida | Base | Versão final |
|---|---:|---:|
| Pico mediano de memória Python | 78.744.320 bytes | 377.772 bytes |
| Maior pico nas três repetições | 79.021.304 bytes | 832.052 bytes |
| Tempo mediano, com `tracemalloc` | 7,099 s | 5,356 s |
| Linhas novas no banco | 5.000 | 5.000 |

Redução de **99,52% no pico mediano de memória Python** nesse ensaio. A redução
de tempo observada foi 24,55%, com variação entre repetições; não é uma garantia
de velocidade. A medida exclui a memória nativa do SQLite e o instrumento de
medição altera o tempo. É um ensaio sintético de carga, não medição de RSS,
concorrência em produção ou de arquivos reais completos.

SHA256 da entrada em todas as repetições:
`669521986a1cbd1a051998ff861dbc19064132d46125ccde0be6e8d241096d0b`.
SHA256 das linhas armazenadas, ordenadas:
`f29ea3a5d0c3081e377fafa20be968c3e22c7114df47fd254787bfaba050b91d`.
SHA256 do `cotahist.py` medido após a correção final:
`32db7f1c39df16e74350f332c8949ac11e711f0f41a7566a27646d24a3b1589f`.

[Antes](evidence/benchmark-before.json),
[depois final](evidence/benchmark-after-final.json) e
[comparação](evidence/benchmark-comparison.json).
`benchmark-after.json` preserva a medição intermediária; ela não foi usada como
resultado final após a correção adicional do commit bloqueado.

## Infraestrutura e alcance da validação

A instalação Linux usa `uv sync --locked --all-extras`, seguida de comandos
`uv run --no-sync`. Assim, divergência entre manifesto e lock falha antes da suíte.
Matriz 3.13/3.14, sem cancelamento de um membro por falha do outro; jobs de qualidade
têm limite de 20 minutos, segredos de 10. Novos commits cancelam execuções antigas
do mesmo PR; execuções de `main` têm identificador próprio e são preservadas.
JUnit e cobertura JSON ficam disponíveis como artefatos por 14 dias.

O piso de cobertura de 77% foi escolhido abaixo da referência anterior reportada
de 78%, sem permitir uma queda ampla. Não é prova de suficiência dos testes.
Ruff continua com regras F; Pyright básico cobre os 17 arquivos explicitados em
`pyproject.toml`, agora incluindo carga, universo, validação e diagnóstico.
Não há afirmação de tipagem completa de todo o acervo.

O build isolado usa `uv build` e o backend declarado em `build-system`; a instalação
do ambiente de testes é travada pelo lock, mas o build e o smoke de instalação
externa ainda resolvem dependências conforme seus intervalos declarados. Portanto,
não há certificado de build hermético. A wheel é instalada e importada fora do
checkout, conferindo a origem dos módulos. Nenhuma dependência foi adicionada ao
runtime do projeto, e `uv.lock` preserva seus bytes.

Referências primárias das opções empregadas:
[uv: lock e sincronização](https://docs.astral.sh/uv/concepts/projects/sync/),
[uv: comandos de build](https://docs.astral.sh/uv/reference/cli/#uv-build),
[GitHub: concorrência](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) e
[artefatos](https://github.com/actions/upload-artifact/tree/v4).
O [Core 3.2 bootstrap](https://github.com/leonardosovienski/core-predictor/blob/v3.2.0/src/predictor_core/measurement/bootstrap.py)
descarta tanto `None` quanto valores não finitos. O novo adaptador usa `NaN` no
mesmo conjunto de reamostras inválidas; teste compara o IC diretamente à semântica
anterior. Não foram alterados sorteio, seed, protocolo ou valores históricos.

## Execuções e preservação

- CI200, `af1397d`: falhou em dois contratos de tipos que estavam suprimidos.
- CI201, `ee3f381`: 846 testes e 25 subtestes passaram em cada Python, cobertura
  reportada de 79%. O build falhou por `uv build --locked`, opção inexistente;
  corrigida para o comando suportado, preservando `--locked` no `sync`.
- [CI202](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34432353530),
  domínio `78d83fa78f5c9f2bf6ab137cc34c4b2b59190b86`: **847 testes e 25 subtestes
  aprovados em cada Python, 79% de cobertura reportada**, zero erros de Pyright,
  Ruff, recibos R3, build, instalação/importação externa da wheel e segredos
  aprovados. Tempos de teste: 252,87 s em 3.13 e 100,45 s em 3.14; comparação
  entre runners diferentes não isola um efeito causal da versão de Python.
  [Resumo](evidence/ci202-summary.json) e logs completos preservados.
- Windows Python 3.12.14: 59 testes stdlib após a correção do snapshot.
  `doctor --check` retorna 1 como esperado: Python fora da faixa de produção,
  Core e PyYAML ausentes. Isso é um diagnóstico correto, não falha mascarada.
- Doze bancos rehashados e idênticos ao catálogo. Nenhum banco operacional criado.
- Replay H21: oito resultados, 16.400 pontos diários e nove objetos originais
  de preços conferidos. Não é nova evidência independente nem nova hipótese.
- Verificador R3: 31 recibos e suas referências aprovados. Protocolos, fontes,
  acervo `vendor/`, resultados e evidência da auditoria não foram reescritos.

Os recibos locais identificam seus próprios SHAs de observação; o check posterior
do domínio e o check final de integração são distintos. Os logs de CI são o texto
UTF-8 retornado pelo conector GitHub, arquivado para consulta após a expiração dos
artefatos. [Manifesto dos arquivos](manifest.json).

## Reprodução

No checkout, com um Python stdlib disponível, sem instalação local:

```text
python -B main.py doctor
python -B -m unittest tests.test_ingestion_integrity tests.test_input_contracts tests.test_diagnostics -v
python -B tools/benchmark_ingestion.py --revision 0e9c48a87ff67bbd8d71fe5b9156799ba9bd8807 --output C:\STOCKS\work\NOVO-antes.json
python -B tools/benchmark_ingestion.py --output C:\STOCKS\work\NOVO-depois.json
python -B research/session-20260910/integral/verify_audit.py
python -B research/session-20260909/h21/reproduce_check.py C:\STOCKS\work\h21 C:\STOCKS\work\NOVO-replay.json
```

Usar nomes de saída novos. A comparação com a base requer esse commit disponível
no histórico Git. O replay H21 requer as fontes locais preservadas; um clone não
as fornece. A suíte completa com Core/pytest pertence à CI Linux neste ambiente.
Nenhuma instalação Windows, ativação de paper, ordem, coleta de mercado ou
automação recorrente foi feita nesta rodada.
