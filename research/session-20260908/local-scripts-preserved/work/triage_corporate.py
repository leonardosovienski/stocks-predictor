from source_utils import BASE, ROOT, read, norm, pages

gaps=[i for i in read(ROOT/'outputs/H19_CAIXA_EXECUCAO_V3.json')['issues'] if i['kind']=='ORDINARY_STOCK_ACTION_DELIVERY_AND_BASIS']
docs=read(BASE/'ipe-corporate-notices.json')
for g in gaps:
    print('\nREQUIREMENT',g)
    dd=[d for d in docs if g in d['matching_requirements']]
    for d in dd:
        if any(k in norm(d['Assunto']) for k in ['desdobr','grupamento','bonifica','leilao','fraco']):
            print(d['local_file'],d['Data_Entrega'],d['Assunto'])
