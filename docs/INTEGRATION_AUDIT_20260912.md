# Auditoria de integração e consolidação — 12/09/2026

## Escopo e identidade

Continuidade do PR #85. O candidato integra a main `938f646b82eb999ee4513ccad13b0c93cac310f0`
e os quatro commits exclusivos até `a3d570fd33749ad62bdb4735bbc24b1ecd421e38`.
Os resultados finais por SHA ficam nos checks do PR e no recibo externo
`C:/STOCKS/work/audit-main-20260912`, evitando reemitir o documento a cada CI.
Não é release nem implantação; a instalação principal CAIN permanece separada.

## Defeito R8 e correção

A execução do verificador antes da correção falhou com
`current code population differs from operational evidence`: quatro ferramentas
Bundle/seleção ausentes do inventário. Foram executados os nove testes Bundle,
cinco de seleção e um teste Snapshot. O inventário corrente foi reconciliado pela
população calculada pelo próprio verificador, sem mudar o gate ou os recibos
históricos. O pacote científico não mudou; a CI mantém carga sintética de 250 mil
linhas, deduplicação e restore com wheel instalado fora do checkout.

Os testes novos usavam caminhos Windows literais também no Linux; agora usam o
temporário nativo no Linux e a raiz Stocks no Windows. O workflow de intercâmbio
passa a executar Bundle e seleção em 3.12/3.13/3.14, além de Snapshot.

## Contratos e aceites separados

ResearchSnapshotV1 é o relato parcial de `STOCKS_CURRENT_STATE.md`.
ResearchBundleV1 exporta o catálogo do recibo real `real-v020.json`, opcionalmente
com seleção de uma sessão no backup permitido. UNKNOWN, clocks ausentes,
reference_only e ausência de licença permanecem explícitos; preços não são copiados.

O contrato Bundle 1.0.0 é candidato canônico do Ecosystem no commit
`a9f6594c840482419d6c310f373813e0e71f17d0`, pinado no workflow; não está na
main Ecosystem `40b02c41452f0dd9441ae3cb35e8b006dd10cd29` inspecionada.
As fontes canônicas dos dois contratos são usadas nos testes auxiliares; isso
não é instalação de runtime Stocks nem uso de vendor histórico.

Importação Bundle exige aprovação administrativa do artefato exato no CAIN.
Exportação/testes não substituem esse aceite. A demonstração completa requer
importação, consulta, reimportação e archive restore do CAIN isolado; até existir
recibo dessas etapas, classificar o percurso como PARCIAL.

`.ci/cain-supply/overlay.zip` foi inspecionado, sem aplicação: exportador idêntico
à árvore e versões históricas de HANDOFF e documentação. Nenhuma implementação
necessária foi encontrada exclusivamente no ZIP.

## Preservação e Git

Inventário remoto: 14 branches; 12 secundárias ancestrais da main, uma candidata
com quatro commits exclusivos. Decisões individuais e SHAs: `baseline.json` na
pasta local da auditoria. Backup `stocks-before.bundle`, verificado por Git,
clonado em `restore-check.git` e conferido com `git fsck --full`.
Árvore inicial limpa, um worktree, sem stashes ou trabalho não rastreado;
ignorados inspecionados são caches. O bundle preserva Git, não os bancos externos.
Bancos e fontes originais permanecem intocados. Recuperação: clone do bundle em
novo destino dentro de C:/STOCKS, nunca sobre o checkout ou dados existentes.

Exclusões dependem de publicação e validação final, decisão por branch e condição
pelo SHA esperado. Não presumir limpeza concluída a partir deste documento.
A auditoria é técnica; lucro, habilitação de capital e nova pesquisa não foram certificados.

## Aceite administrativo e percurso concluído

Após o pedido de aprovação do SHA256
`6c8a00efb6b7ff418ab83372f6768aca8d4f2dd6ca7e9c5b3f81584bad6c9ee0`,
o usuário respondeu "aprovo tudo". O artefato exato foi novamente conferido,
aprovado pela CLI administrativa e importado no CAIN isolado. Consulta retornou
duas entidades/três relações; evidências comparadas ao manifest. Reimportação
retornou duplicate. Archive restore com raízes do produtor inexistentes recuperou
entidades, relações, evidências e referências; verificação/rebuild aprovados.
A web exibiu as duas entidades e as três relações, mantendo UNKNOWN.
Recibo: `bundle-approved-e2e.json` na pasta da auditoria.

A CI245 aprovou 966 testes por Python 3.13/3.14, sem falhas/erros/skips,
com cobertura 79,43%/79,35%. Os dois wheels instalados passaram no percurso de
250 mil linhas sintéticas, deduplicação e restore. Exportadores aprovados em
3.12/3.13/3.14. Ecosystem corrigido pelo PR23, main `1a21dd5`, CI144 aprovada.

A branch de entrega após integração do PR85 é main. As referências secundárias
citadas nos documentos anteriores são históricas e recuperáveis pelos commits
no inventário e no backup verificado. O recibo externo final registra o SHA
publicado, CI posterior ao merge e resultado da limpeza condicionada por SHA.
A integração delimitada não instala CAIN nem promove Bundle Supply a release
Ecosystem; permanece o pin canônico explicitado acima.
