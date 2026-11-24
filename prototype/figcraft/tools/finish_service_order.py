"""Keep the Owner context after completion and clarify the unused-part example."""
import copy,json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'evidence/service-order-map.json').read_text())
f=json.loads((ROOT/'evidence/foundations.json').read_text())
assert not m.get('completionRolePolished'),'Already applied'
api=Native();c=api.command
try:
    c('proto.closePreview')
    for device in ('desktop','mobile'):
        router=next(e for e in m['edges'] if e['source']==device+'-so-real-view' and e['label']=='Kembali ke SO')['action']
        edge=next(e for e in m['edges'] if e['source']==device+'-so-complete' and e['label']=='Konfirmasi')
        def replace(action):
            if action.get('type')=='navigate' and action.get('dest')==m['frames'][device+'-so-completed']:
                action.clear();action.update(copy.deepcopy(router));return
            for block in action.get('blocks',[]):
                for child in block['actions']:replace(child)
        replace(edge['action'])
        if 'logicalAction' in edge:replace(edge['logicalAction'])
        c('proto.interaction.clear',{'ids':[edge['node']]})
        c('proto.interaction.add',{'id':edge['node'],'action':edge['action'],'transition':{'type':'instant'}})
        mobile=device=='mobile';frame=m['frames'][device+'-so-real-edit']
        api.node('text',frame,x=36 if mobile else 252,y=(258 if mobile else 196)+646,width=318 if mobile else 712,text='Lepas hanya untuk part yang belum dipakai.',props={'fontFamily':'Poppins','fontSize':12,'fontStyle':'Regular','lineHeight':'150%','fill':{'$var':f['variables']['Muted']}})
    m['completionRolePolished']=True
    (ROOT/'evidence/service-order-map.json').write_text(json.dumps(m,indent=2))
    c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    c('proto.preview',{'start':m['frames']['desktop-so-hub']})
    print(json.dumps({'ownerCompletionRouting':True,'unusedPartCaption':True}))
finally:api.close()
