"""Keep an invoice draft stale after withdrawal, even when the SO total is unchanged."""
import copy,json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'evidence/maya-invoice-map.json').read_text());so=json.loads((ROOT/'evidence/service-order-map.json').read_text())
assert not m.get('stickyWithdrawalGuard'),'Already applied'
api=Native();c=api.command;operations=[]
try:
    c('proto.closePreview')
    collection=c('variable.createCollection',{'name':'Maya invoice / MIStale','modes':['Default','stale']})['id']
    variable=c('variable.create',{'collection':collection,'name':'MIStale','type':'boolean','values':{'Default':False,'stale':True}})['id']
    m['fieldModes']['MIStale']={'collection':collection,'variable':variable,'values':{'Default':False,'stale':True},'modeForValue':{'false':'Default','true':'stale'}};m['defaults']['MIStale']=False
    label=m['fieldModes']['MIQueueLabel']
    c('variable.addMode',{'collection':label['collection'],'name':'stale'})
    c('variable.set',{'variable':label['variable'],'mode':'stale','value':'Draf perlu Owner'})
    label['values']['stale']='Draf perlu Owner';label['modeForValue']['"Draf perlu Owner"']='stale'
    def flag(value):
        change={'type':'setVariableMode','collection':collection,'mode':'stale' if value else 'Default'}
        return {'type':'conditional','blocks':[{'actions':[change,{'type':'setVariableMode','collection':label['collection'],'mode':'stale'}]}]} if value else change
    def install(edge,action):
        operations.extend([{'command':'proto.interaction.clear','params':{'ids':[edge['node']]}},{'command':'proto.interaction.add','params':{'id':edge['node'],'action':action,'transition':{'type':'instant'}}}]);edge['action']=action
    stage=m['fieldModes']['MIStage'];none_mode=stage['modeForValue']['"none"']
    def refine(action):
        for block in action.get('blocks',[]):
            if block.get('expression','').startswith('SOQueued and SOActualSaved and MITotal'):
                block['expression']='not MIStale and '+block['expression']
            if 'SOQueued and SOActualSaved and MITotal' in block.get('expression','') and not block['expression'].startswith('not MIStale'):
                block['expression']=block['expression'].replace('SOQueued and SOActualSaved and MITotal','not MIStale and SOQueued and SOActualSaved and MITotal')
            actions=block['actions'];expanded=[]
            for child in actions:
                refine(child)
                if child.get('type')=='setVariableMode' and child.get('collection')==stage['collection'] and child.get('mode')==none_mode:expanded.append(flag(False))
                expanded.append(child)
            block['actions']=expanded
    for edge in m['edges']:
        refine(edge['action'])
        if edge['source'].endswith('-maya-demo') and edge['label']=='Demo: penyerahan ditarik':
            device=edge['source'].split('-')[0]
            edge['action']={'type':'conditional','blocks':[{'expression':'MIStage == "draft" and not SOFinal','actions':[flag(True),edge['action']]},{'actions':[{'type':'navigate','dest':m['frames'][device+'-maya-blocked']}]}]}
        install(edge,edge['action'])
    for edge in m['patchedSOActions']:
        refine(edge['action']);install(edge,edge['action'])
    for device in ('desktop','mobile'):
        original=next(e for e in so['edges'] if e['source']==device+'-so-withdraw-filled' and e['label']=='Konfirmasi')
        edge=copy.deepcopy(original);edge['originalAction']=copy.deepcopy(original['action'])
        queued=so['fieldModes']['SOQueued'];off=queued['modeForValue']['false']
        def mark(action):
            for block in action.get('blocks',[]):
                expanded=[]
                for child in block['actions']:
                    mark(child);expanded.append(child)
                    if child.get('type')=='setVariableMode' and child.get('collection')==queued['collection'] and child.get('mode')==off:
                        expanded.append({'type':'conditional','blocks':[{'expression':'MIStage == "draft"','actions':[flag(True)]}]})
                block['actions']=expanded
        mark(edge['action']);install(edge,edge['action']);m['patchedSOActions'].append(edge)
    m['stickyWithdrawalGuard']=True
    result=c('command.batch',{'commands':operations})
    if isinstance(result,list):assert not any(isinstance(r,dict) and 'error' in r for r in result),result
    foundation=json.loads((ROOT/'evidence/foundations.json').read_text())
    for bound in m['boundText']:
        if bound['variable']=='MIQueueLabel':api.set(bound['node'],fill={'$var':foundation['variables']['Text']})
    for device in ('desktop','mobile'):
        root=api.ask('node.get',{'id':m['frames'][device+'-maya-blocked'],'depth':1})
        for node in root.get('children',[]):
            if node.get('characters','').startswith('Tindakan memerlukan hak Kasir/Owner'):
                api.set(node['id'],characters='Tindakan tidak sesuai hak akses atau status transaksi. Status invoice dan pembayaran dipertahankan.')
    (ROOT/'evidence/maya-invoice-map.json').write_text(json.dumps(m,indent=2));c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')});c('proto.preview',{'start':m['frames']['desktop-maya-demo']})
    print(json.dumps({'draftStaysStaleAfterRehandoff':True,'scenarioResetsClearStaleness':True,'newStateFields':len(m['fieldModes'])}))
finally:api.close()
