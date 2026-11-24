"""Capture approved visual states and their explicit prototype hotspots."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'generated'
EXTRACT=(ROOT/'tools/extract.js').read_text(encoding='utf-8')
states=['list','detail','draft','final','cash','cash-short','qris','qris-checked','transfer','transfer-filled','transfer-checked','paid-cash','paid-qris','paid-transfer']
report=[]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for device,width,height in [('desktop',1440,1000),('mobile',390,844)]:
  for state in states:
   page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
   file=(device+'-poppins.html') if state=='list' else 'cashier-flow.html'
   page.goto((ROOT/'sources'/file).as_uri(),wait_until='networkidle')
   page.evaluate("async()=>{await document.fonts.load('400 16px Poppins');await document.fonts.load('600 20px Poppins');await document.fonts.ready}")
   assert page.evaluate("[...document.fonts].some(f=>f.family.includes('Poppins')&&f.status==='loaded')")
   if state!='list':
    page.add_style_tag(content='.intro,.tools,.footer{display:none!important}body{padding:0}.frame{max-width:none;border:0;border-radius:0}.head{margin-bottom:12px}')
    if state not in ('detail','draft'):
     page.locator('#issue').click()
    if state=='detail':
     page.evaluate('''() => {const el=document.getElementById('screen');el.innerHTML=el.innerHTML.replaceAll('INV-0144','').replaceAll('Invoice draf','Periksa realisasi').replace('Rincian invoice','Rincian realisasi').replace('Total invoice','Total realisasi').replace('>Draf<','>Siap ditagih<').replace('<h2>Terbitkan invoice</h2>','<h2>Lanjutkan ke invoice</h2>').replace('>Terbitkan invoice</button>','>Buat invoice draf</button>').replace('Periksa rincian sebelum menerbitkan invoice. Pembayaran tersedia setelah invoice terbit.','Periksa realisasi sebelum membuat invoice draf. Invoice belum dibuat.');}''')
    if state=='final':page.locator('#back').click()
    if state=='cash-short':page.locator('#cash').fill('200000')
    if state.startswith('qris') or state=='paid-qris':
     page.locator('[data-method=qris]').click()
     if state!='qris':page.locator('#qris-verified').check()
     if state=='paid-qris':page.locator('#qris-confirm').click()
    if state.startswith('transfer') or state=='paid-transfer':
     page.locator('[data-method=transfer]').click()
     if state!='transfer':page.locator('#reference').fill('TRF-DEMO-0144')
     if state in ('transfer-checked','paid-transfer'):page.locator('#verified').check()
     if state=='paid-transfer':page.locator('#transfer-confirm').click()
    if state=='paid-cash':page.locator('#confirm').click()
   if state!='list' and not state.startswith('paid-'):
    page.evaluate("() => {const b=document.createElement('button');b.id='back-to-list';b.textContent='Kembali ke antrean';document.getElementById('screen').prepend(b)}")
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(device,state)
   links=[]
   def hit(selector,dest,label):
    locator=page.locator(selector).first
    if not locator.count() or not locator.is_visible():return
    box=locator.bounding_box();links.append(dict(box=box,dest=dest,label=label))
   if state=='list':
    hit('article:first-of-type','detail','Pilih SO-0261')
   elif state in ('draft','detail','final'):
    hit('#issue',{'draft':'cash','detail':'draft','final':'cash'}[state],'Lanjut')
   elif state.startswith('paid-'):
    hit('#queue','list','Kembali ke antrean')
   else:
    for method,dest in [('cash','cash'),('qris','qris'),('transfer','transfer')]:hit('[data-method='+method+']',dest,'Metode '+method)
    for selector in ('#back','#qris-back','#transfer-back'):hit(selector,'final','Kembali ke invoice')
    if state in ('cash','cash-short'):
     hit('#cash','cash-short' if state=='cash' else 'cash','Contoh uang tunai')
     if state=='cash':hit('#confirm','paid-cash','Konfirmasi tunai')
    if state in ('qris','qris-checked'):
     hit('#qris-verified','qris-checked' if state=='qris' else 'qris','Periksa dana QRIS')
     if state=='qris-checked':hit('#qris-confirm','paid-qris','Konfirmasi QRIS')
    if state in ('transfer','transfer-filled','transfer-checked'):
     hit('#reference','transfer-filled','Isi contoh referensi')
     hit('#verified','transfer' if state=='transfer' else 'transfer-checked' if state=='transfer-filled' else 'transfer-filled','Periksa mutasi')
     if state=='transfer-checked':hit('#transfer-confirm','paid-transfer','Konfirmasi transfer')
   if state!='list':
    hit('#back-to-list','list','Kembali ke antrean')
   data=page.evaluate(EXTRACT)
   key=device+'-'+state
   (OUT/(key+'.svg')).write_text(data.pop('svg'),encoding='utf-8')
   data.update(key=key,device=device,state=state,viewport=[width,height],links=links)
   report.append(data)
   if state in ('list','detail','qris','paid-transfer'):page.screenshot(path=str(ROOT/'evidence'/(key+'-source.png')),full_page=True)
   page.close()
   print('Captured '+key,flush=True)
 browser.close()
(OUT/'states.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'states':len(report),'links':sum(len(s['links']) for s in report)}))
