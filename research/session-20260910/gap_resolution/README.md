# R6 — recuperação, correções de fontes e reprodução

Raiz Windows: `C:\STOCKS`; checkout `C:\STOCKS\stocks-predictor`.
Usar o Python auxiliar fornecido pelo Codex (3.12.14, stdlib para recuperação e
replay; `pypdf` já fornecido para exame documental). Produção e suíte: CI 3.13/3.14.
Nenhum comando instala dependências ou envia ordens.

Verificar os recibos publicados, inclusive os cinco objetos originais:

```powershell
python research/session-20260910/gap_resolution/verify.py
```

Verificar integralmente o pacote restaurado com seu programa original:

```powershell
python C:/STOCKS/work/gap-resolution-r6-20260910/h20-complete-package/rodar_validacao.py --verify-only --output-dir C:/STOCKS/work/unused-verification-output
```

Reprodução portátil completa, com código congelado e tolerância R3, sem depender
de uma execução anterior ou dos caminhos da máquina original:

```powershell
python research/session-20260910/gap_resolution/replay_complete.py --package C:/STOCKS/work/gap-resolution-r6-20260910/h20-complete-package --output-dir C:/STOCKS/work/novo-replay-h20
```

O comando verifica o hash do próprio manifesto original antes de ler seus arquivos,
recusa saída existente ou dentro do pacote e grava a comparação em uma pasta nova.
Execução completa e os três controles de recusa foram verificados em Python
3.12.14; o recibo está no manifesto R6. O auxiliar usa somente a biblioteca padrão
e o código congelado do pacote.

Comandos que produziram a rodada, na ordem de dependência:

1. `recover_h20.py` procura blobs Git e variantes uniformes; recebe uma pasta nova.
2. `recover_archives.py` reproduz os dois comandos `git archive` registrados.
3. `recover_mixed_text.py` conserva a tentativa sem resultado sobre revisões.
4. `recover_newline_runs.py` resolve os dois arquivos com finais de linha mistos.
5. `restore_package.py` combina objetos do acervo e recuperações, confere o manifesto
   original e executa o verificador original. Exige `C:/STOCKS/DADOS_STOCKS.zip`.
6. `rodar_validacao.py` sem `--verify-only` reproduz as coortes, mas o comparador
   numérico estrito falha em uma diferença de 2,22e-16 no Windows auxiliar.
7. `replay_complete.py` usa o código congelado recuperado e a tolerância R3 já
   declarada. Sua versão portátil reproduz também a base numa pasta nova. Não muda o
   verificador original e não acrescenta evidência econômica independente.
8. `acquire.py PLAN OUTPUT` captura os planos JSON registrados. Cada captura tem
   recibo próprio, incluindo falhas. `refresh_quotes.py` verifica sobreposição e
   calendário sem recalcular R5.
9. `review_cash.py` expõe páginas das fontes dos 52 eventos sem líquido; revisão
   humana independente não foi realizada. As páginas materiais foram examinadas
   pelo mesmo assistente em texto e imagens.
10. `build_source15.py` verifica e copia a revisão 14, incorpora dois créditos
    documentados e executa a auditoria canônica. A nova revisão não substitui os
    bytes das revisões anteriores nem certifica disponibilidade histórica.
11. `publish_evidence.py` publica o conjunto inicial de recibos e objetos autorais.
    Os recibos adicionais de coleta, CI, preservação e replay portátil foram
    incorporados ao manifesto por comandos registrados na execução e commits R6.

As ferramentas recusam saídas existentes quando criam uma rodada completa. Para
repetir, selecionar novos destinos nos scripts fixos antes da execução e registrar
essa variante; nunca apagar/sobrescrever a rodada anterior. O pacote restaurado
completo permanece local; os cinco objetos ausentes estão também em `exact_objects/`.

Relatório canônico: [R6](../../../docs/research/2026-09-10-r6/README.md).
