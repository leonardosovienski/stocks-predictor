import datetime as dt
import json
from pathlib import Path

root = Path(r'C:\STOCKS')
repo = root / 'stocks-predictor'
work = root / 'work/data-completion-r2-20260909'
now = dt.datetime.now(dt.timezone.utc).isoformat()

def write(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

path = repo / 'docs/continuation/LOCAL_PATHS_20260909.json'
value = json.loads(path.read_text(encoding='utf-8'))
value['restored_scope'] = ('Nine original COTAHIST ZIPs retained; R2 recovered all 12 unique databases '
                          'mapped from 37 archived paths and separate source13/source14 bundles. '
                          'The entire 60023-path archive tree was not materialized.')
value['historical_sources'] = ('PATHS.json remains historical. Source13 manifest 7c24e093f7a148c3f375fff9fbd23db62f049ba8012e49e6ba7b4413e27a372b '
                             'was reproduced exactly; source14 manifest 3b36e2416e44f2b0a30e88d4306e00cdc74a7302c6e9b0e33950a893ea169bda '
                             'is materialized separately and does not silently replace source13. No new economic evaluation.')
value.update(data_catalog=str(root/'data/CATALOG.json'),
             recovered_databases_and_sources=str(root/'data/recovery-r2'),
             recovered_object_catalog=str(root/'data/recovery-r2/catalog.json'),
             source_round_r2=str(work),
             source_round_r2_report='docs/research/2026-09-09-data-completion-r2.md',
             source_round_r2_receipt=str(root/'outputs/ENTREGA_DADOS_FONTES_R2_20260909.json'),
             all_economic_data_ready=False, updated_at_utc=now)
write(path, value)

path = root/'LOCALIZACAO_PROJETO.json'
value = json.loads(path.read_text(encoding='utf-8'))
value['original_data_restoration_state'] = ('Archive and nine quote ZIPs preserved; R2 recovered 12 unique '
    'databases (37 original aliases) and separate source13/source14 evidence. Full path tree not materialized.')
value.update(data_catalog=str(root/'data/CATALOG.json'),
             recovered_data=str(root/'data/recovery-r2'),
             source_review_r2_work=str(work),
             source_review_r2_receipt=str(root/'outputs/ENTREGA_DADOS_FONTES_R2_20260909.json'),
             source_review_r2_report=str(repo/'docs/research/2026-09-09-data-completion-r2.md'),
             data_state_updated_at_utc=now)
# Existing code/main and full-scan fields are timestamped historical observations;
# refresh actual integrated code state only after the reviewed merge.
write(path, value)
print('Current local maps updated; historical full-scan observations retained.')
