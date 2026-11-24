"""Extend the approved native document with a connected registration design slice.

This is a one-time construction script. Existing cashier layers are preserved.
"""
import json, zipfile
from pathlib import Path
from native_api import Native

ROOT = Path(__file__).resolve().parents[1]
api = Native(); c = api.command
f = json.loads((ROOT/'evidence/foundations.json').read_text())
cash = json.loads((ROOT/'evidence/design-completion-map.json').read_text())
pages = json.loads((ROOT/'evidence/consolidation.json').read_text())['pages']
frames, edges, themes, instances, timers = {}, [], {}, [], []
positions = {}
states = ['list','list-saved','list-known','list-edited','new','invalid','filled',
          'review','saving','saved','edit','edited','locked','discard','empty',
          'no-results','load-error','offline','save-error','catalog','known',
          'known-review','known-saving','known-saved']
titles = {'new':'Registrasi baru','invalid':'Registrasi baru','filled':'Registrasi baru',
          'known':'Registrasi kunjungan baru','review':'Periksa registrasi',
          'known-review':'Periksa registrasi','saving':'Menyimpan registrasi',
          'known-saving':'Menyimpan registrasi','saved':'Detail registrasi',
          'known-saved':'Detail registrasi','edited':'Detail registrasi',
          'edit':'Koreksi registrasi','locked':'Detail registrasi',
          'discard':'Tinggalkan isian?','empty':'Belum ada registrasi',
          'no-results':'Registrasi tidak ditemukan','load-error':'Daftar belum dapat dimuat',
          'offline':'Koneksi terputus','save-error':'Registrasi belum tersimpan',
          'catalog':'Skenario registrasi'}
base = {'plate':'DD 1248 KL','customer':'Maya Lestari','phone':'0812 0000 0147',
        'address':'Tidak diisi','complaint':'AC kurang dingin saat siang.',
        'reference':'REG-DEMO-0147','customerId':'DEMO-C0147','vehicleId':'DEMO-V0147'}
returning = {**base,'plate':'B 1234 ABC','phone':'0812 0000 0261',
             'reference':'REG-DEMO-0148','vehicleId':'DEMO-V0261'}
locked = {**returning,'customer':'Rina Prasetyo','reference':'REG-DEMO-0144',
          'customerId':'DEMO-C0261','complaint':'AC kurang dingin.'}
corrected = {**base,'complaint':'AC kurang dingin dan ada bunyi saat dinyalakan.'}

def color(role): return {'$var':f['variables'][role]}
def text(parent,x,y,w,value,size=14,role='Text',weight='Regular'):
    return api.node('text',parent,x=x,y=y,width=w,text=value,props={
        'fontFamily':'Poppins','fontStyle':weight,'fontSize':size,
        'lineHeight':'150%','fill':color(role)})
def rect(parent,x,y,w,h,role='Surface',radius=12,border='Border'):
    return api.node('rectangle',parent,x=x,y=y,width=w,height=h,props={
        'fill':color(role),'cornerRadius':radius,'stroke':color(border)})
def dest(key): return frames[key] if key in frames else cash['frames'][key]
def navigate(node,source,target,label):
    c('proto.interaction.add',{'id':node,'dest':dest(target),'transition':{'type':'instant'}})
    edges.append({'source':source,'target':target,'node':node,'label':label})
def control(parent,source,x,y,w,label,target=None,kind='Secondary',disabled=False,h=44):
    device=source.split('-',1)[0]
    c('page.select',{'id':pages['mobile' if device=='mobile' else 'desktop']})
    px,py=positions[parent]
    node=c('instance.place',{'component':f['buttons'][kind],'x':px+x+w/2,'y':py+y+h/2})['id']
    c('node.reparent',{'ids':[node],'parent':parent})
    api.set(node,x=x,y=y,width=w,height=h,name=label)
    if kind!='InteractionArea': c('instance.setProperties',{'ids':[node],'properties':{'Label':label}})
    if disabled: c('instance.setProperties',{'ids':[node],'properties':{'State':'Disabled'}})
    if target: navigate(node,source,target,label)
    instances.append(node)
    return node
def notice(frame,x,y,w,value,role='Selected',ink='Service',h=76):
    rect(frame,x,y,w,h,role,8,border=role)
    text(frame,x+16,y+14,w-32,value,13,ink)
def save_map():
    report={'frames':frames,'edges':edges,'themeControls':themes,'instances':instances,
            'timers':timers,'fixtures':{'new':base,'returning':returning,'locked':locked,'corrected':corrected}}
    (ROOT/'evidence/registration-map.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
def key_for(device,state): return device+'-reg-'+state

try:
    doc=api.ask('document.inspect',{'allPages':True,'depth':2})
    assert doc['name']=='POS Kasir - Poppins - Manual Payments'
    assert not any(n['name'].startswith(('desktop-reg-','mobile-reg-')) for p in doc['pages'] for n in p.get('children',[])), 'Registration migration already started'
    assert not api.ask('ui.inspect')['status']['dirty'], 'Save manual edits before migration'
    with zipfile.ZipFile(ROOT/'archive/before-registration.zip','w',zipfile.ZIP_DEFLATED) as archive:
        archive.write(ROOT/'pos-kasir.figcraft','pos-kasir.figcraft')
    c('proto.closePreview')
    # Place new states below the existing cashier canvases on each device page.
    for device in ('desktop','mobile'):
        c('page.select',{'id':pages['mobile' if device=='mobile' else 'desktop']})
        w,h=(390,844) if device=='mobile' else (1440,1000)
        for i,state in enumerate(states):
            x=(i%4)*(w+64); y=(12+i//4)*(h+100)
            frame=api.node('frame',x=x,y=y,width=w,height=h,name=key_for(device,state),
                           props={'fill':color('Canvas'),'clip':True,'overflow':'vertical'})
            frames[key_for(device,state)]=frame; positions[frame]=(x,y)
    save_map()
    for key,frame in frames.items():
        device,state=key.split('-reg-'); mobile=device=='mobile'
        w=390 if mobile else 1440; x=16 if mobile else 232; pw=358 if mobile else 1184
        top=148 if mobile else 88; subtitle=190 if mobile else 136; body=258 if mobile else 196
        rect(frame,0,0,w,64,'Surface',0)
        text(frame,16 if mobile else 232,18,168,'Bengkel AC',16,weight='Semi Bold')
        if not mobile:
            rect(frame,0,0,208,1000,'Surface',0)
            text(frame,24,22,160,'Bengkel AC',18,weight='Semi Bold')
            control(frame,key,16,80,176,'POS Kasir',device+'-list')
            rect(frame,16,136,176,44,'Selected',8,border='Selected')
            text(frame,32,147,144,'Registrasi',14,'Service','Semi Bold')
            control(frame,key,16,136,176,'Registrasi',key_for(device,'list'),kind='InteractionArea')
            text(frame,24,930,160,'Kasir · Data contoh',12,'Muted')
        else:
            control(frame,key,16,76,174,'POS Kasir',device+'-list')
            rect(frame,198,76,176,44,'Selected',8,border='Selected')
            text(frame,214,87,144,'Registrasi',14,'Service','Semi Bold')
            control(frame,key,198,76,176,'Registrasi',key_for(device,'list'),kind='InteractionArea')
        control(frame,key,202 if mobile else 1192,8,100 if mobile else 108,'Demo',key_for(device,'catalog'))
        theme=control(frame,key,310 if mobile else 1312,8,64 if mobile else 112,'Tema')
        themes[key]=theme
        c('proto.interaction.add',{'id':theme,'action':{'type':'conditional','blocks':[
            {'expression':'mode(POS) == "Dark"','actions':[{'type':'setVariableMode','collection':f['collection'],'mode':'Light'}]},
            {'actions':[{'type':'setVariableMode','collection':f['collection'],'mode':'Dark'}]}]},'transition':{'type':'instant'}})
        text(frame,x,top,pw,titles.get(state,'Registrasi kendaraan'),24 if mobile else 28,weight='Semi Bold')
        text(frame,x,subtitle,pw,'Kedatangan kendaraan, pelanggan dan keluhan awal.',13,'Muted')
        c('proto.interaction.add',{'id':frame,'trigger':{'type':'keyPress','key':'Escape'},'dest':frames[key_for(device,'list')],'transition':{'type':'instant'}})
        target=lambda s:key_for(device,s)
        data=returning if state.startswith('known') or state=='list-known' else corrected if state in ('edit','edited','list-edited') else locked if state=='locked' else base
        if state.startswith('list'):
            search_y=324 if mobile else 196; cards_y=400 if mobile else 288
            control(frame,key,x,258 if mobile else 88,358 if mobile else 208,'Registrasi baru',target('new'),kind='Primary')
            if not mobile: api.set(instances[-1],x=1208,y=88)
            rect(frame,x,search_y,pw,48,'Surface',8,border='Input')
            text(frame,x+16,search_y+13,pw-32,'Cari plat, nama atau nomor registrasi',14,'Muted')
            control(frame,key,x,search_y,pw,'Contoh pencarian tanpa hasil',target('no-results'),kind='InteractionArea',h=48)
            records=[(locked,'locked')]
            if state!='list': records.insert(0,(data,'known-saved' if state=='list-known' else 'edited' if state=='list-edited' else 'saved'))
            for index,(record,detail) in enumerate(records):
                cx=x if mobile else x+index*604; cy=cards_y+index*268 if mobile else cards_y; cw=358 if mobile else 580
                rect(frame,cx,cy,cw,244)
                text(frame,cx+20,cy+18,cw-40,record['plate'],20,weight='Semi Bold')
                text(frame,cx+20,cy+54,cw-40,record['customer'],14)
                text(frame,cx+20,cy+84,cw-40,record['reference']+' · 15 Nov 2026',12,'Muted')
                text(frame,cx+20,cy+120,cw-40,'SO-0261 sudah dibuat' if detail=='locked' else 'Diagnosa belum dibuat',13,'Service')
                control(frame,key,cx+20,cy+176,cw-40,'Lihat registrasi',target(detail))
            note_y=cards_y+len(records)*268+8 if mobile else cards_y+276
            text(frame,x,note_y,pw,'Setiap kedatangan dicatat sebagai kunjungan baru. Data contoh untuk tinjauan desain.',12,'Muted')
        elif state in ('new','invalid','filled','known','edit'):
            panel_w=pw if mobile else 752; inner=x+20; iw=panel_w-40
            rect(frame,x,body,panel_w,864 if mobile else 620)
            if not mobile:
                rect(frame,1008,body,408,432)
                text(frame,1032,body+24,360,'Kunjungan ini',18,weight='Semi Bold')
                text(frame,1032,body+66,360,'Nomor registrasi dibuat setelah disimpan. Diagnosa, Service Order dan tagihan belum dibuat.',14,'Muted')
                text(frame,1032,body+170,360,'Empat isian wajib',14,weight='Semi Bold')
                text(frame,1032,body+204,360,'Nomor plat, nama pelanggan, nomor telepon dan keluhan awal. Alamat boleh dikosongkan.',14,'Muted')
            fields=[('Nomor plat *','plate'),('Nama pelanggan *','customer'),('Nomor telepon *','phone'),('Alamat (opsional)','address'),('Keluhan awal *','complaint')]
            for index,(label,field) in enumerate(fields):
                if mobile: fx,fy,fw=inner,body+24+index*116,iw
                else: fx,fy,fw=inner+(index%2)*(iw/2+12),body+24+(index//2)*132,(iw-24)/2
                if not mobile and field=='complaint': fx,fw=inner,iw
                text(frame,fx,fy,fw,label,13,weight='Medium')
                ih=96 if field=='complaint' else 48
                empty=state in ('new','invalid')
                value=({'plate':'Contoh: DD 1248 KL','customer':'Nama pelanggan','phone':'Nomor telepon','address':'Alamat pelanggan','complaint':'Ceritakan keluhan awal kendaraan'}[field] if empty else '' if field=='address' else data[field])
                invalid=state=='invalid' and field!='address'
                rect(frame,fx,fy+26,fw,ih,'Surface',8,border='Error' if invalid else 'Input')
                text(frame,fx+12,fy+38,fw-24,value or 'Tidak diisi',14,'Muted' if empty or field=='address' else 'Text')
                helper=('Isi '+label.replace(' *','').lower()+'.') if invalid else 'Opsional; dapat dikosongkan.' if field=='address' else 'Diseragamkan untuk pencocokan kendaraan.' if field=='plate' else ''
                if helper: text(frame,fx,fy+ih+32,fw,helper,12,'Error' if invalid else 'Muted')
            by=body+746 if mobile else body+488
            if state=='known':
                notice(frame,inner,body+640 if mobile else body+552,iw,'Plat ditemukan: gunakan kendaraan yang sama. Pelanggan kunjungan ini Maya; telepon sama tidak menggabungkan pelanggan.',h=96 if mobile else 60)
            if state=='edit':
                text(frame,inner,body+640 if mobile else body+552,iw,'Sebelum SO dibuat: koreksi dicatat pada riwayat kunjungan.',12,'Muted')
            control(frame,key,inner,by,iw if mobile else 342,'Simpan koreksi' if state=='edit' else 'Periksa registrasi',target('edited' if state=='edit' else 'invalid' if state=='new' else 'known-review' if state=='known' else 'review') if state!='invalid' else None,kind='Primary',disabled=state=='invalid')
            control(frame,key,inner if mobile else inner+370,by+56 if mobile else by,iw if mobile else 342,'Batal',target('list') if state in ('new','invalid') else target('discard'))
            if state in ('new','invalid'):
                control(frame,key,x,body+1140 if mobile else body+660,pw,'Demo: isi contoh lengkap',target('filled'))
                control(frame,key,x,body+1196 if mobile else body+716,pw,'Demo: plat sudah terdaftar',target('known'))
        elif state in ('review','known-review','saved','known-saved','edited','locked'):
            success=state in ('saved','known-saved','edited')
            panel_w=pw if mobile else 752; inner=x+20; iw=panel_w-40
            rect(frame,x,body,panel_w,1064 if mobile and state=='edited' else 944 if mobile else 728)
            badge='Koreksi tersimpan' if state=='edited' else 'Registrasi tersimpan' if success else 'Terkunci setelah SO dibuat' if state=='locked' else 'Belum disimpan'
            text(frame,inner,body+20,iw,badge,14,'Success' if success else 'Warning' if state=='locked' else 'Muted','Semi Bold')
            text(frame,inner,body+60,iw,data['plate'],20,weight='Semi Bold')
            text(frame,inner,body+100,iw,data['reference'] if success or state=='locked' else 'Nomor diberikan setelah disimpan',12,'Muted')
            pairs=[('Pelanggan',data['customer']),('Nomor telepon',data['phone']),('Alamat',data['address']),('Keluhan awal',data['complaint'])]
            for i,(label,value) in enumerate(pairs):
                yy=body+150+i*(102 if mobile else 88)
                text(frame,inner,yy,iw,label,12,'Muted','Medium')
                text(frame,inner,yy+26,iw,value,14)
            ny=body+576 if mobile else body+518
            copy='SO-0261 sudah dibuat. Koreksi registrasi hanya oleh Owner dan wajib alasan.' if state=='locked' else 'Identitas kunjungan ini tersimpan sebagai snapshot. Diagnosa, SO dan tagihan belum dibuat.' if success else 'Periksa identitas dan keluhan. Menyimpan registrasi belum membuat diagnosa, SO atau tagihan.'
            notice(frame,inner,ny,iw,copy,role='WarningSurface' if state=='locked' else 'SuccessSurface' if success else 'Selected',ink='Warning' if state=='locked' else 'Success' if success else 'Service',h=108 if mobile else 68)
            by=body+710 if mobile else body+610
            if state in ('review','known-review'):
                control(frame,key,inner,by,iw if mobile else 342,'Simpan registrasi',target('known-saving' if state=='known-review' else 'saving'),kind='Primary')
                control(frame,key,inner if mobile else inner+370,by+56 if mobile else by,iw if mobile else 342,'Periksa isian',target('known' if state=='known-review' else 'filled'))
            else:
                if state=='locked': control(frame,key,inner,by,iw,'Koreksi registrasi',disabled=True)
                elif state!='known-saved': control(frame,key,inner,by,iw,'Koreksi registrasi',target('edit'))
                else: text(frame,inner,by,iw,'Kunjungan baru; kendaraan DEMO-V0261 dipakai ulang.',12,'Muted')
                control(frame,key,inner,by+64,iw,'Kembali ke registrasi',target('list' if state=='locked' else 'list-known' if state=='known-saved' else 'list-edited' if state=='edited' else 'list-saved'))
                if not mobile: text(frame,1008,body+24,390,'Langkah berikutnya',18,weight='Semi Bold'); text(frame,1008,body+68,390,'Teknisi atau Owner melanjutkan Diagnosa & Estimasi. Aksi ini tidak tersedia untuk Kasir.',14,'Muted')
                if state=='edited':
                    text(frame,inner,by+140,iw,'Riwayat koreksi · Kasir · contoh',13,weight='Semi Bold')
                    text(frame,inner,by+174,iw,'Keluhan sebelumnya: '+base['complaint'],12,'Muted')
                    text(frame,inner,by+230,iw,'Keluhan sekarang: '+corrected['complaint'],12,'Muted')
        elif state in ('saving','known-saving'):
            rect(frame,x,body,pw,420)
            text(frame,x+24,body+26,pw-48,'Menyimpan kunjungan '+data['plate'],18,weight='Semi Bold')
            text(frame,x+24,body+80,pw-48,'Tunggu hingga konfirmasi tampil. Hindari mengirim ulang saat proses berjalan.',14,'Muted')
            for i in range(3): rect(frame,x+24,body+168+i*56,pw-48,32,'Secondary',8,border='Secondary')
            control(frame,key,x+24,body+344,pw-48,'Menyimpan…',kind='Primary',disabled=True)
            to=target('known-saved' if state=='known-saving' else 'saved')
            c('proto.interaction.add',{'id':frame,'trigger':{'type':'afterDelay','ms':1000},'dest':frames[to],'transition':{'type':'instant'}})
            timers.append({'source':key,'target':to,'milliseconds':1000})
        elif state=='catalog':
            rect(frame,x,body,pw,1120)
            text(frame,x+20,body+22,pw-40,'Kontrol tinjauan · skenario data contoh',14,'Muted')
            options=[('Form kosong','new'),('Validasi isian wajib','invalid'),('Isian contoh lengkap','filled'),('Plat sudah terdaftar','known'),('Koreksi setelah SO dibuat','locked'),('Daftar kosong','empty'),('Pencarian tanpa hasil','no-results'),('Gagal memuat daftar','load-error'),('Offline saat menyimpan','offline'),('Gagal simpan','save-error')]
            for i,(label,to) in enumerate(options): control(frame,key,x+20,body+92+i*72,pw-40,label,target(to))
            control(frame,key,x+20,body+860,pw-40,'Kembali ke registrasi',target('list'))
            control(frame,key,x+20,body+928,pw-40,'Buka POS Kasir',device+'-list')
        else:
            rect(frame,x,body,pw,600 if mobile else 504)
            copy={
                'discard':'Isian belum disimpan sebagai registrasi. Kembali untuk melanjutkan, atau tinggalkan isian contoh ini.',
                'empty':'Belum ada kunjungan pada daftar ini. Buat registrasi saat kendaraan datang.',
                'no-results':'Tidak ada registrasi untuk DD 0000 XX. Coba plat, nama pelanggan atau nomor registrasi lain.',
                'load-error':'Daftar registrasi belum dapat ditampilkan. Coba muat kembali.',
                'offline':'Isian contoh masih ditampilkan, tetapi registrasi belum tersimpan. Periksa koneksi lalu coba lagi.',
                'save-error':'Penyimpanan belum berhasil. Isian contoh tetap tersedia untuk diperiksa sebelum mencoba lagi.'}[state]
            text(frame,x+24,body+28,pw-48,copy,16)
            if state in ('offline','save-error'):
                text(frame,x+24,body+208,pw-48,base['plate']+' · '+base['customer'],16,weight='Semi Bold')
                text(frame,x+24,body+248,pw-48,'Belum ada nomor registrasi atau dokumen lanjutan.',13,'Warning')
            by=body+344 if mobile else body+264
            if state=='discard':
                control(frame,key,x+24,by,pw-48,'Lanjutkan mengisi',target('filled'),kind='Primary')
                control(frame,key,x+24,by+68,pw-48,'Tinggalkan isian',target('list'))
            elif state=='empty':
                control(frame,key,x+24,by,pw-48,'Registrasi baru',target('new'),kind='Primary')
                control(frame,key,x+24,by+68,pw-48,'Kembali ke daftar',target('list'))
            else:
                control(frame,key,x+24,by,pw-48,'Hapus pencarian' if state=='no-results' else 'Coba muat lagi' if state=='load-error' else 'Periksa isian',target('list') if state in ('no-results','load-error') else target('review'),kind='Primary')
                control(frame,key,x+24,by+68,pw-48,'Kembali ke daftar',target('list'))
        save_map()
        print(json.dumps({'built':key}),flush=True)
    # Connect existing registration labels without altering approved cashier links.
    current=api.ask('document.inspect',{'allPages':True,'depth':2})
    native={n['id']:n for p in current['pages'] for n in p.get('children',[])}
    for key,frame_id in cash['frames'].items():
        device=key.split('-',1)[0]; frame=native[frame_id]
        positions[frame_id]=(frame['x'],frame['y'])
        labels=[n for n in frame.get('children',[]) if n.get('characters')=='Registrasi' and n.get('visible',True)]
        for label in labels:
            control(frame_id,key,max(16,label['x']-12),label['y']-10,max(150,label['width']+24),'Buka Registrasi',key_for(device,'list'),kind='InteractionArea')
        if key.endswith('-catalog'):
            control(frame_id,key,16 if device=='mobile' else 252,944,358 if device=='mobile' else 1144,'Buka Registrasi',key_for(device,'list'))
    for device in ('desktop','mobile'):
        c('page.select',{'id':pages['mobile' if device=='mobile' else 'desktop']})
        c('proto.flow.add',{'start':frames[key_for(device,'list')],'name':'Registrasi / '+('Ponsel' if device=='mobile' else 'Desktop')+' / Demo kunjungan'})
    save_map()
    c('page.select',{'id':pages['desktop']})
    c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    c('proto.preview',{'start':frames['desktop-reg-list']})
    print(json.dumps({'registrationFrames':len(frames),'links':len(edges),'instances':len(instances),'timers':len(timers)}))
finally:
    api.close()
