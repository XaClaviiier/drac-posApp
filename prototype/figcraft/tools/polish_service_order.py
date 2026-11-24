"""Refine per-line consent, pending navigation and the handoff total display."""
import json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
api=Native();c=api.command
m=json.loads((ROOT/'evidence/service-order-map.json').read_text())
f=json.loads((ROOT/'evidence/foundations.json').read_text())
assert not m.get('polished'),'One-time polish already applied'
def go(device,state):return {'type':'navigate','dest':m['frames'][device+'-so-'+state]}
def unconditional(actions):return {'type':'conditional','blocks':[{'actions':actions}]}
def reset_interaction(edge,action):
    c('proto.interaction.clear',{'ids':[edge['node']]});c('proto.interaction.add',{'id':edge['node'],'action':action,'transition':{'type':'instant'}});edge['action']=action
def text(frame,x,y,w,value,size=13,var=None,right=False):
    n=api.node('text',frame,x=x,y=y,width=w,text=value,props={'fontFamily':'Poppins','fontStyle':'Semi Bold' if size>=20 else 'Regular','fontSize':size,'lineHeight':'150%','textAlign':'right' if right else 'left','fill':{'$var':f['variables']['Text']}})
    if var:c('variable.bind',{'ids':[n],'field':'text','variable':m['variables'][var]});m['boundText'].append({'node':n,'variable':var})
    return n
try:
    c('proto.closePreview')
    collection=c('variable.createCollection',{'name':'SO State / SOPendingExit','modes':['Default','list','estimate']})['id']
    variable=c('variable.create',{'collection':collection,'name':'SOPendingExit','type':'string','values':{'Default':'context','list':'list','estimate':'estimate'}})['id']
    m['variables']['SOPendingExit']=variable;m['defaults']['SOPendingExit']='context'
    m['fieldModes']['SOPendingExit']={'collection':collection,'variable':variable,'values':{'Default':'context','list':'list','estimate':'estimate'},'modeForValue':{'"context"':'Default','"list"':'list','"estimate"':'estimate'}}
    def pending(mode):return {'type':'setVariableMode','collection':collection,'mode':mode}
    consent_old='SODraftTotal > SOActualTotal and not SOExtraConsent'
    consent_new='(SODraftPrice > SOActualPrice or (SODraftHasPart and not SOActualHasPart)) and not SOExtraConsent'
    def fix_guard(action):
        for block in action.get('blocks',[]):
            if block.get('expression')==consent_old:block['expression']=consent_new
            for child in block['actions']:fix_guard(child)
    guarded=0
    edit_states={'real-edit','real-consent','real-consent-ready','real-missing','real-invalid','save-error'}
    for edge in m['edges']:
        device=edge['source'].split('-',1)[0]
        state=edge['source'].split('-so-',1)[1] if '-so-' in edge['source'] else ''
        if edge['label'] in ('Periksa dan simpan','Simpan realisasi'):
            fix_guard(edge['action'])
            if 'logicalAction' in edge:fix_guard(edge['logicalAction'])
            reset_interaction(edge,edge['action']);guarded+=1
        if state in edit_states and edge['label'] in ('Service Order','Daftar SO','Estimasi acuan'):
            mode='estimate' if edge['label']=='Estimasi acuan' else 'list'
            reset_interaction(edge,unconditional([pending(mode),go(device,'discard')]))
        elif state=='real-edit' and edge['label']=='Batal':reset_interaction(edge,unconditional([pending('Default'),go(device,'discard')]))
        elif state=='discard' and edge['label']=='Tinggalkan perubahan':
            router=edge['action']
            reset_interaction(edge,{'type':'conditional','blocks':[{'expression':'SOPendingExit == "list"','actions':[go(device,'list')]},{'expression':'SOPendingExit == "estimate"','actions':[go(device,'estimate')]},{'actions':[router]}]})
    for key,frame in m['frames'].items():
        state=key.split('-so-')[1];mobile=key.startswith('mobile-');device=key.split('-')[0]
        if state=='real-edit':
            c('proto.interaction.clear',{'ids':[frame]})
            c('proto.interaction.add',{'id':frame,'trigger':{'type':'keyPress','key':'Escape'},'action':unconditional([pending('Default'),go(device,'discard')]),'transition':{'type':'instant'}})
        if state=='handoff':
            root=api.ask('node.get',{'id':frame,'depth':1});body=258 if mobile else 196
            for n in root.get('children',[]):
                if n.get('name') in ('Serahkan ke kasir','Kembali ke SO') and n['type']=='INSTANCE':api.set(n['id'],y=n['y']+80)
            text(frame,36 if mobile else 252,body+336,318 if mobile else 1144,'Realisasi terakhir yang akan diserahkan',12)
            text(frame,36 if mobile else 252,body+370,318 if mobile else 1144,'Rp150.000',23,'SOActualTotalText',True)
        if state=='invoiced':
            root=api.ask('node.get',{'id':frame,'depth':1})
            for n in root.get('children',[]):
                if n.get('characters','').startswith('Kasir membaca rincian SO. Invoice final'):api.set(n['id'],characters='Invoice final mengunci SO. Koreksi mengikuti alur invoice atau retur.')
    m['polished']=True
    (ROOT/'evidence/service-order-map.json').write_text(json.dumps(m,indent=2))
    c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    c('proto.preview',{'start':m['frames']['desktop-so-hub']})
    print(json.dumps({'perLineConsentGuards':guarded,'pendingNavigationGuarded':True,'handoffTotalVisible':True}))
finally:api.close()
