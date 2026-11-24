"""Check unchanged rehandoff staleness and final locks through actual native UI."""
import json,time
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'evidence/maya-invoice-map.json').read_text());so=json.loads((ROOT/'evidence/service-order-map.json').read_text());frames={**m['frames'],**so['frames']};edges=m['edges']+so['edges']
api=Native();c=api.command;probes={};probe_ids=[];back_edges=[];steps=[];checks=[]
expressions={'stale':'MIStale and MIStage == "draft" and SOQueued and not SOFinal and MITotal == 150000 and SOActualTotal == 150000 and MIPaymentCount == 0','draft':'not MIStale and MIStage == "draft" and MIPaymentCount == 0','blocked':'SOFinal and SOQueued and MIStage == "final" and not MIStale and MIPaymentCount == 0'}
def p():return api.ask('ui.inspect')['preview']
def tap(node):
    api.ask('ui.input',{'events':[{'move':[20,20]}]});time.sleep(.08)
    n=api.ask('node.get',{'id':node,'depth':0});before=p();api.ask('ui.set',{'presentScroll':[0,min(before['scrollRange'][1],max(0,n['y']-before['frameSize'][1]*.4))]});time.sleep(.06)
    r=next(h for h in p()['hotspots'] if h['id']==node)['rect'];pt=[(r[0]+r[2])/2,(r[1]+r[3])/2]
    for event in ({'move':pt},{'down':pt},{'up':pt}):api.ask('ui.input',{'events':[event]});time.sleep(.065)
    time.sleep(.12)
def click(label,target):
    before=p();source=before['name'];edge=next(e for e in edges if e['source']==source and e['label']==label);tap(edge['node']);assert p()['name']==source.split('-')[0]+'-'+target,(label,p())
    steps.append({'source':source,'label':label,'target':p()['name'],'passed':True})
def assertion(state):
    source=p()['name'];device=source.split('-')[0];tap(probes[source]);assert p()['name']==device+'-maya-print-info',(expressions[state],p())
    tap(next(e['node'] for e in back_edges if e['source'].startswith(device)));assert p()['name']==source,p();checks.append({'frame':source,'expression':expressions[state],'passed':True})
def draft_from_completed():
    click('Selesai sebagai Teknisi','so-completed');click('Serahkan ke kasir','so-handoff');click('Serahkan ke kasir','so-queued');click('Demo: buka POS sebagai Kasir','maya-queue');click('Buka transaksi','maya-preview');click('Buat invoice draf','maya-draft')
try:
    c('proto.closePreview')
    for device in ('desktop','mobile'):
        for state,expression in expressions.items():
            source=device+'-maya-'+state;node=api.node('rectangle',frames[source],name='__runtime_assert_withdrawal',x=4,y=65,width=8,height=8,props={'fill':'none'});probe_ids.append(node);probes[source]=node
            c('proto.interaction.add',{'id':node,'action':{'type':'conditional','blocks':[{'expression':expression,'actions':[{'type':'navigate','dest':frames[device+'-maya-print-info']}]},{'actions':[{'type':'navigate','dest':frames[device+'-maya-unknown']}]}]},'transition':{'type':'instant'}})
        edge=next(e for e in m['edges'] if e['source']==device+'-maya-print-info' and e['label']=='Kembali ke nota');back_edges.append(edge);c('proto.interaction.clear',{'ids':[edge['node']]});c('proto.interaction.add',{'id':edge['node'],'action':{'type':'back'},'transition':{'type':'instant'}})
    for device in ('desktop','mobile'):
        c('page.select',{'id':2079 if device=='mobile' else 1});c('proto.preview',{'start':frames[device+'-so-hub']});time.sleep(.08);draft_from_completed()
        click('Demo','maya-demo');click('Kembali ke Service Order','so-list');click('Buka SO','so-queued');click('Demo: lanjut sebagai Owner','so-owner-queued');click('Tarik dari antrean','so-withdraw');click('Isi alasan contoh','so-withdraw-filled');click('Konfirmasi','so-owner-withdrawn')
        click('Serahkan ke kasir','so-handoff');click('Serahkan ke kasir','so-owner-queued');click('Buka POS sebagai Owner','maya-queue');click('Buka transaksi','maya-stale');assertion('stale')
        api.ask('ui.screenshot',{'path':str(ROOT/'evidence'/('maya-'+device+'-unchanged-rehandoff-stale.png'))})
        click('Demo','maya-demo');click('Kembali ke Service Order','so-list');click('Demo','so-hub');draft_from_completed();assertion('draft')
        click('Tinjau penerbitan','maya-issue');click('Terbitkan invoice','maya-final');click('Demo','maya-demo');click('Demo: penyerahan ditarik','maya-blocked');assertion('blocked')
        click('Demo','maya-demo');click('Kembali ke Service Order','so-list');click('Buka SO','so-invoiced');click('Demo: buka POS sebagai Kasir','maya-final')
    report={'stepsPassed':len(steps),'runtimePredicatesPassed':len(checks),'steps':steps,'predicates':checks,'cases':['unchanged rehandoff stays stale','explicit demo reset clears staleness','final invoice cannot be withdrawn','SO final lock opens existing invoice']};(ROOT/'evidence/maya-invoice-withdrawal.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['stepsPassed','runtimePredicatesPassed','cases']}))
finally:
    c('proto.closePreview')
    if probe_ids:c('edit.delete',{'ids':probe_ids})
    for edge in back_edges:
        c('proto.interaction.clear',{'ids':[edge['node']]});c('proto.interaction.add',{'id':edge['node'],'action':edge['action'],'transition':{'type':'instant'}})
    c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')});c('proto.preview',{'start':m['frames']['desktop-maya-demo']});api.close()
