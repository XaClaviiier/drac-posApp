"""Export and check the final one-file diagnosis prototype delivery."""
import json,time,zipfile,hashlib
from pathlib import Path
from collections import Counter
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
api=Native();c=api.command
m=json.loads((ROOT/'evidence/diagnosis-map.json').read_text())
f=json.loads((ROOT/'evidence/foundations.json').read_text())
try:
    exported=[]
    for key,mode in [('desktop-diag-draft','Light'),('mobile-diag-draft','Light'),('desktop-diag-approve-ready','Dark'),('mobile-diag-readonly','Dark'),('desktop-diag-single-approved','Light'),('desktop-diag-owner-log','Dark'),('desktop-diag-price-so-created','Light'),('mobile-diag-origin','Light')]:
        frame=m['frames'][key]
        c('variable.setMode',{'ids':[frame],'collection':f['collection'],'mode':mode})
        try:
            name=key+'-'+mode.lower()+'.png'
            c('file.export',{'ids':[frame],'format':'png','path':str(ROOT/'evidence'/name),'scale':1})
            exported.append(name)
        finally:c('variable.setMode',{'ids':[frame],'collection':f['collection'],'mode':None})
    c('page.select',{'id':2079})
    source='mobile-diag-approve-ready';c('proto.preview',{'start':m['frames'][source]});time.sleep(.1)
    p=api.ask('ui.inspect')['preview'];root=next(h for h in p['hotspots'] if h['id']==m['frames'][source])
    r=root['rect'];point=[(r[0]+r[2])/2,(r[1]+r[3])/2]
    api.ask('ui.input',{'events':[{'move':point},{'scroll':[0,-3000]}]});time.sleep(.3)
    p=api.ask('ui.inspect')['preview'];assert p['scroll'][1]>0,p
    edge=next(e for e in m['edges'] if e['source']==source and e['label']=='Catat persetujuan')
    hot=next(h for h in p['hotspots'] if h['id']==edge['node'])
    api.ask('ui.screenshot',{'path':str(ROOT/'evidence/diagnosis-mobile-approval-scrolled.png')})
    r=hot['rect'];point=[(r[0]+r[2])/2,(r[1]+r[3])/2]
    for event in ({'move':point},{'down':point},{'up':point}):api.ask('ui.input',{'events':[event]});time.sleep(.04)
    time.sleep(1.2);assert api.ask('ui.inspect')['preview']['name']=='mobile-diag-approved'
    wheel={'scroll':p['scroll'],'range':p['scrollRange'],'confirmVisible':True,'confirmClickAndTimerPassed':True}
    doc=api.ask('document.inspect',{'allPages':True,'depth':4})
    types=Counter();fonts=Counter();images=[]
    def walk(n):
        types[n.get('type')]+=1
        if n.get('type')=='TEXT':fonts[n.get('fontFamily')]+=1
        return sum(1 for fill in n.get('fills',[]) if fill.get('type')=='image')+sum(walk(ch) for ch in n.get('children',[]))
    for page in doc['pages']:images.append({'page':page['name'],'count':walk(page)})
    assert types['FRAME']==210,types
    assert set(fonts)=={'Poppins'},fonts
    assert all(p['count']==0 for p in images if p['page'] in ('Desktop','Ponsel')),images
    missing=c('text.missingFonts');assert missing.get('families',[])==[],missing
    c('page.select',{'id':1})
    frame=next(n for p in doc['pages'] for n in p.get('children',[]) if n['id']==m['frames']['desktop-diag-draft'])
    c('view.set',{'zoom':.62,'cx':frame['x']+720,'cy':frame['y']+500})
    c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    path=ROOT/'pos-kasir.figcraft'
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        image_paths=[name for name in archive.namelist() if name.startswith('images/')]
        reference_hashes={hashlib.sha256(archive.read(name)).hexdigest() for name in image_paths}
        original=json.loads((ROOT/'evidence/consolidation.json').read_text())
        assert reference_hashes=={r['sha256'] for r in original['references']}
    verification=json.loads((ROOT/'evidence/diagnosis-verification.json').read_text())
    report={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,
            'pages':[p['name'] for p in doc['pages']],'nodeTypes':dict(types),'fonts':dict(fonts),'imagePages':images,
            'referenceImageHashes':sorted(reference_hashes),'newLinksPassed':verification['linksPassed'],
            'regressionSmokeLinksPassed':verification['regressionSmokeLinksPassed'],'realWheelScroll':wheel,'nativeExports':exported,
            'limits':verification['limits']+['full keyboard/screen-reader/reflow not verified','complete Owner editor journey deferred','no real payment, printer or stock reservation']}
    (ROOT/'evidence/diagnosis-delivery.json').write_text(json.dumps(report,indent=2))
    (ROOT/'evidence/diagnosis-final-inspection.json').write_text(json.dumps(doc,indent=2))
    c('proto.preview',{'start':m['frames']['desktop-diag-origin']})
    print(json.dumps({'totalFrames':types['FRAME'],'newFrames':len(m['frames']),'instances':types['INSTANCE'],'fonts':dict(fonts),'newLinksPassed':verification['linksPassed'],'regressionSmokeLinksPassed':verification['regressionSmokeLinksPassed'],'referencesPreserved':True,'realWheelScrollPassed':True}))
finally:api.close()
