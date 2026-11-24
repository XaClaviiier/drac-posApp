"""Complete UI-04 on a native snapshot; preserve the existing document and assets."""

import copy
import json
import math
import re
import zipfile
from pathlib import Path

from build_ui04 import Doc, TOKENS, EST_ROWS, TOTAL_EST, DIBAYAR, TOTAL_KOREKSI, paint, rp, rename_phase, build_gallery


ROLES = ("Owner", "Teknisi", "Kasir")
VARIANTS = (("Light", "Desktop"), ("Light", "Mobile"), ("Dark", "Desktop"), ("Dark", "Mobile"))
ROUTES = {
    "Owner": ("home", "wo", "before", "edit", "draft", "draft-edit", "final", "correction", "revised", "raised", "audit", "master", "payment", "paid", "reception", "history", "search", "results", "empty", "loading", "error"),
    "Teknisi": ("home", "wo", "before", "edit", "draft", "draft-edit", "final", "reception", "history", "search", "results", "empty", "loading", "error"),
    "Kasir": ("home", "wo", "draft", "final", "payment", "paid", "reception", "history", "search", "results", "empty", "loading", "error"),
}
TITLES = {"home": "Ruang kerja", "wo": "Estimasi work order", "before": "Harga awal work order", "edit": "Ubah harga WO", "draft": "Invoice draf", "draft-edit": "Ubah harga invoice draf", "final": "Invoice final", "correction": "Koreksi invoice final", "revised": "Invoice revisi", "raised": "Sisa tagihan setelah koreksi", "audit": "Audit perubahan harga", "master": "Harga master dan HPP", "payment": "Terima pembayaran", "paid": "Pembayaran tercatat", "reception": "Nota servis dan diagnosa", "history": "Riwayat kendaraan", "search": "Cari di bengkel", "results": "Hasil pencarian", "empty": "Pencarian tanpa hasil", "loading": "Pencarian sedang dimuat", "error": "Pencarian gagal"}
TITLES["draft-after"] = "Invoice draf setelah edit"
TITLES.update(started="Pekerjaan sedang berjalan", completed="Pekerjaan selesai")
ROUTES["Teknisi"] += ("started", "completed")
ROUTES["Owner"] += ("correction-paid", "revised-paid", "payment-raised", "paid-raised", "correction-paid-raised", "revised-paid-raised")
TITLES.update({"correction-paid": "Koreksi invoice lunas", "revised-paid": "Revisi invoice lunas", "payment-raised": "Pembayaran invoice revisi", "paid-raised": "Invoice revisi lunas", "correction-paid-raised": "Koreksi revisi yang lunas", "revised-paid-raised": "Hasil koreksi revisi lunas"})


def walk(D, root):
    yield root
    for child in D.nodes[root].get("children", []):
        yield from walk(D, child)


def meta(D, node, **values):
    D.nodes[node].setdefault("plugin_data", {})["pos.ui04"] = json.dumps(values, ensure_ascii=False)


class Screen:
    def __init__(self, D, page, theme, device, role, route, index, targets):
        self.D, self.tk, self.role, self.route = D, TOKENS[theme.lower()], role, route
        self.theme, self.device, self.targets = theme, device, targets
        self.mobile = device == "Mobile"
        self.w, self.h = (390, 844) if self.mobile else (1440, 1000)
        self.root = targets[(theme, device, role, route)]
        self.x, self.width = (16, 358) if self.mobile else (280, 1120)
        self.y = 24
        self.body = D.frame(self.root, self.x, 202 if self.mobile else 112,
                            self.width, 618 if self.mobile else 864, "Contenu défilant", clip=True)
        D.nodes[self.body]["name"] = "Konten / gulir vertikal"
        D.nodes[self.body]["overflow"] = "vertical"
        self.draw_chrome()
        if route in ("search", "results", "empty", "loading", "error"):
            scrim, alpha = self.tk["scrim"]
            D.rect(self.root, 0, 0, self.w, self.h, "Scrim pencarian", paint(scrim, alpha))
            self.width = 358 if self.mobile else 640
            self.body = D.frame(self.root, 16 if self.mobile else 400, 80, self.width,
                                self.h - 112, "Palet pencarian global", fill=paint(self.tk["surface"]),
                                strokes=[paint(self.tk["input"])], radii=[12]*4, clip=True)
            D.nodes[self.body]["overflow"] = "vertical"
            self.width -= 40
            inner = D.frame(self.body, 20, 64, self.width, self.h - 192, "Hasil / gulir vertikal", clip=True)
            D.nodes[inner]["overflow"] = "vertical"
            self.button("Tutup", "home", parent=self.body, x=self.width - 80, y=8, width=100)
            D.text(self.body, 20, 22, self.width - 110, "Pencarian global", 16, "Semi Bold", self.tk["text"])
            self.body = inner
            self.y = 0

    def text(self, value, size=14, color=None, bold=False, parent=None, x=0, y=None, width=None):
        p = self.body if parent is None else parent
        yy = self.y if y is None else y
        ww = self.width if width is None else width
        nid = self.D.text(p, x, yy, ww, value, size, "Semi Bold" if bold else "Regular",
                          color or self.tk["text"])
        if y is None:
            self.y += self.D.nodes[nid]["height"] + 12
        return nid

    def dest(self, route, role=None, theme=None):
        return self.targets[(theme or self.theme, self.device, role or self.role, route)]

    def button(self, label, route=None, kind="secondary", dest=None, width=None, parent=None, x=0, y=None):
        yy = self.y if y is None else y
        p = self.body if parent is None else parent
        ww = width or (self.width if self.mobile else min(360, self.width))
        target = dest if dest is not None else self.dest(route)
        nid = self.D.button(p, x, yy, ww, 48, label, self.tk, kind, target, ms=160)
        if kind in ("nav", "result"):
            node = self.D.nodes[nid]
            node["fills"] = [paint(self.tk["active"])] if route == self.route else []
            node["strokes"] = []
            for c in node.get("children", []):
                tx = self.D.nodes[c]
                tx["align_h"] = "left"
                tx["transform"][4] = 16.0
                tx["width"] = ww - 32
                tx["fills"] = [paint(self.tk["text"])]
        if y is None:
            self.y += 60
        return nid

    def panel(self, heading, lines, tint=None):
        color = self.tk["warn"] if tint else self.tk["text"]
        inner_w = self.width - 40
        height = 64 + sum(max(1, math.ceil(len(s) * 14 * .57 / inner_w)) * 21 + 8 for s in lines)
        p = self.D.frame(self.body, 0, self.y, self.width, height, heading,
                        fill=paint(self.tk["warn_bg"] if tint else self.tk["surface"]),
                        strokes=[paint(self.tk["divider"])], radii=[12] * 4)
        self.D.text(p, 20, 16, inner_w, heading, 16, "Semi Bold", color)
        yy = 48
        for s in lines:
            n = self.D.text(p, 20, yy, inner_w, s, 14, color=color)
            yy += self.D.nodes[n]["height"] + 8
        self.y += height + 20
        return p

    def field(self, label, value, route):
        self.text(label, 12, self.tk["text2"], True)
        b = self.button(value, route)
        self.D.nodes[b]["name"] = "Field/" + label
        return b

    def draw_chrome(self):
        D, tk = self.D, self.tk
        if not self.mobile:
            side = D.frame(self.root, 0, 0, 248, self.h, "Sidebar", fill=paint(tk["sidebar"]))
            D.text(side, 24, 28, 200, "Dokter AC Mobil", 20, "Semi Bold", tk["text"])
            D.text(side, 24, 68, 200, "Demo " + self.role, 13, color=tk["text2"])
            self.button("Cari di bengkel...", "search", parent=side, x=16, y=108, width=216)
            menu = [("Ruang kerja", "home"), ("Nota dan diagnosa", "reception"), ("Work order", "wo"), ("Invoice draf", "draft"), ("Invoice final", "final"), ("Riwayat kendaraan", "history")]
            if self.role in ("Owner", "Kasir"):
                menu.append(("Pembayaran", "payment"))
            if self.role == "Owner":
                menu += [("Harga master / HPP", "master"), ("Audit perubahan harga", "audit")]
            for j, (label, route) in enumerate(menu):
                self.button(label, route, kind="nav", parent=side, x=16, y=180 + j * 58, width=216)
            self.button("Keluar demo", dest=self.targets[(self.theme, self.device, "Login", "base")], parent=side, x=16, y=self.h - 80, width=216)
            D.text(self.root, 280, 24, 810, TITLES[self.route], 28, "Semi Bold", tk["text"])
            D.text(self.root, 280, 70, 750, self.role + " / Data contoh / Simulasi desain", 12, color=tk["text2"])
            self.button("Ganti tema", dest=self.dest(self.route, theme="Dark" if self.theme == "Light" else "Light"), parent=self.root, x=1210, y=24, width=190)
        else:
            title = {"raised": "Sisa tagihan revisi", "draft-after": "Draf setelah edit", "correction-paid-raised": "Koreksi revisi lunas", "revised-paid-raised": "Hasil koreksi revisi", "payment-raised": "Bayar invoice revisi", "started": "Pekerjaan berlangsung"}.get(self.route, TITLES[self.route])
            D.text(self.root, 16, 18, 252, title, 18, "Semi Bold", tk["text"])
            self.button("Tema", dest=self.dest(self.route, theme="Dark" if self.theme == "Light" else "Light"), parent=self.root, x=282, y=14, width=92)
            D.text(self.root, 16, 58, 358, self.role + " / Data contoh / Gulir isi ke bawah", 12, color=tk["text2"])
            for j, (label, route) in enumerate((("Beranda", "home"), ("WO", "wo"), ("Invoice", "final"))):
                self.button(label, route, parent=self.root, x=16 + j * 122, y=86, width=114)
            self.button("Cari di bengkel...", "search", parent=self.root, x=16, y=144, width=240)
            self.button("Keluar", dest=self.targets[(self.theme, self.device, "Login", "base")], parent=self.root, x=268, y=144, width=106)

    def rows(self, before=False, invoice_edit=False, corrected=False):
        rows = []
        for typ, item, qty, unit, price, subtotal, original in EST_ROWS:
            if corrected and item == "Kuras evaporator":
                continue
            if before and original:
                price = original
            if invoice_edit and item == "Isi freon":
                price = 140000
            rows.append((typ, item, int(qty), unit, price, int(qty) * price))
        if not self.mobile:
            for x, w, val, align in ((16, 430, "Jenis / jasa atau barang", None), (460, 120, "Jumlah", None), (600, 230, "Harga jual satuan", "right"), (850, 250, "Subtotal", "right")):
                self.D.text(self.body, x, self.y, w, val, 13, "Semi Bold", self.tk["text2"], align=align)
            self.y += 32
        for typ, item, qty, unit, price, total in rows:
            if self.mobile:
                p = self.panel(item, [f"{typ} / {qty} {unit}", f"Harga satuan: {rp(price)}", f"Subtotal: {rp(total)}"])
            else:
                p = self.D.frame(self.body, 0, self.y, self.width, 58, "Line/" + item, fill=paint(self.tk["surface"]))
                for x, w, val, align in ((16, 430, typ + " / " + item, None), (460, 120, f"{qty} {unit}", None), (600, 230, rp(price), "right"), (850, 250, rp(total), "right")):
                    self.D.text(p, x, 18, w, val, 14, color=self.tk["text"], align=align)
                self.D.rect(p, 0, 57, self.width, 1, fill=paint(self.tk["divider"]))
                self.y += 66
            meta(self.D, p, kind="line", item=item, category=typ, quantity=qty, unit_price=price, subtotal=total)
        jasa = sum(row[5] for row in rows if row[0] == "Jasa")
        barang = sum(row[5] for row in rows if row[0] == "Part")
        total = jasa + barang
        p = self.panel("Ringkasan harga jual", ["Subtotal jasa: " + rp(jasa), "Subtotal barang: " + rp(barang), "Total: " + rp(total)])
        meta(self.D, p, kind="totals", jasa=jasa, barang=barang, total=total)
        return total

    def contents(self):
        r, role = self.route, self.role
        r = {"correction-paid": "correction", "correction-paid-raised": "correction", "revised-paid": "revised", "revised-paid-raised": "revised", "payment-raised": "payment", "paid-raised": "paid"}.get(r, r)
        if r in ("home", "started", "completed"):
            self.text({"Owner": "Pantau pekerjaan dan tagihan", "Teknisi": "Pekerjaan Teknisi", "Kasir": "Tagihan siap diperiksa"}[role], 24, bold=True)
            self.panel("DD 1248 KL", ["Toyota Avanza / WO-0268 / Budi Santoso", "AC kurang dingin. Tinjau diagnosa dan rincian pekerjaan."])
            if role == "Teknisi":
                status = {"home": "Menunggu", "started": "Dalam pengerjaan", "completed": "Selesai"}[r]
                self.text("Status pekerjaan: " + status, bold=True)
                if r != "completed":
                    self.button("Mulai pekerjaan (demo)" if r == "home" else "Tandai selesai (demo)", "started" if r == "home" else "completed", "primary")
            self.button("Buka work order", "wo", "primary")
            self.button("Nota dan diagnosa", "reception")
            self.button("Buka invoice draf", "draft")
            self.button("Riwayat kendaraan", "history")
            if role in ("Owner", "Kasir"):
                self.button("Terima pembayaran", "payment")
            if role == "Owner":
                self.button("Harga master dan HPP", "master")
                self.button("Audit perubahan harga", "audit")
        elif r == "reception":
            self.text("Nota servis NS-0268", 22, bold=True)
            self.panel("Pelanggan dan kendaraan", ["Budi Santoso / DD 1248 KL / Toyota Avanza 1.3"])
            self.panel("Diagnosa", ["Keluhan: AC kurang dingin.", "Temuan: tekanan freon rendah; periksa evaporator dan filter kabin.", "Rekomendasi: isi freon, kuras evaporator, ganti filter kabin.", "Diagnosa menjelaskan temuan. WO merinci pekerjaan, barang, dan estimasi."])
            self.button("Lihat work order terhubung", "wo", "primary")
        elif r in ("wo", "before"):
            self.text("WO-0268 / DD 1248 KL", 22, bold=True)
            if role in ("Owner", "Teknisi"):
                self.button("Ubah harga Filter kabin", "edit", "primary")
            self.panel("Diagnosa terhubung NS-0268", ["AC kurang dingin; tekanan freon rendah.", "Isi freon, kuras evaporator, ganti filter kabin."])
            self.rows(before=r == "before")
            self.panel("Harga khusus transaksi", ["Master Filter kabin tetap Rp 85.000 per pcs.", "Harga WO awal Rp 85.000; setelah edit lokal Rp 80.000 per pcs.", "Master dan dokumen lain tidak ikut berubah. Semua nominal contoh."], tint=True)
            if role in ("Owner", "Teknisi"):
                self.button("Lihat sebelum perubahan", "before")
            self.button("Tinjau invoice dari WO", "draft")
            self.button("Kembali ke pekerjaan", "home")
        elif r in ("edit", "draft-edit"):
            invoice = r == "draft-edit"
            self.text("Harga hanya untuk dokumen ini", 22, bold=True)
            self.panel("Isi freon" if invoice else "Filter kabin", ["Dokumen: INV-0268 draf" if invoice else "Dokumen: WO-0268", "Harga master: Rp 150.000" if invoice else "Harga master: Rp 85.000", "Harga baru contoh: Rp 140.000" if invoice else "Harga baru contoh: Rp 80.000", "Alasan contoh: penyesuaian paket servis."])
            self.field("Harga jual satuan (simulasi)", "Rp 140.000" if invoice else "Rp 80.000", r)
            self.field("Alasan perubahan (contoh desain)", "Penyesuaian paket servis", r)
            self.button("Simpan perubahan (demo)", "draft-after" if invoice else "wo", "primary")
            self.text("Log lengkap hanya Owner. Perubahan tidak memperbarui harga master.", color=self.tk["text2"])
            self.button("Batal", "draft" if invoice else "before")
        elif r == "draft":
            self.text("INV-0268 / Draf", 22, bold=True)
            self.text("DD 1248 KL / Budi Santoso / sumber WO-0268", color=self.tk["text2"])
            self.rows()
            self.panel("Harga dari WO", ["Rincian memakai snapshot harga WO, bukan mengambil ulang master.", "Teknisi boleh edit harga draf. Invoice final hanya dapat dikoreksi Owner."])
            if role in ("Owner", "Teknisi"):
                self.button("Ubah harga jasa di draf", "draft-edit")
                self.button("Lihat draf setelah edit", "draft-after")
            self.button("Lihat invoice final (demo)", "final", "primary")
            self.button("Kembali ke WO", "wo")
        elif r == "draft-after":
            self.text("INV-0268 / Draf setelah edit lokal", 22, bold=True)
            self.rows(invoice_edit=True)
            self.panel("WO dan master tetap", ["WO-0268 tetap Rp 780.000. Invoice draf contoh menjadi Rp 770.000.", "Master Isi freon tetap Rp 150.000. Harga draf Rp 140.000."])
            self.button("Kembali ke draf awal (demo)", "draft")
        elif r in ("final", "revised", "raised", "paid"):
            revised = r == "revised"
            paid = r == "paid"
            self.text("INV-0268 / " + ("Revisi 1" if revised or r == "raised" else "Final terkunci"), 22, bold=True)
            total = self.rows(corrected=revised)
            extra = self.route in ("raised", "paid-raised", "revised-paid-raised")
            if extra:
                total += 50000
                p = self.panel("Tambahan jasa contoh", ["Pemeriksaan lanjutan: Rp 50.000", "Total revisi: " + rp(total)])
                meta(self.D, p, kind="adjustment", amount=50000, total=total)
            received = 830000 if self.route in ("paid-raised", "revised-paid-raised") else TOTAL_EST if paid or self.route == "revised-paid" else DIBAYAR
            balance = total - received
            label = "Kelebihan bayar" if balance < 0 else "Sisa tagihan" if balance > 0 else "Sisa tagihan (lunas)"
            p = self.panel("Riwayat pembayaran tetap", ["Diterima Kasir: " + rp(received) + " / tunai / data contoh", label + ": " + rp(abs(balance)), "Koreksi bukan refund otomatis. Pengembalian uang dicatat terpisah."])
            meta(self.D, p, kind="payment", received=received, invoice_total=total, balance=balance)
            self.text("Invoice final tidak dapat diubah Teknisi atau Kasir.", color=self.tk["text2"])
            if role == "Owner":
                correction = "correction-paid-raised" if self.route in ("paid-raised", "revised-paid-raised") else "correction-paid" if paid or self.route == "revised-paid" else "correction"
                if r in ("final", "paid"):
                    self.button("Koreksi invoice (Owner)", correction, "primary")
                self.button("Audit perubahan harga", "audit")
            if role in ("Owner", "Kasir") and not paid and not revised:
                self.button("Terima pembayaran", "payment-raised" if r == "raised" else "payment")
            self.button("Kembali ke ruang kerja", "home")
        elif r == "correction":
            self.text("Hanya Owner / INV-0268", 22, bold=True)
            raised = self.route == "correction-paid-raised"
            received = 830000 if raised else 780000 if self.route == "correction-paid" else 500000
            old, new = (830000, 480000) if raised else (780000, 430000)
            self.panel("Koreksi contoh", ["Kuras evaporator Rp 350.000 dibatalkan pelanggan.", f"Total awal {rp(old)}; total baru {rp(new)}.", f"Pembayaran {rp(received)} tetap. Kelebihan bayar {rp(received - new)}."])
            self.field("Alasan koreksi (contoh desain)", "Kuras evaporator dibatalkan pelanggan", self.route)
            self.button("Simpan revisi penurunan (demo)", "revised-paid-raised" if raised else "revised-paid" if self.route == "correction-paid" else "revised", "primary")
            if self.route == "correction":
                self.button("Contoh koreksi tambahan jasa", "raised")
            self.button("Batal", "paid-raised" if raised else "paid" if self.route == "correction-paid" else "final")
        elif r == "audit":
            self.text("Audit hanya Owner", 22, bold=True)
            self.panel("31 Okt 2026 / Teknisi Andi", ["WO-0268 / Filter kabin / Rp 85.000 menjadi Rp 80.000 per pcs.", "Alasan: penyesuaian paket servis. Master tetap Rp 85.000."])
            self.panel("31 Okt 2026 / Teknisi Andi", ["INV-0268 draf / Isi freon / Rp 150.000 menjadi Rp 140.000.", "WO asal dan master tidak berubah. Skenario demo edit draf terpisah."])
            self.panel("31 Okt 2026 / Owner", ["INV-0268 / Rp 780.000 menjadi Rp 430.000.", "Alasan: kuras evaporator dibatalkan pelanggan.", "Uang diterima Rp 500.000 tidak ditulis ulang. Riwayat revisi dipertahankan."])
            self.button("Lihat invoice revisi", "revised", "primary")
            self.button("Harga master dan HPP", "master")
        elif r == "master":
            self.text("Data master / hanya Owner", 22, bold=True)
            p = self.panel("Filter kabin", ["Harga jual master: Rp 85.000 / pcs", "HPP contoh: Rp 50.000 / pcs", "Harga WO contoh Rp 80.000 tidak mengubah master."])
            meta(self.D, p, kind="master", price=85000, cost=50000)
            self.panel("Biaya operasional", ["Pengeluaran contoh Rp 100.000. Nilai ini tidak ditampilkan kepada Teknisi/Kasir."])
            self.button("Audit log", "audit")
        elif r == "history":
            self.text("Riwayat DD 1248 KL", 22, bold=True)
            self.panel("Budi Santoso / Toyota Avanza", ["Nota servis NS-0268", "Work order WO-0268", "Invoice INV-0268. Data contoh untuk kendaraan yang sama."])
            self.button("Buka diagnosa", "reception")
            self.button("Buka WO-0268", "wo")
            self.button("Buka INV-0268", "final")
        elif r == "payment":
            self.text("Pembayaran hanya Kasir / Owner", 22, bold=True)
            total = 830000 if self.route == "payment-raised" else 780000
            self.panel("INV-0268 / DD 1248 KL", ["Total " + rp(total), "Sudah diterima Rp 500.000", "Contoh pembayaran sisa " + rp(total - 500000) + " / tunai."])
            self.button("Konfirmasi pembayaran (demo)", "paid-raised" if self.route == "payment-raised" else "paid", "primary")
            self.text("Simulasi antar-frame. Tidak menerima atau memindahkan uang.", color=self.tk["text2"])
            self.button("Batal", "raised" if self.route == "payment-raised" else "final")
        else:
            self.search()

    def search(self):
        r = self.route
        self.text("Cari halaman, pelanggan, WO, invoice, jasa atau barang.", color=self.tk["text2"])
        # Search icon is geometry, not a Unicode substitute.
        field = self.button("Cari di bengkel..." if r == "search" else "Contoh: Filter kabin", "results")
        self.D.nodes[field]["name"] = "GlobalSearchInput"
        self.D.rect(field, 14, 14, 16, 16, fill=None, stroke=paint(self.tk["text2"]), radii=[8] * 4)
        self.D.rect(field, 29, 29, 7, 2, fill=paint(self.tk["text2"]))
        if r in ("search", "results"):
            if r == "search":
                self.text("Saran / pilih hasil demo", 12, self.tk["text2"], True)
            else:
                self.text("Semua kategori berikut adalah contoh skenario hasil, bukan query live.", 12, self.tk["text2"])
            for group, items in (("Halaman", [("Ruang kerja " + self.role, "home")]), ("Pelanggan / kendaraan", [("Budi Santoso / DD 1248 KL", "history")]), ("Work order", [("WO-0268 / DD 1248 KL", "wo")]), ("Invoice", [("INV-0268 / DD 1248 KL", "final")]), ("Jasa / barang", [("Filter kabin / lihat rincian pada WO", "wo"), ("Isi freon / lihat rincian pada WO", "wo")])):
                self.text(group, 12, self.tk["text2"], True)
                for label, dest in items:
                    self.button(label, dest, "result", width=self.width)
            self.text("Hasil mengikuti peran. Harga jual ditampilkan pada WO/invoice yang diizinkan.", 12, self.tk["text2"])
            self.button("Contoh tanpa hasil", "empty")
            self.button("Contoh memuat", "loading")
            self.button("Contoh gagal", "error")
        elif r == "empty":
            self.panel("Tidak ada hasil", ["Kata contoh: zzz 999", "Coba nama pelanggan, nomor WO/invoice, jasa atau barang."])
            self.button("Ganti pencarian (demo)", "search", "primary")
        elif r == "loading":
            self.panel("Sedang mencari...", ["Contoh state memuat. Tidak ada permintaan jaringan berjalan."])
            self.button("Lihat hasil demo", "results")
        else:
            self.panel("Pencarian gagal", ["Contoh data belum tersedia. Coba lagi atau kembali ke ruang kerja."], tint=True)
            self.button("Coba lagi (demo)", "results", "primary")
        self.button("Tutup pencarian", "home")


def create_routes(D, pages):
    targets = {}
    for theme, device in VARIANTS:
        page = pages[(theme, device)]
        mobile = device == "Mobile"
        width, height = (390, 844) if mobile else (1440, 1000)
        bottom = max(D.nodes[c].get("transform", [0]*6)[5] + D.nodes[c].get("height", 0)
                     for c in D.nodes[page].get("children", [])) + 320
        specs = [("Login", s) for s in ("base", "invalid", "loading", "error", "password")]
        for role in ROLES:
            routes = list(ROUTES[role])
            if role in ("Owner", "Teknisi"):
                routes.append("draft-after")
            specs.extend((role, r) for r in routes)
        for j, (role, route) in enumerate(specs):
            root = D.frame(page, (j % 5) * (width + 120), bottom + (j // 5) * (height + 200), width, height,
                           f"UI04 / {theme} / {device} / {role} / {route}", fill=paint(TOKENS[theme.lower()]["canvas"]), top=True)
            targets[(theme, device, role, route)] = root
            meta(D, root, kind="screen", theme=theme, device=device, role=role, route=route)
    return targets


def login(D, targets, theme, device, state):
    tk = TOKENS[theme.lower()]
    root = targets[(theme, device, "Login", state)]
    mobile = device == "Mobile"
    x, y, w = (24, 140, 342) if mobile else (760, 110, 440)
    if not mobile:
        D.frame(root, 0, 0, 600, 1000, "Identitas bengkel", fill=paint(tk["sidebar"]))
        D.text(root, 64, 370, 460, "Dokter AC Mobil", 32, "Semi Bold", tk["text"])
        D.text(root, 64, 430, 460, "Dari diagnosa ke pekerjaan dan tagihan.", 18, color=tk["text2"])
    else:
        D.text(root, 24, 54, 342, "Dokter AC Mobil", 26, "Semi Bold", tk["text"])
    D.text(root, x, y, w, "Masuk ke ruang kerja", 24, "Semi Bold", tk["text"])
    D.text(root, x, y + 46, w, "Login simulasi. Akun dan data di sini contoh.", 12, color=tk["text2"])
    for j, (label, value) in enumerate((("Username", "teknisi.demo"), ("Password", "[password contoh]" if state == "password" else "••••••••"))):
        yy = y + 100 + j * 98
        D.text(root, x, yy, w, label, 13, "Medium", tk["text2"])
        f = D.frame(root, x, yy + 26, w, 48, "Field/" + label, fill=paint(tk["surface"]), strokes=[paint(tk["input"])], radii=[8]*4)
        D.text(f, 16, 12, w - 32, value, 14, color=tk["text"])
        D.link(f, targets[(theme, device, "Login", "password" if j else "base")], ms=120)
    D.button(root, x, y + 296, w, 48, "Sembunyikan password (demo)" if state == "password" else "Tampilkan password (demo)", tk, "secondary", targets[(theme, device, "Login", "base" if state == "password" else "password")])
    if state in ("invalid", "error", "loading"):
        message = {"invalid": "Isi username dan password sebelum masuk.", "error": "Username atau password tidak sesuai.", "loading": "Sedang memeriksa akun (contoh state)."}[state]
        D.text(root, x, y + 354, w, message, 13, color=tk["err"] if state != "loading" else tk["text2"])
    else:
        D.text(root, x, y + 354, w, "Pilih peran di bawah untuk mencoba alurnya.", 12, color=tk["text2"])
    D.button(root, x, y + 400, w, 48, "Masuk (demo validasi)", tk, "primary", targets[(theme, device, "Login", "invalid")])
    for j, role in enumerate(ROLES):
        D.button(root, x, y + 462 + j * 56, w, 48, "Demo " + role, tk, "secondary", targets[(theme, device, role, "home")])
    D.button(root, 24 if mobile else 64, 774 if mobile else 870, 160, 44, "Contoh gagal login", tk, "secondary", targets[(theme, device, "Login", "error")])
    D.button(root, 204 if mobile else 240, 774 if mobile else 870, 160, 44, "Contoh memuat", tk, "secondary", targets[(theme, device, "Login", "loading")])


def action_targets(node):
    for interaction in node.get("interactions", []):
        for action in interaction.get("actions", []):
            if "dest" in action:
                yield action


def wire_legacy(D, targets, initial_ids):
    for theme, device in VARIANTS:
        page = D.nodes[targets[(theme, device, "Owner", "home")]]["parent"]
        for flow in D.nodes[page].get("flows", []):
            if flow["start"] in initial_ids:
                flow["name"] = "Arsip / " + flow["name"]
        for role in ROLES:
            D.nodes[page].setdefault("flows", []).append({"name": f"{role} / {device} {theme} / UI04", "start": targets[(theme, device, role, "home")], "description": "Journey demo peran. Autentikasi tidak dijalankan."})
        D.nodes[page]["flows"].insert(0, {"name": f"Login / {device} {theme} / UI04", "start": targets[(theme, device, "Login", "base")], "description": "Mulai prototype di sini."})
    for i in initial_ids:
        n = D.nodes[i]
        text = n.get("characters", "")
        if "tanpa harga" in text.lower():
            n["characters"] = re.sub("tanpa harga", "harga jual di WO/invoice", text, flags=re.I)
        if "Cari plat nomor" in text:
            n["characters"] = text.replace("Cari plat nomor", "Cari di bengkel...")
        root = D.root_of(i)
        rn = D.nodes[root].get("name", "")
        if D.nodes[root].get("parent") not in D.d["pages"][:4]:
            continue
        theme = "Dark" if "/ Dark /" in rn else "Light"
        device = "Mobile" if "/ Mobile /" in rn else "Desktop"
        if n.get("name") == "Cari kendaraan":
            n["name"] = "Cari global"
            n["interactions"] = []
            D.link(i, targets[(theme, device, "Owner", "search")], ms=160)
        # Existing technician entries now lead to the complete safe journey.
        for a in action_targets(n):
            dest = D.nodes.get(a["dest"], {})
            if dest.get("name", "").startswith("Teknisi /"):
                a["dest"] = targets[(theme, device, "Teknisi", "home")]


def add_hover(D, initial_pages):
    library = D.add({"name": "Komponen interaksi UI04", "type": "page", "children": [], "width": 0.0, "height": 0.0, "transform": [1, 0, 0, 1, 0, 0], "background": {"r": .95, "g": .95, "b": .95, "a": 1}})
    D.d["pages"].append(library)
    controls = []
    for i, n in list(D.nodes.items()):
        if any(it.get("trigger", {}).get("type") == "onClick" for it in n.get("interactions", [])):
            if n.get("type") in ("frame", "rectangle", "text"):
                controls.append(i)
    # Innermost controls first: component trees retain nested interactions.
    def depth(i):
        count = 0
        while D.nodes[i].get("parent") in D.nodes:
            count += 1
            i = D.nodes[i]["parent"]
        return count
    controls.sort(key=depth, reverse=True)
    for j, original in enumerate(controls):
        n = D.nodes[original]
        root = D.root_of(original)
        nm = D.nodes[root].get("name", "")
        tk = TOKENS["dark" if "Dark" in nm else "light"]
        geom = copy.deepcopy(n.get("transform", [1, 0, 0, 1, 0, 0]))
        parent, width, height = n.get("parent"), n.get("width", 100), n.get("height", 44)
        if n["type"] == "text":
            text_copy = copy.deepcopy(n)
            text_copy.pop("id", None)
            text_copy.pop("interactions", None)
            text_copy["transform"] = [1, 0, 0, 1, 0, 0]
            child = D.add(text_copy)
            n["type"] = "frame"
            n["children"] = [child]
            for key in ("characters", "style", "auto_resize", "align_h"):
                n.pop(key, None)
            D.nodes[child]["parent"] = original
        set_id = D.add({"name": "Control/" + str(original), "type": "componentSet", "parent": library, "children": [], "transform": [1, 0, 0, 1, (j % 8) * 1500, (j // 8) * 400], "width": max(width * 5 + 100, 300), "height": height + 40, "clip": False})
        D.nodes[library]["children"].append(set_id)
        default, _ = D.clone(original)
        for child in list(n.get("children", [])):
            D.delete(child)
        D.nodes[default].update(type="component", parent=set_id, name="State=Default", transform=[1, 0, 0, 1, 0, 0], props={})
        variants = {"Default": default}
        for k, state in enumerate(("Hover", "Pressed", "Focus", "Disabled"), 1):
            variant, _ = D.clone(default)
            D.nodes[variant].update(parent=set_id, name="State=" + state, transform=[1, 0, 0, 1, k * (width + 20), 0])
            v = D.nodes[variant]
            if state in ("Hover", "Pressed"):
                current = v.get("fills", [{}])[0].get("color", {}) if v.get("fills") else {}
                expected = paint(tk["action"])["color"]
                primary = all(abs(current.get(c, -1) - expected[c]) < .002 for c in ("r", "g", "b"))
                v["fills"] = [paint(tk[("action_hover" if state == "Hover" else "action_press") if primary else ("hover_bg" if state == "Hover" else "press_bg")])]
                if not primary:
                    # Text-only links retain a foreground with sufficient contrast.
                    for cid in walk(D, variant):
                        c = D.nodes[cid]
                        if c.get("type") == "text":
                            c["fills"] = [paint(tk["text"])]
            elif state == "Focus":
                v["strokes"] = [paint(tk["focus"])]
                v["stroke"] = {"weight": 2.0, "align": "inside", "cap_start": "none", "cap_end": "none", "join": "miter", "miter_limit": 4, "dashes": [], "sides": None}
            else:
                v["opacity"] = .4
                pending = [variant]
                while pending:
                    cid = pending.pop()
                    c = D.nodes[cid]
                    if c.get("type") == "instance":
                        for child in list(c.get("children", [])):
                            D.delete(child)
                        copied, _ = D.clone(c["component"])
                        static = D.nodes.pop(copied)
                        static.update(id=cid, parent=c["parent"], transform=c["transform"],
                                      width=c["width"], height=c["height"], type="frame")
                        for child in static.get("children", []):
                            D.nodes[child]["parent"] = cid
                        D.nodes[cid] = c = static
                    c.pop("interactions", None)
                    pending.extend(c.get("children", []))
            variants[state] = variant
        D.nodes[set_id]["children"] = list(variants.values())
        for state, vid in variants.items():
            if state == "Disabled":
                continue
            for trigger, target in (("mouseEnter", "Hover"), ("mouseLeave", "Default"), ("mouseDown", "Pressed"), ("mouseUp", "Hover")):
                D.link(vid, variants[target], trigger=trigger, trans="dissolve", ms=120)
                D.nodes[vid]["interactions"][-1]["actions"][0]["type"] = "changeTo"
        # Native instances store materialized paints and descendants. References
        # alone are valid metadata but do not render the source component.
        materialized, mapping = D.clone(default)
        instance = D.nodes.pop(materialized)
        for source_id, clone_id in mapping.items():
            if clone_id == materialized:
                continue
            child = D.nodes[clone_id]
            child.setdefault("source", source_id)
            if child.get("parent") == materialized:
                child["parent"] = original
        instance.update(id=original, type="instance", name=n.get("name", "Control"),
                        component=default, source=default, props={}, parent=parent,
                        transform=geom, width=width, height=height, clip=False)
        meta_data = n.get("plugin_data")
        if meta_data:
            instance["plugin_data"] = meta_data
        D.nodes[original] = instance
    return library, len(controls)


def save_archive(src, out, document):
    with zipfile.ZipFile(src) as original, zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as candidate:
        for member in original.infolist():
            candidate.writestr(member, json.dumps(document, ensure_ascii=False).encode() if member.filename == "document.json" else original.read(member.filename))


def build(src, out, motion=True):
    with zipfile.ZipFile(src) as z:
        doc = json.loads(z.read("document.json"))
    if any(n.get("name", "").startswith("UI04 /") for n in doc["nodes"].values()):
        raise ValueError("Input already contains UI-04. Use the preserved pre-UI04 snapshot.")
    D = Doc(doc, motion)
    initial = list(D.nodes)
    renamed = rename_phase(D)
    pages = dict(zip(VARIANTS, doc["pages"][:4]))
    targets = create_routes(D, pages)
    for theme, device in VARIANTS:
        for state in ("base", "invalid", "loading", "error", "password"):
            login(D, targets, theme, device, state)
        for role in ROLES:
            routes = list(ROUTES[role]) + (["draft-after"] if role in ("Owner", "Teknisi") else [])
            for j, route in enumerate(routes):
                Screen(D, pages[(theme, device)], theme, device, role, route, j, targets).contents()
    galleries = {}
    for theme in ("Light", "Dark"):
        page = pages[(theme, "Desktop")]
        bottom = max(D.nodes[c].get("transform", [0]*6)[5] + D.nodes[c].get("height", 0)
                     for c in D.nodes[page]["children"]) + 200
        g = build_gallery(D, page, 0, bottom, TOKENS[theme.lower()])
        D.nodes[g]["name"] = f"State interaksi / {theme} / Desktop / UI04"
        for i in walk(D, g):
            n = D.nodes[i]
            if n.get("characters", "").startswith("Gambar statis:"):
                n["characters"] = "Galeri state statis. Kontrol pada journey memakai hover/pressed native; keyboard diverifikasi saat tahap browser. Data contoh."
        D.nodes[page].setdefault("flows", []).append({"name": f"State interaksi / {theme} / UI04", "start": g, "description": "Galeri token, bukan kontrol transaksi."})
        galleries[theme] = g
    wire_legacy(D, targets, initial)
    library, controls = add_hover(D, list(pages.values()))
    for n in D.nodes.values():
        if not motion:
            for interaction in n.get("interactions", []):
                interaction["duration_ms"] = 0
                interaction["transition"] = {"type": "instant"}
        if n.get("type") == "text":
            n["characters"] = n.get("characters", "").replace("—", ",")
    document = D.save()
    document["name"] = "Dokter AC Mobil · UI-04 · Login, estimasi, cari global"
    document["current_page"] = pages[("Light", "Desktop")]
    document["selection"] = []
    if out.endswith(".figcraft"):
        save_archive(src, out, document)
    else:
        Path(out).write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    manifest = {"source": str(src), "candidate": str(out), "motion": motion, "nodes": len(D.nodes), "hover_controls": controls, "renamed_fields": renamed, "library": library, "galleries": galleries, "screens": {"/".join(k): v for k, v in targets.items()}}
    Path(out + ".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "screens"}, ensure_ascii=False))
