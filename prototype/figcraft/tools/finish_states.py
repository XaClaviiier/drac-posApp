"""Extend the same native document with cashier states and reusable controls."""
import json
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1];api=Native();c=api.command
foundation=json.loads((ROOT/'evidence/foundations.json').read_text(encoding='utf-8'));v=foundation['variables']
mapping=json.loads((ROOT/'evidence/build-map.json').read_text(encoding='utf-8'));con=json.loads((ROOT/'evidence/consolidation.json').read_text(encoding='utf-8'))
frames=dict(mapping['frames']);edges=list(mapping['edges']);newframes={};instances=[]
doc=api.ask('document.inspect',{'allPages':True,'depth':5})
positions={f['id']:(f.get('x',0),f.get('y',0)) for p in doc['pages'] for f in p.get('children',[])}
def color(role):return {'$var':v[role]}
def rect(parent,x,y,w,h,role='Surface',radius=12):return api.node('rectangle',parent,x=x,y=y,width=w,height=h,props={'fill':color(role),'cornerRadius':radius,'stroke':color('Border')})
def text(parent,x,y,w,label,size=14,role='Text',weight='Regular',fixed=False):
 return api.node('text',parent,x=x,y=y,width=w,text=label,props={'fontFamily':'Poppins','fontStyle':weight,'fontSize':size,'lineHeight':'150%','fill':'#18181B' if fixed else color(role)})
def link(node,source,dest,label):
 c('proto.interaction.add',{'id':node,'dest':frames[dest],'transition':{'type':'instant'}});edges.append({'source':source,'target':dest,'node':node,'label':label})
def button(frame,device,x,y,w,label,dest=None,kind='Secondary',source=None):
 page=con['pages']['mobile' if device=='mobile' else 'desktop'];c('page.select',{'id':page});fx,fy=positions[frame]
 node=c('instance.place',{'component':foundation['buttons'][kind],'x':fx+x+w/2,'y':fy+y+22})['id']
 c('node.reparent',{'ids':[node],'parent':frame});api.set(node,x=x,y=y,width=w,height=44)
 c('instance.setProperties',{'ids':[node],'properties':{'Label':label}})
 if dest:link(node,source,dest,label)
 instances.append(node);return node
def snapshot():
 (ROOT/'evidence/design-completion-map.json').write_text(json.dumps({'frames':frames,'newFrames':newframes,'edges':edges,'instances':instances},indent=2),encoding='utf-8')
try:
 c('proto.closePreview')
 extras=['catalog','empty','no-results','loading','load-error','offline','needs-owner','zero-draft','zero-paid','payment-error','payment-status','print-cash','print-qris','print-transfer','print-zero']
 titles={'catalog':'Skenario kasir','empty':'Belum ada transaksi menunggu','no-results':'Transaksi tidak ditemukan','loading':'Memuat antrean','load-error':'Antrean belum dapat dimuat','offline':'Koneksi terputus','needs-owner':'Perlu pemeriksaan Owner','zero-draft':'Invoice tanpa biaya','zero-paid':'Invoice Rp0 sudah lunas','payment-error':'Pencatatan perlu diperiksa','payment-status':'Status pembayaran diperiksa'}
 for device in ('desktop','mobile'):
  page=con['pages']['mobile' if device=='mobile' else 'desktop'];c('page.select',{'id':page});w,h=(390,844) if device=='mobile' else (1440,1000)
  for index,state in enumerate(extras):
   key=device+'-'+state;x=(index%4)*(w+64);y=(6+index//4)*(h+100)
   frame=api.node('frame',x=x,y=y,width=w,height=h,name=key,props={'fill':color('Canvas'),'clip':True,'overflow':'vertical'})
   frames[key]=frame;newframes[key]=frame;positions[frame]=(x,y)
 snapshot()
 for key,frame in newframes.items():
  device,state=key.split('-',1);mobile=device=='mobile';w,h=(390,844) if mobile else (1440,1000);x=16 if mobile else 232;pw=w-x-16 if mobile else 1184
  rect(frame,0,0,w,64,'Surface',0);text(frame,16 if mobile else 232,16,160,'Bengkel AC',16,weight='Semi Bold')
  if not mobile:
   rect(frame,0,0,185,h,'Surface',0);text(frame,16,22,160,'Bengkel AC',18,weight='Semi Bold');text(frame,24,88,150,'POS Kasir',14,'Service','Semi Bold');text(frame,24,132,150,'Kasir',14,'Muted')
  title=titles.get(state,'Pratinjau nota');text(frame,x,88,pw,title,24 if mobile else 28,weight='Semi Bold')
  if state.startswith('print-'):
   method=state[6:];paperx=16 if mobile else 440;paperw=358 if mobile else 560
   api.node('rectangle',frame,x=paperx,y=152,width=paperw,height=520,props={'fill':'#FFFFFF','stroke':'#E4E4E7','cornerRadius':8})
   text(frame,paperx+16,166,paperw-32,'SIMULASI - BUKAN BUKTI PEMBAYARAN NYATA',12,fixed=True)
   text(frame,paperx+16,204,paperw-32,'Bengkel AC',20,weight='Semi Bold',fixed=True)
   zero=method=='zero';text(frame,paperx+16,245,paperw-32,'INV-0145 / SO-0267' if zero else 'INV-0144 / SO-0261',14,fixed=True)
   text(frame,paperx+16,275,paperw-32,'Nadia Putri / B 7777 XYZ' if zero else 'Rina Prasetyo / B 1234 ABC',14,fixed=True)
   text(frame,paperx+16,320,paperw-32,'Pemeriksaan AC - 1 pekerjaan - Rp0' if zero else 'Servis AC - 1 pekerjaan - Rp150.000\nFilter kabin - 1 pcs - Rp85.000',14,fixed=True)
   text(frame,paperx+16,398,paperw-32,'Total Rp0 / Lunas' if zero else 'Total Rp235.000 / Lunas',20,weight='Semi Bold',fixed=True)
   detail={'cash':'Tunai diterima Rp250.000\nKembalian Rp15.000','qris':'QRIS - pembayaran Rp235.000','transfer':'Transfer manual - Rp235.000\nReferensi TRF-DEMO-0144','zero':'Lunas tanpa transaksi pembayaran'}[method]
   text(frame,paperx+16,446,paperw-32,detail+'\nSisa tagihan Rp0',14,fixed=True)
   dest=device+('-zero-paid' if zero else '-paid-'+method);button(frame,device,x,700,pw,'Tutup pratinjau',dest,source=key)
   text(frame,x,758,pw,'Tampilan nota saja. Cetak fisik mengikuti perangkat yang ditetapkan.',12,'Muted')
   continue
  rect(frame,x,168,pw,940 if state=='catalog' else 560,'Surface')
  inner=x+20;iw=pw-40
  if state=='catalog':
   text(frame,inner,188,iw,'Kontrol tinjauan prototype - data contoh, bukan menu transaksi produksi.',14,'Muted')
   options=[('Antrean kosong','empty'),('Pencarian tanpa hasil','no-results'),('Memuat antrean','loading'),('Gagal memuat antrean','load-error'),('Pembayaran offline','offline'),('Draf perlu Owner','needs-owner'),('Invoice Rp0','zero-draft'),('Gagal mencatat pembayaran','payment-error')]
   for index,(label,dest) in enumerate(options):button(frame,device,inner,258+index*66,iw,label,device+'-'+dest,source=key)
   button(frame,device,inner,820,iw,'Kembali ke antrean',device+'-list',source=key)
  elif state in ('empty','no-results','load-error','loading'):
   copy={'empty':'SO yang telah diserahkan dan invoice yang perlu diproses akan muncul di sini.','no-results':'Tidak ada transaksi untuk pencarian B 0000 XXX. Coba plat, nama pelanggan atau nomor dokumen lain.','load-error':'Data antrean belum dapat ditampilkan. Periksa koneksi, lalu coba lagi.','loading':'Mohon tunggu, antrean sedang dimuat.'}[state]
   text(frame,inner,200,iw,copy,16)
   if state=='loading':
    for j in range(3):rect(frame,inner,330+j*74,iw,52,'Secondary',8)
    c('proto.interaction.add',{'id':frame,'trigger':{'type':'afterDelay','ms':1200},'dest':frames[device+'-list'],'transition':{'type':'instant'}})
   button(frame,device,inner,620,iw,'Coba lagi' if state=='load-error' else 'Hapus pencarian' if state=='no-results' else 'Kembali ke antrean',device+('-loading' if state=='load-error' else '-list'),source=key)
  elif state=='offline':
   text(frame,inner,200,iw,'INV-0144 / Total Rp235.000',18,weight='Semi Bold');text(frame,inner,260,iw,'Pembayaran dan penerbitan invoice memerlukan koneksi internet. Jangan menganggap pembayaran sudah tersimpan.',16)
   disabled=button(frame,device,inner,450,iw,'Konfirmasi pembayaran',kind='Primary');c('instance.setProperties',{'ids':[disabled],'properties':{'State':'Disabled'}})
   button(frame,device,inner,530,iw,'Coba lagi',device+'-cash',source=key)
   button(frame,device,inner,606,iw,'Kembali ke antrean',device+'-list',source=key)
  elif state=='needs-owner':
   text(frame,inner,200,iw,'INV-0144 / SO-0261',18,weight='Semi Bold');text(frame,inner,260,iw,'Realisasi SO telah berubah. Draf tidak dapat diterbitkan sebelum Owner memeriksa sumber terbaru.',16)
   disabled=button(frame,device,inner,470,iw,'Terbitkan invoice',kind='Primary');c('instance.setProperties',{'ids':[disabled],'properties':{'State':'Disabled'}})
   button(frame,device,inner,570,iw,'Kembali ke antrean',device+'-list',source=key)
  elif state in ('zero-draft','zero-paid'):
   text(frame,inner,200,iw,'Nadia Putri / B 7777 XYZ\nSO-0267 / INV-0145',16,weight='Semi Bold');text(frame,inner,285,iw,'Pemeriksaan AC / 1 pekerjaan\nHarga satuan Rp0 / Subtotal Rp0',16)
   text(frame,inner,390,iw,'Total invoice Rp0',24,weight='Semi Bold')
   text(frame,inner,450,iw,'Invoice final Rp0 langsung Lunas, tanpa penerimaan uang atau transaksi pembayaran Rp0.',14,'Muted')
   button(frame,device,inner,570,iw,'Terbitkan invoice' if state=='zero-draft' else 'Pratinjau nota',device+('-zero-paid' if state=='zero-draft' else '-print-zero'),kind='Primary',source=key)
   button(frame,device,inner,640,iw,'Kembali ke antrean',device+'-list',source=key)
  elif state in ('payment-error','payment-status'):
   text(frame,inner,200,iw,'INV-0144 / Rp235.000',20,weight='Semi Bold')
   text(frame,inner,270,iw,'Pencatatan belum dapat dipastikan. Periksa status sebelum mengulang konfirmasi.' if state=='payment-error' else 'Pada skenario ini pembayaran belum tercatat. Kembali ke pembayaran untuk memeriksa rincian sebelum mencoba lagi.',16)
   button(frame,device,inner,550,iw,'Periksa status' if state=='payment-error' else 'Kembali ke pembayaran',device+('-payment-status' if state=='payment-error' else '-cash'),kind='Primary',source=key)
   button(frame,device,inner,625,iw,'Kembali ke antrean',device+'-list',source=key)
  snapshot()
 # Print buttons in the existing paid screens now open a real visual print preview.
 for device in ('desktop','mobile'):
  for method in ('cash','qris','transfer'):
   frame=frames[device+'-paid-'+method];node=api.ask('node.get',{'id':frame,'depth':1})
   children=node.get('node',node).get('children',[]);label=next(n for n in children if n.get('characters')=='Cetak nota')
   x,y=label['x']-10,label['y']-12;hot=api.node('rectangle',frame,x=x,y=y,width=110,height=44,name='Demo / Pratinjau cetak',props={'fill':'#00000000'})
   link(hot,device+'-paid-'+method,device+'-print-'+method,'Pratinjau cetak')
 # Put prototype-only demo and theme controls into existing/new headers.
 for key,frame in frames.items():
  device=key.split('-')[0];mobile=device=='mobile';page=con['pages']['mobile' if mobile else 'desktop'];c('page.select',{'id':page})
  if frame not in positions:
   positions[frame]=(0,0)
  if key not in newframes:
   node=api.ask('node.get',{'id':frame,'depth':1});children=node.get('node',node).get('children',[])
   for n in children:
    if n.get('type')=='TEXT' and n.get('y',999)<56 and ('Konsep' in n.get('characters','') or (n.get('characters')=='Kasir' and n.get('x',0)>150)):
     api.set(n['id'],visible=False)
  button(frame,device,202 if mobile else 1192,8,100 if mobile else 108,'Demo',device+'-catalog',source=key)
  theme=button(frame,device,310 if mobile else 1312,8,64 if mobile else 112,'Tema',source=key)
  action={'type':'conditional','blocks':[{'expression':"mode(POS) == 'Dark'",'actions':[{'type':'setVariableMode','collection':foundation['collection'],'mode':'Light'}]},{'actions':[{'type':'setVariableMode','collection':foundation['collection'],'mode':'Dark'}]}]}
  c('proto.interaction.add',{'id':theme,'action':action,'transition':{'type':'instant'}})
  if key not in newframes:
   c('proto.interaction.add',{'id':frame,'trigger':{'type':'keyPress','key':'Escape'},'dest':frames[device+'-list'],'transition':{'type':'instant'}})
  snapshot()
 c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')});c('page.select',{'id':con['pages']['desktop']});c('proto.preview',{'start':frames['desktop-list']});snapshot()
 print(json.dumps({'totalFrames':len(frames),'newStates':len(newframes),'newInstances':len(instances),'links':len(edges)}))
finally:api.close()
