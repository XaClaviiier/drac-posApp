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
 request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'POS playback test','version':'1'}})
 proc.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n');proc.stdin.flush()
 command('view.set',{'zoom':1,'cx':0,'cy':0})
 ui=call('inspect_ui',{});preview=ui['preview'];rect=preview['hotspots'][0]['rect'];canvas=ui['canvas']['rect']
 x=(rect[0]+rect[2])/2-(canvas[0]+canvas[2]/2);y=(rect[1]+rect[3])/2-(canvas[1]+canvas[3]/2)
 call('pointer',{'x':x,'y':y,'kind':'click'})
 after=call('inspect_ui',{})
 report={'before':preview['name'],'after':after.get('preview'),'point':[x,y]}
 (ROOT/'evidence/playback-click-test.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report))
finally:proc.terminate();proc.wait(timeout=10)
