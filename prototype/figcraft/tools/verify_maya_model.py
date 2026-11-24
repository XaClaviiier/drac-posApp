"""Inspect actual native guard branches without claiming UI playback coverage."""
import json,hashlib
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'evidence/maya-invoice-map.json').read_text());so=json.loads((ROOT/'evidence/service-order-map.json').read_text());fields={**so['fieldModes'],**m['fieldModes']}
api=Native();c=api.command;results=[]
def evaluate(expression,frame):return c('proto.evaluate',{'expr':expression,'id':frame})['value']['value']
def selected(actions,frame,writes):
    for action in actions:
        if action['type']=='navigate':return action['dest']
        if action['type']=='setVariableMode':writes.append(action)
        if action['type']=='conditional':
            for block in action['blocks']:
                if 'condition' not in block or evaluate(block['condition'],frame):
                    dest=selected(block['actions'],frame,writes)
                    if dest is not None:return dest
                    break
    return None
base={'MIActor':'Kasir','MIStage':'draft','MIStale':False,'SOFinal':False,'SOQueued':True,'SOActualSaved':True,'MITotal':150000,'SOActualTotal':150000,'MIPrice':50000,'SOActualPrice':50000,'MIHasPart':True,'SOActualHasPart':True,'MIOffline':False,'MIFail':False,'MIUnknown':False,'MIPaymentCount':0,'SOOwner':False,'SOWriter':True}
try:
    c('proto.closePreview')
    for device in ('desktop','mobile'):
        cases=[
          ('fresh draft','maya-draft','Tinjau penerbitan',{},'maya-issue'),
          ('same money but withdrawn draft','maya-draft','Tinjau penerbitan',{'MIStale':True},'maya-stale'),
          ('offline draft issue','maya-draft','Tinjau penerbitan',{'MIOffline':True},'maya-offline'),
          ('offline draft creation','maya-preview','Buat invoice draf',{'MIStage':'none','MIOffline':True},'maya-offline'),
          ('Technician cannot issue','maya-draft','Tinjau penerbitan',{'MIActor':'Teknisi'},'maya-blocked'),
          ('final cannot be withdrawn','maya-demo','Demo: penyerahan ditarik',{'MIStage':'final','SOFinal':True},'maya-blocked'),
          ('zero invoice goes directly paid','maya-issue','Terbitkan invoice',{'MITotal':0,'SOActualTotal':0,'MIPrice':0,'SOActualPrice':0,'MIHasPart':False,'SOActualHasPart':False},'maya-paid'),
          ('already paid is not charged again','maya-confirm-cash','Konfirmasi pembayaran',{'MIStage':'paid','SOFinal':True,'MIPaymentCount':1},'maya-paid'),
          ('Owner withdrawal selects stale latch','so-withdraw-filled','Konfirmasi',{'SOOwner':True},'so-owner-withdrawn')]
        for name,state,label,changes,target in cases:
            source=device+'-'+state;mapping=so if state.startswith('so-') else m;frame=mapping['frames'][source];edge=next(e for e in mapping['edges'] if e['source']==source and e['label']==label);overrides=[]
            try:
                operations=[]
                for key,value in {**base,**changes}.items():
                    field=fields[key];mode=field['modeForValue'][json.dumps(value,ensure_ascii=False)];overrides.append(field['collection']);operations.append({'command':'variable.setMode','params':{'ids':[frame],'collection':field['collection'],'mode':mode}})
                c('command.batch',{'commands':operations})
                node=api.ask('node.get',{'id':edge['node'],'depth':0});interaction=next(i for i in node['interactions'] if i.get('trigger',{}).get('type','onClick') in ('onClick','click'))
                writes=[];dest=selected(interaction['actions'],frame,writes);expected=(so if target.startswith('so-') else m)['frames'][device+'-'+target]
                assert dest==expected,(name,dest,expected)
                if name=='already paid is not charged again':assert not writes,writes
                if name=='zero invoice goes directly paid':assert any(w['collection']==fields['MIPaymentCount']['collection'] for w in writes),writes
                if name=='Owner withdrawal selects stale latch':assert any(w['collection']==fields['MIStale']['collection'] for w in writes),writes
                results.append({'case':name,'device':device,'selectedTarget':device+'-'+target,'selectedModeActions':writes,'passed':True})
            finally:
                c('command.batch',{'commands':[{'command':'variable.setMode','params':{'ids':[frame],'collection':collection,'mode':None}} for collection in overrides]})
    path=ROOT/'pos-kasir.figcraft';c('page.select',{'id':1});c('file.saveAs',{'path':str(path)})
    report={'kind':'native engine branch selection with explicit document modes','checksPassed':len(results),'checks':results,'uiPlayback':False,'limits':['does not execute pointer input or runtime mode writes','does not replace the remaining GUI journey checks']}
    (ROOT/'evidence/maya-invoice-model-checks.json').write_text(json.dumps(report,indent=2));print(json.dumps({'nativeModelChecksPassed':len(results),'uiPlayback':False,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}))
finally:api.close()
