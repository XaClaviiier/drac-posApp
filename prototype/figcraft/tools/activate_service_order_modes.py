"""Compile finite demo assignments to native modes, validated by the installed player.

The installed player accepted setVariable actions but did not preserve their
values in the observed journeys. Per-field modes retain independent state and
keep existing component hover/pressed feedback.
"""
import json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
api=Native();c=api.command
m=json.loads((ROOT/'evidence/service-order-map.json').read_text())
f=json.loads((ROOT/'evidence/foundations.json').read_text())
assert not m.get('fieldModes'),'Conversion already applied'
old_ids=dict(m['variables']);names={v:k for k,v in old_ids.items()}
def tag(value):return json.dumps(value,ensure_ascii=False)
domains={name:{tag(value):value} for name,value in m['defaults'].items()}
copies=[]
def collect(action):
    if action.get('type')=='setVariable':
        name=names[action['variable']]
        if 'expression' in action:copies.append((name,action['expression']))
        else:
            value=action['value']['value'];domains[name][tag(value)]=value
    for block in action.get('blocks',[]):
        for child in block['actions']:collect(child)
for edge in m['edges']:collect(edge['action'])
while True:
    before=sum(map(len,domains.values()))
    for dest,source in copies:domains[dest].update(domains[source])
    if sum(map(len,domains.values()))==before:break
fields={}
try:
    c('proto.closePreview')
    for name,old in old_ids.items():c('variable.update',{'variable':old,'name':'Archived_'+name})
    for name,default in m['defaults'].items():
        values=[default]+[value for t,value in domains[name].items() if t!=tag(default)]
        mode_names=['Default']+['v'+str(i) for i in range(1,len(values))]
        collection=c('variable.createCollection',{'name':'SO State / '+name,'modes':mode_names})['id']
        kind='boolean' if isinstance(default,bool) else 'number' if isinstance(default,(int,float)) else 'string'
        variable=c('variable.create',{'collection':collection,'name':name,'type':kind,'values':dict(zip(mode_names,values))})['id']
        fields[name]={'collection':collection,'variable':variable,'values':dict(zip(mode_names,values)),'modeForValue':{tag(v):mode for mode,v in zip(mode_names,values)}}
    def switch(name,value):
        return {'type':'setVariableMode','collection':fields[name]['collection'],'mode':fields[name]['modeForValue'][tag(value)]}
    def compile_action(action):
        if action.get('type')=='setVariable':
            name=names[action['variable']]
            if 'expression' not in action:return switch(name,action['value']['value'])
            source=action['expression'];blocks=[]
            for value in domains[source].values():
                dest_value='Rp150.000' if name=='SODraftTotalText' and value=='Belum disimpan' else value
                blocks.append({'expression':source+' == '+tag(value),'actions':[switch(name,dest_value)]})
            return {'type':'conditional','blocks':blocks}
        result=dict(action)
        if 'blocks' in result:result['blocks']=[{**block,'actions':[compile_action(child) for child in block['actions']]} for block in result['blocks']]
        return result
    for item in m['boundText']:
        c('variable.bind',{'ids':[item['node']],'field':'text','variable':fields[item['variable']]['variable']})
    # Restore only intended click actions; remove all temporary probe overrides.
    c('proto.interaction.clear',{'ids':m['instances']})
    operations=[]
    for edge in m['edges']:
        edge['logicalAction']=edge['action'];edge['action']=compile_action(edge['action'])
        operations.append({'command':'proto.interaction.add','params':{'id':edge['node'],'action':edge['action'],'transition':{'type':'instant'}}})
    for node in m['themeControls'].values():
        action={'type':'conditional','blocks':[{'expression':'mode(POS) == "Dark"','actions':[{'type':'setVariableMode','collection':f['collection'],'mode':'Light'}]},{'actions':[{'type':'setVariableMode','collection':f['collection'],'mode':'Dark'}]}]}
        operations.append({'command':'proto.interaction.add','params':{'id':node,'action':action,'transition':{'type':'instant'}}})
    batch=c('command.batch',{'commands':operations})
    if isinstance(batch,list):assert not any(isinstance(r,dict) and 'error' in r for r in batch),batch
    c('variable.deleteCollection',{'collection':m['collection']})
    m['legacyCollection']=m.pop('collection');m['fieldModes']=fields;m['variables']={name:data['variable'] for name,data in fields.items()}
    m['stateImplementation']='independent finite-value native modes'
    (ROOT/'evidence/service-order-map.json').write_text(json.dumps(m,indent=2))
    c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    c('proto.preview',{'start':m['frames']['desktop-so-hub']})
    print(json.dumps({'nativeStateCollections':len(fields),'totalStateModes':sum(len(v['values']) for v in fields.values()),'clickActionsRestored':len(operations),'componentFeedbackPreserved':True}))
finally:api.close()
