"""Validate diagnosis state guards, amounts and actual presenter interactions."""
import json,time
from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
from collections import Counter
from PIL import Image
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
api=Native();c=api.command
m=json.loads((ROOT/'evidence/diagnosis-map.json').read_text())
reg=json.loads((ROOT/'evidence/registration-map.json').read_text())
cash=json.loads((ROOT/'evidence/design-completion-map.json').read_text())
foundation=json.loads((ROOT/'evidence/foundations.json').read_text())
all_frames={**cash['frames'],**reg['frames'],**m['frames']}
results=[]
def inspect():return api.ask('ui.inspect')['preview']
def begin(source):
    c('page.select',{'id':2079 if source.startswith('mobile-') else 1})
    c('proto.preview',{'start':all_frames[source]});time.sleep(.04)
def click(node):
    p=inspect();h=next((h for h in p['hotspots'] if h['id']==node),None)
    assert h,('Missing hotspot',node,p)
    r=h['rect'];point=[(r[0]+r[2])/2,(r[1]+r[3])/2]
    for event in ({'move':point},{'down':point},{'up':point}):
        api.ask('ui.input',{'events':[event]});time.sleep(.025)
    time.sleep(.04)
def follow(edge,reset=True):
    if reset:begin(edge['source'])
    if edge.get('historyBack'):
        begin(edge['source'].split('-')[0]+'-diag-draft')
        api.ask('ui.input',{'events':[{'key':'Escape'}]});time.sleep(.1)
        assert inspect()['name']==edge['source']
    root=nodes[all_frames[edge['source']]];n=nodes[edge['node']]
    y=n['absoluteBounds']['y']-root['absoluteBounds']['y']
    if y+n['height']>root['height']*.8:
        api.ask('ui.set',{'presentScroll':[0,min(inspect()['scrollRange'][1],max(0,y-root['height']*.4))]});time.sleep(.05)
    click(edge['node']);after=inspect()
    assert after and after['name']==edge['target'],(edge,after)
    return {'source':edge['source'],'target':edge['target'],'node':edge['node'],'passed':True}
try:
    print(json.dumps({'phase':'inspect'}),flush=True)
    doc=api.ask('document.inspect',{'allPages':True,'depth':2,'fields':['name','type','characters','x','y','width','height','absoluteBounds','visible','mainComponent','interactions']})
    (ROOT/'evidence/diagnosis-native-inspection.json').write_text(json.dumps(doc,indent=2))
    nodes={}
    def walk(n):
        nodes[n['id']]=n
        for ch in n.get('children',[]):walk(ch)
    for p in doc['pages']:walk(p)
    assert len(m['frames'])==104
    assert sum(i['subtotal'] for i in m['fixture']['items'])==m['fixture']['total']==150000
    assert m['fixture']['localServicePrice']+100000==m['fixture']['localTotal']==145000
    assert int((Decimal('0.500')*Decimal(200001)).quantize(Decimal('1'),rounding=ROUND_HALF_UP))==m['fixture']['fraction']['subtotal']==100001
    print(json.dumps({'phase':'guards','indexedNodes':len(nodes)}),flush=True)
    checks=[]
    for key,frame in m['frames'].items():
        state=key.split('-diag-')[1];children=nodes[frame].get('children',[])
        visible=[n for n in children if n.get('visible',True)]
        content='\n'.join(n.get('characters','') for n in visible)
        if state not in ('hub','empty','no-results','load-error','discard'):
            assert m['fixture']['plate'] in content and m['fixture']['customer'] in content,key
            assert m['fixture']['reference'] in content,key
        if state in ('approved','so-review','so-created','approved-linked','readonly','price-approved','price-so-review','price-so-created','price-approved-linked','single-approved','single-so-review','single-so-created','single-approved-linked'):
            expected='Rp50.000' if state.startswith('single-') else 'Rp145.000' if state.startswith('price-') else 'Rp150.000'
            assert expected in content,(key,expected)
            if state.startswith(('price-','single-')):assert 'Rp150.000' not in content,key
            if state.startswith('single-'):assert 'Filter kabin' not in content,key
            checks.append(key)
        if state in ('approve','price-approve','single-approve','qty-error','price-edit','no-diagnosis','readonly','conflict','conflict-local','offline'):
            direct=[e for e in m['edges'] if e['source']==key]
            if state in ('approve','price-approve','single-approve'):
                button=next(n for n in children if n.get('name')=='Catat persetujuan')
                assert button['mainComponent']==foundation['variants']['Primary']['Disabled'],button
                assert not button.get('interactions'),button
            if state in ('readonly','no-diagnosis'):
                assert not any(e['label'] in ('Buat diagnosa','Catat persetujuan','Buat Service Order','Simpan draf') for e in direct),key
            if state in ('qty-error','price-edit','conflict','conflict-local','offline'):
                assert not any(e['target'].endswith(('-approving','-so-review','-so-created')) for e in direct),key
        if state in ('findings-saved','service-saved'):
            assert m['fixture']['findings'] in content and m['fixture']['recommendations'] in content,key
        if state.endswith('so-created'):
            assert m['fixture']['order'] in content and 'Belum dimulai' in content,key
            assert not any(n.get('name')=='Buat Service Order' for n in children),key
        if m['roles'][key]!='Owner':assert 'Pelaku / waktu' not in content,key
    print(json.dumps({'phase':'playback','links':len(m['edges'])}),flush=True)
    for edge in m['edges']:
        results.append(follow(edge))
        if len(results)%25==0:
            (ROOT/'evidence/diagnosis-playback.json').write_text(json.dumps(results,indent=2))
            print(json.dumps({'diagnosisLinksPassed':len(results)}),flush=True)
    timer_results=[]
    for timer in m['timers']:
        begin(timer['source']);time.sleep(1.2)
        assert inspect()['name']==timer['target'],timer
        timer_results.append(timer)
    cancel=[]
    for device in ('desktop','mobile'):
        for state in ('findings','draft','price-valid'):
            key=device+'-diag-'+state;begin(key)
            api.ask('ui.input',{'events':[{'key':'Escape'}]});time.sleep(.1)
            assert inspect()['name']==device+'-diag-discard'
            api.ask('ui.input',{'events':[{'key':'Escape'}]});time.sleep(.1)
            assert inspect()['name']==key
            cancel.append(key)
    themes=[]
    for device in ('desktop','mobile'):
        key=device+'-diag-draft';begin(key);counts=[]
        for i in range(3):
            path=ROOT/'evidence'/f'diagnosis-{device}-theme-{i}.png'
            api.ask('ui.screenshot',{'path':str(path)})
            counts.append(Counter(Image.open(path).get_flattened_data())[(9,9,11,255)])
            if i<2:click(m['themeControls'][key])
        assert counts[1]>counts[0]+1000 and abs(counts[2]-counts[0])<100,(device,counts)
        themes.append({'device':device,'darkCanvasPixelCounts':counts,'passed':True})
    regression=[]
    cash_routes=[['list','detail','draft','cash','cash-short','cash','paid-cash','list'],['list','detail','draft','cash','qris','qris-checked','paid-qris','list'],['list','detail','draft','cash','transfer','transfer-filled','transfer-checked','paid-transfer','list']]
    reg_routes=[['new','invalid','filled','review','saving'],['known','known-review','known-saving'],['saved','edit','edited','list-edited'],['locked','list']]
    for device in ('desktop','mobile'):
        for route in cash_routes:
            for a,b in zip(route,route[1:]):regression.append(follow(next(e for e in cash['edges'] if e['source']==device+'-'+a and e['target']==device+'-'+b)))
        for route in reg_routes:
            for a,b in zip(route,route[1:]):regression.append(follow(next(e for e in reg['edges'] if e['source']==device+'-reg-'+a and e['target']==device+'-reg-'+b)))
    fonts=c('text.missingFonts');assert fonts.get('families',[])==[]
    report={'frames':len(m['frames']),'linksPassed':len(results),'amountIdentityChecks':checks,'timersPassed':timer_results,'cancelResumesOrigin':cancel,'themesPassed':themes,'regressionSmokeLinksPassed':len(regression),'regressionSmoke':regression,'fonts':fonts,'limits':['scripted inputs','sample journeys do not globally synchronize state','authorization is a design demonstration','SO progress and realization are deferred']}
    (ROOT/'evidence/diagnosis-playback.json').write_text(json.dumps(results,indent=2))
    (ROOT/'evidence/diagnosis-verification.json').write_text(json.dumps(report,indent=2))
    c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    c('proto.preview',{'start':m['frames']['desktop-diag-origin']})
    print(json.dumps({'diagnosisFrames':len(m['frames']),'linksPassed':len(results),'regressionSmokeLinksPassed':len(regression),'timersPassed':len(timer_results),'fonts':fonts}))
finally:api.close()
