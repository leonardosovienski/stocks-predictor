"""Publish validated results with an explicit account of unresolved evidence."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from source_utils import ROOT, OUT, read

CHAT=Path(r'C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2')
repo=ROOT/'work/stocks-predictor';archive=repo/'research/session-20260908/source-closure';outputs=CHAT/'outputs'
full=(OUT/'full-tests-12.log').read_text(encoding='utf-8')
wheel=(OUT/'wheel-tests-12-retry.log').read_text(encoding='utf-8')
assert '714 passed in 116.34s' in full and '145 passed in 0.75s' in wheel
source_validation=read(OUT/'source-validation-12.json'); package=read(OUT/'package-validation-12.json')
audit=read(OUT/'integrated-readiness-12.json'); snapshot=read(OUT/'cash-closure-12.json')
assert (OUT/'integrated-readiness-12.json').read_bytes()==(OUT/'portable-reproduced-12.json').read_bytes()
assert subprocess.check_output(['git','status','--porcelain'],cwd=repo)==b''
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
assert commit=='6e54e5d9c5187a9f555c60d67894334cfdb996be'
validation=dict(tested_commit=commit,python='global3.13',full_suite=dict(passed=714,seconds=116.34,warnings=0),
    wheel_suite=dict(passed=145,seconds=.75,installed=False,checkout_on_import_path=False),
    initial_wheel_test_failure='Legacy tests imported cash_source_audit as a flat module; harness now includes only the extracted wheel package directory. Runtime unchanged; failed log preserved.',
    source_validation=source_validation,portable_package=package,
    source_manifest_sha256=audit['source_manifest_sha256'],
    source_protocol_sha256='da8b91a7a263d9870822c58af85b4a47f2c051e932ecb3099fea986ba4456c49',
    raw_entitlements_preserved=778,raw_entitlements_without_net=64,source_revision=snapshot['counts'],
    profit=None,future_profit_projection=None,new_historical_return_evaluations=0,
    administrative_counts=[53,55],economic_status='BLOCKED_MISSING_EVIDENCE',
    scientific_independence=False,real_orders=0,paid_services=0,new_runtime_dependencies=0)
report='''# Stocks Predictor — correções e fontes revisadas

**As correções de código passaram nos testes. A base melhorou, mas a comprovação de lucro continua bloqueada. Ainda existem pendências de dados; não seria correto declarar que todas foram resolvidas.**

| Verificação | Antes da reconstrução | Revisão12 |
|---|---:|---:|
| Direitos de proventos originais preservados | 778 | 778 |
| Direitos sem data de pagamento | 356 | 37 |
| Direitos originais sem valor líquido | 389 | 64 |
| Linhas de pagamento sem líquido, contando parcelas | 389 | 66 |
| Cronogramas parcelados reconciliados nesta reconstrução | 0 | 9, com32 parcelas |
| Eventos societários integrados | 0 | 8 |
| Eventos societários ainda exigidos | 36 | 28 |

Foram resolvidas319 datas ausentes. Os778 direitos resultam em801 linhas de pagamento após a separação de parcelas. Os grupos de pendências se sobrepõem: não devem ser somados. A auditoria confere788 arquivos, incluindo753 arquivos primários e1 relatório local derivado, além de365.198 cotações.

## O que foi corrigido

- O parser preserva créditos B3 sem data de aprovação em uma lista separada de registros incompletos. Mantém os3.202 créditos completos já extraídos e recupera3.665 incompletos nos mesmos163 documentos. Esses registros não são associados automaticamente a declarações de proventos.
- Parcelamentos conservam o direito original e impedem pagar novamente o total agregado. As diferenças literais de arredondamento ficam explícitas. Foram reconciliados, entre outros, os sete pagamentos da CPFL em2025 e os dois dividendos da antiga BR Distribuidora em2020.
- Avisos originais e retificações são ligados pela identidade do evento. Foram retiradas duas associações provisórias erradas entre JCP e dividendos; os arquivos anteriores continuam preservados. Duas datas TIM foram corrigidas com o aviso posterior da companhia.
- Tabelas presentes como imagens foram conferidas visualmente nos PDFs originais. Isso recuperou informações de CPFL, Telefônica, Aliansce e Grupo Soma que a extração de texto não mostrava.
- O relatório local reconstruído deixou de ser contado como fonte primária. Hash confirma integridade; não prova sozinho origem, veracidade ou completude.
- A atualização Selic sobre proventos recebeu tratamento separado, com período documentado e regra de retenção para pessoa física. Os líquidos de2026 tratados nesta revisão representam retenção no pagamento; não resolvem eventual imposto mínimo anual pessoal.
- Os oito desdobramentos inteiros conservam quantidade proporcional e custo fiscal total. Os demais eventos não receberam termos ou bases inventados.

A publicação original da Telefônica confirma o pagamento da restituição de capital em15/07/2025; a data foi incorporada, mas a tributação e a base fiscal continuam pendentes. A reapresentação versão2 na CVM esclarece que o pagamento da Vibra anteriormente indicado para2026 está agendado para15/09/2027. Pagamento agendado não equivale a dinheiro recebido. [Telefônica: comunicado original](https://api.mziq.com/mzfilemanager/v2/d/24165f81-24d6-4648-bf9f-66712905d5a2/95055a57-421c-0f90-4b03-811356da6775?origin=1), [Vibra: versão2](https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&descTipo=IPE&CodigoInstituicao=1&numProtocolo=1494351&numSequencia=1019057&numVersao=2).

## O que continua bloqueando o resultado econômico

Restam37 datas e66 líquidos de pagamentos derivados, além de28 entradas societárias. Há avisos que trazem apenas prazo máximo, documentos históricos que não foram recuperados, divergências de valores, devolução de capital dependente de base fiscal e eventos com frações, sucessores ou novas classes de ações. Prazos máximos não foram tratados como datas efetivas.

Nenhum dos1.248 intervalos exigidos tem inventário integral certificado. Encontrar pagamentos conhecidos não demonstra que nenhum outro provento ocorreu. A revisão identificou, por exemplo, duas atualizações monetárias da BR Distribuidora em2020 que não constam dos778 direitos congelados. Elas foram registradas como lacuna de inventário. A SLC em2019 tem data confirmada, mas as unidades antes/depois do desdobramento ainda precisam de reconciliação.

Também permanecem os requisitos de arredondamento do caixa na corretora, tratamento de frações e revisão H20 vinculada à versão final das fontes. O calendário congelado termina em01/04/2026; não acrescentei pregões futuros presumidos. Parte dos campos de disponibilidade permanece bloqueada. O primeiro sinal de2018 continua sem cobertura suficiente. Não retirei períodos ou empresas para melhorar artificialmente o resultado.

**Lucro líquido histórico e projeção de lucro futuro permanecem desconhecidos.** Não há holdout intacto. Foram preservados H1–H20, a contagem administrativa53/55 e as observações anteriores. Nenhuma nova avaliação de retorno, ordem, serviço pago, instalação, agente adicional ou escrita em bancos protegidos ocorreu nesta revisão. O protocolo de aquisição de fontes não autoriza um novo teste de retorno: ele ainda exigirá evidência completa e pré-inscrição vinculada ao hash final.

## Validação e reprodução

- **714 testes passaram**, sem avisos, no Python global3.13, em116,34s:697 regulares e17 arquivados.
- **145 testes passaram na wheel extraída fora do checkout**, em0,75s. A primeira tentativa dessa suíte parou porque testes antigos usam importação de módulo sem o nome do pacote; o caminho do ambiente de teste foi corrigido para apontar à própria wheel, preservando o log inicial e sem mudar o runtime.
- Ruff e Pyright passaram; os módulos de fontes foram incluídos no escopo permanente do Pyright.
- Cinco tentativas de adulteração foram rejeitadas: alteração de fonte, exclusão de direito, alteração do bruto com novo manifesto, liberação indevida do inventário e promoção de relatório derivado a fonte primária.
- O pacote portátil verificou seus856 arquivos e reproduziu a auditoria **byte a byte**, com Python3.13 em modo isolado, sem instalar a wheel, sem rede e sem importar código do checkout.

Código testado: `6e54e5d9c5187a9f555c60d67894334cfdb996be`.

Manifesto das fontes: `b9dfab5fb2dc67f7fcdd71f52b325a3a1d442917c116f514fd09f11926876f7e`.

SHA256 da auditoria: `fdaf20300e47ca4b42e1e99cea46ffc80ecf4efaac4f0f80f6f39e917b4d105a`.

O ZIP contém fontes locais, baseline preservada, revisão, wheel, histórico e comando `REPRODUZIR_FONTES.py`. Depois de extrair, execute `py -3.13 -I REPRODUZIR_FONTES.py --output auditoria-reproduzida.json`. O código de saída0 significa reprodução correta da auditoria; o resultado econômico continua `BLOCKED_MISSING_EVIDENCE`.

Arquivos complementares: `PENDENCIAS_STOCKS.json` lista os bloqueios concretos; `VALIDACAO_FONTES_12.json` registra os testes e hashes; `PRONTIDAO_FONTES_12.json` contém a auditoria completa. A conferência foi feita pelo mesmo agente, sem revisão científica independente.
'''
# Restore conventional spacing around numerals in the prose, leaving URLs,
# hashes and code spans unchanged by applying replacements only to known text.
for a,b in [('revisão12','revisão 12'),('com32','com 32'),('resolvidas319','resolvidas 319'),
    ('Os778','Os 778'),('em801','em 801'),('confere788','confere 788'),('incluindo753','incluindo 753'),
    ('e1 relatório','e 1 relatório'),('de365.198','de 365.198'),('os3.202','os 3.202'),
    ('recupera3.665','recupera 3.665'),('mesmos163','mesmos 163'),('em2025','em 2025'),
    ('em2020','em 2020'),('de2026','de 2026'),('em15/07/2025','em 15/07/2025'),
    ('versão2','versão 2'),('para2026','para 2026'),('para15/09/2027','para 15/09/2027'),
    ('Restam37','Restam 37'),('e66','e 66'),('de28','de 28'),('dos1.248','dos 1.248'),
    ('dos778','dos 778'),('em2019','em 2019'),('em01/04/2026','em 01/04/2026'),
    ('de2018','de 2018'),('administrativa53/55','administrativa 53/55'),('global3.13','global 3.13'),
    ('em116,34','em 116,34'),('s:697','s: 697'),('e17','e 17'),('em0,75','em 0,75'),
    ('seus856','seus 856'),('Python3.13','Python 3.13'),('saída0','saída 0')]:report=report.replace(a,b)
for p in [outputs/'REVISAO_FONTES_STOCKS.md',archive/'RESULTADO_FONTES_12.md',
          repo/'docs/research/2026-09-08-source-closure-results.md']:
    p.write_text(report,encoding='utf-8',newline='\n')
for directory in [outputs,archive]:
    (directory/'VALIDACAO_FONTES_12.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
for name in ['PENDENCIAS_STOCKS.json','PRONTIDAO_FONTES_12.json']:
    shutil.copyfile(archive/name,outputs/name)
for name in ['REPRODUZIR_FONTES.py','package_source_closure12.py','verify_source_closure12.py','finalize_source_closure12.py']:
    shutil.copyfile(CHAT/'work'/name,archive/name)
for name in ['full-tests-12.log','wheel-tests-12.log','wheel-tests-12-retry.log','source-validation-12.json',
             'portable-reproduction-12.log','package-validation-12.json']:
    shutil.copyfile(OUT/name,archive/name)
for name in ['HANDOFF.md','STOCKS_CURRENT_STATE.md','docs/continuation/UPDATE_20260908.md']:
    p=repo/name;t=p.read_text(encoding='utf-8')
    t=t.replace('27 testes focados passam; Ruff/Pyright serão registrados com a suíte final.\nA validação completa e a wheel portátil serão anexadas após este commit.',
        'Validação do código 6e54e5d: 714 testes completos, sem avisos; 145 testes\nna wheel fora do checkout. Ruff e Pyright verdes. Cinco adulterações rejeitadas.\nPacote de 856 arquivos reproduz a auditoria byte a byte com Python 3.13\nisolado, sem instalação ou rede. Resultados em docs/research/\n2026-09-08-source-closure-results.md e na pasta de pesquisa source-closure.')
    # Only the new leading section is normalized; historical text is preserved.
    marker='## Correções concluídas da revisão (08/09/2026 UTC)'
    split=t.find(marker)
    if split>=0:
        head,tail=t[:split],t[split:]
        for a,b in [('Protocolo0700','Protocolo 0700'),('versões01','versões 01'),('fontes\nprimárias e1','fontes\nprimárias e 1'),
            ('verificados;754','verificados; 754'),('quais753','quais 753'),('.365.198','. 365.198'),('Os778','Os 778'),
            ('em801','em 801'),('com9','com 9'),('e32','e 32'),('ausentes:356','ausentes: 356'),
            ('ausentes:389','ausentes: 389'),('originais→66','originais→66'),('8 desdobramentos','8 desdobramentos'),
            ('integrados;28','integrados; 28'),('fiscal.1.248','fiscal. 1.248'),('líquidos2026','líquidos 2026'),
            ('SLC2019','SLC 2019'),('BRDT2020','BRDT 2020'),('dos778','dos 778'),('Extrações01','Extrações 01'),
            ('usaram3.14','usaram 3.14'),('materializações04','materializações 04'),('global3.13','global 3.13'),
            ('ajusteH1','ajuste H1')]:head=head.replace(a,b)
        t=head+tail
    p.write_text(t,encoding='utf-8',newline='\n')
print(json.dumps({'tested_commit':commit,'economic_status':audit['status'],**package}))
