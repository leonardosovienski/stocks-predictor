# Encerramento revisado — 10/09/2026

O usuário pediu uma pausa com o trabalho revisado, corrigido quando necessário e
integrado ao GitHub. A infraestrutura de **pesquisa em lote, em um host com disco
local**, foi concluída e validada. **O objetivo econômico integral permanece aberto:
lucro líquido pessoal executável ou futuro não foi validado.**

Este é o ponto de retomada. A revisão cruzou o mandato original, o histórico
disponível da conversa, os registros R3–R8, os PRs, os artefatos e a CI por commit.
O leitor do aplicativo retornou somente os turnos iniciais; a continuidade foi
reconstruída também pelo contexto da conversa e pelos registros de execução.
Isso não representa revisão independente nem inspeção linha a linha de todo o
acervo histórico. A revisão final do código concentrou-se nas mudanças R8 de
armazenamento, CLI, isolamento de versões, backup/restauração e CI.

## Correção desta revisão

O fechamento da CI230 e o recibo da entrega R8 existiam apenas localmente e nos
PRs. O registro histórico de falhas ainda continha estados `CORRECTED_PENDING_CI`.
Agora o [fechamento final](evidence/ci230-closure.json), os resultados brutos de CI,
os recibos de build/entrega e seus [hashes](manifest.json) estão versionados.
Os recibos antigos não foram reescritos; a resolução posterior está vinculada abaixo.
O verificador deste encerramento roda também na CI.

| Registro histórico | Resolução comprovada |
|---|---|
| LOCAL-01: fsync no Windows e fixture WAL | Correção testada localmente e na CI Linux subsequente |
| CI223: comparação Row/tuple e dois hashes sinalizados | Regressão de migrações corrigida; CI224 e posteriores aprovadas |
| CI226: scan de push examinou zero commits | PR80 adicionou scan independente de toda a árvore versionada |
| CI227: seis falsos positivos na árvore inteira | Exceções por regra, caminho e conteúdo exatos; controle de detecção mantido |
| CI228: exceção de digest ainda não correspondia | Correção literal; CI229 e CI230 aprovadas |

As execuções 223 e 228 terminaram canceladas, com falhas em jobs já executados;
a 227 terminou com falha. Não foram recategorizadas como execuções aprovadas.

## Implementação validada e preservação

- PR79 e PR80 integrados; implementação R8 em
  `0742bfc6fc1f33edabf00aaea73b54435f415bfa`.
- [CI230 da main](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34526489586):
  em cada Python 3.13/3.14, 891 testes ativos e 63 subtests, mais 17 arquivados.
  O JUnit ativo registra 954 entradas porque inclui os 63 subtests;
  não são 954 testes independentes nem se somam as versões de Python.
- Cobertura geral: 79,54%/79,48% (exibição 80%/79%); piso 77% mantido.
  Lint, tipos, recibos históricos, builds idênticos e wheel instalado fora do checkout aprovados.
- Scanner da CI230: 1.538 arquivos, 148.855.849 bytes, zero alertas pendentes após
  exceções exatas; token sintético detectado na cópia exportada.
- Carga real: 55.986 preços/408 tickers, 02/01 a 09/09/2026, BDI02/mercado010;
  origem preservada e conciliada com R7. Aquisição em 10/09 não comprova publicação
  histórica de todos os dados. A capacidade adicional foi medida em 250 mil linhas sintéticas.
- Replay, escritores concorrentes, leitores/WAL, morte de processo, timeout,
  corrupção, backup e restauração testados. Os 12 bancos originais foram preservados.

Os artefatos neste diretório pertencem exatamente à implementação acima.
A CI do commit que adiciona este encerramento é uma execução posterior, consultável
no PR de integração e no histórico do GitHub; ela não muda os recibos da CI230.

## Estado dos achados e limites restantes

O [consolidado R7](../../audit/2026-09-10-r7/CONSOLIDADO.md) preserva os 75 itens,
50 registros sem líquido, 28 registros societários e as 1.590 ocorrências
sobrepostas. As 22 datas de pagamento ausentes se sobrepõem a esses grupos.
Não somar as contagens como se fossem falhas independentes.

| Frente | Estado na pausa / condição concreta de retomada |
|---|---|
| I01–I09, correções R4, recuperação I15 e omissão PR75 | Resolvidos no escopo registrado; evidência e resultados originais preservados |
| L22/M10: concorrência/capacidade | R8 acrescentou ensaios finitos e recuperação; falta capacidade irrestrita/atribuição por alocador, que não foi alegada |
| L10/L23: integração de origem/tempo | CLI integra as APIs; não certifica datas fornecidas, independência ou migra identidades históricas |
| L24/M12: reprodução local | Entrega R8 inclui fonte real, backup e histórico Git deste fluxo; os demais bancos/fontes externos continuam necessários aos experimentos antigos |
| I10/I11: informação histórica e cobertura | Completar identidade temporal, publicação/reapresentação e cobertura contínua de preços/eventos com fontes verificáveis |
| I12/I13: cenário pessoal e despesas | R$5.000 confirmado; prazo, residência fiscal, perda máxima quantificada, custos XP/assessor/fixos e valor do tempo desconhecidos |
| I14: caixa e eventos | Restam 50 líquidos, 22 datas e 28 registros societários; não imputar zero nem certificar os 1.248 intervalos sem essas provas |
| I16/M06: observação prospectiva | Zero observações concluídas; janela H21 previamente fixada até primeira sessão em/após 10/09/2027, sem antecipar resultado |
| Licenças e revisão independente | 794 registros: licença da base CVM identificada para dois ZIPs, licença individual de 792 documentos não verificada; revisão por este assistente não é independente |
| Operação financeira e perda do host | Não implantadas; backup externo/agendamento ausentes, RPO no último snapshot; testes não certificam falha física de energia/hardware |

H22 foi rejeitada nos 11 pares calculáveis de sua rodada de 24 avaliações (22
calculadas e duas inviáveis). H21 conserva resultado histórico condicional, sem
transformá-lo em lucro pessoal, futuro ou vantagem incremental validada. Não houve
nova seleção por retorno nesta revisão. Resultados negativos, erro de float de
2,22e-16 e limites estatísticos anteriores permanecem nos registros históricos.

## Reprodução e arquivos

No checkout completo, com Python compatível, os verificadores stdlib podem ser
executados sem instalar Core no Windows:

```text
python research/session-20260910/integral/verify_audit.py
python research/session-20260910/gap_resolution/verify.py
python tools/audit_registry.py
python tools/verify_operational_evidence.py
python research/session-20260910/final_review/verify.py
```

Para conferir também os 53 arquivos do ZIP local e os hashes dos 12 bancos:

```text
python research/session-20260910/final_review/verify.py --local
```

Suíte completa e builds: Linux/Python 3.13 ou 3.14, conforme
[workflow](../../../.github/workflows/ci.yml) e [runbook R8](../../engineering/2026-09-10-r8/RUNBOOK.md).
O [script da entrega R8](../../../research/session-20260910/final_review/deliver_r8_archived.py)
foi preservado para rastrear sua construção. É um script histórico ligado ao commit
0742bfc e a destinos exclusivos em `C:\STOCKS`; não deve ser executado novamente
nos destinos já existentes nem receber lacres reemitidos para aceitar outra revisão.

Entrega integral local desta implementação:
`C:\STOCKS\outputs\INFRAESTRUTURA_R8_EXECUTAVEL_20260910.zip`, 102.710.038 bytes,
SHA-256 `bd85c37c3222421c9380335bbb7ff2c725d8aa68e4a236ecc3981b7348974671`.
O [recibo](evidence/delivery-receipt.json) relaciona todos os membros, o relatório e
seus hashes. O ZIP recupera a implementação 0742bfc; o fechamento posterior está no Git.

Fontes, bancos, binários e entregas volumosas ficam preservados em `C:\STOCKS`;
o Git contém código, documentação, protocolos e evidência publicável. Isso segue o
[mandato original](../PROMPT_AUDITORIA_INTEGRAL_20260909.md), que não exige transferir
todos os dados locais ao remoto nem autoriza redistribuir documentos sem licença.

Para retomar, conferir `main`, este encerramento, R7/R8 e os hashes; escolher uma
dependência aberta com prova nova ou informação pessoal verificável. Não reabrir
busca ilimitada nem alterar a janela prospectiva para produzir aprovação.
A pausa não cria monitor, ordem, automação ou trabalho em segundo plano.
