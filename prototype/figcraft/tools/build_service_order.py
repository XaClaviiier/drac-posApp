"""Native Service Order journey with shared demo state across progress screens."""
import json,zipfile,sys
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1]
api=Native();c=api.command
f=json.loads((ROOT/'evidence/foundations.json').read_text())
diag=json.loads((ROOT/'evidence/diagnosis-map.json').read_text())
reg=json.loads((ROOT/'evidence/registration-map.json').read_text())
cash=json.loads((ROOT/'evidence/design-completion-map.json').read_text())
states=['hub','list','ready','assign-none','assign-one','assign-b','assign-two','assigned','start',
        'running','pause','pause-filled','paused','real-empty','real-edit','real-missing',
        'real-invalid','real-consent','real-consent-ready','real-view','complete',
        'completed','cancel','cancel-filled','cancelled','handoff','queued',
        'owner-completed','reopen','reopen-filled','owner-queued','withdraw',
        'withdraw-filled','owner-withdrawn','readonly','estimate','history','owner-history',
        'blocked','offline','conflict','save-error','discard','empty','no-results','invoiced']
defaults={'SOActor':'Teknisi','SOOwner':False,'SOWriter':True,'SOAssigned':True,
 'SOTechs':'Teknisi A · Teknisi B','SOStatus':'Belum dimulai','SOActualSaved':True,
 'SOActualPrice':50000,'SOActualPriceText':'Rp50.000','SOActualHasPart':True,
 'SOActualPartText':'Rp100.000','SOActualPartQty':'1 pcs','SOActualTotal':150000,'SOActualTotalText':'Rp150.000',
 'SODraftPrice':50000,'SODraftPriceText':'Rp50.000','SODraftHasPart':True,
 'SODraftPartText':'Rp100.000','SODraftPartQty':'1 pcs','SODraftTotal':150000,'SODraftTotalText':'Rp150.000',
 'SODraftQtyValid':True,'SODraftReasonValid':False,'SODraftReason':'Belum diisi',
 'SOExtraConsent':False,'SOQueued':False,'SOFinal':False,'SOOffline':False,
 'SOConflict':False,'SOSaveFailure':False,'SOHasContext':False}
variables={};frames={};positions={};edges=[];instances=[];themes={};bound=[]
def K(device,state):return device+'-so-'+state
def color(name):return {'$var':f['variables'][name]}
def txt(parent,x,y,w,value,size=14,ink='Text',weight='Regular',var=None,right=False):
    n=api.node('text',parent,x=x,y=y,width=w,text=value,props={'fontFamily':'Poppins','fontSize':size,'fontStyle':weight,'lineHeight':'150%','fill':color(ink),'textAlign':'right' if right else 'left'})
    if var:
        c('variable.bind',{'ids':[n],'field':'text','variable':variables[var]});bound.append({'node':n,'variable':var})
    return n
def box(parent,x,y,w,h,fill='Surface',border='Border',r=12):return api.node('rectangle',parent,x=x,y=y,width=w,height=h,props={'fill':color(fill),'stroke':color(border),'cornerRadius':r})
def setv(name,value):
    kind='boolean' if isinstance(value,bool) else 'number' if isinstance(value,(int,float)) else 'string'
    return {'type':'setVariable','variable':variables[name],'value':{'type':kind,'value':value}}
def copyv(dest,source):return {**setv(dest,defaults[dest]),'expression':source}
def go(device,state):return {'type':'navigate','dest':frames[K(device,state)]}
def branch(expression,actions,otherwise):return {'type':'conditional','blocks':[{'expression':expression,'actions':actions},{'actions':otherwise}]}
def router(device):
    return {'type':'conditional','blocks':[
      {'expression':'not SOWriter','actions':[go(device,'readonly')]},
      {'expression':'SOFinal','actions':[go(device,'invoiced')]},
      {'expression':'SOQueued and SOOwner','actions':[go(device,'owner-queued')]},
      {'expression':'SOQueued','actions':[go(device,'queued')]},
      {'expression':'SOStatus == "Selesai" and SOOwner','actions':[go(device,'owner-completed')]},
      {'expression':'SOStatus == "Selesai"','actions':[go(device,'completed')]},
      {'expression':'SOStatus == "Dibatalkan"','actions':[go(device,'cancelled')]},
      {'expression':'SOStatus == "Ditunda"','actions':[go(device,'paused')]},
      {'expression':'SOStatus == "Dalam Pengerjaan"','actions':[go(device,'running')]},
      {'expression':'SOAssigned','actions':[go(device,'assigned')]},{'actions':[go(device,'ready')]}]}
def guard(device,actions,extra='true'):
    return {'type':'conditional','blocks':[
      {'expression':'SOFinal','actions':[go(device,'invoiced')]},
      {'expression':'SOQueued','actions':[go(device,'blocked')]},
      {'expression':'SOOffline','actions':[go(device,'offline')]},
      {'expression':'SOConflict','actions':[go(device,'conflict')]},
      {'expression':'SOWriter and ('+extra+')','actions':actions},{'actions':[go(device,'blocked')]}]}
def seed(**changes):
    values={**defaults,'SOHasContext':True,**changes}
    return [setv(k,v) for k,v in values.items()]
def base_seed(**changes):return seed(SOAssigned=False,SOTechs='Belum ditugaskan',SOActualSaved=False,SOActualTotalText='Belum disimpan',**changes)
def action_wrap(actions):return {'type':'conditional','blocks':[{'actions':actions}]}
def btn(frame,source,x,y,w,label,target=None,actions=None,kind='Secondary',disabled=False):
    device=source.split('-',1)[0];c('page.select',{'id':2079 if device=='mobile' else 1})
    px,py=positions[frame];n=c('instance.place',{'component':f['buttons'][kind],'x':px+x+w/2,'y':py+y+22})['id']
    c('node.reparent',{'ids':[n],'parent':frame});api.set(n,x=x,y=y,width=w,height=44,name=label)
    c('instance.setProperties',{'ids':[n],'properties':{'Label':label,**({'State':'Disabled'} if disabled else {})}})
    if target or actions:
        act=action_wrap(actions) if isinstance(actions,list) else actions if actions else go(device,target)
        c('proto.interaction.add',{'id':n,'action':act,'transition':{'type':'instant'}})
        edges.append({'source':source,'node':n,'label':label,'target':K(device,target) if target else None,'action':act})
    instances.append(n);return n
def notice(frame,x,y,w,copy,fill='Selected',ink='Service',h=88):box(frame,x,y,w,h,fill,fill,8);txt(frame,x+16,y+14,w-32,copy,13,ink)
def identity(frame,x,y,w):
    txt(frame,x,y,w,'DD 1248 KL · Maya Lestari',18,weight='Semi Bold')
    txt(frame,x,y+34,w,'SO-DEMO-0147 · REG-DEMO-0147',12,'Muted')
def totals(frame,x,y,w,draft=False):
    prefix='SODraft' if draft else 'SOActual'
    txt(frame,x,y,w,'Jasa',13,'Muted');txt(frame,x,y,w,'Rp50.000',13,var=prefix+'PriceText',right=True)
    txt(frame,x,y+34,w,'Part',13,'Muted');txt(frame,x,y+34,w,'Rp100.000',13,var=prefix+'PartText',right=True)
    txt(frame,x,y+78,w,'Total realisasi',14,weight='Medium');txt(frame,x,y+112,w,'Rp150.000',23,weight='Bold',var=prefix+'TotalText',right=True)
def draft_reset():return [copyv('SODraftPrice','SOActualPrice'),copyv('SODraftPriceText','SOActualPriceText'),copyv('SODraftHasPart','SOActualHasPart'),copyv('SODraftPartText','SOActualPartText'),copyv('SODraftPartQty','SOActualPartQty'),copyv('SODraftTotal','SOActualTotal'),copyv('SODraftTotalText','SOActualTotalText'),setv('SODraftQtyValid',True),setv('SODraftReasonValid',False),setv('SODraftReason','Belum diisi'),setv('SOExtraConsent',False)]
def recalc():
    blocks=[]
    for price,has,total in [(60000,True,160000),(60000,False,60000),(50000,True,150000),(50000,False,50000)]:
        blocks.append({'expression':f'SODraftPrice == {price} and '+('SODraftHasPart' if has else 'not SODraftHasPart'),'actions':[setv('SODraftTotal',total),setv('SODraftTotalText','Rp'+format(total,',').replace(',','.'))]})
    return {'type':'conditional','blocks':blocks}
def save_actual(device):
    actions=[copyv('SOActualPrice','SODraftPrice'),copyv('SOActualPriceText','SODraftPriceText'),copyv('SOActualHasPart','SODraftHasPart'),copyv('SOActualPartText','SODraftPartText'),copyv('SOActualPartQty','SODraftPartQty'),copyv('SOActualTotal','SODraftTotal'),copyv('SOActualTotalText','SODraftTotalText'),setv('SOActualSaved',True),go(device,'real-view')]
    editable='SOOwner or (SOStatus != "Selesai" and SOStatus != "Dibatalkan")'
    return guard(device,[{'type':'conditional','blocks':[
      {'expression':'SOSaveFailure','actions':[go(device,'save-error')]},
      {'expression':'SODraftHasPart and not SODraftQtyValid','actions':[go(device,'real-invalid')]},
      {'expression':'not SODraftReasonValid','actions':[go(device,'real-missing')]},
      {'expression':'(SODraftPrice > SOActualPrice or (SODraftHasPart and not SOActualHasPart)) and not SOExtraConsent','actions':[go(device,'real-consent')]},
      {'actions':actions}]}],editable)
def snapshot():
    (ROOT/'evidence/service-order-map.json').write_text(json.dumps({'frames':frames,'edges':edges,'themeControls':themes,'instances':instances,'variables':variables,'defaults':defaults,'collection':collection,'boundText':bound,'fixture':diag['fixture']},indent=2))

try:
    old=api.ask('document.inspect',{'allPages':True,'depth':1,'fields':['name','type','x','y']})
    if '--resume-empty' in sys.argv:
        saved=json.loads((ROOT/'evidence/service-order-map.json').read_text())
        frames=saved['frames'];variables=saved['variables'];collection=saved['collection']
        roots={n['id']:n for p in old['pages'] for n in p.get('children',[])}
        for n in frames.values():
            assert not api.ask('node.get',{'id':n,'depth':1}).get('children',[]),'Resume requires empty seeded frames'
            positions[n]=(roots[n]['x'],roots[n]['y'])
    else:
        assert not api.ask('ui.inspect')['status']['dirty'],'Save manual edits first'
        assert not any(n['name'].startswith(('desktop-so-','mobile-so-')) for p in old['pages'] for n in p.get('children',[])),'SO migration already started'
        with zipfile.ZipFile(ROOT/'archive/before-service-order.zip','w',zipfile.ZIP_DEFLATED) as z:z.write(ROOT/'pos-kasir.figcraft','pos-kasir.figcraft')
        c('proto.closePreview');collection=c('variable.createCollection',{'name':'Service Order demo','modes':['Default']})['id']
        for name,value in defaults.items():variables[name]=c('variable.create',{'collection':collection,'name':name,'type':'boolean' if isinstance(value,bool) else 'number' if isinstance(value,(int,float)) else 'string','values':{'Default':value}})['id']
        for device in ('desktop','mobile'):
            mobile=device=='mobile';w,h=(390,844) if mobile else (1440,1000);c('page.select',{'id':2079 if mobile else 1})
            for i,state in enumerate(states):
                xx=(i%4)*(w+64);yy=(38+i//4)*(h+100)
                n=api.node('frame',x=xx,y=yy,width=w,height=h,name=K(device,state),props={'fill':color('Canvas'),'clip':True,'overflow':'vertical'})
                frames[K(device,state)]=n;positions[n]=(xx,yy)
    snapshot()
    for source,frame in frames.items():
        device,state=source.split('-so-');mobile=device=='mobile';w=390 if mobile else 1440
        x=16 if mobile else 232;pw=358 if mobile else 1184;body=258 if mobile else 196;inner=x+20;iw=pw-40
        title='Service Order'
        titles={'hub':'Journey Service Order','list':'Daftar Service Order','assign-none':'Pilih Teknisi','assign-one':'Pilih Teknisi','assign-b':'Pilih Teknisi','assign-two':'Pilih Teknisi','real-edit':'Realisasi pekerjaan','real-empty':'Realisasi pekerjaan','real-view':'Realisasi tersimpan','real-consent':'Persetujuan biaya tambahan','real-consent-ready':'Persetujuan biaya tambahan','estimate':'Estimasi acuan','history':'Riwayat pengerjaan','owner-history':'Riwayat harga lokal','discard':'Tinggalkan perubahan?'}
        title=titles.get(state,title)
        box(frame,0,0,w,64,r=0);txt(frame,16 if mobile else 232,8 if mobile else 18,170,'Bengkel AC',16,weight='Semi Bold')
        txt(frame,16 if mobile else 420,36 if mobile else 22,170,'Teknisi',12,'Muted',var='SOActor')
        if not mobile:
            box(frame,0,0,208,1000,r=0);txt(frame,24,22,160,'Bengkel AC',18,weight='Semi Bold')
            btn(frame,source,16,80,176,'Service Order','list')
            btn(frame,source,16,136,176,'Estimasi acuan','estimate')
            txt(frame,24,930,160,'Data contoh',12,'Muted')
        else:
            btn(frame,source,16,76,174,'Daftar SO','list');btn(frame,source,198,76,176,'Estimasi acuan','estimate')
        btn(frame,source,202 if mobile else 1192,8,100 if mobile else 108,'Demo','hub')
        theme=btn(frame,source,310 if mobile else 1312,8,64 if mobile else 112,'Tema');themes[source]=theme
        c('proto.interaction.add',{'id':theme,'action':{'type':'conditional','blocks':[{'expression':'mode(POS) == "Dark"','actions':[{'type':'setVariableMode','collection':f['collection'],'mode':'Light'}]},{'actions':[{'type':'setVariableMode','collection':f['collection'],'mode':'Dark'}]}]},'transition':{'type':'instant'}})
        txt(frame,x,148 if mobile else 88,pw,title,24 if mobile else 28,weight='Semi Bold')
        txt(frame,x,190 if mobile else 136,pw,'Pengerjaan dan biaya aktual kunjungan ini.',13,'Muted')
        c('proto.interaction.add',{'id':frame,'trigger':{'type':'keyPress','key':'Escape'},'action':{'type':'back'} if state=='discard' else go(device,'discard' if state=='real-edit' else 'list'),'transition':{'type':'instant'}})
        if state=='hub':
            box(frame,x,body,pw,1450);txt(frame,inner,body+20,iw,'Skenario data contoh · pilihan ini memulai ulang journey SO.',13,'Muted')
            scenarios=[('Mulai SO baru',base_seed(),'ready'),
              ('Sedang dikerjakan',seed(SOStatus='Dalam Pengerjaan',SOActualSaved=False,SOActualTotalText='Belum disimpan'),'running'),
              ('Realisasi Rp150.000',seed(SOStatus='Dalam Pengerjaan'),'running'),
              ('Realisasi Rp160.000',seed(SOStatus='Dalam Pengerjaan',SOActualPrice=60000,SOActualPriceText='Rp60.000',SOActualTotal=160000,SOActualTotalText='Rp160.000'),'running'),
              ('Selesai sebagai Teknisi',seed(SOStatus='Selesai'),'completed'),
              ('Selesai tanpa realisasi',seed(SOStatus='Selesai',SOActualSaved=False,SOActualTotalText='Belum disimpan'),'completed'),
              ('Selesai sebagai Owner',seed(SOActor='Owner',SOOwner=True,SOStatus='Selesai'),'owner-completed'),
              ('Batal dengan biaya · Owner',seed(SOActor='Owner',SOOwner=True,SOStatus='Dibatalkan'),'cancelled'),
              ('Batal tanpa biaya · Owner',seed(SOActor='Owner',SOOwner=True,SOStatus='Dibatalkan',SOActualPrice=0,SOActualPriceText='Rp0',SOActualHasPart=False,SOActualPartText='Rp0',SOActualTotal=0,SOActualTotalText='Rp0'),'cancelled'),
              ('Antrean kasir · Teknisi',seed(SOStatus='Selesai',SOQueued=True),'queued'),
              ('Antrean kasir · Owner',seed(SOActor='Owner',SOOwner=True,SOStatus='Selesai',SOQueued=True),'owner-queued'),
              ('Baca sebagai Kasir',seed(SOActor='Kasir',SOWriter=False,SOStatus='Selesai'),'readonly'),
              ('Invoice final terkunci',seed(SOActor='Owner',SOOwner=True,SOStatus='Selesai',SOFinal=True),'invoiced'),
              ('Draf offline',seed(SOStatus='Dalam Pengerjaan',SOOffline=True),'offline'),
              ('Konflik versi',seed(SOStatus='Dalam Pengerjaan',SOConflict=True,SODraftPrice=60000,SODraftPriceText='Rp60.000',SODraftTotal=160000,SODraftTotalText='Rp160.000'),'conflict'),
              ('Gagal simpan realisasi',seed(SOStatus='Dalam Pengerjaan',SOSaveFailure=True),'real-edit'),
              ('Daftar kosong',seed(),'empty'),('Pencarian tanpa hasil',seed(),'no-results')]
            for i,(label,actions,target) in enumerate(scenarios):btn(frame,source,inner,body+86+i*68,iw,label,actions=actions+[go(device,target)])
            btn(frame,source,inner,body+1340,iw,'Demo: kembali ke Diagnosa',actions=[{'type':'navigate','dest':diag['frames'][device+'-diag-so-created']}])
        elif state=='list':
            box(frame,x,body,pw,48,'Surface','Input',8);txt(frame,x+16,body+13,pw-32,'Cari plat, pelanggan atau nomor SO',14,'Muted')
            btn(frame,source,x,body+68,pw,'Contoh pencarian tanpa hasil','no-results')
            box(frame,x,body+142,pw,344);identity(frame,inner,body+164,iw)
            txt(frame,inner,body+254,iw,'Belum dimulai',14,'Service','Semi Bold',var='SOStatus')
            txt(frame,inner,body+292,iw,'Teknisi A · Teknisi B',13,'Muted',var='SOTechs')
            txt(frame,inner,body+330,iw,'Realisasi terakhir',12,'Muted');txt(frame,inner,body+356,iw,'Rp150.000',20,weight='Semi Bold',var='SOActualTotalText')
            btn(frame,source,inner,body+420,iw,'Buka SO',actions=router(device),kind='Primary')
        elif state in ('assign-none','assign-one','assign-b','assign-two'):
            box(frame,x,body,pw,650);identity(frame,inner,body+24,iw)
            notice(frame,inner,body+132,iw,'Semua Teknisi setara. Pilih minimal satu sebelum memulai pengerjaan.',h=110 if mobile else 76)
            a_target={'assign-none':'assign-one','assign-one':'assign-none','assign-b':'assign-two','assign-two':'assign-b'}[state]
            b_target={'assign-none':'assign-b','assign-one':'assign-two','assign-b':'assign-none','assign-two':'assign-one'}[state]
            btn(frame,source,inner,body+280,iw,'✓ Teknisi A' if state in ('assign-one','assign-two') else 'Teknisi A',a_target)
            btn(frame,source,inner,body+348,iw,'✓ Teknisi B' if state in ('assign-b','assign-two') else 'Teknisi B',b_target)
            actions=guard(device,[setv('SOAssigned',True),setv('SOTechs','Teknisi A · Teknisi B' if state=='assign-two' else 'Teknisi B' if state=='assign-b' else 'Teknisi A'),router(device)],'SOStatus != "Selesai" and SOStatus != "Dibatalkan"')
            btn(frame,source,inner,body+460,iw,'Simpan penugasan',actions=actions if state!='assign-none' else None,kind='Primary',disabled=state=='assign-none')
            btn(frame,source,inner,body+530,iw,'Kembali ke SO',actions=router(device))
        elif state in ('ready','assigned','running','paused','completed','cancelled','queued','owner-completed','owner-queued','owner-withdrawn','readonly','invoiced'):
            panel=pw if mobile else 752;ax=x+20;aw=panel-40
            box(frame,x,body,panel,1060 if mobile else 840);identity(frame,ax,body+24,aw)
            label={'ready':'Belum dimulai','assigned':'Belum dimulai','running':'Dalam Pengerjaan','paused':'Ditunda','completed':'Selesai','owner-completed':'Selesai','owner-withdrawn':'Selesai · ditarik dari antrean','cancelled':'Dibatalkan','queued':'Dalam antrean kasir','owner-queued':'Dalam antrean kasir','readonly':'Tampilan baca Kasir','invoiced':'Invoice final · terkunci'}[state]
            txt(frame,ax,body+124,aw,label,18,'Success' if 'completed' in state else 'Warning' if state in ('paused','cancelled','invoiced') else 'Service','Semi Bold')
            txt(frame,ax,body+178,aw,'Teknisi',12,'Muted');txt(frame,ax,body+206,aw,'Belum ditugaskan' if state=='ready' else 'Teknisi A · Teknisi B',14,var=None if state=='ready' else 'SOTechs')
            txt(frame,ax,body+270,aw,'Estimasi acuan · Rp150.000',14,'Muted')
            txt(frame,ax,body+318,aw,'Realisasi terakhir',14,weight='Medium')
            txt(frame,ax,body+356,aw,'Belum disimpan' if state=='ready' else 'Rp150.000',24,weight='Bold',var=None if state=='ready' else 'SOActualTotalText')
            yy=body+438
            if state in ('ready','assigned'):
                btn(frame,source,ax,yy,aw,'Pilih Teknisi',actions=guard(device,[go(device,'assign-none')]))
                btn(frame,source,ax,yy+68,aw,'Mulai pengerjaan',actions=guard(device,[branch('SOAssigned',[go(device,'start')],[go(device,'blocked')])],'SOStatus == "Belum dimulai"'),kind='Primary',disabled=state=='ready')
            elif state=='running':
                btn(frame,source,ax,yy,aw,'Realisasi jasa / part',actions=guard(device,[branch('SOActualSaved',draft_reset()+[go(device,'real-edit')],[go(device,'real-empty')])]),kind='Primary')
                btn(frame,source,ax,yy+68,aw,'Tunda pengerjaan',actions=guard(device,[go(device,'pause')],'SOStatus == "Dalam Pengerjaan"'))
                btn(frame,source,ax,yy+136,aw,'Tandai selesai',actions=guard(device,[go(device,'complete')],'SOStatus == "Dalam Pengerjaan"'))
                btn(frame,source,ax,yy+204,aw,'Batalkan pekerjaan',actions=guard(device,[go(device,'cancel')]))
                btn(frame,source,ax,yy+272,aw,'Ubah penugasan',actions=guard(device,[go(device,'assign-none')],'SOStatus == "Dalam Pengerjaan"'))
            elif state=='paused':
                btn(frame,source,ax,yy,aw,'Lanjutkan pengerjaan',actions=guard(device,[setv('SOStatus','Dalam Pengerjaan'),go(device,'running')],'SOStatus == "Ditunda"'),kind='Primary')
                btn(frame,source,ax,yy+68,aw,'Realisasi jasa / part',actions=guard(device,[branch('SOActualSaved',draft_reset()+[go(device,'real-edit')],[go(device,'real-empty')])]))
            elif state in ('completed','cancelled','owner-completed','owner-withdrawn'):
                owner_edit=state in ('owner-completed','owner-withdrawn') or state=='cancelled'
                btn(frame,source,ax,yy,aw,'Periksa realisasi',actions=branch('SOActualSaved',[go(device,'real-view')],[go(device,'blocked')]))
                btn(frame,source,ax,yy+68,aw,'Serahkan ke kasir',actions=guard(device,[go(device,'handoff')]))
                if owner_edit:
                    btn(frame,source,ax,yy+136,aw,'Koreksi realisasi (Owner)',actions=guard(device,draft_reset()+[go(device,'real-edit')],'SOOwner'))
                    if state!='cancelled':btn(frame,source,ax,yy+204,aw,'Buka kembali pekerjaan',actions=guard(device,[go(device,'reopen')],'SOOwner and SOStatus == "Selesai"'))
                else:btn(frame,source,ax,yy+136,aw,'Koreksi realisasi',disabled=True)
                if state=='completed':btn(frame,source,ax,yy+208,aw,'Demo: tinjau sebagai Owner',actions=[setv('SOOwner',True),setv('SOActor','Owner'),setv('SOWriter',True),go(device,'owner-completed')])
                txt(frame,ax,yy+282,aw,'Setelah pekerjaan ditutup, Teknisi tidak mengubah realisasi. Owner memeriksa sesuai hak akses.',13,'Muted')
            elif state in ('queued','owner-queued'):
                notice(frame,ax,yy,aw,'Biaya dan progres terkunci selama mengantre. Penyerahan belum menerbitkan invoice atau menerima pembayaran.',h=132 if mobile else 100)
                btn(frame,source,ax,yy+164,aw,'Ubah realisasi',disabled=True)
                if state=='owner-queued':btn(frame,source,ax,yy+232,aw,'Tarik dari antrean',actions=branch('SOOwner and SOQueued and not SOFinal',[go(device,'withdraw')],[go(device,'blocked')]))
                else:btn(frame,source,ax,yy+232,aw,'Demo: lanjut sebagai Owner',actions=[setv('SOOwner',True),setv('SOActor','Owner'),setv('SOWriter',True),go(device,'owner-queued')])
            else:notice(frame,ax,yy,aw,'Invoice final mengunci SO. Koreksi mengikuti alur invoice atau retur.' if state=='invoiced' else 'Kasir membaca; penugasan, progres dan realisasi dikelola Teknisi/Owner.',h=150 if mobile else 100)
            btn(frame,source,ax,body+962 if mobile else body+760,aw,'Riwayat',actions=branch('SOOwner',[go(device,'owner-history')],[go(device,'history')]))
            if not mobile:
                box(frame,1008,body,408,360);txt(frame,1032,body+24,360,'Stok part · contoh',18,weight='Semi Bold')
                txt(frame,1032,body+80,360,'Filter kabin\nTercatat 16 · Reservasi 3\nRusak diblokir 1 · Tersedia 12',14)
                txt(frame,1032,body+218,360,'Data contoh untuk membaca stok; tidak menjalankan reservasi nyata.',13,'Muted')
        elif state=='real-empty':
            box(frame,x,body,pw,650);identity(frame,inner,body+24,iw)
            notice(frame,inner,body+140,iw,'Realisasi belum disimpan. Estimasi yang disetujui belum dianggap sebagai biaya akhir.',h=116 if mobile else 80)
            btn(frame,source,inner,body+324,iw,'Salin estimasi untuk diperiksa',actions=guard(device,[setv('SODraftPrice',50000),setv('SODraftPriceText','Rp50.000'),setv('SODraftHasPart',True),setv('SODraftPartText','Rp100.000'),setv('SODraftTotal',150000),setv('SODraftTotalText','Rp150.000'),setv('SODraftReasonValid',False),setv('SODraftReason','Belum diisi'),setv('SODraftQtyValid',True),setv('SOExtraConsent',False),go(device,'real-edit')]),kind='Primary')
            btn(frame,source,inner,body+402,iw,'Kembali ke SO',actions=router(device))
        elif state in ('real-edit','real-view','estimate'):
            draft=state=='real-edit';estimate=state=='estimate';panel=pw if mobile else 752;ix=x+20;ww=panel-40
            box(frame,x,body,panel,1310 if mobile else 1160);identity(frame,ix,body+24,ww)
            txt(frame,ix,body+128,ww,'Acuan disetujui · tidak diubah' if estimate else 'Perubahan belum disimpan' if draft else 'Rincian realisasi terakhir',14,'Service','Semi Bold')
            for i,(name,kind,unit) in enumerate([('Pemeriksaan AC','Jasa','pekerjaan'),('Filter kabin','Part','pcs')]):
                yy=body+190+i*230;box(frame,ix,yy,ww,208)
                txt(frame,ix+16,yy+14,ww-32,kind,12,'Service' if i==0 else 'Part','Medium');txt(frame,ix+16,yy+46,ww-32,name,16,weight='Semi Bold')
                txt(frame,ix+16,yy+88,ww-32,'1 '+unit,13,'Muted',var=None if estimate or i==0 else 'SODraftPartQty' if draft else 'SOActualPartQty')
                txt(frame,ix+16,yy+122,ww-32,'Rp50.000' if i==0 else 'Rp100.000',18,weight='Semi Bold',var=None if estimate else ('SODraftPriceText' if i==0 else 'SODraftPartText') if draft else ('SOActualPriceText' if i==0 else 'SOActualPartText'))
                if draft and i==0:
                    btn(frame,source,ix+16,yy+158,ww-32,'Contoh harga Rp60.000',actions=guard(device,[setv('SODraftPrice',60000),setv('SODraftPriceText','Rp60.000'),setv('SOExtraConsent',False),recalc(),go(device,'real-edit')]))
                if draft and i==1:
                    btn(frame,source,ix+16,yy+158,(ww-40)/2,'Qty 0,5 pcs',actions=branch('SODraftHasPart',[setv('SODraftQtyValid',False),setv('SODraftPartQty','0,5 pcs'),setv('SOExtraConsent',False),go(device,'real-invalid')],[go(device,'real-edit')]))
                    btn(frame,source,ix+24+(ww-40)/2,yy+158,(ww-40)/2,'Lepas part',actions=guard(device,[setv('SODraftHasPart',False),setv('SODraftPartText','Rp0'),setv('SODraftPartQty','Tidak dipakai'),setv('SOExtraConsent',False),recalc(),go(device,'real-edit')]))
            if estimate:
                txt(frame,ix,body+680,ww,'Total estimasi Rp150.000',24,weight='Bold');txt(frame,ix,body+738,ww,'EST-DEMO-0147 revisi 2. Pemeriksaan dan rekomendasi tetap menjadi acuan.',14,'Muted')
                btn(frame,source,ix,body+850,ww,'Kembali ke SO',actions=router(device))
            else:
                totals(frame,ix,body+682,ww,draft)
                if draft:
                    txt(frame,ix,body+878,ww,'Alasan perubahan realisasi',13,weight='Medium');txt(frame,ix,body+914,ww,'Belum diisi',13,'Muted',var='SODraftReason')
                    btn(frame,source,ix,body+994,ww,'Isi alasan contoh',actions=[setv('SODraftReasonValid',True),setv('SODraftReason','Realisasi sesuai pemeriksaan; harga lokal dicatat.'),go(device,'real-edit')])
                    btn(frame,source,ix,body+1060,ww,'Periksa dan simpan',actions=save_actual(device),kind='Primary')
                    btn(frame,source,ix,body+1126,ww,'Batal','discard')
                else:
                    btn(frame,source,ix,body+896,ww,'Revisi realisasi',actions=guard(device,draft_reset()+[go(device,'real-edit')],'SOOwner or (SOStatus != "Selesai" and SOStatus != "Dibatalkan")'))
                    btn(frame,source,ix,body+964,ww,'Kembali ke SO',actions=router(device),kind='Primary')
        elif state in ('real-consent','real-consent-ready'):
            box(frame,x,body,pw,850);identity(frame,inner,body+24,iw)
            txt(frame,inner,body+132,iw,'Estimasi acuan tetap Rp150.000',14,'Muted');totals(frame,inner,body+200,iw,True)
            notice(frame,inner,body+400,iw,'Ada kenaikan biaya terhadap realisasi/acuan sebelumnya. Catat hanya setelah pelanggan menyetujui rincian tambahan.',h=132 if mobile else 88)
            ready=state.endswith('ready')
            btn(frame,source,inner,body+562,iw,'✓ Setuju' if ready else 'Setuju',actions=[setv('SOExtraConsent',not ready),go(device,'real-consent' if ready else 'real-consent-ready')])
            btn(frame,source,inner,body+638,iw,'Simpan realisasi',actions=save_actual(device) if ready else None,kind='Primary',disabled=not ready)
            btn(frame,source,inner,body+706,iw,'Periksa isian','real-edit')
        elif state in ('start','pause','pause-filled','complete','cancel','cancel-filled','handoff','reopen','reopen-filled','withdraw','withdraw-filled'):
            box(frame,x,body,pw,760);identity(frame,inner,body+24,iw)
            copy={'start':'Mulai pengerjaan dengan Teknisi yang sudah dipilih. Penugasan tidak membuat biaya atau pembayaran.',
              'pause':'Isi alasan penundaan sebelum menyimpan status Ditunda.','pause-filled':'Alasan: menunggu ketersediaan waktu pelanggan.',
              'complete':'Tandai pekerjaan Selesai. Realisasi tersimpan diperlukan saat diserahkan ke kasir; Teknisi tidak merevisi setelah Selesai.',
              'cancel':'Isi alasan pembatalan. Biaya aktual yang sudah timbul tetap harus diperiksa.','cancel-filled':'Alasan: pelanggan membatalkan sisa pekerjaan.',
              'handoff':'Periksa realisasi tersimpan sebelum menyerahkan. Biaya/progres dikunci; belum ada invoice atau pembayaran.',
              'reopen':'Owner mengisi alasan sebelum membuka kembali SO Selesai. Invoice final atau antrean yang belum ditarik tetap terkunci.',
              'reopen-filled':'Alasan: pemeriksaan ulang setelah keluhan pelanggan.',
              'withdraw':'Owner mengisi alasan penarikan. Penarikan tidak otomatis membuka progres atau menyerahkan kembali SO.',
              'withdraw-filled':'Alasan: periksa ulang rincian realisasi sebelum penagihan.'}[state]
            notice(frame,inner,body+142,iw,copy,fill='WarningSurface',ink='Warning',h=180 if mobile else 100)
            yy=body+374
            if state in ('pause','cancel','reopen','withdraw'):
                btn(frame,source,inner,yy,iw,'Isi alasan contoh',state+'-filled')
                btn(frame,source,inner,yy+68,iw,'Konfirmasi',disabled=True,kind='Primary')
            else:
                if state=='start':act=guard(device,[setv('SOStatus','Dalam Pengerjaan'),go(device,'running')],'SOAssigned and SOStatus == "Belum dimulai"')
                elif state=='pause-filled':act=guard(device,[setv('SOStatus','Ditunda'),go(device,'paused')],'SOStatus == "Dalam Pengerjaan"')
                elif state=='cancel-filled':act=guard(device,[setv('SOStatus','Dibatalkan'),go(device,'cancelled')],'SOStatus != "Selesai" and SOStatus != "Dibatalkan"')
                elif state=='complete':act=guard(device,[setv('SOStatus','Selesai'),router(device)],'SOStatus == "Dalam Pengerjaan"')
                elif state=='reopen-filled':act=guard(device,[setv('SOStatus','Dalam Pengerjaan'),go(device,'running')],'SOOwner and SOStatus == "Selesai"')
                elif state=='withdraw-filled':act=branch('SOOwner and SOQueued and not SOFinal and not SOOffline',[setv('SOQueued',False),go(device,'owner-withdrawn')],[go(device,'blocked')])
                else:act=guard(device,[branch('SOActualSaved and ((SOStatus == "Selesai") or (SOStatus == "Dibatalkan" and SOOwner and SOActualTotal > 0))',[setv('SOQueued',True),router(device)],[go(device,'blocked')])])
                btn(frame,source,inner,yy,iw,'Serahkan ke kasir' if state=='handoff' else 'Konfirmasi',actions=act,kind='Primary')
            btn(frame,source,inner,yy+148,iw,'Kembali ke SO',actions=router(device))
        elif state in ('history','owner-history'):
            box(frame,x,body,pw,760);identity(frame,inner,body+24,iw)
            txt(frame,inner,body+144,iw,'Jejak pengerjaan contoh',18,weight='Semi Bold')
            txt(frame,inner,body+202,iw,'09.55 · SO dibuat, Belum dimulai\nTeknisi saat ini:',14)
            txt(frame,inner,body+270,iw,'Teknisi A · Teknisi B',14,var='SOTechs')
            txt(frame,inner,body+308,iw,'Dalam Pengerjaan',13,'Muted',var='SOStatus')
            if state=='owner-history':
                notice(frame,inner,body+376,iw,'Owner · Contoh log harga lokal',h=80)
                txt(frame,inner,body+488,iw,'Pemeriksaan AC: Rp50.000 menjadi Rp60.000\nPelaku: Teknisi (contoh) · 10.15\nAlasan: realisasi hasil pemeriksaan\nPersetujuan tambahan: dicatat untuk revisi terkait.',14)
            btn(frame,source,inner,body+660,iw,'Kembali ke SO',actions=router(device))
        elif state=='discard':
            box(frame,x,body,pw,500);txt(frame,inner,body+32,iw,'Perubahan realisasi belum disimpan. Isian masih tersedia bila Anda melanjutkan.',16)
            btn(frame,source,inner,body+246,iw,'Lanjutkan mengisi','real-edit',kind='Primary')
            btn(frame,source,inner,body+316,iw,'Tinggalkan perubahan',actions=router(device))
        else:
            box(frame,x,body,pw,760)
            if state not in ('empty','no-results'):identity(frame,inner,body+24,iw)
            copies={'blocked':'Tindakan belum tersedia untuk kondisi SO ini. Periksa penugasan, status, realisasi tersimpan, peran dan penguncian antrean. Pembatalan tanpa biaya tidak ditagihkan.',
              'offline':'Koneksi terputus. Perubahan lokal contoh dipertahankan; belum ada konfirmasi simpan, status atau penyerahan baru.',
              'conflict':'Versi lokal tertinggal. Isian lokal dipertahankan dan tidak menimpa versi server. Periksa versi terbaru serta status penguncian.',
              'save-error':'Realisasi belum berhasil disimpan. Periksa isian sebelum mencoba lagi; jangan menganggap biaya akhir sudah berubah.',
              'real-invalid':'Jumlah 0,5 pcs tidak valid. Pcs harus bulat positif; harga dan alasan lain tetap dipertahankan.',
              'real-missing':'Isi alasan perubahan realisasi sebelum menyimpan. Rincian dan nominal contoh tetap dipertahankan.',
              'empty':'Belum ada Service Order pada daftar ini. SO dibuat dari estimasi yang telah disetujui.',
              'no-results':'Tidak ada hasil untuk pencarian DD 0000 XX. Coba plat atau nomor SO lain.'}
            notice(frame,inner,body+150,iw,copies[state],fill='ErrorSurface' if state in ('save-error','real-invalid','real-missing') else 'WarningSurface',ink='Error' if state in ('save-error','real-invalid','real-missing') else 'Warning',h=200 if mobile else 100)
            if state=='real-invalid':btn(frame,source,inner,body+428,iw,'Gunakan qty 1 pcs',actions=[setv('SODraftQtyValid',True),setv('SODraftPartQty','1 pcs'),setv('SOExtraConsent',False),go(device,'real-edit')],kind='Primary')
            elif state=='real-missing':btn(frame,source,inner,body+428,iw,'Kembali mengisi','real-edit',kind='Primary')
            elif state=='offline':btn(frame,source,inner,body+428,iw,'Coba koneksi lagi',actions=[setv('SOOffline',False),go(device,'real-edit')],kind='Primary')
            elif state=='save-error':btn(frame,source,inner,body+428,iw,'Periksa isian',actions=[setv('SOSaveFailure',False),go(device,'real-edit')],kind='Primary')
            elif state=='conflict':
                btn(frame,source,inner,body+428,iw,'Lihat isian lokal','real-edit')
                btn(frame,source,inner,body+498,iw,'Gunakan versi server',actions=seed(SOStatus='Selesai')+[router(device)],kind='Primary')
            else:btn(frame,source,inner,body+428,iw,'Kembali ke daftar','list')
        snapshot();print(json.dumps({'built':source}),flush=True)
    # The original two-item handoff is the entry fixture; alternative estimate
    # amounts remain independent demonstration journeys.
    old=api.ask('document.inspect',{'allPages':True,'depth':1,'fields':['name','type','x','y']})
    roots={n['id']:n for p in old['pages'] for n in p.get('children',[])}
    for device in ('desktop','mobile'):
        for source,target_map,xx,yy,ww in [(device+'-diag-so-created',diag,36 if device=='mobile' else 1032,1520 if device=='mobile' else 320,318 if device=='mobile' else 360),(device+'-diag-hub',diag,36 if device=='mobile' else 252,1560 if device=='mobile' else 1500,318 if device=='mobile' else 1144),(device+'-catalog',cash,36 if device=='mobile' else 252,1076,318 if device=='mobile' else 1144)]:
            parent=target_map['frames'][source];positions[parent]=(roots[parent]['x'],roots[parent]['y'])
            action=branch('SOHasContext',[go(device,'list')],base_seed()+[go(device,'list')]) if source.endswith('so-created') else action_wrap([go(device,'hub')])
            btn(parent,source,xx,yy,ww,'Kelola Service Order' if source.endswith('so-created') else 'Demo: Service Order',actions=action)
        c('page.select',{'id':2079 if device=='mobile' else 1});c('proto.flow.add',{'start':frames[K(device,'hub')],'name':'Service Order / '+('Ponsel' if device=='mobile' else 'Desktop')+' / Demo'})
    snapshot();c('page.select',{'id':1});c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')});c('proto.preview',{'start':frames['desktop-so-hub']})
    print(json.dumps({'newFrames':len(frames),'controls':len(edges),'variables':len(variables)}))
finally:api.close()
