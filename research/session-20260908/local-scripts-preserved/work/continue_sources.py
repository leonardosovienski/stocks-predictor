from concurrent.futures import ThreadPoolExecutor
from acquire_issuer_originals import get

jobs=[
 ('rd-2021-df','https://estadaori.estadao.com.br/wp-content/uploads/2022/02/final-Raia-Drogasil_DF_31dez2021-1.pdf'),
 ('rd-2020-itr','https://vipfiles.valor.com.br/BDEmpresas/578029.pdf'),
 ('rd-2021-ri','https://ri.rd.com.br/Download.aspx?Arquivo=FtOkKRYVBWNFLtttjipZ8Q%3D%3D&IdCanal=M9eciSyHCkOXeOE9W1JJeA%3D%3D'),
]
with ThreadPoolExecutor(max_workers=3) as pool:
    for r in pool.map(get,jobs):print(r,flush=True)
