# Reprodução R5/H22

[Relatório e 24 avaliações](../../../docs/research/2026-09-10-r5/README.md).
Protocolo publicado antes de medir; código e recibos vinculados no relatório.
Uma rodada, não pesquisa de parâmetros. Execução local sem Core ou dependências
novas; nenhuma ordem, automação, instalação ou modificação de banco.

Arquivos locais em `C:\STOCKS\work\profit-validation-r5-20260910`:

- `raw/`: seis capturas bem-sucedidas e oito recibos, incluindo dois HTTP403;
- `text/` e PNGs: extração e conferência das páginas de PDF;
- `inputs.json`: 2.405 preços e calendário, hashes dos ZIPs; preços originais preservados;
- `attempt01.jsonl`: primeiro resultado completo, início/fim e todas as curvas;
- `prepare-attempt02.log`: preparação corrigida, sem resultados econômicos.

Os arquivos volumosos e fontes integrais ficam localmente. O GitHub contém código,
identidades, resultados resumidos, livros de ordens/impostos e o relato completo.
Não se deve confundir clone do repositório com backup dos ZIPs/fontes.

No checkout limpo, com o Python já fornecido pelo Codex:

```powershell
$researchPython = 'C:\Users\leona\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Set-Location -LiteralPath 'C:\STOCKS\stocks-predictor'
& $researchPython -B -m unittest discover -s tests -p test_monthly_etf.py -v
& $researchPython -B research/session-20260910/profit_validation/run.py C:\STOCKS\work\profit-validation-r5-20260910 C:\STOCKS\work\profit-validation-r5-20260910\reproduction-new.jsonl
```

O destino deve ser novo: os runners recusam sobrescrever resultados. Não usar
`-O`, que desativa assertions; o verificador rejeita esse modo. O runner recusa
árvore Git suja, alteração dos bytes do protocolo e hash de inputs divergente.
Registra todos os erros, termina a matriz e retorna falha se qualquer avaliação
falhar. Inviabilidade de orçamento declarada é um resultado esperado, sem lucro.
Reprodução idêntica confirma mecânica; não é evidência econômica independente.

`prepare.py` reconcilia preços com os ZIPs existentes e cria inputs apenas se não
existirem. Não refazer downloads por rotina: os URLs podem entregar revisões
posteriores. `acquire.py` é uma aquisição pública finita de oito URLs; não executar
no diretório já preenchido. Catálogos anteriores e fontes de 2018–2026 são requisitos
de reprodução, não rebaixados a dados opcionais para fazer o teste passar.

Falhas pré-medição preservadas no relato: filtro BDI14 incorreto para 92 datas de
2019 e truncamento de centavos na primeira versão do verificador ao receber float
artificialmente adulterado. Ambos foram detectados e corrigidos antes da primeira
medição econômica. Nenhuma fonte histórica ou resultado negativo foi descartado.
