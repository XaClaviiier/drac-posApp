"""Consolidate the active prototype and reference images into one native file."""
import hashlib,json,socket,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'pos-kasir.figcraft'
mapping=json.loads((ROOT/'evidence/build-map.json').read_text(encoding='utf-8'))
sock=socket.create_connection(('127.0.0.1',7980),timeout=30)
stream=sock.makefile('rwb');sequence=0
def ask(method,params=None):
 global sequence
 sequence+=1
 stream.write((json.dumps({'id':sequence,'method':method,'params':params or {}})+'\n').encode());stream.flush()
 response=json.loads(stream.readline())
 if not response['ok']:raise RuntimeError(response)
 return response['result']
def command(name,params=None):return ask('engine.execute',{'command':name,'params':params or {}})
try:
 before=ask('document.inspect',{'depth':1,'outline':True})
 assert before['name']=='POS Kasir - Poppins - Manual Payments',before['name']
 assert not before['dirty'],'Document has unsaved changes; preserve them before consolidation'
 assert len(before['pages'])==1,'Already consolidated or changed; inspect before repeating'
 archive=ROOT/'archive';archive.mkdir(exist_ok=True)
 backup=archive/'before-one-file.zip'
 assert not backup.exists(),'Existing backup: inspect before repeating'
 with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as z:z.write(TARGET,'pos-kasir.figcraft')
 original_hash=hashlib.sha256(TARGET.read_bytes()).hexdigest()
 desktop=before['pages'][0]['id']
 command('proto.closePreview')
 command('page.rename',{'id':desktop,'name':'Desktop'})
 command('proto.flow.remove',{'start':mapping['frames']['mobile-list']})
 mobile=command('page.add',{'name':'Ponsel'})['id']
 mobile_ids=[node for key,node in mapping['frames'].items() if key.startswith('mobile-')]
 command('node.reparent',{'ids':mobile_ids,'parent':mobile})
 for index,node in enumerate(mobile_ids):command('node.set',{'ids':[node],'props':{'x':(index%4)*454,'y':(index//4)*950}})
 command('page.select',{'id':mobile})
 command('proto.flow.add',{'start':mapping['frames']['mobile-list'],'name':'Kasir / Ponsel / Demo SO-0261'})
 reference=command('page.add',{'name':'Referensi'})['id']
 command('page.select',{'id':reference})
 assets=[]
 for index,(name,label) in enumerate([('desktop-source.png','Acuan desktop / First pair refined'),('mobile-source.png','Acuan ponsel / First pair refined')]):
  path=ROOT.parents[1]/'doc/DBD/figcraft-handoff-v1/trial'/name
  assert path.is_file(),str(path)
  command('node.create',{'type':'text','x':index*1504,'y':0,'width':1440,'text':label,'props':{'fontFamily':'Poppins','fontStyle':'Semi Bold','fontSize':20,'fill':'#18181B'}})
  node=command('file.import',{'path':str(path),'x':index*1504,'y':56})['id']
  command('node.set',{'ids':[node],'props':{'name':label}})
  assets.append({'id':node,'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 command('page.select',{'id':desktop})
 command('file.saveAs',{'path':str(TARGET)})
 after=ask('document.inspect',{'allPages':True,'depth':5,'fields':['name','type','characters','fontFamily','interactions','width','height'],'maxBytes':7000000})
 (ROOT/'evidence/native-inspection.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
 command('proto.preview',{'start':mapping['frames']['desktop-list']})
 report={'file':str(TARGET),'backup':str(backup),'priorSha256':original_hash,'pages':{'desktop':desktop,'mobile':mobile,'reference':reference},'references':assets,'sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest()}
 (ROOT/'evidence/consolidation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report))
finally:stream.close();sock.close()
