"""Persist directly reviewed legal terms without pretending taxes are closed."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];base=root/'work/h19-cash-expanded-source'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def source(name,page,fragments):
    p=base/(name+'.pdf');meta=read(p.with_suffix('.pdf.source.json'))
    assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']
    text=' '.join(next(r['text'] for r in read(p.with_suffix('.complete-text.json')) if r['page']==page).split())
    for part in fragments:assert part in text,(name,part)
    return {'file':p.name,'sha256':meta['sha256'],'url':meta['url'],'page':page,'verified_fragments':fragments}
facts=[
 {'ticker':'LIGT3','ex_date':'2021-06-28','quantity_rule':'floor(original_quantity/100)*100',
  'source':source('cvm-corporate-0041',1,['múltiplos de 100','múltiplo de 100']),
  'auction_date':'2021-07-27','payment_deadline':'2021-08-03','auction_net_of_fees_reported_per_share':'15.19',
  'auction_source':source('cvm-corporate-0043',1,['R$15,19','3 de agosto de 2021']),
  'not_net_of_personal_income_tax':True},
 {'ticker':'VIVT3','ex_date':'2025-04-15','quantity_rule':'floor(original_quantity/40)*80',
  'source':source('cvm-corporate-0148',1,['40 (quarenta)','80 (oitenta)','26,64196300439','28 de maio de 2025']),
  'auction_date':'2025-05-19','payment_deadline':'2025-05-28','auction_net_of_fees_per_share':'26.64196300439',
  'not_net_of_personal_income_tax':True,
  'tax_warning_source':source('cvm-corporate-0148',2,['poderão estar sujeitos','ganhos líquidos'])},
 {'ticker':'RENT3','ex_date':'2025-12-30','delivered_ticker':'RENT4','delivered_isin':'BRRENTACNPR1',
  'declared_bonus_ratio':'1/26','operational_bonus_ratio':'0.0384609533429','credit_date':'2026-01-05',
  'tradable_on':'2025-12-30','basis_per_new_share':'49.60',
  'source':source('cvm-corporate-0157',2,['26 (vinte e seis)','05 de janeiro de 2026','R$49,60']),
  'security_source':source('cvm-corporate-0157',3,['RENT4','30 de dezembro de 2025']),
  'operational_ratio_source':source('cvm-corporate-0196',1,['0,0384609533429']),
  'ratio_revision_requires_causal_handling':True},
 {'ticker':'CYRE3','ex_date':'2026-01-02','delivered_ticker':'CYRE4','delivered_isin':'BRCYREACNPR4',
  'declared_bonus_ratio':'0.18958333333','credit_date':'2026-01-06','basis_per_new_share':'34.33',
  'source':source('cvm-corporate-0166',1,['0,18958333333','preferenciais de classe especial']),
  'delivery_source':source('cvm-corporate-0166',2,['06 de janeiro de 2026','34,33'])},
 {'ticker':'BRML3','ex_date':'2023-01-09','delivered_ticker':'ALSO3','credit_date':'2023-01-11',
  'source':source('cvm-corporate-0099',3,['11 de janeiro de 2023: crédito efetivo']),
  'auction_date':'2023-01-24','payment_deadline':'2023-02-02','auction_net_of_fees_per_share':'17.694416',
  'auction_source':source('cvm-successor-0053',1,['24 de janeiro de 2023','17,694416','2 de fevereiro de 2023']),
  'not_net_of_personal_income_tax':True},
 {'ticker':'ALSC3','ex_date':'2019-08-06','auction_date':'2020-01-15','auction_reported_per_share':'54.26688776859',
  'notice_date':'2020-01-30','payment_deadline_description':'7 business days from notice; credit day not independently confirmed',
  'source':source('cvm-successor-0023',1,['15 de janeiro de 2020','54,26688776859','7 (sete) dias úteis'])},
 {'ticker':'LCAM3','ex_date':'2022-07-04','auction_date':'2022-09-05','payment_date':'2022-09-14',
  'auction_reported_per_share':'63.200889473',
  'source':source('cvm-successor-0044',1,['05 de setembro de 2022','63,200889473','14 de setembro de 2022'])},
 {'ticker':'SOMA3','ex_date':'2024-08-01','auction_date':'2024-08-22','payment_deadline':'2024-08-26',
  'auction_reported_approximate_per_share':'50.20718','auction_total':'916532.03','auction_whole_shares':18255,
  'source':source('cvm-successor-0063',1,['916.532,03','50,20718','26 de agosto de 2024']),
  'personal_tax_and_net_custody_credit_not_confirmed':True}]
out={'facts':facts,'full_action_execution_certified':False,'new_return_evaluations':0,
     'interpretation':'Physical terms and primary references; not a completed personal-tax or continuous-return calculation.'}
path=root/'outputs/H19_EVENTOS_SOCIETARIOS_CONFERIDOS.json'
path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(len(facts))
