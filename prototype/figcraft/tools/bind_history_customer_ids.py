"""Use customer IDs for visit selection and history filters, independently of names."""
import json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1];m=json.loads((ROOT/'evidence/customer-history-map.json').read_text());f=json.loads((ROOT/'evidence/foundations.json').read_text());assert not m.get('customerIdsBound'),'Already applied';api=Native();c=api.command;ops=[]
try:
    c('proto.closePreview')
    for name in ('CHSelectedCustomerId','CHRegCustomerId'):
        col=c('variable.createCollection',{'name':'Customer history / '+name,'modes':['Default','arif']})['id'];var=c('variable.create',{'collection':col,'name':name,'type':'string','values':{'Default':'DEMO-C0147','arif':'DEMO-C0150'}})['id'];m['fieldModes'][name]={'collection':col,'variable':var,'values':{'Default':'DEMO-C0147','arif':'DEMO-C0150'},'modeForValue':{'"DEMO-C0147"':'Default','"DEMO-C0150"':'arif'}};m['defaults'][name]='DEMO-C0147'
    def mode(name,value):
        field=m['fieldModes'][name];return {'type':'setVariableMode','collection':field['collection'],'mode':field['modeForValue'][json.dumps(value)]}
    selected=m['fieldModes']['CHSelectedName'];reg=m['fieldModes']['CHRegName']
    def refine(action):
        for block in action.get('blocks',[]):
            if 'expression' in block:
                block['expression']=block['expression'].replace('CHSelectedName == "Arif Ramadhan"','CHSelectedCustomerId == "DEMO-C0150"').replace('CHSelectedName == "Maya Lestari"','CHSelectedCustomerId == "DEMO-C0147"').replace('CHRegName == "Arif Ramadhan"','CHRegCustomerId == "DEMO-C0150"').replace('CHRegName == "Maya Lestari"','CHRegCustomerId == "DEMO-C0147"')
            expanded=[]
            for child in block['actions']:
                refine(child);expanded.append(child)
                if child.get('type')=='setVariableMode' and child.get('collection')==selected['collection']:
                    name=selected['values'][child['mode']];expanded.append(mode('CHSelectedCustomerId','DEMO-C0150' if name=='Arif Ramadhan' else 'DEMO-C0147'))
                if child.get('type')=='setVariableMode' and child.get('collection')==reg['collection']:
                    expanded.append({'type':'conditional','blocks':[{'expression':'CHSelectedCustomerId == "DEMO-C0150"','actions':[mode('CHRegCustomerId','DEMO-C0150')]},{'actions':[mode('CHRegCustomerId','DEMO-C0147')]}]})
            block['actions']=expanded
    for edge in m['edges']+m['patchedHistoryLinks']:
        refine(edge['action']);ops.extend([{'command':'proto.interaction.clear','params':{'ids':[edge['node']]}},{'command':'proto.interaction.add','params':{'id':edge['node'],'action':edge['action'],'transition':{'type':'instant'}}}])
    result=c('command.batch',{'commands':ops});assert not (isinstance(result,list) and any(isinstance(r,dict) and 'error' in r for r in result)),result
    for key,frame in m['frames'].items():
        state=key.split('-ch-')[1]
        if state in ('new-visit','visit-invalid','review','saved'):
            mobile=key.startswith('mobile');name='CHRegCustomerId' if state in ('review','saved') else 'CHSelectedCustomerId';node=api.node('text',frame,x=36 if mobile else 252,y=(242 if mobile else 196)+103,width=318 if mobile else 1144,text='DEMO-C0147',props={'fontFamily':'Poppins','fontStyle':'Regular','fontSize':12,'lineHeight':'150%','fill':{'$var':f['variables']['Muted']}});c('variable.bind',{'ids':[node],'field':'text','variable':m['fieldModes'][name]['variable']});m['boundText'].append({'node':node,'variable':name})
    m['customerIdsBound']=True;(ROOT/'evidence/customer-history-map.json').write_text(json.dumps(m,indent=2),encoding='utf-8');c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')});c('proto.preview',{'start':m['frames']['desktop-ch-hub']});print(json.dumps({'customerIdFilters':True,'independentPhoneAndNames':True,'fields':len(m['fieldModes'])}))
finally:api.close()
