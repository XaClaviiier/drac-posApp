"""One-time native customer, vehicle and visit-history prototype slice."""
import json,zipfile,hashlib
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
f=json.loads((ROOT/'evidence/foundations.json').read_text());mi=json.loads((ROOT/'evidence/maya-invoice-map.json').read_text());so=json.loads((ROOT/'evidence/service-order-map.json').read_text());diag=json.loads((ROOT/'evidence/diagnosis-map.json').read_text());reg=json.loads((ROOT/'evidence/registration-map.json').read_text())
states=['hub','customers','customer','customer-inactive','arif','phones','vehicles','vehicle','vehicle-owner','vehicle-inactive','search','no-results','timeline','timeline-new','timeline-arif','history-empty','visit-old','old-diagnosis','old-so','old-invoice','old-receipt','visit-current','current-invoice-readonly','pending','customer-edit','customer-invalid','plate-edit','plate-invalid','plate-collision','plate-log','deactivate-customer','deactivate-vehicle','choose','choose-inactive','new-visit','visit-invalid','review','saved','offline','failed','blocked']
domains={
 'CHActor':['Kasir','Owner','Teknisi'],'CHPhone':['0812 0000 0147','0812 0000 0148'],
 'CHPhoneDraft':['0812 0000 0147','0812 0000 0148','Belum diisi'],
 'CHCustomerActive':[True,False],'CHVehicleActive':[True,False],
 'CHPlate':['DD 1248 KL','DD 2248 KL'],'CHPlateDraft':['DD 2248 KL','B 1234 ABC','DD 1248 KL'],
 'CHReasonValid':[False,True],'CHReason':['Belum diisi','Plat kendaraan berubah; diverifikasi Owner.'],
 'CHPlateChanged':[False,True],'CHScope':['vehicle','maya','arif'],
 'CHScopeTitle':['Riwayat kendaraan','Riwayat Maya Lestari','Riwayat Arif Ramadhan'],
 'CHSelectedName':['Maya Lestari','Arif Ramadhan'],'CHSelectedPhone':['0812 0000 0147','0812 0000 0148'],
 'CHComplaintValid':[False,True],'CHComplaint':['Belum diisi','AC kembali kurang dingin pada siang hari.'],
 'CHRegName':['Maya Lestari','Arif Ramadhan'],'CHRegPhone':['0812 0000 0147','0812 0000 0148'],
 'CHRegPlate':['DD 1248 KL','DD 2248 KL'],'CHRegComplaint':['Belum diisi','AC kembali kurang dingin pada siang hari.'],
 'CHNewSaved':[False,True],'CHOffline':[False,True],'CHFail':[False,True]}
defaults={k:v[0] for k,v in domains.items()};fields={};allfields={**mi['fieldModes'],**so['fieldModes']};frames={};positions={};edges=[];instances=[];themes={};bound=[];patches=[];api=Native();c=api.command
def tag(v):return json.dumps(v,ensure_ascii=False)
def mode(name,value):
    field=allfields[name];return {'type':'setVariableMode','collection':field['collection'],'mode':field['modeForValue'][tag(value)]}
def copyv(dest,source):return {'type':'conditional','blocks':[{'expression':source+' == '+tag(value),'actions':[mode(dest,value)]} for value in allfields[source]['values'].values() if tag(value) in allfields[dest]['modeForValue']]}
def go(device,state):return {'type':'navigate','dest':frames[device+'-ch-'+state]}
def branch(expr,yes,no):return {'type':'conditional','blocks':[{'expression':expr,'actions':yes},{'actions':no}]}
def wrap(actions):return {'type':'conditional','blocks':[{'actions':actions}]}
def reset():return [mode(k,v) for k,v in defaults.items()]
def customer_route(device):return branch('CHCustomerActive',[go(device,'customer')],[go(device,'customer-inactive')])
def vehicle_route(device):return {'type':'conditional','blocks':[{'expression':'not CHVehicleActive','actions':[go(device,'vehicle-inactive')]},{'expression':'CHActor == "Owner"','actions':[go(device,'vehicle-owner')]},{'actions':[go(device,'vehicle')]}]}
def timeline_route(device):return {'type':'conditional','blocks':[
 {'expression':'CHScope == "arif"','actions':[branch('CHNewSaved and CHRegName == "Arif Ramadhan"',[go(device,'timeline-arif')],[go(device,'history-empty')])]},
 {'expression':'CHNewSaved and (CHScope == "vehicle" or CHRegName == "Maya Lestari")','actions':[go(device,'timeline-new')]},{'actions':[go(device,'timeline')]}]}
def history(device,scope):return [mode('CHScope',scope),mode('CHScopeTitle',{'vehicle':'Riwayat kendaraan','maya':'Riwayat Maya Lestari','arif':'Riwayat Arif Ramadhan'}[scope]),timeline_route(device)]
def choose(device):return branch('not CHVehicleActive',[go(device,'blocked')],[branch('CHNewSaved',[go(device,'saved')],[branch('CHCustomerActive',[go(device,'choose')],[go(device,'choose-inactive')])])])
def valid_selected():return 'CHVehicleActive and (CHSelectedName == "Arif Ramadhan" or CHCustomerActive)'
def snapshot():return [copyv('CHRegName','CHSelectedName'),branch('CHSelectedName == "Arif Ramadhan"',[mode('CHRegPhone','0812 0000 0147')],[copyv('CHRegPhone','CHPhone')]),copyv('CHRegPlate','CHPlate'),copyv('CHRegComplaint','CHComplaint')]
def invoice_route(device):
    tech=[go(device,'current-invoice-readonly')]
    normal=next(e['action'] for e in mi['edges'] if e['source']==device+'-maya-demo' and e['label']=='Buka transaksi Maya')
    return branch('MIStage == "none"',[go(device,'pending')],[copyv('MIActor','CHActor'),branch('CHActor == "Teknisi"',tech,[normal])])
def color(name):return {'$var':f['variables'][name]}
def text(frame,x,y,w,value,size=14,ink='Text',weight='Regular',var=None,right=False,white=False):
    n=api.node('text',frame,x=x,y=y,width=w,text=value,props={'fontFamily':'Poppins','fontStyle':weight,'fontSize':size,'lineHeight':'150%','textAlign':'right' if right else 'left','fill':'#18181B' if white else color(ink)})
    if var:c('variable.bind',{'ids':[n],'field':'text','variable':allfields[var]['variable']});bound.append({'node':n,'variable':var})
    return n
def box(frame,x,y,w,h,fill='Surface',r=12):return api.node('rectangle',frame,x=x,y=y,width=w,height=h,props={'fill':color(fill),'stroke':color('Border'),'cornerRadius':r})
def btn(frame,source,x,y,w,label,actions=None,primary=False,disabled=False):
    px,py=positions[frame];kind='Primary' if primary else 'Secondary';n=c('instance.place',{'component':f['buttons'][kind],'x':px+x+w/2,'y':py+y+22})['id'];c('node.reparent',{'ids':[n],'parent':frame});api.set(n,x=x,y=y,width=w,height=44,name=label)
    c('instance.setProperties',{'ids':[n],'properties':{'Label':label,**({'State':'Disabled'} if disabled else {})}})
    if actions and not disabled:
        action=wrap(actions) if isinstance(actions,list) else actions;c('proto.interaction.add',{'id':n,'action':action,'transition':{'type':'instant'}});edges.append({'source':source,'node':n,'label':label,'action':action})
    instances.append(n);return n
def note(frame,x,y,w,value,h=112,warning=False):box(frame,x,y,w,h,'WarningSurface' if warning else 'Selected',8);text(frame,x+16,y+14,w-32,value,13,'Warning' if warning else 'Service')
def identity(frame,x,y,w,kind='vehicle'):
    if kind=='customer':text(frame,x,y,w,'Maya Lestari',20,weight='Semi Bold');text(frame,x,y+38,w,'DEMO-C0147 · identitas pelanggan',12,'Muted')
    else:text(frame,x,y,w,'DD 1248 KL',20,weight='Semi Bold',var='CHPlate');text(frame,x,y+38,w,'DEMO-V0147 · identitas kendaraan',12,'Muted')
def old_identity(frame,x,y,w,white=False):text(frame,x,y,w,'DD 1248 KL · Maya Lestari',18,weight='Semi Bold',white=white);text(frame,x,y+36,w,'REG-DEMO-0140 · 5 Sep 2026 · data contoh',12,'Muted',white=white)
def old_rows(frame,x,y,w,white=False):
    for i,(label,amount) in enumerate([('1 pekerjaan · Pemeriksaan AC','Rp50.000'),('1 pcs · Filter kabin','Rp100.000')]):text(frame,x,y+i*92,w,label,14,white=white);text(frame,x,y+32+i*92,w,amount,17,weight='Semi Bold',right=True,white=white)
    text(frame,x,y+220,w,'Total',14,white=white);text(frame,x,y+258,w,'Rp150.000',25,weight='Bold',right=True,white=white)
def save_map(baseline):
    (ROOT/'evidence/customer-history-map.json').write_text(json.dumps({'frames':frames,'edges':edges,'themeControls':themes,'instances':instances,'boundText':bound,'fieldModes':fields,'defaults':defaults,'patchedHistoryLinks':patches,'baseline':baseline,'states':states,'fixture':{'vehicleId':'DEMO-V0147','mayaId':'DEMO-C0147','arifId':'DEMO-C0150','sharedPhone':'0812 0000 0147','historicalVisit':'REG-DEMO-0140','currentVisit':'REG-DEMO-0147','newVisit':'REG-DEMO-0150','historicalTotal':150000},'stateImplementation':'independent finite-value native modes'},indent=2),encoding='utf-8')
try:
    doc=api.ask('document.inspect',{'allPages':True,'depth':1,'fields':['name','type','x','y','width','height']});assert not api.ask('ui.inspect')['status']['dirty'],'Save manual edits first'
    assert not any(n['name'].startswith(('desktop-ch-','mobile-ch-')) for p in doc['pages'] for n in p.get('children',[])),'Already constructed'
    path=ROOT/'pos-kasir.figcraft';baseline={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':sum(n['type']=='FRAME' for p in doc['pages'] for n in p.get('children',[]))}
    with zipfile.ZipFile(ROOT/'archive/before-customer-history.zip','w',zipfile.ZIP_DEFLATED) as z:z.write(path,'pos-kasir.figcraft')
    c('proto.closePreview')
    for name,values in domains.items():
        names=['Default']+['v'+str(i) for i in range(1,len(values))];collection=c('variable.createCollection',{'name':'Customer history / '+name,'modes':names})['id'];kind='boolean' if isinstance(values[0],bool) else 'string'
        variable=c('variable.create',{'collection':collection,'name':name,'type':kind,'values':dict(zip(names,values))})['id'];fields[name]={'collection':collection,'variable':variable,'values':dict(zip(names,values)),'modeForValue':{tag(v):n for n,v in zip(names,values)}}
    allfields.update(fields)
    for device,pageid in [('desktop',1),('mobile',2079)]:
        mobile=device=='mobile';w,h=(390,844) if mobile else (1440,1000);page=next(p for p in doc['pages'] if p['id']==pageid);bottom=max(n.get('y',0)+n.get('height',0) for n in page['children'])+400;c('page.select',{'id':pageid})
        for i,state in enumerate(states):
            xx=(i%4)*(w+64);yy=bottom+(i//4)*(h+100);frame=api.node('frame',x=xx,y=yy,width=w,height=h,name=device+'-ch-'+state,props={'fill':color('Canvas'),'clip':True,'overflow':'vertical'});frames[device+'-ch-'+state]=frame;positions[frame]=(xx,yy)
    save_map(baseline)
    for source,frame in frames.items():
        device,state=source.split('-ch-');mobile=device=='mobile';c('page.select',{'id':2079 if mobile else 1});w=390 if mobile else 1440;x=16 if mobile else 232;pw=358 if mobile else 1184;body=242 if mobile else 196;ix=x+20;iw=pw-40;panel=pw if mobile else 752;cw=panel-40
        title={'hub':'Pelanggan dan riwayat','customers':'Pelanggan','customer':'Profil pelanggan','customer-inactive':'Profil pelanggan','arif':'Profil pelanggan','phones':'Nomor telepon sama','vehicles':'Kendaraan','vehicle':'Profil kendaraan','vehicle-owner':'Profil kendaraan','vehicle-inactive':'Profil kendaraan','search':'Cari pelanggan / kendaraan','no-results':'Pencarian tanpa hasil','timeline':'Riwayat kunjungan','timeline-new':'Riwayat kunjungan','timeline-arif':'Riwayat kunjungan','history-empty':'Belum ada kunjungan','visit-old':'Kunjungan terdahulu','visit-current':'Kunjungan Maya 0147','customer-edit':'Ubah pelanggan','customer-invalid':'Periksa nomor telepon','plate-edit':'Ubah plat kendaraan','plate-invalid':'Alasan belum diisi','plate-collision':'Plat sudah digunakan','plate-log':'Riwayat perubahan plat','choose':'Pilih pelanggan kunjungan','choose-inactive':'Pilih pelanggan kunjungan','new-visit':'Registrasi kunjungan baru','visit-invalid':'Keluhan belum diisi','review':'Periksa registrasi baru','saved':'Registrasi baru tersimpan','offline':'Koneksi terputus','failed':'Perubahan belum tersimpan','pending':'Dokumen belum tersedia','blocked':'Tindakan tidak tersedia','deactivate-customer':'Nonaktifkan pelanggan?','deactivate-vehicle':'Nonaktifkan kendaraan?','old-receipt':'Nota kunjungan terdahulu','current-invoice-readonly':'Invoice · tampilan baca'}.get(state,'Dokumen kunjungan terdahulu')
        box(frame,0,0,w,64,r=0);text(frame,16 if mobile else 232,8 if mobile else 18,170,'Bengkel AC',16,weight='Semi Bold');text(frame,16 if mobile else 420,36 if mobile else 22,160,'Kasir',12,'Muted',var='CHActor')
        if not mobile:
            box(frame,0,0,208,1000,r=0);text(frame,24,22,160,'Bengkel AC',18,weight='Semi Bold')
            for i,(label,action) in enumerate([('Pelanggan',go(device,'customers')),('Kendaraan',go(device,'vehicles')),('Riwayat',history(device,'vehicle')),('Cari',go(device,'search'))]):btn(frame,source,16,80+i*56,176,label,action)
            text(frame,24,918,160,'Data contoh · satu cabang',12,'Muted')
        else:btn(frame,source,16,76,174,'Pelanggan',go(device,'customers'));btn(frame,source,198,76,176,'Kendaraan',go(device,'vehicles'))
        btn(frame,source,202 if mobile else 1192,8,100 if mobile else 108,'Demo',go(device,'hub'))
        theme=btn(frame,source,310 if mobile else 1312,8,64 if mobile else 112,'Tema',{'type':'conditional','blocks':[{'expression':'mode(POS) == "Dark"','actions':[{'type':'setVariableMode','collection':f['collection'],'mode':'Light'}]},{'actions':[{'type':'setVariableMode','collection':f['collection'],'mode':'Dark'}]}]});themes[source]=theme
        text(frame,x,146 if mobile else 88,pw,title,24 if mobile else 28,weight='Semi Bold');text(frame,x,188 if mobile else 136,pw,'Pelanggan, kendaraan dan kunjungan · data contoh',12,'Muted')
        if state=='hub':
            box(frame,x,body,pw,1100);text(frame,ix,body+24,iw,'Perubahan master tidak menulis ulang riwayat kunjungan.',16,weight='Semi Bold')
            options=[('Buka pelanggan',[go(device,'customers')]),('Buka kendaraan',[go(device,'vehicles')]),('Buka riwayat kendaraan',history(device,'vehicle')),('Demo: sebagai Owner',[mode('CHActor','Owner'),vehicle_route(device)]),('Demo: sebagai Teknisi',[mode('CHActor','Teknisi'),go(device,'customers')]),('Demo: sebagai Kasir',[mode('CHActor','Kasir'),go(device,'customers')]),('Demo: koneksi offline',[mode('CHOffline',True),go(device,'new-visit')]),('Demo: simpan gagal',[mode('CHFail',True),go(device,'new-visit')]),('Ulang contoh pelanggan / riwayat',[*reset(),go(device,'customers')])]
            for i,(label,action) in enumerate(options):btn(frame,source,ix,body+118+i*86,iw,label,action,primary=i==0)
            text(frame,ix,body+942,iw,'Reset ini hanya mengulang contoh pelanggan/riwayat; tidak menghapus data layanan Maya pada demo invoice.',13,'Muted')
        elif state in ('customers','phones'):
            note(frame,x,body,pw,'Telepon boleh sama. Gunakan ID pelanggan untuk membedakan identitas.',h=118 if mobile else 80)
            for i,(name,ref,action,var) in enumerate([('Maya Lestari','DEMO-C0147',customer_route(device),'CHPhone'),('Arif Ramadhan','DEMO-C0150',go(device,'arif'),None)]):
                yy=body+152+i*258;box(frame,x,yy,pw,234);text(frame,ix,yy+20,iw,name,18,weight='Semi Bold');text(frame,ix,yy+56,iw,ref,12,'Muted');text(frame,ix,yy+90,iw,'0812 0000 0147',14,var=var);btn(frame,source,ix,yy+158,iw,'Buka '+name.split()[0],action,primary=i==0)
            btn(frame,source,x,body+712,pw,'Cari nama / plat',go(device,'search'))
        elif state in ('customer','customer-inactive','arif'):
            arif=state=='arif';inactive=state=='customer-inactive';box(frame,x,body,panel,1040);name='Arif Ramadhan' if arif else 'Maya Lestari';text(frame,ix,body+24,cw,name,20,weight='Semi Bold');text(frame,ix,body+62,cw,'DEMO-C0150' if arif else 'DEMO-C0147',12,'Muted');text(frame,ix,body+112,cw,'Nonaktif' if inactive else 'Aktif',14,'Warning' if inactive else 'Success');text(frame,ix,body+162,cw,'Telepon master',13,'Muted');text(frame,ix,body+196,cw,'0812 0000 0147',18,var=None if arif else 'CHPhone');text(frame,ix,body+246,cw,'Alamat: tidak diisi',14,'Muted')
            note(frame,ix,body+300,cw,'Profil ini menggunakan ID tersendiri. Telepon yang sama tidak menggabungkan data atau riwayat.',h=142 if mobile else 100)
            btn(frame,source,ix,body+494,cw,'Riwayat pelanggan',history(device,'arif' if arif else 'maya'),primary=True)
            if not arif:
                btn(frame,source,ix,body+562,cw,'Ubah telepon master',[copyv('CHPhoneDraft','CHPhone'),go(device,'customer-edit')]);btn(frame,source,ix,body+630,cw,'Aktifkan pelanggan' if inactive else 'Nonaktifkan pelanggan',[mode('CHCustomerActive',True),go(device,'customer')] if inactive else go(device,'deactivate-customer'))
            btn(frame,source,ix,body+720,cw,'Lihat kendaraan',go(device,'vehicles'))
        elif state=='vehicles':
            box(frame,x,body,pw,390);identity(frame,ix,body+24,iw);text(frame,ix,body+122,iw,'Riwayat terhubung ke ID kendaraan, bukan nama pemilik tetap.',14,'Muted');btn(frame,source,ix,body+244,iw,'Buka kendaraan',vehicle_route(device),primary=True);btn(frame,source,x,body+438,pw,'Cari plat dengan huruf kecil / spasi',go(device,'search'))
        elif state in ('vehicle','vehicle-owner','vehicle-inactive'):
            inactive=state=='vehicle-inactive';box(frame,x,body,panel,1120);identity(frame,ix,body+24,cw);text(frame,ix,body+118,cw,'Nonaktif' if inactive else 'Aktif',14,'Warning' if inactive else 'Success');text(frame,ix,body+166,cw,'Pelanggan dapat berbeda pada setiap kedatangan. Snapshot kunjungan lama tetap dipertahankan.',14,'Muted');btn(frame,source,ix,body+310,cw,'Riwayat kendaraan',history(device,'vehicle'),primary=True);btn(frame,source,ix,body+378,cw,'Registrasi kunjungan baru',choose(device) if not inactive else None,disabled=inactive)
            if state=='vehicle-owner':btn(frame,source,ix,body+466,cw,'Ubah plat (Owner)',[copyv('CHPlateDraft','CHPlate'),mode('CHReasonValid',False),mode('CHReason','Belum diisi'),go(device,'plate-edit')])
            else:btn(frame,source,ix,body+466,cw,'Ubah plat · hanya Owner',disabled=True)
            btn(frame,source,ix,body+534,cw,'Riwayat perubahan plat',go(device,'plate-log'));btn(frame,source,ix,body+622,cw,'Aktifkan kendaraan' if inactive else 'Nonaktifkan kendaraan',[mode('CHVehicleActive',True),vehicle_route(device)] if inactive else go(device,'deactivate-vehicle'))
            note(frame,ix,body+720,cw,'Nonaktif tidak menghapus kendaraan atau dokumen lama. Kendaraan nonaktif tidak dipilih untuk kunjungan baru.',h=156 if mobile else 104)
        elif state=='search':
            box(frame,x,body,pw,900);text(frame,ix,body+24,iw,'Contoh pencarian tersedia',18,weight='Semi Bold');text(frame,ix,body+68,iw,'Plat dinormalisasi menjadi kapital tanpa spasi. Pencarian riwayat plat lama otomatis belum ditambahkan.',13,'Muted')
            opts=[('Cari Maya Lestari',customer_route(device)),('Cari telepon 0812 0000 0147',go(device,'phones')),('Cari "dd 1248 kl"',branch('CHPlate == "DD 1248 KL"',[vehicle_route(device)],[go(device,'no-results')])),('Cari " dd 2248 kl "',branch('CHPlate == "DD 2248 KL"',[vehicle_route(device)],[go(device,'no-results')])),('Contoh tanpa hasil',go(device,'no-results'))]
            for i,(label,action) in enumerate(opts):btn(frame,source,ix,body+188+i*102,iw,label,action)
        elif state in ('timeline','timeline-new','timeline-arif'):
            text(frame,x,body,pw,'Riwayat kendaraan',18,weight='Semi Bold',var='CHScopeTitle');text(frame,x,body+42,pw,'Satu kedatangan = satu registrasi. Status pekerjaan dan pembayaran dibaca terpisah.',13,'Muted')
            rows=[] if state=='timeline-arif' else [('0147','Kunjungan layanan Maya · 15 Nov 2026','Dokumen mengikuti skenario layanan yang dijalankan.',go(device,'visit-current')),('0140','Kunjungan terdahulu · 5 Sep 2026','Maya Lestari · Selesai · Lunas Rp150.000',go(device,'visit-old'))]
            if state!='timeline':rows=[('0150','Kunjungan baru · 16 Nov 2026','Registrasi tersimpan · belum ada SO atau invoice',go(device,'saved'))]+rows
            for i,(ref,title_,sub,action) in enumerate(rows):
                yy=body+120+i*258;box(frame,x,yy,pw,234);text(frame,ix,yy+18,iw,'REG-DEMO-'+ref,16,weight='Semi Bold');text(frame,ix,yy+54,iw,title_,13,'Muted');text(frame,ix,yy+92,iw,sub,13)
                if ref=='0150':text(frame,ix,yy+122,iw,'Maya Lestari',13,var='CHRegName')
                btn(frame,source,ix,yy+166,iw,'Buka kunjungan '+ref,action,primary=i==0)
            btn(frame,source,x,body+160+len(rows)*258,pw,'Registrasi kunjungan baru',choose(device))
        elif state in ('visit-old','visit-current'):
            old=state=='visit-old';box(frame,x,body,pw,1320);text(frame,ix,body+24,iw,'DD 1248 KL · Maya Lestari',18,weight='Semi Bold');text(frame,ix,body+62,iw,'REG-DEMO-0140 · 5 Sep 2026' if old else 'REG-DEMO-0147 · 15 Nov 2026',12,'Muted');text(frame,ix,body+122,iw,'Snapshot saat kunjungan',15,weight='Semi Bold');text(frame,ix,body+168,iw,'Telepon: 0812 0000 0147\nPlat: DD 1248 KL\nAlamat: tidak diisi',14);text(frame,ix,body+276,iw,'Keluhan: AC kurang dingin saat siang.',14)
            note(frame,ix,body+342,iw,'Mengubah master tidak mengubah data di atas. Ini bukan formulir koreksi kunjungan.',h=132 if mobile else 88)
            if old:actions=[('Diagnosa & Estimasi',go(device,'old-diagnosis')),('Service Order',go(device,'old-so')),('Invoice',go(device,'old-invoice')),('Nota',go(device,'old-receipt'))]
            else:
                sorouter=next(e['action'] for e in so['edges'] if e['source']==device+'-so-list' and e['label']=='Buka SO')
                sync=[copyv('SOActor','CHActor'),branch('CHActor == "Owner"',[mode('SOOwner',True),mode('SOWriter',True)],[mode('SOOwner',False),branch('CHActor == "Teknisi"',[mode('SOWriter',True)],[mode('SOWriter',False)])])]
                actions=[('Diagnosa & Estimasi',branch('SOHasContext',[{'type':'navigate','dest':diag['frames'][device+'-diag-readonly']}],[go(device,'pending')])),('Service Order',branch('SOHasContext',sync+[sorouter],[go(device,'pending')])),('Invoice',invoice_route(device)),('Nota',branch('MIStage == "paid"',[copyv('MIActor','CHActor'),{'type':'navigate','dest':mi['frames'][device+'-maya-receipt']}],[go(device,'pending')]))]
            for i,(label,action) in enumerate(actions):btn(frame,source,ix,body+538+i*76,iw,label,action,primary=i==0)
            if not old:btn(frame,source,ix,body+868,iw,'Demo: lanjut layanan sebagai Kasir',[mode('CHActor','Kasir'),{'type':'navigate','dest':reg['frames'][device+'-reg-saved']}])
            btn(frame,source,ix,body+980,iw,'Kembali ke riwayat',timeline_route(device))
        elif state in ('old-diagnosis','old-so','old-invoice','old-receipt'):
            receipt=state=='old-receipt';rw=pw if mobile else 752
            if receipt:api.node('rectangle',frame,x=x,y=body,width=rw,height=1080,props={'fill':'#FFFFFF','stroke':'#E4E4E7','cornerRadius':8})
            else:box(frame,x,body,rw,1120)
            ww=rw-40;old_identity(frame,ix,body+24,ww,receipt);text(frame,ix,body+120,ww,{'old-diagnosis':'EST-DEMO-0140 · Disetujui','old-so':'SO-DEMO-0140 · Selesai','old-invoice':'INV-DEMO-0140 · Lunas','old-receipt':'NOTA INV-DEMO-0140 · Lunas'}[state],16,'Success',weight='Semi Bold',white=receipt);old_rows(frame,ix,body+210,ww,receipt)
            text(frame,ix,body+560,ww,'Dokumen historis · hanya dibaca',14,'Muted',white=receipt)
            if state in ('old-invoice','old-receipt'):text(frame,ix,body+612,ww,'Tunai: Rp200.000\nPembayaran: Rp150.000\nKembalian: Rp50.000\nSisa tagihan: Rp0',14,white=receipt)
            if state=='old-invoice':btn(frame,source,ix,body+770,ww,'Lihat nota historis',go(device,'old-receipt'),primary=True)
            btn(frame,source,ix,body+910,ww,'Kembali ke kunjungan 0140',go(device,'visit-old'))
        elif state=='current-invoice-readonly':
            box(frame,x,body,pw,870);text(frame,ix,body+24,iw,'INV-DEMO-0147 · tampilan baca Teknisi',17,weight='Semi Bold');text(frame,ix,body+80,iw,'DD 1248 KL · Maya Lestari',15);text(frame,ix,body+142,iw,'Invoice draf',16,var='MIQueueLabel');text(frame,ix,body+204,iw,'Total invoice',14);text(frame,ix,body+244,iw,'Rp150.000',24,weight='Bold',var='MITotalText',right=True);text(frame,ix,body+318,iw,'Sisa tagihan',14);text(frame,ix,body+358,iw,'Rp0',20,var='MIDueText',right=True);note(frame,ix,body+436,iw,'Teknisi membaca rincian. Penerbitan dan pembayaran dilakukan Kasir atau Owner.',h=138 if mobile else 92);btn(frame,source,ix,body+632,iw,'Kembali ke kunjungan 0147',go(device,'visit-current'))
        elif state in ('customer-edit','customer-invalid'):
            box(frame,x,body,pw,920);identity(frame,ix,body+24,iw,'customer');text(frame,ix,body+136,iw,'Telepon master',14);text(frame,ix,body+176,iw,'0812 0000 0147',20,var='CHPhoneDraft');btn(frame,source,ix,body+250,iw,'Isi contoh telepon baru',[mode('CHPhoneDraft','0812 0000 0148'),go(device,'customer-edit')]);btn(frame,source,ix,body+318,iw,'Kosongkan telepon contoh',[mode('CHPhoneDraft','Belum diisi'),go(device,'customer-invalid')])
            if state=='customer-invalid':note(frame,ix,body+402,iw,'Nomor telepon wajib diisi. Data master belum berubah.',warning=True)
            else:note(frame,ix,body+402,iw,'Perubahan ini hanya memperbarui master. Telepon pada kunjungan lama tetap.',h=126 if mobile else 88)
            btn(frame,source,ix,body+596,iw,'Simpan telepon',branch('CHPhoneDraft == "Belum diisi"',[go(device,'customer-invalid')],[copyv('CHPhone','CHPhoneDraft'),customer_route(device)]),primary=True);btn(frame,source,ix,body+664,iw,'Batal',customer_route(device))
        elif state in ('plate-edit','plate-invalid','plate-collision'):
            box(frame,x,body,pw,1120);identity(frame,ix,body+24,iw);text(frame,ix,body+132,iw,'Plat baru · hasil normalisasi',14);text(frame,ix,body+174,iw,'DD 2248 KL',20,weight='Semi Bold',var='CHPlateDraft');btn(frame,source,ix,body+244,iw,'Contoh "dd 2248 kl"',[mode('CHPlateDraft','DD 2248 KL'),go(device,'plate-edit')]);btn(frame,source,ix,body+312,iw,'Contoh plat sudah digunakan',[mode('CHPlateDraft','B 1234 ABC'),go(device,'plate-edit')]);text(frame,ix,body+402,iw,'Alasan',14);text(frame,ix,body+440,iw,'Belum diisi',13,'Muted',var='CHReason');btn(frame,source,ix,body+510,iw,'Isi alasan contoh',[mode('CHReasonValid',True),mode('CHReason','Plat kendaraan berubah; diverifikasi Owner.'),go(device,'plate-edit')])
            if state!='plate-edit':note(frame,ix,body+594,iw,'Plat B 1234 ABC sudah dipakai kendaraan lain. Data tidak digabung.' if state=='plate-collision' else 'Owner wajib mengisi alasan sebelum mengganti plat.',warning=True,h=152 if mobile else 100)
            action={'type':'conditional','blocks':[{'expression':'CHActor != "Owner"','actions':[go(device,'blocked')]},{'expression':'not CHReasonValid','actions':[go(device,'plate-invalid')]},{'expression':'CHPlateDraft == "B 1234 ABC"','actions':[go(device,'plate-collision')]},{'expression':'CHPlateDraft == CHPlate','actions':[vehicle_route(device)]},{'actions':[copyv('CHPlate','CHPlateDraft'),mode('CHPlateChanged',True),vehicle_route(device)]}]}
            btn(frame,source,ix,body+802,iw,'Simpan perubahan plat',action,primary=True);btn(frame,source,ix,body+870,iw,'Batal',vehicle_route(device))
        elif state=='plate-log':
            box(frame,x,body,pw,760);identity(frame,ix,body+24,iw);text(frame,ix,body+138,iw,'Plat saat kunjungan terdahulu: DD 1248 KL',14);text(frame,ix,body+190,iw,'Plat master terkini',14);text(frame,ix,body+228,iw,'DD 1248 KL',20,var='CHPlate');text(frame,ix,body+292,iw,'ID kendaraan tetap DEMO-V0147. Tidak ada penggabungan kendaraan atau perubahan snapshot kunjungan.',14,'Muted');btn(frame,source,ix,body+470,iw,'Riwayat kendaraan',history(device,'vehicle'),primary=True);btn(frame,source,ix,body+538,iw,'Kembali ke kendaraan',vehicle_route(device))
        elif state in ('deactivate-customer','deactivate-vehicle'):
            customer=state.endswith('customer');box(frame,x,body,pw,760);identity(frame,ix,body+24,iw,'customer' if customer else 'vehicle');note(frame,ix,body+142,iw,'Master ini sudah digunakan dalam kunjungan. Nonaktifkan tanpa menghapus riwayat; aktifkan kembali bila diperlukan.',h=172 if mobile else 108,warning=True);btn(frame,source,ix,body+396,iw,'Konfirmasi nonaktifkan',[mode('CHCustomerActive' if customer else 'CHVehicleActive',False),customer_route(device) if customer else vehicle_route(device)],primary=True);btn(frame,source,ix,body+464,iw,'Batal',customer_route(device) if customer else vehicle_route(device))
        elif state in ('choose','choose-inactive'):
            box(frame,x,body,pw,810);identity(frame,ix,body+24,iw);text(frame,ix,body+124,iw,'Pelanggan pada kunjungan baru dipilih eksplisit. Tidak mengubah pelanggan pada kunjungan lama.',14,'Muted');inactive=state=='choose-inactive';btn(frame,source,ix,body+288,iw,'Maya Lestari · nonaktif' if inactive else 'Pilih Maya Lestari',[mode('CHSelectedName','Maya Lestari'),copyv('CHSelectedPhone','CHPhone'),mode('CHComplaintValid',False),mode('CHComplaint','Belum diisi'),go(device,'new-visit')] if not inactive else None,primary=True,disabled=inactive);btn(frame,source,ix,body+376,iw,'Pilih Arif Ramadhan',[mode('CHSelectedName','Arif Ramadhan'),mode('CHSelectedPhone','0812 0000 0147'),mode('CHComplaintValid',False),mode('CHComplaint','Belum diisi'),go(device,'new-visit')]);text(frame,ix,body+460,iw,'Arif dan Maya memiliki ID berbeda meskipun nomor telepon sama.',13,'Muted')
        elif state in ('new-visit','visit-invalid','review','saved'):
            saved=state=='saved';review=state=='review';box(frame,x,body,pw,1170);text(frame,ix,body+24,iw,'REG-DEMO-0150 · tersimpan' if saved else 'Registrasi baru · belum disimpan',17,weight='Semi Bold');text(frame,ix,body+82,iw,'DEMO-V0147 · kendaraan existing',12,'Muted');text(frame,ix,body+126,iw,'Maya Lestari',20,weight='Semi Bold',var='CHRegName' if saved or review else 'CHSelectedName');text(frame,ix,body+174,iw,'0812 0000 0147',14,var='CHRegPhone' if saved or review else 'CHSelectedPhone');text(frame,ix,body+214,iw,'DD 1248 KL',20,weight='Semi Bold',var='CHRegPlate' if saved or review else 'CHPlate');text(frame,ix,body+266,iw,'Alamat: tidak diisi (opsional)',13,'Muted');text(frame,ix,body+326,iw,'Keluhan awal',14,weight='Medium');text(frame,ix,body+368,iw,'Belum diisi',14,var='CHRegComplaint' if saved or review else 'CHComplaint')
            if saved:
                note(frame,ix,body+492,iw,'Kunjungan baru tersimpan sebagai contoh. Belum ada diagnosa, SO, invoice atau pembayaran untuk 0150.',h=164 if mobile else 108);btn(frame,source,ix,body+712,iw,'Lihat riwayat kendaraan',history(device,'vehicle'),primary=True);btn(frame,source,ix,body+780,iw,'Diagnosa belum dibuat',disabled=True)
            elif review:
                note(frame,ix,body+492,iw,'Periksa pelanggan dan kendaraan. Menyimpan registrasi tidak menagihkan biaya.',h=138 if mobile else 96)
                action={'type':'conditional','blocks':[{'expression':'CHNewSaved','actions':[go(device,'saved')]},{'expression':'not ('+valid_selected()+')','actions':[go(device,'blocked')]},{'expression':'CHOffline','actions':[go(device,'offline')]},{'expression':'CHFail','actions':[go(device,'failed')]},{'actions':[mode('CHNewSaved',True),go(device,'saved')]}]};btn(frame,source,ix,body+706,iw,'Simpan registrasi baru',action,primary=True);btn(frame,source,ix,body+774,iw,'Periksa isian',go(device,'new-visit'))
            else:
                if state=='visit-invalid':note(frame,ix,body+468,iw,'Keluhan wajib diisi sebelum ditinjau.',warning=True)
                btn(frame,source,ix,body+614,iw,'Isi keluhan contoh',[mode('CHComplaintValid',True),mode('CHComplaint','AC kembali kurang dingin pada siang hari.'),go(device,'new-visit')]);btn(frame,source,ix,body+702,iw,'Periksa registrasi',branch('not ('+valid_selected()+')',[go(device,'blocked')],[branch('CHComplaintValid',snapshot()+[go(device,'review')],[go(device,'visit-invalid')])]),primary=True);btn(frame,source,ix,body+770,iw,'Ganti pelanggan',choose(device))
        else:
            box(frame,x,body,pw,830);messages={'history-empty':'Belum ada kunjungan untuk ID pelanggan ini. Kesamaan telepon tidak mengambil riwayat pelanggan lain.','no-results':'Tidak ada hasil pada contoh pencarian ini. Setelah plat berubah, gunakan plat master terkini; riwayat lama dibaca dari ID kendaraan.','pending':'Dokumen belum tersedia pada konteks kunjungan ini. Dokumen 0150 tidak diarahkan ke dokumen 0147.','offline':'Registrasi belum tersimpan. Koneksi diperlukan untuk menyimpan pada contoh ini; isian tetap tersedia.','failed':'Pencatatan registrasi belum berhasil. Data kunjungan lama dipertahankan dan contoh belum ditandai tersimpan.','blocked':'Tindakan tidak sesuai hak akses atau status master. Gunakan master aktif; perubahan plat hanya Owner.'}
            note(frame,ix,body+30,iw,messages.get(state,'Pilihan belum tersedia.'),h=244 if mobile else 144,warning=state in ('blocked','failed','offline'))
            if state=='offline':btn(frame,source,ix,body+348,iw,'Demo: koneksi pulih',[mode('CHOffline',False),go(device,'review')],primary=True)
            elif state=='failed':btn(frame,source,ix,body+348,iw,'Demo: coba simpan kembali',[mode('CHFail',False),go(device,'review')],primary=True)
            elif state=='no-results':btn(frame,source,ix,body+348,iw,'Kembali mencari',go(device,'search'),primary=True)
            btn(frame,source,ix,body+448,iw,'Kembali ke pelanggan',go(device,'customers'));btn(frame,source,ix,body+516,iw,'Riwayat kendaraan',history(device,'vehicle'))
        if (len(edges)%50)<8:save_map(baseline)
    # Existing POS history opens this module without resetting invoice or master state.
    operations=[]
    for edge in mi['edges']:
        if edge['label'] in ('Riwayat','Riwayat kunjungan'):
            device=edge['source'].split('-')[0];action=wrap([copyv('CHActor','MIActor'),*history(device,'vehicle')]);patches.append({'source':edge['source'],'node':edge['node'],'label':edge['label'],'originalAction':edge['action'],'action':action});operations.extend([{'command':'proto.interaction.clear','params':{'ids':[edge['node']]}},{'command':'proto.interaction.add','params':{'id':edge['node'],'action':action,'transition':{'type':'instant'}}}])
    result=c('command.batch',{'commands':operations});assert not (isinstance(result,list) and any(isinstance(x,dict) and 'error' in x for x in result)),result
    for device in ('desktop','mobile'):
        c('page.select',{'id':2079 if device=='mobile' else 1});c('proto.flow.add',{'start':frames[device+'-ch-hub'],'name':'Pelanggan dan Riwayat / '+('Ponsel' if device=='mobile' else 'Desktop')+' / Demo'})
    save_map(baseline);c('page.select',{'id':1});c('file.saveAs',{'path':str(path)});c('proto.preview',{'start':frames['desktop-ch-hub']});print(json.dumps({'newFrames':len(frames),'newFields':len(fields),'newActions':len(edges),'historyLinksUpdated':len(patches),'baseline':baseline}),flush=True)
finally:api.close()
