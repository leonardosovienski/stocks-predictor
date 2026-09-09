# Recuperação dos bancos e auditoria de fontes R2

Estado: [relatório](../../../docs/research/2026-09-09-data-completion-r2.md) e
[catálogo versionado](../../../docs/research/2026-09-09-data-readiness.json).
A recuperação já foi executada em `C:\STOCKS\data\recovery-r2`.
Não repetir por padrão nem substituir o destino existente.

`tools/data_bank.py` usa somente stdlib e aceita Python 3.12 ou posterior.
Não importa Core, calcula retorno, migra banco ou instala dependências.
O catálogo associa nomes originais a objetos por SHA-256, preservando versões.
Os bancos são referências para leitura; o programa não escolhe nem ativa
automaticamente um banco de produção.

## Recuperar em um novo destino, quando necessário

No checkout `C:\STOCKS\stocks-predictor`, com espaço e orçamento disponíveis:

```powershell
$stocksPython = 'C:\Users\leona\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $stocksPython -B tools/data_bank.py C:\STOCKS\DADOS_STOCKS.zip C:\STOCKS\data\recovery-new `
  --archive-sha256 83d5aac8e23d72e4deb1331077e08313914375a5dbac4276e5f8ad89da586d23 `
  --bundle source13=unpacked-archives/session/outputs/AUDITORIA_STOCKS_REPRODUZIVEL_13.zip.contents `
  --bundle source14=unpacked-archives/session/outputs/COMPLEMENTO_FONTES_14.zip.contents
```

O comando verifica o arquivo completo antes de escrever; valida nomes, tamanho,
SHA-256 e CRC de cada objeto recuperado. Recusa destino existente, links no caminho
e restauração que ultrapasse 6 GB ou a reserva de espaço livre. Falhas preservam
arquivos parciais para diagnóstico; não reutilizar silenciosamente esse destino.
Journal transacional não vazio recebe estado pendente, não atestado de integridade.

O arquivo de migração separa código e dados. Os 1.459 arquivos do conjunto 13 não
incluem os scripts/wheels removidos na exportação; o código fica neste repositório.
O conjunto 14 tem nove arquivos. Para compor uma revisão 14 em destino novo, copiar
`bundles/source13/inputs` para `source14-inputs`, aplicar sobre **essa cópia** os três
arquivos de `bundles/source14/replacement-inputs` e copiar os dois documentos de
`bundles/source14/reviewed-primary` para `source14-inputs/primary`.
Conferir o manifesto final antes de auditar. Essa composição já existe no destino R2.

## Reproduzir a auditoria, sem retorno histórico

O comando abaixo deve usar nome de saída ainda inexistente dentro de `C:\STOCKS\work`:

```powershell
& $stocksPython -B -I research/session-20260909/data_completion/audit_recovered.py `
  C:\STOCKS\data\recovery-r2 C:\STOCKS\work\source-audits-new.json
```

O script confere os manifestos 13 (`7c24e093…`) e 14 (`3b36e241…`), exige igualdade
exata do resultado 13 com a auditoria original e registra zero novas valorizações.
A saída mantém `production_environment_certificate=false`. Não é nova hipótese,
nem reprodução econômica independente. O resultado executado está em
`C:\STOCKS\work\data-completion-r2-20260909\reproduced-source-audits.json`.

Nove testes sintéticos do recuperador:

```powershell
$env:TEMP = 'C:\STOCKS\work\data-completion-r2-20260909'
$env:TMP = $env:TEMP
& $stocksPython -B -m unittest tests.test_data_bank -v
```

Não executar ingestões legadas sobre os bancos recuperados. Não transformar hash
correto ou SQLite íntegro em cobertura econômica completa. Para produção, usar
os checks Linux da CI; nenhuma instalação Windows faz parte desta reprodução.

## Fontes públicas e normalização

O diretório local `C:\STOCKS\work\data-completion-r2-20260909` preserva `acquire.py`,
12 lotes, `acquisition.jsonl`, metadados por resposta, PDFs/HTML/JSON brutos,
extrações de texto e páginas usadas na verificação visual.
`normalize_readiness.py` produziu `normalized-v1`, com inventário de fontes,
entradas operacionais, revisão de eventos, prontidão e hashes. Ele depende dos
artefatos R1/R2 desse computador e do pypdf já fornecido pelo ambiente; não é
um coletor de produção nem um comando para executar automaticamente em outro host.
Snapshots anteriores e tentativas malsucedidas permanecem separados.
