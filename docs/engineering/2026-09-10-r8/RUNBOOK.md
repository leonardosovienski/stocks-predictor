# Operação de pesquisa em lote

Instalar o wheel e dependências travadas em Linux/Python 3.13 ou 3.14 conforme a
CI. Não instalar o runtime de produção neste Windows. A entrada instalada é
`python -m stocks_predictor`; no checkout, `python main.py ops` usa a mesma entrada.
`doctor --check` verifica os metadados do runtime; `inspect` verifica o banco.

## Criar, carregar e conferir

Exemplo Linux, com diretórios explícitos já criados pelo operador:

```bash
python -m stocks_predictor doctor --check
python -m stocks_predictor init --db /dados/pesquisa/research.sqlite
python -m stocks_predictor ingest --db /dados/pesquisa/research.sqlite \
  --archive /fontes/COTAHIST_A2026.ZIP --scratch-dir /dados/temporarios \
  --publisher B3 --dataset COTAHIST_A2026 --version observed-20260910T152027Z \
  --source-url https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A2026.ZIP \
  --observed-at 2026-09-10T15:20:27.036342+00:00 \
  --sha256 34b774681cbd201ef197fb98af8d431e4d7302e801f58b66e54036d2935dc4f4
python -m stocks_predictor inspect --db /dados/pesquisa/research.sqlite
```

O hash acima identifica exclusivamente a aquisição R6 preservada, não qualquer
download posterior com o mesmo nome. Guardar fonte e recibo de aquisição. O hash
é conferido sobre o snapshot realmente lido pelo parser. Mudança de conteúdo sob
a mesma versão é erro; uma nova versão deve ser declarada e permanece separada.
Por padrão entram apenas BDI02/mercado010; `--all-markets` é outra política explícita.
Não há combinação automática de versões, ajuste de eventos nem certificado PIT.

`init` recusa arquivo existente. Bancos geridos usam application_id STKP,
schema v1, WAL, synchronous FULL, chaves estrangeiras e bloqueios de atualização/
exclusão. Comandos legados recusam esse application_id antes de migrar ou ler.
Esses bloqueios protegem o uso normal; o dono do arquivo pode alterar SQL/arquivos.

## Concorrência e capacidade

SQLite admite um escritor por vez. `ingest --timeout 5` espera até cinco segundos
para adquirir o lock; não é um limite para o tempo total da carga. Cópia, hash,
parse e commit fazem parte da operação do escritor. Leitores observam uma versão
consistente, anterior ou posterior ao commit. Não fazer ingestões longas paralelas
por padrão. Usar fila externa/manual, ou timeout explícito até 3600 segundos.

Saída normal é JSON em stdout. Erros operacionais retornam código 2 e JSON em
stderr; `retryable_lock=true` identifica contenção. Repetir com a mesma fonte e
versão é idempotente depois de resolver contenção. CLI inválida também retorna 2;
`doctor --check` retorna 1 se o ambiente não atende ao contrato.

250 mil registros sintéticos e 55.986 cotações reais são cargas finitas medidas,
não limites universais. Manter espaço para ZIP temporário, banco, índices, WAL,
backup e restauração. O tamanho descomprimido depende da fonte; erro de disco deve
interromper a operação. Não usar WAL em compartilhamento de rede, múltiplos hosts
ou armazenamento com semântica de bloqueio/sincronização não comprovada.

## Backup e restauração

```bash
python -m stocks_predictor snapshot --db /dados/pesquisa/research.sqlite \
  --destination /backups/pesquisa-001 --timeout 60
python -m stocks_predictor restore --snapshot /backups/pesquisa-001 \
  --destination /dados/restauracao-001
python -m stocks_predictor inspect --db /dados/restauracao-001/research.sqlite
```

Ambos os destinos devem ser novos. Backup usa a API SQLite, incluindo commits
presentes no WAL. Não copiar somente o arquivo `.sqlite` de um banco aberto.
Manifesto contém SHA-256, schema, fontes, contagens e hashes de linhas. Restauração
confere os bytes copiados e o conteúdo lógico antes de publicar o arquivo final.

`INCOMPLETE.json` significa falha/interrupção; não remover o marcador para forçar
aceitação. Preservar o diretório para diagnóstico e repetir em outro destino novo.
O leitor recusa diretórios incompletos. Nunca substituir o banco ativo por esse
comando. Depois de conferir a restauração, o operador pode apontar sua próxima
operação para o caminho restaurado explicitamente. Reverter código não altera
fontes, e fontes novas não devem ser apagadas para simular rollback.

RPO é o último snapshot concluído; agendamento e cópia externa não estão ativos.
RTO depende do volume e disco: o recibo registra os tempos medidos. Perda de host
exige cópia em outro meio, ainda não provisionada neste projeto local. Os testes
cobrem morte de processo e erro simulado de armazenamento, não certificam hardware,
energia, retenção externa ou restauração de um host perdido.

## Entradas econômicas e observações

`profile --input perfil.json` recebe capital/custos/prazo explícitos, mantendo
ausências como desconhecidas. Usar números decimais como strings para valores
monetários. O cenário confirmado é `{"capital_brl":"5000"}`.
`evidence --input resultados.json --asof <ISO-com-fuso>` recebe a lista de
`observation_id`, `decision_at`, `matured_at`, `observed_at`, `gross_edge`.
Recusa duplicação, cronologia inválida e observação no corte ou depois dele.
Não certifica independência, veracidade das datas, lucro nem habilita capital.

## Reproduzir os checks

CI executa suíte integral e histórica, lint, tipos, cobertura, dois builds iguais
e `tools/operational_validation.py --installed --output <novo> --rows 250000`
sobre o wheel instalado fora do checkout. Os testes de processo e recuperação
ficam em `tests/test_operational_store.py`. `tools/audit_registry.py` mantém código
R7 no commit c259ff64771a6c560ddb4aadac6bf81301c3066a e verifica os documentos
históricos no disco. `tools/verify_operational_evidence.py` verifica o código atual,
a identidade da fonte real e o ciclo completo de carga/replay/backup/restauração.

Referências: [backup SQLite](https://www.sqlite.org/backup.html),
[regras de WAL](https://www.sqlite.org/wal.html),
[Connection.backup](https://docs.python.org/3.13/library/sqlite3.html#sqlite3.Connection.backup).
