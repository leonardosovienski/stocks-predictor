# Publicação e continuidade da sessão de 09/09/2026

O usuário pediu publicar no GitHub o trabalho produzido antes de encerrar a tarefa.
O código e os relatórios integrados até o PR72 já estavam na `main`, base
`7de0ea9ad5e9c34e695c49a2c720561cad283685`. Este pacote acrescenta o
[prompt integral final](../../../docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md)
e preserva os artefatos autorais que estavam fora do checkout.

## O que foi preparado

- Auditoria ampla de lógica, arquitetura, dados, fontes, metodologia e claims,
  orientada a lucro líquido executável e simplificação quando justificável.
- Critérios de execução, contabilidade, reprodução, limites e encerramento.
- Continuidade que supera a antiga fila limitada a completar eventos/custos H21.

A auditoria ainda não foi executada. Esta publicação não produz novo resultado
econômico, nova hipótese validada ou certificado global de prontidão.

## Conteúdo publicado

[MANIFEST.json](MANIFEST.json) mapeia caminhos relativos a `C:\STOCKS`, tamanhos,
SHA-256 e destinos no repositório. Arquivos autorais idênticos são referenciados
pelo mesmo conteúdo, evitando duplicações desnecessárias.

- `PUBLISHED_SNAPSHOT`: cópia preservada em `local/`.
- `PUBLISHED_IDENTICAL_CONTENT`: bytes iguais em outro caminho versionado.
- `LOCAL_ONLY`: conteúdo inventariado, mas não enviado ao GitHub.

As cópias incluem instruções anteriores, entregas, resultados, recibos, inventários,
catálogos, scripts auxiliares e registros de validação/coleta. Os originais locais
e seus lacres permanecem intactos. `.gitattributes` preserva os bytes das cópias.
O diff das cópias históricas conserva 32 ocorrências de whitespace preexistente,
mesmo reconhecendo CRLF como término de linha. Elas não foram normalizadas para
alterar os hashes. O diff dos arquivos atuais passa em `git diff --check`;
os checks existentes da CI permanecem inalterados.

Os scripts em `local/` são registros históricos. Não foram promovidos a comandos
operacionais ou à suíte ativa. Muitos possuem caminhos fixos, prazos encerrados
ou efeitos de escrita: examinar antes de executar e respeitar o mandato atual.
Links relativos dentro das cópias preservam o contexto original; o manifesto
é a referência para localizar cada conteúdo publicado.

## O que continua apenas local

O repositório é público. Este pacote não redistribui os bancos recuperados,
arquivos ZIP de migração, COTAHIST brutos, capturas HTTP, documentos de terceiros
ou suas extrações integrais. A publicação desses bytes não foi certificada
quanto às condições de redistribuição das fontes. Seus caminhos, tamanhos e
hashes estão registrados; a distinção é explícita, sem alegar backup completo.

Um clone do GitHub não contém todos os dados existentes em `C:\STOCKS`.
Preservar a pasta local e consultar `data/CATALOG.json`, o catálogo de recuperação
e os inventários de fontes antes de reproduzir as pesquisas.

## Verificação

O preparo conferiu hashes entre originais e cópias. A validação da publicação
confere os destinos do manifesto, a integridade do prompt de 24 frentes e os
links novos. A integração usa a CI Linux existente, sem modificar os checks,
o runtime Windows ou os resultados econômicos anteriores.

O commit e o PR fornecem a versão publicada. Seus checks devem ser consultados
no SHA correspondente, sem atribuir a esta consolidação resultados de outra versão.

O helper [prepare_publication.py](prepare_publication.py) documenta os critérios
do inventário. Depende do staging local da sessão e não é um restaurador dos dados.

O inventário cobre 4.514 arquivos fora do checkout: 365 cópias publicadas, 21
referências a conteúdo idêntico e 4.128 arquivos somente locais. Os bytes não
enviados somam aproximadamente 15,75 GB, incluindo cópias de migração e dados.
[VALIDATION.json](VALIDATION.json) registra os hashes e verificações locais;
[validate_publication.py](validate_publication.py) permite repetir a conferência
das cópias sem executar os scripts históricos. O helper
[finalize_manifest.py](finalize_manifest.py) registra a atualização do ponto
de entrada local e a resolução final dos destinos do manifesto.
