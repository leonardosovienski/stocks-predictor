# Contexto vigente e histórico — 09/09/2026

Use [PROMPT_NOVO_CHAT](PROMPT_NOVO_CHAT.md), [mandato](MANDATO_20260909.md)
e [estado atual](../../STOCKS_CURRENT_STATE.md).
Raiz `C:\STOCKS`; código em `C:\STOCKS\stocks-predictor`, main;
entregas em `C:\STOCKS\outputs`. [Mapa local](LOCAL_PATHS_20260909.json).

O texto de 07–08/09 abaixo é histórico. Capital informado, branch fix ativa,
raízes em Superleo13, dependências locais e ausência de push ali descritos
não são fatos deste computador. R$5/10 mil são cenários. Base H21 integrada:
`4a85d43`, 782 testes regulares na CI184. Somente nove COTAHIST recuperados;
bancos não restaurados integralmente. H21 inconclusiva para lucro executável,
com plano prospectivo já registrado, sem execução.

---

# Continuidade independente da conversa — 07/09/2026

> Atualização de 08/09/2026: o código vigente está na **main local e no GitHub**,
> com 777 testes aprovados. Só main permanece em ambos. Começar por MIGRACAO_MAIN.md e
> MIGRACAO_VERIFICADA.json. O checkout da branch fix citado abaixo é histórico;
> as raízes preservadas continuam servindo como origem dos dados, não como
> indicação da branch de código vigente.

O usuário pediu preservar tudo no Git, conferir o prompt e permitir apagar a
conversa anterior. Este diretório registra contexto operacional e científico;
não é uma nova hipótese ou promoção econômica. A íntegra do pedido inicial foi
copiada para INITIAL_REQUEST.md; PROMPT_NOVO_CHAT.md incorpora as instruções
posteriores e a auditoria final. Não é necessário recuperar o chat para continuar.

## O que foi reconciliado no prompt

- Capital R$5–10 mil é uma informação do usuário. Piso anual de lucro e horas de
  manutenção seguem desconhecidos; R$500/ano de um relatório antigo era cenário
  provisório do agente, não uma preferência confirmada.
- A autonomia para implementar e mudar a linha foi reiterada pelo usuário; ela
  não autoriza operações, gastos, alteração de registros protegidos ou resgatar
  retrospectivamente hipóteses. H19 pode perder prioridade por motivo econômico.
- O pedido original proíbe coordenar agentes e pesquisar outros domínios. Mantido.
- A restrição de bancos foi esclarecida: fontes existentes e ledgers são
  preservados; scripts legados que reconstroem bases não são um roteiro automático.
- 592 testes pertencem ao runtime 741d237; commits de documentação/preservação
  posteriores não receberam indevidamente crédito por uma nova suíte ou experimento.
- Código 2 é bloqueio de evidência; não é sucesso financeiro, lucro zero ou prejuízo.
- 36 são registros societários exigidos, incluindo componentes legais; não se
  afirma que sejam 36 operações independentes. As fontes parciais não são ações
  já aprovadas para o replay.

## Histórico e correções que não devem se perder

O trabalho começou com auditoria de versões/data/unidades CVM, universo e execução
legados. Houve reconstruções isoladas e diagnósticos H17, seguidos dos protocolos
H18/H19 e correções de eventos/medições. Os registros datados em docs/research e
as observações preservam essa sequência; títulos antigos não descrevem a prontidão
atual. H3 não foi executada; H11 aparentemente favorável não tem retorno total
certificado. H17 ficou inconclusiva; H18 é instável; H19 trimestral é Discovery.

Na revisão final foram corrigidos consumo de lotes em vendas antes do crédito,
compras junto a entregas pendentes, conhecimento temporal de termos societários,
vínculo das carteiras ao protocolo/observação congelados, casos vazios/duplicados,
calendários/mercados inválidos e distinção entre testes sintéticos e retornos reais.
Bonificação de outra classe mantém a unidade da ordem original e não dá direitos
a quem compra na data-ex. Os comandos consultivos passaram a usar SQLite somente
leitura, sem criação/migrações; README/estado/adapter foram alinhados à H19 NO_GO.

11 regressões reproduziram falhas no código antigo. A última suíte passou 592
testes, cobertura 79%; 48 testes passaram fora do repositório. O pacote final teve
450 payloads verificados e duas reproduções idênticas com código 2. Nenhuma nova
observação histórica foi produzida nessa revisão/preservação. Contagem mínima
mantida: 32 configurações / 37 avaliações, sem holdout intacto identificado.

## Dados que exigem cuidado

O arquivo `work/stocks-final-review-bundle/inputs` da raiz preservada contém o
protocolo congelado, observação original, 31 entradas com SHA256, cotações,
calendário fiscal de 95 meses e cadastro de evidências. corporate-actions.json
está vazio por revisão/integrabilidade pendente. Não tornar o gate verde copiando
marcadores de aprovação ou usando dividendos desconhecidos como zero.

- Caixa: 778 linhas atuais; 356 sem pagamento; cadastro V5 com 420 pagamentos
  individuais revisados e dois eventos normalizados em parcelas. Datas não
  certificam completude de inventário, líquidos ou arredondamento da corretora.
- Cobertura: 1.237 intervalos de ambas as carteiras/sucessores; zero inventários
  completos certificados. JBS posterior e proventos de sucessores não estão fechados.
- Fontes já adquiridas: work/h19-cash-expanded-source, h19-tax-source,
  h19-cash-closure-source, value-event-terms, source-acquisition e arquivos de índices.
  Há mais documentos nesses caches que nas 367 cópias do pacote final.
- LIGT 2021: grupamento/desdobramento composto arredonda posições para centenas.
  VIVT 2025: grupos de 40 viram blocos de 80. Net factor de preço sozinho não
  representa a posição inteira/fração do varejo.
- RENT 2025 entrega RENT4, com razão operacional revisada após a data-ex; CYRE
  2026 entrega CYRE4. Cotações PN foram adquiridas, mas termos/frações/fisco ainda
  não estão integrados. O caso mecânico de bonificação em outra classe foi corrigido.
- Resultado de leilão líquido de taxas não é necessariamente líquido de imposto
  pessoal. Imposto pode depender do custo fiscal/quantidade de cada carteira e
  não pode ser representado universalmente por uma constante por ação.
- Cogna tem parcela futura estimada em 2028; BBAS tem atualizações monetárias;
  ALSO tem parcelas explícitas. Não antecipar crédito, duplicar ou deduplicar
  parcelas cegamente. Relatórios de preço não substituem essa contabilidade.

## Preservação e execução

PATHS.json identifica raiz antiga e raiz durável. A substituição é para localizar
arquivos, não para reescrever conteúdo histórico/hash. Os scripts de pesquisa
autoria desta sessão foram arquivados em research/session-20260907/scripts; as
entregas textuais, em deliverables. Alguns scripts usam a estrutura antiga e têm
efeitos de escrita. Leia-os; prefira os entrypoints de replay testados.

Os dados brutos/ZIPs/bancos extensos ficam fora dos objetos Git, numa cópia local
verificada por SHA256. O manifesto dessa cópia é versionado. O checkout durável e
o banco operacional ficam fora da pasta do Codex desta conversa. O Git principal
mantém sua branch e arquivos locais anteriores; a pesquisa tem checkout próprio.
Não foi solicitado push ou publicação remota nesta etapa; commits locais e cópia
independente não devem ser descritos como upload ao GitHub.

A documentação de [worktrees do Codex](https://learn.chatgpt.com/docs/environments/git-worktrees)
descreve limpeza de worktrees geridos pelo aplicativo, inclusive ao arquivar tarefas.
Ela não estabelece aqui o destino de todo arquivo de uma conversa sem projeto.
Por isso a continuidade não depende de retenção do aplicativo: foi preparada uma
cópia explícita fora da pasta da conversa, verificável pelo recibo de preservação.

Para validar o recorte sem instalar bibliotecas, na raiz preservada:

```powershell
Push-Location .\work\stocks-final-review-bundle
py -3.13 -m stocks_predictor.continuous_research --inputs .\inputs --output .\CONTINUACAO_AUDITORIA.json
Pop-Location
```

O resultado esperado com este snapshot é código 2 e nenhum lucro calculado.
As dependências de desenvolvimento usadas na sessão foram preservadas em
work/runtime, work/checks e work/lint; não criar venv. Não repetir testes caros
sem mudança/preocupação concreta, nem reexecutar famílias antigas para escolher
o melhor retorno. Nenhuma automação ou operação financeira foi criada para continuar
trabalhando após o encerramento: a retomada ocorre no novo chat do usuário.
