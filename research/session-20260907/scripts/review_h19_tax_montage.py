import json
from pathlib import Path
from PIL import Image, ImageDraw

base=Path(__file__).resolve().parent/'h19-tax-source'
rows=json.loads((base/'pdf-date-review.json').read_text(encoding='utf-8'))['candidates']
for start in range(0,len(rows),6):
    sheet=Image.new('RGB',(1680,1800),'#ddd')
    for n,r in enumerate(rows[start:start+6]):
        im=Image.open(r['rendered_page']).convert('RGB')
        thumb=im.copy();thumb.thumbnail((280,570))
        x=(n%2)*840;y=(n//2)*600
        sheet.paste(thumb,(x,y+25))
        label=f"{r['candidate_due_date']} / p{r['page']}"
        ImageDraw.Draw(sheet).text((x+5,y+5),label,fill='black')
        top=max(0,int(min(r['date_word']['top'],r['code_word']['top'])*1.4)-30)
        bottom=min(im.height,int(r['code_word']['bottom']*1.4)+50)
        region=im.crop((0,top,im.width,bottom));region.thumbnail((550,360))
        sheet.paste(region,(x+285,y+150))
        header=im.crop((0,0,im.width,260));header.thumbnail((550,140))
        sheet.paste(header,(x+285,y+25))
    sheet.save(base/'review-pages'/f'contact-{start//6+1}.png')
