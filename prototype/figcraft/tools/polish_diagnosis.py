"""Preserve partial drafts and add a valid one-item approval branch."""
import json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
api=Native();c=api.command
m=json.loads((ROOT/'evidence/diagnosis-map.json').read_text())
f=json.loads((ROOT/'evidence/foundations.json').read_text())
assert not m.get('polished'),'One-time migration already applied'
def text(frame,x,y,w,value,size=12,role='Muted',right=False):
    return api.node('text',frame,x=x,y=y,width=w,text=value,props={'fontFamily':'Poppins','fontSize':size,'fontStyle':'Regular','lineHeight':'150%','fill':{'$var':f['variables'][role]},'textAlign':'right' if right else 'left'})
def edge_set(edge,target):
    c('proto.interaction.clear',{'ids':[edge['node']]})
    c('proto.interaction.add',{'id':edge['node'],'dest':m['frames'][target],'transition':{'type':'instant'}})
    edge['target']=target
try:
    c('proto.closePreview')
    originals=dict(m['frames']);old_edges=list(m['edges']);clones={}
    pairs=[('findings','findings-saved'),('service','service-saved')]+[(name,'single-'+name) for name in ('approve','approve-ready','approving','approved','so-review','so-created','approved-linked')]
    for device in ('desktop','mobile'):
        mobile=device=='mobile';w,h=(390,844) if mobile else (1440,1000)
        c('page.select',{'id':2079 if mobile else 1})
        for i,(original,state) in enumerate(pairs):
            source=device+'-diag-'+original;key=device+'-diag-'+state
            result=c('edit.duplicate',{'ids':[originals[source]],'dx':0,'dy':0,'map':True})
            frame=result['ids'][0]
            api.set(frame,x=(i%4)*(w+64),y=(32+i//4)*(h+100),name=key)
            m['frames'][key]=frame;m['roles'][key]='Teknisi';clones[key]={'source':source,'map':result['map']}
            m['themeControls'][key]=result['map'][str(m['themeControls'][source])]
            root=api.ask('node.get',{'id':frame,'depth':1})
            m['instances'].extend(n['id'] for n in root.get('children',[]) if n['type']=='INSTANCE')
    # Remap copied navigation, including the single-item SO round trip.
    for key,clone in clones.items():
        device=key.split('-',1)[0];state=key.split('-diag-')[1]
        for old in old_edges:
            if old['source']!=clone['source']:continue
            node=clone['map'][str(old['node'])];target=old['target']
            if state.startswith('single-'):
                base=target.split('-diag-',1)[1] if '-diag-' in target else ''
                if base in ('approve','approve-ready','approving','approved','so-review','so-created','approved-linked'):target=device+'-diag-single-'+base
                elif base=='saved':target=device+'-diag-service-saved'
            elif old['label']=='Simpan draf':target=key
            elif old['label']=='Batal':target=device+'-diag-list'
            edge={**old,'source':key,'target':target,'node':node};m['edges'].append(edge)
            edge_set(edge,target)
        frame=m['frames'][key];root=api.ask('node.get',{'id':frame,'depth':1})
        c('proto.interaction.clear',{'ids':[frame]})
        if state=='single-approving':
            target=device+'-diag-single-approved'
            c('proto.interaction.add',{'id':frame,'trigger':{'type':'afterDelay','ms':1000},'dest':m['frames'][target],'transition':{'type':'instant'}})
            m['timers'].append({'source':key,'target':target,'milliseconds':1000})
        else:c('proto.interaction.add',{'id':frame,'trigger':{'type':'keyPress','key':'Escape'},'dest':m['frames'][device+'-diag-list'],'transition':{'type':'instant'}})
        if state in ('findings-saved','service-saved'):
            text(frame,16 if device=='mobile' else 252,232 if device=='mobile' else 168,358 if device=='mobile' else 712,'Draf tersimpan · isian dipertahankan.' if device=='mobile' else 'Draf tersimpan · simulasi. Isian pemeriksaan dipertahankan.',12,'Success')
    for device in ('desktop','mobile'):
        for source_state,target_state in [('findings','findings-saved'),('service','service-saved')]:
            source=device+'-diag-'+source_state
            for edge in m['edges']:
                if edge['source']==source and edge['label']=='Simpan draf':edge_set(edge,device+'-diag-'+target_state)
        for state in ('service','service-saved'):
            key=device+'-diag-'+state;root=api.ask('node.get',{'id':m['frames'][key],'depth':1})
            button=next(n for n in root['children'] if n.get('name')=='Tinjau dan catat persetujuan')
            c('instance.setProperties',{'ids':[button['id']],'properties':{'State':'Default'}})
            edge={'source':key,'target':device+'-diag-single-approve','node':button['id'],'label':'Tinjau dan catat persetujuan'}
            m['edges'].append(edge);edge_set(edge,edge['target'])
    # Remove the second item and shift the copy's lower content up one item row.
    for key,frame in m['frames'].items():
        mobile=key.startswith('mobile-');state=key.split('-diag-')[1]
        root=api.ask('node.get',{'id':frame,'depth':1});children=root.get('children',[])
        if state.startswith('single-'):
            body=258 if mobile else 196
            sy=body+(240 if 'so-' in state else 300 if mobile else 260)
            second_y=sy+(244 if mobile else 202);delta=244 if mobile else 202
            x0=36 if mobile else 252;item_w=318 if mobile else 712
            for n in children:
                if n['type']=='TEXT' and n.get('characters')=='Mencatat persetujuan Rp150.000':api.set(n['id'],characters='Mencatat persetujuan Rp50.000')
                if n['x']>=x0-1 and n['x']+n['width']<=x0+item_w+1 and n['y']>=second_y-1 and n['y']+n['height']<=second_y+(228 if mobile else 186)+1:
                    api.set(n['id'],visible=False)
                elif n['y']>=second_y+delta-1 and (mobile or n['x']<1000):api.set(n['id'],y=n['y']-delta)
                if n['type']=='TEXT' and n.get('characters')=='Rp150.000':api.set(n['id'],characters='Rp50.000')
                if n['type']=='TEXT' and n.get('characters')=='Rp100.000' and n['y']>second_y+(228 if mobile else 186):api.set(n['id'],characters='Rp0')
                if n['type']=='TEXT' and n.get('characters')=='Rp100.000' and not mobile and n['x']>=1000:api.set(n['id'],characters='Rp0')
        # The price editing view focuses on price, and deletion targets only the
        # demonstrated part. Avoid actions that silently drop another line.
        for n in children:
            if n.get('name')!='Hapus' or n['type']!='INSTANCE':continue
            is_price=state in ('price-edit','price-valid')
            has_two=state in ('draft','saved','qty-error')
            first_y=(258+438+8) if mobile else (196+380+8)
            if is_price or (has_two and abs(n['y']-first_y)<1):
                c('proto.interaction.clear',{'ids':[n['id']]});api.set(n['id'],visible=False)
                m['edges']=[e for e in m['edges'] if e['node']!=n['id']]
        if not mobile:
            for n in children:
                if n['type']=='RECTANGLE' and n['x']==1008 and n['y']==196 and n['height'] in (450,460):api.set(n['id'],height=850 if n['height']==450 else 650)
            for n in children:
                if n['type']!='TEXT' or n.get('characters') not in ('Pemeriksaan AC','Filter kabin') or n.get('visible') is False:continue
                iy=n['y']-54
                if not any(b['type']=='RECTANGLE' and b['x']==n['x']-16 and b['y']==iy and b['height']==186 and b.get('visible') is not False for b in children):continue
                if state.startswith('single-') and n['characters']=='Filter kabin':continue
                amount='—' if state=='qty-error' and n['characters']=='Filter kabin' else 'Rp45.000' if state.startswith('price-') and n['characters']=='Pemeriksaan AC' else 'Rp50.000' if n['characters']=='Pemeriksaan AC' else 'Rp100.000'
                text(frame,n['x'],iy+162,680,'Subtotal',12)
                text(frame,n['x'],iy+162,680,amount,13,'Text',True)
        elif state in ('new','invalid','findings','partial','service','draft','saved','qty-error','price-edit','price-valid','findings-saved','service-saved'):
            for n in children:
                if n['type']=='RECTANGLE' and n['x']==16 and n['y']==258 and n['height']>1000:api.set(n['id'],height=n['height']+100)
    m['polished']=True;m['singleItemTotal']=50000
    (ROOT/'evidence/diagnosis-map.json').write_text(json.dumps(m,indent=2))
    c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    for key,mode in [('desktop-diag-draft','Light'),('mobile-diag-draft','Light'),('desktop-diag-approve-ready','Dark'),('mobile-diag-readonly','Dark'),('desktop-diag-single-approved','Light')]:
        frame=m['frames'][key];c('variable.setMode',{'ids':[frame],'collection':f['collection'],'mode':mode})
        try:c('file.export',{'ids':[frame],'format':'png','path':str(ROOT/'evidence'/(key+'-'+mode.lower()+'.png')),'scale':1})
        finally:c('variable.setMode',{'ids':[frame],'collection':f['collection'],'mode':None})
    c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    print(json.dumps({'diagnosisFrames':len(m['frames']),'links':len(m['edges']),'singleItemApprovalBranch':True,'partialDraftValuesPreserved':True}))
finally:api.close()
