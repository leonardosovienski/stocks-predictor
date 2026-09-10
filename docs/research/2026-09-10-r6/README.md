# Correção de lacunas R6 — 10/09/2026

Os cinco objetos ausentes do pacote H20 foram recuperados com os hashes originais.
O verificador original aprovou todos os **1.448 arquivos**, totalizando 203.594.583
bytes. As cotações BOVA11 foram atualizadas até **09/09/2026**: 172 pregões de 2026,
171 registros anteriores sem alteração e nenhum pregão previsto faltante.

Isso elimina a falta de arquivos de I15 e atualiza a fonte de preços. Ainda não
certifica lucro executável/futuro, fontes econômicas completas ou operação real.
O registro R3 permanece histórico; esta rodada adiciona evidência, sem mudar seus
lacres, os protocolos ou os resultados anteriores.

## Recuperação e reprodução

| Objeto originalmente ausente | Recuperação comprovada |
|---|---|
| `baseline/audit/repository-f9987faa06d5.zip` | Mesmo `git archive` do commit registrado; hash idêntico |
| `audit/repository.zip` | Mesmo `git archive` de `b7435087…`; hash idêntico |
| `discovery_value_repair.py` | Blob Git com CRLF; hash idêntico |
| `discovery_value.py` | CRLF com seis linhas LF, identificadas pelo tamanho e hash originais |
| `discovery_reorganizations.py` | CRLF com cinco linhas LF; hash idêntico |

Não foram inventados conteúdos ou reemitidos hashes. O primeiro levantamento leu
2.444 blobs locais, incluindo objetos fora das referências, e 164.812.417 bytes.
A busca de versões uniformes não resolveu os dois últimos arquivos; a busca por
trechos com quebras diferentes resolveu. As tentativas e transformações constam
dos [recibos](manifest.json). Os cinco objetos autorais acompanham o repositório.
O recibo numérico completo está comprimido sem perdas; a CI verifica também o hash
dos bytes descomprimidos contra o manifesto anterior preservado em `manifest-v1.json`.

O ZIP externo histórico não foi recriado byte por byte. Seu conteúdo selado está
integralmente restaurado em
`C:\STOCKS\work\gap-resolution-r6-20260910\h20-complete-package`.

A reprodução com o código congelado reconciliou as quatro coortes e 9.732 células.
O comparador numérico original, que exige igualdade exata de floats, falhou em uma
anualização: diferença de **2,220446049250313e-16**. O comparador separado aprovou
com a tolerância de **2e-12 já registrada na R3**. O resultado original de falha foi
preservado; a aprovação de integridade dos arquivos não é aprovação daquele
comparador numérico estrito. Não há nova evidência econômica independente.

## Dados, fontes e datas

A captura oficial anual de preços tem SHA256
`34b774681cbd201ef197fb98af8d431e4d7302e801f58b66e54036d2935dc4f4`.
Foi obtida em 10/09/2026, às 15:20 UTC. O relatório distingue a data do pregão da
aquisição; não retrodata a disponibilidade histórica da fonte. As medições R5
mantêm o corte original em 08/09. O pregão de 10/09 estava em andamento na captura.

Dois boletins B3 confirmam dividendos antes sem data definida na revisão 14:

| Evento | Crédito reportado | Valor por ação | Documento |
|---|---|---|---|
| RECV3, ex 25/04/2024 | 15/05/2024 | R$ 0,05928343241 | [BDI, página 9](https://arquivos.b3.com.br/bdi/download/bdi/2024-05-15/BDI_05_20240515.pdf) |
| RADL3, ex 18/04/2024 | 31/05/2024 | R$ 0,04915092700 | [BDI, página 5](https://arquivos.b3.com.br/bdi/download/bdi/2024-05-31/BDI_05_20240531.pdf) |

Páginas examinadas em texto e imagem. A auditoria canônica da revisão 15 confirmou
**24 → 22 datas ausentes e 52 → 50 líquidos ausentes**, com 793 fontes primárias
verificadas. O resultado geral continua `BLOCKED_MISSING_EVIDENCE`. Ela mantém 800 pagamentos e todos
os direitos originais. Preenche essas duas datas e os dois líquidos no cenário PF
residente pré-2026, com a fonte tributária já preservada. A aquisição em 2026 fica
explícita: a correção contábil posterior não permite usar a informação em um sinal
histórico. O inventário de eventos completo continua sem certificação.

O exame dos avisos Ambev de fevereiro e maio de 2026 encontrou líquidos publicados
de R$ 0,063 e R$ 0,0642 para as duas primeiras parcelas do JCP de 2025. Eles não foram
convertidos automaticamente em líquido exato: a primeira publicação não reconcilia
com as alíquotas nominais, e a segunda tem precisão arredondada. A terceira parcela
é explicitamente estimada e futura. Os documentos e a inconsistência permanecem
registrados; preencher campos sem resolver isso produziria falsa precisão.

A [LC 224/2025, arts. 8 e 14](https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-224-26-dezembro-2025-798608-publicacaooriginal-177629-pl.html)
alterou a alíquota de JCP para 17,5% com efeitos em 01/01/2026. O fato gerador envolve
pagamento ou crédito ao beneficiário. Não foi aplicada uma taxa única a todos os
pagamentos de 2026, nem presumida a data do crédito fiscal a partir da data ex.

A [comunicação B3 de dezembro de 2020](https://www.b3.com.br/pt_br/noticias/tarifacao.htm)
documenta a transição da tarifa não day trade de 0,0325% para 0,0300% em 02/02/2021.
O exemplo em reais da página tem inconsistência aritmética; foi usada a tabela
percentual. Isso melhora a cadeia documental, sem certificar despesas históricas
da conta XP ou os custos específicos de execução do usuário.

A [política BOVA publicada pela gestora, página 8](https://www.blackrock.com/br/literature/continuous-disclosure-and-important-information/ishares-bova11-brl-informacoes-adicionais-ptbr.pdf)
prevê reinvestimento ordinário e exceções
para resgates/amortizações/liquidação. As demonstrações de 2018 também abrangem
2017, incluindo a transferência de administração, e incorporam dividendos/JCP ao
patrimônio. Isso reforça a revisão do aquecimento de 2017; não prova inexistência
universal de eventos. A exportação adicional da gestora contém volumes negociados,
não um inventário de proventos. Respostas HTTP 500/403 e boletins sem a tabela
necessária foram preservados como tentativas insuficientes. A demonstração 2018
preservada tem SHA `f88d52b52bf04d3b91156e6da914eb121fb5c83a4771b51c69518cc33ec258dd`,
páginas PDF 7 e 16 examinadas nesta rodada.

## Estado das pendências

| Achado R3 | Estado após R6 |
|---|---|
| I10 — PIT/identidade ampla | Parcial; publicação histórica e identidade por intervalo não certificadas em todo o painel |
| I11 — eventos BOVA | Políticas e contas ampliadas; inventário contínuo de eventos ainda parcial |
| I12 — conta/custos pessoais | Cenários disponíveis; condições reais XP e situação fiscal pessoal não informadas |
| I13 — tarifas históricas | Nova fonte oficial de transição; cadeia de custos exatos ainda parcial |
| I14 — fontes 13/14 | Revisão 15 aditiva com dois pagamentos reconciliados; inventário amplo ainda parcial |
| I15 — cinco arquivos ausentes | **Resolvido: 1.448/1.448 arquivos aprovados pelo verificador original** |
| I16 — futuro/execução | Sem execução real; horizonte prospectivo ainda não transcorrido |

Não foi criada automação, enviada ordem, autenticada corretora ou instalada
dependência no Windows. Não foi fabricado comprovante pessoal, dado futuro ou
atestado independente. As demais linhas permanecem abertas, com a distinção entre
trabalho documental recuperável e informação que precisa de fonte externa/futura.

## Reprodução

[Scripts e comandos](../../../research/session-20260910/gap_resolution/README.md),
[protocolo](protocol.json), [manifesto](manifest.json) e recibos em `evidence/`.
O verificador R6 entrou na CI, junto dos checks existentes em Python 3.13/3.14.
A [CI do primeiro conjunto de correções](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34498020049)
aprovou 859 testes e 29 subtestes em cada Python, cobertura 79%, Ruff, Pyright,
lock, identidades R3/R6, build, wheel fora do checkout e segredos, em `ec11a435…`.
Os 12 bancos e 20 recibos R4 foram novamente conferidos por hash, sem diferenças.
[PR77](https://github.com/leonardosovienski/stocks-predictor/pull/77) registra os
checks finais e o SHA integrado.

Foram preservadas 27 tentativas de captura nesta rodada. A verificação adicional
dos capítulos antigos 02/04/06 encontrou indicadores/renda fixa ou falhas de
acesso; não resolveu as datas restantes. Não foram usados esses PDFs para atestar
crédito de dividendos ou ausência de eventos.
