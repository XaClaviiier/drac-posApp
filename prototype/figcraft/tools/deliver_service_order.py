"""Export the SO slice and validate the saved combined native document."""
import json,time,zipfile,hashlib
from collections import Counter
from pathlib import Path
from PIL import Image
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'evidence/service-order-map.json').read_text())
f=json.loads((ROOT/'evidence/foundations.json').read_text())
api=Native();c=api.command;exports=[];screens=[]
def preview():return api.ask('ui.inspect')['preview']
def click(node):
    n=api.ask('node.get',{'id':node,'depth':0});p=preview()
    api.ask('ui.set',{'presentScroll':[0,min(p['scrollRange'][1],max(0,n['y']-p['frameSize'][1]*.4))]});time.sleep(.08)
    p=preview();h=next(h for h in p['hotspots'] if h['id']==node);r=h['rect'];point=[(r[0]+r[2])/2,(r[1]+r[3])/2]
    for event in ({'move':point},{'down':point},{'up':point}):api.ask('ui.input',{'events':[event]});time.sleep(.04)
    time.sleep(.08)
def follow(label,target):
    source=preview()['name'];edge=next(e for e in m['edges'] if e['source']==source and e['label']==label)
    click(edge['node']);assert preview()['name']==target,(label,preview())
def shot(name):
    api.ask('ui.screenshot',{'path':str(ROOT/'evidence'/name)});screens.append(name)
try:
    c('proto.closePreview')
    running={'SOStatus':'Dalam Pengerjaan','SOActualPrice':60000,'SOActualPriceText':'Rp60.000','SOActualTotal':160000,'SOActualTotalText':'Rp160.000'}
    owner={**running,'SOActor':'Owner','SOOwner':True,'SOStatus':'Selesai','SOQueued':True}
    draft={**running,'SODraftPrice':60000,'SODraftPriceText':'Rp60.000','SODraftHasPart':False,'SODraftPartText':'Rp0','SODraftPartQty':'Tidak dipakai','SODraftTotal':60000,'SODraftTotalText':'Rp60.000'}
    variants=[('desktop-so-running','Light',running),('mobile-so-running','Light',running),('desktop-so-real-edit','Light',draft),('mobile-so-real-edit','Light',draft),('desktop-so-owner-queued','Dark',owner),('mobile-so-owner-queued','Dark',owner),('desktop-so-assign-two','Light',{}),('mobile-so-real-consent-ready','Dark',{'SODraftPriceText':'Rp60.000','SODraftTotalText':'Rp160.000','SOExtraConsent':True})]
    for key,theme,values in variants:
        frame=m['frames'][key];overridden=[]
        try:
            c('variable.setMode',{'ids':[frame],'collection':f['collection'],'mode':theme});overridden.append(f['collection'])
            for name,value in values.items():
                field=m['fieldModes'][name];mode=field['modeForValue'][json.dumps(value,ensure_ascii=False)]
                c('variable.setMode',{'ids':[frame],'collection':field['collection'],'mode':mode});overridden.append(field['collection'])
            name=key+'-'+theme.lower()+'.png';c('file.export',{'ids':[frame],'format':'png','path':str(ROOT/'evidence'/name),'scale':1});exports.append(name)
        finally:
            for collection in overridden:c('variable.setMode',{'ids':[frame],'collection':collection,'mode':None})
    c('page.select',{'id':2079});c('proto.preview',{'start':m['frames']['mobile-so-hub']});time.sleep(.12)
    follow('Realisasi Rp150.000','mobile-so-running');follow('Realisasi jasa / part','mobile-so-real-edit')
    api.ask('ui.set',{'presentScroll':[0,0]});time.sleep(.1)
    p=preview();root=next(h for h in p['hotspots'] if h['id']==p['current']);r=root['rect'];point=[(r[0]+r[2])/2,(r[1]+r[3])/2]
    api.ask('ui.input',{'events':[{'move':point},{'scroll':[0,-3000]}]});time.sleep(.25)
    p=preview();assert p['scroll'][1]>0,p
    wheel={'scroll':p['scroll'],'range':p['scrollRange'],'passed':True}
    shot('service-order-mobile-real-edit-wheel.png')
    follow('Isi alasan contoh','mobile-so-real-edit');follow('Periksa dan simpan','mobile-so-real-view')
    wheel['scrolledControlsClickedAndSaved']=True
    themes=[]
    for device in ('desktop','mobile'):
        c('page.select',{'id':2079 if device=='mobile' else 1});source=device+'-so-hub'
        c('proto.preview',{'start':m['frames'][source]});time.sleep(.1)
        follow('Realisasi Rp150.000',device+'-so-running');counts=[]
        source=device+'-so-running'
        for i in range(3):
            name=f'service-order-{device}-theme-final-{i}.png';shot(name)
            counts.append(Counter(Image.open(ROOT/'evidence'/name).get_flattened_data())[(9,9,11,255)])
            if i<2:click(m['themeControls'][source])
        assert counts[1]>counts[0]+1000 and abs(counts[2]-counts[0])<100,(device,counts)
        themes.append({'device':device,'darkPixelCounts':counts,'passed':True})
    doc=api.ask('document.inspect',{'allPages':True,'depth':4});types=Counter();fonts=Counter();images=[]
    def walk(n):
        types[n.get('type')]+=1
        if n.get('type')=='TEXT':fonts[n.get('fontFamily')]+=1
        return sum(1 for fill in n.get('fills',[]) if fill.get('type')=='image')+sum(walk(ch) for ch in n.get('children',[]))
    for page in doc['pages']:images.append({'page':page['name'],'count':walk(page)})
    assert types['FRAME']==302 and types['COMPONENT']==19 and types['COMPONENT_SET']==3,types
    assert set(fonts)=={'Poppins'},fonts
    assert all(p['count']==0 for p in images if p['page'] in ('Desktop','Ponsel')),images
    assert not c('text.missingFonts').get('families',[])
    c('proto.closePreview');c('page.select',{'id':1})
    frame=next(n for p in doc['pages'] for n in p.get('children',[]) if n['id']==m['frames']['desktop-so-hub'])
    c('view.set',{'zoom':.62,'cx':frame['x']+720,'cy':frame['y']+500})
    path=ROOT/'pos-kasir.figcraft';c('file.saveAs',{'path':str(path)})
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        reference_hashes={hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist() if name.startswith('images/')}
        original=json.loads((ROOT/'evidence/consolidation.json').read_text());assert reference_hashes=={r['sha256'] for r in original['references']}
    verification=json.loads((ROOT/'evidence/service-order-verification.json').read_text())
    regression=json.loads((ROOT/'evidence/service-order-regression.json').read_text())
    report={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'pages':[p['name'] for p in doc['pages']],'nodeTypes':dict(types),'fonts':dict(fonts),'imagePages':images,'referenceImageHashes':sorted(reference_hashes),'newFrames':len(m['frames']),'newControlActions':len(m['edges']),'stateFields':len(m['fieldModes']),'stateImplementation':m['stateImplementation'],'journeyStepsPassed':verification['journeyStepsPassed'],'completionRoleChecksPassed':regression['completionRoleChecksPassed'],'previousModuleChecksPassed':regression['previousModuleChecksPassed'],'realWheelScroll':wheel,'themesPassed':themes,'nativeExports':exports,'screenshots':screens,'limits':verification['limits']+['selected earlier-module regression only','full keyboard/screen-reader/reflow not verified','Owner price history is a sample','no actual stock allocation, payment, printer or Maya invoice journey']}
    (ROOT/'evidence/service-order-delivery.json').write_text(json.dumps(report,indent=2))
    (ROOT/'evidence/service-order-final-inspection.json').write_text(json.dumps(doc,indent=2))
    c('proto.preview',{'start':m['frames']['desktop-so-hub']})
    print(json.dumps({k:report[k] for k in ['newFrames','newControlActions','stateFields','journeyStepsPassed','completionRoleChecksPassed','previousModuleChecksPassed','nodeTypes','realWheelScroll','themesPassed','sha256']}))
finally:api.close()
