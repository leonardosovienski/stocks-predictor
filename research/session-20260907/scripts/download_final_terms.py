from download_value_event_sources import download
import json
for name, protocol in [('crfb-options',1365364),('igta-final',918777),('igta-calculation',919272),('igta-calendar',913258)]:
    print(json.dumps(download((name,f'https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&numProtocolo={protocol}&descTipo=IPE&CodigoInstituicao=1'))),flush=True)
