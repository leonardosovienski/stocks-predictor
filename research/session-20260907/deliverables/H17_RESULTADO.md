# H17 executada — resultado e como repetir

**O diagnóstico da H17 rodou com dados reais.** O pacote inclui código, dados e
um comando para repetir a execução offline com Python 3.13. A primeira rodada
foi preservada; quatro exclusões mecânicas indevidas foram corrigidas e a segunda
rodada foi registrada separadamente. Não houve mudança de hipótese ou direção.

**Resultado corrigido: `INCONCLUSIVE_DATA_QUALITY`.** A triagem não mostrou uma
vantagem consistente de accruals baixos. Isso não é erro de instalação e não é
uma conclusão definitiva sobre rentabilidade em retorno total.

| Medida | Resultado |
|---|---:|
| Meses programados / elegíveis | 96 / 94 |
| Meses com todas as observações medidas | 59 |
| Observações medidas | 5.352 de 5.399 — 99,13% |
| Observações não resolvidas | 47, incluindo 14 do quintil selecionado |
| IC médio entre accruals baixos e retorno, nos dados disponíveis | −0,0132 |
| Diferença mensal média do quintil contra o universo, apenas nos meses completos | −0,1613 ponto percentual |
| Testes automatizados | 483 aprovados |

A diferença mensal também foi negativa nas duas metades fixadas antes do
resultado: −0,1880 p.p. em 2018–2021 e −0,1356 p.p. em 2022–2025. Essas medidas
são **condicionais aos dados disponíveis**. Não omitem silenciosamente empresas
deslistadas: suas células continuam registradas, inclusive quando o retorno não
pode ser medido. Ainda assim, usar apenas células/meses completos pode introduzir
seleção pela disponibilidade futura e impede interpretar o resultado como uma
carteira executável.

## O que foi concluído

- Recuperação do ISIN nos arquivos COTAHIST originais para distinguir os papéis
  ao longo do tempo. Foi necessário ordenar os registros, pois os arquivos anuais
  não estão sempre em ordem cronológica.
- Reconstrução mensal do universo por liquidez e CNPJ, ligada a documentos CVM
  já públicos, respeitando recebimento, versão e escala monetária.
- Ligação de 194 eventos B3 à identidade histórica; inclusão exploratória de
  48 ajustes de uma fonte secundária e cruzamento de 81 ajustes coincidentes.
  Outras duas diferenças foram identificadas como arredondamento.
- Correção da comparação de três fatores arredondados de 1/3 e do evento composto
  de VIVT3 em 2025. O fator B3 foi mantido e não foi aplicado duas vezes.
- Programa com inputs lacrados por hash, leitura sem alteração do banco e
  resultados que não sobrescrevem execuções anteriores.

Os campos do ISIN seguem o [layout oficial do COTAHIST](https://www.b3.com.br/data/files/33/67/B9/50/D84057102C784E47AC094EA8/SeriesHistoricas_Layout.pdf).
A interpretação de percentuais de bonificação/desdobramento e de fatores de
grupamento segue a [documentação B3, página 18](https://www.b3.com.br/data/files/FB/83/0C/33/2D2109105391B9F8AC094EA8/OPCOES.pdf).
Respostas originais das consultas de eventos e seus hashes estão no pacote.

## O que ainda impede o backtest econômico completo

As 47 células restantes envolvem mudanças de identidade/código, ausência de
cotação nos dias definidos, incorporações, cisões, restituição de capital,
subscrições ou movimentos grandes ainda sem classificação documental. Uma célula
pode ter mais de um motivo. A relação completa está em
`h17-unresolved-outcomes.json` e dentro do pacote.

Também falta cobertura completa de dividendos/JCP e das condições de entrega de
direitos. A consulta atual da B3 omite algumas bonificações antigas; a segunda
fonte ficou indisponível para 41 códigos históricos. A ausência de um evento na
consulta não foi tratada como prova de inexistência.

Este diagnóstico usa retornos de **preço com ajustes teóricos de base** e não
estima lucro líquido executável com R$5 mil ou R$10 mil. O viés relativo de omitir
dividendos para a H17 é desconhecido. O histórico já foi usado em pesquisa
adaptativa; não existe holdout intacto identificado. A família H17 passa a ter
resultado observado, com duas revisões de medição registradas. H18/H19 continuam
sem resultado e dependem adicionalmente da base histórica de capitalização por
classe de ação. Os runners confirmatórios continuam bloqueados.

## Execução e verificação

No ambiente entregue, o lançador `RODAR_H17.py` já está ao lado do ZIP na pasta
`outputs`. Ele confere o pacote, extrai automaticamente para `work` e executa:

```powershell
py -3.13 RODAR_H17.py
```

Também é possível extrair o pacote inteiro e executar, na pasta extraída:

```powershell
py -3.13 rodar_h17.py
```

O programa salva um novo JSON em `results/`. Não é necessário instalar pacotes
ou obter credenciais. O arquivo `LEIA-ME.md` do ZIP explica os inputs e limites.

Código testado: `4f487098e702004a88f02fe65d62a008c6df618b`. Suíte completa:
483 testes em 138,36 segundos; cobertura geral de 84%; Ruff no escopo do CI e
Pyright configurado aprovados. A wheel foi construída e importada fora do
checkout, em diretório isolado. Os hashes do banco operacional e do banco de
fontes permanecem idênticos aos anteriores à execução.

A reprodução a partir do ZIP entregue, extraído em outra pasta pelo lançador,
passou: protocolo, conteúdo de todos os inputs, 5.399 células e resumo idênticos.
Só mudaram o horário da execução e os caminhos absolutos dos arquivos. A conferência
está em `h17-reproduction-verification.json`.

A primeira saída, a saída corrigida, as quatro diferenças e o registro do
consumo de evidência foram preservados. Não houve investimento, gasto ou ordem.
