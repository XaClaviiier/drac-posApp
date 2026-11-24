# build_ui04.py - menerapkan irisan UI-04 (login, peran Owner/Teknisi/Kasir,
# estimasi WO, invoice final/koreksi, audit log, cari global, state interaksi)
# ke file .figcraft native TANPA regenerasi baseline lama.
#
# Cara pakai (dari root POS):
#   python doc/DBD/prototype/build_ui04.py <native.figcraft> <out.json> [--no-motion]
# lalu:
#   figcraft-cli convert <out.json> <out.figcraft>
#
# Sumber keputusan: doc/POS-handoff-login-role-global-search.md §4;
# token: doc/DBD/DESIGN_POS_Extend.md (prototype + UI-04).
# Skrip ini menambah node baru dan menambal interaksi existing; konten lama
# (invoice A4, motion UI-03, galeri kondisi) tidak dibangun ulang.

import json
import re
import sys
import zipfile
import math

# ----------------------------------------------------------------------------- util


def load(path):
    with zipfile.ZipFile(path) as z:
        return json.loads(z.read("document.json").decode("utf-8"))


def C(hexs, a=1.0):
    h = hexs.lstrip("#")
    return {
        "r": int(h[0:2], 16) / 255.0,
        "g": int(h[2:4], 16) / 255.0,
        "b": int(h[4:6], 16) / 255.0,
        "a": a,
    }


def paint(hexs, a=1.0):
    return {"type": "solid", "color": C(hexs, a), "opacity": 1.0, "visible": True, "blend": "normal"}


TOKENS = {
    "light": {
        "canvas": "#F7F9FC", "surface": "#FFFFFF", "sidebar": "#F1F4F8",
        "text": "#172B4D", "text2": "#53647B", "divider": "#DDE4ED",
        "input": "#7B8BA1", "action": "#006BEB", "on_action": "#FFFFFF",
        "active": "#E9F2FF", "ok": "#147A52", "ok_bg": "#EAF7F0",
        "warn": "#8B5B10", "warn_bg": "#FFF5E0", "err": "#B42332",
        "hover_bg": "#EEF5FF", "press_bg": "#DCEAFE",
        "action_hover": "#0058C2", "action_press": "#00479E",
        "focus": "#006BEB", "scrim": ("#172B4D", 0.48),
    },
    "dark": {
        "canvas": "#101319", "surface": "#181D25", "sidebar": "#131820",
        "text": "#EDF2FA", "text2": "#AAB8CB", "divider": "#303A49",
        "input": "#71829A", "action": "#66AAFF", "on_action": "#10233E",
        "active": "#20344E", "ok": "#71D9AA", "ok_bg": "#17372C",
        "warn": "#F2CE87", "warn_bg": "#3B301C", "err": "#FFACB7",
        "hover_bg": "#1C2E45", "press_bg": "#27415F",
        "action_hover": "#85BCFF", "action_press": "#A5CFFF",
        "focus": "#66AAFF", "scrim": ("#05070A", 0.64),
    },
}


class Doc:
    def __init__(self, doc, motion=True):
        self.d = doc
        self.nodes = {int(k): v for k, v in doc["nodes"].items()}
        self.next = int(doc["next_id"])
        self.motion = motion

    def save(self):
        self.d["nodes"] = {str(k): v for k, v in self.nodes.items()}
        self.d["next_id"] = self.next
        return self.d

    def add(self, node):
        i = self.next
        self.next += 1
        node["id"] = i
        self.nodes[i] = node
        return i

    def dur(self, ms):
        return ms if self.motion else 0

    def link(self, nid, dest, trigger="onClick", trans="dissolve", ms=180, easing="easeOut"):
        n = self.nodes[nid]
        n.setdefault("interactions", []).append({
            "trigger": {"type": trigger},
            "actions": [{"type": "navigate", "dest": dest}],
            "transition": {"type": trans},
            "duration_ms": self.dur(ms),
            "easing": easing,
        })

    # ---- primitive builders (mengikuti skema node existing) ----
    def frame(self, parent, x, y, w, h, name="Frame", fill=None, strokes=None,
              radii=None, clip=False, top=False):
        n = {"name": name, "type": "frame", "parent": parent, "children": [],
             "transform": [1.0, 0.0, 0.0, 1.0, float(x), float(y)],
             "width": float(w), "height": float(h),
             "stroke": {"weight": 1.0 if strokes else 0.0, "align": "inside", "sides": None,
                        "cap_start": "none", "cap_end": "none", "join": "miter",
                        "miter_limit": 4.0, "dashes": []},
             "corners": {"radii": [float(r or 0) for r in (radii or [0, 0, 0, 0])] if radii else [0.0] * 4,
                          "smoothing": 0.0}}
        if fill is not None:
            n["fills"] = [fill] if isinstance(fill, dict) else fill
        if strokes is not None:
            n["strokes"] = strokes
        if top:
            n["clip"] = True
        elif clip:
            n["clip"] = True
        i = self.add(n)
        self.nodes[parent].setdefault("children", []).append(i)
        return i

    def rect(self, parent, x, y, w, h, name="Surface", fill=None, radii=None,
             stroke=None, sw=1.0, visible=True):
        n = {"name": name, "type": "frame", "children": [], "parent": parent, "blend": "normal",
             "transform": [1.0, 0.0, 0.0, 1.0, float(x), float(y)],
             "width": float(w), "height": float(h),
             "stroke": {"weight": float(sw if stroke else 0.0), "align": "inside",
                        "sides": None, "cap_start": "none", "cap_end": "none",
                        "join": "miter", "miter_limit": 4.0, "dashes": []},
             "corners": {"radii": [float(r) for r in (radii or [0, 0, 0, 0])], "smoothing": 0.0}}
        if fill is not None:
            n["fills"] = [fill]
        if stroke is not None:
            n["strokes"] = [stroke]
        if not visible:
            n["visible"] = False
        i = self.add(n)
        self.nodes[parent].setdefault("children", []).append(i)
        return i

    def text(self, parent, x, y, w, chars, size=14, style="Regular", color="#172B4D",
             lh=None, name=None, align=None, alpha=1.0):
        lh = lh or (40 if size >= 27 else round(size * 1.5))
        lines = sum(max(1, math.ceil(len(line) * size * 0.57 / max(w, 1)))
                    for line in chars.split("\n"))
        h = lh * lines + 2
        styleobj = {"font_family": "Inter", "font_style": style, "font_size": float(size),
                    "line_height": {"unit": "pixels", "value": float(lh)},
                    "letter_spacing": {"unit": "percent", "value": 0.0},
                    "decoration": "none", "case": "original", "fills": None, "link": None}
        n = {"name": name or chars.split("\n")[0][:48], "type": "text", "characters": chars,
             "style": styleobj, "auto_resize": "height", "parent": parent, "blend": "normal",
             "transform": [1.0, 0.0, 0.0, 1.0, float(x), float(y)],
             "width": float(w), "height": float(h),
             "fills": [paint(color, alpha)],
             "child_layout": {"sizing_h": "fixed", "sizing_v": "hug", "absolute": False,
                              "min_w": None, "max_w": None, "min_h": None, "max_h": None,
                              "grid_column": None, "grid_row": None,
                              "grid_column_span": 0, "grid_row_span": 0}}
        if align:
            n["align_h"] = align
        i = self.add(n)
        self.nodes[parent].setdefault("children", []).append(i)
        return i

    def button(self, parent, x, y, w, h, label, tk, kind="primary", dest=None, ms=180):
        if kind == "primary":
            fill = paint(tk["action"])
            fg = tk["on_action"]
            strokes = None
            style = "Semi Bold"
        else:
            fill = paint(tk["surface"])
            fg = tk["action"]
            strokes = [paint(tk["input"])]
            style = "Medium"
        f = self.frame(parent, x, y, w, h, name=f"Button/{label}", fill=fill,
                       strokes=strokes, radii=[8, 8, 8, 8])
        t = self.text(f, 0, (h - (round(14 * 1.5) + 2)) / 2.0, w, label, size=14,
                      style=style, color=fg, align="center")
        if dest is not None:
            self.link(f, dest, ms=ms)
        return f

    def badge(self, parent, x, y, label, fg, bg, w=None):
        w = w or (12 + 7 * len(label))
        r = self.rect(parent, x, y, w, 27, name=f"Status/{label}", fill=paint(bg), radii=[6, 6, 6, 6])
        self.text(r, 10, 4, w - 20, label, size=12, style="Medium", color=fg)
        return r

    def clone(self, root, dx=0.0, dy=0.0):
        """Salin subtree dengan id baru; interaksi disalin apa adanya."""
        mapping = {}

        def cp(oid, parent):
            o = self.nodes[oid]
            n = {k: (list(v) if isinstance(v, list) else (dict(v) if isinstance(v, dict) else v))
                 for k, v in o.items() if k not in ("id", "children", "parent")}
            if parent is not None:
                n["parent"] = parent
            if "transform" in n and parent is None:
                t = list(n["transform"])
                t[4] += dx
                t[5] += dy
                n["transform"] = t
            if "interactions" in n:
                n["interactions"] = json.loads(json.dumps(n["interactions"]))
            nid = self.add(n)
            mapping[oid] = nid
            kids = []
            for c in o.get("children", []):
                kids.append(cp(c, nid))
            if "children" in o or kids:
                n["children"] = kids
            return nid

        new_root = cp(root, None)
        return new_root, mapping

    def find(self, name, page=None):
        for i, n in self.nodes.items():
            if n.get("name") == name and (page is None or n.get("parent") == page):
                return i
        raise KeyError(name)

    def root_of(self, nid):
        seen = set()
        while True:
            p = self.nodes[nid].get("parent")
            if p is None or self.nodes[p].get("type") == "page" or p in seen:
                return nid
            seen.add(p)
            nid = p

    def delete(self, nid):
        n = self.nodes.pop(nid)
        for c in n.get("children", []):
            if c in self.nodes:
                self.delete(c)
        p = n.get("parent")
        if p in self.nodes and nid in self.nodes[p].get("children", []):
            self.nodes[p]["children"].remove(nid)


# ----------------------------------------------------------------------------- phase 1: rename


SUP_MAP = {
    "Catat hasil pemeriksaan untuk supervisor.":
        "Catat hasil pemeriksaan dan estimasi pekerjaan.",
    "Supervisor atau kasir melanjutkan penagihan.":
        "Kasir atau owner melanjutkan penagihan.",
}


def rename_phase(D):
    hits = 0
    for n in D.nodes.values():
        if n.get("type") == "page":
            for f in n.get("flows", []):
                new = f["name"].replace("Mekanik", "Teknisi").replace("mekanik", "teknisi")
                if new != f["name"]:
                    f["name"] = new
                    hits += 1
            continue
        for key in ("characters", "name"):
            v = n.get(key)
            if not isinstance(v, str):
                continue
            new = v
            if key == "characters" and new in SUP_MAP:
                new = SUP_MAP[new]
            new = new.replace("Mekanik", "Teknisi").replace("mekanik", "teknisi")
            new = new.replace("Supervisor", "Owner").replace("supervisor", "owner")
            if new != v:
                n[key] = new
                hits += 1
    return hits


# ----------------------------------------------------------------------------- shells


def shell_clone(D, base_id, page_id, x, y, name, keep_names):
    """Clone shell (mis. Detail WO), buang konten lama selain sidebar/topbar."""
    root, m = D.clone(base_id)
    D.nodes[root]["name"] = name
    D.nodes[root]["parent"] = page_id
    t = [1.0, 0.0, 0.0, 1.0, float(x), float(y)]
    D.nodes[root]["transform"] = t
    D.nodes[page_id]["children"].append(root)
    for c in list(D.nodes[root]["children"]):
        n = D.nodes[c]
        keep = n.get("name") in keep_names or (
            n.get("type") == "text" and n.get("characters", "").startswith("Bengkel"))
        if not keep:
            D.delete(c)
    return root, m


SHELL_KEEP = {"Sidebar", "Surface", "Divider", "Ganti tema", "Data contoh"}


def set_breadcrumb(D, root, text):
    for c in D.nodes[root]["children"]:
        n = D.nodes[c]
        if n.get("type") == "text" and n.get("characters", "").startswith("Bengkel"):
            n["characters"] = text
            n["name"] = text[:48]
            return


def place_frames(D, page_id, count, w, h, gap=200):
    """Baris posisi baru di bawah semua frame existing pada halaman."""
    max_y = 0.0
    max_x = 0.0
    for c in D.nodes[page_id].get("children", []):
        n = D.nodes[c]
        t = n.get("transform")
        if not t:
            continue
        max_y = max(max_y, t[5] + float(n.get("height", 0)))
        max_x = max(max_x, t[4] + float(n.get("width", 0)))
    y = max_y + 400
    return [(max(0.0, i * (w + gap)), y) for i in range(count)], y


# ----------------------------------------------------------------------------- tabel estimasi

# Data contoh; perhitungan harus rekonsiliasi: subtotal baris = qty x harga;
# subtotal jasa + subtotal part = total. (handoff §4.5)
EST_ROWS = [
    # jenis, item, qty, satuan, harga_satuan, subtotal, diubah_dari
    ("Jasa", "Isi freon", "1", "paket", 150000, 150000, None),
    ("Jasa", "Kuras evaporator", "1", "paket", 350000, 350000, None),
    ("Part", "Filter kabin", "2", "pcs", 80000, 160000, 85000),
    ("Part", "Freon R134a", "2", "tabung", 60000, 120000, None),
]
SUB_JASA = 500000
SUB_PART = 280000
TOTAL_EST = 780000
DIBAYAR = 500000
TOTAL_KOREKSI = TOTAL_EST - 350000


def rp(v):
    return "Rp " + f"{v:,}".replace(",", ".")


def table_estimasi(D, parent, x, y, w, tk, total_label="Total estimasi", edited=True):
    """Tabel itemized + ringkasan. Mengembalikan tinggi terpakai."""
    cols = [("Jenis", x + 24, 90, None), ("Pekerjaan", x + 124, 420, None),
            ("Qty", x + 554, 60, None), ("Satuan", x + 624, 80, None),
            ("Harga satuan", x + 714, 190, "right"), ("Subtotal", x + 914, w - 24 - (914 - x + x), "right")]
    hdr = D.rect(parent, x, y, w, 32, name="Table header", fill=paint(tk["sidebar"]), radii=[6, 6, 6, 6])
    for label, cx, cw, al in cols:
        D.text(hdr, cx - x + (10 if al != "right" else 0), 6, cw - (20 if al == "right" else 10),
               label, size=12, style="Semi Bold", color=tk["text2"],
               align=al or None)
    ry = y + 32
    for jenis, item, qty, sat, harga, sub, old in EST_ROWS:
        row = D.frame(parent, x, ry, w, 44, name=f"Row/{item}", fill=paint(tk["surface"]))
        D.rect(row, 0, 43, w, 1, name="Divider", fill=paint(tk["divider"]))
        if old and edited:
            D.rect(row, 4, 2, w - 8, 40, name="Highlight edit harga", fill=paint(tk["warn_bg"]), radii=[6, 6, 6, 6])
        D.text(row, 34, 12, 90, jenis, size=13, color=tk["text2"])
        D.text(row, 134, 12, 420, item, size=13, style="Medium", color=tk["text"])
        D.text(row, 564, 12, 60, qty, size=13, color=tk["text"])
        D.text(row, 634, 12, 80, sat, size=13, color=tk["text2"])
        D.text(row, 724, 12, 180, rp(harga), size=13, color=tk["text"], align="right")
        D.text(row, 924, 12, w - 24 - 924, rp(sub), size=13, style="Medium", color=tk["text"], align="right")
        if old and edited:
            D.text(row, 134, 28, 420, f"diubah dari {rp(old)} hanya untuk baris ini",
                   size=10, color=tk["warn"])
        ry += 44
    sy = ry + 12
    D.text(parent, x + w - 400, sy, 200, "Subtotal jasa", size=13, color=tk["text2"], align="right")
    D.text(parent, x + w - 190, sy, 166, rp(SUB_JASA), size=13, color=tk["text"], align="right")
    D.text(parent, x + w - 400, sy + 26, 200, "Subtotal part", size=13, color=tk["text2"], align="right")
    D.text(parent, x + w - 190, sy + 26, 166, rp(SUB_PART), size=13, color=tk["text"], align="right")
    D.rect(parent, x + w - 400, sy + 56, 376, 1, name="Divider", fill=paint(tk["divider"]))
    D.text(parent, x + w - 400, sy + 66, 200, total_label, size=15, style="Semi Bold", color=tk["text"], align="right")
    D.text(parent, x + w - 190, sy + 62, 166, rp(TOTAL_EST), size=18, style="Bold", color=tk["text"], align="right")
    return sy + 96 - y


# ----------------------------------------------------------------------------- frame fitur


def build_estimasi(D, page, x, y, base_detail, tk, dest_board, dest_draft):
    root, m = shell_clone(D, base_detail, page, x, y,
                          "Detail work order / Light / Desktop / estimasi", SHELL_KEEP)
    set_breadcrumb(D, root, "Bengkel   /   Detail work order   /   Estimasi")
    D.text(root, 272, 101, 560, "Detail work order", size=26, style="Bold", color=tk["text"])
    D.text(root, 272, 148, 700, "WO-0268  ·  Toyota Avanza 1.3  ·  Budi Santoso", size=14, color=tk["text2"])
    D.text(root, 272, 196, 300, "DD 1248 KL", size=27, style="Semi Bold", color=tk["text"])
    D.badge(root, 460, 204, "Dalam pengerjaan", tk["warn"], tk["warn_bg"], w=160)
    D.button(root, 868, 101, 240, 44, "Kembali ke papan WO", tk, "secondary", dest_board)
    D.button(root, 1128, 101, 280, 44, "Kirim estimasi ke kasir", tk, "primary", dest_draft, ms=200)
    # diagnosa terhubung
    card = D.frame(root, 272, 260, 1136, 104, name="Diagnosa terhubung", fill=paint(tk["surface"]),
                   strokes=[paint(tk["divider"])], radii=[12, 12, 12, 12])
    D.text(card, 24, 16, 340, "Diagnosa terhubung", size=16, style="Semi Bold", color=tk["text"])
    D.text(card, 24, 44, 340, "Sumber: nota servis NS-0268\n(dibaca saja, tidak dientry ulang)",
           size=12, color=tk["text2"])
    D.text(card, 392, 16, 340, "Temuan", size=12, style="Semi Bold", color=tk["text2"])
    D.text(card, 392, 40, 340, "Tekanan freon rendah; sambungan pipa baik.", size=13, color=tk["text"])
    D.text(card, 760, 16, 352, "Rekomendasi teknisi", size=12, style="Semi Bold", color=tk["text2"])
    D.text(card, 760, 40, 352, "Isi freon, kuras evaporator, ganti filter kabin.", size=13, color=tk["text"])
    # tabel estimasi
    est = D.frame(root, 272, 388, 1136, 400, name="Estimasi pekerjaan", fill=paint(tk["surface"]),
                  strokes=[paint(tk["divider"])], radii=[12, 12, 12, 12])
    D.text(est, 24, 16, 700, "Estimasi pekerjaan (harga jual, data contoh)", size=16,
           style="Semi Bold", color=tk["text"])
    table_estimasi(D, est, 24, 52, 1088, tk)
    D.text(est, 24, 364, 1088,
           "Subtotal baris = qty × harga satuan. Total = subtotal jasa + subtotal part. Angka contoh, dihitung apa adanya.",
           size=12, color=tk["text2"])
    # strip edit harga lokal
    strip = D.frame(root, 272, 804, 1136, 60, name="Perubahan harga lokal", fill=paint(tk["warn_bg"]),
                    radii=[8, 8, 8, 8])
    D.text(strip, 16, 8, 1104,
           "Harga jual Filter kabin diubah Rp 85.000 menjadi Rp 80.000 hanya untuk baris WO ini. Harga master tetap Rp 85.000.",
           size=12, color=tk["warn"])
    D.text(strip, 16, 30, 1104,
           "Tercatat di log harga: Teknisi (Andi) · 31 Oktober 2026 09.12 · alasan: diskon paket. Log lengkap hanya Owner.",
           size=12, color=tk["warn"])
    return root


def build_invoice_draft(D, page, x, y, base_detail, tk, dest_final, dest_kasir):
    root, m = shell_clone(D, base_detail, page, x, y,
                          "Invoice / Light / Desktop / draft", SHELL_KEEP)
    set_breadcrumb(D, root, "Bengkel   /   Invoice   /   INV-0268")
    D.text(root, 272, 101, 560, "Invoice INV-0268", size=26, style="Bold", color=tk["text"])
    D.badge(root, 596, 110, "Draf", tk["warn"], tk["warn_bg"], w=70)
    D.text(root, 272, 150, 700, "DD 1248 KL  ·  Toyota Avanza 1.3  ·  Budi Santoso", size=14, color=tk["text2"])
    card = D.frame(root, 272, 196, 1136, 400, name="Tagihan draf", fill=paint(tk["surface"]),
                   strokes=[paint(tk["divider"])], radii=[12, 12, 12, 12])
    D.text(card, 24, 16, 700, "Tagihan draf (disalin dari WO-0268)", size=16, style="Semi Bold", color=tk["text"])
    table_estimasi(D, card, 24, 52, 1088, tk, total_label="Total tagihan draf")
    D.text(card, 24, 364, 1088,
           "Baris memakai harga transaksi WO, bukan harga master yang diambil ulang. Edit di draf tidak mengubah WO asal.",
           size=12, color=tk["text2"])
    note = D.frame(root, 272, 620, 1136, 72, name="Catatan status", fill=paint(tk["sidebar"]), radii=[8, 8, 8, 8])
    D.text(note, 16, 10, 1104,
            "Teknisi dapat mengubah harga jual lokal pada draf; HPP tetap hanya Owner.", size=13, color=tk["text"])
    D.text(note, 16, 36, 1104,
           "Setelah difinalkan invoice terkunci: hanya Owner yang dapat mengoreksi.", size=13, color=tk["text2"])
    D.button(root, 272, 724, 220, 44, "Finalkan invoice", tk, "primary", dest_final, ms=180)
    D.button(root, 508, 724, 200, 44, "Kembali ke kasir", tk, "secondary", dest_kasir)
    return root


def build_invoice_final(D, page, x, y, base_detail, tk, dest_koreksi, dest_audit, dest_list):
    root, m = shell_clone(D, base_detail, page, x, y,
                          "Invoice / Light / Desktop / final", SHELL_KEEP)
    set_breadcrumb(D, root, "Bengkel   /   Invoice   /   INV-0268")
    D.text(root, 272, 101, 560, "Invoice INV-0268", size=26, style="Bold", color=tk["text"])
    D.badge(root, 596, 110, "Final", tk["ok"], tk["ok_bg"], w=80)
    D.text(root, 272, 150, 700, "DD 1248 KL  ·  Toyota Avanza 1.3  ·  Budi Santoso", size=14, color=tk["text2"])
    card = D.frame(root, 272, 196, 1136, 260, name="Tagihan final", fill=paint(tk["surface"]),
                   strokes=[paint(tk["divider"])], radii=[12, 12, 12, 12])
    D.text(card, 24, 16, 700, "Tagihan final", size=16, style="Semi Bold", color=tk["text"])
    ry = 52
    for jenis, item, qty, sat, harga, sub, old in EST_ROWS:
        D.text(card, 24, ry, 500, f"{jenis}  ·  {item}  ·  {qty} {sat}", size=13, color=tk["text"])
        D.text(card, 900, ry, 164, rp(sub), size=13, color=tk["text"], align="right")
        ry += 30
    D.rect(card, 24, ry + 4, 1064, 1, name="Divider", fill=paint(tk["divider"]))
    D.text(card, 700, ry + 14, 200, "Total tagihan", size=15, style="Semi Bold", color=tk["text"], align="right")
    D.text(card, 900, ry + 10, 164, rp(TOTAL_EST), size=18, style="Bold", color=tk["text"], align="right")
    pay = D.frame(root, 272, 480, 1136, 132, name="Riwayat pembayaran", fill=paint(tk["surface"]),
                  strokes=[paint(tk["divider"])], radii=[12, 12, 12, 12])
    D.text(pay, 24, 16, 700, "Riwayat pembayaran (tidak diubah oleh koreksi)", size=16,
           style="Semi Bold", color=tk["text"])
    D.text(pay, 24, 50, 1064, f"{rp(DIBAYAR)}  ·  Tunai  ·  31 Oktober 2026 10.05  ·  diterima Kasir",
           size=13, color=tk["text"])
    D.text(pay, 24, 80, 1064, f"Sisa tagihan: {rp(TOTAL_EST - DIBAYAR)}", size=14, style="Semi Bold",
           color=tk["warn"])
    note = D.frame(root, 272, 636, 1136, 56, name="Catatan kunci", fill=paint(tk["sidebar"]), radii=[8, 8, 8, 8])
    D.text(note, 16, 8, 1104,
           "Invoice final terkunci untuk Teknisi dan Kasir walau belum lunas. Koreksi hanya oleh Owner,", size=13, color=tk["text"])
    D.text(note, 16, 30, 1104,
           "wajib alasan, dan tidak menulis ulang uang yang sudah diterima.", size=13, color=tk["text2"])
    D.button(root, 272, 724, 260, 44, "Koreksi invoice (Owner)", tk, "primary", dest_koreksi)
    D.button(root, 548, 724, 240, 44, "Audit log (Owner)", tk, "secondary", dest_audit)
    D.button(root, 804, 724, 240, 44, "Kembali ke daftar", tk, "secondary", dest_list)
    return root


def build_koreksi(D, page, x, y, base_detail, tk, dest_audit, dest_final):
    root, m = shell_clone(D, base_detail, page, x, y,
                          "Koreksi invoice / Light / Desktop / owner", SHELL_KEEP)
    set_breadcrumb(D, root, "Bengkel   /   Invoice   /   INV-0268   /   Koreksi")
    D.text(root, 272, 101, 700, "Koreksi invoice final", size=26, style="Bold", color=tk["text"])
    D.badge(root, 660, 110, "Hanya Owner", tk["action"], tk["active"], w=130)
    D.text(root, 272, 150, 700, "INV-0268  ·  DD 1248 KL  ·  Budi Santoso", size=14, color=tk["text2"])
    c1 = D.frame(root, 272, 196, 1136, 116, name="Alasan koreksi", fill=paint(tk["surface"]),
                 strokes=[paint(tk["divider"])], radii=[12, 12, 12, 12])
    D.text(c1, 24, 14, 400, "Alasan koreksi (wajib)", size=12, style="Semi Bold", color=tk["text2"])
    inp = D.rect(c1, 24, 40, 1088, 44, name="Input/alasan", fill=paint(tk["canvas"]),
                 radii=[8, 8, 8, 8], stroke=paint(tk["input"]))
    D.text(inp, 16, 12, 1056, "Pekerjaan kuras evaporator dibatalkan pelanggan; tagihan disesuaikan.",
           size=13, color=tk["text"])
    c2 = D.frame(root, 272, 336, 1136, 108, name="Perubahan nilai", fill=paint(tk["surface"]),
                 strokes=[paint(tk["divider"])], radii=[12, 12, 12, 12])
    D.text(c2, 24, 14, 400, "Total tagihan", size=12, style="Semi Bold", color=tk["text2"])
    D.text(c2, 24, 40, 700, f"{rp(TOTAL_EST)}  →  {rp(TOTAL_KOREKSI)}", size=18, style="Semi Bold",
           color=tk["text"])
    D.text(c2, 24, 74, 1064,
           "Nilai sebelum/sesudah, aktor, dan waktu disimpan sebagai riwayat revisi; dokumen asli tidak ditimpa.",
           size=12, color=tk["text2"])
    imp = D.frame(root, 272, 468, 1136, 108, name="Dampak uang", fill=paint(tk["warn_bg"]), radii=[12, 12, 12, 12])
    D.text(imp, 24, 14, 700, "Dampak uang (dicatat terpisah)", size=14, style="Semi Bold", color=tk["warn"])
    D.text(imp, 24, 42, 1064,
           f"Dibayar {rp(DIBAYAR)} tidak berubah. Total baru {rp(TOTAL_KOREKSI)}: kelebihan bayar",
           size=13, color=tk["warn"])
    D.text(imp, 24, 64, 1064,
           f"{rp(DIBAYAR - TOTAL_KOREKSI)} dicatat sebagai saldo kelebihan. Refund = pergerakan uang terpisah, tidak otomatis.",
           size=13, color=tk["warn"])
    rev = D.frame(root, 272, 600, 1136, 92, name="Riwayat revisi", fill=paint(tk["surface"]),
                  strokes=[paint(tk["divider"])], radii=[12, 12, 12, 12])
    D.text(rev, 24, 12, 400, "Riwayat revisi", size=12, style="Semi Bold", color=tk["text2"])
    D.text(rev, 24, 38, 1064,
           f"Rev 1  ·  31 Oktober 2026 11.20  ·  Owner  ·  {rp(TOTAL_EST)} → {rp(TOTAL_KOREKSI)}  ·  alasan di atas",
           size=13, color=tk["text"])
    D.text(rev, 24, 64, 1064, "Rev 0  ·  31 Oktober 2026 10.10  ·  Kasir  ·  invoice difinalkan", size=13,
           color=tk["text2"])
    b_simpan = D.button(root, 272, 736, 240, 44, "Simpan koreksi (demo)", tk, "primary", dest_audit)
    b_batal = D.button(root, 528, 736, 120, 44, "Batal", tk, "secondary", dest_final)
    return root, b_batal


def build_audit(D, page, x, y, base_detail, tk, dest_back):
    root, m = shell_clone(D, base_detail, page, x, y,
                          "Audit log / Light / Desktop / owner", SHELL_KEEP)
    set_breadcrumb(D, root, "Bengkel   /   Audit log")
    D.text(root, 272, 101, 560, "Audit log", size=26, style="Bold", color=tk["text"])
    D.badge(root, 452, 110, "Hanya Owner", tk["action"], tk["active"], w=130)
    D.text(root, 272, 150, 900, "Catatan aksi, aktor, waktu, nilai lama → baru, dan alasan. Seluruh data contoh.",
           size=14, color=tk["text2"])
    card = D.frame(root, 272, 196, 1136, 340, name="Tabel audit", fill=paint(tk["surface"]),
                   strokes=[paint(tk["divider"])], radii=[12, 12, 12, 12])
    hdr = D.rect(card, 0, 0, 1136, 36, name="Table header", fill=paint(tk["sidebar"]), radii=[12, 12, 0, 0])
    colsx = [(16, 130, "Waktu"), (156, 150, "Aktor"), (316, 250, "Aksi"),
             (576, 210, "Dokumen"), (796, 220, "Lama → Baru"), (1026, 94, "Alasan")]
    for cx, cw, label in colsx:
        D.text(hdr, cx, 8, cw, label, size=12, style="Semi Bold", color=tk["text2"])
    rows = [
        ("31 Okt 11.20", "Owner", "Koreksi invoice final", "INV-0268",
         f"{rp(TOTAL_EST)} →\n{rp(TOTAL_KOREKSI)}", "Evaporator dibatalkan pelanggan"),
        ("31 Okt 10.05", "Kasir", "Terima pembayaran tunai", "INV-0268",
         f"Rp 0 →\n{rp(DIBAYAR)}", "Pembayaran pelanggan"),
        ("31 Okt 09.12", "Teknisi (Andi)", "Ubah harga jual baris WO", "WO-0268 ·\nFilter kabin",
         "Rp 85.000 →\nRp 80.000", "Diskon paket kuras evaporator"),
        ("31 Okt 08.55", "Owner", "Ubah harga master jasa", "Kuras evaporator",
         "Rp 325.000 →\nRp 350.000", "Penyesuaian biaya (contoh)"),
    ]
    ry = 44
    for row in rows:
        rr = D.frame(card, 0, ry, 1136, 66, name=f"Audit/{row[1]} {row[2]}", fill=paint(tk["surface"]))
        D.rect(rr, 16, 65, 1104, 1, name="Divider", fill=paint(tk["divider"]))
        for (cx, cw, _), val in zip(colsx, row):
            D.text(rr, cx, 10, cw, val, size=12, color=tk["text"])
        ry += 66
    note = D.frame(root, 272, 560, 1136, 76, name="Batas otorisasi", fill=paint(tk["sidebar"]), radii=[8, 8, 8, 8])
    D.text(note, 16, 10, 1104,
           "Log lengkap termasuk HPP dan pengeluaran hanya terlihat Owner. Sisi admin audit log = Owner, bukan peran keempat.",
           size=13, color=tk["text"])
    D.text(note, 16, 38, 1104,
           "Tampilan ini contoh desain; otorisasi nyata divalidasi di server (TRD §4), bukan oleh UI.",
           size=13, color=tk["text2"])
    D.button(root, 272, 680, 240, 44, "Kembali ke ringkasan", tk, "secondary", dest_back)
    return root


# ----------------------------------------------------------------------------- galeri state


def cell_button(D, g, x, y, tk, kind, state):
    w, h = 160, 44
    if kind == "primary":
        base, fg, st = tk["action"], tk["on_action"], None
    else:
        base, fg, st = tk["surface"], tk["text"], tk["input"]
    if state == "hover":
        base = tk["action_hover"] if kind == "primary" else tk["hover_bg"]
    elif state == "pressed":
        base = tk["action_press"] if kind == "primary" else tk["press_bg"]
    fill = paint(base, 0.4 if state == "disabled" else 1.0)
    b = D.frame(g, x, y, w, h, name=f"{kind}/{state}", fill=fill,
                strokes=[paint(st, 0.4 if state == "disabled" else 1.0)] if st else None,
                radii=[8, 8, 8, 8])
    D.text(b, 0, 11, w, "Simpan" if kind == "primary" else "Batal", size=14,
           style="Semi Bold" if kind == "primary" else "Medium",
           color=fg, align="center", alpha=0.5 if state == "disabled" else 1.0)
    if state == "focus":
        D.rect(g, x - 4, y - 4, w + 8, h + 8, name="Ring fokus", radii=[10, 10, 10, 10],
               stroke=paint(tk["focus"]), sw=2.0)
    return b


def cell_nav(D, g, x, y, tk, state):
    w, h = 190, 44
    bg = {"default": None, "hover": tk["hover_bg"], "pressed": tk["press_bg"],
          "focus": None, "disabled": None}[state]
    n = D.frame(g, x, y, w, h, name=f"nav/{state}", fill=paint(bg) if bg else None,
                radii=[8, 8, 8, 8])
    D.rect(n, 14, 12, 20, 20, name="Icon/box", radii=[4, 4, 4, 4],
           fill=paint(tk["text2"], 0.5 if state == "disabled" else 1.0))
    D.text(n, 44, 12, w - 54, "Work order", size=14,
           style="Semi Bold" if state in ("default", "focus") else "Medium",
           color=tk["text"], alpha=0.4 if state == "disabled" else 1.0)
    if state == "focus":
        D.rect(g, x - 4, y - 4, w + 8, h + 8, name="Ring fokus", radii=[10, 10, 10, 10],
               stroke=paint(tk["focus"]), sw=2.0)
    return n


def cell_row(D, g, x, y, tk, state):
    w, h = 200, 56
    bg = {"default": tk["surface"], "hover": tk["hover_bg"], "pressed": tk["press_bg"],
          "focus": tk["surface"], "disabled": tk["surface"]}[state]
    r = D.frame(g, x, y, w, h, name=f"row/{state}", fill=paint(bg, 0.4 if state == "disabled" else 1.0),
                strokes=[paint(tk["divider"])], radii=[8, 8, 8, 8])
    D.text(r, 12, 8, w - 24, "DD 1248 KL", size=14, style="Semi Bold", color=tk["text"],
           alpha=0.4 if state == "disabled" else 1.0)
    D.text(r, 12, 30, w - 24, "Toyota Avanza", size=12, color=tk["text2"],
           alpha=0.4 if state == "disabled" else 1.0)
    if state == "focus":
        D.rect(g, x - 4, y - 4, w + 8, h + 8, name="Ring fokus", radii=[10, 10, 10, 10],
               stroke=paint(tk["focus"]), sw=2.0)
    return r


def cell_search(D, g, x, y, tk, state):
    w, h = 200, 44
    border = tk["input"]
    bg = tk["surface"]
    if state == "hover":
        bg = tk["hover_bg"]
    elif state == "pressed":
        bg = tk["press_bg"]
    s = D.frame(g, x, y, w, h, name=f"search/{state}", fill=paint(bg, 0.4 if state == "disabled" else 1.0),
                strokes=[paint(border if state != "focus" else tk["focus"])],
                radii=[8, 8, 8, 8])
    D.nodes[s]["strokes"][0] = paint(tk["focus"] if state == "focus" else tk["input"],
                                     0.4 if state == "disabled" else 1.0)
    c = D.frame(s, 12, 12, 20, 20, name="Icon/search")
    e = {"name": "Icon circle", "type": "ellipse", "start": 0.0, "sweep": 6.283185307179586,
         "inner": 0.0, "parent": c, "blend": "normal",
         "transform": [1.0, 0.0, 0.0, 1.0, 2.0, 2.0], "width": 11.0, "height": 11.0,
         "strokes": [paint(tk["text2"], 0.4 if state == "disabled" else 1.0)],
         "stroke": {"weight": 1.6, "align": "center", "sides": None, "cap_start": "none",
                    "cap_end": "none", "join": "miter", "miter_limit": 4.0, "dashes": []},
         "fills": []}
    ei = D.add(e)
    D.nodes[c]["children"].append(ei)
    h2 = {"name": "Surface", "type": "rectangle", "parent": c, "blend": "normal",
          "transform": [1.0, 0.0, 0.0, 1.0, 13.0, 13.0], "width": 5.0, "height": 2.0,
          "fills": [paint(tk["text2"], 0.4 if state == "disabled" else 1.0)],
          "stroke": {"weight": 0.0, "align": "inside", "sides": None, "cap_start": "none",
                     "cap_end": "none", "join": "miter", "miter_limit": 4.0, "dashes": []},
          "corners": {"radii": [0.0] * 4, "smoothing": 0.0}}
    hi = D.add(h2)
    D.nodes[c]["children"].append(hi)
    D.text(s, 42, 12, w - 54, "Cari di bengkel...", size=13, color=tk["text2"],
           alpha=0.4 if state == "disabled" else 1.0)
    if state == "focus":
        D.rect(g, x - 4, y - 4, w + 8, h + 8, name="Ring fokus", radii=[10, 10, 10, 10],
               stroke=paint(tk["focus"]), sw=2.0)
    return s


def cell_field(D, g, x, y, tk, state):
    w, h = 200, 44
    bg = tk["surface"]
    if state == "disabled":
        bg = tk["canvas"]
    elif state in ("hover", "pressed"):
        bg = tk["hover_bg"]
    f = D.frame(g, x, y, w, h, name=f"field/{state}", fill=paint(bg, 0.4 if state == "disabled" else 1.0),
                strokes=[paint(tk["focus"] if state == "focus" else tk["input"],
                               0.4 if state == "disabled" else 1.0)],
                radii=[8, 8, 8, 8])
    D.text(f, 16, 12, w - 32, "DD 1248 KL" if state != "disabled" else "Terisi otomatis",
           size=13, color=tk["text"] if state != "disabled" else tk["text2"],
           alpha=1.0 if state != "disabled" else 0.6)
    if state == "focus":
        D.rect(g, x - 4, y - 4, w + 8, h + 8, name="Ring fokus", radii=[10, 10, 10, 10],
               stroke=paint(tk["focus"]), sw=2.0)
    return f


def cell_tab(D, g, x, y, tk, state):
    w, h = 120, 44
    bg = {"default": tk["surface"], "hover": tk["hover_bg"], "pressed": tk["press_bg"],
          "focus": tk["surface"], "disabled": tk["surface"]}[state]
    t = D.frame(g, x, y, w, h, name=f"tab/{state}",
                fill=paint(bg, 0.4 if state == "disabled" else 1.0),
                strokes=[paint(tk["input"], 0.4 if state == "disabled" else 1.0)],
                radii=[8, 8, 8, 8])
    D.text(t, 0, 11, w, "Jasa", size=14, style="Medium", color=tk["text"], align="center",
           alpha=0.4 if state == "disabled" else 1.0)
    if state == "focus":
        D.rect(g, x - 4, y - 4, w + 8, h + 8, name="Ring fokus", radii=[10, 10, 10, 10],
               stroke=paint(tk["focus"]), sw=2.0)
    return t


def cell_result(D, g, x, y, tk, state):
    w, h = 200, 44
    bg = {"default": None, "hover": tk["hover_bg"], "pressed": tk["press_bg"],
          "focus": None, "disabled": None}[state]
    r = D.frame(g, x, y, w, h, name=f"hasil/{state}", fill=paint(bg) if bg else None,
                radii=[8, 8, 8, 8])
    D.text(r, 12, 5, w - 24, "DD 1248 KL", size=13, style="Medium", color=tk["text"],
           alpha=0.4 if state == "disabled" else 1.0)
    D.text(r, 12, 24, w - 24, "Kendaraan", size=11, color=tk["text2"],
           alpha=0.4 if state == "disabled" else 1.0)
    if state == "focus":
        D.rect(g, x - 4, y - 4, w + 8, h + 8, name="Ring fokus", radii=[10, 10, 10, 10],
               stroke=paint(tk["focus"]), sw=2.0)
    return r


FAMILIES = [
    ("Tombol utama", lambda D, g, x, y, tk, s: cell_button(D, g, x, y, tk, "primary", s)),
    ("Tombol sekunder", lambda D, g, x, y, tk, s: cell_button(D, g, x, y, tk, "secondary", s)),
    ("Item navigasi", cell_nav),
    ("Tab / filter", cell_tab),
    ("Baris daftar / kartu", cell_row),
    ("Baris hasil pencarian", cell_result),
    ("Pemicu pencarian", cell_search),
    ("Field input", cell_field),
]
STATES = ["default", "hover", "focus", "pressed", "disabled"]
STATE_ID = {"default": "Default", "hover": "Hover", "focus": "Fokus", "pressed": "Pressed",
            "disabled": "Disabled"}


def build_gallery(D, page, x, y, tk):
    g = D.frame(page, x, y, 1440, 900, name="State interaksi / Light / Desktop / base",
                fill=paint(tk["canvas"]), top=True)
    D.nodes[g]["parent"] = page
    D.text(g, 64, 40, 1000, "State interaksi", size=26, style="Bold", color=tk["text"])
    D.text(g, 64, 86, 1312,
           "Spec hover/fokus/pressed/disabled untuk semua kontrol interaktif enabled. Token: DESIGN_POS_Extend §State interaksi (UI-04).",
           size=13, color=tk["text2"])
    D.text(g, 64, 108, 1312,
           "Gambar statis: perilaku hover nyata diuji pada tahap browser. Invoice cetak dan teks statis tidak menerima state. Data contoh.",
           size=13, color=tk["text2"])
    x0, y0 = 320, 158
    for j, s in enumerate(STATES):
        D.text(g, x0 + j * 210, y0, 190, STATE_ID[s], size=12, style="Semi Bold", color=tk["text2"])
    for i, (label, fn) in enumerate(FAMILIES):
        ry = y0 + 30 + i * 82
        D.text(g, 64, ry + 10, 240, label, size=14, style="Medium", color=tk["text"])
        for j, s in enumerate(STATES):
            fn(D, g, x0 + j * 210, ry, tk, s)
        D.rect(g, 64, ry + 66, 1312, 1, name="Divider", fill=paint(tk["divider"]))
    D.text(g, 64, 856, 1312,
           "Ring fokus 2 px offset 2 px. Disabled: opacity 40%, tanpa aksi. Target sentuh minimum 44 px dipertahankan pada semua state.",
           size=12, color=tk["text2"])
    return g


# ----------------------------------------------------------------------------- login


def build_login(D, page, x, y, tk, device, dests):
    W, Hh = (1440, 900) if device == "desktop" else (390, 844)
    cap = "Desktop" if device == "desktop" else "Mobile"
    theme = "Light" if tk is TOKENS["light"] else "Dark"
    root = D.frame(page, x, y, W, Hh, name=f"Login / {theme} / {cap} / base",
                   fill=paint(tk["canvas"]), top=True)
    D.nodes[root]["parent"] = page
    if device == "desktop":
        D.rect(root, 0, 0, 560, 900, name="Panel identitas", fill=paint(tk["sidebar"]))
        D.text(root, 64, 330, 440, "Dokter AC Mobil", size=28, style="Bold", color=tk["text"])
        D.text(root, 64, 376, 440, "Ruang kerja bengkel", size=16, color=tk["text2"])
        D.text(root, 64, 420, 440, "Tiga peran: Owner, Teknisi, Kasir.", size=13, color=tk["text2"])
        D.text(root, 64, 800, 440, "Pratinjau desain  ·  seluruh data contoh", size=12, color=tk["text2"])
        cx, cy, cw = 700, 170, 440
        card_h = 580
    else:
        D.text(root, 24, 100, 342, "Dokter AC Mobil", size=24, style="Bold", color=tk["text"])
        D.text(root, 24, 140, 342, "Ruang kerja bengkel", size=14, color=tk["text2"])
        D.text(root, 24, 796, 342, "Pratinjau desain  ·  seluruh data contoh", size=12, color=tk["text2"])
        cx, cy, cw = 24, 190, 342
        card_h = 580
    card = D.frame(root, cx, cy, cw, card_h, name="Form login", fill=paint(tk["surface"]),
                   strokes=[paint(tk["divider"])], radii=[12, 12, 12, 12])
    ix = 32
    iw = cw - 64
    D.text(card, ix, 32, iw, "Masuk ke aplikasi", size=20, style="Semi Bold", color=tk["text"])
    D.text(card, ix, 64, iw, "Login simulasi: tidak ada autentikasi nyata.", size=12, color=tk["text2"])
    D.text(card, ix, 104, iw, "Username", size=12, style="Medium", color=tk["text2"])
    inp = D.rect(card, ix, 124, iw, 44, name="Input/username", fill=paint(tk["canvas"]),
                 radii=[8, 8, 8, 8], stroke=paint(tk["input"]))
    D.text(inp, 16, 12, iw - 32, "username", size=13, color=tk["text2"])
    D.text(card, ix, 188, iw, "Password", size=12, style="Medium", color=tk["text2"])
    inp2 = D.rect(card, ix, 208, iw, 44, name="Input/password", fill=paint(tk["canvas"]),
                  radii=[8, 8, 8, 8], stroke=paint(tk["input"]))
    D.text(inp2, 16, 12, iw - 32, "••••••••", size=13, color=tk["text2"])
    D.button(card, ix, 276, iw, 44, "Masuk", tk, "primary", dests["owner"], ms=200)
    D.text(card, ix, 348, iw, "atau pilih akun demo", size=12, color=tk["text2"], align="center")
    D.button(card, ix, 372, iw, 44, "Demo sebagai Owner", tk, "secondary", dests["owner"], ms=200)
    D.button(card, ix, 428, iw, 44, "Demo sebagai Kasir", tk, "secondary", dests["kasir"], ms=200)
    D.button(card, ix, 484, iw, 44, "Demo sebagai Teknisi", tk, "secondary", dests["teknisi"], ms=200)
    D.text(card, ix, 544, iw, "Akun dibuat oleh Owner. Demo menentukan tujuan yang diizinkan per peran.",
           size=12, color=tk["text2"])
    return root


# ----------------------------------------------------------------------------- shell kasir terbatas


def build_kasir_shell(D, page, base_id, theme_name, x, y):
    root, m = D.clone(base_id)
    D.nodes[root]["name"] = f"Kasir / {theme_name} / Desktop / role-kasir"
    D.nodes[root]["parent"] = page
    D.nodes[root]["transform"] = [1.0, 0.0, 0.0, 1.0, float(x), float(y)]
    D.nodes[page]["children"].append(root)
    sidebar = None
    for c in D.nodes[root]["children"]:
        if D.nodes[c].get("name") == "Sidebar":
            sidebar = c
    remove_names = {"Nav/Teknisi", "Nav/Ringkasan", "Nav/Laporan", "Data bengkel",
                    "Nav/Jasa dan Part", "Nav/Cocok Part", "Nav/Pengaturan"}
    keep_pos = {"Nav/Terima mobil": 193, "Nav/Work order": 240, "Nav/Kasir": 287,
                "Nav/Invoice": 334, "Pemantauan": 388, "Nav/Riwayat plat": 416}
    for c in list(D.nodes[sidebar]["children"]):
        nm = D.nodes[c].get("name")
        if nm in remove_names:
            D.delete(c)
        elif nm in keep_pos and nm != "Pemantauan":
            D.nodes[c]["transform"][5] = float(keep_pos[nm])
        elif nm == "Pemantauan":
            D.nodes[c]["transform"][5] = float(keep_pos[nm])
    D.text(sidebar, 24, 480, 192,
           "Shell demo Kasir:\nmenu Owner-only tidak\nditampilkan.", size=12, color=TOKENS["light" if theme_name == "Light" else "dark"]["text2"])
    return root


# ----------------------------------------------------------------------------- cari global


def result_row(D, panel, x, y, w, title, meta, tk, dest=None, selected=False):
    bg = tk["active"] if selected else None
    r = D.frame(panel, x, y, w, 44, name=f"Hasil/{title[:24]}", fill=paint(bg) if bg else None,
                radii=[8, 8, 8, 8])
    D.text(r, 16, 12, w - 200, title, size=14,
           style="Semi Bold" if selected else "Regular", color=tk["text"])
    D.text(r, w - 190, 13, 174, meta, size=12, color=tk["text2"], align="right")
    if dest is not None:
        D.link(r, dest, ms=120)
    return r


def group_label(D, panel, x, y, label, tk):
    return D.text(panel, x, y, 560, label, size=12, style="Semi Bold", color=tk["text2"])


def build_search(D, page, host_id, x, y, tk, state, dests):
    root, m = D.clone(host_id)
    D.nodes[root]["name"] = f"Cari global / Light / Desktop / {state}"
    D.nodes[root]["parent"] = page
    D.nodes[root]["transform"] = [1.0, 0.0, 0.0, 1.0, float(x), float(y)]
    D.nodes[page]["children"].append(root)
    sh, sa = tk["scrim"]
    D.rect(root, 0, 0, 1440, 900, name="Scrim", fill=paint(sh, sa))
    H = {"awal": 340, "hasil": 640, "kosong": 260, "memuat": 220, "error": 260}.get(state, 400)
    if state == "hasil teknisi":
        H = 560
    panel = D.frame(root, 400, 120, 640, H, name="Palet pencarian", fill=paint(tk["surface"]),
                    strokes=[paint(tk["divider"])], radii=[12, 12, 12, 12], clip=True)
    # baris input
    icon = D.frame(panel, 24, 20, 20, 20, name="Icon/search")
    e = {"name": "Icon circle", "type": "ellipse", "start": 0.0, "sweep": 6.283185307179586,
         "inner": 0.0, "parent": icon, "blend": "normal",
         "transform": [1.0, 0.0, 0.0, 1.0, 2.0, 2.0], "width": 11.0, "height": 11.0,
         "strokes": [paint(tk["text2"])],
         "stroke": {"weight": 1.6, "align": "center", "sides": None, "cap_start": "none",
                    "cap_end": "none", "join": "miter", "miter_limit": 4.0, "dashes": []},
         "fills": []}
    ei = D.add(e)
    D.nodes[icon]["children"].append(ei)
    h2 = {"name": "Surface", "type": "rectangle", "parent": icon, "blend": "normal",
          "transform": [1.0, 0.0, 0.0, 1.0, 13.0, 13.0], "width": 5.0, "height": 2.0,
          "fills": [paint(tk["text2"])],
          "stroke": {"weight": 0.0, "align": "inside", "sides": None, "cap_start": "none",
                     "cap_end": "none", "join": "miter", "miter_limit": 4.0, "dashes": []},
          "corners": {"radii": [0.0] * 4, "smoothing": 0.0}}
    hi = D.add(h2)
    D.nodes[icon]["children"].append(hi)
    queries = {"awal": "", "hasil": "dd", "kosong": "zzz 999", "memuat": "dd", "error": "dd",
               "hasil teknisi": "dd"}
    q = queries[state]
    D.text(panel, 56, 20, 440, q if q else "Cari halaman, pelanggan, WO, invoice, jasa, part...",
           size=14, color=tk["text"] if q else tk["text2"])
    close = D.frame(panel, 556, 14, 60, 32, name="Tutup", fill=paint(tk["sidebar"]), radii=[6, 6, 6, 6])
    D.text(close, 0, 6, 60, "Esc", size=12, color=tk["text2"], align="center")
    D.link(close, dests["host"], ms=120)
    D.rect(panel, 24, 60, 592, 1, name="Divider", fill=paint(tk["divider"]))
    cy = 76
    if state == "awal":
        group_label(D, panel, 24, cy, "Sering dibuka", tk)
        cy += 24
        result_row(D, panel, 24, cy, 592, "Kasir", "Halaman", tk, dests["kasir"])
        cy += 48
        result_row(D, panel, 24, cy, 592, "Riwayat plat", "Halaman", tk, dests["riwayat"])
        cy += 48
        result_row(D, panel, 24, cy, 592, "DD 1248 KL  ·  Budi Santoso", "Kendaraan", tk, dests["riwayat"])
        cy += 60
        hint = result_row(D, panel, 24, cy, 592, "Coba contoh: \"dd\"", "Demo hasil", tk, dests["hasil"])
        cy += 60
        D.text(panel, 24, cy, 592,
               "Pencarian global mencakup lebih dari plat nomor. Hasil difilter peran (contoh: Kasir).",
               size=12, color=tk["text2"])
    elif state in ("hasil", "hasil teknisi"):
        teknisi = state == "hasil teknisi"
        group_label(D, panel, 24, cy, "Halaman", tk)
        cy += 24
        if teknisi:
            result_row(D, panel, 24, cy, 592, "Pekerjaan teknisi", "Halaman", tk, dests["pekerjaan"])
            cy += 48
            result_row(D, panel, 24, cy, 592, "Work order", "Halaman", tk, dests["board"])
            cy += 48
        else:
            result_row(D, panel, 24, cy, 592, "Kasir", "Halaman", tk, dests["kasir"])
            cy += 48
        group_label(D, panel, 24, cy, "Pelanggan & kendaraan", tk)
        cy += 24
        result_row(D, panel, 24, cy, 592, "DD 1248 KL  ·  Budi Santoso  ·  Toyota Avanza", "Kendaraan",
                   tk, dests["riwayat"], selected=True)
        cy += 48
        result_row(D, panel, 24, cy, 592, "DD 8921 AR  ·  Honda Brio Satya", "Kendaraan", tk, dests["riwayat"])
        cy += 48
        group_label(D, panel, 24, cy, "Work order", tk)
        cy += 24
        result_row(D, panel, 24, cy, 592, "WO-0268  ·  DD 1248 KL  ·  Menunggu", "WO", tk, dests["estimasi"])
        cy += 48
        if not teknisi:
            group_label(D, panel, 24, cy, "Invoice", tk)
            cy += 24
            result_row(D, panel, 24, cy, 592, "INV-0265  ·  Lunas", "Invoice", tk, dests["invoice_list"])
            cy += 48
        group_label(D, panel, 24, cy, "Jasa & part", tk)
        cy += 24
        if teknisi:
            result_row(D, panel, 24, cy, 592, "Filter kabin  ·  part", "Tanpa harga di pencarian", tk, dests["board"])
            cy += 48
            result_row(D, panel, 24, cy, 592, "Isi freon  ·  jasa", "Tanpa harga di pencarian", tk, dests["board"])
            cy += 60
            D.text(panel, 24, cy, 592,
                   "Hasil difilter untuk Teknisi: harga jual muncul di konteks WO yang diizinkan;\nnominal terbatas (HPP, pengeluaran) tidak ditampilkan.",
                   size=12, color=tk["text2"])
        else:
            result_row(D, panel, 24, cy, 592, "Filter kabin  ·  part  ·  Rp 85.000", "Master part", tk, dests["master"])
            cy += 48
            result_row(D, panel, 24, cy, 592, "Isi freon  ·  jasa  ·  Rp 150.000", "Master jasa", tk, dests["master"])
            cy += 60
            D.text(panel, 24, cy, 592,
                   "Baris pertama terpilih (latar biru): Enter membuka tujuan. Harga di snippet = harga jual; HPP tidak pernah tampil.",
                   size=12, color=tk["text2"])
    elif state == "kosong":
        D.text(panel, 24, cy + 24, 592, "Tidak ada hasil untuk \"zzz 999\"", size=16,
               style="Semi Bold", color=tk["text"], align="center")
        D.text(panel, 100, cy + 64, 440,
               "Periksa ejaan plat atau nomor dokumen.\nCari juga: nama pelanggan, WO, invoice, jasa, part, halaman.",
               size=13, color=tk["text2"], align="center")
        D.text(panel, 100, cy + 130, 440, "State tanpa hasil adalah contoh desain statis.",
               size=12, color=tk["text2"], align="center")
    elif state == "memuat":
        sp = D.frame(panel, 290, cy + 20, 20, 20, name="Spinner")
        D.add({"name": "Arc", "type": "ellipse", "start": 0.0, "sweep": 4.712, "inner": 0.0,
               "parent": sp, "blend": "normal", "transform": [1.0, 0.0, 0.0, 1.0, 0.0, 0.0],
               "width": 20.0, "height": 20.0, "strokes": [paint(tk["action"])],
               "stroke": {"weight": 2.0, "align": "center", "sides": None, "cap_start": "round",
                          "cap_end": "round", "join": "miter", "miter_limit": 4.0, "dashes": []},
               "fills": []})
        D.nodes[sp]["children"].append(D.next - 1)
        D.text(panel, 24, cy + 56, 592, "Mencari hasil untuk \"dd\"...", size=14, color=tk["text"],
               align="center")
        D.text(panel, 24, cy + 88, 592, "State memuat adalah contoh desain statis.", size=12,
               color=tk["text2"], align="center")
    elif state == "error":
        D.text(panel, 24, cy + 16, 592, "Pencarian gagal", size=16, style="Semi Bold",
               color=tk["err"], align="center")
        D.text(panel, 100, cy + 52, 440,
               "Koneksi offline dan data lokal belum tersinkron.\nSambungkan kembali, lalu ulangi pencarian.",
               size=13, color=tk["text"], align="center")
        D.button(panel, 250, cy + 116, 140, 44, "Coba lagi", tk, "primary", dests["hasil"], ms=120)
    return root


# ----------------------------------------------------------------------------- patch existing


def patch_cari_kendaraan(D, page, teknisi_roots, dest_awal, dest_teknisi):
    n_patch = 0
    for i, n in list(D.nodes.items()):
        if n.get("name") != "Cari kendaraan" or not n.get("interactions"):
            continue
        root = D.root_of(i)
        if D.nodes[root].get("parent") != page:
            continue
        dest = dest_teknisi if root in teknisi_roots else dest_awal
        for it in n["interactions"]:
            it["trigger"] = {"type": "onClick"}
            it["actions"] = [{"type": "navigate", "dest": dest}]
            it["transition"] = {"type": "dissolve"}
            it["duration_ms"] = D.dur(160)
            it["easing"] = "easeOut"
            n_patch += 1
    return n_patch


def add_topbar_buttons(D, frame_id, tk, pairs):
    """pairs: (label, x, dest). Tombol secondary 44px di area topbar."""
    ids = []
    for label, x, dest in pairs:
        b = D.button(frame_id, x, 14, 180, 44, label, tk, "secondary", dest)
        ids.append(b)
    return ids


# ----------------------------------------------------------------------------- main


def main():
    from complete_ui04 import build
    build(sys.argv[1], sys.argv[2], "--no-motion" not in sys.argv)


def legacy_main():
    src, out = sys.argv[1], sys.argv[2]
    motion = "--no-motion" not in sys.argv
    d = load(src)
    D = Doc(d, motion)
    pages = d["pages"]
    P_DL, P_ML, P_DD, P_MD, P_INV = pages[0], pages[1], pages[2], pages[3], pages[4]
    tkL, tkD = TOKENS["light"], TOKENS["dark"]

    renamed = rename_phase(D)

    def F(name):
        return D.find(name)

    detail_L = F("Detail work order / Light / Desktop / base")
    board_L = F("Work order / Light / Desktop / base")
    kasir_L = F("Kasir / Light / Desktop / base")
    kasir_D = F("Kasir / Dark / Desktop / base")
    ringk_L = F("Ringkasan / Light / Desktop / base")
    invoice_L = F("Invoice / Light / Desktop / base")
    master_L = F("Jasa dan Part / Light / Desktop / base")
    riwayat_L = F("Riwayat plat / Light / Desktop / base")
    pekerjaan_L = F("Pekerjaan teknisi / Light / Desktop / base")
    pekerjaan_started = F("Pekerjaan teknisi / Light / Desktop / started")
    pekerjaan_done = F("Pekerjaan teknisi / Light / Desktop / completed")
    teknisi_L = F("Teknisi / Light / Desktop / base")
    teknisi_Lc = F("Teknisi / Light / Desktop / collapsed")
    kondisi_L = F("Kondisi antarmuka / Light / Desktop / base")
    ringk_ML = F("Ringkasan / Light / Mobile / base")
    kasir_ML = F("Kasir / Light / Mobile / base")
    teknisi_ML = F("Teknisi / Light / Mobile / base")
    ringk_DD = F("Ringkasan / Dark / Desktop / base")
    teknisi_DD = F("Teknisi / Dark / Desktop / base")
    ringk_MD = F("Ringkasan / Dark / Mobile / base")
    kasir_MD = F("Kasir / Dark / Mobile / base")
    teknisi_MD = F("Teknisi / Dark / Mobile / base")

    # ---- posisi frame baru: satu baris di bawah konten existing per halaman
    posL, _ = place_frames(D, P_DL, 14, 1440, 900)
    posML, _ = place_frames(D, P_ML, 1, 390, 844)
    posDD, _ = place_frames(D, P_DD, 2, 1440, 900)
    posMD, _ = place_frames(D, P_MD, 1, 390, 844)
    it = iter(posL)
    p_shellL = next(it); p_audit = next(it); p_koreksi = next(it); p_final = next(it)
    p_draft = next(it); p_est = next(it); p_gal = next(it); p_loginDL = next(it)
    p_hasil = next(it); p_hasilT = next(it); p_kosong = next(it); p_memuat = next(it)
    p_error = next(it); p_awal = next(it)

    # ---- shell kasir terbatas (light untuk journey + dark untuk login dark)
    shellL = build_kasir_shell(D, P_DL, kasir_L, "Light", *p_shellL)
    shellD = build_kasir_shell(D, P_DD, kasir_D, "Dark", *posDD[1])

    # ---- frame fitur (urutan menghormati dependensi destinasi)
    audit = build_audit(D, P_DL, *p_audit, detail_L, tkL, ringk_L)
    koreksi, btn_batal = build_koreksi(D, P_DL, *p_koreksi, detail_L, tkL, audit, None)
    final = build_invoice_final(D, P_DL, *p_final, detail_L, tkL, koreksi, audit, invoice_L)
    D.link(btn_batal, final, ms=180)
    draft = build_invoice_draft(D, P_DL, *p_draft, detail_L, tkL, final, kasir_L)
    est = build_estimasi(D, P_DL, *p_est, detail_L, tkL, board_L, draft)
    gallery = build_gallery(D, P_DL, *p_gal, tkL)

    # ---- login 4 varian
    loginDL = build_login(D, P_DL, *p_loginDL, tkL, "desktop",
                          {"owner": ringk_L, "kasir": shellL, "teknisi": teknisi_L})
    loginML = build_login(D, P_ML, *posML[0], tkL, "mobile",
                          {"owner": ringk_ML, "kasir": kasir_ML, "teknisi": teknisi_ML})
    loginDD = build_login(D, P_DD, *posDD[0], tkD, "desktop",
                          {"owner": ringk_DD, "kasir": shellD, "teknisi": teknisi_DD})
    loginMD = build_login(D, P_MD, *posMD[0], tkD, "mobile",
                          {"owner": ringk_MD, "kasir": kasir_MD, "teknisi": teknisi_MD})

    # ---- cari global (light desktop; host = shell kasir / papan teknisi)
    dests_kasir = {"host": shellL, "kasir": shellL, "riwayat": riwayat_L, "estimasi": est,
                   "invoice_list": invoice_L, "master": master_L, "board": board_L,
                   "pekerjaan": pekerjaan_L, "hasil": None}
    hasil = build_search(D, P_DL, shellL, *p_hasil, tkL, "hasil", dests_kasir)
    dests_kasir["hasil"] = hasil
    dests_tek = {"host": teknisi_L, "kasir": shellL, "riwayat": riwayat_L, "estimasi": est,
                 "invoice_list": invoice_L, "master": master_L, "board": board_L,
                 "pekerjaan": pekerjaan_L, "hasil": hasil}
    hasilT = build_search(D, P_DL, teknisi_L, *p_hasilT, tkL, "hasil teknisi", dests_tek)
    kosong = build_search(D, P_DL, shellL, *p_kosong, tkL, "kosong", dests_kasir)
    memuat = build_search(D, P_DL, shellL, *p_memuat, tkL, "memuat", dests_kasir)
    error = build_search(D, P_DL, shellL, *p_error, tkL, "error", dests_kasir)
    awal = build_search(D, P_DL, shellL, *p_awal, tkL, "awal", dests_kasir)

    # ---- patch frame existing (additif)
    add_topbar_buttons(D, ringk_L, tkL,
                       [("Audit log (Owner)", 860, audit), ("Koreksi invoice (demo)", 1052, final)])
    D.button(pekerjaan_L, 1148, 344, 260, 44, "Buka estimasi (harga jual)", tkL, "secondary", est)

    teknisi_roots = {teknisi_L, teknisi_Lc, pekerjaan_L, pekerjaan_started, pekerjaan_done, hasilT}
    n_cari = patch_cari_kendaraan(D, P_DL, teknisi_roots, awal, hasilT)

    # ---- flows
    def add_flow(page, name, start):
        D.nodes[page].setdefault("flows", []).append({"name": name, "start": start, "description": ""})

    add_flow(P_DL, "Login Desktop Light", loginDL)
    add_flow(P_DL, "Kasir Desktop Light", shellL)
    add_flow(P_DL, "Estimasi dan Invoice Light", est)
    add_flow(P_DL, "Cari Global Light", awal)
    add_flow(P_DL, "State Interaksi Light", gallery)
    add_flow(P_ML, "Login Mobile Light", loginML)
    add_flow(P_DD, "Login Desktop Dark", loginDD)
    add_flow(P_DD, "Kasir Desktop Dark", shellD)
    add_flow(P_MD, "Login Mobile Dark", loginMD)

    doc = D.save()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False)
    print(json.dumps({
        "renamed_fields": renamed, "cari_patched": n_cari, "next_id": D.next,
        "nodes": len(D.nodes), "motion": motion,
        "new_frames": {"shellL": shellL, "shellD": shellD, "audit": audit, "koreksi": koreksi,
                       "final": final, "draft": draft, "est": est, "gallery": gallery,
                       "loginDL": loginDL, "loginML": loginML, "loginDD": loginDD,
                       "loginMD": loginMD, "hasil": hasil, "hasilT": hasilT, "kosong": kosong,
                       "memuat": memuat, "error": error, "awal": awal},
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
