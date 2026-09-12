# Exportação ResearchBundleV1 — candidato local

Estado corrente 12/09/2026: remediação local, perfil `local-research/2`.
Origem/restrições são do produtor. `exporter_revision` identifica a evidence
`exporter-provenance/1`, com hashes dos bytes efetivos do exportador, seletor,
módulos usados pela seleção e contratos compartilhados, versões e Python.
CAIN exige aprovação administrativa do pacote exato antes da importação.
O modo padrão lê apenas o recibo; o modo opcional executa DatasetSelection para
esta exportação sobre cópia verificada, sem simulação ou transferência de preços.
Recibos abaixo são históricos; nova evidência fica em
`C:/STOCKS/work/bundle-remediation-20260912-real`. Sem push, release, venv ou
instalação de Core/runtime neste Windows. Fontes e recibos R8 são preservados.

Este incremento é aditivo ao exportador ResearchSnapshotV1, que permanece intacto.
O produtor usa somente o pacote independente predictor-research-bundle 1.0.0 do Ecosystem;
não importa CAIN nem executa o runtime científico. Instale o wheel compartilhado em ambiente
auxiliar separado. Não instale o runtime de produção para usar estas ferramentas.

Fontes têm allowlist fixa, SHA256 explícito, limite de 100 KB e precisam estar commitadas.
O exportador verifica novamente os hashes antes de criar saída. O destino é novo, fora do
checkout e dentro da raiz do produtor. Manifest é escrito por último; não há sobrescrita.
O horário --exported-at é explícito para permitir repetição determinística e nunca preenche
os clocks científicos ausentes. Cada entity tem status, eixo, payload, clocks e proveniência.

Entrada: `python tools/export_cain_bundle.py --root ROOT --expected-sha SHA --destination DESTINO_NOVO --exported-at ISO_OFFSET`.
Fonte única: docs/engineering/2026-09-11-architecture/evidence/real-v020.json.
Exporta o recibo existente como measurement e suas versões exatas de catálogo como datasets.
Conserva source_id, hash do arquivo, hash das linhas, versão, publisher, período e contagens.
O observed_at do catálogo vira recorded_at; available_at permanece null porque disponibilidade
pública histórica não foi certificada. Isso é uma âncora de versão real, não um recibo inventado
de execução DatasetSelection. O contrato DatasetSelection existente não é substituído por latest.
Fonte B3 e recibo bruto são reference_only, com licença UNKNOWN e sem auto-fetch/materialização.
Os metadados preservados não concedem direito de redistribuir documentos ou preços.
No modo padrão nenhum banco ou módulo de domínio é aberto/importado. No modo opcional,
somente os adaptadores stdlib necessários à seleção são usados; não há simulação. Os recibos R8
históricos e seus hashes foram preservados; este incremento está em tools, fora do runtime.

Testes: `python tools/test_export_cain_bundle.py`. E2E em
C:/STOCKS/bundle-v1-final-e2e; logs em C:/STOCKS/work/bundle-installed-tests.log.
Mantida a restrição local: sem criação de venv ou instalação do runtime Stocks neste Windows.

Validação: 9 testes específicos com fixtures fictícias e fontes commitadas: determinismo,
UNKNOWN/null, leitura sem alteração, fonte inesperada/ausente/alterada, hash incorreto,
destino existente/checkout, entrada malformada e credencial fictícia. Wheels e E2E foram
exercitados separadamente; isso não é validação científica ou econômica.

Nenhum push, release, instalação operacional, modelo, hipótese, trial, holdout, ledger ou
banco científico foi executado/alterado. Rollback desativa esta ferramenta opcional e mantém
as publicações/bundles existentes. Não apagar evidências para retornar ao caminho SnapshotV1.

Na retomada, a identidade calculada da measurement é explicitamente content_hash;
a identidade source_id continua source_assigned. O bundle real em
C:/STOCKS/bundle-v1-completion-e2e foi reimportado e restaurado offline. A fonte
pinada permaneceu inalterada. Nenhuma seleção foi inventada a partir do catálogo.

## Seleção real de exportação

O modo opcional --backup-sha/--source-id/--observed-before/--session-date usa o
DatasetSelection existente. O único backup admitido é
work/architecture-20260911/real-v020/backup/snapshot.sqlite, relativo a C:/STOCKS.
Exige SHA256, até quatro source_ids explícitos, exatamente uma sessão e no máximo
500 linhas. Copia bytes verificados para scratch, valida o schema conhecido antes
da consulta e materializa somente para obter o recibo; não chama simulação.
Tuplas do recibo são representadas por arrays JSON, sem alterar o hash do domínio.

Execução: 312 linhas de 2026-09-09, observed_before=2026-09-11T00:00:00Z;
selection_sha256=7550c20348e9bb7666271b9396d583247de9770a1e7cfb82a508e7629a2d9449.
O backup ficou com SHA256 f498ba3ec9a00e8d1cf5b37a47ad16665d09b00401551fa24383715f053e258c.
É seleção desta exportação, não prova de input usado por experimento histórico.
Preços não são transferidos; licença UNKNOWN. Snapshot e bancos originais preservados.

Bundle final: C:/STOCKS/bundle-v1-selection-final-e2e. Três entidades/seis relações,
três referências. 9 testes do exportador e 5 do seletor aprovados, incluindo cutoff,
hash errado, seleção vazia/ampla, journal não fechado e preservação determinística.
