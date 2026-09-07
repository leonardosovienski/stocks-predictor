# H17: registro anterior à primeira observação

Esta rodada é `DISCOVERY`, família H17, e mantém a direção de accruals baixos.
O usuário autorizou concluir o necessário para testar na cópia isolada. Seu
pedido original permite protótipos baratos com governança proporcional e não
autoriza gastos ou capital. A autorização cobre esta primeira observação
exploratória; não reabre as famílias encerradas nem transforma o histórico já
usado em holdout.

O protocolo JSON adjacente define o diagnóstico, limitações e parada antes do
primeiro cálculo de IC ou diferença entre quintil e universo. Seu hash semântico
é `a35f166a0a9ae8d38e6fe13b21ac77e63629673ae66a20f8820123c062c9072b`.
A contagem nominal passa de 15 para pelo menos 16 candidatos observados quando
a execução ocorrer. O denominador adaptativo completo continua desconhecido.

Preparo anterior à observação: 96 snapshots mensais, 181 emissores, 195 códigos,
387.101 cotações selecionadas sem alteração de preço e o mesmo calendário de
2.647 pregões da origem. Base de cotações extraída:
`30ce8e91fba9cb0a0c09571be71821c9da2d0aec49d12ec15aab8b26522ffd2c`.
O ISIN foi recuperado dos arquivos originais COTAHIST, ordenando por data antes
de comprimir intervalos, pois os arquivos anuais não estão sempre ordenados.

Eventos: 194 registros B3 ligados ao ISIN histórico, mais 48 mudanças de base
obtidas na fonte secundária Yahoo; 81 coincidências e duas diferenças pequenas
de arredondamento nos cruzamentos. Fonte secundária indisponível para 41 códigos
históricos: eles permanecem no universo e suas lacunas são registradas. A B3
atual omite parte das bonificações antigas. Não existe certificado de cobertura
completa; nem ausência de saltos nem resposta vazia significa ausência de evento.

O desenho original aceita retorno só-preço como primeira passada na H1 (§M2).
Esta aplicação à H17 é uma revisão metodológica explícita de Discovery, não
execução confirmatória do lacre antigo. O viés relativo da omissão de dividendos
para accruals é desconhecido. Bonificações são ajustes teóricos de base desde o
ex, sem alegar disponibilidade para negociação. Não há P&L executável, DSR,
PBO ou projeção de lucro a partir deste diagnóstico.

Os runners formais H17/H18/H19 e seus lacres permanecem protegidos. Após este
diagnóstico, entretanto, H17 deixa de ser um output nunca visto: qualquer novo
resultado da família deve carregar esta exposição. H18/H19 continuam não vistas.

Fontes de especificação: [layout COTAHIST B3](https://www.b3.com.br/data/files/33/67/B9/50/D84057102C784E47AC094EA8/SeriesHistoricas_Layout.pdf)
e [fatores de proventos B3, página 18](https://www.b3.com.br/data/files/FB/83/0C/33/2D2109105391B9F8AC094EA8/OPCOES.pdf).
