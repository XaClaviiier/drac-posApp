"""Guard draft writes, retain state during navigation, and polish receipt fields."""
import json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'evidence/maya-invoice-map.json').read_text());f=json.loads((ROOT/'evidence/foundations.json').read_text());so=json.loads((ROOT/'evidence/service-order-map.json').read_text())
assert not m.get('polished'),'Already applied'
api=Native();c=api.command
def go(device,state):return {'type':'navigate','dest':m['frames'][device+'-maya-'+state]}
def switch(name,value):
    field=m['fieldModes'][name];return {'type':'setVariableMode','collection':field['collection'],'mode':field['modeForValue'][json.dumps(value,ensure_ascii=False)]}
def install(edge,action):
    c('proto.interaction.clear',{'ids':[edge['node']]});c('proto.interaction.add',{'id':edge['node'],'action':action,'transition':{'type':'instant'}});edge['action']=action
try:
    c('proto.closePreview')
    collection=c('variable.createCollection',{'name':'Maya invoice / MIReceiptRef','modes':['Default','transfer']})['id']
    variable=c('variable.create',{'collection':collection,'name':'MIReceiptRef','type':'string','values':{'Default':'—','transfer':'DEMO-MAYA-0147'}})['id']
    m['fieldModes']['MIReceiptRef']={'collection':collection,'variable':variable,'values':{'Default':'—','transfer':'DEMO-MAYA-0147'},'modeForValue':{'"—"':'Default','"DEMO-MAYA-0147"':'transfer'}};m['defaults']['MIReceiptRef']='—'
    reset=[switch(n,v) for n,v in m['defaults'].items()]
    patched=[]
    for original in m['patchedSOActions']:
        action=original['originalAction']
        seeds=action.get('type')=='conditional' and len(action.get('blocks',[{}])[0].get('actions',[]))>3 and action['blocks'][0]['actions'][0]['type']=='setVariableMode'
        install(original,{'type':'conditional','blocks':[{'actions':reset+[action]}]} if seeds else action)
        if seeds:patched.append(original)
    m['patchedSOActions']=patched
    for edge in m['edges']:
        device=edge['source'].split('-')[0];state=edge['source'].split('-maya-')[-1]
        if edge['label']=='Buat invoice draf':
            install(edge,{'type':'conditional','blocks':[{'expression':'MIOffline','actions':[go(device,'offline')]},{'expression':'MIFail','actions':[go(device,'failed')]},{'actions':[edge['action']]}]})
        elif edge['label']=='Konfirmasi pembayaran':
            # Keep the cash received amount; non-cash receipts use a dash.
            def refine(action):
                for block in action.get('blocks',[]):
                    acts=block['actions']
                    if any(a.get('type')=='setVariableMode' and a.get('collection')==m['fieldModes']['MIPaymentCount']['collection'] for a in acts):
                        acts.insert(0,switch('MIReceiptRef','DEMO-MAYA-0147' if state=='confirm-transfer' else '—'))
                        if state!='confirm-cash':acts.insert(0,switch('MIReceivedText','—'))
                    for child in list(acts):refine(child)
            refine(edge['action']);install(edge,edge['action'])
        elif state=='demo' and edge['label'] in ('Demo: koneksi offline','Demo: simpan gagal','Demo: hasil pembayaran belum pasti','Demo: baca sebagai Teknisi'):
            install(edge,{'type':'conditional','blocks':[{'expression':'MIStage == "final"','actions':[edge['action']]},{'actions':[go(device,'blocked')]}]})
    for device in ('desktop','mobile'):
        key=device+'-maya-receipt';root=api.ask('node.get',{'id':m['frames'][key],'depth':1});body=242 if device=='mobile' else 196
        ref=next(n for n in root['children'] if n['type']=='TEXT' and abs(n.get('y',0)-(body+914))<1)
        c('variable.bind',{'ids':[ref['id']],'field':'text','variable':variable})
        for b in m['boundText']:
            if b['node']==ref['id']:b['variable']='MIReceiptRef'
        key=device+'-maya-queue';root=api.ask('node.get',{'id':m['frames'][key],'depth':1});x=36 if device=='mobile' else 252;cw=318 if device=='mobile' else 328
        for n in root['children']:
            if n.get('characters')=='Pemeriksaan AC · 1 pekerjaan':api.set(n['id'],characters='1 pekerjaan · Pemeriksaan AC',width=cw-100,fontSize=12)
            elif n.get('characters')=='Filter kabin · 1 pcs / tidak dipakai':api.set(n['id'],characters='Filter kabin',width=cw-100,fontSize=12)
        for offset,value,var in [(228,'Rp50.000','SOActualPriceText'),(262,'Rp100.000','SOActualPartText'),(286,'1 pcs','SOActualPartQty')]:
            node=api.node('text',m['frames'][key],x=x,y=body+offset,width=cw,text=value,props={'fontFamily':'Poppins','fontStyle':'Regular','fontSize':12,'lineHeight':'150%','textAlign':'left' if offset==286 else 'right','fill':{'$var':f['variables']['Muted']}})
            c('variable.bind',{'ids':[node],'field':'text','variable':so['fieldModes'][var]['variable']});m['boundText'].append({'node':node,'variable':var})
    m['polished']=True
    (ROOT/'evidence/maya-invoice-map.json').write_text(json.dumps(m,indent=2))
    c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')});c('proto.preview',{'start':m['frames']['desktop-maya-demo']})
    print(json.dumps({'resetOnlyScenarioSeeds':len(patched),'draftOnlineGuards':True,'receiptRefs':True,'queueLinePrices':True}))
finally:api.close()
