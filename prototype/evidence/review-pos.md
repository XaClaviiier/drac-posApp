# WEB-04P — Beranda Kasir / POS

Tanggal: 2026-11-07. Lingkup: arah beranda Kasir dan integrasi UI prototype dummy.

## Hasil dan sumber keputusan

**Observed:** Kasir clean langsung ke POS. Laptop memakai antrean kiri/detail kanan;
mobile memakai daftar lalu detail. Preferensi peran demo dipulihkan saat reload,
dengan fallback/exception terisolasi dari ledger. Transaksi aktif tetap terbuka
setelah Lunas dan tidak otomatis memilih pelanggan lain.

Keputusan user di CONTEXT §2.8, hak harga/pembayaran tetap §2.7. Kontrak proyeksi
dan preferensi hanya BSD §3.4; AC dan pilihan demo pada IPD WEB-04P. Harga Kasir
tetap read-only; tidak ada migrasi finansial, dependency atau ledger POS baru.

## Arsitektur dan alternatif

`pos.js` memiliki proyeksi, seleksi dan preview; satu entri per SO. Handoff
mendelegasikan presentasi, tetapi tetap memiliki validasi/aksi penyerahan.
`invoices.open()` mengembalikan boolean agar pembatalan/gagal write tidak mengganti
pilihan. Invoice dan receipt tetap anak langsung main dengan satu DOM finansial.
Sibling grid dimatikan saat print; view aktual ikut guard beforeprint.

Antrean mencakup queued SO tanpa invoice, draf (termasuk Perlu Owner bila stale),
serta final bersisa positif. Draf/SO menampilkan total; final belum lunas menampilkan
sisa. Filter Lunas/Semua menampilkan nota tersimpan tanpa mengubah default menunggu.
Memilih preview tidak menulis; create invoice tetap aksi eksplisit.

Alternatif hanya mengganti landing ke antrean lama lebih kecil, tetapi tidak
memenuhi dua area yang disetujui. Planner read-only mendukung sibling-grid dan
pemakaian ulang editor, bukan memindahkan/menduplikasi DOM pembayaran.

## Verifikasi segar

| Pemeriksaan | Hasil | Artefak / UTC 2026-11-07 |
|---|---|---|
| `node --check` items/app/diagnosis/realization/service-orders/handoff/invoices/pos | Exit 0 | Output terminal sesi ini |
| Python 3.12 `prototype/tests/pos_browser.py` | Exit 0, 12 kelompok lulus | `verification-pos.json`, `05:00:53.471809+00:00` |
| Regresi Fase 1 | 20 kelompok lulus | `verification-phase1.json`, `05:00:54.661358+00:00` |
| Regresi Fase 2 | 16 kelompok lulus | `verification-phase2.json`, `05:01:01.013672+00:00` |
| Regresi Fase 3A | 12 kelompok lulus | `verification-phase3a.json`, `05:00:55.511669+00:00` |
| Regresi Fase 3B | 17 kelompok lulus | `verification-phase3b.json`, `05:03:36.102641+00:00` |
| Regresi Fase 3C | 14 kelompok lulus | `verification-phase3c.json`, `05:03:31.745404+00:00` |
| Regresi Fase 4 | 12 kelompok lulus | `verification-phase4.json`, `05:03:40.347593+00:00` |

Interpreter `C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe`.
Regresi 1/2/3A/3B memakai `rtk test`; JSON lengkap dibaca ulang. Seluruh laporan
`passed: true` dan error browser yang direkam kosong. Total 103 kelompok, bukan
klaim seluruh kombinasi input. Server tes loopback dan browser context terisolasi;
tidak menjalankan tes pada profil/data browser pengguna.

Cakupan POS:
- Landing/reload Kasir, key invalid, read preference SecurityError dan write
  preference quota failure; ledger tetap utuh dan transaksi masih dapat disimpan.
- Custom role tidak sah ditolak; Teknisi tidak membuka POS lewat menu/handler,
  daftar/preview dibersihkan, log harga dan pembayaran tetap mengikuti Fase 4.
- Empat identitas pencarian, filter/kosong, satu entri per SO; preview tanpa write.
- Pembatalan pindah invoice/preview menjaga nominal, pilihan dan konteks; role
  berubah tanpa membuang isian. Source SO dirty tetap terlindungi regresi existing.
- Pembayaran penuh Kasir dengan kembalian tidak memilih baris berikutnya, nota
  tetap terbuka walaupun transaksi keluar antrean menunggu.
- Failed create/offline/conflict menjaga preview/selection; reload tidak replay,
  invoice yang dibuat tab lain dibuka tanpa duplikasi.
- Draf stale bertanda Perlu Owner; Kasir tidak bisa menerbitkan. Invoice terkoreksi
  total Rp110.000 dengan uang Rp100.000 menampilkan Sisa Rp10.000 pada antrean.
- Print hanya ketika invoice benar-benar aktif, final, bersih dan revision valid;
  view daftar/preview tidak mencetak receipt invoice lama. Tidak ada write saat print.

## Red/green, review dan adaptasi regresi

Kegagalan awal disimpan pada `failure-pos-20261107T042608445698.json` (landing)
dan `failure-pos-20261107T042716198763.json` (preview belum ada), lalu lulus setelah
implementasi. Tes quota menemukan tombol create tetap disabled sesudah reload
karena render saat loading; `failure-pos-20261107T043432982743.json` dipertahankan.
Renderer kini dipanggil lagi setelah loading selesai; assertion enabled dan
seluruh cek gagal-write/conflict lulus.

Correctness reviewer menemukan minor context warning: pesan pilihan di luar filter
ditulis pada panel invoice yang tersembunyi ketika preview SO aktif. Regression
`failure-pos-20261107T045840970484.json` membuktikan belum ada pesan preview.
Pesan kini tampil pada kedua konteks yang relevan, tanpa mengganti pilihan.
Probe Chromium independen reviewer memverifikasi pesan terlihat, identitas benar,
raw ledger byte-identical dan cleanup Teknisi. Finding ditutup.

Security reviewer tidak menemukan blocker pada inspeksi role/event, output teks,
preferensi terpisah, dirty guards, failure dan print revision/view checks. Probe
independen security tidak berjalan akibat command quoting/adapter PTY Windows;
tidak ada assertion probe tersebut diklaim berjalan. Bukti runnable utama tetap
suite primary di atas. Reviewer tidak mengulang seluruh suite browser sendiri.

Regresi lama mengasumsikan memilih Kasir tidak menavigasi, reload kembali ke
registrasi, dan klik antrean langsung membuka SO. Tes diarahkan lewat menu
registrasi/diagnosa/SO secara eksplisit serta preview → Buka SO lengkap. Tes
Fase 4 kini mengassert invoice final belum lunas ada di POS, lalu filter Siap
ditagih kosong. Tidak menghapus/melemahkan pemeriksaan uang, peran, history atau lock.

## Riset, visual dan batas bukti

Target layout disetujui user; memakai token/komponen existing dan reference lock
DBD. Shopmonkey workflow live dibaca ulang: status, identitas kendaraan, universal
search dan transisi pekerjaan menjadi invoice. URL bantuan Square ternyata artikel
login; tidak dipakai sebagai bukti checkout. Refero subscription diketahui tidak
tersedia dari sesi ini; tidak mengklaim riset/screenshot Refero baru.

Enam screenshot detail desktop/tablet/mobile light/dark, daftar mobile dan print
dibuka. Layout desktop dua area, mobile list-detail, lebar 320/620/1049/1050/1280,
teks 200%, Enter dan fokus heading lulus. Detector hanya memperingatkan Inter
existing pada HTML/CSS; font dipertahankan sesuai token. Tidak ada UI polish loop
terbuka atau perubahan arah merek baru.

Print diuji melalui mock `window.print`, pemicuan `beforeprint` dan emulasi print
media, bukan dialog OS/printer fisik. Chromium headless saja; screen reader,
perangkat ponsel asli dan browser lain belum diuji. Tidak mengklaim audit WCAG penuh.

## Keamanan scoped dan rollback

| Kontrol | Bukti | Status |
|---|---|---|
| Harga/pembayaran tetap pada handler existing | Regresi Fase 4 dan POS bayar Kasir | Green untuk simulasi |
| Preferensi bukan otorisasi | Whitelist, failure read/write, banner demo | Green untuk UI demo |
| Data role/preview dan output | Cleanup Teknisi, pembentukan text nodes, regresi markup | Green untuk DOM |
| Dirty/failure/conflict | Cancel tidak mengubah pilihan/input, retry bukan replay | Green untuk konflik sequential |
| Print | View aktif, conflict latch/revision dan receipt-only | Green untuk handler/media print |
| Backend/auth/gateway/stock/audit tahan manipulasi | Di luar implementasi prototype | Unverified untuk produksi |

No-auth dan localStorage non-atomik tetap batas produksi; PRD §9 belum hijau.
Pengingat role bisa dibaca/diubah pemilik browser, bukan sesi login. Tidak ada
data pelanggan nyata atau secret ditambahkan. Input belum tersimpan tidak dijamin
pulih setelah crash/force-close.

Rollback ke baseline Fase 4 aman terhadap kontrak ledger yang sama; key preferensi
dapat diabaikan. Jangan memakai writer pra-Fase-4 atau menghapus ledger untuk
mengembalikan tampilan. Tidak ada migrasi/skema finansial baru.
