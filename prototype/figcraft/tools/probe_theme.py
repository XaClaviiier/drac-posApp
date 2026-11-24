"""Capture a real presenter theme toggle without changing document tokens."""
import json, time
from pathlib import Path
from native_api import Native
ROOT = Path(__file__).resolve().parents[1]
api = Native()
mapping = json.loads((ROOT/'evidence/design-completion-map.json').read_text())
try:
    api.command('page.select', {'id': 1})
    api.command('proto.preview', {'start': mapping['frames']['desktop-list']})
    result = []
    for index in range(3):
        time.sleep(.15)
        capture = api.ask('ui.screenshot', {'path': str(ROOT/'evidence'/f'theme-live-{index}.png')})
        result.append({'index': index, 'capture': capture})
        if index == 2:
            break
        preview = api.ask('ui.inspect')['preview']
        hot = next(h for h in preview['hotspots'] if h['id'] == mapping['themeControls']['desktop-list'])
        r = hot['rect']; p = [(r[0]+r[2])/2, (r[1]+r[3])/2]
        for event in ({'move': p}, {'down': p}, {'up': p}):
            api.ask('ui.input', {'events': [event]})
            time.sleep(.1)
    (ROOT/'evidence/theme-live-captures.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
finally:
    api.close()
