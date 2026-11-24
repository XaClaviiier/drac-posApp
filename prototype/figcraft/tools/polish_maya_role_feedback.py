"""Explain why a Technician cannot open a payment action in the demo."""
import json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'evidence/maya-invoice-map.json').read_text());assert not m.get('roleFeedbackPolished'),'Already applied'
api=Native();c=api.command
try:
    c('proto.closePreview')
    for edge in m['edges']:
        if edge['source'].endswith('-maya-final') and edge['label'] in ('Tunai','QRIS','Transfer bank'):
            device=edge['source'].split('-')[0];action={'type':'conditional','blocks':[{'expression':'MIActor == "Teknisi"','actions':[{'type':'navigate','dest':m['frames'][device+'-maya-blocked']}]},{'actions':[edge['action']]}]}
            c('proto.interaction.clear',{'ids':[edge['node']]});c('proto.interaction.add',{'id':edge['node'],'action':action,'transition':{'type':'instant'}});edge['action']=action
    m['roleFeedbackPolished']=True;(ROOT/'evidence/maya-invoice-map.json').write_text(json.dumps(m,indent=2));c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    print(json.dumps({'technicianPaymentActionsExplainRestriction':True}))
finally:api.close()
