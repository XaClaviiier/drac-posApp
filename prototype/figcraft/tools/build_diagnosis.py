"""One-time native Diagnosa & Estimasi slice, preserving approved prior modules."""
import json, zipfile
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
api=Native();c=api.command
foundation=json.loads((ROOT/'evidence/foundations.json').read_text())
reg=json.loads((ROOT/'evidence/registration-map.json').read_text())
cash=json.loads((ROOT/'evidence/design-completion-map.json').read_text())
pages=json.loads((ROOT/'evidence/consolidation.json').read_text())['pages']
frames,edges,themes,instances,timers,positions={},{},{},[],[],{}
edges=[]
states=['hub','origin','list','new','invalid','findings','partial','catalog-service',
        'catalog-part','service','draft','saved','qty-error','approve','approve-ready',
        'approving','approved','so-review','so-created','approved-linked',
        'price-edit','price-valid','price-approve','price-approve-ready','price-approving',
        'price-approved','price-so-review','price-so-created','price-approved-linked',
        'readonly','no-diagnosis','owner-log','offline','conflict','conflict-local',
        'save-error','approve-error','check-status','empty','no-results','load-error',
        'discard','fraction-demo']
fixture={**reg['fixtures']['new'],'estimate':'EST-DEMO-0147','order':'SO-DEMO-0147',
         'findings':'Aliran udara lemah; filter kabin kotor.',
         'recommendations':'Pemeriksaan AC dan penggantian filter kabin.',
         'reason':'Penyesuaian harga pemeriksaan untuk kunjungan ini.',
         'items':[{'name':'Pemeriksaan AC','kind':'Jasa','qty':'1','unit':'pekerjaan','price':50000,'subtotal':50000},
                  {'name':'Filter kabin','kind':'Part','qty':'1','unit':'pcs','price':100000,'subtotal':100000}],
         'total':150000,'localServicePrice':45000,'localTotal':145000,
         'fraction':{'name':'Refrigeran timbang','qty':'0.500','unit':'kg','price':200001,'subtotal':100001}}
editor_states={'new','invalid','findings','partial','service','draft','saved','qty-error','price-edit','price-valid'}
dirty_states={'findings','service','draft','qty-error','price-edit','price-valid'}
def key(device,state):return device+'-diag-'+state
def role(state):return 'Kasir' if state in ('readonly','no-diagnosis') else 'Owner' if state=='owner-log' else 'Demo' if state=='hub' else 'Teknisi'
def money(value):return 'Rp'+format(value,',').replace(',','.')
def color(name):return {'$var':foundation['variables'][name]}
def text(parent,x,y,w,value,size=14,ink='Text',weight='Regular',right=False):
    return api.node('text',parent,x=x,y=y,width=w,text=value,props={'fontFamily':'Poppins','fontStyle':weight,'fontSize':size,'lineHeight':'150%','fill':color(ink),'textAlign':'right' if right else 'left'})
def box(parent,x,y,w,h,fill='Surface',border='Border',radius=12):
    return api.node('rectangle',parent,x=x,y=y,width=w,height=h,props={'fill':color(fill),'stroke':color(border),'cornerRadius':radius})
def target_id(dest):return frames[dest] if dest in frames else reg['frames'][dest] if dest in reg['frames'] else cash['frames'][dest]
def nav(node,source,dest,label):
    c('proto.interaction.add',{'id':node,'dest':target_id(dest),'transition':{'type':'instant'}})
    edges.append({'source':source,'target':dest,'node':node,'label':label})
def button(frame,source,x,y,w,label,dest=None,kind='Secondary',disabled=False,h=44):
    device=source.split('-',1)[0];c('page.select',{'id':pages['mobile' if device=='mobile' else 'desktop']})
    px,py=positions[frame]
    node=c('instance.place',{'component':foundation['buttons'][kind],'x':px+x+w/2,'y':py+y+h/2})['id']
    c('node.reparent',{'ids':[node],'parent':frame});api.set(node,x=x,y=y,width=w,height=h,name=label)
    if kind!='InteractionArea':c('instance.setProperties',{'ids':[node],'properties':{'Label':label}})
    if disabled:c('instance.setProperties',{'ids':[node],'properties':{'State':'Disabled'}})
    if dest:nav(node,source,dest,label)
    instances.append(node);return node
def notice(frame,x,y,w,value,fill='Selected',ink='Service',h=80):
    box(frame,x,y,w,h,fill,fill,8);text(frame,x+16,y+14,w-32,value,13,ink)
def snapshot():
    (ROOT/'evidence/diagnosis-map.json').write_text(json.dumps({'frames':frames,'edges':edges,'themeControls':themes,'instances':instances,'timers':timers,'fixture':fixture,'roles':{k:role(k.split('-diag-')[1]) for k in frames}},indent=2))
def identity(frame,x,y,w,registration=True):
    text(frame,x,y,w,fixture['plate']+' · '+fixture['customer'],18,weight='Semi Bold')
    text(frame,x,y+34,w,fixture['reference']+' · '+fixture['estimate'],12,'Muted')
    if registration:text(frame,x,y+65,w,'Keluhan: '+fixture['complaint'],13,'Muted')
def summary(frame,x,y,w,priced=False,items=2):
    service=fixture['localServicePrice'] if priced else 50000
    text(frame,x,y,w,'Jasa',13,'Muted');text(frame,x,y,w,money(service if items else 0),13,right=True)
    text(frame,x,y+34,w,'Part',13,'Muted');text(frame,x,y+34,w,money(100000 if items==2 else 0),13,right=True)
    total=(service+(100000 if items==2 else 0)) if items else 0
    text(frame,x,y+82,w,'Total estimasi',14,weight='Medium')
    text(frame,x,y+118,w,money(total),24,weight='Bold',right=True)
    return total
def items_view(frame,x,y,w,mobile,source,priced=False,editable=False,count=2,qty_error=False):
    for i,item in enumerate(fixture['items'][:count]):
        iy=y+i*(244 if mobile else 202);height=228 if mobile else 186
        box(frame,x,iy,w,height)
        ink='Service' if i==0 else 'Part';tint='Selected' if i==0 else 'PartSurface'
        box(frame,x+16,iy+16,62,24,tint,tint,6);text(frame,x+24,iy+18,50,item['kind'],12,ink,'Medium')
        text(frame,x+16,iy+54,w-32,item['name'],16,weight='Semi Bold')
        if editable:
            button(frame,source,x+w-96,iy+8,80,'Hapus',key(source.split('-')[0],'findings' if count==1 else 'service'))
        col=(w-48)/2
        text(frame,x+16,iy+92,col,'Jumlah · '+item['unit'],12,'Muted')
        text(frame,x+32+col,iy+92,col,'Harga jual satuan',12,'Muted')
        for fx,fw,val,err in [(x+16,col,'0,5' if qty_error and i==1 else '1',qty_error and i==1),
                              (x+32+col,col,money(45000 if priced and i==0 else item['price']),False)]:
            box(frame,fx,iy+116,fw,44,'Surface','Error' if err else 'Input',8)
            text(frame,fx+10,iy+126,fw-20,val,14)
        if editable and i==1 and not priced and not qty_error:
            button(frame,source,x+16,iy+116,col,'Contoh qty tidak valid',key(source.split('-')[0],'qty-error'),kind='InteractionArea')
        if editable and i==0 and count==2 and not priced and not qty_error:
            button(frame,source,x+32+col,iy+116,col,'Contoh ubah harga lokal',key(source.split('-')[0],'price-edit'),kind='InteractionArea')
        if mobile:
            text(frame,x+16,iy+184,w-32,'Qty pcs harus bulat positif.' if qty_error and i==1 else 'Subtotal',12,'Error' if qty_error and i==1 else 'Muted')
            text(frame,x+16,iy+184,w-32,'—' if qty_error and i==1 else money(45000 if priced and i==0 else item['subtotal']),14,weight='Semi Bold',right=True)
    return y+count*(244 if mobile else 202)

try:
    doc=api.ask('document.inspect',{'allPages':True,'depth':1})
    assert not api.ask('ui.inspect')['status']['dirty'],'Save manual edits first'
    assert not any('-diag-' in n['name'] for p in doc['pages'] for n in p.get('children',[])),'Migration already started'
    with zipfile.ZipFile(ROOT/'archive/before-diagnosis.zip','w',zipfile.ZIP_DEFLATED) as archive:archive.write(ROOT/'pos-kasir.figcraft','pos-kasir.figcraft')
    c('proto.closePreview')
    for device in ('desktop','mobile'):
        mobile=device=='mobile';w,h=(390,844) if mobile else (1440,1000)
        c('page.select',{'id':pages['mobile' if mobile else 'desktop']})
        for i,state in enumerate(states):
            xx=(i%4)*(w+64);yy=(20+i//4)*(h+100)
            frame=api.node('frame',x=xx,y=yy,width=w,height=h,name=key(device,state),props={'fill':color('Canvas'),'clip':True,'overflow':'vertical'})
            frames[key(device,state)]=frame;positions[frame]=(xx,yy)
    snapshot()
    for source,frame in frames.items():
        device,state=source.split('-diag-');mobile=device=='mobile';actor=role(state)
        w=390 if mobile else 1440;x=16 if mobile else 232;pw=358 if mobile else 1184
        body=258 if mobile else 196;to=lambda s:key(device,s)
        title='Diagnosa & Estimasi'
        if state=='hub':title='Journey diagnosa'
        elif state=='origin':title='Kunjungan untuk diperiksa'
        elif state.startswith('catalog-'):title='Pilih jasa dan part'
        elif state=='owner-log':title='Riwayat harga lokal'
        elif 'so-' in state:title='Service Order awal'
        elif state=='discard':title='Tinggalkan perubahan?'
        elif state=='fraction-demo':title='Contoh qty pecahan'
        elif state in ('conflict','conflict-local'):title='Versi estimasi berbeda'
        box(frame,0,0,w,64,'Surface',radius=0)
        text(frame,16 if mobile else 232,8 if mobile else 18,170,'Bengkel AC',16,weight='Semi Bold')
        text(frame,16 if mobile else 420,36 if mobile else 22,170,actor+' · Data contoh',12,'Muted')
        if not mobile:
            box(frame,0,0,208,1000,'Surface',radius=0);text(frame,24,22,160,'Bengkel AC',18,weight='Semi Bold')
            button(frame,source,16,80,176,'Registrasi' if actor=='Kasir' else 'Kunjungan',device+'-reg-saved' if actor=='Kasir' else to('origin') if actor!='Owner' else None,disabled=actor=='Owner')
            box(frame,16,136,176,44,'Selected','Selected',8);text(frame,30,147,156,'Diagnosa & Estimasi',13,'Service','Semi Bold')
            button(frame,source,16,136,176,'Daftar diagnosa',to('readonly' if actor=='Kasir' else 'owner-log' if actor=='Owner' else 'list'),kind='InteractionArea')
            text(frame,24,930,164,actor+' · Simulasi',12,'Muted')
        else:
            button(frame,source,16,76,174,'Registrasi' if actor=='Kasir' else 'Kunjungan',device+'-reg-saved' if actor=='Kasir' else to('origin') if actor!='Owner' else None,disabled=actor=='Owner')
            box(frame,198,76,176,44,'Selected','Selected',8);text(frame,214,87,144,'Diagnosa',14,'Service','Semi Bold')
            button(frame,source,198,76,176,'Daftar diagnosa',to('readonly' if actor=='Kasir' else 'owner-log' if actor=='Owner' else 'list'),kind='InteractionArea')
        button(frame,source,202 if mobile else 1192,8,100 if mobile else 108,'Demo',to('hub'))
        theme=button(frame,source,310 if mobile else 1312,8,64 if mobile else 112,'Tema');themes[source]=theme
        c('proto.interaction.add',{'id':theme,'action':{'type':'conditional','blocks':[{'expression':'mode(POS) == "Dark"','actions':[{'type':'setVariableMode','collection':foundation['collection'],'mode':'Light'}]},{'actions':[{'type':'setVariableMode','collection':foundation['collection'],'mode':'Dark'}]}]},'transition':{'type':'instant'}})
        text(frame,x,148 if mobile else 88,pw,title,24 if mobile else 28,weight='Semi Bold')
        text(frame,x,190 if mobile else 136,pw,'Pemeriksaan dan rencana biaya untuk kunjungan ini.',13,'Muted')
        if state=='discard':c('proto.interaction.add',{'id':frame,'trigger':{'type':'keyPress','key':'Escape'},'action':{'type':'back'},'transition':{'type':'instant'}})
        elif state not in ('approving','price-approving'):
            c('proto.interaction.add',{'id':frame,'trigger':{'type':'keyPress','key':'Escape'},'dest':frames[to('discard' if state in dirty_states else 'readonly' if actor=='Kasir' else 'owner-log' if actor=='Owner' else 'list')],'transition':{'type':'instant'}})
        priced=state.startswith('price-') or state in ('owner-log','conflict-local')
        if state=='hub':
            box(frame,x,body,pw,1310)
            text(frame,x+20,body+20,pw-40,'Simulasi peran dan skenario · bukan pergantian akun nyata',13,'Muted')
            options=[('Journey Teknisi','origin'),('Baca sebagai Kasir','readonly'),('Log harga sebagai Owner','owner-log'),
                     ('Draf kosong','new'),('Draf parsial tersimpan','partial'),('Isian lengkap','draft'),
                     ('Qty pcs tidak valid','qty-error'),('Harga lokal perlu alasan','price-edit'),
                     ('Contoh pembulatan qty pecahan','fraction-demo'),('Draf offline','offline'),
                     ('Konflik dengan versi disetujui','conflict'),('Simpan draf gagal','save-error'),
                     ('Pencatatan approval perlu diperiksa','approve-error'),('Daftar kosong','empty'),
                     ('Pencarian tanpa hasil','no-results'),('Gagal memuat','load-error')]
            for i,(label,target) in enumerate(options):button(frame,source,x+20,body+96+i*68,pw-40,label,to(target))
            button(frame,source,x+20,body+1216,pw-40,'Kembali ke Registrasi (Kasir)',device+'-reg-saved')
        elif state in ('origin','no-diagnosis'):
            box(frame,x,body,pw,620 if mobile else 500);identity(frame,x+20,body+24,pw-40)
            notice(frame,x+20,body+180,pw-40,'Diagnosa belum dibuat untuk kunjungan ini. Identitas dan keluhan mengambil snapshot registrasi.',h=116 if mobile else 76)
            button(frame,source,x+20,body+340,pw-40,'Buat diagnosa',to('new') if actor=='Teknisi' else None,kind='Primary',disabled=actor=='Kasir')
            if actor=='Kasir':
                text(frame,x+20,body+408,pw-40,'Kasir membaca dokumen yang sudah ada. Pembuatan dilakukan Teknisi/Owner.',13,'Muted')
                button(frame,source,x+20,body+520,pw-40,'Demo: journey Teknisi',to('origin'))
            else:button(frame,source,x+20,body+412,pw-40,'Lihat daftar diagnosa',to('list'))
        elif state=='list':
            box(frame,x,body,pw,48,'Surface','Input',8);text(frame,x+16,body+13,pw-32,'Cari plat, pelanggan atau nomor dokumen',14,'Muted')
            button(frame,source,x,body,pw,'Contoh hasil pencarian kosong',to('no-results'),kind='InteractionArea',h=48)
            box(frame,x,body+80,pw,324);identity(frame,x+20,body+102,pw-40)
            text(frame,x+20,body+226,pw-40,'Kunjungan terdaftar · Diagnosa belum dibuat',13,'Service')
            button(frame,source,x+20,body+284,pw-40,'Periksa kunjungan',to('origin'),kind='Primary')
        elif state in editor_states:
            count=0 if state in ('new','invalid','findings','partial') else 1 if state=='service' else 2
            panel_w=pw if mobile else 752;inner=x+20;iw=panel_w-40
            item_y=body+438 if mobile else body+380
            end=item_y+count*(244 if mobile else 202)
            box(frame,x,body,panel_w,(end-body)+540 if mobile else max(970,end-body+290))
            identity(frame,inner,body+20,iw)
            empty=state in ('new','invalid','partial')
            for label,field,dy in [('Temuan pemeriksaan','findings',118),('Rekomendasi tindakan','recommendations',268 if mobile else 244)]:
                yy=body+dy;text(frame,inner,yy,iw,label,13,weight='Medium')
                box(frame,inner,yy+26,iw,96 if mobile else 76,'Surface','Error' if state=='invalid' else 'Input',8)
                text(frame,inner+12,yy+38,iw-24,'Belum diisi' if empty else fixture[field],14,'Muted' if empty else 'Text')
                if state=='invalid':text(frame,inner,yy+(126 if mobile else 108),iw,'Lengkapi '+label.lower()+'.',12,'Error')
            text(frame,inner,item_y-30,iw,'Rincian estimasi',18,weight='Semi Bold')
            if count:items_view(frame,inner,item_y,iw,mobile,source,priced,True,count,state=='qty-error')
            else:
                notice(frame,inner,item_y,iw,'Belum ada item. Pilih jasa atau part dari katalog.',h=96 if mobile else 72)
                if state=='invalid':text(frame,inner,item_y+110,iw,'Tambahkan minimal satu item sebelum persetujuan.',12,'Error')
                end=item_y+(150 if mobile else 128)
            if state=='qty-error':
                notice(frame,inner,end+8,iw,'Jumlah 0,5 pcs tidak valid. Subtotal dan total belum dapat disahkan. Gunakan pcs bulat positif.',fill='ErrorSurface',ink='Error',h=112 if mobile else 72)
            elif state in ('price-edit','price-valid'):
                text(frame,inner,end+10,iw,'Alasan perubahan harga jual lokal',13,weight='Medium')
                box(frame,inner,end+38,iw,88 if mobile else 60,'Surface','Error' if state=='price-edit' else 'Input',8)
                text(frame,inner+12,end+50,iw-24,'Wajib diisi sebelum persetujuan.' if state=='price-edit' else fixture['reason'],13,'Error' if state=='price-edit' else 'Text')
                text(frame,inner,end+140,iw,'Harga katalog tetap Rp50.000; harga lokal Rp45.000.',12,'Muted')
            elif state=='partial':notice(frame,inner,end+8,iw,'Draf parsial tersimpan · simulasi. Belum lengkap dan belum disetujui.',fill='SuccessSurface',ink='Success',h=104 if mobile else 72)
            elif state=='saved':notice(frame,inner,end+8,iw,'Draf tersimpan · simulasi. Persetujuan pelanggan belum dicatat.',fill='SuccessSurface',ink='Success',h=96 if mobile else 64)
            if mobile:
                sy=end+188 if state in ('price-edit','price-valid') else end+146 if state in ('qty-error','partial','saved') else end+24
                if state!='qty-error':summary(frame,inner,sy,iw,priced,count)
                by=sy+190
            else:
                box(frame,1008,body,408,450);text(frame,1032,body+24,360,'Ringkasan estimasi',18,weight='Semi Bold')
                if state=='qty-error':text(frame,1032,body+90,360,'Total belum dapat dihitung',18,'Error')
                else:summary(frame,1032,body+84,360,priced,count)
                text(frame,1032,body+280,360,'Harga jual contoh. Belum menjadi invoice, pembayaran atau reservasi part.',13,'Muted')
                by=body+470
                if state in ('new','invalid','findings','service','draft'):button(frame,source,1032,by,360,'Pilih jasa / part',to('catalog-part' if count else 'catalog-service'))
                by+=68
            action_x=inner if mobile else 1032; action_w=iw if mobile else 360
            if mobile and state in ('new','invalid','findings','service','draft'):
                button(frame,source,action_x,by,action_w,'Pilih jasa / part',to('catalog-part' if count else 'catalog-service'));by+=60
            if state in ('new','invalid','partial'):
                button(frame,source,action_x,by,action_w,'Simpan draf parsial',to('partial'));by+=60
                button(frame,source,action_x,by,action_w,'Catat persetujuan',to('invalid') if state=='new' else None,kind='Primary',disabled=state!='new');by+=60
                button(frame,source,action_x,by,action_w,'Demo: isi pemeriksaan',to('findings'))
            elif state=='qty-error':button(frame,source,action_x,by,action_w,'Gunakan qty 1 pcs',to('draft'),kind='Primary')
            elif state=='price-edit':button(frame,source,action_x,by,action_w,'Demo: isi alasan',to('price-valid'),kind='Primary')
            elif state=='price-valid':button(frame,source,action_x,by,action_w,'Tinjau dan catat persetujuan',to('price-approve'),kind='Primary')
            else:
                button(frame,source,action_x,by,action_w,'Simpan draf',to('saved' if count==2 else 'service' if count else 'partial'));by+=60
                button(frame,source,action_x,by,action_w,'Tinjau dan catat persetujuan',to('approve') if count==2 else None,kind='Primary',disabled=count!=2)
            button(frame,source,action_x,by+76,action_w,'Batal',to('discard') if state in dirty_states else to('list'))
        elif state.startswith('catalog-'):
            box(frame,x,body,pw,544);identity(frame,x+20,body+24,pw-40,False)
            label='Pemeriksaan AC · 1 pekerjaan · Rp50.000' if state=='catalog-service' else 'Filter kabin · 1 pcs · Rp100.000'
            notice(frame,x+20,body+130,pw-40,label,h=88 if mobile else 64)
            text(frame,x+20,body+242,pw-40,'Harga jual katalog contoh; penambahan ini hanya mengisi estimasi.',14,'Muted')
            button(frame,source,x+20,body+350,pw-40,'Tambahkan item',to('service' if state=='catalog-service' else 'draft'),kind='Primary')
            button(frame,source,x+20,body+420,pw-40,'Kembali',to('findings' if state=='catalog-service' else 'service'))
        elif state in ('approve','approve-ready','price-approve','price-approve-ready','approved','price-approved','approved-linked','price-approved-linked','readonly'):
            approved=state in ('approved','price-approved','approved-linked','price-approved-linked','readonly')
            linked=state.endswith('-linked');ready=state.endswith('-ready')
            panel_w=pw if mobile else 752;inner=x+20;iw=panel_w-40
            rows_y=body+300 if mobile else body+260
            end=rows_y+2*(244 if mobile else 202)
            box(frame,x,body,panel_w,end-body+(500 if mobile else 340))
            identity(frame,inner,body+20,iw)
            text(frame,inner,body+130,iw,'Disetujui · terkunci' if approved else 'Tinjau sebelum persetujuan',14,'Success' if approved else 'Warning','Semi Bold')
            text(frame,inner,body+170,iw,fixture['findings']+'\n'+fixture['recommendations'],14)
            items_view(frame,inner,rows_y,iw,mobile,source,priced)
            if mobile:summary(frame,inner,end+20,iw,priced);by=end+210;ax=inner;aw=iw
            else:
                box(frame,1008,body,408,460);text(frame,1032,body+24,360,'Ringkasan estimasi',18,weight='Semi Bold');summary(frame,1032,body+80,360,priced);by=body+320;ax=1032;aw=360
            if approved:
                text(frame,inner,end+(220 if mobile else 24),iw,'Persetujuan lisan dicatat Teknisi (contoh), 15 Nov 2026 pukul 09.55. EST-DEMO-0147 revisi 2.',12,'Muted')
                if mobile:by=end+310
                if actor=='Kasir':
                    notice(frame,ax,by,aw,'Akses baca Kasir. Perubahan, persetujuan dan pembuatan SO dilakukan Teknisi/Owner.',h=116 if mobile else 100)
                    button(frame,source,ax,by+140,aw,'Kembali ke Registrasi',device+'-reg-saved')
                else:
                    button(frame,source,ax,by,aw,'Lihat Service Order' if linked else 'Buat Service Order',to(('price-' if priced else '')+('so-created' if linked else 'so-review')),kind='Primary')
                    text(frame,ax,by+78,aw,'Acuan disetujui terkunci. Perubahan realisasi dikelola pada SO.',13,'Muted')
            else:
                check=button(frame,source,ax,by,aw,'✓ Setuju' if ready else 'Setuju',to(('price-' if priced else '')+('approve' if ready else 'approve-ready')))
                text(frame,ax,by+64,aw,'Tandai hanya setelah pelanggan menyetujui rincian dan total estimasi.',13,'Muted')
                button(frame,source,ax,by+158,aw,'Catat persetujuan',to(('price-' if priced else '')+'approving') if ready else None,kind='Primary',disabled=not ready)
                button(frame,source,ax,by+220,aw,'Periksa draf',to('price-valid' if priced else 'saved'))
        elif state in ('approving','price-approving'):
            box(frame,x,body,pw,444);identity(frame,x+20,body+22,pw-40)
            text(frame,x+20,body+170,pw-40,'Mencatat persetujuan '+money(145000 if priced else 150000),18,weight='Semi Bold')
            text(frame,x+20,body+232,pw-40,'Tunggu konfirmasi sebelum melanjutkan ke Service Order.',14,'Muted')
            button(frame,source,x+20,body+340,pw-40,'Mencatat…',kind='Primary',disabled=True)
            dest=to('price-approved' if priced else 'approved')
            c('proto.interaction.add',{'id':frame,'trigger':{'type':'afterDelay','ms':1000},'dest':frames[dest],'transition':{'type':'instant'}})
            timers.append({'source':source,'target':dest,'milliseconds':1000})
        elif state in ('so-review','price-so-review','so-created','price-so-created'):
            created=state.endswith('created');panel_w=pw if mobile else 752;inner=x+20;iw=panel_w-40
            rows_y=body+240;end=rows_y+2*(244 if mobile else 202)
            box(frame,x,body,panel_w,end-body+470);identity(frame,inner,body+20,iw)
            text(frame,inner,body+136,iw,fixture['order']+' · Belum dimulai' if created else 'Salin rincian estimasi disetujui',16,'Success' if created else 'Service','Semi Bold')
            text(frame,inner,body+184,iw,'Satu SO untuk kunjungan ini. Estimasi acuan tetap dipertahankan.',13,'Muted')
            items_view(frame,inner,rows_y,iw,mobile,source,priced)
            summary(frame,inner,end+18,iw,priced);by=end+206
            if created:
                text(frame,inner,by,iw,'Belum ada Teknisi ditugaskan. Pengerjaan belum dimulai; belum ada invoice atau pembayaran.',13,'Muted')
                button(frame,source,inner,by+108,iw,'Buka estimasi acuan',to(('price-' if priced else '')+'approved-linked'))
            else:
                button(frame,source,inner,by,iw,'Buat Service Order',to(('price-' if priced else '')+'so-created'),kind='Primary')
                button(frame,source,inner,by+68,iw,'Kembali ke estimasi',to('price-approved' if priced else 'approved'))
        elif state=='owner-log':
            box(frame,x,body,pw,824);identity(frame,x+20,body+24,pw-40)
            notice(frame,x+20,body+166,pw-40,'Owner · Riwayat perubahan harga lokal estimasi',h=80)
            rows=[('Item','Pemeriksaan AC'),('Sebelum','Rp50.000'),('Sesudah','Rp45.000'),('Alasan',fixture['reason']),('Pelaku / waktu','Teknisi (contoh) · 15 Nov 2026 09.50'),('Dokumen',fixture['estimate']+' · harga katalog tetap Rp50.000')]
            yy=body+280
            for label,value in rows:
                text(frame,x+20,yy,pw-40,label,12,'Muted');text(frame,x+20,yy+26,pw-40,value,14);yy+=92 if mobile else 78
        elif state=='fraction-demo':
            box(frame,x,body,pw,680);identity(frame,x+20,body+24,pw-40,False)
            text(frame,x+20,body+132,pw-40,'Contoh perhitungan terpisah',16,weight='Semi Bold')
            text(frame,x+20,body+184,pw-40,'Refrigeran timbang\n0,500 kg × Rp200.001 = Rp100.000,50\nSubtotal dibulatkan menjadi Rp100.001',16)
            text(frame,x+20,body+316,pw-40,'Kg/liter/meter/jam mendukung maksimal tiga desimal. Pcs/unit/pekerjaan memakai jumlah bulat positif.',14,'Muted')
            notice(frame,x+20,body+426,pw-40,'Skenario hitung ini tidak ditambahkan ke estimasi acuan Rp150.000.',h=96 if mobile else 64)
            button(frame,source,x+20,body+570,pw-40,'Tutup contoh hitung',to('hub'))
        elif state=='discard':
            box(frame,x,body,pw,464);text(frame,x+24,body+28,pw-48,'Perubahan contoh belum disimpan. Lanjutkan mengisi atau tinggalkan perubahan ini.',16)
            back=button(frame,source,x+24,body+224,pw-48,'Lanjutkan mengisi')
            c('proto.interaction.add',{'id':back,'action':{'type':'back'},'transition':{'type':'instant'}})
            edges.append({'source':source,'target':to('draft'),'node':back,'label':'Lanjutkan mengisi','historyBack':True})
            button(frame,source,x+24,body+296,pw-48,'Tinggalkan perubahan',to('list'))
        else:
            box(frame,x,body,pw,930 if state in ('conflict','conflict-local') else 680)
            identity(frame,x+20,body+22,pw-40)
            copy={
                'offline':'Draf lokal · simulasi. Belum disinkronkan; persetujuan belum dicatat dan part belum direservasi.',
                'conflict':'Versi lokal 1 berbeda dari versi server 2 yang sudah disetujui. Salinan lokal dipertahankan dan tidak menimpa estimasi acuan.',
                'conflict-local':'Salinan lokal · baca saja. Usulan harga pemeriksaan Rp45.000 menghasilkan Rp145.000; versi server Rp150.000 sudah disetujui.',
                'save-error':'Draf belum berhasil disimpan. Isian contoh masih tersedia; jangan menganggap perubahan sudah tersimpan.',
                'approve-error':'Hasil pencatatan persetujuan belum dapat dipastikan. Periksa status sebelum mengirim ulang.',
                'check-status':'Pada skenario ini persetujuan belum tercatat. Draf server masih tersedia dan belum membuat Service Order.',
                'empty':'Belum ada kunjungan untuk diperiksa pada daftar ini.',
                'no-results':'Tidak ada hasil untuk DD 0000 XX. Coba plat, nama atau nomor dokumen lain.',
                'load-error':'Daftar diagnosa belum dapat dimuat. Periksa koneksi dan coba lagi.'}[state]
            notice(frame,x+20,body+170,pw-40,copy,fill='WarningSurface',ink='Warning',h=188 if mobile else 100)
            if state=='conflict':
                text(frame,x+20,body+390,pw-40,'Server revisi 2 · disetujui · Rp150.000\nLokal revisi 1 · usulan Rp145.000',16)
                button(frame,source,x+20,body+550,pw-40,'Buka versi server',to('approved'),kind='Primary')
                button(frame,source,x+20,body+620,pw-40,'Lihat salinan lokal',to('conflict-local'))
            elif state=='conflict-local':
                text(frame,x+20,body+390,pw-40,'Temuan lokal: '+fixture['findings']+'\nAlasan harga lokal: '+fixture['reason'],14)
                button(frame,source,x+20,body+600,pw-40,'Simpan ke versi server',disabled=True)
                button(frame,source,x+20,body+670,pw-40,'Kembali membandingkan',to('conflict'))
            else:
                label,target=('Periksa status','check-status') if state=='approve-error' else ('Kembali ke draf','saved') if state=='check-status' else ('Periksa isian','draft') if state in ('save-error','offline') else ('Hapus pencarian','list') if state=='no-results' else ('Coba lagi','list')
                button(frame,source,x+20,body+426,pw-40,label,to(target),kind='Primary')
                if state=='offline':button(frame,source,x+20,body+496,pw-40,'Catat persetujuan',disabled=True)
        snapshot();print(json.dumps({'built':source}),flush=True)
    # Entry from registration preserves the cashier role until a demo role is chosen.
    current=api.ask('document.inspect',{'allPages':True,'depth':1})
    roots={n['id']:n for p in current['pages'] for n in p.get('children',[])}
    for device in ('desktop','mobile'):
        for source,xx,yy,ww,label,dest in [
            (device+'-reg-saved',16 if device=='mobile' else 1008,1120 if device=='mobile' else 380,358 if device=='mobile' else 390,'Buka Diagnosa',key(device,'no-diagnosis')),
            (device+'-reg-catalog',36 if device=='mobile' else 252,1258 if device=='mobile' else 1196,318 if device=='mobile' else 1144,'Demo: Diagnosa & Estimasi',key(device,'hub')),
            (device+'-catalog',36 if device=='mobile' else 252,1008,318 if device=='mobile' else 1144,'Demo: Diagnosa & Estimasi',key(device,'hub'))]:
            frame=reg['frames'][source] if source in reg['frames'] else cash['frames'][source]
            positions[frame]=(roots[frame]['x'],roots[frame]['y'])
            button(frame,source,xx,yy,ww,label,dest)
        c('page.select',{'id':pages['mobile' if device=='mobile' else 'desktop']})
        c('proto.flow.add',{'start':frames[key(device,'origin')],'name':'Diagnosa / '+('Ponsel' if device=='mobile' else 'Desktop')+' / Teknisi / REG-DEMO-0147'})
        c('proto.flow.add',{'start':frames[key(device,'readonly')],'name':'Diagnosa / '+('Ponsel' if device=='mobile' else 'Desktop')+' / Kasir baca'})
    snapshot();c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
    c('proto.preview',{'start':frames['desktop-diag-origin']})
    print(json.dumps({'diagnosisFrames':len(frames),'links':len(edges),'instances':len(instances),'timers':len(timers)}))
finally:api.close()
