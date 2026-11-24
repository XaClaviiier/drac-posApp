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
frames={};edges=[];components=[]
def checkpoint():
 (ROOT/'evidence/build-map.json').write_text(json.dumps({'frames':frames,'edges':edges,'components':components},indent=2),encoding='utf-8')
try:
 request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'POS cashier prototype','version':'1'}})
 proc.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n');proc.stdin.flush()
 command('file.new',{'name':'POS Kasir - Poppins - Manual Payments'})
 for index,state in enumerate(states):
  group=index%14;mobile=state['device']=='mobile';x=(6400 if mobile else 0)+(group%4)*(454 if mobile else 1504);y=(group//4)*1100
  result=command('file.import',{'path':str(ROOT/'generated'/(state['key']+'.svg')),'x':x,'y':y})
  node=result['id'];frames[state['key']]=node
  call('set_properties',{'ids':[node],'props':{'name':state['key'],'height':state['viewport'][1],'fill':'#FAFAFA','clip':True,'overflow':'vertical'}})
  checkpoint();print('Imported '+state['key'],flush=True)
 # Turn actual primary/back button primitives into reusable native components.
 inspection=call('inspect_document',{'depth':3,'fields':['name','type','x','y','width','height','characters'],'maxBytes':4000000})
 allframes=inspection['pages'][0]['children']
 for device in ('desktop','mobile'):
  state=next(s for s in states if s['key']==device+'-draft');frame=next(f for f in allframes if f['id']==frames[state['key']])
  for label in ('Lanjut','Kembali ke antrean'):
   link=next(l for l in state['links'] if l['label']==label);box=link['box']
   ids=[n['id'] for n in frame.get('children',[]) if n['type'] in ('RECTANGLE','TEXT') and n.get('x',0)>=box['x']-1 and n.get('y',0)>=box['y']-1 and n.get('x',0)+n.get('width',0)<=box['x']+box['width']+2 and n.get('y',0)+n.get('height',0)<=box['y']+box['height']+2]
   if len(ids)>=2:
    component=command('component.create',{'ids':ids});components.append({'device':device,'label':label,'sourceLayers':ids,'result':component})
 for state in states:
  for link in state['links']:
   dest=state['device']+'-'+link['dest'];assert dest in frames,dest
   box=dict(link['box']);padx=max(0,44-box['width'])/2;pady=max(0,44-box['height'])/2;box.update(x=box['x']-padx,y=box['y']-pady,width=max(44,box['width']),height=max(44,box['height']));node=call('create_node',{'type':'rectangle','parent':frames[state['key']],'name':'Demo / '+link['label'],'x':box['x'],'y':box['y'],'width':box['width'],'height':box['height'],'props':{'fill':'#00000000'},'select':False})
   node=node['id'] if isinstance(node,dict) else node
   command('proto.interaction.add',{'id':node,'dest':frames[dest],'transition':{'type':'instant'}})
   edges.append({'source':state['key'],'target':dest,'node':node,'label':link['label']})
  checkpoint()
 command('proto.flow.add',{'start':frames['desktop-list'],'name':'Kasir / Desktop / Demo SO-0261'})
 command('proto.flow.add',{'start':frames['mobile-list'],'name':'Kasir / Ponsel / Demo SO-0261'})
 call('save_file',{'path':str(ROOT/'pos-kasir.figcraft')})
 inspection=call('inspect_document',{'depth':5,'fields':['name','type','width','height','fontFamily','characters','interactions'],'maxBytes':6000000})
 (ROOT/'evidence/native-inspection.json').write_text(json.dumps(inspection,indent=2),encoding='utf-8')
 missing=command('text.missingFonts');assert not missing['families'],missing
 for key in ('desktop-list','desktop-detail','desktop-qris-checked','mobile-list','mobile-paid-transfer'):
  call('export',{'ids':[frames[key]],'format':'png','path':str(ROOT/'evidence'/(key+'-native.png')),'scale':1})
 command('view.zoomFit')
 command('proto.preview',{'start':frames['desktop-list']})
 checkpoint();print(json.dumps({'file':str(ROOT/'pos-kasir.figcraft'),'frames':len(frames),'links':len(edges),'components':len(components),'missingFonts':missing['families']}),flush=True)
finally:
 proc.terminate();proc.wait(timeout=10)
