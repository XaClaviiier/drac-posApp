"""Connect customer navigation back to POS and the existing Maya service demo."""
import json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1];m=json.loads((ROOT/'evidence/customer-history-map.json').read_text());mi=json.loads((ROOT/'evidence/maya-invoice-map.json').read_text());so=json.loads((ROOT/'evidence/service-order-map.json').read_text());f=json.loads((ROOT/'evidence/foundations.json').read_text());assert not m.get('navigationConnected'),'Already applied'
api=Native();c=api.command
def mode(name,value):
    field=mi['fieldModes'][name];return {'type':'setVariableMode','collection':field['collection'],'mode':field['modeForValue'][json.dumps(value,ensure_ascii=False)]}
def role_copy():return {'type':'conditional','blocks':[{'expression':'CHActor == '+json.dumps(role),'actions':[mode('MIActor',role)]} for role in ('Kasir','Owner','Teknisi')]}
def add(source,x,y,w,label,action):
    frame=m['frames'][source];node=api.ask('node.get',{'id':frame,'depth':0});device=source.split('-')[0];c('page.select',{'id':2079 if device=='mobile' else 1});b=c('instance.place',{'component':f['buttons']['Secondary'],'x':node['x']+x+w/2,'y':node['y']+y+22})['id'];c('node.reparent',{'ids':[b],'parent':frame});api.set(b,x=x,y=y,width=w,height=44,name=label);c('instance.setProperties',{'ids':[b],'properties':{'Label':label}});c('proto.interaction.add',{'id':b,'action':action,'transition':{'type':'instant'}});m['instances'].append(b);m['edges'].append({'source':source,'node':b,'label':label,'action':action})
try:
    c('proto.closePreview')
    for source in m['frames']:
        device=source.split('-')[0];mobile=device=='mobile';queue=next(e['action'] for e in mi['edges'] if e['source']==device+'-maya-paid' and e['label']=='Kembali ke antrean');pos={'type':'conditional','blocks':[{'expression':'CHActor == "Teknisi"','actions':[{'type':'navigate','dest':m['frames'][device+'-ch-blocked']}]},{'actions':[role_copy(),queue]}]}
        if not mobile:add(source,16,304,176,'POS Kasir',pos)
        if source.endswith('-ch-hub'):
            add(source,36 if mobile else 252,(242 if mobile else 196)+880,318 if mobile else 1144,'Demo: layanan Maya 0147',{'type':'navigate','dest':so['frames'][device+'-so-hub']})
            add(source,36 if mobile else 252,(242 if mobile else 196)+1030,318 if mobile else 1144,'Kembali ke POS',pos)
    m['navigationConnected']=True;(ROOT/'evidence/customer-history-map.json').write_text(json.dumps(m,indent=2),encoding='utf-8');c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')});c('proto.preview',{'start':m['frames']['desktop-ch-hub']});print(json.dumps({'newActions':len(m['edges']),'crossModuleNavigationKeepsCustomerState':True}))
finally:api.close()
