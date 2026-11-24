"""Give legacy hotspots reusable hover/pressed variants and repair offscreen links."""
import json
from pathlib import Path
from native_api import Native
ROOT = Path(__file__).resolve().parents[1]
api = Native(); c = api.command
m = json.loads((ROOT/'evidence/design-completion-map.json').read_text())
f = json.loads((ROOT/'evidence/foundations.json').read_text())
pages = json.loads((ROOT/'evidence/consolidation.json').read_text())['pages']
assert 'InteractionArea' not in f['variants'], 'One-time migration already applied'
try:
    c('proto.closePreview')
    doc = api.ask('document.inspect', {'allPages': True, 'depth': 5})
    nodes = {}
    def walk(n):
        nodes[n['id']] = n
        for child in n.get('children', []): walk(child)
    for page in doc['pages']: walk(page)
    c('page.select', {'id': f['libraryPage']})
    base = api.node('component', x=1120, y=0, width=220, height=44, name='State=Default', props={'fill':'#00000000','stroke':'#00000000','cornerRadius':8})
    variants = {'Default': base}
    for state in ('Hover','Pressed','Focus','Disabled'):
        n = c('component.addVariant', {'id':base,'property':'State','value':state})['id']
        variants[state] = n
        if state != 'Disabled': api.set(n, stroke={'$var': f['variables']['Primary']}, strokeWeight=2 if state=='Focus' else 1)
    for state, n in variants.items():
        if state=='Disabled': continue
        for trigger, dest in [('mouseEnter','Hover'),('mouseLeave','Default'),('mouseDown','Pressed')]:
            c('proto.interaction.add', {'id':n,'trigger':{'type':trigger},'action':{'type':'changeTo','dest':variants[dest]},'transition':{'type':'instant'}})
    f['variants']['InteractionArea'] = variants; f['buttons']['InteractionArea'] = base
    fixes = []; replacements = {}
    for edge in m['edges']:
        old = edge['node']
        if old in replacements:
            edge['node'] = replacements[old]; continue
        n = nodes[old]
        if n['type'] != 'RECTANGLE': continue
        frame = nodes[m['frames'][edge['source']]]
        x,y = n['x'],n['y']
        if y < 0:
            labels = [ch for ch in frame.get('children',[]) if ch.get('characters') == edge['label']]
            assert labels, ('No visible matching label',edge)
            label = min(labels,key=lambda ch:ch.get('y',99999))
            x,y = max(16,label['x']-12),max(64,label['y']-12)
            fixes.append({'node':old,'source':edge['source'],'oldY':n['y'],'newY':y})
        device = edge['source'].split('-',1)[0]
        c('page.select', {'id':pages['mobile' if device=='mobile' else 'desktop']})
        inst = c('instance.place', {'component':base,'x':frame['x']+x+n['width']/2,'y':frame['y']+y+22})['id']
        c('node.reparent', {'ids':[inst],'parent':frame['id']})
        api.set(inst,x=x,y=y,width=n['width'],height=n['height'],name=n['name'])
        for interaction in n.get('interactions',[]):
            c('proto.interaction.add', {'id':inst,**interaction})
        c('proto.interaction.clear', {'ids':[old]})
        api.set(old,visible=False)
        replacements[old] = inst; edge['node'] = inst; m['instances'].append(inst)
    # Escape returns from additional state screens without issuing a business action.
    for key, frame in m['newFrames'].items():
        device = key.split('-',1)[0]
        c('proto.interaction.add', {'id':frame,'trigger':{'type':'keyPress','key':'Escape'},'dest':m['frames'][device+'-list'],'transition':{'type':'instant'}})
    (ROOT/'evidence/design-completion-map.json').write_text(json.dumps(m,indent=2))
    (ROOT/'evidence/foundations.json').write_text(json.dumps(f,indent=2))
    report = {'replacedHotspots':replacements,'fixedOffscreenLinks':fixes,'mouseUpVariantChangeOmitted':'Installed player consumes onClick when a mouseUp changeTo is present. MouseDown and mouseLeave supply pressed/reset.'}
    (ROOT/'evidence/interaction-polish.json').write_text(json.dumps(report,indent=2))
    c('file.saveAs', {'path':str(ROOT/'pos-kasir.figcraft')})
    print(json.dumps({'reusableInteractionAreas':len(replacements),'offscreenLinksFixed':len(fixes)}))
finally:
    api.close()
