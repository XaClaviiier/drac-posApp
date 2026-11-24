# POS: prototype FigCraft UI-04

Status: artefak FigCraft siap ditinjau, menunggu persetujuan visual sebelum tahap browser.
Seluruh pelanggan, kendaraan, pekerjaan, nominal dan tanggal adalah data contoh.

## Terbaru: UI-04, login dan tiga role (31 Oktober 2026)

Gunakan [file utama](pos-ui.figcraft) atau [versi tanpa gerak](pos-ui-no-motion.figcraft).
Di page `Desktop · Light`, pilih flow **`Login / Desktop Light / UI04`**, lalu Present.
Tiga tombol **Demo Owner**, **Demo Teknisi**, **Demo Kasir** membuka journey sesuai
role. Empat page perangkat/tema menyediakan flow Login yang setara. Frame login
desktop light bernama `UI04 / Light / Desktop / Login / base`; gunakan Zoom to selection
setelah memilihnya bila perlu.

### Cara mencoba

1. **Teknisi:** buka WO, klik `Ubah harga Filter kabin`, lalu simpan demo. State harga
   awal memperlihatkan total Rp 790.000; setelah edit Rp 780.000, master tetap
   Rp 85.000 per pcs. Invoice draf menyalin WO. Contoh edit jasa pada invoice draf
   menghasilkan Rp 770.000, sedangkan WO tetap Rp 780.000.
2. **Owner:** buka Invoice final, lalu koreksi. Pembatalan kuras evaporator mengubah
   tagihan Rp 780.000 menjadi Rp 430.000; penerimaan Rp 500.000 tetap, kelebihan
   bayar Rp 70.000. Skenario koreksi setelah lunas mempertahankan penerimaan
   Rp 780.000 dan kelebihan Rp 350.000. Koreksi kenaikan memiliki pembayaran lanjutan
   yang mempertahankan total revisi Rp 830.000. Tidak ada perpindahan uang nyata.
3. **Kasir:** buka pembayaran sisa dan konfirmasi demo. Journey tidak menuju HPP,
   audit atau koreksi Owner. Teknisi tidak mendapat tujuan pembayaran.
4. **Cari global:** klik `Cari di bengkel...`. Palet berkelompok mengikuti struktur
   command1 dengan token POS. Pilih hasil halaman, pelanggan/kendaraan, WO, invoice,
   atau jasa/barang. Semua hasil contoh menuju kendaraan/dokumen yang konsisten.
   Gulir palet untuk state kosong, memuat dan gagal. Ini skenario terpilih, bukan
   filtering query atau database live. Tidak menampilkan shortcut yang belum berfungsi.
5. Arahkan pointer pada kontrol untuk konfigurasi hover/pressed native. Galeri
   `State interaksi / Light / UI04` atau Dark memperlihatkan default, hover, fokus,
   pressed dan disabled. Keyboard/focus trap serta playback belum dibuktikan headless.
6. Isi panjang memakai viewport gulir vertikal; header dan navigasi tetap terpisah.
   Di ponsel, buka menu lain dari Beranda atau palet pencarian.

### Preview terbaru

Seluruh screenshot dan pratinjau PNG disimpan di `screenshot/`. Ekspor screenshot
berikutnya wajib memakai folder ini, bukan direktori utama `prototype/`.

- Login: [desktop light](screenshot/ui04-login-desktop-light.png), [mobile light](screenshot/ui04-login-mobile-light.png),
  [desktop dark](screenshot/ui04-login-desktop-dark.png), [mobile dark](screenshot/ui04-login-mobile-dark.png).
- [Estimasi WO](screenshot/ui04-estimasi-desktop.png).
- Cari global: [desktop](screenshot/ui04-search-desktop.png), [mobile dark](screenshot/ui04-search-mobile-dark.png).
- [Koreksi setelah invoice lunas](screenshot/ui04-koreksi-invoice-lunas.png).
- [Galeri state dark](screenshot/ui04-state-interaksi-dark.png).

### Bukti dan batas UI-04

- **Observed:** file native utama 3.456.465 byte disimpan lewat FigCraft. Sebelum
  penyimpanan akhir kandidat dibuka dengan `repairs: []`; 6 page, 93.861 layer
  (93.867 node termasuk page). Ada 252 state layar baru pada empat varian, dua galeri,
  dan 4.516 instance kontrol dengan variant Default/Hover/Pressed/Focus/Disabled.
- **Observed:** verifier native final exit 0; [laporan](verification-ui04.json)
  memeriksa 12 graf role hingga seluruh state komponen termasuk Focus. Logout ke
  Login mengakhiri journey; memilih akun demo baru bukan role escape.
- **Observed:** 8 negative checks menolak escape role, salah subtotal, hilangnya
  trigger hover, escape pada Focus, total invoice terlepas dari baris, snippet HPP,
  total tampilan salah dan kontrol tanpa isi materialized. Total kategori/baris,
  adjustment, pembayaran serta teks nominal diperiksa. Pasangan teks token yang
  dihitung memiliki rasio terendah 4,881:1; bukan audit seluruh piksel/disabled/arsip.
- **Observed:** template invoice A4 identik terhadap snapshot pra-UI04. Versi tanpa
  gerak dibuat dari native final yang sama, identik selain konfigurasi motion;
  seluruh durasi 0 ms, transition instant. Preferensi OS tidak dideteksi otomatis.
- **Observed:** render login desktop/mobile kedua tema, WO, search, koreksi invoice,
  state interaksi dan header mobile panjang dilihat. Header yang overlap diperbaiki;
  verifier sekarang menolak judul mobile yang beririsan dengan metadata.
- **Review:** planner/security/reviewer menemukan konteks koreksi/pembayaran revisi,
  cakupan Focus, nilai tampilan vs metadata, snippet HPP, materialisasi kontrol,
  dan header mobile. Temuan diperbaiki dan diuji dengan gate yang diperketat.
  Recheck terpisah mengonfirmasi empat dari lima temuan review; temuan terakhir
  (dua header panjang) kemudian diperbaiki dan dikonfirmasi lewat geometri/render.
- **Batas:** playback hover, interupsi animasi, scrolling presenter, keyboard,
  input form, pencarian/perhitungan live dan autentikasi/otorisasi server belum diuji.
  Proteksi graf demo bukan keamanan aplikasi. Semua data/harga merupakan contoh.
- **Reopen final:** main dan no-motion dibuka dari disk, keduanya 6 page/93.861 layer,
  `repairs: []`. Salinan tanpa gerak tidak membuka cache lama; tab lama ditutup dahulu.
- Flow berawalan **Arsip** mempertahankan layar lama sebagai referensi Owner,
  bukan journey role terbatas. Mulai evaluasi role dari flow **Login ... UI04**.

### Regenerasi dan pemulihan

Sumber aman: [snapshot pra-UI04](pos-ui-before-ui04.figcraft). Jangan memakai file
utama yang sudah mengandung UI-04 sebagai input builder: akan ditolak untuk mencegah
penambahan state ganda. Jangan menjalankan generator UI-01 atas hasil terbaru.
`build_ui04.py` memakai `complete_ui04.py`, membangun node native lewat stdlib Python;
tidak memerlukan CLI/dependency baru. Konstruksi node, bukan patch string source/CSS.

```cmd
"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" -B doc\DBD\prototype\build_ui04.py doc\DBD\prototype\pos-ui-before-ui04.figcraft C:\Users\user\AppData\Local\Temp\opencode\pos-ui04-candidate.figcraft
"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" -B doc\DBD\prototype\verify_ui04.py doc\DBD\prototype\pos-ui.figcraft --source doc\DBD\prototype\pos-ui-before-ui04.figcraft --negative --no-motion-out doc\DBD\prototype\pos-ui-no-motion.figcraft --report doc\DBD\prototype\verification-ui04.json
```

Verifikasi kandidat sebelum mengganti file utama. Pemetaan layar baru ada di
[manifest UI-04](manifest-ui04.json); manifest/verifier baseline di bawah hanya bukti
historis UI-01. Rollback dapat memakai snapshot pra-UI04, tanpa menghapus hasil terbaru.

#### Delivery gate UI-04 (prototype)

- PASS arah/isi: keputusan CONTEXT terbaru, token POS dan struktur command1 dipakai;
  teks Indonesia, data contoh, tanpa logo/foto/testimonial baru atau klaim produksi.
- PASS navigasi/role secara metadata: tujuan ada, 12 graf role dan seluruh variants
  diperiksa, tidak ada role lama pada nama/teks aktif. Tidak ada threshold approval rekaan.
- PASS nominal: baris, ringkasan tampilan, pembayaran dan koreksi direkonsiliasi.
- PASS state: hover/pressed native terpasang pada instance kontrol; Focus/Disabled
  tersedia sebagai variant; galeri hanya dokumentasi. Disabled tidak memiliki aksi.
- PASS kontras token: 20 pasangan teks baru dihitung; minimum 4,881:1.
- PASS render/persistensi: render dilihat dan native tersimpan; bukti reopen di IPD UI-04.
- PASS no-motion manual: konten sama dan durasi nol; OS reduced-motion runtime N/A.
- N/A uji runtime: keyboard, pembaca layar, interupsi, typing, pencarian dan otorisasi.
- N/A cetak fisik: template dipertahankan, tidak diuji dengan printer nyata.

---

## Arsip bukti UI-01 sampai UI-03

Informasi, jumlah node, nama flow dan screenshot di bawah adalah keadaan historis
sebelum UI-04, bukan petunjuk role atau navigasi terbaru.

## Buka hasil

- [Desain editable FigCraft](pos-ui.figcraft)
- [Seluruh menu desktop terang](screenshot/all-desktop-light.png)
- [Seluruh menu desktop gelap](screenshot/all-desktop-dark.png)
- [Seluruh menu mobile terang](screenshot/all-mobile-light.png)
- [Seluruh menu mobile gelap](screenshot/all-mobile-dark.png)
- Work order ukuran asli: [desktop terang](screenshot/desktop-light.png), [desktop gelap](screenshot/desktop-dark.png), [mobile terang](screenshot/mobile-light.png), [mobile gelap](screenshot/mobile-dark.png).
- [Pembayaran mobile](screenshot/payment-mobile-light.png)
- Mekanik: [sedang dikerjakan](screenshot/mechanic-started-mobile.png), [selesai](screenshot/mechanic-completed-mobile.png).

File FigCraft memiliki empat halaman aplikasi dan satu halaman `Invoice · Cetak`.
Setiap halaman aplikasi menyediakan titik mulai POS,
Mekanik dan Kondisi. Tekan Present pada titik mulai yang ingin ditinjau.
Pada shell umum, footer “Pratinjau desain” membuka daftar kondisi pendukung.
`manifest.json` memetakan nama frame ke ID sumber impor; ID native FigCraft dapat berbeda.

## Cakupan

### Tambahan UI-03: animasi UX prototype

Gunakan [file utama beranimasi](pos-ui.figcraft), bukan PNG/PDF, untuk melihat motion.
Alternatif manual: [prototype tanpa gerak](pos-ui-no-motion.figcraft).

Cara mencoba di aplikasi FigCraft:
1. Buka file utama, pilih `Desktop · Light` lalu flow `POS Desktop Light`, tekan Present.
2. Klik kontrol sidebar di kiri atas untuk ciut/perluas. Sebelas menu dasar memiliki
   transisi sidebar dua arah pada light dan dark.
3. Klik ganti tema pada Work order; buka Kasir, klik `Lanjut ke pembayaran`, lalu
   `Kembali ke kasir` atau `Konfirmasi (demo)`.
4. Pada `Mobile · Light`, pilih flow `POS Mobile Light`, tekan Present, lalu buka
   `Menu` dan `Tutup`. Sebelas menu dasar, detail WO, pembayaran dan detail mekanik
   memiliki transisi menu pada kedua tema.
5. Untuk perubahan status, mulai flow `Mekanik Desktop Light` atau `Mekanik Mobile Light`,
   buka tugas contoh, klik `Mulai` lalu `Tandai selesai (demo)`.

Timing dan alasan motion hanya bersumber pada bagian Motion UI-03 di
`../DESIGN_POS_Extend.md`. Sebanyak 112 interaksi existing diperbarui melalui MCP:
44 sidebar, 32 buka/tutup menu, 14 tema alur utama, 14 pembayaran, 8 status mekanik.
Nama 82 container sidebar disamakan untuk pencocokan Smart Animate.

Observed: perintah batch mengembalikan sukses; sampel metadata setiap kelompok
diperiksa. Native disimpan 489.013 byte, ditutup dan dibuka ulang tanpa repair,
tetap lima halaman dan 11.279 layer termasuk template invoice. Setelah reopen,
node 239, 10269, 537 dan 10990 masih menyimpan transisi dan durasi yang ditetapkan.
Render desktop dan mobile dilihat untuk memeriksa frame statis.
Salinan tanpa gerak dibuka tanpa repair; sampel node 239 dan 4650 durasinya 0 ms.

#### Delivery gate UI-03

- PASS R-19/R-31/R-37: tiap gerak memiliki peran dan timing dalam sumber desain.
- PASS R-24/R-26 secara metadata: patch hanya transisi/durasi/easing index 0;
  tujuan dan trigger interaksi existing dipertahankan. Tidak ada fungsi transaksi baru.
- PASS persistensi/R-35 statis: save, close, reopen, inspeksi sampel dan render dilakukan.
- PASS integritas visual terbatas: desktop/mobile light dilihat, geometri, warna,
  teks dan invoice tidak diedit. Pemeriksaan kontras UI-01 tetap bukti historis,
  tidak diklaim dijalankan ulang sebagai audit lengkap UI-03.
- PASS alternatif manual: file tanpa gerak tersimpan dan sampel 0 ms diperiksa.
- UNVERIFIED playback: sesi FigCraft headless menerima `proto.present` tetapi tidak
  menyediakan pemutaran timeline yang dapat diamati. Kelancaran, arah visual menu,
  kecocokan semua shared layer, klik cepat berulang dan interupsi belum dibuktikan.
- UNVERIFIED R-32 dan reduced-motion OS: wajib diperiksa pada presenter/browser nyata.
  Salinan tanpa gerak bukan deteksi otomatis preferensi aksesibilitas.
- N/A dependency/build web: tidak ada kode aplikasi atau dependency yang diubah.

Generator dan manifest baseline belum memuat UI-02/UI-03. File native adalah artefak
terbaru; impor ulang baseline akan kehilangan template dan konfigurasi motion ini.

### Tambahan UI-02: template invoice A4

- Editable: page kelima `Invoice · Cetak`, frame `Invoice A4 / Template siap isi`.
- [PDF satu lembar](invoice-template-a4.pdf) dan [pratinjau PNG](screenshot/invoice-template-a4.png).
- Ubah teks dalam `[kurung]` di FigCraft, duplikasi baris jasa/part sesuai kebutuhan,
  lalu ekspor ulang. PDF adalah hasil cetak statis, bukan formulir PDF interaktif.
- Format awal A4 portrait; printer fisik belum diuji. Untuk invoice panjang,
  tata ulang baris dan buat lembar lanjutan; tidak ada pagination otomatis.
- Kertas putih menggunakan token light existing, juga ketika aplikasi memakai dark.
  Ini dokumen cetak, bukan varian layar aplikasi. Ukuran huruf cetak 10 point untuk
  isi, berbeda dari UI 14–16 px; alasannya skala fisik A4. Revisit setelah uji printer.
- Nama, kontak, harga, pajak dan ketentuan garansi tetap placeholder. Footer penanda
  template dapat diganti setelah semua isian berisi data yang benar.
- Reference lock UI-01 dipertahankan. Refero MCP `NO_SUBSCRIPTION`; URL invoice
  Shopmonkey awal 404, homepage berhasil dibaca live dan menautkan `/product/invoices`.
  Tidak ada klaim menyalin layout invoice atau token hasil ekstraksi situs itu.
- Observed: screenshot 893 × 1263 dilihat, 44 layer anak berada di dalam frame
  595,276 × 841,89; PDF dibuka dan terbaca satu halaman. Kontras teks sekunder pada
  putih 6,04:1; teks utama pada header tabel 12,78:1 (checker exit 0).
- Observed: file native 488.238 byte ditutup dan dibuka ulang tanpa repair,
  lima halaman dan 11.279 layer; halaman cetak beserta frame tersimpan.
- Generator `build_design.py`, sumber JSON, manifest dan verifier UI-01 masih
  merepresentasikan baseline empat halaman. UI-02 ditambahkan langsung lewat MCP;
  jangan mengganti file native dengan impor baseline bila ingin mempertahankan template.

#### Delivery gate UI-02 (desain cetak statis)

- PASS R-02/17/18/23/36/38: teks dan render diperiksa; tidak ada klaim usaha, harga,
  logo atau pelanggan buatan; seluruh nilai isian diberi kurung placeholder.
- PASS R-25: pasangan teks paling lemah yang dipakai 6,04:1, checker dijalankan.
- PASS R-35: render diperiksa, PDF satu halaman dibaca, native ditutup dan dibuka ulang.
- PASS R-37/C-1/C-3: token existing, hierarki kendaraan, tabel dan total mengikuti brief.
- PASS purpose gate: pemisah mengelompokkan rincian dan total; Inter menjaga keterbacaan;
  tanpa ikon, gradien, shadow, kartu dekoratif atau animasi.
- PASS liveliness: ENERGY 1 / RHYTHM 2 / MOTION 1; plat dan total menonjol,
  jarak memisahkan identitas, rincian, dan pembayaran. Warna teks mewarisi navy POS;
  aksen aksi tidak dipakai sebagai hiasan pada dokumen cetak.
- N/A R-03/24/26/27/28/32/34: tidak ada UI interaktif, navigasi, FAQ, tema toggle,
  loading, atau layout mobile yang dikirim. Dokumen A4 dibaca memakai zoom PDF.
- PASS R-33: dibuat langsung memakai layer FigCraft, tanpa skrip penambal source.
- Batas: invoice belum terhubung ke transaksi atau tombol aplikasi; perhitungan,
  pagination otomatis, printer dan PDF bertag aksesibilitas belum diverifikasi.

138 frame, termasuk 44 tampilan dasar untuk 11 menu pada dua ukuran dan dua tema.
Tersedia 22 varian sidebar ciut, empat pembayaran, detail WO, detail mekanik beserta
status dimulai/selesai, menu mobile, contoh form master dan hasil pengaturan.
Galeri kondisi berisi kosong, memuat, error, offline, validasi, konfirmasi,
konflik versi, pilihan item statis dan menyimpan draf.

Ini prototype visual dengan navigasi antar-frame. Field, pemilihan metode bayar,
filter, katalog dan daftar data merupakan representasi statis. Tidak ada input
form, transaksi, penyimpanan, otorisasi server atau sinkronisasi yang dijalankan.
State pendukung adalah contoh desain bersama, bukan implementasi kondisi runtime
untuk setiap modul. Nama dan identitas final bengkel belum ditetapkan.

## Bukti verifikasi, 30 Oktober 2026

Perintah dijalankan dari root POS memakai interpreter existing, tanpa dependency baru:

```cmd
"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" -B doc\DBD\prototype\build_design.py
"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" -B doc\DBD\prototype\verify_design.py
```

Keduanya exit 0. Hasil: 138 frame, 44 dasar, 11.234 node, 1.462 tautan.
Generator memeriksa batas geometri frame, target navigasi dan graf Mekanik tanpa
harga. Verifier mencocokkan 11 menu baseline, empat pembayaran, ukuran hotspot
non-teks minimal 44 px, dan kontras teks. Hasil hitung berada di `verification.json`.

Kontras memakai luminans sRGB WCAG dengan surface di posisi awal teks; teks
background yang tertutup modal tidak dihitung. Hasil tidak menemukan pelanggaran
pada pasangan yang diperiksa. Pasangan 4,424:1 hanya dipakai pada teks “AC” besar
dan tebal di sidebar ciut, yang memakai ambang teks besar 3:1. Metode ini bukan
pengukuran setiap piksel, seluruh batas kontrol, atau kontras saat fokus.

Impor REST JSON berhasil tanpa warning. File native disimpan sebesar 485.762 byte,
seluruh tab hasil impor ditutup, lalu file native dibuka kembali dari disk:
empat halaman, 11.234 layer, `repairs: []`. Inspeksi sesudah reopen mengonfirmasi
tautan sidebar ciut dan pergantian tema tetap tersimpan.

PNG desktop/mobile/light/dark telah dirender dan dilihat. Review terpisah menemukan
tiga masalah: tautan detail tidak sesuai pilihan, alur mekanik belum sampai selesai,
dan penugasan Andi tidak konsisten. Ketiganya diperbaiki; verdict pass menyatakan
3 resolved, 0 partial, 0 unresolved. Verdict tersebut khusus tiga temuan ini.

Detector Impeccable dijalankan atas generator dan menghasilkan `[]`; karena target
berupa Python/artefak FigCraft, hasil ini tidak dipakai sebagai bukti audit HTML/CSS.

### Jejak kegagalan yang diperbaiki

- Perintah `python` standar mengarah ke alias Microsoft Store; interpreter existing
  ditemukan di direktori Python312 dan dipakai dengan path absolut.
- Generator awal exit 1: `Missing target Light/Desktop/detail/collapsed`.
  Kontrol collapse pada route tanpa varian dihilangkan, validasi target dipertahankan.
- Verifier awal exit 1 dengan 21 kegagalan kontras, 4,325:1 pada biru di surface aktif.
  Teks navigasi aktif dan badge memakai teks utama existing; biru tetap dipakai
  untuk ikon/interaksi. Semua pemeriksaan relevan kemudian dijalankan ulang.

## Pemeriksaan navigasi statis

Pemeriksaan di bawah berasal dari graf sumber dan metadata impor, bukan klik runtime.

| Elemen | Tujuan yang diperiksa |
|---|---|
| Navigasi shell umum | 11 frame menu pada tema/perangkat yang sesuai |
| Tema | Frame pasangan light/dark dengan route dan state sama |
| Sidebar ciut | Varian collapsed untuk 11 menu desktop; kontrol kembali ke base |
| Menu mobile | Halaman menu umum atau menu mekanik, dengan tombol Tutup |
| Terima mobil / simpan nota demo | Frame nota servis / papan WO contoh |
| Kartu DD 1248 KL / Lihat detail | Detail contoh dengan plat yang sama |
| Kartu kendaraan lain | Tanpa tautan detail; label `(statis)` terlihat |
| Riwayat / cari kendaraan | Frame riwayat plat contoh |
| Kasir / lanjut pembayaran | Pembayaran DD 3107 MA, total contoh Rp 450.000 |
| Konfirmasi pembayaran demo | Daftar invoice; tidak melakukan transaksi |
| Invoice lunas/tempo | Daftar statis, tanpa tautan pembayaran yang salah |
| Katalog item | Penjelasan pemilihan statis, lalu kembali ke kasir |
| Mekanik / buka DD 1248 KL | Detail mekanik tanpa harga |
| Mulai / tandai selesai | State `started`, lalu `completed`, badge Selesai |
| Kembali ke tugas | Frame Mekanik; graf tidak mencapai halaman berharga |
| Tambah jasa/part | Contoh form master dan jalan kembali ke daftar |
| Simpan pengaturan demo | State hasil simulasi dan jalan kembali |
| Galeri kondisi | Sembilan kondisi, aksi pemulihan dan jalan kembali |

## Delivery gate desain statis

Status PASS di bawah hanya berlaku pada bukti visual/struktur artefak ini.
N/A berarti pemeriksaan runtime belum berlaku dan tetap wajib pada tahap browser.

- R-02 PASS: generator menolak em dash dalam teks UI.
- R-03 PASS pada ukuran 1440×900 dan 390×844: batas frame diperiksa, montage dilihat; reflow kontinu belum diuji.
- R-17 PASS: angka dinyatakan sebagai data contoh, tidak menjadi klaim bisnis.
- R-18 PASS: tidak ada testimonial atau identitas pelanggan sebagai bukti sosial.
- R-23 PASS: nama sementara berupa teks, tanpa logo/foto baru; konten contoh diberi label.
- R-24 PASS: 11 menu memiliki frame tujuan; seluruh target sumber terurai.
- R-25 PASS untuk pasangan teks yang dihitung dalam verification.json, dengan batas metode di atas.
- R-26 PASS untuk cakupan navigasi desain: target ada, contoh statis ditandai; fungsi input runtime N/A.
- R-27 PASS: frame kosong, memuat dan error tersedia di empat varian.
- R-28 PASS: tidak ada FAQ.
- R-32 N/A: keyboard, focus trap dan fokus terlihat perlu diuji di browser.
- R-33 PASS: generator membangun geometri impor, tidak menambal source/CSS aplikasi.
- R-34 PASS secara visual: dua tema dirender dan diperiksa.
- R-35 PASS untuk pengganti mockup statis: impor, render, inspeksi graf dan reopen dilakukan; click-through runtime belum dilakukan.
- R-36 PASS: tidak ada klaim keamanan/performa/sertifikasi atau bukti pelanggan buatan.
- R-37 PASS: mengikuti reference lock dan direction contract yang sudah disetujui.
- R-38 PASS: seluruh data ilustratif ditandai; placeholder identitas bukan fakta produksi.
- R-01 PASS: warna mengikuti peran token prototype; tidak ada gradien/glow dekoratif.
- R-04 PASS: ikon berfungsi sebagai petunjuk jenis menu, disertai label pada navigasi penuh.
- R-06 PASS: Inter untuk keterbacaan form/tabel sesuai token; tidak memakai mono dekoratif.
- R-07 PASS: tidak ada grid latar dekoratif.
- R-08 PASS: tombol tidak memakai panah dekoratif.
- R-09 PASS: badge mengomunikasikan status pekerjaan/penyimpanan.
- R-10 PASS: tidak ada glassmorphism.
- R-12 PASS: tidak ada shadow berulang pada kartu; modal dibedakan dengan scrim.
- R-13 PASS: tidak ada glow.
- R-14 PASS: kartu kendaraan mengikuti entitas papan, bukan grid fitur pemasaran.
- R-19 PASS pada mockup: state navigasi tersedia; animasi dan reduced-motion runtime N/A.
- R-22 PASS: tidak ada ilustrasi generik.
- Liveliness PASS: dial dan alasan berada di token/reference lock; plat dominan, ruang kerja terpisah, aksen mengarahkan aksi.
- C-1 PASS: keputusan mayor terlacak ke brief dan ledger DBD.
- C-2 PASS pada batas mockup: kontrol navigasi memiliki tujuan; field/data statis dinyatakan.
- C-3 PASS: isi berasal dari 11 menu existing dan alur bengkel.
- C-4 PASS pada varian statis yang diperiksa; zoom, keyboard, koneksi dan ukuran antara N/A.
- C-5 PASS: tidak ada bukti sosial atau klaim bisnis buatan.
- R-05 PASS: komposisi mengikuti form penerimaan, papan, kasir, daftar, riwayat dan pengaturan.
- R-11 PASS: geometri mengikuti token prototype, bukan pill seragam.
- R-15 PASS: aksi memakai istilah tugas bengkel.
- R-16 PASS: tidak ada promosi/buzzword generik.
- R-20 PASS: identitas kendaraan dan konteks bengkel mendominasi informasi.
- R-21 PASS: kedua tema diminta user dan tersedia.
- R-29 PASS: peran biru interaksi, hijau keberhasilan, amber peringatan dan merah error mengikuti sistem token.
- R-30 PASS: referensi dipinjam terbatas sesuai brief, bukan keseluruhan merek lain.
- R-31 PASS: alasan mayor tercatat dalam ledger DBD.

## Referensi dan batas selanjutnya

Reference lock dan keputusan visual tetap bersumber pada [DBD](../dbd.md) dan
[token prototype](../DESIGN_POS_Extend.md). Refero MCP mengembalikan
`NO_SUBSCRIPTION`; hasil Refero tidak diklaim tersedia. Halaman resmi
[Shopmonkey](https://www.shopmonkey.io/) dan [Calendly](https://calendly.com/)
dibaca ulang melalui Jina pada sesi ini. Pembacaan tersebut tidak mengukur CSS/font.

Tahap browser memerlukan persetujuan visual. Pada tahap itu verifikasi keyboard,
reduced-motion, aksesibilitas form, ukuran antara/tablet, zoom dan perilaku kontrol
harus dilakukan pada implementasi nyata. Backend, keamanan aplikasi dan PRD §9
belum dapat dinyatakan selesai dari artefak FigCraft.
