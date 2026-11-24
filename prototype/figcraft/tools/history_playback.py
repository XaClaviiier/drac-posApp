"""Small native playback driver with probes installed before any journey."""
import json,time
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
class Player:
    def __init__(self,maps,probe_specs):
        self.maps=maps;self.main=maps[0];self.frames={k:v for m in maps for k,v in m['frames'].items()};self.edges=[e for m in maps for e in m['edges']];self.api=Native();self.c=self.api.command;self.steps=[];self.checks=[];self.ids=[];self.probes={};self.returns={};self.screens=[];self.disabled_checks=[]
        self.c('proto.closePreview')
        for device in ('desktop','mobile'):
            for state,expressions in probe_specs.items():
                source=device+'-ch-'+state
                for i,expression in enumerate(expressions):
                    n=self.api.node('rectangle',self.frames[source],name='__runtime_assert_history',x=2+i*22,y=65,width=18,height=10,props={'fill':'none'});self.ids.append(n);self.probes[(source,expression)]=n
                    self.c('proto.interaction.add',{'id':n,'action':{'type':'conditional','blocks':[{'expression':expression,'actions':[{'type':'navigate','dest':self.frames[device+'-ch-pending']}]},{'actions':[{'type':'navigate','dest':self.frames[device+'-ch-blocked']}]}]},'transition':{'type':'instant'}})
            n=self.api.node('rectangle',self.frames[device+'-ch-pending'],name='__runtime_assert_history_return',x=2,y=65,width=18,height=10,props={'fill':'none'});self.ids.append(n);self.returns[device]=n;self.c('proto.interaction.add',{'id':n,'action':{'type':'back'},'transition':{'type':'instant'}})
    def p(self):return self.api.ask('ui.inspect')['preview']
    def begin(self,device,source='ch-hub'):
        self.c('page.select',{'id':2079 if device=='mobile' else 1});key=device+'-'+source;self.c('proto.preview',{'start':self.frames[key]})
        for _ in range(12):
            p=self.p()
            if p and p.get('name')==key and p.get('frameSize'):return
            time.sleep(.1)
        raise RuntimeError('FigCraft preview has no geometry; show its window before playback')
    def tap(self,node):
        self.api.ask('ui.input',{'events':[{'move':[20,20]}]});time.sleep(.06);n=self.api.ask('node.get',{'id':node,'depth':0});p=self.p();assert p.get('frameSize'),'Native UI is unavailable'
        desired=min(p['scrollRange'][1],max(0,n['y']-p['frameSize'][1]*.4))
        if abs(p['scroll'][1]-desired)>.5:self.api.ask('ui.set',{'presentScroll':[0,desired]})
        # ui.set acknowledges before the presenter has laid out the new viewport.
        # Wait for its scroll and hotspot geometry before sending pointer input.
        hot=None
        for _ in range(20):
            time.sleep(.1);p=self.p()
            if abs(p['scroll'][1]-desired)<.5:
                hot=next((h for h in p['hotspots'] if h['id']==node),None)
                if hot:break
        if not hot:
            (ROOT/'evidence/customer-history-hotspot-failure.json').write_text(json.dumps({'node':node,'desiredScroll':desired,'preview':p},indent=2),encoding='utf-8')
            raise AssertionError(('Native hotspot unavailable after scrolling',node,p['name']))
        r=hot['rect'];point=[(r[0]+r[2])/2,(r[1]+r[3])/2]
        for event in ({'move':point},{'down':point},{'up':point}):self.api.ask('ui.input',{'events':[event]});time.sleep(.12)
        time.sleep(.16)
    def click(self,label,target):
        before=self.p();source=before['name'];edge=next(e for e in self.edges if e['source']==source and e['label']==label);self.tap(edge['node']);expected=source.split('-')[0]+'-'+target;retried=False
        # A busy native presenter can miss a pointer event. Retry once only when
        # navigation has not started; a wrong destination must still fail.
        if self.p()['name']==source and expected!=source:
            time.sleep(.3);self.tap(edge['node']);retried=True
        assert self.p()['name']==expected,(source,label,expected,self.p()['name']);self.steps.append({'source':source,'label':label,'target':expected,'passed':True,'navigationPointerRetried':retried})
        if len(self.steps)%20==0:self.checkpoint();print(json.dumps({'steps':len(self.steps),'runtimeChecks':len(self.checks)}),flush=True)
    def assertion(self,expression):
        source=self.p()['name'];device=source.split('-')[0];self.tap(self.probes[(source,expression)]);retried=False
        if self.p()['name']==source:
            time.sleep(.3);self.tap(self.probes[(source,expression)]);retried=True
        assert self.p()['name']==device+'-ch-pending',(source,expression,self.p()['name']);self.tap(self.returns[device])
        if self.p()['name']==device+'-ch-pending':time.sleep(.3);self.tap(self.returns[device]);retried=True
        assert self.p()['name']==source,self.p()['name'];self.checks.append({'source':source,'expression':expression,'passed':True,'probePointerRetried':retried})
    def disabled(self,label):
        root=self.api.ask('node.get',{'id':self.p()['current'],'depth':1});n=next(n for n in root['children'] if n.get('name')==label);f=json.loads((ROOT/'evidence/foundations.json').read_text());assert n.get('mainComponent') in (f['variants']['Primary']['Disabled'],f['variants']['Secondary']['Disabled']) and not n.get('interactions'),n;self.disabled_checks.append({'frame':root['name'],'label':label,'passed':True})
    def shot(self,name,scroll=0):
        self.api.ask('ui.set',{'presentScroll':[0,scroll]});time.sleep(.1);name='customer-history-'+self.p()['name'].split('-')[0]+'-'+name+'.png';self.api.ask('ui.screenshot',{'path':str(ROOT/'evidence'/name)});self.screens.append(name)
    def checkpoint(self):
        (ROOT/'evidence/customer-history-playback.json').write_text(json.dumps({'steps':self.steps,'runtimeChecks':self.checks,'disabledControls':self.disabled_checks,'screenshots':self.screens},indent=2),encoding='utf-8')
    def close(self):
        self.checkpoint();self.c('proto.closePreview')
        if self.ids:self.c('edit.delete',{'ids':self.ids})
        self.c('page.select',{'id':1});self.c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')});self.c('proto.preview',{'start':self.frames['desktop-ch-hub']});self.api.close()
