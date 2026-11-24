# Penutupan WEB-04 — Invoice dan pembayaran demo

Tanggal: 2026-11-07. Lingkup: prototype HTML/CSS/JS dummy, bukan sistem produksi.

## Hasil dan kontrak

**Observed:** draf dari penyerahan SO, penerbitan final, pembayaran penuh, koreksi
harga Owner dan nota print-media sudah diimplementasikan. Collection opsional
menjaga store lama terbaca tanpa rewrite/reseed. Tidak menambah dependency,
backend, gateway, stok/reservasi atau refund nyata.

Keputusan user pada CONTEXT §2.7: harga draf hanya Owner; final Rp0 langsung Lunas
tanpa transaksi pembayaran Rp0/uang masuk. Kasir/Owner menerbitkan dan menerima
pembayaran; Teknisi membaca. Kontrak JSON hanya pada BSD §3.3, AC/pilihan demo di IPD WEB-04.

## Arsitektur

`invoices.js` memakai satu ledger urut snapshot dan pembayaran; urutan tidak
bergantung pada timestamp yang dapat sama. Saldo/status dihitung, bukan flag yang
diedit. Snapshot created/rebased mengikuti realisasi penyerahan tepat. Price/
corrected menjaga identitas/baris/qty, issued menjaga draf terakhir. Persist
memeriksa identitas dan prefix append-only.

Tender tunai dibedakan dari penerimaan bersih: tagihan Rp100.000, uang Rp120.000,
amount Rp100.000 dan kembalian Rp20.000. Transfer harus tepat dengan referensi;
gateway-demo wajib pengakuan simulasi. Koreksi tidak mengganti pembayaran lama,
melainkan menghitung sisa/kelebihan terpisah, tanpa refund otomatis.

Draf tetap di antrean; draf stale memerlukan rebase Owner eksplisit setelah SO
ditarik/revisi/serahkan ulang. Final keluar antrean tetapi SO tetap terkunci.
Perubahan pekerjaan/qty sebelum final lewat SO, bukan editor invoice. Ini pilihan
demo terbatas, bukan penetapan mekanisme retur produksi.

## Verifikasi segar

| Pemeriksaan | Hasil | Artefak / waktu UTC 2026-11-07 |
|---|---|---|
| `node --check` items/app/diagnosis/realization/service-orders/handoff/invoices | Exit 0 | Output terminal sesi ini |
| Python 3.12 `prototype/tests/phase4_browser.py` | Exit 0, 12 kelompok lulus | `verification-phase4.json`, `03:57:31.191271+00:00` |
| Regresi Fase 1 | 20 kelompok lulus | `verification-phase1.json`, `03:30:40.925006+00:00` |
| Regresi Fase 2 | 16 kelompok lulus | `verification-phase2.json`, `03:30:47.909893+00:00` |
| Regresi Fase 3A | 12 kelompok lulus | `verification-phase3a.json`, `03:30:43.398785+00:00` |
| Regresi Fase 3B | 17 kelompok lulus | `verification-phase3b.json`, `03:30:54.712761+00:00` |
| Regresi Fase 3C | 14 kelompok lulus | `verification-phase3c.json`, `03:30:50.040144+00:00` |

Interpreter: `C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe`.
Regresi dijalankan melalui `rtk test`; JSON lengkap dibaca ulang. Semua laporan
memiliki `passed: true` dan error browser yang direkam kosong. Total 91 kelompok,
bukan klaim seluruh kemungkinan input. Setelah regresi, kode aplikasi hanya
berubah pada CSS print; suite Fase 4 diulang penuh sesudahnya.

Cakupan penting:
- Legacy, satu invoice per SO dan snapshot realisasi; estimasi/SO tidak ditimpa.
- Owner-only harga draf/final, synthetic submits peran, Kasir menerima pembayaran
  positif dan menerbitkan, Teknisi membaca.
- Harga invalid/no-op/alasan kosong; Rp0 final Lunas tanpa event pembayaran.
- Cash full/change; transfer nominal tepat/ref wajib; gateway pengakuan wajib.
- Koreksi turun menghasilkan kelebihan tanpa mengganti uang; koreksi naik dibayar
  sebesar seluruh sisa baru, bukan cicilan normal.
- Rebase stale eksplisit, prefix utuh dan sumber SO final tidak dapat ditarik.
- Quota gagal menjaga harga/alasan/nominal; reload tidak replay; pembayaran stale
  ditolak setelah koreksi tab lain. Pembayaran ganda tidak menambah uang.
- Offline writes, dirty navigation dan pembatalan unload menjaga isian.
- 19 injeksi collection/relasi/snapshot/aktor/sumber/nominal/revisi/waktu/lock final
  ditolak tanpa reseed; guard prefix menolak rewrite. Event 200 sah, 201 ditolak.
- Markup menjadi teks; log lengkap/pembayaran dibersihkan dari DOM Teknisi.
- Print tidak menulis storage atau menyertakan kontrol/history lengkap.
- Tab pada harga/alasan/aksi dan Enter memicu validasi berfokus tanpa write.

## Review, kegagalan dan perbaikan

Planner gagal TLS upstream. Review rencana alternatif read-only berhasil; saran
ledger tunggal, prefix append-only, tender terpisah dan lock final diadopsi.
Tracer awal gagal karena `#so-invoice` belum tersedia pada
`failure-phase4-20261107T025709836340.json`, lalu lulus setelah implementasi.

Reviewer correctness/security menemukan bahwa render biasa dapat menghapus stale
flag setelah konflik dan membuka cetak cached receipt. Probe independen membuktikan
celah sebelum patch. Perbaikan: latch konflik terpisah, hanya clear pada reload
sukses; cetak memeriksa revision storage valid, dengan guard `beforeprint` juga.

Tes dua tab membuktikan role/network render, navigasi/reopen dan reset tidak membuka
cetak sebelum reload. Tombol dan handler beforeprint memblokir receipt stale/dirty;
CSS menutup receipt dan menampilkan petunjuk pemulihan. Setelah reload, nominal/
status terbaru dipakai. Kedua reviewer menutup blocker berdasarkan probe independen,
kode, assertion dan laporan browser; tidak menjalankan seluruh suite ulang sendiri.
Penutupan reviewer memakai laporan 11 kelompok pada 03:30 UTC. Setelah itu,
perbaikan canvas print, diagnostik server tes dan tambahan cek keyboard diverifikasi
primary lewat suite final 12 kelompok; tidak ada perubahan guard ledger/JS setelah review.

Kegagalan mock print awal bukan bukti tambahan bug: assignment expression saat
pemasangan mock memanggil fungsi sekali. Diganti callback eksplisit dan counter
awal diassert nol, tanpa melonggarkan assertion perilaku cetak.

Inspeksi print-media menemukan root HTML masih gelap. Assertion gagal pada
`failure-phase4-20261107T034146845989.json`; root print dipaksa putih, lalu assertion
dan screenshot konfirmasi terbaru lulus.

Dua run berikutnya gagal startup context fixture karena aset `ERR_CONNECTION_REFUSED`;
`failure-phase4-20261107T034447900738.json` menyimpan error tersebut dan modul yang
tidak ter-load. Runtime Python 3.12 terukur backlog 5. Server tes WEB-04 memakai
backlog 128 serta diagnostik URL request gagal, lalu suite diulang penuh dan lulus
tanpa mengubah assertion startup/error. **Inferred:** kapasitas backlog berkontribusi
pada burst context baru, bukan penyebab eksklusif yang terbukti.
Dokumentasi: https://docs.python.org/3/library/socketserver.html#socketserver.BaseServer.request_queue_size
Default berubah di Python 3.15; nilai runtime 3.12 diukur langsung.

## Visual dan cetak

Reference lock existing dan referensi live Shopmonkey invoice yang sudah dibaca
dipakai ulang; tidak mengklaim riset Refero baru. Arah di DBD, token tetap di
DESIGN_POS_Extend. Enam screenshot desktop/tablet/mobile light/dark dan satu
`phase4-print.png` dibuka. Overflow 320/620/1049/1050/1280 dan teks 200% diperiksa.
Print-media konfirmasi putih dari tema dark. Detector hanya menandai Inter
existing pada HTML/CSS; font dipertahankan sesuai keputusan proyek.

**Batas bukti:** cetak memakai mock `window.print`, pemicuan `beforeprint` dan
emulasi media print. Ini bukti handler/CSS, bukan operasi dialog OS, pagination
perangkat atau hasil printer fisik. Nota selalu bertanda simulasi dan tidak
diklaim sebagai bukti transaksi/gateway/fiskal nyata.

## Kontrol keamanan scoped

| Kontrol | Bukti | Status |
|---|---|---|
| Hak handler/replay | Synthetic role, harga Owner, Kasir issue/pay | Green untuk simulasi |
| Uang dan append-only | Full remaining/change, invalid/duplicate/revision, prefix | Green untuk konsistensi lokal |
| Sumber/lock/stale | Rebase eksplisit, penarikan final dan sumber palsu ditolak | Green untuk demo |
| Output/history/print | Teks aman, log dibersihkan, guard konflik/dirty/version | Green untuk DOM/handler/media print |
| Gagal write/konflik | Input bertahan, reload tidak replay, basis terbaru wajib | Green untuk konflik sequential |
| Auth/webhook/MySQL/stok/audit tahan manipulasi | Belum diimplementasikan | Unverified untuk produksi |

Boundary yang ditinjau: role simulasi, input, ledger localStorage, state/DOM dan
receipt. PRD §9 belum tersedia; bukan gate produksi atau klaim ASVS. Tidak ada
key, secret atau data pelanggan nyata ditambahkan.

## Batas dan kelanjutan

- LocalStorage tidak atomik dan bukan audit tahan manipulasi; pembayaran serentak
  lintas perangkat tidak dijamin, tidak ada autentikasi nyata.
- Navigator online adalah guard UX, bukan bukti server; seluruh pembayaran/gateway
  simulasi, tidak menerima uang sebenarnya.
- Reservasi/stok/retur/refund nyata belum dibuat; final stok produksi masih perlu
  transaksi MySQL sesuai CONTEXT §2.4.
- Batas event demo dapat menghentikan aksi berikutnya; tidak menghapus history
  untuk melewatinya dan bukan batas bisnis produksi.
- Dialog OS/printer, screen reader, non-Chromium dan ponsel asli belum diuji.
  Isian belum tersimpan tidak dijamin pulih dari crash/force-close.
- Jangan gunakan writer pra-Fase-4 pada origin berisi invoice; rollback memakai
  origin/salinan dummy terpisah, bukan menghapus ledger/pembayaran.

Alur inti prototype Fase 1–4 selesai sesuai cakupan IPD. Produksi dan modul lain
bukan otomatis selesai; irisan berikutnya mengikuti keputusan proyek.
