"""Build the explicitly authorized two-screen trial in a new live document."""
import json
import queue
import subprocess
import threading
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'trial'
process=subprocess.Popen([r'C:\Program Files\ArtCraft\FigCraft\figcraft-cli.exe','mcp','--attach','7979','--timeout','60'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
responses=queue.Queue()
def reader():
    for line in process.stdout:
        try:responses.put(json.loads(line))
        except ValueError:pass
threading.Thread(target=reader,daemon=True).start()
def request(i,method,params):
    process.stdin.write(json.dumps({'jsonrpc':'2.0','id':i,'method':method,'params':params})+'\n');process.stdin.flush()
    while True:
        value=responses.get(timeout=65)
        if value.get('id')==i:
            if 'error' in value:raise RuntimeError(value['error'])
            return value['result']
results=[]
try:
    request(1,'initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'POS editable trial','version':'1'}})
    process.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n');process.stdin.flush()
    operations=json.loads((OUT/'operations.json').read_text(encoding='utf-8'))
    for i,operation in enumerate(operations,2):
        result=request(i,'tools/call',operation)
        results.append({'operation':operation,'result':result})
        (OUT/'live-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        if result.get('isError'):raise RuntimeError(result)
    print(json.dumps([{'name':r['operation']['name'],'isError':r['result'].get('isError',False)} for r in results]))
finally:
    process.terminate();process.wait(timeout=10)
