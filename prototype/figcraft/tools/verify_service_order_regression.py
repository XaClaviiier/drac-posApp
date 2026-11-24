"""Check changed completion routing and selected earlier-module journeys."""
import json,time
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
maps={key:json.loads((ROOT/'evidence'/name).read_text()) for key,name in {'so':'service-order-map.json','diag':'diagnosis-map.json','reg':'registration-map.json','cash':'design-completion-map.json'}.items()}
frames={k:v for m in maps.values() for k,v in m['frames'].items()}
api=Native();c=api.command;checks=[]
def start(source):
    c('page.select',{'id':2079 if source.startswith('mobile-') else 1})
    c('proto.preview',{'start':frames[source]});time.sleep(.06)
def follow(edge,target=None):
    api.ask('ui.input',{'events':[{'move':[20,20]}]});time.sleep(.08)
    before=api.ask('ui.inspect')['preview'];assert before['name']==edge['source'],before
    node=api.ask('node.get',{'id':edge['node'],'depth':0})
    api.ask('ui.set',{'presentScroll':[0,min(before['scrollRange'][1],max(0,node['y']-before['frameSize'][1]*.4))]});time.sleep(.06)
    p=api.ask('ui.inspect')['preview'];h=next(h for h in p['hotspots'] if h['id']==edge['node']);r=h['rect'];point=[(r[0]+r[2])/2,(r[1]+r[3])/2]
    for event in ({'move':point},{'down':point},{'up':point}):api.ask('ui.input',{'events':[event]});time.sleep(.065)
    time.sleep(.12);p=api.ask('ui.inspect')['preview']
    expected=target or edge['target'];assert p['name']==expected,(edge,p)
    checks.append({'source':edge['source'],'label':edge.get('label'),'target':expected,'passed':True})
def so(device,label,state):
    source=api.ask('ui.inspect')['preview']['name']
    follow(next(e for e in maps['so']['edges'] if e['source']==source and e['label']==label),device+'-so-'+state)
try:
    for device in ('desktop','mobile'):
        start(device+'-so-hub');so(device,'Selesai sebagai Owner','owner-completed')
        so(device,'Buka kembali pekerjaan','reopen');so(device,'Isi alasan contoh','reopen-filled')
        so(device,'Konfirmasi','running');so(device,'Tandai selesai','complete');so(device,'Konfirmasi','owner-completed')
        start(device+'-so-hub');so(device,'Sedang dikerjakan','running');so(device,'Tandai selesai','complete');so(device,'Konfirmasi','completed')
    role_checks=len(checks)
    cash_routes=[['list','detail','draft','cash','cash-short','cash','paid-cash','list'],['list','detail','draft','cash','qris','qris-checked','paid-qris','list'],['list','detail','draft','cash','transfer','transfer-filled','transfer-checked','paid-transfer','list']]
    reg_routes=[['new','invalid','filled','review','saving'],['known','known-review','known-saving'],['saved','edit','edited','list-edited'],['locked','list']]
    diag_routes=[['approve','approve-ready','approve'],['saved','approve','approve-ready'],['approved','so-review','so-created']]
    for device in ('desktop','mobile'):
        for key,routes,prefix in [('cash',cash_routes,device+'-'),('reg',reg_routes,device+'-reg-'),('diag',diag_routes,device+'-diag-')]:
            for route in routes:
                for a,b in zip(route,route[1:]):
                    start(prefix+a)
                    follow(next(e for e in maps[key]['edges'] if e['source']==prefix+a and e['target']==prefix+b))
        start(device+'-diag-so-created')
        edge=next(e for e in maps['so']['edges'] if e['source']==device+'-diag-so-created' and e['label']=='Kelola Service Order')
        follow(edge,device+'-so-list');so(device,'Buka SO','ready')
    report={'completionRoleChecksPassed':role_checks,'previousModuleChecksPassed':len(checks)-role_checks,'checks':checks,'limits':['selected earlier-module routes only','sample data and native UI actions, not backend tests']}
    (ROOT/'evidence/service-order-regression.json').write_text(json.dumps(report,indent=2))
    start('desktop-so-hub')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
finally:api.close()
