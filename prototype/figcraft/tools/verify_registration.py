"""Verify registration identity, guards and actual native presenter navigation."""
import json, time
from pathlib import Path
from collections import Counter
from PIL import Image
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
api=Native(); c=api.command
m=json.loads((ROOT/'evidence/registration-map.json').read_text())
cash=json.loads((ROOT/'evidence/design-completion-map.json').read_text())
foundation=json.loads((ROOT/'evidence/foundations.json').read_text())
pages=json.loads((ROOT/'evidence/consolidation.json').read_text())['pages']
results=[]
def preview(): return api.ask('ui.inspect')['preview']
def click(node):
    p=preview(); hot=next((h for h in p['hotspots'] if h['id']==node),None)
    assert hot,('Missing hotspot',node,p)
    r=hot['rect']; point=[(r[0]+r[2])/2,(r[1]+r[3])/2]
    for event in ({'move':point},{'down':point},{'up':point}):
        api.ask('ui.input',{'events':[event]}); time.sleep(.025)
    time.sleep(.035)
try:
    doc=api.ask('document.inspect',{'allPages':True,'depth':5})
    (ROOT/'evidence/registration-native-inspection.json').write_text(json.dumps(doc,indent=2))
    nodes={}
    def walk(n):
        nodes[n['id']]=n
        for ch in n.get('children',[]): walk(ch)
    for p in doc['pages']: walk(p)
    all_frames={**cash['frames'],**m['frames']}
    assert len(m['frames'])==48
    fixture_checks=[]
    for key,frame in m['frames'].items():
        state=key.split('-reg-',1)[1]
        content='\n'.join(n.get('characters','') for n in nodes[frame].get('children',[]))
        if state in ('review','saved','edit','edited','known','known-review','known-saved','locked'):
            record=m['fixtures']['returning' if state.startswith('known') else 'locked' if state=='locked' else 'corrected' if state in ('edit','edited') else 'new']
            assert record['plate'] in content and record['customer'] in content,(key,record)
            if state not in ('edit','known'): assert record['phone'] in content,key
            fixture_checks.append(key)
        if state in ('invalid','locked','offline','save-error'):
            outs=[e['target'] for e in m['edges'] if e['source']==key]
            assert not any(t.endswith(('-saving','-saved','-edited')) for t in outs),(key,outs)
        if state=='locked':
            button=next(n for n in nodes[frame]['children'] if n.get('name')=='Koreksi registrasi' and n['type']=='INSTANCE')
            assert button['mainComponent']==foundation['variants']['Secondary']['Disabled'],button
            assert not button.get('interactions'),button
    assert m['fixtures']['returning']['vehicleId']==m['fixtures']['locked']['vehicleId']
    assert m['fixtures']['returning']['phone']==m['fixtures']['locked']['phone']
    assert m['fixtures']['returning']['customerId']!=m['fixtures']['locked']['customerId']
    assert m['fixtures']['returning']['reference']!=m['fixtures']['locked']['reference']
    for edge in m['edges']:
        device=edge['source'].split('-',1)[0]
        c('page.select',{'id':pages['mobile' if device=='mobile' else 'desktop']})
        c('proto.preview',{'start':all_frames[edge['source']]});time.sleep(.04)
        if edge.get('historyBack'):
            seed=device+'-reg-filled'
            c('proto.preview',{'start':m['frames'][seed]})
            api.ask('ui.input',{'events':[{'key':'Escape'}]});time.sleep(.08)
            assert preview()['name']==edge['source']
        root=nodes[all_frames[edge['source']]]; n=nodes[edge['node']]
        y=n['absoluteBounds']['y']-root['absoluteBounds']['y']
        if y+n['height']>root['height']*.8:
            api.ask('ui.set',{'presentScroll':[0,min(preview()['scrollRange'][1],max(0,y-root['height']*.4))]});time.sleep(.04)
        click(edge['node'])
        after=preview()
        assert after and after['name']==edge['target'],(edge,after)
        results.append({'source':edge['source'],'target':edge['target'],'node':edge['node'],'passed':True})
        if len(results)%25==0:
            (ROOT/'evidence/registration-playback.json').write_text(json.dumps(results,indent=2))
            print(json.dumps({'registrationLinksPassed':len(results)}),flush=True)
    timer_results=[]
    cancel_results=[]
    for device in ('desktop','mobile'):
        c('page.select',{'id':pages['mobile' if device=='mobile' else 'desktop']})
        for state in ('filled','known','edit'):
            key=device+'-reg-'+state
            c('proto.preview',{'start':m['frames'][key]})
            api.ask('ui.input',{'events':[{'key':'Escape'}]});time.sleep(.1)
            assert preview()['name']==device+'-reg-discard'
            api.ask('ui.input',{'events':[{'key':'Escape'}]});time.sleep(.1)
            assert preview()['name']==key
            cancel_results.append(key)
    for timer in m['timers']:
        device=timer['source'].split('-',1)[0]
        c('page.select',{'id':pages['mobile' if device=='mobile' else 'desktop']})
        c('proto.preview',{'start':m['frames'][timer['source']]})
        time.sleep(1.25)
        assert preview()['name']==timer['target'],timer
        timer_results.append(timer)
    theme_results=[]
    for device in ('desktop','mobile'):
        c('page.select',{'id':pages['mobile' if device=='mobile' else 'desktop']})
        key=device+'-reg-list';c('proto.preview',{'start':m['frames'][key]})
        counts=[]
        for i in range(3):
            path=ROOT/'evidence'/f'registration-{device}-theme-{i}.png'
            api.ask('ui.screenshot',{'path':str(path)})
            counts.append(Counter(Image.open(path).get_flattened_data())[(9,9,11,255)])
            if i<2:click(m['themeControls'][key])
        assert counts[1]>counts[0]+1000 and abs(counts[2]-counts[0])<100,(device,counts)
        theme_results.append({'device':device,'darkCanvasPixelCounts':counts,'passed':True})
        c('proto.preview',{'start':m['frames'][device+'-reg-locked']})
        api.ask('ui.input',{'events':[{'key':'Escape'}]});time.sleep(.1)
        assert preview()['name']==key
    fonts=c('text.missingFonts');assert fonts.get('families',[])==[],fonts
    report={'registrationFrames':len(m['frames']),'linksPassed':len(results),'fixtureChecks':fixture_checks,
            'timersPassed':timer_results,'themesPassed':theme_results,'escapePassed':['desktop','mobile'],
            'guardsPassed':['required-fields','post-SO-lock','offline','save-error','same-vehicle-new-visit','same-phone-separate-customers'],
            'cancelResumesOriginatingForm':cancel_results,'fonts':fonts}
    (ROOT/'evidence/registration-playback.json').write_text(json.dumps(results,indent=2))
    (ROOT/'evidence/registration-verification.json').write_text(json.dumps(report,indent=2))
    c('page.select',{'id':pages['desktop']})
    c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    c('proto.preview',{'start':m['frames']['desktop-reg-list']})
    print(json.dumps({'registrationFrames':len(m['frames']),'linksPassed':len(results),'timersPassed':len(timer_results),'themeRoundTripsPassed':len(theme_results),'fonts':fonts}))
finally:api.close()
