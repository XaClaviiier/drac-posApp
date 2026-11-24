"""Inspect and exercise the real native prototype via FigCraft's control API."""
import json,socket,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
mapping=json.loads((ROOT/'evidence/build-map.json').read_text(encoding='utf-8'));states=json.loads((ROOT/'generated/states.json').read_text(encoding='utf-8'))
sock=socket.create_connection(('127.0.0.1',7980),timeout=20);stream=sock.makefile('rwb');sequence=0
def ask(method,params=None):
 global sequence
 sequence+=1;stream.write((json.dumps({'id':sequence,'method':method,'params':params or {},'timeoutMs':15000})+'\n').encode());stream.flush()
 r=json.loads(stream.readline())
 if not r['ok']:raise RuntimeError(r)
 return r['result']
def command(name,params=None):return ask('engine.execute',{'command':name,'params':params or {}})
def inspect():return ask('ui.inspect')['preview']
def begin(device):
 consolidation=ROOT/'evidence/consolidation.json'
 if consolidation.exists():command('page.select',{'id':json.loads(consolidation.read_text(encoding='utf-8'))['pages']['mobile' if device=='mobile' else 'desktop']})
 command('proto.preview',{'start':mapping['frames'][device+'-list']})
 return inspect()
def click(device,source,target):
 edge=next(e for e in mapping['edges'] if e['source']==device+'-'+source and e['target']==device+'-'+target)
 state=next(s for s in states if s['key']==device+'-'+source);box=next(l['box'] for l in state['links'] if l['dest']==target and l['label']==edge['label'])
 if box['y']+box['height']>state['viewport'][1]:
  preview=inspect();anchor=preview['hotspots'][0];ae=next(e for e in mapping['edges'] if e['node']==anchor['id']);ab=next(l['box'] for l in state['links'] if l['label']==ae['label'] and device+'-'+l['dest']==ae['target']);r=anchor['rect'];z=preview['zoom'];ox=r[0]-(ab['x']-preview['scroll'][0])*z;oy=r[1]-(ab['y']-preview['scroll'][1])*z
  point=[ox+state['viewport'][0]*z/2,oy+state['viewport'][1]*z/2]
  ask('ui.input',{'events':[{'move':point},{'scroll':[0,-2000]}]});time.sleep(.1)
 for _ in range(8):
  preview=inspect();hot=next((h for h in preview['hotspots'] if h['id']==edge['node']),None)
  if hot:break
  rect=preview['hotspots'][0]['rect'] if preview['hotspots'] else [950,350,960,360]
  ask('ui.input',{'events':[{'move':[(rect[0]+rect[2])/2,(rect[1]+rect[3])/2]},{'scroll':[0,-250]}]})
 else:raise AssertionError(('Hotspot not visible',device,source,target))
 rect=hot['rect'];point=[(rect[0]+rect[2])/2,(rect[1]+rect[3])/2]
 ask('ui.input',{'events':[{'move':point}]});ask('ui.input',{'events':[{'down':point}]});ask('ui.input',{'events':[{'up':point}]})
 after=inspect();assert after['name']==device+'-'+target,(source,target,after)
 return after
try:
 inspection=ask('document.inspect',{'depth':5,'fields':['name','type','characters','fontFamily','interactions','width','height']})
 for frame in inspection['pages'][0]['children']:
  command('node.set',{'ids':[frame['id']],'props':{'fill':'#FAFAFA'}})
  if frame['name'].endswith('-detail'):
   for node in frame.get('children',[]):
    if node.get('type')=='TEXT' and node.get('characters')=='Total invoice':command('node.set',{'ids':[node['id']],'props':{'characters':'Total realisasi'}})
 command('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
 results=[]
 for device in ('desktop','mobile'):
  begin(device)
  routes=[['list','detail','draft','cash','cash-short','cash','paid-cash','list'],['list','detail','draft','cash','qris','qris-checked','paid-qris','list'],['list','detail','draft','cash','transfer','transfer-filled','transfer-checked','paid-transfer','list']]
  for route in routes:
   begin(device)
   for source,target in zip(route,route[1:]):
    after=click(device,source,target);results.append({'device':device,'from':source,'to':target,'current':after['name'],'scrollRange':after['scrollRange']});(ROOT/'evidence/playback-verified.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
 (ROOT/'evidence/playback-verified.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
 print(json.dumps({'verifiedTransitions':len(results),'devices':['desktop','mobile']}))
finally:stream.close();sock.close()
