"""Add the zero-invoice example and make connectivity demos stage-aware."""
import copy,json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'evidence/maya-invoice-map.json').read_text());so=json.loads((ROOT/'evidence/service-order-map.json').read_text());f=json.loads((ROOT/'evidence/foundations.json').read_text())
assert not m.get('zeroCaseAdded'),'Already applied'
fields={**so['fieldModes'],**m['fieldModes']};api=Native();c=api.command
def switch(name,value):
    field=fields[name];return {'type':'setVariableMode','collection':field['collection'],'mode':field['modeForValue'][json.dumps(value,ensure_ascii=False)]}
try:
    c('proto.closePreview')
    for device in ('desktop','mobile'):
        source=device+'-maya-demo';route=next(e for e in m['edges'] if e['source']==source and e['label']=='Buka transaksi Maya')['action']
        for edge in m['edges']:
            if edge['source']==source and edge['label'] in ('Demo: koneksi offline','Demo: simpan gagal'):
                flag='MIOffline' if 'offline' in edge['label'] else 'MIFail'
                action={'type':'conditional','blocks':[{'expression':'MIStage != "paid"','actions':[switch(flag,True),copy.deepcopy(route)]},{'actions':[{'type':'navigate','dest':m['frames'][device+'-maya-paid']}]}]}
                c('proto.interaction.clear',{'ids':[edge['node']]});c('proto.interaction.add',{'id':edge['node'],'action':action,'transition':{'type':'instant'}});edge['action']=action
        frame=m['frames'][source];node=api.ask('node.get',{'id':frame,'depth':0});mobile=device=='mobile';c('page.select',{'id':2079 if mobile else 1});x=36 if mobile else 252;y=(242 if mobile else 196)+954;w=318 if mobile else 1144
        b=c('instance.place',{'component':f['buttons']['Secondary'],'x':node['x']+x+w/2,'y':node['y']+y+22})['id'];c('node.reparent',{'ids':[b],'parent':frame});api.set(b,x=x,y=y,width=w,height=44,name='Demo: SO Selesai Rp0 (ulang data)');c('instance.setProperties',{'ids':[b],'properties':{'Label':'Demo: SO Selesai Rp0 (ulang data)'}})
        values={**so['defaults'],'SOActor':'Owner','SOOwner':True,'SOStatus':'Selesai','SOActualSaved':True,'SOActualPrice':0,'SOActualPriceText':'Rp0','SOActualHasPart':False,'SOActualPartText':'Rp0','SOActualPartQty':'Tidak dipakai','SOActualTotal':0,'SOActualTotalText':'Rp0','SOQueued':True,'SOFinal':False,'SOHasContext':True}
        action={'type':'conditional','blocks':[{'actions':[*(switch(n,v) for n,v in m['defaults'].items()),*(switch(n,v) for n,v in values.items()),switch('MIActor','Owner'),{'type':'navigate','dest':m['frames'][device+'-maya-queue']}]}]}
        c('proto.interaction.add',{'id':b,'action':action,'transition':{'type':'instant'}});m['instances'].append(b);m['edges'].append({'source':source,'node':b,'label':'Demo: SO Selesai Rp0 (ulang data)','action':action})
    m['zeroCaseAdded']=True
    (ROOT/'evidence/maya-invoice-map.json').write_text(json.dumps(m,indent=2));c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')});c('proto.preview',{'start':m['frames']['desktop-maya-demo']})
    print(json.dumps({'zeroInvoiceExample':True,'stageAwareOfflineAndFailure':True}))
finally:api.close()
