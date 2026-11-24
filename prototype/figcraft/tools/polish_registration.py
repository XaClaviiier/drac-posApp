"""Preserve the originating form on cancel and refine native registration geometry."""
import json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
api=Native();c=api.command
m=json.loads((ROOT/'evidence/registration-map.json').read_text())
f=json.loads((ROOT/'evidence/foundations.json').read_text())
try:
    for key,frame in m['frames'].items():
        node=api.ask('node.get',{'id':frame,'depth':1}); state=key.split('-reg-',1)[1]
        mobile=key.startswith('mobile-'); device=key.split('-',1)[0]
        for child in node.get('children',[]):
            if mobile and child.get('name')=='Demo: isi contoh lengkap':api.set(child['id'],y=1138)
            if mobile and child.get('name')=='Demo: plat sudah terdaftar':api.set(child['id'],y=1194)
            if state=='edited' and not mobile and child.get('type')=='RECTANGLE' and child.get('y')==196 and child.get('height')==728:
                api.set(child['id'],height=940)
        # A shared discard view returns to the form that actually opened it.
        if state=='discard':
            edge=next(e for e in m['edges'] if e['source']==key and e['label']=='Lanjutkan mengisi')
            c('proto.interaction.clear',{'ids':[edge['node']]})
            c('proto.interaction.add',{'id':edge['node'],'action':{'type':'back'},'transition':{'type':'instant'}})
            edge['historyBack']=True
        escape_target={
            'filled':'discard','known':'discard','edit':'discard',
            'review':'filled','known-review':'known','saved':'list-saved',
            'known-saved':'list-known','edited':'list-edited'
        }.get(state)
        if escape_target or state in ('discard','saving','known-saving'):
            c('proto.interaction.clear',{'ids':[frame]})
            for interaction in node.get('interactions',[]):
                if interaction.get('trigger',{}).get('type')!='keyPress':c('proto.interaction.add',{'id':frame,**interaction})
            if state=='discard':
                c('proto.interaction.add',{'id':frame,'trigger':{'type':'keyPress','key':'Escape'},'action':{'type':'back'},'transition':{'type':'instant'}})
            elif escape_target:
                c('proto.interaction.add',{'id':frame,'trigger':{'type':'keyPress','key':'Escape'},'dest':m['frames'][device+'-reg-'+escape_target],'transition':{'type':'instant'}})
    (ROOT/'evidence/registration-map.json').write_text(json.dumps(m,indent=2))
    for key,mode in [('desktop-reg-filled','Light'),('mobile-reg-filled','Light'),('desktop-reg-known-review','Dark'),('mobile-reg-invalid','Dark'),('mobile-reg-saved','Light')]:
        frame=m['frames'][key]
        c('variable.setMode',{'ids':[frame],'collection':f['collection'],'mode':mode})
        try:c('file.export',{'ids':[frame],'format':'png','path':str(ROOT/'evidence'/(key+'-'+mode.lower()+'.png')),'scale':1})
        finally:c('variable.setMode',{'ids':[frame],'collection':f['collection'],'mode':None})
    c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    c('proto.preview',{'start':m['frames']['desktop-reg-list']})
    print(json.dumps({'formHistoryPreserved':True,'escapeConfirmsUnsavedForms':True,'nativeExports':5}))
finally:api.close()
