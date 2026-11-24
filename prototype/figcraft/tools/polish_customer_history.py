"""Add canonical plate keys, saved change metadata and saved-registration guards."""
import json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1];m=json.loads((ROOT/'evidence/customer-history-map.json').read_text());f=json.loads((ROOT/'evidence/foundations.json').read_text());assert not m.get('polished'),'Already applied'
api=Native();c=api.command;operations=[]
try:
    c('proto.closePreview')
    definitions={'CHPlateKey':['DD1248KL','DD2248KL'],'CHDraftKey':['DD2248KL','B1234ABC','DD1248KL'],'CHSavedPlateReason':['Belum ada perubahan','Plat kendaraan berubah; diverifikasi Owner.'],'CHSavedPlateActor':['—','Owner · sesi demo']}
    for name,values in definitions.items():
        names=['Default']+['v'+str(i) for i in range(1,len(values))];collection=c('variable.createCollection',{'name':'Customer history / '+name,'modes':names})['id'];variable=c('variable.create',{'collection':collection,'name':name,'type':'string','values':dict(zip(names,values))})['id'];m['fieldModes'][name]={'collection':collection,'variable':variable,'values':dict(zip(names,values)),'modeForValue':{json.dumps(v,ensure_ascii=False):n for n,v in zip(names,values)}};m['defaults'][name]=values[0]
    def mode(name,value):
        field=m['fieldModes'][name];return {'type':'setVariableMode','collection':field['collection'],'mode':field['modeForValue'][json.dumps(value,ensure_ascii=False)]}
    def go(device,state):return {'type':'navigate','dest':m['frames'][device+'-ch-'+state]}
    watched={m['fieldModes'][n]['collection']:n for n in ('CHPlate','CHPlateDraft','CHPlateChanged')}
    def refine(action):
        for block in action.get('blocks',[]):
            expr=block.get('expression','');expr=expr.replace('CHPlate == "DD 1248 KL"','CHPlateKey == "DD1248KL"').replace('CHPlate == "DD 2248 KL"','CHPlateKey == "DD2248KL"').replace('CHPlateDraft == "B 1234 ABC"','CHDraftKey == "B1234ABC"').replace('CHPlateDraft == CHPlate','CHDraftKey == CHPlateKey')
            if 'expression' in block:block['expression']=expr
            expanded=[]
            for child in block['actions']:
                refine(child);expanded.append(child)
                if child.get('type')=='setVariableMode' and child.get('collection') in watched:
                    name=watched[child['collection']];value=m['fieldModes'][name]['values'][child['mode']]
                    if name in ('CHPlate','CHPlateDraft'):expanded.append(mode('CHPlateKey' if name=='CHPlate' else 'CHDraftKey',value.replace(' ','')))
                    else:expanded.extend([mode('CHSavedPlateReason','Plat kendaraan berubah; diverifikasi Owner.' if value else 'Belum ada perubahan'),mode('CHSavedPlateActor','Owner · sesi demo' if value else '—')])
            block['actions']=expanded
    for edge in m['edges']:
        device=edge['source'].split('-')[0];refine(edge['action'])
        if edge['label']=='Cari telepon 0812 0000 0147':edge['action']={'type':'conditional','blocks':[{'expression':'CHPhone == "0812 0000 0147"','actions':[go(device,'phones')]},{'actions':[go(device,'arif')]}]}
        if edge['label']=='Riwayat perubahan plat':edge['action']={'type':'conditional','blocks':[{'expression':'CHActor == "Owner"','actions':[go(device,'plate-log')]},{'actions':[go(device,'blocked')]}]}
        if edge['source'].endswith('-ch-hub') and edge['label'] in ('Demo: koneksi offline','Demo: simpan gagal'):
            edge['label']='Demo: registrasi offline' if 'offline' in edge['label'] else 'Demo: gagal simpan registrasi'
            api.set(edge['node'],name=edge['label']);c('instance.setProperties',{'ids':[edge['node']],'properties':{'Label':edge['label']}})
        if edge['label']=='Periksa registrasi':edge['action']={'type':'conditional','blocks':[{'expression':'CHNewSaved','actions':[go(device,'saved')]},{'actions':[edge['action']]}]}
        if edge['label']=='Simpan perubahan plat':
            blocks=edge['action']['blocks'];noop=next(b for b in blocks if b.get('expression')=='CHDraftKey == CHPlateKey');blocks.remove(noop);blocks.insert(1,noop)
        operations.extend([{'command':'proto.interaction.clear','params':{'ids':[edge['node']]}},{'command':'proto.interaction.add','params':{'id':edge['node'],'action':edge['action'],'transition':{'type':'instant'}}}])
    for patched in m['patchedHistoryLinks']:
        refine(patched['action']);operations.extend([{'command':'proto.interaction.clear','params':{'ids':[patched['node']]}},{'command':'proto.interaction.add','params':{'id':patched['node'],'action':patched['action'],'transition':{'type':'instant'}}}])
    result=c('command.batch',{'commands':operations});assert not (isinstance(result,list) and any(isinstance(x,dict) and 'error' in x for x in result)),result
    def bound(frame,x,y,w,value,var):
        node=api.node('text',frame,x=x,y=y,width=w,text=value,props={'fontFamily':'Poppins','fontStyle':'Regular','fontSize':12,'lineHeight':'150%','fill':{'$var':f['variables']['Muted']}});c('variable.bind',{'ids':[node],'field':'text','variable':m['fieldModes'][var]['variable']});m['boundText'].append({'node':node,'variable':var})
    for key,frame in m['frames'].items():
        mobile=key.startswith('mobile');body=242 if mobile else 196;x=36 if mobile else 252;w=318 if mobile else 1144
        if key.endswith(('plate-edit','plate-invalid','plate-collision')):
            bound(frame,x,body+210,w,'DD2248KL','CHDraftKey')
            root=api.ask('node.get',{'id':frame,'depth':1})
            for node in root.get('children',[]):
                if node.get('characters')=='Plat baru · hasil normalisasi':api.set(node['id'],characters='Plat baru · tampilan dan kunci pencocokan')
        if key.endswith(('vehicle','vehicle-owner','vehicle-inactive')):bound(frame,x,body+82,w,'DD1248KL','CHPlateKey')
        if key.endswith('plate-log'):
            bound(frame,x,body+384,w,'Belum ada perubahan','CHSavedPlateReason');bound(frame,x,body+424,w,'—','CHSavedPlateActor')
    m['polished']=True;(ROOT/'evidence/customer-history-map.json').write_text(json.dumps(m,indent=2),encoding='utf-8');c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')});c('proto.preview',{'start':m['frames']['desktop-ch-hub']});print(json.dumps({'canonicalPlateKeys':True,'savedPlateMetadata':True,'newRegistrationSnapshotProtected':True,'stateFields':len(m['fieldModes'])}))
finally:api.close()
