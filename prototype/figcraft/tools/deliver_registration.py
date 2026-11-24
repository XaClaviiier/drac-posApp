"""Render the final slice, check embedded assets and save the single native file."""
import json, time, zipfile, hashlib
from pathlib import Path
from collections import Counter
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
api=Native();c=api.command
m=json.loads((ROOT/'evidence/registration-map.json').read_text())
f=json.loads((ROOT/'evidence/foundations.json').read_text())
try:
    exports=[]
    for key,mode in [('desktop-reg-list-saved','Light'),('mobile-reg-list-known','Dark'),('desktop-reg-edited','Light'),('mobile-reg-locked','Dark')]:
        frame=m['frames'][key]; c('variable.setMode',{'ids':[frame],'collection':f['collection'],'mode':mode})
        try:
            name=key+'-'+mode.lower()+'.png'
            c('file.export',{'ids':[frame],'format':'png','path':str(ROOT/'evidence'/name),'scale':1})
            exports.append(name)
        finally:c('variable.setMode',{'ids':[frame],'collection':f['collection'],'mode':None})
    c('page.select',{'id':2079})
    c('proto.preview',{'start':m['frames']['mobile-reg-filled']});time.sleep(.1)
    p=api.ask('ui.inspect')['preview']; root=next(h for h in p['hotspots'] if h['id']==m['frames']['mobile-reg-filled'])
    r=root['rect'];point=[(r[0]+r[2])/2,(r[1]+r[3])/2]
    api.ask('ui.input',{'events':[{'move':point},{'scroll':[0,-900]}]});time.sleep(.3)
    p=api.ask('ui.inspect')['preview'];assert p['scroll'][1]>0,p
    edge=next(e for e in m['edges'] if e['source']=='mobile-reg-filled' and e['target']=='mobile-reg-review')
    assert any(h['id']==edge['node'] for h in p['hotspots']),p
    api.ask('ui.screenshot',{'path':str(ROOT/'evidence/registration-mobile-form-scrolled.png')})
    scroll_proof={'offset':p['scroll'],'range':p['scrollRange'],'primaryButtonVisible':True}
    doc=api.ask('document.inspect',{'allPages':True,'depth':5})
    counts=Counter();fonts=Counter(); image_pages=[]
    def walk(n):
        counts[n.get('type')]+=1
        if n.get('type')=='TEXT':fonts[n.get('fontFamily')]+=1
        return sum(1 for paint in n.get('fills',[]) if paint.get('type')=='image')+sum(walk(ch) for ch in n.get('children',[]))
    for page in doc['pages']:image_pages.append({'name':page['name'],'images':walk(page)})
    assert counts['FRAME']==106,counts
    assert set(fonts)=={'Poppins'},fonts
    assert all(p['images']==0 for p in image_pages if p['name'] in ('Desktop','Ponsel')),image_pages
    assert c('text.missingFonts').get('families',[])==[]
    c('page.select',{'id':1})
    focus=next(n for p in doc['pages'] for n in p.get('children',[]) if n['id']==m['frames']['desktop-reg-filled'])
    c('view.set',{'zoom':.62,'cx':focus['x']+720,'cy':focus['y']+500})
    c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    path=ROOT/'pos-kasir.figcraft'
    prior=json.loads((ROOT/'evidence/consolidation.json').read_text())
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        images=[n for n in archive.namelist() if n.startswith('images/')]
        assert len(images)==2,images
        hashes={hashlib.sha256(archive.read(n)).hexdigest() for n in images}
        assert hashes=={r['sha256'] for r in prior['references']},hashes
    reg=json.loads((ROOT/'evidence/registration-verification.json').read_text())
    cash=json.loads((ROOT/'evidence/completion-verification.json').read_text())
    report={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,
            'pages':[p['name'] for p in doc['pages']],'nodeTypes':dict(counts),'fonts':dict(fonts),
            'imagePages':image_pages,'referenceImageHashes':sorted(hashes),'nativeExports':exports,
            'registrationLinksPassed':reg['linksPassed'],'cashierRegressionLinksPassed':cash['linksPassed'],
            'totalNavigationLinksPassed':reg['linksPassed']+cash['linksPassed'],'realWheelScroll':scroll_proof,
            'limits':['scripted inputs','no backend','no real payment or printer','cashier role only for registration','full keyboard/screen-reader/reflow not verified']}
    (ROOT/'evidence/registration-delivery.json').write_text(json.dumps(report,indent=2))
    (ROOT/'evidence/registration-final-inspection.json').write_text(json.dumps(doc,indent=2))
    c('proto.preview',{'start':m['frames']['desktop-reg-list']})
    print(json.dumps({'frames':counts['FRAME'],'instances':counts['INSTANCE'],'fonts':dict(fonts),'linksPassed':report['totalNavigationLinksPassed'],'referencesPreserved':True,'realWheelScrollPassed':True}))
finally:api.close()
