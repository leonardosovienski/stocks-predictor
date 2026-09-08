from source_utils import OUT, read, norm

for name in ('rir-2018','mafon-2019'):
    for p in read(OUT/'law'/f'{name}.text.json'):
        t=norm(p['text'])
        for needle in ['acrescimo da quantidade de acoes por desdobramento']:
            at=t.find(needle)
            if at>=0:
                print(name,p['page'],t[max(0,at-1600):at+900])
        if name=='mafon-2019' and p['page'] in (48,49):print(name,p['page'],p['text'])
