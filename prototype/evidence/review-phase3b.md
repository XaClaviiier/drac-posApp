# Penutupan WEB-03B — 2026-11-07

## Hasil dan lingkup

**Observed:** editor realisasi SO dan dukungan qty pecahan lulus verifikasi penutupan.
Suite 3B mencatat 17 kelompok lulus; regresi Fase 1/2/3A mencatat 20/16/12 kelompok
lulus. Ini gate prototype dummy, bukan persetujuan produksi. Antrean kasir 3C,
invoice/pembayaran Fase 4, backend dan stok nyata belum diimplementasikan.

Kontrak: `../../doc/CONTEXT.md` §2.1–§2.5 dan `../../doc/IPD/ipd.md` WEB-03B.
Reference lock dan token tetap memakai DBD existing. Tidak ada keputusan visual,
dependency, skema atau migrasi baru pada penutupan ini.

## Temuan dan perbaikan

| Temuan | Bukti sebelum perbaikan | Perbaikan dan bukti sesudahnya | Status |
|---|---|---|---|
| Qty legacy berawalan nol ditolak parser baru | Fixture diagnosis qty `0000001` + qty SO numerik `1` memunculkan error storage | Parser menormalkan leading zero setelah batas panjang 30 karakter, lalu memvalidasi nilai; fixture tetap dibaca tanpa write, dengan/tanpa workflow | Resolved |
| Log harga Diagnosa hanya disembunyikan, tetap berada di DOM non-Owner | Tes mengharapkan nol node log, aktual satu | Daftar dibersihkan, hanya diisi untuk Owner; panel ditutup untuk non-Owner. Browser menguji Teknisi/Kasir ketika halaman aktif maupun tersembunyi | Resolved |
| Overflow total estimasi ditolak tanpa pesan pemulihan | Sepuluh baris valid individual menghasilkan total tidak terhitung, tetapi `items-error` kosong | Pesan kapasitas angka, fokus qty, `aria-invalid` dan relasi pesan ditambahkan; approval ditolak, fixture tersimpan tidak berubah | Resolved |

Kegagalan browser sebelum patch disimpan pada
`failure-phase3b-20261107T013016893007.json`. Dua kelompok batas kapasitas/realisasi
sudah lulus pada run tersebut; tiga kegagalan baru tidak dihapus atau dilemahkan.
Setelah patch, seluruhnya lulus dalam `verification-phase3b.json`.

Review correctness dan security dilakukan oleh reviewer terpisah. Re-review
mengonfirmasi finding tertutup berdasarkan kode, tes dan hasil eksekusi primary;
reviewer tidak menjalankan ulang suite browser secara independen. Security finding
SEC-3B-01 ditutup hanya untuk kebocoran DOM pada prototype.

## Verifikasi segar

Perintah dijalankan dari folder POS. Suite memakai context Chromium headless
terisolasi dan server loopback berport dinamis milik tes, dengan cleanup di `finally`.

| Pemeriksaan | Hasil | Artefak/waktu UTC |
|---|---|---|
| `node --check` pada `items.js`, `app.js`, `diagnosis.js`, `service-orders.js`, `realization.js` di folder prototype | Exit 0 | Output terminal sesi penutupan |
| Python 3.12 `prototype/tests/phase3b_browser.py` | 17 kelompok lulus | `verification-phase3b.json`, `2026-11-07T01:32:29.148882+00:00` |
| Python 3.12 `prototype/tests/phase1_browser.py` melalui `rtk test` | 20 kelompok lulus | `verification-phase1.json`, `2026-11-07T01:33:04.621999+00:00` |
| Python 3.12 `prototype/tests/phase2_browser.py` melalui `rtk test` | 16 kelompok lulus | `verification-phase2.json`, `2026-11-07T01:33:11.498057+00:00` |
| Python 3.12 `prototype/tests/phase3a_browser.py` melalui `rtk test` | 12 kelompok lulus | `verification-phase3a.json`, `2026-11-07T01:33:05.729956+00:00` |

Path interpreter: `C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe`.
RTK memfilter output terminal; jumlah dan hasil di atas diperiksa ulang pada JSON
lengkap, bukan diasumsikan dari ringkasan RTK. Seluruh laporan memiliki `passed: true`
dan daftar error aplikasi yang direkam kosong. Label keterbatasan pada suite Fase 2
menjelaskan lingkup suite historis tersebut, bukan inventaris fitur aplikasi terbaru.

Tambahan bukti bernilai tinggi:

- Fixture pra-3B tetap di `../tests/fixtures/phase2-store.json`; bukan SO yang dibuat
  oleh implementasi baru lalu diberi nama legacy. Raw storage dibandingkan utuh.
- Pembulatan pecahan kg/liter/meter/jam dan total diverifikasi setelah reload;
  snapshot diagnosa, estimasi SO dan katalog tetap dibandingkan.
- Item baru tetap meminta approval ketika pengurangan baris lain membuat total
  bersih turun; workflow tab lain mereset approval tanpa membuang buffer.
- Pembatalan dialog `beforeunload` mempertahankan halaman, qty, alasan dan storage.
- Baris ke-100 dan revisi ke-200 sah; penambahan berikutnya ditolak tanpa write,
  pemangkasan riwayat atau hilangnya input. Overflow agregat realisasi juga ditolak.

## Inspeksi visual dan craft

Enam screenshot baru desktop 1440, tablet 768 dan mobile 390 pada light/dark dibuka
dan diperiksa: `phase3b-desktop-*.png`, `phase3b-tablet-*.png`,
`phase3b-mobile-*.png`. Dua keadaan tambahan dengan banyak baris, error, isian dirty
dan riwayat Owner terbuka diperiksa pada `phase3b-history-error-320.png` dan
`phase3b-history-error-390.png` (teks 200%). Tidak ditemukan pemotongan konten atau
perubahan arah/token pada inspeksi tersebut. Halaman panjang tetap memakai scroll
vertikal; ini bukan bukti performa pada data besar.

Suite memeriksa overflow pada lebar 320/620/1049/1050/1280, teks 200%, fokus error
dan urutan Tab. Regresi Fase 1 menghitung 14 pasangan kontras token ≥4,5:1;
bukan audit WCAG penuh atau pengujian screen reader.

Detector Impeccable dijalankan sekali pada `diagnosis.js`, `items.js`, `index.html`
dan `styles.css`: hanya dua warning `overused-font` untuk Inter di HTML/CSS.
Inter dipertahankan karena token proyek, bukan temuan fungsional. Impeccable dipakai
untuk audit craft; riset reference lock existing tidak diulang karena tidak ada
keputusan arah/layout/interaksi visual baru. Tidak ada perubahan CSS atau token.

## Kontrol keamanan scoped

| Kontrol | Bukti runnable | Status |
|---|---|---|
| Guard role dan terminal status dalam handler | Submit buatan Kasir/Teknisi terminal ditolak; Owner merevisi tanpa reopen/invoice | Green, simulasi klien |
| Persetujuan revisi dan basis stale | Tanpa approval ditolak, reset rincian/peran/workflow, stale write tidak replay | Green, simulasi klien |
| Validasi input/angka dan konsistensi history | Invalid/no-op/overflow, aktor/basis/waktu/approval palsu ditolak tanpa reseed | Green, konsistensi lokal |
| Output teks dan log Owner | Markup menjadi teks; riwayat realisasi dan harga Diagnosa dibersihkan dari DOM non-Owner | Green, DOM saja |
| Storage gagal/konflik | Quota failure menjaga input/history; retry tidak replay dan tidak menimpa basis realisasi baru | Green, konflik sequential |
| Autentikasi, otorisasi server, kerahasiaan storage, audit tahan manipulasi | Backend tidak tersedia; role demo dan data/log tersimpan di browser | Unverified untuk produksi |

Boundary yang ditinjau: input/storage → validasi → state/DOM dan role demo → handler.
Endpoint server, session, CSRF, SQL injection, SSRF, upload dan gateway tidak menjadi
permukaan implementasi irisan ini. Tidak ada klaim kepatuhan ASVS atau keamanan
produksi. PRD §9 belum tersedia; persyaratan produksi di TRD §4 tetap terbuka.

## Batas dan kelanjutan

- Penyimpanan `localStorage` bukan transaksi lintas tab atomik; race write simultan
  belum dijamin. Riwayat dapat direkayasa secara konsisten oleh pemilik storage.
- Role demo bukan login. Menghapus log dari DOM tidak menghapusnya dari storage
  atau membuat browser menjadi boundary kerahasiaan produksi.
- Isian realisasi belum tersimpan tidak dijamin pulih dari crash/force-close.
- Browser non-Chromium, screen reader, keyboard ponsel fisik dan printer belum diuji.
- Pilihan pembukaan kembali SO, batas demo dan alur persetujuan bukan penetapan
  seluruh kebijakan produksi. Belum ada finalisasi realisasi/antrean kasir 3C.
- Tidak ada migrasi atau reseed. Rollback patch kode harus menjaga store pengguna;
  build pra-3B tidak boleh dipakai menulis origin yang sudah berisi data realisasi.

**Recommended:** irisan berikutnya WEB-03C, dengan kriteria penerimaan ditulis
terlebih dahulu. Penutupan 3B tidak menyatakan SO otomatis siap ditagihkan.
