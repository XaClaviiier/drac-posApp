"""Verify the connected Maya journey using native clicks and runtime predicates."""
import ast,json,time,sys
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
maps=[json.loads((ROOT/'evidence'/name).read_text()) for name in ['maya-invoice-map.json','service-order-map.json','diagnosis-map.json','registration-map.json','design-completion-map.json']]
m,so,diag,reg,cash=maps;frames={k:v for data in maps for k,v in data['frames'].items()};edges=[e for data in maps for e in data['edges']]
api=Native();c=api.command;steps=[];predicates=[];screens=[];disabled_checks=[];probes={};probe_ids=[];back_edges=[]
resumed=any(arg in sys.argv for arg in ('--resume-methods','--resume-mobile','--resume-tail'))
if resumed:
    previous=json.loads((ROOT/'evidence/maya-invoice-playback.json').read_text())
    steps=previous['steps'];predicates=previous['predicates'];disabled_checks=previous.get('disabledControls',[])
    screens=previous.get('screenshots',[name for name in ['maya-desktop-pos-160.png','maya-desktop-paid-160.png','maya-desktop-receipt-160.png','maya-desktop-qris-receipt.png'] if (ROOT/'evidence'/name).exists()])
def p():return api.ask('ui.inspect')['preview']
def begin(device,key):
    c('page.select',{'id':2079 if device=='mobile' else 1});c('proto.preview',{'start':frames[device+'-'+key]});time.sleep(.08)
    for _ in range(10):
        current=p()
        if current and current.get('name')==device+'-'+key and current.get('frameSize'):return
        time.sleep(.1)
    raise RuntimeError('FigCraft UI unavailable: restore a visible window before playback')
def click(label,target,wait=0):
    api.ask('ui.input',{'events':[{'move':[20,20]}]});time.sleep(.08)
    before=p();source=before['name'];edge=next(e for e in edges if e['source']==source and e['label']==label)
    n=api.ask('node.get',{'id':edge['node'],'depth':0})
    api.ask('ui.set',{'presentScroll':[0,min(before['scrollRange'][1],max(0,n['y']-before['frameSize'][1]*.4))]});time.sleep(.07)
    h=next(h for h in p()['hotspots'] if h['id']==edge['node']);r=h['rect'];point=[(r[0]+r[2])/2,(r[1]+r[3])/2]
    for event in ({'move':point},{'down':point},{'up':point}):api.ask('ui.input',{'events':[event]});time.sleep(.065)
    time.sleep(.12);after=p();expected=source.split('-')[0]+'-'+target
    assert after['name']==expected,(source,label,expected,after)
    steps.append({'source':source,'label':label,'target':expected,'passed':True})
    if wait:
        time.sleep(1.25);timer=next(t for data in (reg,diag) for t in data.get('timers',[]) if t['source']==expected)
        assert p()['name']==timer['target'],p()
        steps.append({'source':expected,'timerTarget':timer['target'],'passed':True})
    if len(steps)%20==0:checkpoint();print(json.dumps({'stepsPassed':len(steps),'runtimePredicates':len(predicates)}),flush=True)
def checkpoint():
    (ROOT/'evidence/maya-invoice-playback.json').write_text(json.dumps({'steps':steps,'predicates':predicates,'disabledControls':disabled_checks,'screenshots':screens},indent=2))
def assert_state(expression):
    """Preinstalled test hotspots evaluate a predicate in the actual player state.

    No variable modes are assigned by this check. A passing navigation is undone
    with native history. No document edits happen during the journey: the live
    preview reinitializes its state when interaction definitions are edited.
    """
    before=p();source=before['name'];device=source.split('-')[0];marker=device+'-maya-print-info';failure=device+'-maya-blocked'
    assert source!=marker and '-maya-' in source,source
    test={'node':probes[(source,expression)]}
    back=next(e for e in m['edges'] if e['source']==marker and e['label']=='Kembali ke nota')
    def tap(edge):
        api.ask('ui.input',{'events':[{'move':[20,20]}]});time.sleep(.08)
        n=api.ask('node.get',{'id':edge['node'],'depth':0});before=p()
        api.ask('ui.set',{'presentScroll':[0,min(before['scrollRange'][1],max(0,n['y']-before['frameSize'][1]*.4))]});time.sleep(.07)
        h=next(h for h in p()['hotspots'] if h['id']==edge['node']);r=h['rect'];point=[(r[0]+r[2])/2,(r[1]+r[3])/2]
        for event in ({'move':point},{'down':point},{'up':point}):api.ask('ui.input',{'events':[event]});time.sleep(.065)
        time.sleep(.12)
    tap(test)
    assert p()['name']==marker,('Runtime predicate failed',source,expression,p())
    tap(back);retried=False
    if p()['name']==marker:
        time.sleep(.2);tap(back);retried=True
    assert p()['name']==source,p()
    predicates.append({'source':source,'expression':expression,'passed':True,'backPointerRetried':retried})
def install_probes():
    expressions=sorted({n.args[0].value for n in ast.walk(ast.parse(Path(__file__).read_text(encoding='utf-8'))) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='assert_state' and n.args and isinstance(n.args[0],ast.Constant)})
    for source,frame in m['frames'].items():
        device=source.split('-')[0]
        if source.endswith('print-info'):continue
        if '--resume-tail' in sys.argv and (device!='mobile' or source.split('-maya-')[1] not in ('offline','paid','stale')):continue
        for i,expression in enumerate(expressions):
            node=api.node('rectangle',frame,name='__runtime_assert_'+str(i),x=2+i*10,y=65,width=8,height=8,props={'fill':'none'})
            action={'type':'conditional','blocks':[{'expression':expression,'actions':[{'type':'navigate','dest':frames[device+'-maya-print-info']}]},{'actions':[{'type':'navigate','dest':frames[device+'-maya-blocked']}]}]}
            c('proto.interaction.add',{'id':node,'action':action,'transition':{'type':'instant'}});probes[(source,expression)]=node;probe_ids.append(node)
    for device in ('desktop','mobile'):
        edge=next(e for e in m['edges'] if e['source']==device+'-maya-print-info' and e['label']=='Kembali ke nota');back_edges.append(edge)
        c('proto.interaction.clear',{'ids':[edge['node']]});c('proto.interaction.add',{'id':edge['node'],'action':{'type':'back'},'transition':{'type':'instant'}})
    print(json.dumps({'preinstalledRuntimeProbes':len(probe_ids),'uniquePredicates':len(expressions)}),flush=True)
def remove_probes():
    c('proto.closePreview')
    if probe_ids:c('edit.delete',{'ids':probe_ids});probe_ids.clear()
    for edge in back_edges:
        c('proto.interaction.clear',{'ids':[edge['node']]});c('proto.interaction.add',{'id':edge['node'],'action':edge['action'],'transition':{'type':'instant'}})
    back_edges.clear()
def disabled(label):
    root=api.ask('node.get',{'id':p()['current'],'depth':1});n=next(n for n in root['children'] if n.get('name')==label)
    foundation=json.loads((ROOT/'evidence/foundations.json').read_text())
    assert n.get('mainComponent') in [foundation['variants'][kind]['Disabled'] for kind in ('Primary','Secondary')] and not n.get('interactions'),n
    disabled_checks.append({'frame':p()['name'],'label':label,'passed':True})
def capture(name,scroll=0):
    api.ask('ui.set',{'presentScroll':[0,scroll]});time.sleep(.1)
    name='maya-'+p()['name'].split('-')[0]+'-'+name+'.png';api.ask('ui.screenshot',{'path':str(ROOT/'evidence'/name)});screens.append(name)
def make_final(device,total=150000,owner=False,issue=True):
    begin(device,'so-hub');click('Selesai sebagai Owner' if owner else 'Selesai sebagai Teknisi','so-owner-completed' if owner else 'so-completed')
    if total==160000:
        click('Koreksi realisasi (Owner)','so-real-edit');click('Contoh harga Rp60.000','so-real-edit');click('Isi alasan contoh','so-real-edit');click('Periksa dan simpan','so-real-consent');click('Setuju','so-real-consent-ready');click('Simpan realisasi','so-real-view');click('Kembali ke SO','so-owner-completed')
    elif total in (50000,60000):
        click('Koreksi realisasi (Owner)','so-real-edit')
        if total==60000:click('Contoh harga Rp60.000','so-real-edit')
        click('Lepas part','so-real-edit');click('Isi alasan contoh','so-real-edit');click('Periksa dan simpan','so-real-consent' if total==60000 else 'so-real-view')
        if total==60000:click('Setuju','so-real-consent-ready');click('Simpan realisasi','so-real-view')
        click('Kembali ke SO','so-owner-completed')
    click('Serahkan ke kasir','so-handoff');click('Serahkan ke kasir','so-owner-queued' if owner else 'so-queued')
    click('Buka POS sebagai Owner' if owner else 'Demo: buka POS sebagai Kasir','maya-queue')
    click('Buka transaksi','maya-preview');click('Buat invoice draf','maya-draft')
    if issue:click('Tinjau penerbitan','maya-issue');click('Terbitkan invoice','maya-final')
try:
    c('proto.closePreview');install_probes()
    if '--probe' in sys.argv:
        begin('desktop','maya-demo');assert_state('MIStage == "none" and MIPaymentCount == 0');print('Runtime predicate button navigation passed');sys.exit(0)
    for device in ('desktop','mobile'):
        if device=='desktop' and any(arg in sys.argv for arg in ('--resume-mobile','--resume-tail')):continue
        print(json.dumps({'phase':'full connected journey','device':device}),flush=True)
        if not ((resumed and device == "desktop") or '--resume-tail' in sys.argv):
            begin(device,'maya-demo');click('Mulai dari registrasi Maya','reg-new');click('Demo: isi contoh lengkap','reg-filled');click('Periksa registrasi','reg-review');click('Simpan registrasi','reg-saving',wait=1)
            click('Buka Diagnosa','diag-no-diagnosis');click('Demo: journey Teknisi','diag-origin');click('Buat diagnosa','diag-new');click('Demo: isi pemeriksaan','diag-findings');click('Pilih jasa / part','diag-catalog-service');click('Tambahkan item','diag-service');click('Pilih jasa / part','diag-catalog-part');click('Tambahkan item','diag-draft')
            click('Tinjau dan catat persetujuan','diag-approve');click('Setuju','diag-approve-ready');click('Catat persetujuan','diag-approving',wait=1);click('Buat Service Order','diag-so-review');click('Buat Service Order','diag-so-created');click('Kelola Service Order','so-list');click('Buka SO','so-ready')
            click('Pilih Teknisi','so-assign-none');click('Teknisi B','so-assign-b');click('Simpan penugasan','so-assigned');click('Mulai pengerjaan','so-start');click('Konfirmasi','so-running')
            click('Realisasi jasa / part','so-real-empty');click('Salin estimasi untuk diperiksa','so-real-edit');click('Contoh harga Rp60.000','so-real-edit');click('Isi alasan contoh','so-real-edit');click('Periksa dan simpan','so-real-consent');click('Setuju','so-real-consent-ready');click('Simpan realisasi','so-real-view');click('Kembali ke SO','so-running');click('Tandai selesai','so-complete');click('Konfirmasi','so-completed');click('Serahkan ke kasir','so-handoff');click('Serahkan ke kasir','so-queued');click('Demo: buka POS sebagai Kasir','maya-queue')
            assert_state('SOActualTotal == 160000 and MIStage == "none" and not SOFinal and SOTechs == "Teknisi B"');capture('pos-160')
            click('Buka transaksi','maya-preview');assert_state('MIStage == "none"');click('Buat invoice draf','maya-draft');assert_state('MIStage == "draft" and MITotal == 160000 and MIPrice == 60000 and MIHasPart and not SOFinal')
            click('Kembali ke antrean','maya-queue');click('Buka transaksi','maya-draft');assert_state('MIStage == "draft" and MIInvoice == "INV-DEMO-0147" and MIPaymentCount == 0')
            click('Tinjau penerbitan','maya-issue');click('Terbitkan invoice','maya-final');assert_state('SOFinal and MIStage == "final" and MIPaymentCount == 0')
            click('Tunai','maya-cash');disabled('Tinjau pembayaran');click('Isi contoh Rp100.000','maya-cash-short');disabled('Tinjau pembayaran');assert_state('MIReceived == 100000 and MIStage == "final" and MIPaymentCount == 0')
            click('Isi contoh Rp200.000','maya-cash-filled');assert_state('MIChangeText == "Rp40.000"');click('Tinjau pembayaran','maya-confirm-cash');click('Konfirmasi pembayaran','maya-paid')
            assert_state('MIStage == "paid" and MITotal == 160000 and MIDueText == "Rp0" and MIPaymentCount == 1 and SOFinal');capture('paid-160')
            click('Lihat nota','maya-receipt');assert_state('MITotalText == "Rp160.000" and MIPriceText == "Rp60.000" and MIPartText == "Rp100.000" and MIChangeText == "Rp40.000"');capture('receipt-160',300)
            click('Cetak / simpan PDF','maya-print-info');click('Kembali ke nota','maya-receipt');click('Kembali ke detail','maya-paid');click('Kembali ke antrean','maya-empty');click('Lihat riwayat','maya-history');click('Buka kunjungan Maya','maya-history-detail');click('Buka invoice','maya-paid');assert_state('MIPaymentCount == 1 and MIStage == "paid"')
        print(json.dumps({'phase':'methods and guards','device':device}),flush=True)
        if "--resume-tail" not in sys.argv:
            make_final(device)
            click('QRIS','maya-qris');disabled('Tinjau pembayaran');click('Demo: dana masuk diperiksa','maya-qris-checked');click('Transfer bank','maya-transfer');disabled('Tinjau pembayaran');assert_state('not MIChecked and not MIRefValid')
            click('Isi referensi contoh','maya-transfer-filled');click('Demo: dana masuk diperiksa','maya-transfer-checked');click('QRIS','maya-qris');disabled('Tinjau pembayaran');assert_state('not MIChecked and not MIRefValid')
            click('Demo: dana masuk diperiksa','maya-qris-checked');click('Tinjau pembayaran','maya-confirm-qris');click('Konfirmasi pembayaran','maya-paid');assert_state('MIMethod == "QRIS" and MIPaymentCount == 1 and MIReceivedText == "—"');click('Lihat nota','maya-receipt');capture('qris-receipt',400)
            make_final(device,60000,True);assert_state('MITotal == 60000 and not MIHasPart and MIPartQty == "Tidak dipakai"')
            click('Transfer bank','maya-transfer');disabled('Tinjau pembayaran');disabled('Demo: dana masuk diperiksa');click('Isi referensi contoh','maya-transfer-filled');disabled('Tinjau pembayaran');click('Demo: dana masuk diperiksa','maya-transfer-checked');click('Tinjau pembayaran','maya-confirm-transfer');click('Konfirmasi pembayaran','maya-paid');click('Lihat nota','maya-receipt');assert_state('MITotal == 60000 and MIPaymentCount == 1 and MIReceiptRef == "DEMO-MAYA-0147" and MIMethod == "Transfer bank"');capture('transfer-60-receipt',400)
            make_final(device);click('Demo','maya-demo');click('Demo: baca sebagai Teknisi','maya-final');click('Tunai','maya-blocked');assert_state('MIActor == "Teknisi" and MIPaymentCount == 0')
            click('Demo','maya-demo');click('Demo: kembali sebagai Kasir','maya-final');click('Demo','maya-demo');click('Demo: koneksi offline','maya-final');click('Tunai','maya-cash');click('Isi contoh Rp200.000','maya-cash-filled');click('Tinjau pembayaran','maya-offline');assert_state('MIStage == "final" and MIPaymentCount == 0');click('Demo: koneksi pulih','maya-final')
            click('Demo','maya-demo');click('Demo: simpan gagal','maya-final');click('Tunai','maya-cash');click('Isi contoh Rp200.000','maya-cash-filled');click('Tinjau pembayaran','maya-failed');assert_state('MIStage == "final" and MIPaymentCount == 0');click('Demo: periksa status','maya-final')
            click('Demo','maya-demo');click('Demo: hasil pembayaran belum pasti','maya-final');click('QRIS','maya-qris');click('Demo: dana masuk diperiksa','maya-qris-checked');click('Tinjau pembayaran','maya-unknown');assert_state('MIStage == "final" and MIPaymentCount == 0 and MIUnknown');click('Periksa status transaksi','maya-checked-unpaid');click('Demo: status belum tercatat','maya-final');assert_state('not MIUnknown and not MIChecked and not MIRefValid and MIPaymentCount == 0')
        # An offline draft cannot be issued, and creation itself also needs connectivity.
        make_final(device,issue=False);click('Demo','maya-demo');click('Demo: koneksi offline','maya-draft');click('Tinjau penerbitan','maya-offline');assert_state('MIStage == "draft" and not SOFinal and MIPaymentCount == 0');click('Demo: koneksi pulih','maya-draft')
        begin(device,'so-hub');click('Selesai sebagai Teknisi','so-completed');click('Serahkan ke kasir','so-handoff');click('Serahkan ke kasir','so-queued');click('Demo: buka POS sebagai Kasir','maya-queue');click('Buka transaksi','maya-preview');click('Demo','maya-demo');click('Demo: koneksi offline','maya-preview');click('Buat invoice draf','maya-offline');assert_state('MIStage == "none" and not SOFinal and MIPaymentCount == 0');click('Demo: koneksi pulih','maya-preview');click('Buat invoice draf','maya-draft')
        # A zero invoice is paid without a payment record.
        begin(device,'maya-demo');click('Demo: SO Selesai Rp0 (ulang data)','maya-queue');click('Buka transaksi','maya-preview');click('Buat invoice draf','maya-draft');click('Tinjau penerbitan','maya-issue');click('Terbitkan invoice','maya-paid');assert_state('MIStage == "paid" and MITotal == 0 and MIPaymentCount == 0 and MIMethod == "Tanpa pembayaran" and SOFinal');click('Lihat nota','maya-receipt');capture('zero-receipt',350)
        # A withdrawn draft must not be issued or silently refreshed.
        begin(device,'so-hub');click('Selesai sebagai Teknisi','so-completed');click('Serahkan ke kasir','so-handoff');click('Serahkan ke kasir','so-queued');click('Demo: buka POS sebagai Kasir','maya-queue');click('Buka transaksi','maya-preview');click('Buat invoice draf','maya-draft');click('Demo','maya-demo');click('Demo: penyerahan ditarik','maya-draft');click('Tinjau penerbitan','maya-stale');assert_state('MIStage == "draft" and not SOFinal and MITotal == 150000 and MIPaymentCount == 0')
    checkpoint();fonts=c('text.missingFonts');assert not fonts.get('families',[])
    report={'status':'complete','newFrames':len(m['frames']),'nativeStepsPassed':len(steps),'runtimePredicatesPassed':len(predicates),'disabledControlsPassed':disabled_checks,'screenshots':screens,'devices':['desktop','mobile'],'fonts':fonts,'resumedFromPassedCheckpoint':resumed,'resumePhase':'mobile-tail' if '--resume-tail' in sys.argv else 'mobile' if '--resume-mobile' in sys.argv else 'desktop-methods' if resumed else None,'limits':['scripted inputs and native modes','no backend, actual funds or stock','Owner price correction and full customer history deferred','QRIS and bank assets not supplied','print/PDF is a preview']}
    (ROOT/'evidence/maya-invoice-verification.json').write_text(json.dumps(report,indent=2));remove_probes();c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')});begin('desktop','maya-demo')
    print(json.dumps({'stepsPassed':len(steps),'runtimePredicatesPassed':len(predicates),'disabledControlsPassed':len(disabled_checks)}))
finally:
    if '--probe' not in sys.argv:checkpoint()
    if probe_ids or back_edges:remove_probes()
    api.close()
