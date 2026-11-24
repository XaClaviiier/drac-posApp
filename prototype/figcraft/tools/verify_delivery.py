"""Check delivery colors, embedded references and representative native renders."""
import json, hashlib, zipfile
from pathlib import Path
from collections import Counter
from native_api import Native
ROOT = Path(__file__).resolve().parents[1]
m = json.loads((ROOT/'evidence/design-completion-map.json').read_text())
f = json.loads((ROOT/'evidence/foundations.json').read_text())
def luminance(hex):
    rgb = [int(hex[i:i+2],16)/255 for i in (1,3,5)]
    rgb = [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    return sum(a*b for a,b in zip(rgb,(.2126,.7152,.0722)))
def ratio(a,b):
    x,y = sorted((luminance(a),luminance(b)))
    return (y+.05)/(x+.05)
api = Native()
try:
    contrasts = []
    pairs = [('Text','Canvas'),('Text','Surface'),('Muted','Surface'),('OnPrimary','Primary'),('Service','Selected'),('Part','PartSurface'),('Success','SuccessSurface'),('Warning','WarningSurface'),('Error','ErrorSurface')]
    for mode_index,mode in enumerate(('Light','Dark')):
        for fg,bg in pairs:
            value = ratio(f['roles'][fg][mode_index],f['roles'][bg][mode_index])
            assert value >= 4.5,(mode,fg,bg,value)
            contrasts.append({'mode':mode,'foreground':fg,'background':bg,'contrast':round(value,2)})
    captures = []
    for key,mode in [('desktop-paid-transfer','Dark'),('mobile-qris-checked','Dark'),('mobile-zero-draft','Light'),('mobile-print-zero','Dark'),('desktop-catalog','Light')]:
        frame = m['frames'][key]
        api.command('variable.setMode',{'ids':[frame],'collection':f['collection'],'mode':mode})
        try:
            path = ROOT/'evidence'/f'completed-{key}-{mode.lower()}.png'
            api.command('file.export',{'ids':[frame],'format':'png','path':str(path),'scale':1})
            captures.append(path.name)
        finally:
            api.command('variable.setMode',{'ids':[frame],'collection':f['collection'],'mode':None})
    doc = api.ask('document.inspect',{'allPages':True,'depth':5})
    counts = Counter(); fonts = Counter(); image_pages = []
    def walk(n):
        counts[n.get('type','unknown')]+=1
        if n.get('type')=='TEXT': fonts[n.get('fontFamily')]+=1
        for child in n.get('children',[]): walk(child)
    for page in doc['pages']:
        walk(page)
        def image_count(n):
            return sum(1 for paint in n.get('fills',[]) if paint.get('type')=='image')+sum(image_count(c) for c in n.get('children',[]))
        image_pages.append({'name':page['name'],'images':image_count(page)})
    assert all(p['images']==0 for p in image_pages if p['name'] in ('Desktop','Ponsel'))
    (ROOT/'evidence/completed-native-inspection.json').write_text(json.dumps(doc,indent=2))
    api.command('page.select',{'id':1})
    api.command('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    path = ROOT/'pos-kasir.figcraft'
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        assets = [n for n in archive.namelist() if n.startswith('images/')]
        assert len(assets)==2, assets
        assert all(archive.read(name).startswith(b'\x89PNG\r\n\x1a\n') for name in assets)
    report = {'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'pages':[p['name'] for p in doc['pages']],'counts':dict(counts),'fonts':dict(fonts),'imagePages':image_pages,'embeddedPng':assets,'contrastPairs':contrasts,'nativeExports':captures}
    (ROOT/'evidence/completion-delivery.json').write_text(json.dumps(report,indent=2))
    api.command('proto.preview',{'start':m['frames']['desktop-list']})
    print(json.dumps({'pages':report['pages'],'types':report['counts'],'fonts':report['fonts'],'contrastChecks':len(contrasts),'embeddedPng':len(assets),'bytes':report['bytes']}))
finally:
    api.close()
