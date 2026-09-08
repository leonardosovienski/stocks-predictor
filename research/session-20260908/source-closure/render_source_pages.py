"""Render original PDFs for visual source review; no PDF authoring."""
from pathlib import Path
import sys
import struct
import zlib
import pypdfium2 as pdfium

ROOT=Path(r'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907')
OUT=ROOT/'work/source-closure-20260908/pages'
OUT.mkdir(exist_ok=True)
for arg in sys.argv[1:]:
    name,page=arg.rsplit(':',1); index=int(page)-1
    source=ROOT/'work/h19-cash-expanded-source'/name
    pdf=pdfium.PdfDocument(source); p=pdf[index]
    bitmap=p.render(scale=1.4, rev_byteorder=True)
    channels=bitmap.n_channels
    assert channels in (3,4)
    raw=bytes(bitmap.buffer)
    rows=b''.join(b'\0'+raw[y*bitmap.stride:y*bitmap.stride+bitmap.width*channels] for y in range(bitmap.height))
    def chunk(tag,data):
        return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',bitmap.width,bitmap.height,8,2 if channels==3 else 6,0,0,0))
    png+=chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')
    dest=OUT/f'{source.stem}-p{page}.png';dest.write_bytes(png)
    print(dest)
    p.close();pdf.close()
