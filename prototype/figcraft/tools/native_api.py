"""Small client for the installed FigCraft loopback control protocol."""
import json,socket
class Native:
 def __init__(self):
  self.socket=socket.create_connection(('127.0.0.1',7980),timeout=45);self.stream=self.socket.makefile('rwb');self.number=0
 def ask(self,method,params=None):
  self.number+=1;self.stream.write((json.dumps({'id':self.number,'method':method,'params':params or {},'timeoutMs':40000})+'\n').encode());self.stream.flush();response=json.loads(self.stream.readline())
  if not response['ok']:raise RuntimeError(response)
  return response['result']
 def command(self,name,params=None):return self.ask('engine.execute',{'command':name,'params':params or {}})
 def node(self,kind,parent=None,**kwargs):
  if parent is not None:kwargs['parent']=parent
  return self.command('node.create',dict(type=kind,**kwargs))['id']
 def set(self,ids,**props):return self.command('node.set',{'ids':ids if isinstance(ids,list) else [ids],'props':props})
 def close(self):self.stream.close();self.socket.close()
