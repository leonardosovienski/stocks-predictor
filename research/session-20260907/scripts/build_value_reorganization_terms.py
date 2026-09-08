"""Transcribe verified final issuer/B3 terms; no portfolio outcomes here."""
from pathlib import Path
import hashlib
import json
import shutil

BASE=Path(__file__).resolve().parent
DEST=BASE/'value-event-terms'
def source(name):
    return json.loads((DEST/(name+'.source.json')).read_text(encoding='utf-8'))
def stock(ticker,isin,ratio,credit=None):
    return dict(ticker=ticker,isin=isin,ratio=ratio,credit_date=credit)
def cash(amount,payment,label='COMPULSORY_CASH'):
    return dict(amount_brl=amount,payment_date=payment,label=label)
def event(ticker,isin,last,ex,stocks,cashes,names,labels=None,retains=False):
    return dict(ticker=ticker,isin=isin,last_cum=last,ex_date=ex,stocks=stocks,cash=cashes,
                removes_original=not retains,source_names=names,sources=[source(n) for n in names],
                covered_panel_labels=labels or ['INCORPORACAO'])
events=[
event('FIBR3','BRFIBRACNOR9','2019-01-03','2019-01-04',[stock('SUZB3','BRSUZBACNOR0',0.4613,'2019-01-08')],[cash(50.20,'2019-01-14')],['fibr','fibr-procedure']),
event('ALSC3','BRALSCACNOR0','2019-08-05','2019-08-06',[stock('ALSO3','BRALSOACNOR5',0.787808369)],[],['alsc']),
event('TIMP3','BRTIMPACNOR1','2020-10-09','2020-10-13',[stock('TIMS3','BRTIMSACNOR5',1)],[],['timp']),
event('IGTA3','BRIGTAACNOR5','2021-11-19','2021-11-22',[stock('IGTI11','BRIGTICDAM16',0.15964,'2021-11-24')],[],['igta','igta-final']),
event('GNDI3','BRGNDIACNOR2','2022-02-11','2022-02-14',[stock('HAPV3','BRHAPVACNOR4',5.24364185943,'2022-02-16')],[cash(5.16614751932,'2022-03-29'),cash(1.613026961,'2022-03-29','CLOSING_DIVIDEND')],['gndi']),
event('LCAM3','BRLCAMACNOR3','2022-07-01','2022-07-04',[stock('RENT3','BRRENTACNOR4',0.43884446,'2022-07-06')],[cash(0.8374919192,'2022-08-16','CLOSING_DIVIDEND')],['lcam-final','lcam-cash','lcam-payment']),
event('BRML3','BRBRMLACNOR9','2023-01-06','2023-01-09',[stock('ALSO3','BRALSOACNOR5',0.398551577675763)],[cash(1.62899410177968,'2023-01-20')],['brml','brml-close']),
event('SOMA3','BRSOMAACNOR3','2024-07-31','2024-08-01',[stock('AZZA3','BRAZZAACNOR9',0.121695988348,'2024-08-05')],[],['soma-final']),
event('VAMO3','BRVAMOACNOR7','2024-12-13','2024-12-16',[stock('VAMO3','BRVAMOACNOR7',1),stock('AMOB3','BRAMOBACNOR9',1.15136366)],[],['vamo'],['CIS RED CAP'],True),
event('CCRO3','BRCCROACNOR2','2025-04-30','2025-05-02',[stock('MOTV3','BRMOTVACNOR7',1,'2025-05-02')],[],['ccro'],['INCORPORACAO']),
event('CRFB3','BRCRFBACNOR2','2025-05-30','2025-06-02',[],[cash(8.50,'2025-06-10','DEFAULT_CASH_REDEMPTION')],['crfb-options','crfb-final','crfb-close']),
event('JBSS3','BRJBSSACNOR8','2025-06-06','2025-06-09',[stock('JBSS32','BRJBSSBDR002',0.5)],[],['jbss-b3']),
event('NTCO3','BRNTCOACNOR5','2025-07-01','2025-07-02',[stock('NATU3','BRNATUACNOR6',1,'2025-07-03')],[],['ntco'])
]
panel=json.loads((BASE/'value-measurement-source/events.json').read_text(encoding='utf-8'))
subs=[r for r in panel['events'] if r['label']=='SUBSCRICAO' and (r['ticker'],r['ex_date']) in {
    ('MGLU3','2024-02-01'),('RENT3','2024-06-27'),('EQTL3','2025-01-14'),
    ('BEEF3','2025-04-30'),('SMFT3','2025-12-08'),('CVCB3','2021-06-25')}]
assert len(subs)==6
for row in subs:
    for name in row['sources']:
        src=BASE/'h17-run-pack-v2/sources'/name
        shutil.copy2(src,DEST/name)
        shutil.copy2(src.with_suffix('.source.json'),DEST/src.with_suffix('.source.json').name)
record={'events':events,'subscriptions':subs,
        'unknown_credit_dates_policy':'Null is explicitly unverified physical delivery timing; theoretical entitlement valuation only.',
        'evidence_limit':'Corporate final terms and historical quotes do not certify full ordinary dividend coverage or executable settlement.'}
path=DEST/'reorganizations.json'
with path.open('x',encoding='utf-8') as stream:
    json.dump(record,stream,ensure_ascii=False,indent=2,allow_nan=False)
print('saved',len(events),'reorganizations',len(subs),'subscriptions')
