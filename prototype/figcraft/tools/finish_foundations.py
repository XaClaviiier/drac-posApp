"""Add semantic native color modes, type styles and reusable button variants."""
import json,zipfile
from pathlib import Path
from collections import defaultdict
from native_api import Native
ROOT=Path(__file__).resolve().parents[1];api=Native();c=api.command
doc=api.ask('document.inspect',{'allPages':True,'depth':5})
assert doc['name']=='POS Kasir - Poppins - Manual Payments'
assert not doc['dirty'],'Unsaved edits found; inspect before changing foundations'
assert doc['variables']==0,'Foundations already exist; inspect instead of duplicating'
with zipfile.ZipFile(ROOT/'archive/before-cashier-finish.zip','w',zipfile.ZIP_DEFLATED) as z:z.write(ROOT/'pos-kasir.figcraft','pos-kasir.figcraft')
roles={
 'Canvas':['#FAFAFA','#09090B'],'Surface':['#FFFFFF','#18181B'],'Secondary':['#F4F4F5','#202023'],
 'Text':['#18181B','#FAFAFA'],'Muted':['#52525B','#A1A1AA'],'Border':['#E4E4E7','#323237'],
 'Input':['#8B8B95','#71717A'],'Primary':['#006BEB','#66AAFF'],'OnPrimary':['#FFFFFF','#10233E'],
 'Selected':['#E9F2FF','#20344E'],'Service':['#0058C2','#66AAFF'],'Part':['#0F766E','#7DD3C8'],
 'PartSurface':['#F0FDFA','#123B36'],'Success':['#147A52','#71D9AA'],'SuccessSurface':['#EAF7F0','#17372C'],
 'Warning':['#8B5B10','#F2CE87'],'WarningSurface':['#FFF5E0','#3B301C'],'Error':['#B42332','#FFACB7'],'ErrorSurface':['#FFF1F2','#451C25']}
collection=c('variable.createCollection',{'name':'POS','modes':['Light','Dark']})['id'];variables={}
for role,values in roles.items():variables[role]=c('variable.create',{'collection':collection,'name':role,'type':'color','values':dict(zip(['Light','Dark'],values))})['id']
aliases={'#000000':'Text','#71717A':'Muted','#B9D9FF':'Primary','#C2DBFF':'Primary','#D4D4D8':'Border','#FDE68A':'Warning'}
lookup={v[0]:k for k,v in roles.items() if k!='OnPrimary'};lookup.update(aliases)
groups=defaultdict(list);small=[];texts=[]
def walk(n,fixed=False):
 if n.get('type')=='TEXT':
  texts.append(n)
  if n.get('fontSize',12)<12:small.append(n['id'])
 if not fixed:
  for field in ('fills','strokes'):
   for index,paint in enumerate(n.get(field,[])):
    if paint.get('type')!='solid' or paint.get('opacity',1)==0:continue
    color=paint.get('color');role='OnPrimary' if color=='#FFFFFF' and n.get('type')=='TEXT' else lookup.get(color)
    if role:groups[(field+'/'+str(index)+'/color',role)].append(n['id'])
 for child in n.get('children',[]):walk(child,fixed)
for page in doc['pages']:
 if page['name']=='Referensi':continue
 for frame in page.get('children',[]):
  fixed_ids=set()
  if '-paid-' in frame['name']:
   white=[n for n in frame.get('children',[]) if n.get('type')=='RECTANGLE' and 300<=n.get('width',0)<=700 and any(p.get('color')=='#FFFFFF' for p in n.get('fills',[]))]
   if white:
    paper=max(white,key=lambda n:n['width']*n['height']);b=paper['absoluteBounds']
    for n in frame.get('children',[]):
     a=n.get('absoluteBounds',{})
     if a and a['x']>=b['x']-2 and a['y']>=b['y']-2 and a['x']+a['width']<=b['x']+b['width']+2 and a['y']+a['height']<=b['y']+b['height']+2:fixed_ids.add(n['id'])
  saved=frame.get('children',[]);frame['children']=[];walk(frame);frame['children']=saved
  for n in saved:walk(n,n['id'] in fixed_ids)
for (field,role),ids in groups.items():c('variable.bind',{'ids':ids,'field':field,'variable':variables[role]})
if small:api.set(small,fontSize=12)
styles={}
for name,size,weight in [('Body',14,'Regular'),('Label',12,'Medium'),('Heading',28,'Semi Bold'),('Plate',20,'Semi Bold'),('Total',23,'Bold')]:
 styles[name]=c('style.create',{'type':'text','name':'POS / '+name,'value':{'fontFamily':'Poppins','fontStyle':weight,'fontSize':size}})['id']
library=c('page.add',{'name':'Komponen'})['id'];c('page.select',{'id':library})
buttons={};variant_report={}
for column,kind in enumerate(('Primary','Secondary')):
 node=api.node('component',x=column*560,y=0,width=220,height=44,name='State=Default',props={'fill':{'$var':variables['Primary' if kind=='Primary' else 'Surface']},'stroke':{'$var':variables['Primary' if kind=='Primary' else 'Border']},'cornerRadius':8,'layout':'horizontal','mainAlign':'center','crossAlign':'center','padding':12})
 label=api.node('text',node,text='Tombol',props={'fontFamily':'Poppins','fontSize':14,'fontStyle':'Semi Bold','fill':{'$var':variables['OnPrimary' if kind=='Primary' else 'Text']}})
 c('component.addProperty',{'id':node,'layer':label,'name':'Label','type':'text','default':'Tombol'})
 variants={'Default':node}
 for state in ('Hover','Pressed','Focus','Disabled'):
  variant=c('component.addVariant',{'id':node,'property':'State','value':state})['id'];variants[state]=variant
  if state in ('Hover','Pressed'):api.set(variant,fill={'$var':variables['Service' if kind=='Primary' else 'Selected']})
  if state=='Focus':api.set(variant,stroke={'$var':variables['Primary']},strokeWeight=2)
  if state=='Disabled':api.set(variant,opacity=.4)
 for state,node_id in variants.items():
  if state=='Disabled':continue
  # Mouse-up variant changes consume the instance click in the installed player.
  for trigger,dest in [('mouseEnter','Hover'),('mouseLeave','Default'),('mouseDown','Pressed')]:
   c('proto.interaction.add',{'id':node_id,'trigger':{'type':trigger},'action':{'type':'changeTo','dest':variants[dest]},'transition':{'type':'instant'}})
 buttons[kind]=variants['Default'];variant_report[kind]=variants
report={'collection':collection,'variables':variables,'roles':roles,'styles':styles,'buttons':buttons,'variants':variant_report,'libraryPage':library,'smallLabelsAdjusted':len(small),'colorBindings':sum(len(v) for v in groups.values())}
(ROOT/'evidence/foundations.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')});print(json.dumps({'variables':len(variables),'styles':len(styles),'buttonSets':len(buttons),'smallLabels':len(small),'bindings':report['colorBindings']}));api.close()
