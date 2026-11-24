# Prototype browser POS — preview alur layanan

## Prototype FigCraft aktif

Prototype FigCraft baru dikumpulkan di [figcraft/](figcraft/README.md), dengan file
utama [pos-kasir.figcraft](figcraft/pos-kasir.figcraft). Ini alur simulasi Kasir
desktop/ponsel, terpisah dari prototype browser yang dijelaskan di bawah.

## Penyempurnaan desain visual (WEB-09)

Navigasi aktif, ritme judul, metadata daftar dan kesejajaran kolom diperjelas.
Form pemeriksaan dua kolom di desktop; ringkasan invoice sejajar ketika ruang
cukup. Ponsel tetap bertumpuk, dengan status/waktu dikelompokkan dan navigasi SO
lebih mudah disentuh. Palet, sidebar, font dan perilaku bisnis tetap.

Refresh paksa dengan Ctrl+F5 untuk memuat stylesheet terbaru. Verifikasi mencakup
runner UI/fokus/UX/POS/Fase 2 serta probe isi panjang pada enam lebar dan dua tema.

## Perbaikan audit UI/UX (WEB-08)

- Simpan realisasi secara eksplisit sebelum Tandai selesai; perubahan realisasi
  yang belum disimpan memblokir penyelesaian. Hak Teknisi pada SO terminal tetap.
- Pembayaran menampilkan sisa, uang diterima dan kembalian sebelum dicatat;
  konfirmasi menyebut invoice, plat dan nominal. Error muncul dekat field terkait.
- Daftar diagnosa menampilkan nomor dan waktu kunjungan, bukan hanya plat.
  Petunjuk persetujuan tidak menghalangi penyimpanan draf parsial.
- Di form registrasi, Buang draf dan mulai baru meminta konfirmasi. Hanya draf
  registrasi yang dibuang setelah penyimpanan berhasil, bukan dokumen tersimpan.
- Pesan penyimpanan membedakan data rusak dan akses terblokir. Unduh salinan data
  mentah menyimpan salinan lokal persis apa adanya untuk pemulihan manual;
  bukan reset, import atau perbaikan otomatis. Simpan unduhan secara privat.

Regresi terarah: `prototype/tests/ux_browser.py`; bukti ringkas
`prototype/evidence/verification-ux.json`. Hasil integrasi dicatat di IPD WEB-08.

## Penataan UI/UX shadcn (WEB-06)

Halaman registrasi (daftar/form/detail), diagnosa, SO/progres/realisasi, Kasir/POS,
invoice/pembayaran dan panduan preview memakai komponen HTML native dengan pola
visual shadcn/ui. Tidak ada dependensi React/shadcn yang dipasang. Sidebar
dikelompokkan, kontrol/badge/form konsisten, kolom daftar desktop berubah menjadi
baris bertumpuk pada ponsel, dan SO memiliki navigasi antarbagian. Dialog konfirmasi
tetap native browser agar kontrak aksi sinkron dan seluruh guard existing utuh;
penampilannya mengikuti OS/browser, bukan tema aplikasi.

Pengujian tambahan UI: `prototype/tests/ui_browser.py`; hasil dan screenshot di
`prototype/evidence/verification-ui.json` serta `ui-*.png`. Runner ini memeriksa
label, fokus error, penutupan menu dengan keyboard, kontras token CSS aktual pada
dua tema, lebar 1440/390/320 dan ledger yang tidak berubah saat navigasi.
Dashboard belum ada pada prototype aktif; halaman legacy ROOT tidak diubah.

## Preview revisi 11 November 2026

Buka `http://127.0.0.1:8765/prototype/preview.html` setelah server lokal dijalankan.
Panduan menyediakan pintasan setiap tahap, dengan contoh SO sedang dikerjakan,
SO siap ditagih dan invoice belum lunas. Semua harga dan identitas adalah contoh.
Pilih Kasir/Owner untuk proses tagihan, Teknisi/Owner untuk pekerjaan.

Mode latihan memakai dataset terpisah; refresh mempertahankan perubahan latihan.
Tautan prototype utama membuka data existing. Tidak ada reset otomatis.
SO kini mendukung satu teknisi utama dan beberapa anggota melalui tindakan
Tetapkan teknisi/Mulai pengerjaan; riwayat dan lock existing tetap berlaku.
Master kendaraan/pelanggan, penonaktifan master, pembelian/penerimaan/retur terbaru
belum diimplementasikan. HPP otomatis dan laporan profit tetap ditunda.

Uji tambahan: `prototype/tests/preview_browser.py`. Dataset `preview-store.json`
dibuat lewat tindakan UI existing, bukan melewati validasi ledger. Menghapus dataset
bukan bagian dari pengujian rutin; test hanya membuatnya bila belum ada.

Entry point: `prototype/index.html`. Buka melalui HTTP lokal dengan origin yang
konsisten agar penyimpanan browser dapat diuji. Tidak memerlukan npm/build.

Contoh dari folder POS, jika Python tersedia pada PATH:

```cmd
python -m http.server 8765 --bind 127.0.0.1
```

Lalu buka `http://127.0.0.1:8765/prototype/`.

## Cakupan

- Fase 1: shell light/dark, simulasi tiga peran, daftar/form/detail registrasi,
  pencarian plat/nama/telepon, filter hari ini, autosave draf lokal, pesan kegagalan.
- Fase 2: Diagnosa & Estimasi, persetujuan lisan, salinan SO read-only. Selesai.
- Fase 3A: daftar/detail SO, penanggung jawab, progres dan riwayat. Selesai.
- Fase 3B: penyesuaian realisasi, qty pecahan dan riwayat perubahan. Selesai.
- Fase 3C: penyerahan realisasi, antrean kasir, lock dan penarikan Owner. Selesai.
- Fase 4: invoice draf/final, pembayaran penuh simulasi, koreksi Owner dan nota cetak. Selesai.
- WEB-04P: Kasir langsung POS, antrean transaksi kiri/detail kanan, mobile list-detail. Selesai.

Keputusan produk bersumber pada `../doc/CONTEXT.md` §2.2–§2.8. Kriteria dan status
pelaksanaan berada di `../doc/IPD/ipd.md` WEB-01/WEB-02/WEB-03A/WEB-03B/WEB-03C/WEB-04/WEB-04P. Tidak ada backend, autentikasi,
sinkronisasi, PWA, atau transaksi gateway nyata pada prototype ini.

## Mencoba beranda Kasir / POS

1. Refresh browser (Ctrl+F5 jika tampilan lama masih tersimpan) lalu pilih peran
   Kasir. Beranda langsung POS; pilihan peran demo diingat untuk reload berikutnya.
   Ini tetap simulasi, bukan login atau otorisasi server.
2. Antrean menampilkan SO siap ditagih, invoice draf serta invoice Belum Lunas.
   Cari plat, pelanggan, nomor SO/invoice atau gunakan filter tagihan/pekerjaan.
   Draf yang sumbernya berubah bertanda Perlu Owner.
3. Laptop menampilkan antrean kiri dan rincian kanan. Pada ponsel pilih transaksi
   dari daftar, lalu gunakan Kembali ke antrean untuk melihat daftar lagi.
4. Memilih SO hanya membuka preview, tidak membuat invoice. Periksa rincian lalu
   Buat invoice draf. Memilih invoice membuka editor dan pembayaran yang sama
   dengan Fase 4; harga tetap hanya Owner, Kasir menerbitkan/menerima pembayaran.
5. Setelah Lunas, detail/nota tetap terbuka dan tidak otomatis pindah pelanggan.
   Filter Lunas/Semua dapat membuka nota lama. Default Menunggu proses hanya
   menampilkan pekerjaan/tagihan yang masih perlu ditangani.
6. Jika berpindah transaksi saat ada isian lokal, konfirmasi dapat dibatalkan tanpa
   kehilangan input atau pilihan. Pergantian ke Kasir ketika SO masih dirty tidak
   memaksa meninggalkan isian; buka POS setelah isian disimpan/dibersihkan.

Antrean kosong adalah normal bila belum ada SO diserahkan atau seluruh tagihan
sudah Lunas. Untuk membuat contoh transaksi, jalankan alur Fase 2–3C di bawah.
Registrasi kendaraan tetap tersedia dari menu. Preferensi peran terpisah dari
ledger, kontraknya pada BSD §3.4; nilai invalid/read failure memakai fallback Owner.

## Mencoba Fase 2

1. Pilih peran Teknisi atau Owner pada Simulasi peran.
2. Buka detail kunjungan lalu Buat diagnosa, atau menu Diagnosa & Estimasi.
3. Isi masalah yang ditemukan dan saran tindakan.
4. Pilih jasa/sparepart contoh, tambah item, lalu ubah jumlah dan harga lokal.
   Jika harga berbeda dari katalog, isi alasan sebelum persetujuan.
5. Draf tersimpan otomatis. Centang pengakuan persetujuan lisan, lalu Catat
   persetujuan lisan setelah pelanggan setuju. Estimasi menjadi terkunci.
6. Pilih Buat Service Order. Tombol berikutnya membuka SO yang sama, bukan duplikat.

Kasir hanya dapat membaca diagnosa dan SO existing pada simulasi ini. Semua
peran tetap metadata demo, bukan login. Draf registrasi dan diagnosa disimpan
terpisah. Saat data tab lain berubah, Muat data terbaru mempertahankan isian
lokal; jika estimasi sudah disetujui, konfirmasi dahulu sebelum mengganti isian.

Diagnosa memakai satu dokumen per kunjungan dan harga rupiah bulat 0–1.000.000.000
untuk validasi demo. Aturan qty mengikuti CONTEXT §2.5: kg/liter/meter/jam maksimal
tiga desimal; pcs/unit/pekerjaan bilangan bulat positif. Batas teknis demo qty
999999,999 (atau 999999 untuk satuan bulat), bukan batas bisnis produksi.
Subtotal dibulatkan per baris ke rupiah terdekat, Rp0,50 naik; total menjumlahkan
subtotal yang sudah dibulatkan. Perhitungan skala 1.000 memakai integer/BigInt,
bukan perkalian float. Ini bukan batas biaya otomatis persetujuan.
Log perubahan harga disimpan; alasan yang dilengkapi setelah autosave menyimpan
waktu dan petugas pelengkap alasan. Log lengkap hanya ditampilkan pada mode Owner.
Collection baru pada version 1 bersifat opsional sehingga data Fase 1 tetap terbaca.
Jangan membuka build pra-Fase-4 untuk menulis origin yang sudah berisi invoice.
Gunakan satu build aktif saat mencoba agar data baru tidak dihilangkan build lama.

## Mencoba 3A

1. Buka menu Service Order. Bila kosong, buat SO dari estimasi disetujui pada Fase 2.
2. Buka SO, pilih teknisi contoh, lalu Mulai pengerjaan. Penanggung jawab juga bisa
   ditetapkan lebih dahulu lewat tindakan Tetapkan teknisi.
3. Pilih Tunda pekerjaan dan isi alasan; lanjutkan lewat Lanjutkan pengerjaan.
4. Simpan realisasi dahulu, lalu Tandai selesai dari Dalam Pengerjaan. Dialog
   konfirmasi tidak menerbitkan invoice.
5. Teknisi tidak dapat mengubah SO Selesai. Mode Owner menyediakan Buka kembali
   dengan alasan. SO Dibatalkan terminal; kunjungan berikutnya memakai SO baru.
6. Riwayat memuat tindakan, peran simulasi, waktu, status sebelum/sesudah, teknisi
   dan catatan. Estimasi disetujui tidak diubah oleh tindakan progres.

Pilihan ini merupakan aturan demo di IPD WEB-03A; belum keputusan seluruh workflow
produksi. Form progres tidak mengubah biaya. Gunakan editor 3B di bawah untuk
rekonsiliasi biaya; total estimasi bukan otomatis tagihan pembatalan.

Form progres memakai tindakan eksplisit, tidak autosave perubahan status. Saat
storage gagal atau konflik, isian lokal tetap terlihat. Coba lagi/Muat data terbaru
hanya memuat ulang, tidak menjalankan ulang tindakan. Periksa status terbaru lalu
pilih/terapkan tindakan lagi. Meninggalkan isian yang belum diterapkan meminta
konfirmasi; Bersihkan isian membuang isian lokal saja, bukan riwayat.

SO dari Fase 2 tanpa workflow dibaca Belum dimulai tanpa rewrite. Workflow rusak
ditolak tanpa menimpa raw data. Hanya gunakan satu build aktif pada origin yang sama.

## Mencoba 3B

1. Pilih Teknisi atau Owner, lalu buka detail Service Order.
2. Editor Realisasi pekerjaan dan biaya mula-mula mengikuti estimasi disetujui.
   Tambah/hapus item atau ubah qty/harga lokal sesuai pekerjaan sebenarnya.
   Estimasi disetujui dan katalog contoh tetap utuh.
3. Isi alasan pencatatan/perubahan. Item baru atau kenaikan subtotal satu baris
   memerlukan pengakuan persetujuan lisan pelanggan, meskipun total bersih turun.
   Checkbox direset ketika rincian, peran atau basis workflow/realisasi berubah.
4. Pilih Simpan realisasi. Perubahan ini disimpan eksplisit, bukan autosave;
   lihat status Tersimpan sebelum menutup tab. Riwayat lengkap hanya tampil pada Owner.
5. Kasir hanya membaca. Teknisi tidak dapat merevisi SO Selesai/Dibatalkan.
   Owner dapat menyesuaikan biaya terminal dengan alasan tanpa membuka kembali
   status pekerjaan, setelah menarik SO bila sedang dalam antrean kasir.
   Ini belum menerbitkan invoice atau mengeluarkan stok.
6. Jika benar-benar tidak ada biaya aktual, hapus seluruh baris dan simpan dengan
   alasan. Qty nol bukan cara membatalkan biaya dan akan ditolak.

Muat realisasi tersimpan meminta konfirmasi ketika ada isian lokal; tindakan ini
membuang isian editor, bukan riwayat tersimpan. Saat storage gagal, input/alasan
dipertahankan. Coba lagi/Muat data terbaru tidak menjalankan ulang penyimpanan.
Jika realisasi sudah berubah di tab lain, isian lama tidak dapat menimpa basis baru;
muat realisasi tersimpan lalu terapkan ulang perubahan yang masih diperlukan.
Navigasi atau unload dengan perubahan belum tersimpan memberikan peringatan.
Crash/force-close tetap tidak menjamin pemulihan isian editor yang belum disimpan.

Batas teknis demo: 100 baris dan 200 revisi per SO. Penambahan berikutnya ditolak
tanpa memangkas data. Overflow total dokumen ditolak dengan pesan pemulihan.
Snapshot SO lama dengan qty numerik tetap terbaca tanpa migrasi/rewrite; penulisan
realisasi baru memakai qty teks desimal canonical.

## Mencoba 3C

1. Saat SO masih dikerjakan, simpan realisasi yang sudah diperiksa. Setelah SO
   Selesai, Teknisi atau Owner memilih Serahkan ke kasir dan mengonfirmasi nominal.
   Untuk SO terminal lama yang belum memiliki realisasi, Owner perlu mencatatnya
   dahulu. Penyelesaian baru wajib menyimpan realisasi sebelum status Selesai;
   estimasi tidak otomatis menjadi biaya akhir.
2. SO Dibatalkan dengan biaya hanya dapat diserahkan Owner. Pada demo, SO
   Dibatalkan Rp0 tidak masuk antrean, sedangkan SO Selesai Rp0 dapat diperiksa
   dengan label tanpa biaya pada SO. Invoice final Rp0 kini langsung Lunas tanpa
   transaksi pembayaran atau uang masuk (CONTEXT §2.7).
3. Buka menu Kasir / POS pada mode Kasir/Owner. Cari plat, nama atau nomor SO,
   pilih transaksi lalu Buka SO lengkap bila ingin melihat penyerahan/progres.
   Nominal SO bersumber dari realisasi yang diserahkan,
   bukan estimasi. Teknisi melihat status penyerahan pada detail SO saja.
4. Selama berada dalam antrean, biaya dan progres terkunci termasuk untuk Owner.
   Untuk revisi, Owner mengisi alasan dan memilih Tarik dari antrean, lalu konfirmasi.
5. Penarikan tidak mengubah biaya/progres dan tidak menghapus riwayat. Setelah
   direvisi atau diperiksa ulang, pilih Serahkan ke kasir lagi secara eksplisit.
   Hak penyerahan ulang sama dengan penyerahan awal. Antrean tidak digandakan.

Isian progres/realisasi yang belum diterapkan memblokir penyerahan; tidak otomatis
disimpan. Alasan penarikan yang belum tersimpan juga dilindungi saat navigasi/unload.
Gagal write atau konflik menjaga isian; Coba lagi/Muat data terbaru hanya memuat
ulang, bukan replay aksi. Basis penarikan stale harus dibersihkan lalu diperiksa
ulang sebelum tindakan baru. Riwayat lengkap penyerahan/penarikan hanya tampil
untuk Owner. Batas demo 100 peristiwa per SO tanpa pemangkasan riwayat.

Kontrak JSON dummy ada di `../doc/BSD/bsd.md` §3.2. Field opsional menjaga SO lama
tetap terbaca tanpa rewrite. Build lama tidak memahami lock antrean, sehingga tidak
boleh dipakai menulis origin yang sama setelah mencoba 3C.

## Mencoba Fase 4

1. Pilih Kasir atau Owner. Pada Kasir / POS, pilih SO lalu Buat invoice draf dari
   preview; tombol yang sama juga tersedia pada detail SO lengkap.
   Rincian mengikuti realisasi yang diserahkan, bukan estimasi. Satu SO memiliki
   satu invoice; tombol berikutnya membuka dokumen yang sama.
2. Hanya Owner mengubah harga satuan lokal invoice, wajib alasan dan Simpan harga
   draf. Qty/baris tetap mengikuti SO; katalog, estimasi dan realisasi tidak berubah.
   Teknisi membaca invoice, tidak menerbitkan atau menerima pembayaran.
3. Jika pekerjaan berubah sebelum final, Owner menarik SO, merevisi realisasi lalu
   menyerahkan ulang. Draf lama tidak otomatis ditimpa: Owner mengisi alasan dan
   memilih Muat realisasi terbaru pada invoice, dengan history tetap utuh.
4. Kasir/Owner memilih Terbitkan invoice final dan konfirmasi. SO tetap terkunci;
   entri POS berubah menjadi Belum Lunas sampai dibayar. Total Rp0 langsung Lunas
   tanpa pembayaran. Dokumen juga tersedia pada menu Invoice & Pembayaran.
5. Untuk sisa positif, catat pembayaran penuh:
   - Tunai: uang diterima minimal seluruh sisa; selisih menjadi kembalian. Tagihan
     Rp100.000 dengan uang Rp120.000 mencatat Rp100.000 dan kembalian Rp20.000.
   - Transfer manual: nominal tepat sebesar sisa dan referensi wajib.
   - Gateway — SIMULASI: nominal tepat dan pengakuan simulasi wajib dicentang.
     Tidak menghubungi gateway, memverifikasi pembayaran atau menerima uang nyata.
6. Sesudah final, hanya Owner menyimpan koreksi harga dengan alasan. Pembayaran
   lama tetap: penurunan dapat menghasilkan kelebihan bayar tanpa refund otomatis;
   kenaikan dapat menghasilkan sisa baru yang dibayar penuh terpisah. Ini bukan
   dukungan DP, cicilan atau tempo normal.
7. Cetak nota simulasi hanya untuk final tersimpan dan versi terbaru. Isian dirty
   atau konflik memblokir cetak sampai data dimuat dan isian dibersihkan/disimpan.
   Print CSS hanya menyertakan nota, tanpa navigasi/editor/log. Dialog OS/printer
   fisik belum diuji; seluruh nota bertanda simulasi, bukan transaksi nyata.

Invoice writes memerlukan status online browser sebagai guard UX demo, bukan
verifikasi server. Maksimal 200 peristiwa invoice tanpa pemangkasan. Refund,
perubahan qty sesudah final, retur/stok nyata dan gateway nyata belum tersedia.
Kontrak JSON dummy di BSD §3.3, keputusan harga/Rp0 pada CONTEXT §2.7.

## Data dan pemulihan

### Penyimpanan lokal

Seluruh data fiktif. Jangan memasukkan data pelanggan nyata. Key khusus
`pos_browser_prototype_v1` menyimpan registrasi, draf, diagnosa dan SO beserta
realisasi/riwayat, penyerahan antrean dan invoice/pembayaran dummy; key tema
`pos_browser_prototype_theme`. Tidak membaca atau mengubah `dokterac_v2`.

Draf disimpan setelah jeda input 400 ms. Registrasi hanya masuk daftar ketika
Simpan registrasi berhasil. Gagal menulis mempertahankan isian di halaman;
jangan menutup tab sebelum penyimpanan berhasil. Data rusak tidak otomatis diganti
seed. Tombol Coba lagi membaca ulang setelah data/akses dipulihkan.

Konflik berurutan antar-tab dideteksi memakai revision dan storage event. Isian
lokal dipertahankan saat Muat data terbaru. Ini bukan transaksi lintas tab atomik;
penulisan simultan dalam jendela race localStorage belum dijamin. Tidak cocok untuk
pencatatan produksi. Tidak ada tombol reset yang menghapus data.

## Reference lock

Ekstensi arah FigCraft existing, bukan redesign: lihat `../doc/DBD/dbd.md` dan
token bagian Prototype pada `../doc/DBD/DESIGN_POS_Extend.md`. Riset live existing
Shopmonkey/Calendly dan referensi Cursor/Linear dipakai ulang; tidak mengklaim riset
Refero baru. Preview FigCraft `desktop-light.png` telah dibaca sebelum implementasi.

Mode Operate, dial ENERGY 1 / RHYTHM 2 / MOTION 2. Inter adalah pilihan pertama
dengan fallback Segoe UI/system sans karena belum ada aset Inter lokal; tidak ada
font CDN. Plat menonjol untuk identifikasi kunjungan; sidebar dan form mengikuti
token existing. Biru hanya interaksi, amber status/peringatan, hijau sukses, merah
error. Tidak memakai ilustrasi/logo/foto atau angka pemasaran.

Komposisi: daftar penerimaan sebagai layar awal; form pada halaman tersendiri dengan
petunjuk tahapan di samping pada desktop, bertumpuk di ponsel. Informasi kendaraan
mendahului metadata. Gerak hanya feedback kontrol, tanpa animasi masuk atau delay.

## Verifikasi

Penutupan WEB-04P pada 2026-11-07: **12 kelompok POS** lulus, regresi Fase
1/2/3A/3B/3C/4 **20/16/12/17/14/12** lulus; total **103 kelompok**. Delapan JS
lolos pemeriksaan sintaks. Bukti: `evidence/verification-pos.json`,
`evidence/review-pos.md` dan `evidence/pos-*.png`.

```cmd
"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" prototype/tests/pos_browser.py
```

Suite POS meliputi landing/preferensi, proyeksi dan nominal sisa, preview tanpa
write, dirty cancel, pembayaran/nota terpilih, role/DOM cleanup, kegagalan preferensi,
failed create/conflict/offline, stale Owner, keyboard/reflow dan print view guard.

Penutupan Fase 4 pada 2026-11-07: **12 kelompok** lulus, termasuk 19 injeksi data
invalid dan append-only. Regresi Fase 1/2/3A/3B/3C lulus **20/16/12/17/14**,
total **91 kelompok**. Tujuh JS lolos pemeriksaan sintaks. Bukti:
`evidence/verification-phase4.json`, `evidence/review-phase4.md` dan `phase4-*.png`.

```cmd
"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" prototype/tests/phase4_browser.py
```

Suite memeriksa peran, Rp0, uang/kembalian, koreksi, draf stale, final lock,
failure/conflict/offline/dirty guard dan pencegahan cetak versi lama. Cetak diuji
melalui mock `window.print`, pemicuan `beforeprint` dan emulasi media print, bukan
dialog OS atau printer fisik. Server tes memakai backlog 128 untuk burst context
Chromium baru; startup dan error browser tetap diperiksa penuh.

Penutupan 3C pada 2026-11-07: **14 kelompok** lulus, termasuk 15 injeksi history
invalid. Regresi Fase 1/2/3A/3B lulus **20/16/12/17 kelompok**. Enam file JS lolos
pemeriksaan sintaks. Catatan review dan batas verifikasi di `evidence/review-phase3c.md`;
laporan di `evidence/verification-phase3c.json`, screenshot `evidence/phase3c-*.png`.

```cmd
"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" prototype/tests/phase3c_browser.py
```

Suite menguji gate peran/status/realisasi secara mandiri, queued lock, penarikan
beralasan, revisi/penyerahan ulang, retry tanpa replay, konflik/dirty guard,
history malformed, batas peristiwa, markup sebagai teks dan pembersihan DOM.

Penutupan 3B pada 2026-11-07: suite browser 3B lulus **17 kelompok**; regresi
Fase 1/2/3A lulus **20/16/12 kelompok**. Pemeriksaan sintaks lima file JS lulus.
Laporan terbaru tersedia pada `evidence/verification-phase3b.json` dan laporan
fase regresi; review, red/green, batas keamanan dan inspeksi visual di
`evidence/review-phase3b.md`.

Jalankan dari folder POS dengan runner existing:

```cmd
"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" prototype/tests/phase3b_browser.py
```

Suite 3B menguji fixture pra-3B, qty pecahan/pembulatan, snapshot/master tetap,
approval tambahan meskipun total turun, role/terminal lock, pembersihan DOM log,
failed write/conflict/workflow, unload, kapasitas baris/revisi dan overflow.
Snapshot visual enam varian di `evidence/phase3b-*.png`; dua screenshot tambahan
`phase3b-history-error-*.png` mencakup editor dirty/error dengan riwayat terbuka.

Fase 3A: jalankan `prototype/tests/phase3a_browser.py` dengan interpreter yang sama
di bawah. Hasil aktual 12 kelompok lulus; regresi Fase 1 20 dan Fase 2 16 lulus.
Laporan `evidence/verification-phase3a.json`, screenshot `phase3a-*.png`, dan
catatan gate/review `evidence/review-phase3a.md`. Pengujian mencakup penolakan
transisi/role, konfirmasi, failed write, konflik, replay history malformed, markup,
fokus keyboard/ARIA, reflow detail/form/history serta daftar pada 320 px dan teks 200%.

Skrip `tests/phase1_browser.py` menjalankan browser pada profil terisolasi, membuat
data uji sementara, dan menyimpan screenshot/laporan di `evidence/`. Tidak memakai
profil browser pengguna. Tanpa argumen, skrip menjalankan server loopback pada port
dinamis dan menutupnya dalam finally. Jika URL diberikan sebagai argumen, gunakan
server yang sudah tersedia.

Pada mesin ini Python tidak tersedia melalui alias PATH. Perintah yang teruji
dari folder POS:

```cmd
"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" prototype/tests/phase1_browser.py
```

Hasil regresi Fase 1: 20 kelompok pemeriksaan lulus. Fase 2: 16 kelompok lulus,
termasuk harga invalid, persetujuan wajib, snapshot terkunci, copy SO tepat sekali,
peran Kasir, write gagal dan konflik approval. Jalankan dengan interpreter yang
sama, mengganti path test menjadi `prototype/tests/phase2_browser.py`.

Bukti di `evidence/verification-phase1.json` dan `evidence/verification-phase2.json`;
gate/review per fase di folder yang sama. Ini bukan pengujian produksi, browser
selain Chromium, atau perangkat ponsel fisik. Batas jumlah collection/log belum
ditetapkan menyeluruh; performa pada data besar belum diuji.
