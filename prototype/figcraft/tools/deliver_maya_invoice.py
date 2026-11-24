"""Render and read back the combined native file after the connected journey tests."""
import hashlib,json,time,zipfile,sys
from pathlib import Path
from collections import Counter
from PIL import Image
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'evidence/maya-invoice-map.json').read_text());so=json.loads((ROOT/'evidence/service-order-map.json').read_text());f=json.loads((ROOT/'evidence/foundations.json').read_text())
fields={**so['fieldModes'],**m['fieldModes']};api=Native();c=api.command;exports=[]
prepare='--prepare' in sys.argv
def p():return api.ask('ui.inspect')['preview']
def click(node):
    api.ask('ui.input',{'events':[{'move':[20,20]}]});time.sleep(.08)
    n=api.ask('node.get',{'id':node,'depth':0});before=p();api.ask('ui.set',{'presentScroll':[0,min(before['scrollRange'][1],max(0,n['y']-before['frameSize'][1]*.4))]});time.sleep(.08)
    h=next(h for h in p()['hotspots'] if h['id']==node);r=h['rect'];pt=[(r[0]+r[2])/2,(r[1]+r[3])/2]
    for event in ({'move':pt},{'down':pt},{'up':pt}):api.ask('ui.input',{'events':[event]});time.sleep(.065)
    time.sleep(.12)
try:
    verification={} if prepare else json.loads((ROOT/'evidence/maya-invoice-verification.json').read_text())
    if not prepare:assert verification['status']=='complete' and verification['runtimePredicatesPassed']>30
    regression=json.loads((ROOT/'evidence/service-order-regression.json').read_text())
    withdrawal={} if prepare else json.loads((ROOT/'evidence/maya-invoice-withdrawal.json').read_text())
    if not prepare:assert withdrawal['runtimePredicatesPassed']==6
    c('proto.closePreview')
    actual={'SOStatus':'Selesai','SOQueued':True,'SOActualPrice':60000,'SOActualPriceText':'Rp60.000','SOActualTotal':160000,'SOActualTotalText':'Rp160.000'}
    invoice={**actual,'MIInvoice':'INV-DEMO-0147','MIPrice':60000,'MIPriceText':'Rp60.000','MITotal':160000,'MITotalText':'Rp160.000','MIDueText':'Rp160.000'}
    paid={**invoice,'SOFinal':True,'MIStage':'paid','MIQueueLabel':'Lunas','MIMethod':'Tunai','MIReceived':200000,'MIReceivedText':'Rp200.000','MIChangeText':'Rp40.000','MIDueText':'Rp0','MIPaymentCount':1}
    transfer={**invoice,'MIActor':'Owner','MIStage':'final','MIMethod':'Transfer bank','MIHasPart':False,'MIPartText':'Rp0','MIPartQty':'Tidak dipakai','MITotal':60000,'MITotalText':'Rp60.000','MIDueText':'Rp60.000','MIReference':'DEMO-MAYA-0147','MIRefValid':True,'MIChecked':True}
    variants=[('desktop-maya-queue','Light',actual),('mobile-maya-queue','Light',actual),('desktop-maya-draft','Light',{**invoice,'MIStage':'draft','MIQueueLabel':'Invoice draf'}),('mobile-maya-cash-filled','Light',{**paid,'MIStage':'final','MIDueText':'Rp160.000','MIPaymentCount':0}),('desktop-maya-paid','Dark',paid),('mobile-maya-qris-checked','Dark',{**invoice,'SOFinal':True,'MIStage':'final','MIMethod':'QRIS','MIChecked':True}),('desktop-maya-transfer-checked','Light',transfer),('desktop-maya-receipt','Light',paid),('mobile-maya-receipt','Dark',paid)]
    for key,theme,values in variants:
        frame=m['frames'][key];collections=[]
        try:
            c('variable.setMode',{'ids':[frame],'collection':f['collection'],'mode':theme});collections.append(f['collection'])
            for name,value in values.items():
                field=fields[name];mode=field['modeForValue'][json.dumps(value,ensure_ascii=False)];c('variable.setMode',{'ids':[frame],'collection':field['collection'],'mode':mode});collections.append(field['collection'])
            name=key+'-'+theme.lower()+'.png'
            if '--reuse-exports' not in sys.argv or not (ROOT/'evidence'/name).exists():c('file.export',{'ids':[frame],'format':'png','path':str(ROOT/'evidence'/name),'scale':1})
            exports.append(name)
        finally:
            for collection in collections:c('variable.setMode',{'ids':[frame],'collection':collection,'mode':None})
    themes=[];wheel={"passed":False,"reason":"UI verification pending"}
    if not prepare:
        themes=[]
        for device in ('desktop','mobile'):
            c('page.select',{'id':2079 if device=='mobile' else 1});source=device+'-maya-demo';c('proto.preview',{'start':m['frames'][source]});time.sleep(.1);counts=[]
            for i in range(3):
                name=f'maya-{device}-theme-{i}.png';api.ask('ui.screenshot',{'path':str(ROOT/'evidence'/name)});counts.append(Counter(Image.open(ROOT/'evidence'/name).get_flattened_data())[(9,9,11,255)])
                if i<2:click(m['themeControls'][source])
            assert counts[1]>counts[0]+1000 and abs(counts[2]-counts[0])<100,(device,counts)
            themes.append({'device':device,'darkPixelCounts':counts,'passed':True})
        # Real wheel input on the mobile receipt, with the lower controls clicked.
        c('page.select',{'id':2079});c('proto.preview',{'start':m['frames']['mobile-maya-demo']});time.sleep(.1)
        def follow(label,target):
            edge=next(e for e in m['edges'] if e['source']==p()['name'] and e['label']==label);click(edge['node']);assert p()['name']=='mobile-maya-'+target,(label,p())
        follow('Demo: SO Selesai Rp0 (ulang data)','queue');follow('Buka transaksi','preview');follow('Buat invoice draf','draft');follow('Tinjau penerbitan','issue');follow('Terbitkan invoice','paid');follow('Lihat nota','receipt')
        api.ask('ui.set',{'presentScroll':[0,0]});time.sleep(.1);before=p();root=next(h for h in before['hotspots'] if h['id']==before['current']);r=root['rect'];point=[(r[0]+r[2])/2,(r[1]+r[3])/2]
        api.ask('ui.input',{'events':[{'move':point},{'scroll':[0,-3000]}]});time.sleep(.3);after=p();assert after['scroll'][1]>0,after
        wheel={'scroll':after['scroll'],'range':after['scrollRange'],'passed':True};api.ask('ui.screenshot',{'path':str(ROOT/'evidence/maya-mobile-receipt-wheel.png')});follow('Cetak / simpan PDF','print-info');follow('Kembali ke nota','receipt');wheel['lowerControlsClicked']=True
        c('proto.closePreview')
    doc=api.ask('document.inspect',{'allPages':True,'depth':4,'fields':['name','type','fontFamily','fills','x','y','width','height','mainComponent','boundVariables']})
    types=Counter();fonts=Counter();image_pages=[];probe_names=[]
    def walk(node):
        types[node['type']]+=1
        if node['type']=='TEXT':fonts[node.get('fontFamily')]+=1
        if node.get('name','').startswith('__runtime_assert'):probe_names.append(node['id'])
        return sum(1 for fill in node.get('fills',[]) if fill.get('type')=='image')+sum(walk(ch) for ch in node.get('children',[]))
    for page in doc['pages']:image_pages.append({'page':page['name'],'count':walk(page)})
    assert not probe_names,probe_names
    assert types['FRAME']==360 and types['COMPONENT']==19 and types['COMPONENT_SET']==3,types
    assert set(fonts)=={'Poppins'},fonts
    assert all(page['count']==0 for page in image_pages if page['page'] in ('Desktop','Ponsel')),image_pages
    missing=c('text.missingFonts');assert not missing.get('families',[])
    c('page.select',{'id':1});frame=next(n for page in doc['pages'] for n in page.get('children',[]) if n['id']==m['frames']['desktop-maya-demo'])
    c('view.set',{'zoom':62,'cx':frame['x']+720,'cy':frame['y']+500});path=ROOT/'pos-kasir.figcraft';c('file.saveAs',{'path':str(path)})
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        hashes={hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist() if name.startswith('images/')};original=json.loads((ROOT/'evidence/consolidation.json').read_text());assert hashes=={ref['sha256'] for ref in original['references']}
    report={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'pages':[page['name'] for page in doc['pages']],'nodeTypes':dict(types),'fonts':dict(fonts),'imagePages':image_pages,'referenceImageHashes':sorted(hashes),'newFrames':len(m['frames']),'newControlActions':len(m['edges']),'newStateFields':len(m['fieldModes']),'nativeStepsPassed':verification.get('nativeStepsPassed'),'runtimePredicatesPassed':verification.get('runtimePredicatesPassed'),'disabledControlsPassed':len(verification.get('disabledControlsPassed',[])),'regressionChecksPassed':None if prepare else regression['completionRoleChecksPassed']+regression['previousModuleChecksPassed'],'temporaryTestNodesRemaining':len(probe_names),'realWheelScroll':wheel,'themesPassed':themes,'nativeExports':exports,'limits':verification.get('limits',[])+['keyboard/screen-reader/full reflow not verified','no real invoice writes or real stock movements']}
    report['withdrawalGuardChecks']=None if prepare else {'stepsPassed':withdrawal['stepsPassed'],'runtimePredicatesPassed':withdrawal['runtimePredicatesPassed'],'cases':withdrawal['cases']}
    report['preparationOnly']=prepare
    (ROOT/'evidence'/('maya-invoice-preparation.json' if prepare else 'maya-invoice-delivery.json')).write_text(json.dumps(report,indent=2));(ROOT/'evidence/maya-invoice-final-inspection.json').write_text(json.dumps(doc,indent=2))
    if not prepare:c('proto.preview',{'start':m['frames']['desktop-maya-demo']})
    print(json.dumps({k:report[k] for k in ['newFrames','nodeTypes','nativeStepsPassed','runtimePredicatesPassed','regressionChecksPassed','temporaryTestNodesRemaining','realWheelScroll','sha256']}))
finally:api.close()
