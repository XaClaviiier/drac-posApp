"""Exercise saved cashier links through real presenter input; never rebuild screens."""
import json, time
from pathlib import Path
from collections import Counter
from PIL import Image
from native_api import Native
ROOT = Path(__file__).resolve().parents[1]
api = Native()
m = json.loads((ROOT/'evidence/design-completion-map.json').read_text())
f = json.loads((ROOT/'evidence/foundations.json').read_text())
pages = json.loads((ROOT/'evidence/consolidation.json').read_text())['pages']
results = []

def inspect():
    return api.ask('ui.inspect')['preview']

def click_id(node):
    p = inspect()
    hot = next((h for h in p['hotspots'] if h['id'] == node), None)
    assert hot, ('Missing hotspot', node, p)
    r = hot['rect']; point = [(r[0]+r[2])/2, (r[1]+r[3])/2]
    for event in ({'move': point}, {'down': point}, {'up': point}):
        api.ask('ui.input', {'events': [event]})
        time.sleep(.025)
    time.sleep(.03)

try:
    doc = api.ask('document.inspect', {'allPages': True, 'depth': 5})
    (ROOT/'evidence/completed-native-inspection.json').write_text(json.dumps(doc, indent=2))
    roots = {n['id']: n for p in doc['pages'] for n in p.get('children', [])}
    nodes = {}
    def walk(n):
        nodes[n['id']] = n
        for child in n.get('children', []): walk(child)
    for page in doc['pages']: walk(page)
    assert len(m['frames']) == 58
    for edge in m['edges']:
        device = edge['source'].split('-', 1)[0]
        api.command('page.select', {'id': pages['mobile' if device == 'mobile' else 'desktop']})
        api.command('proto.preview', {'start': m['frames'][edge['source']]})
        time.sleep(.035)
        root = roots[m['frames'][edge['source']]]
        n = nodes[edge['node']]
        y = n['absoluteBounds']['y'] - root['absoluteBounds']['y']
        max_scroll = inspect()['scrollRange'][1]
        if y+n['height'] > root['height'] or y > root['height']*.75:
            api.ask('ui.set', {'presentScroll': [0, min(max_scroll, max(0, y-root['height']*.45))]})
            time.sleep(.03)
        click_id(edge['node'])
        after = inspect()
        assert after and after['name'] == edge['target'], (edge, after)
        results.append({'from': edge['source'], 'to': edge['target'], 'node': edge['node'], 'passed': True})
        if len(results)%25 == 0:
            (ROOT/'evidence/completed-playback.json').write_text(json.dumps(results, indent=2))
            print(json.dumps({'linksPassed': len(results)}), flush=True)
    delays = []
    themes = []
    for device in ('desktop', 'mobile'):
        api.command('page.select', {'id': pages['mobile' if device == 'mobile' else 'desktop']})
        api.command('proto.preview', {'start': m['frames'][device+'-loading']})
        time.sleep(1.4)
        assert inspect()['name'] == device+'-list'
        delays.append(device)
        counts = []
        for index in range(3):
            path = ROOT/'evidence'/f'{device}-theme-live-{index}.png'
            api.ask('ui.screenshot', {'path': str(path)})
            counts.append(Counter(Image.open(path).get_flattened_data())[(9,9,11,255)])
            if index < 2: click_id(m['themeControls'][device+'-list'])
        assert counts[1] > counts[0]+1000 and abs(counts[2]-counts[0]) < 100, (device, counts)
        themes.append({'device': device, 'darkCanvasPixelCounts': counts, 'roundTripPassed': True})
    guards = {}
    for device in ('desktop', 'mobile'):
        for state in ('offline','needs-owner','cash-short','qris','transfer','transfer-filled','payment-error'):
            key = device+'-'+state
            outgoing = [e['target'] for e in m['edges'] if e['source'] == key]
            assert not any('-paid-' in target or '-print-' in target for target in outgoing), (key, outgoing)
            guards[key] = outgoing
        assert any(e['source'] == device+'-zero-draft' and e['target'] == device+'-zero-paid' for e in m['edges'])
    fonts = api.command('text.missingFonts')
    assert fonts.get('families', []) == [], fonts
    api.command('page.select', {'id': pages['desktop']})
    api.command('file.saveAs', {'path': str(ROOT/'pos-kasir.figcraft')})
    api.command('proto.preview', {'start': m['frames']['desktop-list']})
    report = {'frames': len(m['frames']), 'linksPassed': len(results), 'automaticLoadingPassed': delays, 'themes': themes, 'guards': guards, 'fonts': fonts}
    (ROOT/'evidence/completed-playback.json').write_text(json.dumps(results, indent=2))
    (ROOT/'evidence/completion-verification.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({'frames': len(m['frames']), 'linksPassed': len(results), 'themeRoundTripsPassed': len(themes), 'fonts': fonts}))
finally:
    api.close()
