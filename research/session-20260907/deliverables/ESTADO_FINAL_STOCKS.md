# Estado final de Stocks

**A revisão técnica foi concluída. O projeto ainda não demonstrou lucro líquido.**
Ele é um protótipo de pesquisa auditável, com dados e contabilidade societária
insuficientes para concluir o resultado econômico. Decisão atual: **não operar**.

| Verificação | Resultado |
|---|---|
| Código | 592 testes passaram; lint, análise estática ampliada e wheel passaram |
| Correções | Entregas parciais, conhecimento de eventos, vínculo ao protocolo, casos inválidos e consultas sem escrita |
| Cotações | 365.198 registros comparados com os extratos brutos, sem divergência nos campos auditados |
| Resultados antigos | 9.732 células e 12 cenários reproduzidos; continuam sendo diagnósticos de preços |
| Execução econômica real | Tentada; bloqueada por evidência incompleta, sem retorno publicado |
| Lucro ou prejuízo líquido | Ainda indeterminado; bloqueio não significa lucro zero |

Faltam 356 datas de pagamento, certificar o inventário de caixa dos 1.237
intervalos e integrar os 36 registros societários exigidos. Há também tratamento
fiscal que depende da posição de cada carteira: essa parte exige código e revisão
de fontes. Não é apenas preencher datas ou apertar outro botão de execução.

O pacote `STOCKS_REVISAO_FINAL.zip` contém o código completo, a wheel e uma
reprodução offline. `RODAR_H19.ps1` executa a auditoria com Python 3.13 global,
sem instalar bibliotecas. Com estes dados o resultado correto é **código 2**.
`RESULTADO_H19.json` enumera as pendências. O programa não envia ordens.

Os detalhes e limites da revisão estão abaixo.

---

# Revisão final de Stocks — 07/09/2026

O projeto é um protótipo de pesquisa com evidência econômica incompleta. Não é
um sistema de investimento validado. A revisão encontrou defeitos reais, corrigiu
os casos reproduzíveis e mantém como desconhecido o resultado líquido histórico.

## Histórico científico

| Linha | Leitura após revisão |
|---|---|
| H1–H16 | Quinze hipóteses executadas; H3 não executada. Preservar os vereditos históricos, mas os motores/preços/benchmarks antigos não sustentam lucro executável. H11 em particular tem proventos e retorno total não certificados. |
| H17 | Diagnóstico observado duas vezes, com correção documentada. INCONCLUSIVE_DATA_QUALITY; não ajustar direção ou limiar para resgatar o resultado. |
| H18 | Controle de valor, enfraquecido por instabilidade temporal. Sem promoção. |
| H19 trimestral | Prioridade relativa para resolver evidência; não é edge confirmado. Os 12 intervalos descritivos da validação de preços incluem zero. |
| RJ | Código e registro histórico preservados; testes mecânicos não criam evidência nova nem autorizam operar. |

Ao menos 32 configurações e 37 avaliações já foram expostas ao histórico.
Não existe holdout intacto demonstrado. Mesmo um futuro replay líquido positivo
nesta janela seria exploratório. A revisão atual não revela retorno novo.

## Defeitos corrigidos

- Os comandos consultivos `status`, `analyst`, `splits-review` e `cobertura_h18`
  abriam a conexão que cria/migra o banco. A consulta agora usa SQLite somente
  leitura, e `status` com banco ausente não cria nada. O adapter do ecossistema
  informa H19 inconclusiva/NO_GO, alinhado ao estado corrente.

- Venda parcial de ações negociáveis antes do crédito não reduzia o lote pendente.
  O lote podia exceder a posição restante e bloquear vendas posteriores indevidamente.
- Compra junto a uma entrega ainda pendente era rejeitada, embora fosse possível
  manter o bloqueio individual da entrega. Agora somente a quantidade pendente fica travada.
- Quantidades societárias publicadas depois da data-ex podiam ser aplicadas no
  passado. A API exige conhecimento dos termos até a data do evento; revisões
  futuras precisam ser representadas como revisões datadas.
- Um manifesto refeito localmente permitia trocar o protocolo, as carteiras ou
  a janela sem comprovar igualdade com a observação congelada. A H19 agora confere
  os dois hashes registrados e todos os membros/datas de ambas as carteiras.
- Lista vazia de casos podia terminar em sucesso sem executar carteira alguma.
  Capital, custos, unicidade, datas, lotes e calendário recebem controles explícitos.
- O bloqueio econômico ocorria antes da leitura das cotações. O executor agora
  valida a fita inteira mesmo quando ainda faltam eventos; mercados indevidos,
  preços inválidos, identidades ambíguas e duplicatas são erros de entrada.
- Bonificação em outra classe não altera as unidades da ordem na ação original.
  O executor aceita esse caso e atribui o direito só à posição anterior. Não cria
  direito para compras na data-ex. Isso não aprova automaticamente os termos reais.
- Testes sintéticos agora são identificados como tais e não incrementam o contador
  de observações históricas. README/estado/metadados desatualizados foram corrigidos.

Onze casos de regressão falharam no código anterior, reproduzido em pasta isolada.
O Pyright foi ampliado para os módulos H19; suas 11 queixas de estado opcional
foram resolvidas com invariantes/validação, sem desativar as checagens.

## Fonte, execução e lacunas

Conferidos 365.198 registros de cotação contra os extratos brutos da B3, com cinco
campos numéricos por registro, identidade e unicidade. As 367 cópias das fontes
referenciadas possuem o hash esperado. Isso mede integridade do conjunto adquirido;
não prova que o universo de eventos está completo, nem que uma ordem teria sido
preenchida na abertura do mercado fracionário. Custo/slippage continuam cenários.

Dos 778 registros atuais de caixa, 356 não têm data de pagamento. Nenhum dos
1.237 intervalos tem certificação de inventário completo. O arquivo operacional
de eventos societários contém zero entradas aprovadas frente a 36 requisitos:
existem fontes e revisões parciais, que ainda precisam virar dados executáveis.
Esses números não são uma contagem de erros de Python.

Além das fontes, permanece trabalho de implementação/integração: imposto individual
de reorganizações e leilões depende de custo fiscal e quantidade de cada carteira;
uma constante por ação não é uma solução geral. Conversões que mudam a unidade de
ordem entre sinal e execução exigem transformação revisada. Bonificações de outra
classe são suportadas mecanicamente, mas precisam dos termos reais de entrega,
negociabilidade, fração e tributação. O caixa dos sucessores e a história posterior
de JBS também impedem certificar o conjunto como completo.

O arredondamento de centavos por nota/pagamento, alternativas líquidas de caixa,
custos fixos, tempo de manutenção e fills prospectivos continuam sem validação
integral. Ter o calendário DARF de 95 meses não resolve toda a fiscalidade.

## Decisão de projeto

Manter fontes imutáveis, identidades, protocolo congelado e bloqueio de resultados
incompletos. Consolidar a leitura corrente em um parecer e um pacote reproduzível,
preservando os relatórios antigos como história. Não adicionar ML, H20 ou uma
varredura de parâmetros para contornar lacunas de medição. Não promover a antiga
curva sintética de preços a lucro real. A conclusão apropriada é
INCONCLUSIVE_NET_PROFIT / OPERATIONAL_NO_GO, e não lucro zero ou prejuízo demonstrado.

Sobre R$5 mil/R$10 mil, cada ponto percentual anual incremental corresponde a
R$50/R$100 antes de custos fixos. É escala aritmética, não previsão. A necessidade
de reconstrução manual extensa reduz a atratividade econômica da operação neste
capital. Não há evidência suficiente para afirmar rentabilidade futura.

As regras ordinárias de IRRF e isenção foram reconferidas nas páginas primárias
da Receita: [retenções](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/retencoes)
e [isenções](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/isencoes).
Essas regras não certificam a tributação específica das reorganizações.

## Validação desta versão

Validação final do código `741d237388405970127492a4eff81ab1e5c755a1`: **592 testes passaram** em
206.77 segundos. Cobertura geral 79%; contabilidade de varejo
86%, execução contínua 78% e driver
78%. Ruff, Pyright no escopo ampliado, build da wheel e importação
fora do checkout passaram. O recorte independente passou 48 testes. O comando
de status foi executado no banco real com conexão somente leitura; os dois bancos
mantiveram os hashes anteriores. Nenhuma instalação/dependência nova de runtime.

O replay real validou 31 arquivos de entrada e 365.198 registros de cotação,
então terminou com **exit 2 / BLOCKED_MISSING_EVIDENCE**. Não executou o histórico
completo nem publicou retorno parcial. Os quatro casos continuam cadastrados;
nenhum foi observado nesta revisão. A reprodução anterior conferiu 1.448 arquivos,
as quatro coortes, 9.732 células e os 12 cenários/intervalos antigos idênticos.
Isso não acrescenta amostra independente nem transforma preços em lucro líquido.
