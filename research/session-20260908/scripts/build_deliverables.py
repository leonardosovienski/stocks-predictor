"""Package measured results and a bounded economic decision; no market ingestion."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

workspace = Path(__file__).resolve().parents[1]
work = workspace/'work'; outputs = workspace/'outputs'
repo = Path('C:/Users/Superleo13/stocks-predictor-work/.local-research/stocks-session-20260907/work/stocks-predictor')
archive = repo/'research/session-20260908'
stage = work/'reproduction-package'
for p in (outputs, archive/'deliverables', archive/'scripts', archive/'logs'):
    p.mkdir(parents=True, exist_ok=True)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(name, value):
    (outputs/name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


code_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
replay = read(work/'replay-after.json')
feasibility = read(work/'feasibility-final.json')
assert len(feasibility['entry_cases']) == 248
assert all(r['status'] == 'SIMULATED_ENTRY_ONLY' for r in feasibility['entry_cases'])
assert (stage/'work/feasibility.json').read_bytes() == (work/'feasibility-final.json').read_bytes()
assert (stage/'work/replay.json').read_bytes() == (work/'replay-before.json').read_bytes()
assert '69 passed' in (stage/'work/tests.log').read_text(encoding='utf-8')
assert '613 passed' in (work/'full-tests-final.log').read_text(encoding='utf-8')
db_expected = {
    'C:/Users/Superleo13/stocks-predictor-work/data/stocks.db':
        'a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4',
    str(repo.parent/'stocks-tested-real-v2-20260907.db'):
        'a8238568980d3303890b04590cfb5c55ab2d24c9271edd86820269336b09679a'}
assert all(sha(Path(p)) == h for p, h in db_expected.items())

decision = {
    'created_at_utc': datetime.now(timezone.utc).isoformat(), 'final_code_commit': code_commit,
    'economic_verdict': 'INCONCLUSIVE_NET_PROFIT', 'operational_decision': 'NO_GO',
    'research_allocation': 'PAUSE_MANUAL_BULK_H19_RECONSTRUCTION',
    'line_rejected_as_no_edge': False, 'net_profit_brl': None, 'loss_demonstrated': False,
    'chosen_path_executed': 'Bounded entry feasibility and position-dependent ordinary auction accounting',
    'capital_scenarios_brl': [5000, 10000], 'user_minimum_profit_unknown': True,
    'user_acceptable_maintenance_hours_unknown': True,
    'evidence': {'entry_snapshots_attempted_final': 248, 'entry_snapshots_completed_final': 248,
        'entry_dates_per_portfolio': 31, 'overhead_sensitivity_cells': 432,
        'economic_replay_status': replay['status'], 'payment_dates_missing': 356,
        'net_cash_amounts_missing': 389, 'certified_cash_intervals': 0, 'required_cash_intervals': 1237,
        'required_corporate_records': 36, 'approved_integrated_corporate_records': 0,
        'acquisition_spans_after_planning_merge_only': 312, 'ticker_isin_pairs_in_required_intervals': 123,
        'settlement_session_lags_in_entry_simulations': {'2': 216, '3': 32}},
    'implementation': {'ordinary_exchange_fraction_tax_from_position_basis': True,
        'separate_auction_withholding_and_monthly_gain_recognition': True,
        'already_net_corporate_constants_bound_to_full_book': True,
        'future_fixed_corporate_tax_rejected': True,
        'general_reorganization_tax_engine_complete': False,
        'actual_broker_rounding_and_fills_validated': False},
    'conditional_economics': {'assumed_incremental_maintenance_hours_per_month': 2,
        'assumed_hourly_opportunity_cost_brl': 25, 'annual_cost_brl': 600,
        'required_incremental_net_return_only_to_cover_that_cost': {'5000': 0.12, '10000': 0.06},
        'not_a_user_preference_or_alpha_forecast': True},
    'search_budget': {'minimum_exposed_return_configurations': 32, 'minimum_historical_return_evaluations': 37,
        'new_return_configurations': 0, 'new_historical_return_evaluations': 0,
        'new_feasibility_protocols': 1, 'completed_feasibility_editions': 2,
        'distinct_entry_snapshot_cases': 248, 'initial_edition_completed': 244,
        'source_resolved_entry_cases': 4, 'new_confirmatory_or_prospective_tranches': 0},
    'resume_condition': 'A concrete cheap source-closure route and maintenance economics compatible with the capital; unchanged frozen strategy or a separately registered material new equity mechanism. No automatic scheduling or capital.',
    'sources_and_databases_preserved': True, 'real_orders_submitted': False,
    'paid_services_purchased': False, 'runtime_dependencies_installed': False, 'github_push_performed': False}
save('STOCKS_CONTINUIDADE_DECISAO.json', decision)

validation = {
    'full_suite': {'snapshot_commit': '0ac04cb', 'passed': 613,
        **read(work/'full-tests-final-result.json'), 'log_sha256': sha(work/'full-tests-final.log')},
    'final_code_commit': code_commit,
    'final_compatibility_fix': 'bebe1f7 binds the review to the frozen plan ISIN; ordinary action requirements may omit ISIN.',
    'validation_after_final_fix': {'targeted_diagnostic_tests_passed': 3, 'external_packaged_tests_passed': 69,
        'package_test_log_sha256': sha(stage/'work/tests.log'), 'source_audit_passed': True,
        'three_old_unsafe_cases_rejected_by_final_runtime': True,
        'full_suite_not_repeated_for_final_two_line_identity_binding_fix': True},
    'static_checks': read(work/'static-check-results.json'), 'coverage_overall_percent': 79,
    'pyright_scope': 'Configured six modules: three RJ plus retail_cash, continuous_cash, continuous_research; unchanged after their successful check.',
    'real_replay_exit_code': 2, 'real_replay_byte_identical': True,
    'real_replay_sha256': sha(work/'replay-after.json'),
    'final_feasibility_byte_identical_outside_checkout': True,
    'final_feasibility_sha256': sha(work/'feasibility-final.json'),
    'initial_feasibility_sha256_preserved': sha(work/'feasibility-first.json'),
    'verified_replay_input_files': 31, 'validated_quote_records': 365198,
    'preservation_recheck': {'snapshot_manifest_sha256': sha(repo/'docs/continuation/PRESERVATION_MANIFEST.json'),
        'selected_preserved_files_reverified': 33, 'mismatches': 0,
        'scope': 'Inputs plus research database; not a fresh audit of all 36998 preserved files.'},
    'database_hashes_before_and_after': db_expected,
    'source_module_sha256': {n: sha(repo/'stocks_predictor'/n) for n in
        ['retail_cash.py', 'continuous_cash.py', 'continuous_research.py']},
    'new_historical_return_evaluations': 0, 'new_dependencies_installed': False}
save('STOCKS_CONTINUIDADE_VALIDACAO.json', validation)
sources = {'vivt_review': read(work/'vivt-source-audit.json'),
    'cyre_entry_unit_review': read(work/'entry-unit-review/review.json'),
    'current_tax_source_downloads': read(work/'current-tax-sources/sources.json'),
    'legal_browse_note': 'LC224 was read through the web tool on the official Planalto page; a separate local urllib archive attempt timed out. No rate was imputed into missing 2026 cash inputs.',
    'pdf_review_method': 'Existing primary PDF bytes checked against their acquisition SHA256; relevant terms read from the preserved extraction JSONs. No new PDF extraction or completeness certificate.',
    'new_corporate_actions_approved_for_full_replay': 0}
save('STOCKS_CONTINUIDADE_FONTES.json', sources)
shutil.copyfile(work/'feasibility-final.json', outputs/'STOCKS_CONTINUIDADE_RESULTADOS.json')

report = '''# Continuidade Stocks — resultado da execução

**A pesquisa ganhou contabilidade mais correta e uma medida concreta de viabilidade.
O lucro líquido da H19 continua desconhecido. A decisão operacional permanece não operar.**
Recomendo pausar a reconstrução manual extensa da H19 e só retomá-la com uma rota
barata de fechamento das fontes e manutenção compatível com R$5–10 mil.
Isso é uma decisão de alocação de esforço, não prova de que a H19 perde dinheiro.

## Trabalho executado

- Reproduzi o bloqueio original e conferi a preservação das entradas e dos bancos.
- Implementei ganho de leilão calculado com o custo fiscal da fração de cada posição,
  integrado à apuração mensal, compensação de perdas, retenção e datas de caixa.
- Corrigi três falhas reproduzidas na versão anterior: valores já líquidos e impostos
  fixos aceitos em outra carteira, e imposto futuro antecipado antes de ser conhecido.
- Executei compras inteiras nas 31 datas congeladas, em ambas as carteiras, com
  R$5 mil/R$10 mil e custos de 0,18%/0,36% por lado: **248 casos concluídos**.
- Calculei os 432 cenários registrados de manutenção, custos fixos, reconstrução
  futura e lucro desejado; arquivei as duas versões do diagnóstico e sua reprodução.

A primeira versão concluiu 244 compras e bloqueou quatro na entrada da Cyrela.
A fonte existente de 31/12/2025 confirmou uma bonificação em outra classe, sem
mudar o número de ON. A revisão de unidades, registrada separadamente, permitiu
concluir essas quatro compras sem dar direitos de bonificação ao livro vazio.
Um ajuste de compatibilidade também vinculou o ISIN ao plano congelado, pois o
cadastro de requisitos societários ordinários não repete esse campo.
Isso não aprova pagamentos, frações ou fiscalidade da Cyrela no replay contínuo.

## Compras iniciais: resultado medido

Medianas nas mesmas 31 datas, custo de **0,18% por lado**. Cada data começa com
caixa integral e nenhuma posição; não é uma simulação de riqueza acumulada.

| Capital | Carteira | Ações distintas compradas | Custo modelado da compra | Caixa após liquidação |
|---|---|---:|---:|---:|
| R$5.000 | H19 | 8 | R$8,92 | R$33,22 |
| R$5.000 | Comparação congelada | 40 | R$8,12 | R$481,29 |
| R$10.000 | H19 | 8 | R$17,92 | R$25,88 |
| R$10.000 | Comparação congelada | 40 | R$17,15 | R$452,58 |

As ordens usam quantidades inteiras definidas pelos fechamentos do sinal e preços
de abertura distintos para lote padrão e fracionário. O calendário fornecido
liquida 216 casos em dois pregões e 32 em três pregões; as obrigações foram
liquidadas sem empréstimo ou caixa negativo. O cenário de custo dobrado também
foi executado e está no JSON completo, sem selecionar uma variante vencedora.

Com R$5 mil, a comparação deixa cerca de 9,63% do capital em caixa na mediana,
contra 0,66% da H19. Logo, uma comparação futura precisa considerar a diferença
de exposição. A H19 concentra seis a nove nomes; a comparação tem de 33 a 46.
Nenhum desses números demonstra equivalência de risco ou vantagem de seleção.

As aberturas observadas não comprovam preenchimento, spread, prioridade da ordem
ou arredondamento por nota. **Giro efetivo contínuo, dividendos totais, imposto
histórico total, lucro líquido e retorno excedente ajustado ao risco seguem
desconhecidos.** Não extrapole estes custos iniciais para um retorno anual.

## Quanto esforço esse capital pode sustentar

Os valores abaixo são hipóteses de custo, não preferências suas nem previsões
de alpha. O retorno adicional necessário é depois de negociação e impostos,
antes dos custos desta tabela, em relação a uma alternativa comparável.
Adota-se custo administrativo zero para a alternativa; se não for zero,
é a diferença entre os custos das duas alternativas que deve ser usada.

| Cenário, sem reconstrução futura | Custo anual | Retorno adicional necessário sobre R$5 mil | Sobre R$10 mil |
|---|---:|---:|---:|
| 1 h/mês a R$25/h | R$300 | 6% | 3% |
| 2 h/mês a R$25/h | R$600 | 12% | 6% |
| 2 h/mês a R$25/h + R$120 fixos/ano | R$720 | 14,4% | 7,2% |

Por exemplo, uma vantagem hipotética de 5% ao ano produziria R$250/R$500 antes
da manutenção. Com duas horas mensais a R$25/h, sobrariam **−R$350/−R$100**.
São cenários de custo de oportunidade, não perdas da estratégia observadas.
Sem custos fixos, essa vantagem hipotética pagaria no máximo 50 minutos/mês
de trabalho a R$25/h sobre R$5 mil, ou 100 minutos sobre R$10 mil.

Se houver ainda 20 horas futuras de reconstrução a R$25/h, amortizadas em três
anos, acrescente R$166,67 por ano. Para desejar R$500 anuais adicionais, com
duas horas mensais e R$120 fixos, seria necessário retorno excedente líquido
de aproximadamente 27,73% sobre R$5 mil ou 13,87% sobre R$10 mil.
O esforço já gasto foi excluído: é custo passado, não justificativa para continuar.
Piso de lucro e horas aceitáveis continuam desconhecidos; cenários de custo zero
também estão registrados, sem supor que seu tempo seja gratuito.

## O que a revisão fiscal resolveu e o que ainda falta

A implementação distingue bruto de leilão, despesas, retenção e custo da posição.
Nos controles sintéticos, o mesmo recebimento gera imposto com um custo de
aquisição menor e perda fiscal com um custo maior. Não são retornos da H19.
O tratamento ordinário segue as regras gerais de ganho, deduções e compensações
da [Receita Federal](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/bolsa-de-valores),
com a [isenção mensal de ações](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/isencoes)
aplicada ao total elegível de vendas, não inferida do capital inicial.
Cada evento ainda exige enquadramento legal e fonte próprios.

Revi os três documentos VIVT preservados. O comunicado de 19/05/2025 informa
resultado descontadas despesas, não certifica o imposto pessoal nem o crédito
exato de cada investidor. Por isso, o exemplo de 39 ON, convertido em 78 unidades
de leilão, tem recebimento antes do imposto pessoal de R$2.078,07311434242,
mas imposto desconhecido. A quantidade e os custos usados no exemplo são
hipotéticos, não uma posição histórica calculada da H19.
[Comunicado da Telefônica/CVM](https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&descTipo=IPE&CodigoInstituicao=1&numProtocolo=1380678&numSequencia=905390&numVersao=1).

O cadastro real permanece com **356 datas de pagamento ausentes, 389 líquidos
não revisados, zero certificados para 1.237 intervalos e zero dos 36 registros
societários integrados/aprovados**. O problema adicional de cronologia é o
pagamento estimado da Cogna em 2028, ainda sem disponibilidade validada.
O motor não inventa essa data. Em planejamento, os 1.237 intervalos podem ser
agrupados em 312 períodos para 123 identidades ticker/ISIN; isso reduz repetição
na busca de documentos, mas não certifica nenhum intervalo.

Dependem de fonte: inventários completos de proventos e sucessores, datas e
valores líquidos revisados, bruto/despesas/retenções de leilões e termos de
entrega. Dependem também de código/integração: outras modalidades de reorganização,
revisões de razão de entrega, alterações de custo por restituição, fiscalidade
fora da bolsa/estrangeira e conciliação de centavos. Fills precisam de evidência
de execução futura. Nenhuma lacuna foi preenchida como zero.

## Decisão de pesquisa

| Caminho | Decisão e motivo |
|---|---|
| Completar todo o histórico H19 manualmente | Pausar a reconstrução extensa: há custo alto de fonte e integração para chegar apenas a um resultado exploratório. |
| Simplificar a medição e a manutenção | Caminho executado nesta etapa: compras quantificadas, código fiscal corrigido e custo de esforço explícito. Uma retomada depende de uma rota concreta de fontes com baixo custo recorrente. |
| Nova hipótese em ações | Backlog: reação a resultados pode ter mecanismo informacional, mas ainda não há vantagem PIT demonstrada; trocar de hipótese não elimina as obrigações de execução e não justifica nova varredura. |

H19 permanece Discovery/inconclusiva; não foi descartada como sem edge.
As famílias antigas não foram reabertas para procurar um backtest positivo.
Há pelo menos **32 configurações e 37 avaliações históricas expostas**, sem
holdout intacto demonstrado. Esta etapa acrescentou **zero avaliações de retorno**.
As duas versões do diagnóstico de compras e o complemento de fonte foram preservados.
Nenhuma coorte prospectiva ou automação foi iniciada. Se surgir mérito econômico
e a cadeia de dados for fechada, será necessário registrar validação futura
independente antes de qualquer operação real.

## Validação e reprodução

Suíte completa: **613 testes passaram** no snapshot `0ac04cb`. O ajuste final
de compatibilidade `bebe1f7` foi validado pelos três testes do diagnóstico e
pelos **69 testes do pacote fora do checkout**; a suíte inteira não foi repetida
para essa alteração localizada. Os módulos contábeis não mudaram depois da suíte.
Ruff e Pyright no escopo configurado passaram; cobertura geral de 79%.

As três regressões falharam na versão anterior de forma reproduzível e agora
rejeitam as entradas sem alterar a carteira. O replay real conferiu 31 arquivos
e 365.198 cotações e permaneceu **exit 2 / BLOCKED_MISSING_EVIDENCE**, idêntico
byte a byte ao anterior. O diagnóstico final e a auditoria das fontes também
foram reproduzidos byte a byte. Os bancos conservaram seus hashes.

O ZIP contém código, testes, protocolo, fontes específicas, resultados e
`reproduce.py`. Reutiliza as cotações da pasta independente já preservada;
não duplica o conjunto extenso de dados. Execute com Python 3.13 global,
sem venv ou instalação de dependências. O relatório de validação registra
commits, hashes, escopos e comandos. Nenhuma ordem, compra de serviço ou push
ao GitHub foi realizado.
'''
(outputs/'RELATORIO_STOCKS_CONTINUIDADE.md').write_text(report, encoding='utf-8')
(repo/'docs/research/2026-09-08-feasibility-results.md').write_text(report, encoding='utf-8')

for p in outputs.iterdir():
    if p.suffix in {'.md', '.json'}:
        shutil.copyfile(p, archive/'deliverables'/p.name)
for name in ['feasibility-first.json', 'feasibility-final.json', 'replay-before.json',
             'replay-after.json', 'vivt-source-audit.json', 'regression-comparison.json']:
    shutil.copyfile(work/name, archive/'deliverables'/name)
shutil.copyfile(work/'entry-unit-review/review.json', archive/'deliverables/entry-unit-review.json')
for name in ['audit_vivt_sources.py', 'probe_corporate_regressions.py', 'build_deliverables.py']:
    shutil.copyfile(work/name, archive/'scripts'/name)
shutil.copyfile(stage/'reproduce.py', archive/'scripts/reproduce.py')
for p in work.glob('*.log'):
    shutil.copyfile(p, archive/'logs'/p.name)
for p in (stage/'work').glob('*.log'):
    shutil.copyfile(p, archive/'logs'/('package-'+p.name))

observation = {'protocol': feasibility['protocol'], 'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'kind': 'FEASIBILITY_SOURCE_RESOLUTION_NOT_RETURN_TRIAL',
    'first_sha256': sha(work/'feasibility-first.json'), 'final_sha256': sha(work/'feasibility-final.json'),
    'first_completed_cases': 244, 'final_completed_cases': 248, 'cases_registered': 248,
    'intermediate_source_integration_failure': 'Requirement ISIN absent; corrected binding to frozen plan ISIN before publishing final edition.',
    'new_historical_return_evaluations': 0, 'minimum_historical_evaluations_after': 37,
    'minimum_exposed_return_configurations_after': 32, 'new_feasibility_protocols': 1}
(archive/'observations.jsonl').write_text(json.dumps(observation, ensure_ascii=False)+'\n', encoding='utf-8')

for p in outputs.iterdir():
    if p.suffix in {'.md', '.json'}:
        shutil.copyfile(p, stage/p.name)
manifest = {p.relative_to(stage).as_posix(): sha(p) for p in sorted(stage.rglob('*')) if p.is_file()
    and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts
    and 'work' not in p.relative_to(stage).parts and p.name != 'SHA256.json'}
(stage/'SHA256.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
zip_path = outputs/'STOCKS_CONTINUIDADE.zip'
with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive_zip:
    for name in [*manifest, 'SHA256.json']:
        archive_zip.write(stage/name, name)
with zipfile.ZipFile(zip_path) as archive_zip:
    assert archive_zip.testzip() is None
    assert all(hashlib.sha256(archive_zip.read(name)).hexdigest() == h for name, h in manifest.items())
receipt = {'package': zip_path.name, 'sha256': sha(zip_path), 'bytes': zip_path.stat().st_size,
    'verified_payloads': len(manifest), 'code_commit': code_commit,
    'standalone_reproduction_script_passed_before_documentation_added': True,
    'external_packaged_tests_passed': 69, 'full_economic_history_executed': False,
    'profit': None, 'new_historical_return_evaluations': 0}
save('STOCKS_CONTINUIDADE_PACOTE.json', receipt)
shutil.copyfile(outputs/'STOCKS_CONTINUIDADE_PACOTE.json', archive/'deliverables/STOCKS_CONTINUIDADE_PACOTE.json')

durable_outputs = repo.parents[1]/'outputs/continuation-20260908'
durable_outputs.mkdir(parents=True, exist_ok=True)
for p in outputs.iterdir():
    shutil.copyfile(p, durable_outputs/p.name)
durable_sources = repo.parents[1]/'work/continuation-20260908/current-tax-sources'
durable_sources.mkdir(parents=True, exist_ok=True)
for p in (work/'current-tax-sources').iterdir():
    shutil.copyfile(p, durable_sources/p.name)
print(json.dumps({'package': receipt, 'durable_outputs': str(durable_outputs),
                  'archived_authored_files': sum(p.is_file() for p in archive.rglob('*'))}, indent=2))
