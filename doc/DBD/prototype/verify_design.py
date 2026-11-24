"""Verify the generated visual artifact without running the POS application."""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def luminance(rgb):
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
    return sum(v * k for v, k in zip(linear, (.2126, .7152, .0722)))


def ratio(a, b):
    a, b = sorted((luminance(a), luminance(b)))
    return (b + .05) / (a + .05)


def rgb(n):
    c = n['fills'][0]['color']
    return tuple(c[k] for k in ('r', 'g', 'b'))


def main():
    document = json.loads((HERE / 'pos-ui.figcraft-source.json').read_text(encoding='utf-8'))['document']
    frames = [f for p in document['children'] for f in p['children']]
    base = [f for f in frames if f['name'].endswith('/ base') and f['name'].split(' / ')[0] in (
        'Terima mobil', 'Work order', 'Mekanik', 'Kasir', 'Invoice', 'Ringkasan',
        'Riwayat plat', 'Laporan', 'Jasa dan Part', 'Cocok Part', 'Pengaturan')]
    assert len(base) == 44, len(base)
    assert sum(f['name'].startswith('Pembayaran /') for f in frames) == 4
    source = (HERE.parents[2] / 'index.html').read_text(encoding='utf-8')
    assert len(set(re.findall(r'<section id="v-([^\"]+)"', source))) == 11
    nodes = {}
    pairs = {}
    links = []
    failures = []
    for frame in frames:
        shapes = []
        children = frame['children']
        scrim = next((i for i, n in enumerate(children) if n['name'] == 'Payment scrim'), None)

        def walk(n, visible=True):
            nodes[n['id']] = n
            b = n['absoluteBoundingBox']
            if n.get('interactions'):
                for interaction in n['interactions']:
                    for action in interaction['actions']:
                        links.append((n['id'], action['destinationId']))
                if n['type'] != 'TEXT':
                    assert b['height'] >= 44 and b['width'] >= 44, n['name']
            if n['type'] != 'TEXT' and n.get('fills'):
                shapes.append(n)
            if n['type'] == 'TEXT' and visible:
                # First ink position avoids the unused remainder of wide text boxes.
                point = b['x'] + min(5, b['width']/2), b['y'] + n['style']['fontSize']/2
                background = next(s for s in reversed(shapes) if (
                    s['absoluteBoundingBox']['x'] <= point[0] <= s['absoluteBoundingBox']['x'] + s['absoluteBoundingBox']['width'] and
                    s['absoluteBoundingBox']['y'] <= point[1] <= s['absoluteBoundingBox']['y'] + s['absoluteBoundingBox']['height']))
                foreground, ground = rgb(n), rgb(background)
                value = ratio(foreground, ground)
                style = n['style']
                threshold = 3 if style['fontSize'] >= 24 or (style['fontSize'] >= 18.667 and style['fontWeight'] >= 700) else 4.5
                pair = tuple(round(c*255) for c in foreground), tuple(round(c*255) for c in ground)
                pairs[pair] = round(value, 3)
                if value < threshold:
                    failures.append((frame['name'], n['characters'], round(value, 3), threshold))
            for child in n.get('children', []):
                walk(child, visible)

        walk_shallow = dict(frame, children=[])
        walk(walk_shallow)
        for i, child in enumerate(children):
            walk(child, scrim is None or i > scrim)
    assert all(to in nodes for _, to in links), 'Broken prototype destination'
    report = dict(frames=len(frames), base_frames=len(base), nodes=len(nodes), links=len(links),
                  text_pairs=[dict(foreground=a, background=b, ratio=v) for (a,b),v in sorted(pairs.items())],
                  contrast_failures=failures,
                  method='WCAG sRGB luminance; visible text first-ink backing surface; obscured modal background excluded',
                  limitation='Static artifact. Keyboard, reduced motion, form input and runtime actions require the browser phase.')
    target = 'verification-failed.json' if failures else 'verification.json'
    (HERE / target).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True))
    assert not failures, f'{len(failures)} contrast failures'


if __name__ == '__main__':
    main()
