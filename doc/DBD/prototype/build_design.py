"""Generate editable FigCraft REST import geometry, not application code.

Run from this folder: python build_design.py
The source index.html and its storage are never opened by this generator.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
NEXT = 1
LINKS = []
FRAMES = {}
NODES = []
LIGHT = dict(bg='#F7F9FC', surface='#FFFFFF', side='#F1F4F8', ink='#172B4D',
             muted='#53647B', line='#DDE4ED', field='#7B8BA1', blue='#006BEB',
             onblue='#FFFFFF', active='#E9F2FF', green='#147A52', good='#EAF7F0',
             amber='#8B5B10', warn='#FFF5E0', red='#B42332')
DARK = dict(bg='#101319', surface='#181D25', side='#131820', ink='#EDF2FA',
            muted='#AAB8CB', line='#303A49', field='#71829A', blue='#66AAFF',
            onblue='#10233E', active='#20344E', green='#71D9AA', good='#17372C',
            amber='#F2CE87', warn='#3B301C', red='#FFACB7')
MENUS = [
    ('nota', 'Terima mobil', 'receipt'), ('wo', 'Work order', 'board'),
    ('mek', 'Mekanik', 'person'), ('pos', 'Kasir', 'cart'),
    ('inv', 'Invoice', 'receipt'), ('dash', 'Ringkasan', 'home'),
    ('riwayat', 'Riwayat plat', 'clock'), ('lap', 'Laporan', 'chart'),
    ('master', 'Jasa dan Part', 'box'), ('fit', 'Cocok Part', 'link'),
    ('set', 'Pengaturan', 'settings')]
LABEL = {k: v for k, v, _ in MENUS}
LABEL.update(detail='Detail work order', detail_mek='Pekerjaan mekanik',
             payment='Pembayaran', states='Kondisi antarmuka', menu='Menu', menu_mek='Menu mekanik')
MENU_ROUTES = {k for k, _, _ in MENUS}
JOBS = [
    ('DD 1248 KL', 'Toyota Avanza 1.3', 'AC kurang dingin saat macet', 'Budi Santoso', 'Andi', 'Menunggu', 'Rp 450.000'),
    ('DD 8921 AR', 'Honda Brio Satya', 'Cek kebocoran freon', 'Siti Rahma', 'Rian', 'Dalam pengerjaan', 'Rp 250.000'),
    ('DD 3107 MA', 'Mitsubishi Xpander', 'Cek kebocoran dan isi freon', 'Ahmad Yusuf', 'Dedi', 'Selesai', 'Rp 450.000'),
    ('DD 5672 TS', 'Suzuki Ertiga', 'Kuras evaporator', 'Dewi Lestari', 'Andi', 'Dalam pengerjaan', 'Rp 350.000'),
    ('DD 7340 BN', 'Toyota Innova', 'Paket servis AC rutin', 'Rizal Akbar', 'Santo', 'Menunggu', 'Rp 650.000'),
    ('DD 2086 HP', 'Daihatsu Xenia', 'Isi freon dan cek tekanan', 'Nina Putri', 'Rian', 'Selesai', 'Rp 300.000'),
    ('DD 4429 SC', 'Honda Mobilio', 'Ganti blower', 'Fajar Hadi', 'Dedi', 'Menunggu', 'Rp 850.000'),
    ('DD 9105 RT', 'Toyota Rush', 'Cek kebocoran', 'Arif Wijaya', 'Santo', 'Dibayar', 'Rp 375.000')]
ITEMS = [
    ('Cek kebocoran', 'Jasa', 'Rp 150.000', 'Tanpa stok'),
    ('Isi freon R134a', 'Freon dan oli', 'Rp 250.000', '12 tabung'),
    ('Kuras evaporator', 'Jasa', 'Rp 350.000', 'Tanpa stok'),
    ('Filter kabin Avanza', 'Part', 'Rp 175.000', '8 unit'),
    ('Servis AC rutin', 'Paket', 'Rp 450.000', 'Tanpa stok'),
    ('Oli kompresor', 'Freon dan oli', 'Rp 50.000', '3 botol')]


def uid():
    global NEXT
    v = f'pos:{NEXT}'
    NEXT += 1
    return v


def color(hexcode):
    h = hexcode.lstrip('#')
    return dict(r=int(h[:2], 16)/255, g=int(h[2:4], 16)/255, b=int(h[4:6], 16)/255)


def paint(c):
    return [dict(type='SOLID', color=color(c))] if c else []


def node(parent, kind, name, x=0, y=0, w=100, h=100, fill=None, **props):
    px, py = (parent['_x'], parent['_y']) if parent else (0, 0)
    n = dict(id=uid(), name=name, type=kind,
             absoluteBoundingBox=dict(x=px+x, y=py+y, width=w, height=h),
             fills=paint(fill), **props)
    n['_x'], n['_y'] = px+x, py+y
    if kind in ('FRAME', 'COMPONENT', 'CANVAS'):
        n['children'] = []
    if parent:
        parent['children'].append(n)
    NODES.append(n)
    return n


def rect(p, x, y, w, h, fill, radius=0, stroke=None, name='Surface'):
    return node(p, 'RECTANGLE', name, x, y, w, h, fill, cornerRadius=radius,
                strokes=paint(stroke), strokeWeight=1 if stroke else 0)


def text(p, s, x, y, w, size=14, c=None, weight=400, h=None, align='LEFT'):
    if h is None:
        lines = sum(max(1, math.ceil(len(t)/(max(1, w/(size*.52))))) for t in s.split('\n'))
        h = math.ceil(size*1.45)*lines+2
    return node(p, 'TEXT', s[:65], x, y, w, h, c or p['_t']['ink'],
                characters=s, style=dict(fontFamily='Inter', fontWeight=weight,
                    fontPostScriptName=f'Inter-{ {400:"Regular",500:"Medium",600:"SemiBold",700:"Bold"}[weight]}',
                    fontSize=size, lineHeightPx=math.ceil(size*1.45),
                    letterSpacing=-.4 if size >= 26 else 0,
                    textAlignHorizontal=align, textAlignVertical='TOP', textAutoResize='HEIGHT'))


def group(p, name, x, y, w, h, fill=None, radius=0, stroke=None):
    g = node(p, 'FRAME', name, x, y, w, h, fill, cornerRadius=radius,
             clipsContent=False, strokes=paint(stroke), strokeWeight=1 if stroke else 0)
    g['_t'] = p['_t']
    return g


def bind(n, dest, transition='DISSOLVE'):
    LINKS.append((n, dest, transition))
    return n


def line(p, x, y, w, c=None):
    return rect(p, x, y, w, 1, c or p['_t']['line'], name='Divider')


def circle(p, x, y, diameter, fill=None, stroke=None):
    return node(p, 'ELLIPSE', 'Icon circle', x, y, diameter, diameter, fill,
                strokes=paint(stroke), strokeWeight=1.6 if stroke else 0)


def icon(p, kind, x, y, c=None):
    c = c or p['_t']['muted']
    g = group(p, f'Icon/{kind}', x, y, 20, 20)
    if kind in ('receipt', 'box', 'board', 'home', 'cart'):
        rect(g, 3, 3, 14, 14, None, 2, c)
        if kind == 'board':
            for a, h in [(6, 8), (10, 5), (14, 7)]: rect(g, a, 6, 1.5, h, c)
        elif kind == 'box':
            rect(g, 4, 8, 12, 1.5, c); rect(g, 9, 4, 1.5, 12, c)
        elif kind == 'home':
            for a in (6, 11):
                for b in (6, 11): rect(g, a, b, 3, 3, c, 1)
        else:
            for b in (7, 11): rect(g, 6, b, 8, 1.5, c)
    elif kind == 'person':
        circle(g, 6, 2, 8, None, c); rect(g, 3, 13, 14, 5, None, 3, c)
    elif kind in ('clock', 'settings'):
        circle(g, 2, 2, 16, None, c)
        if kind == 'clock': rect(g, 9, 5, 1.5, 6, c); rect(g, 10, 10, 4, 1.5, c)
        else: circle(g, 7, 7, 6, None, c)
    elif kind == 'chart':
        for a, h in [(3, 5), (9, 11), (15, 15)]: rect(g, a, 18-h, 3, h, c, 1)
    elif kind == 'link':
        rect(g, 2, 4, 9, 7, None, 3, c); rect(g, 9, 9, 9, 7, None, 3, c)
    elif kind == 'search':
        circle(g, 2, 2, 11, None, c); rect(g, 13, 13, 5, 2, c, 1)
    elif kind == 'menu':
        for b in (5, 10, 15): rect(g, 2, b, 16, 1.5, c, 1)
    elif kind == 'rail':
        rect(g, 2, 3, 16, 14, None, 2, c); rect(g, 7, 3, 1.5, 14, c)
    elif kind == 'plus':
        rect(g, 9, 3, 1.5, 14, c); rect(g, 3, 9, 14, 1.5, c)
    elif kind == 'sun':
        circle(g, 6, 6, 8, None, c)
        for a, b, w, h in [(9, 0, 1.5, 3), (9, 17, 1.5, 3), (0, 9, 3, 1.5), (17, 9, 3, 1.5)]: rect(g, a, b, w, h, c)
    return g


def button(p, label, x, y, w, primary=False, dest=None, glyph=None):
    t = p['_t']
    b = group(p, 'Button/'+label, x, y, w, 44, t['blue'] if primary else t['surface'], 8,
              None if primary else t['field'])
    tc = t['onblue'] if primary else t['ink']
    if glyph: icon(b, glyph, 12, 12, tc)
    text(b, label, 36 if glyph else 8, 11, w-(44 if glyph else 16), 14, tc, 500, align='LEFT' if glyph else 'CENTER')
    if dest: bind(b, dest)
    return b


def badge(p, label, x, y, w=None, tone='blue'):
    t = p['_t']
    c, bg = (t['green'], t['good']) if tone == 'green' else (t['amber'], t['warn']) if tone == 'amber' else (t['ink'], t['active'])
    w = w or len(label)*7+20
    rect(p, x, y, w, 27, bg, 6, name='Status/'+label)
    text(p, label, x+10, y+4, w-16, 12, c, 500)


def field(p, label, value, x, y, w, multi=False, placeholder=False):
    t = p['_t']
    text(p, label, x, y, w, 13, t['ink'], 500)
    rect(p, x, y+26, w, 80 if multi else 46, t['surface'], 8, t['field'], 'Input/'+label)
    text(p, value, x+13, y+39, w-26, 14, t['muted'] if placeholder else t['ink'])


def panel(p, title, x, y, w, h, sub=None):
    t = p['_t']
    g = group(p, title, x, y, w, h, t['surface'], 12, t['line'])
    text(g, title, 24, 20, w-48, 18, weight=600)
    if sub: text(g, sub, 24, 49, w-48, 13, t['muted'])
    return g


def table(p, headers, rows, x, y, w, widths=None, rowh=66, links=None):
    t = p['_t']
    widths = widths or [1/len(headers)]*len(headers)
    rect(p, x, y, w, 44, t['side'], 6, name='Table header')
    xx = x
    for hd, fr in zip(headers, widths):
        text(p, hd, xx+16, y+12, w*fr-25, 12, t['muted'], 500)
        xx += w*fr
    for i, row in enumerate(rows):
        yy = y+44+i*rowh
        r = group(p, 'Row/'+str(row[0]), x, yy, w, rowh)
        xx = 0
        for col, fr in zip(row, widths):
            if isinstance(col, tuple):
                lab, tone = col
                badge(r, lab, xx+16, 18, min(w*fr-24, len(lab)*7+20), tone)
            else:
                bits = str(col).split('\n')
                text(r, bits[0], xx+16, 14 if len(bits)>1 else 23, w*fr-24, 13, weight=500 if xx == 0 else 400)
                if len(bits)>1: text(r, bits[1], xx+16, 35, w*fr-24, 12, t['muted'])
            xx += w*fr
        line(r, 0, rowh-1, w)
        if links and links[i % len(links)]: bind(r, links[i % len(links)])


def key(theme, device, page, state='base'):
    return f'{theme}/{device}/{page}/{state}'


def frame(page, theme, device, route, col, row, state='base'):
    mobile = device == 'Mobile'
    w, h = (390, 844) if mobile else (1440, 900)
    f = node(page, 'FRAME', f'{LABEL.get(route,route)} / {theme} / {device} / {state}',
             col*(w+100), row*(h+100), w, h,
             (LIGHT if theme == 'Light' else DARK)['bg'], clipsContent=True)
    f['_t'] = LIGHT if theme == 'Light' else DARK
    f['_theme'], f['_device'], f['_route'], f['_state'] = theme, device, route, state
    FRAMES[key(theme,device,route,state)] = f
    return f


def dest(f, route, state='base', theme=None):
    return key(theme or f['_theme'], f['_device'], route, state)


def sidebar(f, collapsed=False, overlay=False):
    t = f['_t']; w = 72 if collapsed else 240
    height = f['absoluteBoundingBox']['height']
    mechanic = f['_route'] in ('mek', 'detail_mek', 'menu_mek')
    s = group(f, 'Sidebar/'+('collapsed' if collapsed else 'expanded'), 0, 0, w, height, t['side'])
    rect(s, w-1, 0, 1, height, t['line'])
    if not collapsed:
        text(s, 'Dokter AC Mobil', 22, 29, 195, 17, weight=600)
        text(s, 'Ruang kerja bengkel', 22, 58, 195, 12, t['muted'])
        search = group(s, 'Cari kendaraan', 16, 97, 208, 44, t['surface'], 8, t['line'])
        icon(search, 'search', 12, 12); text(search, 'Cari plat nomor', 40, 13, 150, 13, t['muted'])
        bind(search, dest(f, 'mek' if mechanic else 'riwayat'))
    else:
        text(s, 'AC', 20, 32, 40, 20, t['blue'], 700)
        icon(s, 'search', 26, 108)
    mobile=f['_device']=='Mobile'
    yy = 148 if mobile else 165
    for idx, (route, label, glyph) in enumerate([MENUS[2]] if mechanic else MENUS):
        if idx in (0, 5, 8):
            if not collapsed: text(s, ['Operasional','Pemantauan','Data bengkel'][(0,5,8).index(idx)], 24, yy, 190, 12, t['muted'], 500)
            yy += 24 if mobile else 28
        active = route == f['_route']
        n = group(s, 'Nav/'+label, 12, yy, w-24, 44, t['active'] if active else None, 8)
        icon(n, glyph, 14, 12, t['blue'] if active else t['muted'])
        if not collapsed: text(n, label, 44, 12, 162, 14, t['ink'], 600 if active else 400)
        st = 'collapsed' if collapsed and f['_device']=='Desktop' else 'base'
        bind(n, dest(f, route, st))
        yy += 44 if mobile else 47
    if not collapsed:
        line(s, 16, height-95, w-32)
        text(s, 'Pratinjau desain', 24, height-79, 185, 13, weight=500)
        text(s, 'Seluruh data adalah contoh', 24, height-56, 200, 12, t['muted'])
        if not mechanic:
            bind(rect(s,16,height-88,w-32,64,None,name='Buka kondisi pratinjau'),dest(f,'states'))
    return s


def shell(f, subtitle, action=None, collapsed=False):
    t = f['_t']; mobile = f['_device']=='Mobile'
    route = f['_route']; W = 390 if mobile else 1440
    bx = 0 if mobile else (72 if collapsed else 240)
    if not mobile: sidebar(f, collapsed)
    rect(f, bx, 0, W-bx, 72 if not mobile else 64, t['surface'])
    line(f, bx, 71 if not mobile else 63, W-bx)
    if mobile or route in MENU_ROUTES:
        ctrl = group(f, 'Menu' if mobile else 'Ciutkan sidebar', bx+12, 10 if mobile else 14, 64 if mobile else 44, 44)
        if mobile:
            text(ctrl,'Menu',8,12,50,13,t['ink'],500)
        else:
            icon(ctrl, 'rail', 12, 12)
        menu = 'menu_mek' if route in ('mek','detail_mek') else 'menu'
        bind(ctrl, key(f['_theme'],'Mobile',menu) if mobile else dest(f,route,'base' if collapsed else 'collapsed'))
    text(f, 'Dokter AC Mobil' if mobile else 'Bengkel   /   '+LABEL.get(route,'Work order'), bx+84 if mobile else bx+60, 23 if mobile else 26, 185 if mobile else 520, 13, t['muted'], 500)
    theme = group(f, 'Ganti tema', W-60, 10 if mobile else 14, 44, 44, t['side'], 8)
    icon(theme, 'sun', 12, 12)
    bind(theme, dest(f,route,f['_state'], 'Dark' if f['_theme']=='Light' else 'Light'))
    if not mobile:
        text(f, 'Data contoh', W-191, 27, 120, 12, t['muted'], 500)
    else:
        text(f, 'Pratinjau statis. Seluruh isi adalah contoh.', 20, 819, 350, 11, t['muted'])
    x, cw = (20,350) if mobile else (bx+32,W-bx-64)
    title = LABEL.get(route, 'Detail work order')
    text(f, title, x, 86 if mobile else 101, cw, 26 if mobile else 30, weight=600)
    text(f, subtitle, x, 129 if mobile else 148, cw, 13 if mobile else 14, t['muted'])
    if action and not mobile:
        label, to = action
        button(f, label, W-232, 105, 200, True, to, 'plus')
    return x,cw,178 if mobile else 205


def vehicle_card(p, job, x, y, w, target=None, money=False):
    t = p['_t']; plate, car, issue, customer, mechanic, status, total = job
    g = group(p, 'Vehicle/'+plate, x,y,w,156,t['surface'],10,t['line'])
    text(g,plate,16,15,w-32,16,weight=600)
    text(g,car,16,42,w-32,12,t['muted'])
    text(g,issue,16,70,w-32,13,weight=500,h=40)
    line(g,16,118,w-32)
    text(g,mechanic+'  ·  '+customer.split()[0]+('  (statis)' if target is None else ''),16,130,w-32,12,t['muted'])
    if target: bind(g,target)
    return g


def draw_wo(f,x,w,y):
    t=f['_t']; m=f['_device']=='Mobile'
    if m:
        button(f,'Terima mobil',x,y,w,True,dest(f,'nota'),'plus')
        y+=62
        text(f,'Pekerjaan aktif',x,y,w,16,weight=600)
        badge(f,'7 kendaraan contoh',x+192,y-2,158)
        for i,j in enumerate(JOBS[:3]):
            yy=y+40+i*177
            vehicle_card(f,j,x,yy,w,dest(f,'detail') if j==JOBS[0] else None)
            badge(f,j[5],x+170,yy+14,164,'green' if j[5]=='Selesai' else 'blue' if j[5].startswith('Dalam') else 'amber')
    else:
        button(f,'Papan',x,y,90,False,dest(f,'wo'))
        button(f,'Lihat detail',x+102,y,132,False,dest(f,'detail'))
        text(f,'8 work order contoh',x+254,y+14,260,13,t['muted'])
        button(f,'Cari kendaraan',x+w-218,y,218,False,dest(f,'riwayat'),'search')
        stages=['Menunggu','Dalam pengerjaan','Selesai','Dibayar']; gap=16; colw=(w-3*gap)/4
        for k,stage in enumerate(stages):
            col=group(f, 'Column/'+stage,x+k*(colw+gap),y+68,colw,566,t['side'],10)
            text(col,stage,14,15,colw-45,14,weight=600)
            js=[j for j in JOBS if j[5]==stage]
            text(col,str(len(js)),colw-34,16,24,13,t['muted'],500)
            for i,j in enumerate(js): vehicle_card(col,j,10,54+i*166,colw-20,dest(f,'detail') if j==JOBS[0] else None)
        text(f,'Buka DD 1248 KL untuk detail contoh. Kartu lainnya adalah contoh statis.',x,y+658,w,13,t['muted'])


def draw_nota(f,x,w,y):
    t=f['_t']; m=f['_device']=='Mobile'
    if m:
        badge(f,'Draf contoh',x,y,112,'green')
        vals=[('Plat nomor','DD 1248 KL'),('Nama pelanggan','Budi Santoso'),('Keluhan','AC kurang dingin saat macet'),('Diagnosa awal','Periksa tekanan dan kebocoran')]
        for i,(a,b) in enumerate(vals): field(f,a,b,x,y+48+i*89,w)
        button(f,'Simpan nota servis (demo)',x,y+420,w,True,dest(f,'wo'))
        text(f,'Contoh kendaraan ditemukan',x,y+492,w,16,weight=600)
        text(f,'Toyota Avanza 1.3  ·  Budi Santoso\nRiwayat servis tersedia untuk plat ini.',x,y+526,w,14,t['muted'])
        button(f,'Lihat riwayat kendaraan',x,y+592,w,False,dest(f,'riwayat'))
    else:
        lw=round(w*.62); rw=w-lw-24
        g=panel(f,'Nota servis baru',x,y,lw,414,'Mulai dari plat nomor, lalu catat keluhan.')
        fw=(lw-64)/2
        field(g,'Plat nomor','DD 1248 KL',24,92,fw)
        field(g,'Nama pelanggan','Budi Santoso',40+fw,92,fw)
        field(g,'Keluhan','AC kurang dingin saat macet',24,190,lw-48)
        field(g,'Diagnosa awal','Periksa tekanan freon dan kebocoran',24,284,lw-48)
        r=panel(f,'Kendaraan ditemukan',x+lw+24,y,rw,414)
        badge(r,'Pelanggan kembali',24,66,155,'green')
        text(r,'DD 1248 KL',24,116,rw-48,25,weight=600)
        text(r,'Toyota Avanza 1.3\nBudi Santoso\n85.200 km',24,160,rw-48,14,t['muted'])
        line(r,24,250,rw-48)
        text(r,'Servis terakhir',24,268,rw-48,13,t['muted'])
        text(r,'12 Agustus 2026\nServis AC rutin',24,294,rw-48,14,weight=500)
        button(r,'Lihat riwayat',24,352,rw-48,False,dest(f,'riwayat'))
        button(f,'Simpan nota (demo)',x,y+438,220,True,dest(f,'wo'))
        text(f,'Draf contoh. Belum tersimpan sebagai data bengkel.',x+242,y+453,w-250,13,t['muted'])
        text(f,'Penerimaan terakhir',x,y+487,w,18,weight=600)
        table(f,['Nota servis','Kendaraan','Pelanggan','Keluhan'],[
            ['NS-0268\n30 Oktober 2026',JOBS[1][0]+'\n'+JOBS[1][1],JOBS[1][3],JOBS[1][2]],
            ['NS-0267\n30 Oktober 2026',JOBS[2][0]+'\n'+JOBS[2][1],JOBS[2][3],JOBS[2][2]]],x,y+526,w,[.18,.25,.22,.35],rowh=60)


def draw_pos(f,x,w,y):
    t=f['_t']; m=f['_device']=='Mobile'
    if m:
        text(f,'DD 3107 MA',x,y,w,20,weight=600)
        text(f,'Ahmad Yusuf  ·  Pekerjaan selesai',x,y+34,w,13,t['muted'])
        line(f,x,y+74,w)
        text(f,'Rincian tagihan contoh',x,y+97,w,18,weight=600)
        rows=[('Cek kebocoran','Rp 150.000'),('Isi freon R134a','Rp 250.000'),('Oli kompresor','Rp 50.000')]
        for i,(a,b) in enumerate(rows):
            yy=y+147+i*75
            text(f,a,x,yy,220,14,weight=500);text(f,'1 item',x,yy+25,200,12,t['muted']);text(f,b,x+224,yy,126,14,align='RIGHT');line(f,x,yy+59,w)
        button(f,'Tambah jasa atau part',x,y+388,w,False,dest(f,'master'),'plus')
        text(f,'Total contoh',x,y+463,160,14,t['muted'])
        text(f,'Rp 450.000',x+140,y+454,210,28,weight=600,align='RIGHT')
        button(f,'Lanjut ke pembayaran',x,y+520,w,True,dest(f,'payment'))
        text(f,'Simulasi. Tidak memproses pembayaran.',x,y+581,w,12,t['muted'])
    else:
        rw=358;lw=w-rw-24
        for i,(lab,to) in enumerate([('Semua','pos'),('Jasa','master'),('Part','master')]):button(f,lab,x+i*108,y,96,False,dest(f,to))
        gap=16; cardw=(lw-gap)/2
        for i,it in enumerate(ITEMS):
            xx=x+(i%2)*(cardw+gap);yy=y+70+(i//2)*151
            g=group(f,'Item/'+it[0],xx,yy,cardw,135,t['surface'],10,t['line'])
            text(g,it[1],18,14,cardw-36,12,t['muted']);text(g,it[0],18,41,cardw-36,16,weight=500)
            text(g,it[2],18,91,cardw-64,16,weight=600)
            bind(g,dest(f,'states','selection'))
        r=panel(f,'Tagihan servis',x+lw+24,y,rw,618)
        badge(r,'Selesai',24,63,82,'green')
        text(r,'DD 3107 MA',24,109,rw-48,22,weight=600)
        text(r,'Ahmad Yusuf  ·  Mitsubishi Xpander',24,147,rw-48,13,t['muted'])
        line(r,24,188,rw-48)
        for i,(a,b) in enumerate([('Cek kebocoran','Rp 150.000'),('Isi freon R134a','Rp 250.000'),('Oli kompresor','Rp 50.000')]):
            yy=213+i*68
            text(r,a,24,yy,rw-48,14,weight=500);text(r,'1 × '+b,24,yy+25,rw-48,13,t['muted'])
        line(r,24,425,rw-48)
        text(r,'Total contoh',24,450,rw-48,13,t['muted']);text(r,'Rp 450.000',24,477,rw-48,30,weight=600)
        button(r,'Lanjut ke pembayaran',24,546,rw-48,True,dest(f,'payment'))
        text(f,'Harga contoh untuk evaluasi desain, bukan daftar harga bengkel.',x,y+568,lw,13,t['muted'])


def draw_inv(f,x,w,y):
    t=f['_t'];m=f['_device']=='Mobile'
    if m:
        button(f,'Buka kasir',x,y,w,True,dest(f,'pos'))
        for i,j in enumerate([JOBS[2],JOBS[3],JOBS[5]]):
            yy=y+74+i*170
            g=group(f,'Invoice contoh',x,yy,w,148,t['surface'],10,t['line'])
            text(g,'INV-026'+str(8-i),16,16,200,14,weight=600);badge(g,'Lunas' if i!=1 else 'Tempo',250,14,82,'green' if i!=1 else 'amber')
            text(g,j[0]+'  ·  '+j[3],16,58,w-32,13,t['muted']);text(g,j[6],16,99,w-32,22,weight=600)
        text(f,'Daftar invoice statis. Buka kasir untuk simulasi pembayaran.',x,y+582,w,13,t['muted'])
    else:
        metrics(f,x,y,w,[('Lunas contoh','Rp 1.125.000'),('Tempo contoh','Rp 350.000'),('Nota contoh','4 invoice')])
        text(f,'Daftar invoice',x,y+126,w,18,weight=600)
        table(f,['Invoice','Pelanggan / kendaraan','Total contoh','Metode','Status'],[
            ['INV-0268\n30 Oktober 2026','Ahmad Yusuf\nDD 3107 MA','Rp 450.000','Tunai',('Lunas','green')],
            ['INV-0267\n30 Oktober 2026','Dewi Lestari\nDD 5672 TS','Rp 350.000','Tempo',('Tempo','amber')],
            ['INV-0266\n29 Oktober 2026','Nina Putri\nDD 2086 HP','Rp 300.000','QRIS',('Lunas','green')],
            ['INV-0265\n29 Oktober 2026','Arif Wijaya\nDD 9105 RT','Rp 375.000','Transfer',('Lunas','green')]],x,y+176,w,[.18,.31,.19,.14,.18],rowh=79)
        button(f,'Buka kasir',x,y+550,180,True,dest(f,'pos'))
        text(f,'Daftar invoice statis. Pembayaran dicontohkan melalui kasir.',x+204,y+563,w-204,13,t['muted'])


def draw_mek(f,x,w,y):
    t=f['_t'];m=f['_device']=='Mobile'
    badge(f,'Pratinjau mekanik · tanpa harga',x,y,270,'green')
    if m:
        text(f,'Tugas Andi',x,y+55,w,18,weight=600)
        for i,j in enumerate([JOBS[0],JOBS[3]]):vehicle_card(f,j,x,y+98+i*170,w,dest(f,'detail_mek') if i==0 else None)
    else:
        text(f,'Tugas mekanik',x,y+75,w,20,weight=600)
        text(f,'Contoh penugasan Andi. Buka pekerjaan untuk melihat keluhan dan daftar tindakan.',x,y+113,w,14,t['muted'])
        gap=20;cw=(w-gap)/2
        for i,j in enumerate([JOBS[0],JOBS[3]]):
            xx=x+i*(cw+gap)
            vehicle_card(f,j,xx,y+165,cw,dest(f,'detail_mek') if i==0 else None)
            if i==0:button(f,'Buka pekerjaan',xx,y+337,cw,False,dest(f,'detail_mek'))
        text(f,'Langkah pekerjaan',x,y+442,w,18,weight=600)
        cw=(w-2*gap)/3
        for i,(a,b) in enumerate([('Periksa keluhan','Baca nota servis dan hasil diagnosa awal.'),('Kerjakan jasa dan part','Catat hasil pemeriksaan untuk supervisor.'),('Tandai selesai','Supervisor atau kasir melanjutkan penagihan.')]):
            xx=x+i*(cw+gap);text(f,a,xx,y+493,cw,15,weight=600);text(f,b,xx,y+527,cw-15,14,t['muted'])


def metrics(f,x,y,w,values):
    t=f['_t'];cw=w/len(values)
    for i,(label,value) in enumerate(values):
        xx=x+i*cw
        text(f,label,xx+2,y+2,cw-24,13,t['muted'])
        text(f,value,xx+2,y+32,cw-24,26,weight=600)
        if i:rect(f,xx-20,y,1,80,t['line'])
    line(f,x,y+95,w)


def chart(p,x,y,w,h):
    t=p['_t'];data=[110,160,125,185,145,230,176]
    for i in range(3):line(p,x,y+i*(h-40)/2,w)
    cw=w/7
    for i,v in enumerate(data):
        bh=(h-45)*v/240
        rect(p,x+i*cw+cw*.28,y+h-42-bh,cw*.42,bh,t['blue'],4,name='Omzet contoh')
        text(p,['Sab','Min','Sen','Sel','Rab','Kam','Jum'][i],x+i*cw,y+h-25,cw,12,t['muted'],align='CENTER')


def draw_dash(f,x,w,y):
    t=f['_t'];m=f['_device']=='Mobile'
    if m:
        text(f,'Jumat, 30 Oktober 2026',x,y,w,13,t['muted'])
        metrics(f,x,y+42,w,[('WO aktif contoh','7'),('Selesai contoh','2')])
        button(f,'Terima mobil',x,y+162,w,True,dest(f,'nota'),'plus')
        text(f,'Perlu ditindaklanjuti',x,y+237,w,18,weight=600)
        for i,(a,b,to) in enumerate([('2 pekerjaan selesai','Buka kasir untuk menagih.','pos'),('3 kendaraan menunggu','Lihat antrean work order.','wo'),('1 invoice tempo contoh','Tinjau daftar invoice.','inv')]):
            yy=y+286+i*93;text(f,a,x,yy,w,15,weight=600);text(f,b,x,yy+29,w,13,t['muted']);bind(rect(f,x,yy,w,72,None,name='Open '+a),dest(f,to));line(f,x,yy+78,w)
    else:
        metrics(f,x,y,w,[('WO aktif contoh','7 kendaraan'),('Siap ditagih contoh','2 kendaraan'),('Tempo contoh','Rp 350.000'),('Lunas contoh','Rp 1.125.000')])
        lw=w*.62;rw=w-lw-24
        a=panel(f,'Omzet 7 hari (contoh)',x,y+130,lw,313,'Grafik ilustrasi untuk menilai keterbacaan laporan.')
        chart(a,24,96,lw-48,190)
        b=panel(f,'Perlu ditindaklanjuti',x+lw+24,y+130,rw,313)
        for i,(a1,b1,to) in enumerate([('2 pekerjaan selesai','Lanjutkan pembayaran','pos'),('3 kendaraan menunggu','Buka work order','wo'),('1 invoice tempo','Tinjau invoice','inv')]):
            yy=68+i*77;text(b,a1,24,yy,rw-48,14,weight=600);z=text(b,b1,24,yy+26,rw-48,13,t['blue']);bind(z,dest(f,to))
        text(f,'Aktivitas servis',x,y+464,w,18,weight=600)
        table(f,['Kendaraan','Pekerjaan','Mekanik','Status'],[[j[0]+'\n'+j[1],j[2],j[4],(j[5],'green' if j[5]=='Selesai' else 'blue')] for j in JOBS[:2]],x,y+506,w,[.25,.38,.15,.22],links=[dest(f,'detail'),None])


def draw_history(f,x,w,y):
    t=f['_t'];m=f['_device']=='Mobile'
    if m:
        field(f,'Cari riwayat plat','DD 1248 KL',x,y,w)
        text(f,'Toyota Avanza 1.3',x,y+109,w,22,weight=600)
        text(f,'Budi Santoso  ·  Data contoh',x,y+148,w,13,t['muted'])
        sy=y+203;tx=x;tw=w
    else:
        left=310;r=panel(f,'Kendaraan',x,y,left,423)
        field(r,'Plat nomor','DD 1248 KL',24,72,left-48)
        text(r,'Toyota Avanza 1.3',24,184,left-48,20,weight=600)
        text(r,'Budi Santoso\n85.200 km\nPelanggan contoh',24,226,left-48,14,t['muted'])
        button(r,'Terima mobil ini',24,351,left-48,True,dest(f,'nota'))
        tx=x+left+36;tw=w-left-36;sy=y
    text(f,'Riwayat servis',tx,sy,tw,18,weight=600)
    for i,(date,head,body) in enumerate([('30 Oktober 2026','Pemeriksaan AC','AC kurang dingin saat macet. Pemeriksaan tekanan dan kebocoran.'),('12 Agustus 2026','Servis AC rutin','Pembersihan saluran dan pemeriksaan kondisi filter kabin.'),('18 April 2026','Isi freon','Pemeriksaan tekanan freon dan sambungan pipa AC.')]):
        yy=sy+60+i*(129 if m else 156)
        circle(f,tx,yy+5,10,t['blue'] if i==0 else t['line'])
        text(f,date,tx+25,yy,tw-25,12,t['muted']);text(f,head,tx+25,yy+28,tw-25,16,weight=600)
        text(f,body,tx+25,yy+60,tw-25,13,t['muted'],h=54)


def draw_reports(f,x,w,y):
    t=f['_t'];m=f['_device']=='Mobile'
    if m:
        field(f,'Periode laporan','24 – 30 Oktober 2026',x,y,w)
        metrics(f,x,y+107,w,[('Omzet contoh','Rp 3.550.000')])
        text(f,'Omzet harian contoh',x,y+239,w,18,weight=600)
        chart(f,x,y+290,w,170)
        text(f,'Rincian contoh',x,y+493,w,18,weight=600)
        text(f,'30 Oktober 2026',x,y+540,190,14);text(f,'Rp 450.000',x+190,y+540,160,14,weight=600,align='RIGHT')
        button(f,'Tinjau invoice',x,y+589,w,False,dest(f,'inv'))
    else:
        text(f,'24 – 30 Oktober 2026',x,y+14,360,14,weight=500)
        button(f,'Lihat invoice',x+w-190,y,190,False,dest(f,'inv'))
        metrics(f,x,y+79,w,[('Omzet contoh','Rp 3.550.000'),('Invoice contoh','12'),('Rata-rata contoh','Rp 295.833')])
        p=panel(f,'Omzet harian contoh',x,y+213,w,278)
        chart(p,28,71,w-56,178)
        table(f,['Tanggal','Invoice contoh','Metode dominan','Omzet contoh'],[
            ['30 Oktober 2026','3','Tunai','Rp 450.000'],['29 Oktober 2026','2','QRIS','Rp 675.000']],x,y+505,w,[.3,.2,.25,.25])


def draw_master(f,x,w,y):
    t=f['_t'];m=f['_device']=='Mobile'
    if m:
        button(f,'Tambah jasa atau part',x,y,w,True,dest(f,'master','empty'),'plus')
        for i,it in enumerate(ITEMS[:4]):
            yy=y+76+i*132
            text(f,it[0],x,yy,w,16,weight=600);text(f,it[1]+'  ·  '+it[3],x,yy+33,w,13,t['muted']);text(f,it[2]+' (contoh)',x,yy+65,w,14,t['blue'],500);line(f,x,yy+108,w)
    else:
        table(f,['Nama','Golongan','Harga contoh','Stok contoh'],[[a,b,c,d] for a,b,c,d in ITEMS],x,y,w,[.36,.24,.21,.19],rowh=72)
        button(f,'Tambah jasa / part',x,y+518,228,True,dest(f,'master','empty'),'plus')
        button(f,'Lihat kecocokan part',x+244,y+518,220,False,dest(f,'fit'))


def draw_fit(f,x,w,y):
    t=f['_t'];m=f['_device']=='Mobile'
    field(f,'Cari sparepart','Filter kabin',x,y,w if m else w*.48)
    field(f,'Tipe mobil','Avanza',x if m else x+w*.52,y+96 if m else y,w if m else w*.48)
    if m:
        text(f,'Kecocokan contoh',x,y+214,w,18,weight=600)
        for i,(a,b) in enumerate([('Toyota Avanza 1.3','2012–2021  ·  1.300 cc'),('Daihatsu Xenia 1.3','2012–2021  ·  1.300 cc')]):
            yy=y+267+i*147;text(f,a,x,yy,w,17,weight=600);text(f,b,x,yy+36,w,14,t['muted']);badge(f,'Filter kabin',x,yy+73,121,'green')
        text(f,'Cocokkan kembali dengan katalog pemasok sebelum digunakan.',x,y+585,w,13,t['muted'])
    else:
        table(f,['Sparepart','Tipe mobil','Kapasitas','Tahun contoh'],[
            ['Filter kabin\nFC-AVZ-01','Toyota Avanza','1.300 cc','2012–2021'],
            ['Filter kabin\nFC-AVZ-01','Daihatsu Xenia','1.300 cc','2012–2021']],x,y+125,w,[.3,.3,.18,.22],rowh=90)
        text(f,'Data kecocokan hanya contoh. Verifikasi dengan katalog pemasok sebelum digunakan.',x,y+385,w,14,t['muted'])


def draw_settings(f,x,w,y):
    t=f['_t'];m=f['_device']=='Mobile'
    fw=w if m else 620
    vals=[('Nama bengkel','Dokter AC Mobil (sementara)'),('Alamat','[Alamat bengkel]'),('Telepon','[Nomor bengkel]'),('Nama kasir','[Nama petugas]')]
    if not m:
        text(f,'Profil bengkel',x,y,w,18,weight=600);y+=53
    for i,(a,b) in enumerate(vals):field(f,a,b,x,y+i*87,fw)
    button(f,'Simpan perubahan (demo)',x,y+371,fw if m else 260,True,dest(f,'set','success'))
    if m:
        text(f,'Tampilan',x,y+454,w,18,weight=600)
        button(f,'Ganti light / dark',x,y+495,w,False,dest(f,'set',theme='Dark' if f['_theme']=='Light' else 'Light'),'sun')
        text(f,'Nama dan identitas bengkel masih sementara.',x,y+563,w,13,t['muted'])
    else:
        r=panel(f,'Tampilan dan data',x+fw+40,y-53,w-fw-40,415)
        text(r,'Tema',24,73,w-fw-88,14,weight=500)
        button(r,'Ganti light / dark',24,113,w-fw-88,False,dest(f,'set',theme='Dark' if f['_theme']=='Light' else 'Light'),'sun')
        line(r,24,190,w-fw-88)
        text(r,'Data prototype',24,216,w-fw-88,16,weight=600)
        text(r,'Semua isi adalah contoh. Tidak membaca atau mengganti data bengkel.',24,254,w-fw-88,14,t['muted'])
        text(r,'Cadangan dan pemulihan dirancang sebagai state konfirmasi.',24,332,w-fw-88,13,t['muted'])


DRAW = dict(nota=draw_nota,wo=draw_wo,mek=draw_mek,pos=draw_pos,inv=draw_inv,
            dash=draw_dash,riwayat=draw_history,lap=draw_reports,master=draw_master,fit=draw_fit,set=draw_settings)
SUBS = dict(nota='Catat kendaraan dan keluhan, lalu lanjutkan pekerjaan.',wo='Pantau kendaraan dari menunggu sampai dibayar.',
            mek='Keluhan dan pekerjaan yang perlu diselesaikan.',pos='Tinjau jasa dan part sebelum menagih.',inv='Tinjau tagihan lunas dan pembayaran tempo.',
            dash='Pekerjaan dan transaksi yang perlu perhatian.',riwayat='Telusuri catatan servis berdasarkan plat nomor.',lap='Tinjau transaksi dan omzet dalam satu periode.',
            master='Kelola daftar jasa, harga, dan suku cadang.',fit='Temukan suku cadang untuk tipe kendaraan.',set='Identitas bengkel dan pilihan tampilan.')


def draw_detail(f):
    t=f['_t'];m=f['_device']=='Mobile'
    mechanic=f['_route']=='detail_mek'
    back='mek' if mechanic else 'wo'
    started=f['_state']=='started'
    completed=f['_state']=='completed'
    x,w,y=shell(f,'Catatan pekerjaan dan hasil pemeriksaan.')
    text(f,'DD 1248 KL',x,y,w,27,weight=600)
    text(f,'Toyota Avanza 1.3  ·  Budi Santoso',x,y+43,w,14,t['muted'])
    badge(f,'Selesai' if completed else 'Dalam pengerjaan' if started else 'Menunggu',x,y+83,170 if started else 111,'green' if completed else 'blue' if started else 'amber')
    next_label='Kembali ke tugas' if completed else 'Tandai selesai (demo)' if started else 'Mulai pekerjaan (demo)'
    next_target=dest(f,'mek') if completed else dest(f,'detail_mek','completed' if started else 'started')
    if m:
        text(f,'Keluhan',x,y+145,w,16,weight=600);text(f,JOBS[0][2],x,y+178,w,14,t['muted'])
        text(f,'Pemeriksaan awal',x,y+230,w,16,weight=600);text(f,'Periksa tekanan freon dan kebocoran pada sambungan pipa.',x,y+264,w,14,t['muted'])
        text(f,'Daftar pekerjaan',x,y+344,w,16,weight=600)
        text(f,'Cek kebocoran\nIsi freon R134a\nOli kompresor',x,y+380,w,15,h=100)
        button(f,next_label if mechanic else 'Lihat tugas mekanik',x,y+506,w,True,next_target if mechanic else dest(f,'mek'))
        button(f,'Kembali ke tugas' if mechanic else 'Kembali ke work order',x,y+565,w,False,dest(f,back))
    else:
        g=panel(f,'Keluhan dan pemeriksaan',x,y+148,w*.58,270)
        text(g,'Keluhan pelanggan',24,69,w*.58-48,13,t['muted']);text(g,JOBS[0][2],24,100,w*.58-48,17,weight=500)
        text(g,'Diagnosa awal',24,158,w*.58-48,13,t['muted']);text(g,'Periksa tekanan freon dan sambungan pipa AC.',24,190,w*.58-48,15)
        r=panel(f,'Penugasan',x+w*.58+24,y+148,w*.42-24,270)
        field(r,'Mekanik','Andi',24,69,w*.42-72)
        field(r,'Perkiraan selesai','30 Oktober 2026, 15.00',24,163,w*.42-72)
        text(f,'Daftar pekerjaan',x,y+461,w,18,weight=600)
        table(f,['Pekerjaan','Jenis','Jumlah'],[['Cek kebocoran','Jasa','1'],['Isi freon R134a','Freon dan oli','1']],x,y+505,w,[.6,.25,.15])
        button(f,'Kembali ke tugas' if mechanic else 'Kembali ke work order',x+w-235,105,235,False,dest(f,back))
        if mechanic:button(f,next_label,x+w-260,y+83,260,True,next_target)


def draw_payment(f):
    t=f['_t'];m=f['_device']=='Mobile'
    x,w,y=shell(f,'Simulasi pembayaran. Tidak memproses uang.')
    draw_pos(f,x,w,y)
    scrim=rect(f,0,0,390 if m else 1440,844 if m else 900,'#10233E',name='Payment scrim');scrim['opacity']=.62
    pw=358 if m else 480;px=16 if m else 600;py=111 if m else 126
    d=group(f,'Dialog/Pembayaran',px,py,pw,666,t['surface'],16,t['line'])
    text(d,'Pembayaran',24,23,pw-48,24,weight=600)
    text(d,'DD 3107 MA  ·  Data contoh',24,68,pw-48,13,t['muted'])
    text(d,'Total tagihan contoh',24,118,pw-48,13,t['muted'])
    text(d,'Rp 450.000',24,149,pw-48,34,weight=600)
    line(d,24,213,pw-48)
    field(d,'Metode pembayaran','Tunai',24,240,pw-48)
    field(d,'Uang diterima (contoh)','Rp 500.000',24,333,pw-48)
    text(d,'Kembalian contoh',24,435,190,14,t['muted']);text(d,'Rp 50.000',pw-172,432,148,19,weight=600,align='RIGHT')
    text(d,'Simulasi desain. Invoice resmi wajib online.',24,484,pw-48,13,t['muted'])
    button(d,'Konfirmasi (demo)',24,536,pw-48,True,dest(f,'inv'))
    button(d,'Kembali ke kasir',24,594,pw-48,False,dest(f,'pos'))


def draw_states(f):
    t=f['_t'];m=f['_device']=='Mobile';x,w,y=shell(f,'Variasi kondisi antarmuka untuk tahap browser.')
    if f['_state']!='base':
        title,body,action,to=STATES[f['_state']]
        pw=w if m else min(w,680)
        p=panel(f,title,x,y,pw,420 if m else 360)
        text(p,body,24,81,pw-48,15,t['muted'])
        if f['_state']=='validation':
            field(p,'Plat nomor','[Belum diisi]',24,159,pw-48)
            text(p,'Isi plat nomor sebelum melanjutkan.',24,239,pw-48,13,t['red'])
        elif f['_state']=='confirm':
            badge(p,'Konfirmasi diperlukan',24,175,210,'amber')
        elif f['_state']=='offline':
            badge(p,'Belum tersinkron',24,175,170,'amber')
        elif f['_state']=='conflict':
            text(p,'Versi perangkat ini: 3\nVersi terbaru: 4 (contoh)',24,175,pw-48,14)
        button(p,action,24,285,pw-48,True,dest(f,to))
        button(f,'Kembali ke daftar kondisi',x,y+(444 if m else 384),min(w,300),False,dest(f,'states'))
        return
    for i,(state,(title,_,_,_)) in enumerate(STATES.items()):
        xx=x if m else x+(i%2)*(w/2+8)
        yy=y+i*66 if m else y+(i//2)*104
        ww=w if m else w/2-8
        button(f,title,xx,yy,ww,False,dest(f,'states',state))


STATES = {
    'empty':('Belum ada pekerjaan','Terima mobil untuk membuat nota servis pertama.','Terima mobil','nota'),
    'loading':('Sedang memuat pekerjaan…','Contoh kondisi memuat. Draf lokal tetap tersedia.','Lihat hasil contoh','wo'),
    'error':('Pekerjaan gagal dimuat','Periksa koneksi lalu coba lagi. Draf lokal tidak dihapus.','Coba lagi (demo)','wo'),
    'offline':('Draf tersimpan di perangkat','Tidak ada koneksi. Draf dapat dilanjutkan. Pembayaran dan invoice resmi memerlukan koneksi.','Lanjutkan draf','nota'),
    'validation':('Periksa plat nomor','Nota servis belum dapat dilanjutkan karena plat nomor belum diisi.','Perbaiki nota servis','nota'),
    'confirm':('Batalkan penghapusan?','Contoh konfirmasi hapus work order. Pratinjau ini tidak menghapus data.','Batalkan, simpan work order','wo'),
    'conflict':('Ada perubahan di perangkat lain','Draf Anda tetap tersedia. Tinjau versi terbaru sebelum menerapkan perubahan.','Tinjau work order terbaru','detail'),
    'selection':('Pilihan item (simulasi)','Item pada katalog adalah contoh statis. Evaluasi rincian tagihan dari halaman kasir.','Kembali ke kasir','pos'),
    'saving':('Menyimpan draf…','Contoh proses penyimpanan. Tunggu sampai status Tersimpan muncul.','Lihat draf tersimpan (demo)','nota'),
}


def clean(value):
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if not k.startswith('_')}
    if isinstance(value,list):return [clean(v) for v in value]
    return value


def main():
    doc=dict(id='0:0',name='Document',type='DOCUMENT',children=[])
    for theme in ('Light','Dark'):
        for device in ('Desktop','Mobile'):
            p=dict(id=uid(),name=f'{device} · {theme}',type='CANVAS',children=[],_x=0,_y=0)
            doc['children'].append(p)
            for i,(route,_,_) in enumerate(MENUS):
                f=frame(p,theme,device,route,i%3,i//3)
                action=('Terima mobil',dest(f,'nota')) if route=='wo' else None
                x,w,y=shell(f,SUBS[route],action)
                DRAW[route](f,x,w,y)
            for i,route in enumerate(('detail','payment','states','detail_mek')):
                f=frame(p,theme,device,route,i,4)
                if route in ('detail','detail_mek'):draw_detail(f)
                elif route=='payment':draw_payment(f)
                else:draw_states(f)
            if device=='Desktop':
                for i,(route,_,_) in enumerate(MENUS):
                    f=frame(p,theme,device,route,i%3,5+i//3,'collapsed')
                    x,w,y=shell(f,SUBS[route],collapsed=True)
                    DRAW[route](f,x,w,y)
            else:
                for i,route in enumerate(('menu','menu_mek')):
                    f=frame(p,theme,device,route,i*3,5)
                    sidebar(f)
                    rect(f,240,0,150,844,f['_t']['bg'])
                    button(f,'Tutup',264,20,104,False,dest(f,'mek' if route=='menu_mek' else 'wo'))
                    text(f,'Pilih menu',264,100,100,16,weight=600)
            for route,state in [('master','empty'),('set','success')]:
                f=frame(p,theme,device,route,1 if route=='master' else 2,9 if device=='Desktop' else 5,state)
                x,w,y=shell(f,'State simulasi untuk prototype.')
                if route=='master':
                    field(f,'Nama jasa atau part','[Nama jasa atau part]',x,y,w if device=='Mobile' else 620)
                    field(f,'Harga contoh','[Harga yang ditetapkan pemilik]',x,y+100,w if device=='Mobile' else 620)
                    button(f,'Kembali ke daftar',x,y+222,min(w,260),False,dest(f,'master'))
                else:
                    badge(f,'Perubahan disimpan (simulasi)',x,y,270,'green')
                    text(f,'Identitas contoh tetap tersimpan di frame desain ini.',x,y+62,w,16)
                    button(f,'Kembali ke pengaturan',x,y+139,min(w,280),True,dest(f,'set'))
            for i,state in enumerate(('started','completed')):
                f=frame(p,theme,device,'detail_mek',3+i,10,state)
                draw_detail(f)
            for i,state in enumerate(STATES):
                f=frame(p,theme,device,'states',i%3,11+i//3,state)
                draw_states(f)
    for n,to,transition in LINKS:
        if to not in FRAMES:raise ValueError(f'Missing target {to}')
        target=FRAMES[to]['id']
        n['transitionNodeID']=target
        n['transitionDuration']=180
        n['interactions']=[dict(trigger=dict(type='ON_CLICK'),actions=[dict(type='NODE',destinationId=target,navigation='NAVIGATE',preserveScrollPosition=False,transition=dict(type=transition,duration=.18,easing=dict(type='EASE_OUT')))])]
    for p in doc['children']:
        theme='Dark' if 'Dark' in p['name'] else 'Light';device='Mobile' if 'Mobile' in p['name'] else 'Desktop'
        p['flowStartingPoints']=[dict(nodeId=FRAMES[key(theme,device,'wo')]['id'],name=f'POS {device} {theme}')]
        p['flowStartingPoints'].extend([
            dict(nodeId=FRAMES[key(theme,device,'mek')]['id'],name=f'Mekanik {device} {theme}'),
            dict(nodeId=FRAMES[key(theme,device,'states')]['id'],name=f'Kondisi {device} {theme}')])
    manifest=dict(frames={k:v['id'] for k,v in FRAMES.items()},nodes=len(NODES),links=len(LINKS),
                  base_frames=sum(k.endswith('/base') and k.split('/')[2] in MENU_ROUTES for k in FRAMES),
                  note='All data, people, plates and prices are explicitly illustrative.')
    assert manifest['base_frames']==44
    assert len({v['id'] for v in FRAMES.values()})==len(FRAMES)
    validate()
    output=dict(name='Dokter AC Mobil · Prototype UI-01',document=clean(doc))
    (HERE/'pos-ui.figcraft-source.json').write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(frames=len(FRAMES),base_frames=44,nodes=len(NODES),links=len(LINKS),output=str(HERE/'pos-ui.figcraft-source.json'))))


def validate():
    errors=[]
    for name,f in FRAMES.items():
        root=f['absoluteBoundingBox']
        def visit(n):
            b=n.get('absoluteBoundingBox')
            if b and (b['x']<root['x']-.5 or b['y']<root['y']-.5 or
                      b['x']+b['width']>root['x']+root['width']+.5 or
                      b['y']+b['height']>root['y']+root['height']+.5):
                errors.append(f'{name}: out of frame: {n["name"]}')
            if n['type']=='TEXT' and '\u2014' in n['characters']:
                errors.append(f'{name}: em dash in UI')
            for child in n.get('children',[]):visit(child)
        visit(f)
    owner={}
    def collect(n,frame_key):
        owner[n['id']]=frame_key
        for child in n.get('children',[]):collect(child,frame_key)
    for name,f in FRAMES.items():collect(f,name)
    edges={name:set() for name in FRAMES}
    for n,to,_ in LINKS:edges[owner[n['id']]].add(to)
    for name in FRAMES:
        if name.split('/')[2]!='mek':continue
        seen=set();todo=[name]
        while todo:
            current=todo.pop()
            if current in seen:continue
            seen.add(current)
            assert current.split('/')[2] in ('mek','detail_mek','menu_mek'), current
            def no_money(n):
                assert 'Rp ' not in n.get('characters',''), current
                for child in n.get('children',[]):no_money(child)
            no_money(FRAMES[current])
            todo.extend(edges[current]-seen)
    if errors:raise ValueError('\n'.join(errors[:40])+f'\nTotal geometry/text failures: {len(errors)}')
    print('PASS: frame bounds, navigation targets, mechanic price isolation, UI text')


if __name__=='__main__':main()
