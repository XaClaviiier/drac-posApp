"""Keep subtotal text inside item cards and omit document IDs before creation."""
import json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
api=Native();m=json.loads((ROOT/'evidence/diagnosis-map.json').read_text())
try:
    adjusted=0
    for key,frame in m['frames'].items():
        state=key.split('-diag-')[1]
        root=api.ask('node.get',{'id':frame,'depth':1})
        for n in root.get('children',[]):
            if n['type']!='TEXT':continue
            if key.startswith('desktop-') and n.get('width')==712 and n.get('x')==268 and n.get('characters') in ('Subtotal','Rp50.000','Rp100.000','Rp45.000','—'):
                api.set(n['id'],width=680);adjusted+=1
            if state in ('origin','no-diagnosis','list') and n.get('characters')==m['fixture']['reference']+' · '+m['fixture']['estimate']:
                api.set(n['id'],characters=m['fixture']['reference']);adjusted+=1
            if state in ('empty','no-results','load-error') and 278<=n['y']<=378 and key.startswith('mobile-'):
                api.set(n['id'],visible=False)
            if state in ('empty','no-results','load-error') and 216<=n['y']<=316 and key.startswith('desktop-'):
                api.set(n['id'],visible=False)
    api.command('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    print(json.dumps({'detailsAdjusted':adjusted}))
finally:api.close()
