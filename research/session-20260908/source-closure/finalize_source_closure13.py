"""Publish tested revision13 with explicit evidence limitations and provenance."""
import json
from pathlib import Path
import shutil
import subprocess
from source_utils import ROOT, OUT, read

CHAT=Path(r'C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2')
repo=ROOT/'work/stocks-predictor';archive=repo/'research/session-20260908/source-closure';outputs=CHAT/'outputs'
code=read(OUT/'code-validation-13.json');package=read(OUT/'package-validation-13.json')
a=read(OUT/'integrated-readiness-13.json');snap=read(OUT/'cash-closure-13.json')
assert subprocess.check_output(['git','status','--porcelain'],cwd=repo)==b''
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()==code['tested_commit']
assert '735 passed in 115.28s' in (OUT/'full-tests-13.log').read_text(encoding='utf-8')
assert '166 passed in 0.87s' in (OUT/'wheel-tests-13.log').read_text(encoding='utf-8')
assert (OUT/'integrated-readiness-13.json').read_bytes()==(OUT/'portable-reproduced-13.json').read_bytes()
missing_original={r.get('parent_event_id',r['event_id']) for r in snap['cash_events'] if r['net_per_share'] is None}
assert len(missing_original)==52
validation=dict(tested_commit=code['tested_commit'],python='global3.13',
    full_suite=dict(passed=735,seconds=115.28,warnings=0),
    wheel_suite=dict(passed=166,seconds=.87,installed=False,checkout_on_import_path=False),
    ruff='PASSED',pyright='0 errors, 0 warnings',source_validation=read(OUT/'source-validation-13.json'),
    portable_package=package,source_manifest_sha256=a['source_manifest_sha256'],
    source_protocol_sha256=snap['source_protocol_sha256'],source_revision=snap['counts'],
    original_records_without_net=len(missing_original),profit=None,future_profit_projection=None,
    new_historical_return_evaluations=0,administrative_counts=[53,55],
    economic_status=a['status'],scientific_independence=False,
    real_orders=0,paid_services=0,new_runtime_dependencies=0)
hypera_url=next(s['url'] for s in snap['duplicate_lineage'][0]['issuer_sources']
               if s['file'].endswith('issuer-13-cvm-1456495.pdf'))
report=f'''# Stocks Predictor — revisão 13 validada

Foram corrigidas novas falhas de busca e de duplicidade, e incorporadas 12 datas de pagamento. **Ainda não há evidência suficiente para comprovar lucro ou afirmar que todas as pendências foram resolvidas.**

| Verificação | Revisão 12 | Revisão 13 |
|---|---:|---:|
| Registros brutos preservados | 778 | 778 |
| Direitos distintos após revisão de duplicidade | não conciliado | 777 |
| Linhas de pagamento para execução | 801 | 800 |
| Linhas sem data de pagamento | 37 | 24 |
| Linhas sem valor líquido | 66 | 54 |
| Registros originais sem valor líquido | 64 | 52 |
| Eventos societários integrados / pendentes | 8 / 28 | 8 / 28 |
| Intervalos com inventário integral certificado | 0 de 1.248 | 0 de 1.248 |

A redução de 13 linhas sem data resulta de **12 datas preenchidas e uma duplicata conciliada**. A linha duplicada continua na fonte original e na trilha de auditoria; ela deixou de gerar um segundo recebível. As contagens de pendências se sobrepõem e não devem ser somadas.

## Correções executadas

- A busca inclui a categoria Relatório Proventos e avisos aos acionistas sem assunto. A janela começa na aprovação, antes da data “ex”. Foram preservados 174 documentos candidatos, incluindo suas versões.
- O filtro temporal verifica a data de envio à CVM. Uma retificação de 2025 que mantém a referência do evento de 2024 não aparece numa consulta limitada a 2024. Um teste com documentos reais capturou e corrigiu essa falha.
- Duas linhas B3 idênticas do JCP Hypera aprovado em 29/01/2024 foram vinculadas a uma única distribuição de R$ 0,09725 por ação. A versão 3 e o aviso de dezembro da companhia fixam 17/12/2025. A execução conserva somente um pagamento, com referência aos dois registros originais. [Relatório original da companhia na CVM]({hypera_url}).
- Não há deduplicação automática por valor ou aparência. As três parcelas Iguatemi de 2019 permanecem separadas, com datas confirmadas no balanço da companhia.
- Foram conciliados pagamentos de Iguatemi, Totvs, Raia, Hapvida, GNDI, Renner, Yduqs, Localiza, Hypera e Porto. Os valores brutos originais foram preservados. Em Localiza, a data fixa do aviso inicial foi combinada com a correção explícita do valor; o aviso posterior de novembro ainda não foi recuperado, e isso permanece registrado.
- O crédito B3 de Porto em 10/04/2026 usa a data de corte no campo apresentado como aprovação. O relatório da companhia permitiu conferir separadamente a aprovação e identificar o pagamento. O líquido continua pendente por divergência documental. [Boletim B3 de 10/04/2026](https://arquivos.b3.com.br/bdi/download/bdi/2026-04-10/BDI_04-1_20260410.pdf).
- Quatorze datas de formulários ficaram registradas como candidatas sem preencher o pagamento: prazo máximo e cronograma agregado superado não demonstram caixa recebido.
- Um ITR Hapvida truncado foi rejeitado como prova. O prospecto integral confirma o pagamento GNDI. A extração de texto de um PDF parcial não o torna completo. Os relatórios CVM com bytes NUL após um EOF válido foram preservados sem alteração.

As confirmações retrospectivas verificam o fluxo de caixa; não tornam o conteúdo de balanços futuros conhecido na data original do sinal. O campo de reconhecimento foi mantido conservador, no pagamento. Não houve novo teste de retorno nem alteração da seleção ou dos parâmetros.

## Limites que continuam reais

Restam **24 datas, 54 líquidos e 28 entradas societárias**, além do inventário integral ainda sem certificação nos 1.248 intervalos. Há documentos que não foram recuperados, prazos máximos sem confirmação de pagamento, conflitos de líquido, capital devolvido dependente de base fiscal, frações e entrega de ações sucessoras. SLC 2019 ainda exige conciliação das unidades no desdobramento. Duas atualizações monetárias BR Distribuidora de 2020 continuam registradas como lacuna do inventário congelado.

Correção do relatório anterior: **as cotações terminam em 01/04/2026; a lista de pregões observados vai até 27/08/2026**. São coberturas diferentes. Nenhuma sessão foi presumida para completar pagamentos posteriores. O sinal de 29/03/2018 continua sem cobertura suficiente de características.

Também permanecem a conferência de arredondamento do caixa na corretora e a revisão H20 vinculada às fontes finais. Os testes passaram, mas isso não demonstra rentabilidade. **Lucro histórico líquido e projeção futura continuam desconhecidos, com estado BLOCKED_MISSING_EVIDENCE.** Não há holdout intacto. O protocolo atual permite reconstruir fontes; uma nova avaliação de retorno exige evidência adequada e pré-inscrição separada vinculada ao hash final.

Foram preservados H1–H20 e as contagens administrativas 53/55. Zero novas avaliações históricas de retorno, ordens, instalações, serviços pagos, agentes adicionais ou escritas em bancos, ledgers e quarentenas protegidos.

## Validação e reprodução

- **735 testes passaram**, sem avisos, em 115,28 s, com Python global 3.13.
- **166 testes passaram na wheel fora do checkout**, em 0,87 s, sem instalação. Seus {package['wheel_modules_matched_to_checkout']} módulos correspondem aos arquivos do código testado.
- Ruff e Pyright passaram. A auditoria da revisão 12 permanece idêntica com o código atualizado.
- Onze adulterações foram rejeitadas, incluindo reinserção da duplicata, remoção da prova, troca da linha B3, retirada das referências originais, alteração de bruto e liberação indevida de inventário.
- O pacote verificou {package['payloads_verified']} arquivos e reproduziu a auditoria **byte a byte** com Python isolado, sem rede. A análise foi feita pelo mesmo agente; não é revisão científica independente.

Código testado: `{code['tested_commit']}`.

Manifesto das fontes: `{a['source_manifest_sha256']}`.

SHA256 da auditoria: `{package['audit_sha256']}`.

SHA256 do ZIP: `{package['zip_sha256']}`.

Após extrair `AUDITORIA_STOCKS_REPRODUZIVEL_13.zip`, execute:

    py -3.13 -I REPRODUZIR_FONTES.py --output auditoria-reproduzida.json

Saída 0 significa reprodução correta da auditoria, não lucro comprovado. O pacote preserva fontes usadas, baseline, revisões e tentativas de aquisição. O diretório investigation-candidates inclui documentos substituídos e downloads rejeitados, explicitamente separados dos dados usados em inputs/.

`PENDENCIAS_STOCKS.json`, `PRONTIDAO_FONTES_13.json` e `VALIDACAO_FONTES_13.json` registram os eventos, bloqueios, fontes e resultados verificáveis.
'''
for p in [outputs/'REVISAO_FONTES_STOCKS.md',outputs/'REVISAO_FONTES_STOCKS_13.md',
          archive/'RESULTADO_FONTES_13.md',repo/'docs/research/2026-09-08-source-closure-results.md']:
    p.write_text(report,encoding='utf-8',newline='\n')
for directory in [outputs,archive]:
    (directory/'VALIDACAO_FONTES_13.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
for name in ['PENDENCIAS_STOCKS.json','PRONTIDAO_FONTES_13.json']:
    shutil.copyfile(archive/name,outputs/name)
for pattern in ['*13*.log']:
    for p in OUT.glob(pattern):shutil.copyfile(p,archive/p.name)
for name in ['code-validation-13.json','package-validation-13.json']:
    shutil.copyfile(OUT/name,archive/name)
for name in ['test_source_closure13.py','package_source_closure13.py','finalize_source_closure13.py']:
    shutil.copyfile(CHAT/'work'/name,archive/name)
for name in ['HANDOFF.md','STOCKS_CURRENT_STATE.md','docs/continuation/UPDATE_20260908.md']:
    p=repo/name;t=p.read_text(encoding='utf-8')
    t=t.replace('11 adulterações rejeitadas. Suíte completa e wheel serão registradas após\no commit de código; não confundir essa validação de fontes com lucro.',
        f'11 adulterações rejeitadas. Código {code["tested_commit"][:7]}: 735 testes completos\ne 166 testes na wheel extraída, sem instalação; Ruff/Pyright verdes. Pacote\nde {package["payloads_verified"]} arquivos reproduz a auditoria byte a byte. Resultados em\ndocs/research/2026-09-08-source-closure-results.md. Não confundir fontes com lucro.')
    p.write_text(t,encoding='utf-8',newline='\n')
print(json.dumps({'tested_commit':code['tested_commit'],'full_tests':735,'wheel_tests':166,
    'economic_status':a['status'],'remaining_dates':24,'remaining_net':54,'original_without_net':52,**package}))
