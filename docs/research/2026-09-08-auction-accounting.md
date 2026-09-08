# Contabilidade de leilões ordinários e limite de integração

O motor passa a aceitar frações alienadas em leilão **quando a fonte revisada
classifica o evento como operação comum em bolsa**. Ele recebe quantidade legal,
valor bruto, despesas, retenção efetiva e datas separadas. O custo fiscal vem da
posição convertida ou do custo de bonificação declarado; não é uma constante de
ganho por ação. O registro fiscal separado aceita frações sem permitir ordens
fracionárias de quantidade não inteira.

O ganho entra na apuração de seu mês, junto às vendas ordinárias, compensações e
isenção aplicável à classe. A retenção do intermediário do leilão é um valor
revisado separado: não se presume que ele seja a mesma corretora das ordens.
O crédito recebido não antecipa compra; DARF e retenção seguem datas próprias.
Os termos futuros não entram antecipadamente no imposto ou poder de compra.
Se o leilão ocorre depois do encerramento do replay, o motor exige extensão fiscal
revisada em vez de publicar um lucro com a obrigação futura não calculada.

Exemplo de contrato de uma fração, inteiramente sintético:

```json
{
  "source_review": true,
  "sources": ["fonte primária do leilão"],
  "tax_source": ["revisão de enquadramento ordinário da classe"],
  "tax_treatment": "ordinary_exchange",
  "disposal_date": "2020-02-03",
  "known_on": "2020-02-03",
  "payment_date": "2020-02-10",
  "available_on": "2020-02-11",
  "gross_cash_per_fraction": "30",
  "fees_per_fraction": "1",
  "irrf_per_fraction": "0.2"
}
```

`per_fraction` significa por uma unidade da ação de destino, não por acionista,
por lote nem por ação original. Por exemplo, meia unidade gera bruto de R$15,
despesa de R$0,50 e retenção de R$0,10 nesse contrato inventado.
O arquivo de execução deve documentar essa unidade. Centavos efetivos da nota e
rateio da depositária ainda precisam de conciliação; os exemplos não os certificam.

Valores societários já líquidos de imposto pessoal usam
`tax_treatment=reviewed_portfolio_net` e `portfolio_state_sha256`, produzido por
`portfolio_fingerprint(book)` **antes** da ação. A conferência inclui histórico
de negócios e alienações, não só a posição atual: uma perda anterior pode mudar
o imposto com a mesma quantidade e o mesmo custo atual. Isso vincula o cálculo
externo revisado à carteira; produzir o hash não constitui aprovação da fonte.
Imposto fixo em `disposal_tax` também exige esse vínculo e conhecimento do valor
até a data da ação. Valores futuros precisam de um evento de reconhecimento,
nunca de uma obrigação antecipada escondida.

O caso VIVT continua sem aprovação para o replay. O fato relevante de 13/03/2025
especifica a operação em 15/04/2025; o documento de 19/05/2025 informa o resultado
após despesas, com a tributação pessoal ainda a verificar. Ele não fornece
separadamente todos os campos exigidos acima, nem comprova o crédito individual
exato na corretora. Não se preenchem bruto, despesas ou retenção com zero.

Reorganizações fora de bolsa, restituições que alteram custo fiscal, valores em
moeda estrangeira, impostos pessoais anuais e revisões de razão de entrega não
ganham classificação automática. São outros contratos ou fontes ainda necessários.
Nenhum dos 36 registros do replay real foi aprovado por esta implementação.

As regras ordinárias de ganho, deduções e compensação foram reconferidas na
[Receita Federal](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/bolsa-de-valores),
assim como o [limite mensal de isenção de ações](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/isencoes).
Essas regras gerais não substituem o enquadramento específico de cada evento.
A [LC 224/2025](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp224.htm) também
foi consultada: a mudança de JCP exige regra datada; não autoriza aplicar uma
alíquota pela data-ex a pagamentos/créditos de outro exercício. Os líquidos de
2026 não revisados continuam desconhecidos.
