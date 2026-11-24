"""Verify real mode switching and prepare consistent component hover colors."""
import json,time
from pathlib import Path
from native_api import Native
ROOT=Path(__file__).resolve().parents[1];api=Native();c=api.command
f=json.loads((ROOT/'evidence/foundations.json').read_text(encoding='utf-8'));m=json.loads((ROOT/'evidence/design-completion-map.json').read_text(encoding='utf-8'));con=json.loads((ROOT/'evidence/consolidation.json').read_text(encoding='utf-8'))
try:
 additions={'PrimaryHover':['#0058C2','#85BCFF'],'PrimaryPressed':['#00479E','#A5CFFF'],'ControlHover':['#F4F4F5','#27272A'],'ControlPressed':['#E4E4E7','#3F3F46']}
 for name,pair in additions.items():f['variables'][name]=c('variable.create',{'collection':f['collection'],'name':name,'type':'color','values':dict(zip(['Light','Dark'],pair))})['id']
 for kind,variants in f['variants'].items():
  for state in ('Hover','Pressed'):
   role=('Primary' if kind=='Primary' else 'Control')+state
   api.set(variants[state],fill={'$var':f['variables'][role]})
 (ROOT/'evidence/foundations.json').write_text(json.dumps(f,indent=2),encoding='utf-8')
 headers=m['instances'][-len(m['frames'])*2:];m['themeControls']={key:headers[i*2+1] for i,key in enumerate(m['frames'])}
 (ROOT/'evidence/design-completion-map.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
 c('page.select',{'id':con['pages']['desktop']});c('proto.preview',{'start':m['frames']['desktop-list']})
 before=api.ask('ui.inspect');theme=m['themeControls']['desktop-list'];hot=next(h for h in before['preview']['hotspots'] if h['id']==theme)
 rect=hot['rect'];point=[(rect[0]+rect[2])/2,(rect[1]+rect[3])/2]
 for event in ({'move':point},{'down':point},{'up':point}):api.ask('ui.input',{'events':[event]})
 after=api.ask('ui.inspect')
 (ROOT/'evidence/theme-playback.json').write_text(json.dumps({'before':before['preview'],'after':after['preview']},indent=2),encoding='utf-8')
 for mode in ('Light','Dark'):
  c('variable.setMode',{'ids':[m['frames']['desktop-list'],m['frames']['mobile-list']],'collection':f['collection'],'mode':mode})
  for device in ('desktop','mobile'):
   c('file.export',{'ids':[m['frames'][device+'-list']],'format':'png','path':str(ROOT/'evidence'/(device+'-list-'+mode.lower()+'.png')),'scale':1})
 c('variable.setMode',{'ids':[m['frames']['desktop-list'],m['frames']['mobile-list']],'collection':f['collection'],'mode':None})
 c('file.saveAs',{'path':str(ROOT/'pos-kasir.figcraft')})
 print(json.dumps({'previewModeBefore':before['preview'],'previewModeAfter':after['preview']}))
finally:api.close()
