"""Check the customer-history slice, render it, and read back the saved file."""
import hashlib
import io
import json
import time
import zipfile
from collections import Counter
from pathlib import Path

from PIL import Image

from native_api import Native

ROOT = Path(__file__).resolve().parents[1]
m = json.loads((ROOT / 'evidence/customer-history-map.json').read_text(encoding='utf-8'))
f = json.loads((ROOT / 'evidence/foundations.json').read_text(encoding='utf-8'))
verification = json.loads((ROOT / 'evidence/customer-history-verification.json').read_text(encoding='utf-8'))
assert verification['status'] == 'complete'
api = Native()
c = api.command


def preview():
    return api.ask('ui.inspect')['preview']


def begin(source):
    c('proto.preview', {'start': m['frames'][source]})
    for _ in range(20):
        time.sleep(.1)
        p = preview()
        if p and p.get('name') == source and p.get('frameSize') and p.get('hotspots'):
            return p
    raise AssertionError(('Preview viewport is not ready', source))


def tap(node):
    api.ask('ui.input', {'events': [{'move': [20, 20]}]})
    time.sleep(.08)
    n = api.ask('node.get', {'id': node, 'depth': 0})
    p = preview()
    assert p and p.get('frameSize'), 'FigCraft preview has no geometry'
    desired = min(p['scrollRange'][1], max(0, n['y'] - p['frameSize'][1] * .4))
    if abs(p['scroll'][1] - desired) > .5:
        api.ask('ui.set', {'presentScroll': [0, desired]})
    hot = None
    for _ in range(20):
        time.sleep(.1)
        p = preview()
        if abs(p['scroll'][1] - desired) < .5:
            hot = next((h for h in p['hotspots'] if h['id'] == node), None)
            if hot:
                break
    assert hot, ('Native hotspot unavailable after scrolling', node, p['name'])
    r = hot['rect']
    point = [(r[0] + r[2]) / 2, (r[1] + r[3]) / 2]
    for event in ({'move': point}, {'down': point}, {'up': point}):
        api.ask('ui.input', {'events': [event]})
        time.sleep(.12)
    time.sleep(.16)


try:
    c('proto.closePreview')
    pending_documents = []
    for device in ('desktop', 'mobile'):
        c('page.select', {'id': 2079 if device == 'mobile' else 1})
        for label in ('Diagnosa & Estimasi', 'Service Order', 'Invoice', 'Nota'):
            source = device + '-ch-visit-current'
            begin(source)
            edge = next(e for e in m['edges'] if e['source'] == source and e['label'] == label)
            tap(edge['node'])
            assert preview()['name'] == device + '-ch-pending', (device, label, preview()['name'])
            pending_documents.append({'device': device, 'document': label, 'passed': True})
            c('proto.closePreview')
    themes = []
    for device in ('desktop', 'mobile'):
        c('page.select', {'id': 2079 if device == 'mobile' else 1})
        source = device + '-ch-hub'
        begin(source)
        counts = []
        for i in range(3):
            name = f'customer-history-{device}-theme-{i}.png'
            api.ask('ui.screenshot', {'path': str(ROOT / 'evidence' / name)})
            counts.append(Counter(Image.open(ROOT / 'evidence' / name).get_flattened_data())[(9, 9, 11, 255)])
            if i < 2:
                tap(m['themeControls'][source])
        assert counts[1] > counts[0] + 1000 and abs(counts[2] - counts[0]) < 100, (device, counts)
        themes.append({'device': device, 'darkPixelCounts': counts, 'passed': True})

    # Wheel input must reach the lower action in the phone layout.
    c('page.select', {'id': 2079})
    before = begin('mobile-ch-hub')
    visible = next(e for e in m['edges'] if e['source'] == 'mobile-ch-hub' and e['label'] == 'Buka pelanggan')
    r = next(h for h in before['hotspots'] if h['id'] == visible['node'])['rect']
    point = [(r[0] + r[2]) / 2, (r[1] + r[3]) / 2]
    api.ask('ui.input', {'events': [{'move': point}, {'scroll': [0, -3000]}]})
    for _ in range(20):
        time.sleep(.1)
        after = preview()
        if after['scroll'][1] > 0:
            break
    assert after['scroll'][1] > 0, after
    edge = next(e for e in m['edges'] if e['source'] == 'mobile-ch-hub' and e['label'] == 'Demo: layanan Maya 0147')
    tap(edge['node'])
    assert preview()['name'] == 'mobile-so-hub'
    wheel = {'scroll': after['scroll'], 'range': after['scrollRange'], 'lowerControlClicked': True, 'passed': True}
    c('proto.closePreview')

    exports = []
    for source, theme in [('desktop-ch-customers', 'Light'), ('mobile-ch-customers', 'Light'),
                          ('desktop-ch-timeline', 'Light'), ('mobile-ch-visit-old', 'Dark'),
                          ('desktop-ch-old-invoice', 'Dark'), ('mobile-ch-old-receipt', 'Dark')]:
        frame = m['frames'][source]
        try:
            c('variable.setMode', {'ids': [frame], 'collection': f['collection'], 'mode': theme})
            name = f'{source}-{theme.lower()}.png'
            c('file.export', {'ids': [frame], 'format': 'png', 'path': str(ROOT / 'evidence' / name), 'scale': 1})
            exports.append(name)
        finally:
            c('variable.setMode', {'ids': [frame], 'collection': f['collection'], 'mode': None})

    doc = api.ask('document.inspect', {'allPages': True, 'depth': 4, 'fields': ['name', 'type', 'fontFamily', 'fills', 'x', 'y', 'width', 'height', 'mainComponent']})
    types, fonts = Counter(), Counter()
    probes, image_pages = [], []

    def walk(node):
        types[node['type']] += 1
        if node['type'] == 'TEXT':
            fonts[node.get('fontFamily')] += 1
        if node.get('name', '').startswith('__runtime_assert'):
            probes.append(node['id'])
        return sum(p.get('type') == 'image' for p in node.get('fills', [])) + sum(walk(ch) for ch in node.get('children', []))

    for page in doc['pages']:
        image_pages.append({'page': page['name'], 'count': walk(page)})
    assert not probes, probes
    assert types['FRAME'] == m['baseline']['frames'] + len(m['frames']), types
    assert types['COMPONENT'] == 19 and types['COMPONENT_SET'] == 3, types
    assert set(fonts) == {'Poppins'}, fonts
    assert all(p['count'] == 0 for p in image_pages if p['page'] in ('Desktop', 'Ponsel'))
    assert not c('text.missingFonts').get('families', [])
    c('page.select', {'id': 1})
    frame = next(n for page in doc['pages'] for n in page.get('children', []) if n['id'] == m['frames']['desktop-ch-hub'])
    c('view.set', {'zoom': 62, 'cx': frame['x'] + 720, 'cy': frame['y'] + 500})
    path = ROOT / 'pos-kasir.figcraft'
    c('file.saveAs', {'path': str(path)})
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        saved = json.loads(archive.read('document.json'))
        hashes = {hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist() if n.startswith('images/')}
        original = json.loads((ROOT / 'evidence/consolidation.json').read_text(encoding='utf-8'))
        assert hashes == {r['sha256'] for r in original['references']}
    with zipfile.ZipFile(ROOT / 'archive/before-customer-history.zip') as archive:
        baseline_bytes = archive.read('pos-kasir.figcraft')
    assert hashlib.sha256(baseline_bytes).hexdigest() == m['baseline']['sha256']
    with zipfile.ZipFile(io.BytesIO(baseline_bytes)) as archive:
        baseline = json.loads(archive.read('document.json'))
    changed = []
    expected = {e['node'] for e in m['patchedHistoryLinks']}
    for key, old in baseline['nodes'].items():
        assert key in saved['nodes'], ('Prior node missing', key)
        new = saved['nodes'][key]
        if old != new:
            fields = {k for k in set(old) | set(new) if old.get(k) != new.get(k)}
            assert (old['id'] in expected and fields == {'interactions'}) or (old['id'] in (1, 2079) and fields <= {'flows', 'children'}), (old['id'], fields)
            changed.append({'id': old['id'], 'name': old['name'], 'fields': sorted(fields)})
    preservation = {'baselineNodes': len(baseline['nodes']), 'currentNodes': len(saved['nodes']),
                    'allPriorNodesPreserved': True, 'changedPriorNodes': changed,
                    'allowedChanges': '60 POS history links plus the two pages children/flows',
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'passed': True}
    (ROOT / 'evidence/customer-history-preservation.json').write_text(json.dumps(preservation, indent=2), encoding='utf-8')
    reopened = c('file.open', {'path': str(path), 'reload': True})
    assert not reopened.get('warnings'), reopened
    readback = api.ask('document.inspect', {'allPages': True, 'depth': 1, 'fields': ['name', 'type']})
    actual = {n['name']: n['id'] for p in readback['pages'] for n in p.get('children', [])}
    assert all(actual.get(name) == node for name, node in m['frames'].items())
    report = {
        'file': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size,
        'pages': [p['name'] for p in doc['pages']], 'nodeTypes': dict(types), 'fonts': dict(fonts),
        'imagePages': image_pages, 'referenceImageHashes': sorted(hashes),
        'newFrames': len(m['frames']), 'stateFields': len(m['fieldModes']), 'controlActions': len(m['edges']),
        'historyLinksUpdated': len(m['patchedHistoryLinks']), 'nativeStepsPassed': verification['nativeStepsPassed'],
        'runtimeChecksPassed': verification['runtimeChecksPassed'], 'themesPassed': themes,
        'unavailableDocumentGuards': pending_documents,
        'realWheelScroll': wheel, 'nativeExports': exports, 'temporaryTestNodesRemaining': len(probes),
        'readback': reopened, 'allNewFramesReadBack': True,
        'priorNodesPreserved': preservation['baselineNodes'],
        'limits': verification['limits'] + ['keyboard, screen reader and full reflow not verified', 'no real printing or PDF integration'],
    }
    (ROOT / 'evidence/customer-history-delivery.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (ROOT / 'evidence/customer-history-final-inspection.json').write_text(json.dumps(doc, indent=2), encoding='utf-8')
    c('proto.preview', {'start': m['frames']['desktop-ch-hub']})
    print(json.dumps({k: report[k] for k in ('newFrames', 'nodeTypes', 'nativeStepsPassed', 'runtimeChecksPassed', 'temporaryTestNodesRemaining', 'realWheelScroll', 'sha256')}))
finally:
    api.close()
