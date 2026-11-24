"""One-time native connection from the Maya SO to invoice, payment and receipt."""
import json,zipfile
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
so=json.loads((ROOT/'evidence/service-order-map.json').read_text())
f=json.loads((ROOT/'evidence/foundations.json').read_text())
reg=json.loads((ROOT/'evidence/registration-map.json').read_text())
diag=json.loads((ROOT/'evidence/diagnosis-map.json').read_text())
api=Native();c=api.command
frames={};positions={};edges=[];themes={};instances=[];bound=[];fields={};patched=[]
states=['queue','preview','draft','issue','final','cash','cash-short','cash-filled','qris','qris-checked','transfer','transfer-filled','transfer-checked','confirm-cash','confirm-qris','confirm-transfer','paid','receipt','print-info','history','history-detail','empty','offline','failed','unknown','checked-unpaid','stale','blocked','demo']
domains={
 'MIStage':['none','draft','final','paid'],'MIActor':['Kasir','Owner','Teknisi'],
 'MIPrice':[50000,60000,0],'MIPriceText':['Rp50.000','Rp60.000','Rp0'],
 'MIHasPart':[True,False],'MIPartText':['Rp100.000','Rp0'],'MIPartQty':['1 pcs','Tidak dipakai'],
 'MITotal':[150000,160000,60000,50000,0],'MITotalText':['Rp150.000','Rp160.000','Rp60.000','Rp50.000','Rp0'],
 'MIInvoice':['Belum dibuat','INV-DEMO-0147'],
 'MIQueueLabel':['SO siap ditagih','Invoice draf','Invoice belum lunas','Lunas'],
 'MIMethod':['Belum dipilih','Tunai','QRIS','Transfer bank','Tanpa pembayaran'],
 'MIReceived':[0,100000,200000],'MIReceivedText':['Belum diisi','Rp100.000','Rp200.000','—'],
 'MIChangeText':['Rp0','Rp40.000','Rp50.000','Rp140.000','Rp150.000'],
 'MIReference':['Belum diisi','DEMO-MAYA-0147'],'MIRefValid':[False,True],'MIChecked':[False,True],
 'MIOffline':[False,True],'MIFail':[False,True],'MIUnknown':[False,True],
 'MIIntent':['issue','pay'],'MIPaymentCount':[0,1],'MIDueText':['Rp150.000','Rp160.000','Rp60.000','Rp50.000','Rp0']}
defaults={name:values[0] for name,values in domains.items()}
allfields={**so['fieldModes'],**fields}
def tag(value):return json.dumps(value,ensure_ascii=False)
def switch(name,value):
    field=allfields[name]
    return {'type':'setVariableMode','collection':field['collection'],'mode':field['modeForValue'][tag(value)]}
def copyv(dest,source):
    return {'type':'conditional','blocks':[{'expression':source+' == '+tag(value),'actions':[switch(dest,value)]} for value in allfields[source]['values'].values() if tag(value) in allfields[dest]['modeForValue']]}
def go(device,state):return {'type':'navigate','dest':frames[device+'-maya-'+state]}
def branch(expression,yes,no):return {'type':'conditional','blocks':[{'expression':expression,'actions':yes},{'actions':no}]}
def wrap(actions):return {'type':'conditional','blocks':[{'actions':actions}]}
def reset():return [switch(name,value) for name,value in defaults.items()]
def allowed():return '(MIActor == "Kasir" or MIActor == "Owner")'
def fresh():return 'SOQueued and SOActualSaved and MITotal == SOActualTotal and MIPrice == SOActualPrice and MIHasPart == SOActualHasPart'
def finance_guard(device,actions,issued=False):
    return {'type':'conditional','blocks':[
      {'expression':'not '+allowed(),'actions':[go(device,'blocked')]},
      {'expression':'MIStage == "paid"','actions':[go(device,'paid')]},
      {'expression':'MIOffline','actions':[go(device,'offline')]},
      {'expression':'MIUnknown','actions':[go(device,'unknown')]},
      {'expression':'MIFail','actions':[go(device,'failed')]},
      {'expression':('SOFinal and MIStage == "final"' if issued else 'not SOFinal and MIStage == "draft" and '+fresh()),'actions':actions},
      {'actions':[go(device,'stale')]}]}
def queue_route(device):
    return branch('MIStage == "paid" or (MIStage == "none" and not SOQueued)',[go(device,'empty')],[go(device,'queue')])
def invoice_route(device):
    return {'type':'conditional','blocks':[{'expression':'MIStage == "paid"','actions':[go(device,'paid')]},{'expression':'MIStage == "final"','actions':[go(device,'final')]},{'expression':'MIStage == "draft"','actions':[branch(fresh(),[go(device,'draft')],[go(device,'stale')])]},{'actions':[go(device,'preview')]}]}
def snapshot():
    return [copyv(dest,source) for dest,source in [('MIPrice','SOActualPrice'),('MIPriceText','SOActualPriceText'),('MIHasPart','SOActualHasPart'),('MIPartText','SOActualPartText'),('MIPartQty','SOActualPartQty'),('MITotal','SOActualTotal'),('MITotalText','SOActualTotalText'),('MIDueText','SOActualTotalText')]]
def color(name):return {'$var':f['variables'][name]}
def text(frame,x,y,w,value,size=14,ink='Text',weight='Regular',var=None,right=False,white=False):
    n=api.node('text',frame,x=x,y=y,width=w,text=value,props={'fontFamily':'Poppins','fontStyle':weight,'fontSize':size,'lineHeight':'150%','textAlign':'right' if right else 'left','fill':'#18181B' if white else color(ink)})
    if var:
        c('variable.bind',{'ids':[n],'field':'text','variable':allfields[var]['variable']});bound.append({'node':n,'variable':var})
    return n
def box(frame,x,y,w,h,fill='Surface',border='Border',r=12):return api.node('rectangle',frame,x=x,y=y,width=w,height=h,props={'fill':color(fill),'stroke':color(border),'cornerRadius':r})
def button(frame,source,x,y,w,label,action=None,kind='Secondary',disabled=False):
    device=source.split('-')[0];c('page.select',{'id':2079 if device=='mobile' else 1});px,py=positions[frame]
    n=c('instance.place',{'component':f['buttons'][kind],'x':px+x+w/2,'y':py+y+22})['id']
    c('node.reparent',{'ids':[n],'parent':frame});api.set(n,x=x,y=y,width=w,height=44,name=label)
    c('instance.setProperties',{'ids':[n],'properties':{'Label':label,**({'State':'Disabled'} if disabled else {})}})
    if action and not disabled:
        action=wrap(action) if isinstance(action,list) else action
        c('proto.interaction.add',{'id':n,'action':action,'transition':{'type':'instant'}})
        edges.append({'source':source,'node':n,'label':label,'action':action})
    instances.append(n);return n
def note(frame,x,y,w,value,ink='Service',fill='Selected',h=96):box(frame,x,y,w,h,fill,fill,8);text(frame,x+16,y+14,w-32,value,13,ink)
def identity(frame,x,y,w,white=False):
    text(frame,x,y,w,'DD 1248 KL · Maya Lestari',18,weight='Semi Bold',white=white)
    text(frame,x,y+36,w,'REG-DEMO-0147 · SO-DEMO-0147',12,'Muted',white=white)
def rows(frame,x,y,w,actual=False,white=False):
    prefix='SOActual' if actual else 'MI'
    text(frame,x,y,w,'Jasa · Pemeriksaan AC',14,'Service',weight='Medium',white=white)
    text(frame,x,y+30,w,'1 pekerjaan',13,'Muted',white=white)
    text(frame,x,y+64,w,'Rp50.000',18,weight='Semi Bold',var=prefix+'PriceText',right=True,white=white)
    text(frame,x,y+118,w,'Part · Filter kabin',14,'Part',weight='Medium',white=white)
    text(frame,x,y+148,w,'1 pcs',13,'Muted',var=prefix+'PartQty',white=white)
    text(frame,x,y+182,w,'Rp100.000',18,weight='Semi Bold',var=prefix+'PartText',right=True,white=white)
    text(frame,x,y+240,w,'Total realisasi' if actual else 'Total invoice',14,weight='Medium',white=white)
    text(frame,x,y+274,w,'Rp150.000',25,weight='Bold',var=prefix+'TotalText',right=True,white=white)
def method_actions(device,method,target):
    return [switch('MIMethod',method),switch('MIChecked',False),switch('MIRefValid',False),switch('MIReference','Belum diisi'),switch('MIReceived',0),switch('MIReceivedText','Belum diisi'),switch('MIChangeText','Rp0'),go(device,target)]
def cash_input(device,received):
    recalcs=[]
    for total in domains['MITotal']:
        if total>0:
            change='Rp'+format(max(0,received-total),',').replace(',','.')
            recalcs.append({'expression':'MITotal == '+str(total),'actions':[switch('MIChangeText',change),go(device,'cash-filled' if received>=total else 'cash-short')]})
    return [switch('MIReceived',received),switch('MIReceivedText','Rp'+format(received,',').replace(',','.')),{'type':'conditional','blocks':recalcs}]
def pay(device,method):
    validation={'Tunai':'MIReceived >= MITotal and MIMethod == "Tunai"','QRIS':'MIChecked and MIMethod == "QRIS"','Transfer bank':'MIChecked and MIRefValid and MIMethod == "Transfer bank"'}[method]
    return finance_guard(device,[branch('MITotal > 0 and '+validation,[switch('MIStage','paid'),switch('MIQueueLabel','Lunas'),switch('MIDueText','Rp0'),switch('MIPaymentCount',1),go(device,'paid')],[go(device,'blocked')])],True)
def save_map():
    (ROOT/'evidence/maya-invoice-map.json').write_text(json.dumps({'frames':frames,'edges':edges,'themeControls':themes,'instances':instances,'boundText':bound,'fieldModes':fields,'defaults':defaults,'patchedSOActions':patched,'states':states,'fixture':{'customer':'Maya Lestari','plate':'DD 1248 KL','registration':'REG-DEMO-0147','estimate':'EST-DEMO-0147','order':'SO-DEMO-0147','invoice':'INV-DEMO-0147'},'stateImplementation':'independent finite-value native modes'},indent=2))
try:
    doc=api.ask('document.inspect',{'allPages':True,'depth':1,'fields':['name','type','x','y']})
    assert not api.ask('ui.inspect')['status']['dirty'],'Save manual edits before construction'
    assert not any(n['name'].startswith(('desktop-maya-','mobile-maya-')) for p in doc['pages'] for n in p.get('children',[])),'Already constructed'
    with zipfile.ZipFile(ROOT/'archive/before-maya-invoice.zip','w',zipfile.ZIP_DEFLATED) as z:z.write(ROOT/'pos-kasir.figcraft','pos-kasir.figcraft')
    c('proto.closePreview')
    for name,values in domains.items():
        modes=['Default']+['v'+str(i) for i in range(1,len(values))]
        collection=c('variable.createCollection',{'name':'Maya invoice / '+name,'modes':modes})['id']
        default=values[0];kind='boolean' if isinstance(default,bool) else 'number' if isinstance(default,(int,float)) else 'string'
        variable=c('variable.create',{'collection':collection,'name':name,'type':kind,'values':dict(zip(modes,values))})['id']
        fields[name]={'collection':collection,'variable':variable,'values':dict(zip(modes,values)),'modeForValue':{tag(value):mode for mode,value in zip(modes,values)}}
    allfields.update(fields)
    for device in ('desktop','mobile'):
        mobile=device=='mobile';w,h=(390,844) if mobile else (1440,1000);c('page.select',{'id':2079 if mobile else 1})
        for i,state in enumerate(states):
            xx=(i%4)*(w+64);yy=(52+i//4)*(h+100)
            frame=api.node('frame',x=xx,y=yy,width=w,height=h,name=device+'-maya-'+state,props={'fill':color('Canvas'),'clip':True,'overflow':'vertical'})
            frames[device+'-maya-'+state]=frame;positions[frame]=(xx,yy)
    save_map()
    for source,frame in frames.items():
        device,state=source.split('-maya-');mobile=device=='mobile';w=390 if mobile else 1440;x=16 if mobile else 232;pw=358 if mobile else 1184;body=242 if mobile else 196;ix=x+20;iw=pw-40
        title={'queue':'Kasir POS','preview':'Periksa Service Order','draft':'Invoice draf','issue':'Terbitkan invoice?','final':'Invoice belum lunas','paid':'Pembayaran lunas','receipt':'Nota pelanggan','print-info':'Cetak atau simpan PDF','history':'Riwayat kunjungan','history-detail':'Rincian kunjungan','empty':'Kasir POS','offline':'Koneksi terputus','failed':'Tindakan belum tersimpan','unknown':'Status pembayaran belum pasti','checked-unpaid':'Pemeriksaan status','stale':'Draf perlu diperiksa','blocked':'Tindakan tidak tersedia','demo':'Skenario invoice Maya'}.get(state,'Pembayaran')
        box(frame,0,0,w,64,r=0);text(frame,16 if mobile else 232,8 if mobile else 18,170,'Bengkel AC',16,weight='Semi Bold');text(frame,16 if mobile else 420,36 if mobile else 22,160,'Kasir',12,'Muted',var='MIActor')
        if not mobile:
            box(frame,0,0,208,1000,r=0);text(frame,24,22,160,'Bengkel AC',18,weight='Semi Bold')
            button(frame,source,16,80,176,'Kasir POS',queue_route(device));button(frame,source,16,136,176,'Riwayat kunjungan',go(device,'history'))
            text(frame,24,918,160,'Data simulasi · Maya',12,'Muted')
        else:
            button(frame,source,16,76,174,'Kasir POS',queue_route(device));button(frame,source,198,76,176,'Riwayat',go(device,'history'))
        button(frame,source,202 if mobile else 1192,8,100 if mobile else 108,'Demo',go(device,'demo'))
        theme=button(frame,source,310 if mobile else 1312,8,64 if mobile else 112,'Tema',{'type':'conditional','blocks':[{'expression':'mode(POS) == "Dark"','actions':[{'type':'setVariableMode','collection':f['collection'],'mode':'Light'}]},{'actions':[{'type':'setVariableMode','collection':f['collection'],'mode':'Dark'}]}]});themes[source]=theme
        text(frame,x,146 if mobile else 88,pw,title,24 if mobile else 28,weight='Semi Bold');text(frame,x,188 if mobile else 136,pw,'Kunjungan Maya · data simulasi',13,'Muted')
        c('proto.interaction.add',{'id':frame,'trigger':{'type':'keyPress','key':'Escape'},'action':queue_route(device),'transition':{'type':'instant'}})
        if state=='queue':
            box(frame,x,body,pw,48,r=8);text(frame,x+16,body+13,pw-32,'Cari plat, pelanggan atau nomor invoice',14,'Muted')
            cardw=pw if mobile else 368;box(frame,x,body+76,cardw,422);cx=x+20;cw=cardw-40
            identity(frame,cx,body+96,cw);text(frame,cx,body+186,cw,'SO siap ditagih',13,'Service',weight='Medium',var='MIQueueLabel')
            text(frame,cx,body+228,cw,'Pemeriksaan AC · 1 pekerjaan',13);text(frame,cx,body+262,cw,'Filter kabin · 1 pcs / tidak dipakai',12,'Muted')
            text(frame,cx,body+310,cw,'Total realisasi',12,'Muted');text(frame,cx,body+336,cw,'Rp150.000',22,weight='Bold',var='SOActualTotalText')
            button(frame,source,cx,body+418,cw,'Buka transaksi',invoice_route(device),kind='Primary')
            text(frame,x,body+532,pw,'Memilih kartu membuka rincian. Invoice dibuat melalui tindakan terpisah.',13,'Muted')
        elif state in ('preview','draft','final','history-detail'):
            panel=pw if mobile else 752;cw=panel-40;box(frame,x,body,panel,1140 if mobile else 1090);identity(frame,ix,body+24,cw)
            text(frame,ix,body+110,cw,'Belum dibuat',13,'Muted',var='MIInvoice')
            text(frame,ix,body+152,cw,'Rincian SO yang diserahkan' if state=='preview' else 'Snapshot invoice kunjungan ini',14,'Service',weight='Semi Bold')
            rows(frame,ix,body+214,cw,actual=state=='preview')
            if state=='preview':
                note(frame,ix,body+556,cw,'Periksa rincian. Membuka halaman ini belum membuat invoice.',h=104 if mobile else 80)
                action=branch('MIStage != "none"',[invoice_route(device)],[branch(allowed()+' and SOQueued and SOActualSaved and not SOFinal and (SOStatus == "Selesai" or (SOStatus == "Dibatalkan" and SOActualTotal > 0))',[*snapshot(),switch('MIStage','draft'),switch('MIInvoice','INV-DEMO-0147'),switch('MIQueueLabel','Invoice draf'),go(device,'draft')],[go(device,'blocked')])])
                button(frame,source,ix,body+700,cw,'Buat invoice draf',action,kind='Primary')
            elif state=='draft':
                note(frame,ix,body+556,cw,'Draf belum menagih pembayaran. Rincian diambil dari realisasi SO; harga hanya dapat dikoreksi Owner.',h=142 if mobile else 104)
                button(frame,source,ix,body+736,cw,'Tinjau penerbitan',finance_guard(device,[go(device,'issue')]),kind='Primary')
                button(frame,source,ix,body+804,cw,'Ubah harga · Owner',disabled=True)
                text(frame,ix,body+870,cw,'Editor koreksi harga Owner dilengkapi pada irisan berikutnya.',12,'Muted')
            elif state=='final':
                note(frame,ix,body+556,cw,'Invoice sudah terbit dan mengunci SO. Pilih metode untuk menerima pembayaran penuh.',h=122 if mobile else 88)
                for i,(label,target) in enumerate([('Tunai','cash'),('QRIS','qris'),('Transfer bank','transfer')]):button(frame,source,ix,body+718+i*68,cw,label,branch('MIStage == "final" and '+allowed(),method_actions(device,label,target),[invoice_route(device)]),kind='Primary' if i==0 else 'Secondary')
            else:
                text(frame,ix,body+566,cw,'Status invoice',13,'Muted');text(frame,ix,body+600,cw,'SO siap ditagih',18,'Success',weight='Semi Bold',var='MIQueueLabel')
                button(frame,source,ix,body+716,cw,'Buka invoice',invoice_route(device),kind='Primary')
            button(frame,source,ix,body+970,cw,'Kembali ke antrean',queue_route(device))
            if not mobile:
                box(frame,1008,body,408,400);text(frame,1032,body+24,360,'Urutan transaksi',18,weight='Semi Bold');text(frame,1032,body+86,360,'1. Periksa SO\n2. Buat draf\n3. Terbitkan invoice\n4. Terima pembayaran\n5. Nota dan riwayat',14)
                text(frame,1032,body+272,360,'Pengeluaran stok mengikuti penerbitan invoice. Pembayaran tidak mengurangi stok kembali.',13,'Muted')
        elif state=='issue':
            box(frame,x,body,pw,780);identity(frame,ix,body+24,iw);text(frame,ix,body+130,iw,'Total yang akan diterbitkan',14);text(frame,ix,body+168,iw,'Rp150.000',25,weight='Bold',var='MITotalText')
            note(frame,ix,body+248,iw,'Setelah terbit, SO terkunci. Pastikan realisasi dan identitas benar. Invoice positif belum Lunas sampai pembayaran penuh diperiksa.',h=172 if mobile else 100)
            actions=[switch('SOFinal',True),branch('MITotal == 0',[switch('MIStage','paid'),switch('MIQueueLabel','Lunas'),switch('MIDueText','Rp0'),switch('MIMethod','Tanpa pembayaran'),switch('MIReceivedText','—'),switch('MIPaymentCount',0),go(device,'paid')],[switch('MIStage','final'),switch('MIQueueLabel','Invoice belum lunas'),go(device,'final')])]
            button(frame,source,ix,body+480,iw,'Terbitkan invoice',finance_guard(device,actions),kind='Primary');button(frame,source,ix,body+548,iw,'Kembali ke draf',go(device,'draft'))
        elif state.startswith(('cash','qris','transfer')):
            box(frame,x,body,pw,1320);identity(frame,ix,body+24,iw);text(frame,ix,body+112,iw,'INV-DEMO-0147 · pembayaran penuh',13,'Muted');text(frame,ix,body+152,iw,'Sisa tagihan',14);text(frame,ix,body+188,iw,'Rp150.000',25,weight='Bold',var='MIDueText')
            for i,(label,target) in enumerate([('Tunai','cash'),('QRIS','qris'),('Transfer bank','transfer')]):button(frame,source,ix+(iw+8)/3*i,body+256,(iw-16)/3,label,method_actions(device,label,target))
            if state.startswith('cash'):
                text(frame,ix,body+340,iw,'Uang diterima',14,weight='Medium');text(frame,ix,body+376,iw,'Belum diisi',23,weight='Semi Bold',var='MIReceivedText')
                button(frame,source,ix,body+438,iw,'Isi contoh Rp100.000',cash_input(device,100000));button(frame,source,ix,body+506,iw,'Isi contoh Rp200.000',cash_input(device,200000))
                text(frame,ix,body+592,iw,'Kembalian',14);text(frame,ix,body+626,iw,'Rp0',23,weight='Semi Bold',var='MIChangeText',right=True)
                if state=='cash-short':note(frame,ix,body+704,iw,'Uang kurang dari sisa tagihan. Invoice belum dapat dilunasi.','Error','ErrorSurface',h=116 if mobile else 80)
                ready=state=='cash-filled';button(frame,source,ix,body+878,iw,'Tinjau pembayaran',finance_guard(device,[branch('MIMethod == "Tunai" and MIReceived >= MITotal',[go(device,'confirm-cash')],[go(device,'cash-short')])],True) if ready else None,kind='Primary',disabled=not ready)
            elif state.startswith('qris'):
                note(frame,ix,body+344,iw,'QRIS milik Owner belum diberikan. Tampilan ini memakai simulasi; tidak ada kode pembayaran yang dapat dipindai.',ink='Warning',fill='WarningSurface',h=168 if mobile else 100)
                text(frame,ix,body+556,iw,'Periksa nominal dan dana masuk sebelum menandai Lunas.',14)
                ready=state=='qris-checked';button(frame,source,ix,body+660,iw,'✓ Dana masuk diperiksa' if ready else 'Demo: dana masuk diperiksa',[switch('MIChecked',not ready),go(device,'qris' if ready else 'qris-checked')])
                button(frame,source,ix,body+878,iw,'Tinjau pembayaran',finance_guard(device,[branch('MIChecked and MIMethod == "QRIS"',[go(device,'confirm-qris')],[go(device,'blocked')])],True) if ready else None,kind='Primary',disabled=not ready)
            else:
                text(frame,ix,body+340,iw,'Tujuan transfer Owner',14,weight='Semi Bold');text(frame,ix,body+382,iw,'Bank: belum diberikan\nNomor rekening: belum diberikan\nAtas nama: belum diberikan',14,'Muted')
                text(frame,ix,body+500,iw,'Referensi transfer',14,weight='Medium');text(frame,ix,body+536,iw,'Belum diisi',14,'Muted',var='MIReference')
                button(frame,source,ix,body+592,iw,'Isi referensi contoh',[switch('MIReference','DEMO-MAYA-0147'),switch('MIRefValid',True),switch('MIChecked',False),go(device,'transfer-filled')])
                filled=state!='transfer';ready=state=='transfer-checked'
                button(frame,source,ix,body+670,iw,'✓ Dana masuk diperiksa' if ready else 'Demo: dana masuk diperiksa',[switch('MIChecked',not ready),go(device,'transfer-filled' if ready else 'transfer-checked')] if filled else None,disabled=not filled)
                text(frame,ix,body+744,iw,'Referensi contoh dan pemeriksaan dana hanya untuk mencoba prototype.',13,'Muted')
                button(frame,source,ix,body+878,iw,'Tinjau pembayaran',finance_guard(device,[branch('MIRefValid and MIChecked and MIMethod == "Transfer bank"',[go(device,'confirm-transfer')],[go(device,'blocked')])],True) if ready else None,kind='Primary',disabled=not ready)
            button(frame,source,ix,body+958,iw,'Kembali ke invoice',invoice_route(device))
        elif state.startswith('confirm-'):
            method={'confirm-cash':'Tunai','confirm-qris':'QRIS','confirm-transfer':'Transfer bank'}[state]
            box(frame,x,body,pw,880);identity(frame,ix,body+24,iw);text(frame,ix,body+132,iw,'INV-DEMO-0147',13,'Muted');text(frame,ix,body+182,iw,'Pembayaran yang akan dicatat',14);text(frame,ix,body+220,iw,'Rp150.000',25,weight='Bold',var='MITotalText')
            text(frame,ix,body+296,iw,'Metode: '+method,15,weight='Medium')
            if method=='Tunai':text(frame,ix,body+344,iw,'Uang diterima',13,'Muted');text(frame,ix,body+376,iw,'Rp200.000',18,var='MIReceivedText',right=True);text(frame,ix,body+424,iw,'Kembalian',13,'Muted');text(frame,ix,body+456,iw,'Rp50.000',18,var='MIChangeText',right=True)
            else:text(frame,ix,body+354,iw,'Dana masuk sudah diperiksa · simulasi',14,'Success');text(frame,ix,body+404,iw,'Referensi transfer' if method=='Transfer bank' else 'QRIS statis milik Owner',13,'Muted');text(frame,ix,body+438,iw,'DEMO-MAYA-0147' if method=='Transfer bank' else 'Aset asli belum tersedia',14,var='MIReference' if method=='Transfer bank' else None)
            button(frame,source,ix,body+596,iw,'Konfirmasi pembayaran',pay(device,method),kind='Primary');button(frame,source,ix,body+664,iw,'Periksa kembali',go(device,{'Tunai':'cash-filled','QRIS':'qris-checked','Transfer bank':'transfer-checked'}[method]))
        elif state=='paid':
            box(frame,x,body,pw,970);identity(frame,ix,body+24,iw);text(frame,ix,body+128,iw,'INV-DEMO-0147',13,'Muted');note(frame,ix,body+178,iw,'Lunas · rincian kunjungan tetap tersedia setelah keluar dari antrean.','Success','SuccessSurface',h=128 if mobile else 88)
            text(frame,ix,body+348,iw,'Total invoice',14);text(frame,ix,body+386,iw,'Rp150.000',25,weight='Bold',var='MITotalText',right=True);text(frame,ix,body+456,iw,'Metode',13,'Muted');text(frame,ix,body+492,iw,'Tunai',18,var='MIMethod');text(frame,ix,body+552,iw,'Sisa tagihan',13,'Muted');text(frame,ix,body+586,iw,'Rp0',22,weight='Semi Bold',var='MIDueText',right=True)
            button(frame,source,ix,body+696,iw,'Lihat nota',go(device,'receipt'),kind='Primary');button(frame,source,ix,body+764,iw,'Riwayat kunjungan',go(device,'history'));button(frame,source,ix,body+832,iw,'Kembali ke antrean',queue_route(device))
        elif state=='receipt':
            rw=pw if mobile else 560;rx=x if mobile else x+160
            api.node('rectangle',frame,x=rx,y=body,width=rw,height=1120,props={'fill':'#FFFFFF','stroke':'#E4E4E7','cornerRadius':8})
            ri=rx+20;ww=rw-40;text(frame,ri,body+24,ww,'Bengkel AC',22,weight='Semi Bold',white=True);text(frame,ri,body+62,ww,'NOTA · DATA SIMULASI',12,white=True);identity(frame,ri,body+110,ww,True)
            text(frame,ri,body+198,ww,'INV-DEMO-0147 · Lunas',14,weight='Semi Bold',white=True);rows(frame,ri,body+260,ww,white=True)
            text(frame,ri,body+610,ww,'Metode pembayaran',13,white=True);text(frame,ri,body+644,ww,'Tunai',16,var='MIMethod',white=True);text(frame,ri,body+700,ww,'Uang diterima / konfirmasi',13,white=True);text(frame,ri,body+736,ww,'Rp200.000',16,var='MIReceivedText',right=True,white=True)
            text(frame,ri,body+790,ww,'Kembalian',13,white=True);text(frame,ri,body+826,ww,'Rp50.000',16,var='MIChangeText',right=True,white=True);text(frame,ri,body+880,ww,'Referensi',13,white=True);text(frame,ri,body+914,ww,'Belum diisi',14,var='MIReference',white=True)
            text(frame,ri,body+984,ww,'Terima kasih. Simpan nota sebagai bukti layanan.',13,white=True)
            button(frame,source,rx,body+1152,rw,'Cetak / simpan PDF',go(device,'print-info'),kind='Primary');button(frame,source,rx,body+1220,rw,'Kembali ke detail',go(device,'paid'))
        elif state in ('history','empty'):
            box(frame,x,body,pw,700)
            if state=='empty':
                text(frame,ix,body+30,iw,'Tidak ada transaksi Maya yang menunggu proses.',18,weight='Semi Bold');text(frame,ix,body+126,iw,'Transaksi lunas dapat dibuka melalui Riwayat. Penyerahan SO yang baru akan muncul di antrean.',14,'Muted');button(frame,source,ix,body+300,iw,'Lihat riwayat',go(device,'history'),kind='Primary')
            else:
                identity(frame,ix,body+30,iw);text(frame,ix,body+128,iw,'Registrasi · Diagnosa · SO · Invoice',14,'Muted');text(frame,ix,body+180,iw,'SO siap ditagih',16,'Service',var='MIQueueLabel');text(frame,ix,body+232,iw,'Belum dibuat',14,var='MIInvoice');text(frame,ix,body+286,iw,'Rp150.000',23,weight='Semi Bold',var='MITotalText');button(frame,source,ix,body+396,iw,'Buka kunjungan Maya',go(device,'history-detail'),kind='Primary')
        elif state in ('offline','failed','unknown','checked-unpaid','stale','blocked','print-info'):
            box(frame,x,body,pw,930);identity(frame,ix,body+24,iw)
            copy={
              'offline':'Invoice dan pembayaran memerlukan koneksi. Data yang sedang ditinjau tetap ada; belum ada tindakan berhasil.',
              'failed':'Tindakan belum tersimpan pada simulasi. Invoice belum dilunasi. Periksa status sebelum mencoba lagi.',
              'unknown':'Hasil pencatatan belum diketahui. Jangan mencatat pembayaran kedua sebelum status diperiksa.',
              'checked-unpaid':'Contoh hasil pemeriksaan: pembayaran belum tercatat. Dana dan referensi perlu diperiksa kembali sebelum mencoba.',
              'stale':'Penyerahan SO sudah ditarik atau rincian berubah. Draf lama dipertahankan dan tidak boleh diterbitkan. Owner perlu memeriksa realisasi dan penyerahan kembali.',
              'blocked':'Tindakan memerlukan hak Kasir/Owner dan kondisi transaksi yang sesuai. Belum ada pembayaran dicatat.',
              'print-info':'Ini pratinjau nota untuk cetak atau PDF. Prototype belum terhubung ke dialog cetak, ekspor PDF aplikasi, atau printer fisik.'}[state]
            note(frame,ix,body+140,iw,copy,'Warning','WarningSurface',h=232 if mobile else 144)
            if state=='offline':button(frame,source,ix,body+444,iw,'Demo: koneksi pulih',[switch('MIOffline',False),invoice_route(device)],kind='Primary')
            elif state=='unknown':button(frame,source,ix,body+444,iw,'Periksa status transaksi',go(device,'checked-unpaid'),kind='Primary')
            elif state=='checked-unpaid':button(frame,source,ix,body+444,iw,'Demo: status belum tercatat',[switch('MIUnknown',False),switch('MIChecked',False),switch('MIRefValid',False),switch('MIReference','Belum diisi'),switch('MIReceived',0),switch('MIReceivedText','Belum diisi'),switch('MIChangeText','Rp0'),go(device,'final')],kind='Primary')
            elif state=='failed':button(frame,source,ix,body+444,iw,'Demo: periksa status',[switch('MIFail',False),invoice_route(device)],kind='Primary')
            elif state=='stale':button(frame,source,ix,body+444,iw,'Demo: tinjau sebagai Owner',[switch('SOOwner',True),switch('SOActor','Owner'),switch('SOWriter',True),{'type':'navigate','dest':so['frames'][device+'-so-list']}],kind='Primary')
            elif state=='print-info':button(frame,source,ix,body+444,iw,'Kembali ke nota',go(device,'receipt'),kind='Primary')
            else:button(frame,source,ix,body+444,iw,'Kembali ke transaksi',invoice_route(device),kind='Primary')
            button(frame,source,ix,body+530,iw,'Kembali ke antrean',queue_route(device))
        elif state=='demo':
            box(frame,x,body,pw,1220);text(frame,ix,body+24,iw,'Pilihan berikut mengubah kondisi demo transaksi ini.',14,'Muted')
            examples=[('Mulai dari registrasi Maya',[*reset(),*[switch(n,v) for n,v in so['defaults'].items()],{'type':'navigate','dest':reg['frames'][device+'-reg-new']}]),
             ('Buka transaksi Maya',[invoice_route(device)]),
             ('Demo: koneksi offline',[switch('MIOffline',True),go(device,'final')]),
             ('Demo: simpan gagal',[switch('MIFail',True),go(device,'final')]),
             ('Demo: hasil pembayaran belum pasti',[switch('MIUnknown',True),go(device,'final')]),
             ('Demo: baca sebagai Teknisi',[switch('MIActor','Teknisi'),go(device,'final')]),
             ('Demo: kembali sebagai Kasir',[switch('MIActor','Kasir'),invoice_route(device)]),
             ('Demo: penyerahan ditarik',[switch('SOQueued',False),go(device,'draft')]),
             ('Kembali ke Service Order',[{'type':'navigate','dest':so['frames'][device+'-so-list']}])]
            for i,(label,action) in enumerate(examples):button(frame,source,ix,body+106+i*86,iw,label,action)
    # Bridge into POS with an explicit demo role switch and without reseeding costs.
    for device in ('desktop','mobile'):
        for state in ('queued','owner-queued','invoiced'):
            source=device+'-so-'+state;frame=so['frames'][source];n=api.ask('node.get',{'id':frame,'depth':0});positions[frame]=(n['x'],n['y']);mobile=device=='mobile'
            owner=state=='owner-queued';label='Buka POS sebagai Owner' if owner else 'Demo: buka POS sebagai Kasir'
            action=[switch('MIActor','Owner' if owner else 'Kasir'),queue_route(device) if state!='invoiced' else invoice_route(device)]
            button(frame,source,36 if mobile else 1032,1298 if mobile else 588,318 if mobile else 360,label,action,kind='Primary')
        # Restarting an SO scenario also restarts its one-invoice demo state.
        for edge in so['edges']:
            if edge['source']==device+'-so-hub' and edge['label']!='Demo: kembali ke Diagnosa':
                patched.append({'source':edge['source'],'node':edge['node'],'label':edge['label'],'originalAction':edge['action']})
                action=wrap(reset()+[edge['action']]);c('proto.interaction.clear',{'ids':[edge['node']]});c('proto.interaction.add',{'id':edge['node'],'action':action,'transition':{'type':'instant'}})
        c('page.select',{'id':2079 if device=='mobile' else 1});c('proto.flow.add',{'start':frames[device+'-maya-demo'],'name':'Maya / '+('Ponsel' if device=='mobile' else 'Desktop')+' / Registrasi sampai nota'})
    save_map();c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')});c('proto.preview',{'start':frames['desktop-maya-demo']})
    print(json.dumps({'frames':len(frames),'newFields':len(fields),'controlActions':len(edges),'resetSOScenarios':len(patched)}))
finally:api.close()
