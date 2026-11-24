"""Build editable state screens and explicit demo links in a new live document."""
import json,queue,subprocess,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
states=json.loads((ROOT/'generated/states.json').read_text(encoding='utf-8'))
proc=subprocess.Popen([r'C:\Program Files\ArtCraft\FigCraft\figcraft-cli.exe','mcp','--attach','7980','--timeout','60'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
responses=queue.Queue();counter=0
def reader():
 for line in proc.stdout:
  try:responses.put(json.loads(line))
  except ValueError:pass
threading.Thread(target=reader,daemon=True).start()
def request(method,params):
 global counter
 counter+=1;number=counter
 proc.stdin.write(json.dumps({'jsonrpc':'2.0','id':number,'method':method,'params':params})+'\n');proc.stdin.flush()
 while True:
  reply=responses.get(timeout=65)
  if reply.get('id')==number:
   if 'error' in reply:raise RuntimeError(reply['error'])
   return reply['result']
def call(name,args):
 result=request('tools/call',{'name':name,'arguments':args})
 if result.get('isError'):raise RuntimeError(result)
 texts=[c['text'] for c in result.get('content',[]) if c['type']=='text']
 return json.loads(texts[0]) if texts else result
def command(name,params=None):return call('run_command',{'command':name,'params':params or {}})

try:
 request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'POS final inspection','version':'1'}})
 proc.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n');proc.stdin.flush()
 m=json.loads((ROOT/'evidence/build-map.json').read_text(encoding='utf-8'))
 states=json.loads((ROOT/'generated/states.json').read_text(encoding='utf-8'))
 for edge in m['edges']:
  state=next(v for v in states if v['key']==edge['source']);box=next(l['box'] for l in state['links'] if l['label']==edge['label'] and state['device']+'-'+l['dest']==edge['target']);px=max(0,44-box['width'])/2;py=max(0,44-box['height'])/2
  if px or py:call('set_properties',{'ids':[edge['node']],'props':{'x':box['x']-px,'y':box['y']-py,'width':max(44,box['width']),'height':max(44,box['height'])}})
 for c in m['components']:
  command('node.set',{'ids':[c['result']['id']],'props':{'name':'Button / '+('Primary' if c['label']=='Lanjut' else 'Back')+' / '+c['device']}})
 call('save_file',{'path':str(ROOT/'pos-kasir.figcraft')})
 doc=call('inspect_document',{'depth':5,'fields':['name','type','width','height','fontFamily','characters','interactions'],'maxBytes':6000000})
 (ROOT/'evidence/native-inspection.json').write_text(json.dumps(doc,indent=2),encoding='utf-8')
 for key in ('desktop-detail','desktop-qris-checked','mobile-paid-transfer'):
  call('export',{'ids':[m['frames'][key]],'format':'png','path':str(ROOT/'evidence'/(key+'-native.png')),'scale':1})
 command('proto.preview',{'start':m['frames']['desktop-list']})
 print(json.dumps({'saved':True,'frames':len(m['frames']),'missingFonts':command('text.missingFonts')}))
finally:proc.terminate();proc.wait(timeout=10)
