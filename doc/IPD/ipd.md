# IPD: Implementation Plan Documentation — POS Bengkel AC Mobil

Dokumen ini menjawab: **dikerjakan dalam urutan apa, dan bagaimana tahu sudah selesai.**
Bergantung pada PRD, AFD, TRD, BSD, DBD. Dokumen yang dipakai tiap sesi kerja:
agent mengambil **satu irisan**, bukan seluruh dokumen.

Sumber awal: `../metaprompt-pembentukan-sistem.md` (M1 peta jalan, M2 prompt fase).

---

## 1. Urutan fase
Urut berdasarkan dependensi dan risiko. Risiko terbesar diuji lebih awal.
| ID | Fase | Tujuan | Bergantung pada | Status |
|---|---|---|---|---|
| FS-01 | ISI: | | | Belum |

## 2. Detail irisan

### AUTH-01: Fondasi aplikasi dan autentikasi nyata (2026-11-17)

- **Permintaan:** user menyetujui mulai dari fondasi/login; pengunduhan dependency,
  engine terpisah dan database baru diizinkan melalui form setup. User meminta
  rekomendasi terkait hosting biasa. MySQL portable lokal dipilih, tanpa Docker
  atau Windows service; keputusan hosting produksi belum diubah.
- **Rencana dan kriteria sebelum eksekusi:** [auth-01-plan.md](auth-01-plan.md).
  Target login/logout, sesi cookie, akun aktif dan izin Owner/Teknisi/Kasir nyata;
  tidak membuat modul bisnis palsu atau mengimpor seluruh SQL draf.
- **Isolasi:** aplikasi baru di `application/`, runtime/data lokal di `.local/`
  yang diabaikan Git. Tidak mengubah MariaDB XAMPP atau database existing.
- **Verifikasi wajib:** migrasi pada MySQL aktual, test jalur utama/gagal,
  penolakan lintas peran, CSRF, logout/sesi invalid, throttling dan browser
  desktop/ponsel. Kredensial tidak dicetak atau dipasang sebagai password bawaan.
- **Hasil:** aplikasi Laravel/React nyata tersedia di `application/`, memakai
  MySQL 8.4.13 lokal terpisah. Login/logout sesi cookie, akun UUID, peran/permission
  server, akun nonaktif, audit auth, throttling dan perintah akun interaktif
  diimplementasikan. Tidak ada akun/password bawaan, signup publik atau token auth
  dalam localStorage. Landing berisi akun/akses nyata, bukan modul POS palsu.
- **Verifikasi:** 49 test Pest/272 assertion pada MySQL terisolasi, 11 test
  frontend, TypeScript strict/build Vite dan enam test Playwright lulus.
  Browser membuktikan login tiga peran, akses silang, replay cookie lama setelah
  logout, penolakan CSRF, password salah, tema, Poppins, fokus dan reflow ponsel.
  Screenshot akhir menunggu transisi selesai; lima capture diperiksa.
- **Review:** pemeriksaan keamanan independen tidak menemukan temuan penting.
  Review UI menemukan pemulihan logout 401 dan ring fokus programatik; perbaikan
  diverifikasi dengan regresi dan verdict akhir menyatakan temuan terdaftar selesai.
  Label izin juga diterjemahkan tanpa mengubah hak server.
- **Temuan integrasi:** parser ID frontend diselaraskan ke UUID; fixture test
  sesi database diperbaiki agar benar-benar mengirim cookie JSON; Vitest dipilih
  yang kompatibel dengan Vite 8 tanpa menurunkan pemeriksaan strict.
- **Preservasi:** database existing/XAMPP tidak disentuh. Akun browser hanya pada
  database e2e, sudah dinonaktifkan dan kredensial sementara dihapus. Runtime MySQL
  dan aplikasi lokal dapat dijalankan ulang melalui README; tidak memasang service.
- **Bukti/cara mencoba:** [auth-01-verification.json](auth-01-verification.json),
  [README aplikasi](../../application/README.md), [kontrak BSD](../BSD/auth-01.md).
- **Status:** selesai untuk fondasi/login AUTH-01. Modul bisnis, PWA/offline,
  deployment dan kelayakan provider hosting belum diimplementasikan/diverifikasi.
  Idle timeout 120 menit belum diuji dengan menunggu browser selama 120 menit;
  invalidasi cookie dan pemulihan sesi berakhir telah diuji.


### DB-02: SQL dan ERD seluruh sistem — draf review (2026-11-17)

- **Permintaan:** user memilih SQL dan ERD seluruh sistem sebagai draf review,
  termasuk modul yang belum memiliki skema fisik. Tidak mengimpor ke database
  aplikasi dan tidak mengesahkan kebijakan bisnis yang masih terbuka.
- **Rencana:** turunkan DB-01 tanpa mengganti identitas/revisi pelanggan–layanan;
  tambahkan autentikasi/katalog, antrean, invoice/pembayaran, pembelian/penerimaan,
  stok/retur, pengeluaran, audit dan idempotensi. SQL dan ERD disimpan di BSD.
- **Kriteria sebelum pengerjaan:** (1) DDL memiliki PK/FK/UNIQUE/CHECK dan ERD
  mencerminkan tabel serta FK yang sama; (2) impor pada instance SQL sementara
  terisolasi dan uji jalur sah/gagal untuk snapshot, qty, duplikat dan uang;
  (3) keputusan teknis tambahan, aturan lintas tabel yang perlu server, serta
  kompatibilitas engine yang benar-benar diuji dicatat secara eksplisit.
- **Batas:** satu irisan artefak database, bukan implementasi aplikasi. Tidak
  mengaktifkan HPP otomatis/profit/gateway. Runtime XAMPP terdeteksi MariaDB
  10.4.32, bukan MySQL; target MySQL tetap mengikuti CONTEXT. Database existing
  tidak diubah dan tidak ada dependency yang dipasang.
- **Hasil:** `doc/BSD/pos-schema.sql` berisi 53 tabel, 122 FK, empat view dan seed
  tiga peran; `doc/BSD/erd.md` menampilkan 11 diagram modul. Panduan review,
  keputusan teknis tambahan dan batas server berada di `database-review.md`.
- **Verifikasi aktual:** impor file SQL final pada database kosong di instance
  privat MariaDB 10.4.32 berhasil; 60 pemeriksaan SQL/struktur lulus. Inventaris
  kolom/FK aktual cocok dengan ERD; 11 diagram dirender Chrome tanpa error.
  Review fisik independen menemukan kelemahan CHECK NULL pada idempotensi yang
  telah diperbaiki dan diverifikasi; review finansial tidak menemukan masalah penting.
- **Bukti:** `doc/BSD/database-verification.json`; hasil ini bukan uji aplikasi
  Laravel, concurrency, otorisasi atau runtime MySQL. SQL privat dihentikan,
  listener ditutup dan data uji dihapus; database existing tidak disentuh.
- **Status:** artefak SQL/ERD selesai sebagai draf review, belum migrasi atau
  pengesahan produksi. Aturan refund/retur dan keputusan terbuka tetap memerlukan
  persetujuan sebelum endpoint terkait diaktifkan. HPP/profit/gateway tetap ditunda.


### FIG-CUSTOMER-HISTORY-01: Pelanggan, kendaraan dan riwayat lintas kunjungan (2026-11-16)

- **Permintaan:** user menyetujui prioritas berikutnya setelah integrasi invoice
  Maya. Kerjakan pada file FigCraft yang sama; simpan backup file terkini, termasuk
  perubahan sesudah delivery sebelumnya. Prototype browser dan backend tidak diubah.
- **Sumber:** CONTEXT §2.1–§2.3, PRD F-02/F-07, AFD peta P-05/P-06 serta BSD
  §2.2–§2.5. Token/Poppins tetap bersumber pada DESIGN_POS_Extend.
- **Kriteria sebelum eksekusi:** daftar/detail pelanggan dan kendaraan, contoh
  pencarian nama/plat ternormalisasi, dua pelanggan dengan telepon sama tanpa
  penggabungan, riwayat lebih dari satu kunjungan, dokumen kunjungan lama read-only,
  serta pembukaan dokumen Maya 0147 yang mengikuti state layanan/invoice existing.
- **Perubahan master:** edit contoh telepon tidak menulis ulang snapshot lama;
  Owner mengganti plat dengan alasan dan menolak plat yang sudah digunakan.
  Riwayat tetap memakai ID kendaraan yang sama. Contoh nonaktif/aktif kembali
  mempertahankan riwayat dan mencegah pemilihan master nonaktif pada kunjungan baru.
  Pencarian plat historis otomatis tidak ditambahkan karena belum diputuskan BSD.
- **Kunjungan baru:** contoh tambahan REG-DEMO-0150 menggunakan kendaraan existing
  dan pelanggan yang dipilih eksplisit. Telepon/plat disalin saat review; keluhan
  wajib. Simpan tidak mengubah REG-0140/0147 atau membuat invoice/pembayaran.
  Contoh ini berhenti pada registrasi baru; tidak mengarahkan dokumen 0150 ke
  diagnosa/invoice 0147. Satu tambahan per reset demo bukan batas produksi.
- **Data contoh:** kunjungan historis tambahan REG/SO/INV-DEMO-0140 dengan total
  Rp150.000 dan pelanggan Arif Ramadhan merupakan fixture demonstrasi, bukan data
  nyata atau pembacaan database. Riwayat 0147 memakai state existing ketika ada.
- **Verifikasi:** klik berurutan desktop/ponsel dengan nilai runtime; master vs
  snapshot, perubahan plat Owner/alasan/duplikat, pemilihan pelanggan berbeda,
  nonaktif, validasi/offline/gagal simpan, dokumen lama tanpa aksi bayar, integrasi
  history dari POS, tema, gulir, font, ZIP/readback dan regresi pilihan jalur lama.
  Pasang probe terbatas sebelum preview, lalu hapus sebelum simpan.
- **Batas:** isian/pencarian berupa contoh terbatas; belum database, pencarian
  global, autentikasi, migrasi atau pencetakan nyata. Tidak membuat refund/retur.
- **Hasil:** 82 frame pelanggan/kendaraan/riwayat pada desktop dan ponsel,
  dengan 29 field mode, 707 aksi kontrol dan 60 tautan riwayat POS diperbarui.
  Profil Maya/Arif tetap terpisah meskipun telepon sama; dokumen lama tetap
  mempertahankan snapshot setelah perubahan master. Registrasi tambahan 0150
  memakai pelanggan yang dipilih dan tidak diarahkan ke dokumen layanan 0147.
- **Playback aktual:** satu run lengkap lulus 312 langkah, 38 pemeriksaan nilai
  runtime dan enam pemeriksaan kontrol nonaktif. Cakupan meliputi validasi,
  duplikat plat, alasan Owner, nonaktif/aktif kembali, offline/gagal simpan,
  pemisahan riwayat pelanggan, snapshot baru/lama, invoice Maya Rp160.000 serta
  akses invoice baca untuk Teknisi. Delapan pembukaan dokumen tanpa konteks
  layanan/invoice mengarah ke penjelasan belum tersedia pada kedua perangkat.
- **Regresi dan tampilan:** 18 pemeriksaan peran SO serta 80 jalur kasir,
  Registrasi dan Diagnosa lulus. Light/Dark pulang-pergi lulus di kedua perangkat;
  gulir roda ponsel mencapai 498 px dan kontrol bawah berhasil digunakan.
  Enam render native diperiksa pada pilihan desktop/ponsel dan tema, termasuk
  nota historis yang tetap putih. Poppins tidak memiliki font hilang.
- **Preservasi file:** seluruh 13.835 node baseline dipertahankan; perubahan
  pada node lama terbatas pada tautan riwayat serta daftar frame/flow halaman.
  File akhir memuat 16.526 node dan 442 frame pada empat halaman, ZIP valid,
  dua hash gambar referensi tetap sama dan seluruh frame baru terbaca setelah
  pembukaan ulang. Tidak ada hotspot uji sementara tertinggal. Backup baseline
  dan backup saat melanjutkan sesi tersedia pada folder `archive`.
- **Kendala pengujian:** runner pointer diperbaiki untuk menunggu geometri gulir
  dan hotspot serta membatasi percobaan klik ulang ketika masih di frame asal.
  Predikat nilai dan tujuan navigasi tetap wajib lulus; laporan 312 langkah
  berasal dari run lengkap sesudah perbaikan, bukan gabungan percobaan gagal.
  Penyebab internal kegagalan awal belum dibuktikan.
- **Bukti:** `prototype/figcraft/evidence/customer-history-verification.json`,
  `customer-history-playback.json`, `customer-history-regression.json`,
  `customer-history-delivery.json`, `customer-history-preservation.json` dan
  `customer-history-test-observations.json`. Cara mencoba mengikuti README
  prototype; file utama tetap `prototype/figcraft/pos-kasir.figcraft`.
- **Status:** selesai untuk irisan prototype. Ketikan bebas, database,
  autentikasi/server, pencarian seluruh pelanggan, printer/PDF nyata dan koreksi
  invoice Owner lengkap belum terintegrasi. Tab, screen reader serta reflow
  otomatis menyeluruh belum diverifikasi. Batas fixture contoh tetap berlaku.

### FIG-MAYA-INVOICE-01: SO Maya sampai pembayaran dan nota (2026-11-15)

- **Permintaan:** user menyetujui prioritas menyambungkan SO Maya sampai invoice,
  pembayaran dan nota. Tetap satu file FigCraft; tidak mengubah prototype browser.
- **Sumber:** CONTEXT §2.2, §2.4, §2.6–§2.8; PRD F-06/F-07/F-14/F-18;
  AFD §2.3–§2.4; BSD kontrak invoice WEB-04. Token tetap pada DESIGN_POS_Extend.
- **Kriteria sebelum eksekusi:** jalur registrasi Maya, estimasi dua item, SO,
  penugasan/progres/realisasi, penyerahan, pemilihan kartu POS, pembuatan draf,
  penerbitan, pembayaran penuh, nota dan riwayat contoh terhubung. Identitas,
  jasa/part, qty/satuan dan nominal yang diserahkan dibawa ke invoice/nota.
  Pilihan transaksi hanya preview; draf dan penerbitan adalah aksi eksplisit.
- **Penguncian:** Kasir/Owner menerbitkan dan membayar; Teknisi tidak. Draf hanya
  satu per SO dan dibuka kembali saat dipilih ulang. Terbit mengunci SO; pembayaran
  tidak mengeluarkan stok lagi. Penyerahan ditarik/berubah membuat draf perlu
  pemeriksaan, bukan menimpa snapshot. Koreksi harga Owner lengkap tetap irisan lain.
- **Pembayaran:** tunai menghitung kembalian dan menolak kekurangan; QRIS/transfer
  meminta pemeriksaan dana; transfer juga meminta referensi contoh. Perubahan
  metode mereset pemeriksaan. Invoice Rp0 langsung Lunas tanpa catatan pembayaran.
  QRIS/rekening asli belum diberikan: tampilkan keterangan, jangan membuat aset
  atau nomor palsu. Semua pemeriksaan uang masuk tetap simulasi eksplisit.
- **Verifikasi:** playback berurutan desktop/ponsel dari registrasi hingga nota;
  nominal Rp150.000/Rp160.000 serta pelepasan part; guard peran, draf berulang,
  transaksi lunas tidak dibayar ulang, final lock, offline/konflik/gagal/hasil
  belum pasti, pergantian metode dan catatan Rp0. Periksa font, tema, gulir,
  referensi, file tersimpan/readback dan regresi pilihan jalur sebelumnya.
- **Batas:** contoh input dan mode native, bukan backend/autentikasi/stok/uang
  nyata. Cetak/PDF berupa tampilan nota; printer dan ekspor PDF aplikasi belum
  dihubungkan. Tidak mengaktifkan gateway, refund atau retur fisik.
- **Hasil:** 58 frame ditambahkan pada file yang sama; dokumen gabungan berisi
  360 frame, 2.429 instance komponen, 26 field mode untuk invoice Maya dan 434
  kontrol navigasi/aksi tambahan. Identitas dan realisasi diteruskan ke draf,
  invoice final, pembayaran, nota dan riwayat kunjungan contoh.
- **Playback aktual:** checkpoint merekam 398 langkah berhasil dan 52 pemeriksaan
  nilai runtime pada desktop/ponsel. Alur registrasi sampai nota Rp160.000 lulus;
  tunai Rp200.000 menghasilkan kembalian Rp40.000. QRIS/transfer, pemeriksaan ulang
  setelah ganti metode, pelepasan part menjadi Rp60.000, invoice Rp0 tanpa catatan
  pembayaran, batas peran serta kondisi offline/gagal/belum pasti lulus.
- **Penguncian tambahan:** 68 langkah dan enam pemeriksaan runtime lulus untuk
  penarikan Owner lalu penyerahan ulang dengan nominal sama, reset demo eksplisit,
  larangan menarik invoice final dan pembukaan invoice existing dari SO terkunci.
  Penarikan memberi penanda draf kedaluwarsa yang tidak hilang hanya karena nilai
  biaya sama. Rebase/koreksi Owner lengkap masih di luar irisan ini.
- **Pemeriksaan lain:** 18 pemilihan cabang engine diperiksa memakai mode dokumen
  eksplisit; dibedakan dari playback GUI. Regresi pilihan modul sebelumnya lulus
  98 pemeriksaan (18 rute penyelesaian sesuai peran dan 80 jalur kasir/registrasi/
  diagnosa). Sembilan render native disiapkan; tema Light/Dark pulang-pergi lulus
  pada desktop/ponsel. Gulir roda ponsel mencapai 662 px dan tombol bawah nota
  berhasil dipakai. Poppins tidak memiliki font hilang.
- **Kendala dan pemulihan:** geometri preview sempat null dan input/screenshot
  tidak tersedia. User memastikan FigCraft terlihat; pemulihan jendela asinkron
  memulihkan koneksi, lalu kasus tertunda diteruskan dari checkpoint. Jumlah
  langkah mencakup pemeriksaan berhasil dari beberapa percobaan, bukan tautan unik.
  Hotspot uji sementara dihapus; dokumen aktif tidak menyisakan node uji.
- **File:** ZIP valid, empat halaman dan dua hash gambar referensi dipertahankan;
  file dibuka ulang tanpa perbaikan data dan dibaca melalui CLI. Bukti utama pada
  `prototype/figcraft/evidence/maya-invoice-verification.json`,
  `maya-invoice-withdrawal.json`, `maya-invoice-model-checks.json`,
  `maya-invoice-delivery.json` dan `maya-invoice-file-info.json`.
- **Status:** selesai untuk irisan prototype. Input bebas, penyimpanan/server,
  autentikasi nyata, stok, uang, printer/PDF aplikasi, editor koreksi/rebase Owner
  lengkap dan riwayat semua pelanggan belum dibuat. QRIS/rekening asli belum
  diberikan. Keyboard, screen reader dan reflow menyeluruh belum diverifikasi.

### FIG-SERVICE-ORDER-01: Pengerjaan dan realisasi SO (2026-11-15)

- **Permintaan:** lanjut membangun prototype setelah Diagnosa & Estimasi dan
  revisi label Setuju. Irisan ini meneruskan SO-DEMO-0147/Maya/DD 1248 KL dari
  estimasi dua item Rp150.000 ke penugasan, progres, realisasi dan serah kasir.
  File utama tetap satu; backup ZIP dibuat sebelum edit.
- **Sumber:** CONTEXT §2.3–§2.6, PRD F-05/F-14, AFD §2.2–§2.3, BSD §2.11–§2.14.
  Browser lama masih memiliki utama/anggota; prototype baru mengikuti keputusan
  2026-11-11 bahwa Teknisi setara, minimal satu sebelum mulai. Token dan Poppins
  serta komponen dari irisan sebelumnya dipakai ulang.
- **Kriteria sebelum eksekusi:** daftar/detail, pemilihan satu/dua Teknisi,
  mulai/tunda/lanjut/selesai/batal, estimasi read-only, salin realisasi secara
  eksplisit, contoh harga lokal dengan alasan/Setuju untuk tambahan biaya,
  validasi qty pcs, simpan/revisi realisasi, riwayat serta batas peran tersedia
  di desktop/ponsel. Nilai tersimpan harus terbawa lintas progres pada journey SO.
- **Penguncian:** Teknisi tidak merevisi Selesai/Dibatalkan. Owner membuka SO
  Selesai dengan alasan, menarik antrean sebelum revisi, dan tidak membuka invoice
  final atau SO Dibatalkan. Penyerahan membutuhkan realisasi tersimpan; SO Selesai
  boleh diserahkan Teknisi/Owner, SO Dibatalkan berbiaya hanya Owner, tanpa biaya
  tidak ditagihkan. Penyerahan belum membuat invoice atau menerima pembayaran.
- **Verifikasi:** input presenter pada skenario bisnis, guard, nilai lintas
  progres, persetujuan ulang setelah perubahan, tema, gulir ponsel, font/render,
  file tersimpan dan regresi pilihan jalur modul sebelumnya. Native variables
  boleh dipakai untuk state demo; ini bukan perubahan skema atau backend.
- **Batas:** contoh input, penyimpanan, konflik/offline dan stok tetap simulasi;
  tidak mengklaim server, reservasi, autentikasi, printer atau pembayaran nyata.
  Journey invoice untuk SO Maya tidak dipasangkan ke contoh kasir Rina yang berbeda.
- **Hasil:** 92 frame SO ditambahkan ke file yang sama, sehingga total menjadi
  302 frame pada empat halaman. Ada 534 kontrol navigasi/aksi SO, 1.981 instance
  komponen pada dokumen gabungan, serta Poppins tanpa font hilang. Dua gambar
  referensi tetap utuh; layar kerja memakai layer native.
- **Playback aktual:** 228 langkah SO desktop/ponsel lulus, termasuk penugasan B
  saja/keduanya, validasi qty dan alasan, persetujuan yang direset setelah edit,
  kenaikan per baris walau total turun, status, batas peran, penyerahan, penarikan,
  pembukaan kembali, invoice final, konflik, offline, gagal simpan, serta konfirmasi
  sebelum meninggalkan isian. Rp160.000 bertahan melalui tunda, selesai, antrean,
  penarikan dan buka kembali; pelepasan contoh part belum dipakai menghasilkan
  Rp60.000. Estimasi acuan tetap Rp150.000. Tambahan 18 pemeriksaan penyelesaian
  sesuai peran dan 80 pemeriksaan pilihan jalur modul sebelumnya lulus.
- **Temuan runtime:** aksi setVariable diterima engine tetapi nilai tidak
  bertahan pada playback terpasang. State SO dikompilasi menjadi 32 field dengan
  mode native independen dan diuji ulang dalam perjalanan berurutan. Ini state
  demo terbatas, bukan perubahan data atau otorisasi server. Riwayat harga Owner
  tetap contoh; invoice Maya belum diintegrasikan ke alur pembayaran existing.
- **Render dan file:** delapan ekspor native diperiksa; pergantian Light/Dark
  pulang-pergi lulus pada desktop/ponsel. Gulir ponsel mencapai 724 px dan kontrol
  bawah berhasil menyimpan realisasi. ZIP tersimpan valid, hash kedua referensi
  cocok, lalu file dibaca kembali melalui CLI. Bukti di
  `prototype/figcraft/evidence/service-order-verification.json`,
  `service-order-regression.json`, `service-order-delivery.json` serta
  `service-order-file-info.json`; cara mencoba pada README di folder yang sama.
- **Status:** selesai untuk irisan prototype SO. Ketikan bebas/katalog lengkap,
  integrasi invoice Maya, server, stok/pembayaran/printer nyata, navigasi keyboard
  penuh, screen reader dan reflow otomatis belum diverifikasi atau dibangun.

### FIG-COPY-01: Label Setuju (2026-11-15)

- **Permintaan:** ganti label kontrol persetujuan estimasi menjadi Setuju.
- **Kriteria sebelum edit:** seluruh varian normal/terpilih pada desktop/ponsel
  diperbarui di file yang sama; target navigasi dan syarat approval dipertahankan.
- **Verifikasi:** baca ulang properti label native serta periksa toggle contoh
  desktop/ponsel; sumber konstruksi dan pemetaan mengikuti label baru.
- **Hasil:** 12 instance diperbarui menjadi Setuju/✓ Setuju, meliputi skenario
  normal, harga lokal dan satu item pada desktop/ponsel. Semua label dibaca ulang;
  target/interaksi tetap sama. Empat perpindahan toggle desktop/ponsel lulus.
  Bukti pada `prototype/figcraft/evidence/approval-label-update.json` dan revisi
  metadata `diagnosis-delivery.json`. Keterangan persetujuan lisan dipertahankan.
- **Status:** selesai; verifikasi terfokus pada label dan toggle, tanpa mengulang
  suite seluruh layar.

### FIG-DIAGNOSIS-01: Diagnosa & Estimasi pada prototype satu file (2026-11-15)

- **Permintaan:** lanjut ke tahap berikutnya setelah Registrasi diterima user.
  Irisan ini membangun Diagnosa & Estimasi sampai salinan awal SO; pengelolaan
  pengerjaan/realisasi SO menjadi irisan berikutnya. File FigCraft utama tetap
  sama dan mendapat backup ZIP sebelum edit.
- **Reference lock:** shell, Poppins, palet/variabel Light/Dark dan komponen
  existing dipakai ulang. Identitas kunjungan mendahului pemeriksaan; biaya
  memisahkan jasa/part, qty/satuan, harga satuan, subtotal dan total. Sumber aturan
  CONTEXT §2.1–§2.5, PRD F-03/F-13, AFD §2.2 dan perilaku prototype WEB-02/03B.
- **Kriteria sebelum eksekusi:** dari REG-DEMO-0147 tampil identitas Maya tanpa
  entry ulang; Teknisi mengisi temuan/rekomendasi, menambah/menghapus contoh item,
  menyimpan draf parsial, memeriksa qty/satuan serta alasan harga lokal. Approval
  memerlukan rincian valid dan persetujuan lisan eksplisit. Estimasi disetujui
  terkunci; salinan awal SO mempertahankan identitas/item dan belum dimulai.
- **Peran:** pergantian journey demo harus eksplisit. Kasir hanya membaca dan
  tidak membuat diagnosa/approval/SO. Contoh log perubahan harga lengkap hanya
  pada journey Owner. Harga beli/HPP tidak ditambahkan.
- **Keadaan tambahan:** draf offline tidak dianggap persetujuan/reservasi stok;
  kegagalan simpan/approval tidak boleh mengklaim sukses. Konflik mempertahankan
  salinan lokal dan membandingkan versi server, tanpa menimpa estimasi disetujui.
  Label Draf/Disetujui mengikuti demo WEB-02, bukan keputusan status pemeriksaan
  produksi yang lengkap. Batas angka demo tidak menjadi aturan bisnis baru.
- **Verifikasi:** seluruh tautan baru lewat presenter, guard/identitas/nominal,
  pembatalan form, timer/tema, render desktop/ponsel, missing-font, file tersimpan
  dan regresi jalur Registrasi/kasir. Input tetap state contoh, belum backend,
  autentikasi, penyimpanan, reservasi atau persetujuan pelanggan nyata.
- **Hasil:** 104 frame Diagnosa & Estimasi (52 desktop/52 ponsel) ditambahkan
  pada file utama; total layar kerja menjadi 210. Entry dari detail Registrasi
  mempertahankan Kasir sampai perpindahan journey Teknisi dipilih secara eksplisit.
  Draf kosong/parsial, pengisian pemeriksaan, katalog dan contoh penghapusan part,
  qty tidak valid, harga lokal beralasan, persetujuan lisan, acuan terkunci serta
  penyalinan SO tersedia. Jalur satu jasa Rp50.000, dua item Rp150.000, dan harga
  lokal Rp145.000 mempertahankan nominal sampai SO. SO awal Belum dimulai;
  kembali ke acuan yang sudah terhubung menyediakan Lihat SO, tanpa aksi buat lagi.
- **Verifikasi nyata:** 552 tautan baru/menu penghubung lulus input presenter,
  enam timer persetujuan serta Light→Dark→Light kedua perangkat lulus. Identitas,
  nominal, guard Kasir/approval/qty/alasan harga/konflik, draf parsial dan kembali
  ke form asal pada pembatalan diperiksa. Sebanyak 64 perpindahan regresi jalur
  Registrasi dan tiga metode pembayaran kasir lulus; ini regresi pilihan jalur,
  bukan pengulangan seluruh 521 tautan historis. Poppins tidak dilaporkan hilang.
  Perhitungan contoh 0,500 × Rp200.001 dibulatkan setengah naik ke Rp100.001.
  Seluruh 5486 teks native memakai Poppins; file memiliki 1337 instance.
  Roda gulir nyata mencapai tombol persetujuan ponsel dan kliknya berhasil
  melalui timer ke Disetujui. CLI membuka kembali empat halaman tanpa missing-font;
  hash file tersimpan cocok, ZIP utuh dan dua gambar referensi tidak berubah.
- **Bukti:** `prototype/figcraft/evidence/diagnosis-map.json`,
  `diagnosis-verification.json`, `diagnosis-playback.json`,
  `diagnosis-delivery.json`, `diagnosis-file-info.json`, render native terkait;
  backup sebelum edit di `prototype/figcraft/archive/before-diagnosis.zip`.
- **Batas:** editor disimulasikan sebagai Teknisi, Kasir membaca dan Owner
  memiliki contoh log harga. Journey editor Owner lengkap belum disimulasikan.
  Input, penyimpanan, approval dan salinan SO masih state contoh; autentikasi,
  otorisasi server, sinkronisasi global antarmodul serta idempotensi produksi
  belum diimplementasikan. Contoh penghapusan berfokus pada part/jasa tunggal;
  tidak mendukung seluruh kombinasi katalog. Progres, penugasan dan realisasi SO
  menjadi irisan berikutnya. Reflow/Tab/screen reader menyeluruh belum diverifikasi.
- **Status:** konstruksi dan playback irisan Diagnosa & Estimasi selesai,
  dengan batas prototype di atas.

### FIG-REGISTRATION-01: Registrasi pada prototype satu file (2026-11-15)

- **Irisan lanjutan:** setelah user menyetujui kasir dan meminta prototype
  dilanjutkan, agent memilih Registrasi sebagai pintu masuk layanan berikutnya.
  Kerjakan di file FigCraft utama yang sama; simpan backup ZIP sebelum edit.
- **Reference lock:** pertahankan shell, Poppins, palet semantik serta komponen
  Light/Dark prototype yang disetujui. Daftar memakai identitas plat terlebih
  dahulu; form dan ringkasan memisahkan kendaraan, pelanggan kunjungan dan keluhan.
  Skill redesign-existing-projects dipakai untuk audit/konsistensi; keputusan
  warna dan font proyek mengalahkan saran palet/font generik pada skill.
- **Kriteria sebelum eksekusi:** menu Registrasi terhubung dari kasir; daftar,
  form kosong/terisi/validasi, tinjauan, menyimpan/tersimpan, koreksi sebelum SO,
  penguncian sesudah SO, konfirmasi meninggalkan isian, kosong/tanpa hasil,
  gagal memuat/offline/gagal simpan tersedia pada desktop dan ponsel.
- **Aturan:** empat field wajib mengikuti CONTEXT §2.2; alamat opsional.
  Kendaraan berplat sama dipakai ulang, kunjungan selalu baru, telepon sama
  tidak menggabungkan pelanggan. Kasir tidak membuat diagnosa atau SO dari
  registrasi dan tidak mengoreksi setelah SO dibuat. Koreksi sebelum SO
  menampilkan riwayat; master dan dokumen final tidak ditulis ulang.
- **Verifikasi:** klik navigasi presenter, timer, tema, guard, identitas antar
  state, render native serta missing-font; regresi kasir yang sudah disetujui.
  Input masih state contoh, bukan ketikan bebas atau penyimpanan produksi.
- **Hasil:** 48 frame Registrasi (24 desktop/24 ponsel) ditambahkan pada halaman
  perangkat yang sama. File utama sekarang memuat 106 frame dan 639 instance.
  Menu Registrasi kasir dan flow khusus kedua perangkat terhubung. Kendaraan
  kembali memakai contoh B 1234 ABC dengan pelanggan Maya, ID pelanggan berbeda
  dari Rina, dan registrasi kunjungan baru. Koreksi keluhan sebelum SO memiliki
  riwayat; contoh setelah SO dibuat menonaktifkan koreksi bagi Kasir.
- **Verifikasi nyata:** seluruh 285 tautan tambahan Registrasi/menu penghubung
  lulus input presenter. Empat timer simpan, Light→Dark→Light kedua perangkat,
  identitas state, guard dan Escape lulus. Pembatalan kembali ke form asal pada
  enam skenario (form baru terisi, kendaraan lama, koreksi; kedua perangkat).
  Regresi seluruh 236 tautan kasir juga lulus; total 521 tautan diperiksa.
  Seluruh 2428 teks native memakai Poppins tanpa missing-font; render native
  terang/gelap ditinjau. Input roda gulir nyata mencapai tombol form ponsel.
  CLI membuka kembali file gabungan; ZIP lulus integritas dan kedua gambar
  referensi mempertahankan hash asalnya.
- **Bukti:** `prototype/figcraft/evidence/registration-map.json`,
  `registration-verification.json`, `registration-playback.json`,
  `registration-delivery.json` dan `registration-file-info.json`; regresi kasir
  pada laporan `completion-verification.json`. Backup sebelum edit ada di
  `prototype/figcraft/archive/before-registration.zip`.
- **Batas:** form dan pencarian memakai skenario terisi yang disiapkan; belum
  menerima ketikan bebas, menyimpan data produksi atau menyinkronkan state
  kunjungan secara global antarmodul. Registrasi pada irisan ini menampilkan
  Kasir; journey Teknisi/Owner dan konstruksi Diagnosa & Estimasi masih berikutnya.
  Form lengkap dan riwayat panjang ponsel digulir; reflow, Tab dan screen reader
  menyeluruh belum diverifikasi. Detail metode pembayaran asli tetap belum diisi.
- **Status:** konstruksi dan playback Registrasi selesai; batas prototype berlaku.

### FIG-CASHIER-FINISH-01: Kelengkapan desain kasir (2026-11-15)

- **Lingkup dipilih user:** tuntaskan kasir pada file utama yang sama; modul lain
  tidak masuk irisan. Simpan backup ZIP sebelum edit, pertahankan flow existing.
- **Kriteria sebelum eksekusi:** tambahkan warna native Light/Dark dari token
  tunggal dan kontrol tema; state kosong, pencarian tanpa hasil, loading, error,
  offline, draf Perlu Owner, invoice Rp0 dan preview nota. Rapikan teks kecil dan
  tambahkan gaya/komponen yang dapat dipakai ulang; referensi gambar tetap asli.
- **Aturan:** Kasir tidak merevisi harga atau draf stale; offline tidak menerima
  pembayaran; Rp0 terbit langsung Lunas tanpa pembayaran. Preview cetak tidak
  menyiratkan dukungan printer nyata. QRIS/rekening asli tidak dibuat-buat.
- **Verifikasi:** missing-font, kontras peran warna, graf pembayaran/guard, state
  baru bisa dibuka, tema pada render dan playback, alur existing tetap bekerja.
  Batas ketikan bebas/keyboard lengkap/semua SO dibedakan dari desain yang diuji.
- **Hasil:** file utama yang sama kini memiliki 58 frame (29 desktop/29 ponsel),
  halaman Komponen, 23 variabel warna Light/Dark, lima text style Poppins, tiga
  set komponen dengan lima varian, serta 298 instance. Tambahan state mencakup
  seluruh skenario pada kriteria, dibuka melalui kontrol Demo. Cetak nota kini
  membuka pratinjau yang sesuai dengan metode; kertas tetap putih di tema gelap.
  Label kecil diperbaiki dan delapan tautan kembali ponsel yang berada di atas
  layar dipindahkan ke kontrol terlihat. Backup ZIP sebelum edit dipertahankan.
- **Verifikasi nyata:** 236 tautan navigasi diuji melalui input presenter dan
  lulus, termasuk alur existing. Pergantian Light→Dark→Light pada kedua perangkat
  dibuktikan lewat perubahan piksel canvas screenshot. Timer loading kedua
  perangkat kembali ke antrean; graf state belum valid/offline/Perlu Owner tidak
  memiliki tautan langsung ke Lunas. Invoice Rp0 langsung Lunas tanpa pembayaran.
  Sebanyak 18 pasangan peran warna memenuhi kontras teks minimal 4,5:1; ini bukan
  audit WCAG menyeluruh. Seluruh 1506 teks native memakai Poppins tanpa missing
  font. CLI membaca kembali file tersimpan: empat halaman, dua embedded image,
  tanpa missing-font. Arsip ZIP lulus pemeriksaan integritas.
- **Bukti:** `prototype/figcraft/evidence/completion-verification.json`,
  `completed-playback.json`, `completion-delivery.json`, `completed-file-info.json`
  dan render native terkait. Panduan aktif di `prototype/figcraft/README.md`.
- **Batas:** alur tetap simulasi input contoh; pencarian/filter bebas, semua SO,
  Tab/screen reader, reflow otomatis, printer fisik dan backend belum diverifikasi
  atau diintegrasikan. Focus tersedia sebagai varian desain. Pada runtime ini,
  mouse-up changeTo menghalangi klik; varian tekan memakai mouse-down dan kembali
  normal saat pointer keluar. QRIS/rekening asli tetap menunggu data user.
- **Status:** irisan pelengkapan desain kasir selesai dengan batas prototype di atas.

### FIG-ONEFILE-01: Satu file kerja FigCraft (2026-11-15)

- **Permintaan:** user mengonfirmasi seluruh layar kerja digabung dalam satu file.
- **Kandidat utama:** `prototype/figcraft/pos-kasir.figcraft`. Pisahkan Desktop,
  Ponsel dan Referensi sebagai halaman dalam dokumen yang sama; reference images
  dari pasangan acuan tidak menjadi pengganti layer editable pada layar utama.
- **Kriteria sebelum eksekusi:** simpan backup arsip, pertahankan 28 frame dan
  116 interaksi, start flow per perangkat pada halaman yang benar, reference assets
  tersimpan di native file, file dapat dibaca kembali. Browser existing dan desain
  historis UI-04 tidak ditimpa atau dimasukkan sebagai alur aktif yang bertentangan.
- **Hasil:** satu native file berisi halaman Desktop (14 frame), Ponsel (14 frame),
  dan Referensi (dua PNG acuan embedded serta judul). ID 28 frame dan 116 link
  dipertahankan; flow ponsel dipindah ke halaman Ponsel. Backup sebelum perubahan
  disimpan di `prototype/figcraft/archive/before-one-file.zip`.
- **Verifikasi:** uji playback 44 perpindahan diulang setelah konsolidasi dan lulus;
  CLI info membuka tiga halaman dan dua images. Pemeriksaan ZIP native memastikan
  dua gambar benar-benar berada di file. Lihat `consolidation-verification.json`.
  Halaman Desktop dan preview desktop dijadikan titik awal kembali. Tidak perlu
  membuka file referensi/first-pair terpisah untuk memakai prototype aktif.
- **Status:** konsolidasi satu file selesai. Batas input contoh dan scope kasir
  yang sudah dilaporkan tetap berlaku; arsip historis tidak dihapus.

### FIG-FLOW-01: Prototype kasir terhubung di folder prototype (2026-11-15)

- **Permintaan:** lanjutkan konstruksi dan kumpulkan file prototype di `/prototype`.
- **Lokasi:** `prototype/figcraft/`, terpisah dari source browser existing. Kandidat
  aktif, sumber konstruksi, bukti dan panduan penggunaan dikumpulkan di sini;
  snapshot/handoff historis di doc tetap sebagai arsip.
- **Kriteria sebelum eksekusi:** satu file native baru dengan alur daftar → detail
  → draf → pembayaran tunai/QRIS/transfer → nota dan kembali; dua ukuran perangkat,
  Poppins dan token existing. Link tidak boleh menuju transaksi yang berbeda.
  Pembayaran/QRIS/rekening tetap simulasi dan data asli tidak dikarang.
- **Verifikasi:** inspect graf/interaksi, kesesuaian identitas/nominal, export dan
  lihat render, simpan/buka kembali file. Bedakan navigasi state statis dari input
  uang atau pembayaran nyata. Artefak/browser existing tidak ditimpa.
- **Hasil:** file utama `prototype/figcraft/pos-kasir.figcraft` dibuat pada sesi
  live terpisah port 7980 dengan root tulis folder yang diminta. Terdapat 28 frame,
  116 link, empat komponen tombol, 1107 teks Poppins, nol image layer; missing font
  kosong. Browser existing dan file FigCraft historis tidak diubah.
- **Uji aktual:** playback native melalui input presenter memverifikasi 44 transisi
  pada tunai/QRIS/transfer di desktop dan ponsel, termasuk scrolling dan kembali
  ke antrean. Percobaan awal pointer canvas tidak menggerakkan preview; uji memakai
  raw input window yang didokumentasikan, bukan menganggap graf sebagai playback.
  Setelah area checkbox diperluas minimal 44 px, suite playback diulang dan lulus.
  Graf memeriksa 14 state terjangkau per perangkat dan tidak ada link Lunas langsung
  dari tunai kurang/QRIS belum diperiksa/transfer belum lengkap. File dibaca kembali
  dengan CLI info; render detail dan nota ponsel diperiksa. Bukti di
  `prototype/figcraft/evidence/` dan panduan di README folder tersebut.
- **Batas:** hanya jalur SO-0261 terhubung; input memakai state contoh, bukan
  ketikan bebas. Print belum terhubung printer; dark lengkap, keyboard/focus,
  role lain dan modul lain belum dibangun. Geometri belum seluruhnya auto-layout
  atau instance komponen; beberapa ikon/shadow belum identik. Tidak ada pembayaran
  nyata atau perubahan storage aplikasi.
- **Status:** irisan prototype kasir terhubung selesai dan siap dicoba. Versi
  aktif terkumpul di `/prototype/figcraft`; pengembangan modul lain tetap berikutnya.

### FIG-TRIAL-01: Pasangan layar editable pertama (2026-11-15)

- **Permintaan:** user meminta mencoba konstruksi desktop/ponsel di FigCraft live.
- **Lingkup:** dokumen kandidat baru dari snapshot HTML grid desktop dan daftar
  ponsel; ekstrak geometri, warna dan teks dari DOM yang sudah dirender. Impor SVG
  sebagai layer editable, bukan menempel screenshot. Artefak historis tetap.
- **Kriteria sebelum eksekusi:** Poppins dan styling acuan termuat; nilai uang
  mengikuti sumber koreksi; hasil native berisi teks editable; font/geometri dan
  screenshot diperiksa, simpan kandidat lalu periksa dapat dibuka kembali.
- **Batas trial:** posisi tetap berdasarkan DOM; komponen/auto-layout/prototyping
  penuh belum dianggap tersedia. Perbedaan ikon/shadow/teks dicatat sebelum klaim
  kemiripan. Dokumen pengguna yang sudah terbuka tidak ditimpa.
- **Hasil:** sumber HTML dimuat dengan Poppins/CSS nyata; tidak ada page error
  atau overflow pada viewport trial. Native kandidat dibuat melalui FigCraft live
  dalam tab baru. Impor SVG menghasilkan layer teks/bentuk editable; bukan image.
  Perbaikan kedua mengoreksi border parsial yang semula menjadi kotak dan radius
  pill yang semula terlalu besar.
- **Artefak akhir trial:**
  `../DBD/figcraft-handoff-v1/trial/pos-first-pair-refined.figcraft` (335 node,
  dua frame, 171 teks Poppins, nol image, nol missing font). CLI info dapat membuka
  kembali file tersimpan. Render desktop 1440×1000 dan mobile 390×1179 diperiksa.
- **Perbandingan:** `trial/verification.json` mencatat mean absolute channel
  difference 2,620 desktop dan 4,357 ponsel pada skala 0–255. Ini metrik beda piksel,
  bukan persentase kemiripan; rasterisasi, shadow dan ikon masih berbeda. Sebagian
  ikon desktop direkonstruksi sebagai vektor sederhana; ikon SVG mobile belum
  seluruhnya sesuai. Tidak mengklaim identik atau prototype interaktif selesai.
- **Batas:** geometri tetap, belum reusable components/auto-layout dan interaksi.
  Frame mobile memuat seluruh tinggi konten 1179 px, belum viewport 844 dengan
  scroll presenter. Token native styles/variables belum dibuat. Artefak lama dan
  aplikasi existing tidak diubah. Kamera live diatur zoom fit pada kandidat baru.
- **Status:** trial pasangan editable selesai dan siap ditinjau. Penyempurnaan
  ikon/shadow serta struktur komponen/prototype adalah tahap berikutnya.

### FIG-HANDOFF-01: Paket acuan untuk FigCraft live (2026-11-15)

- **Permintaan:** user menyetujui persiapan acuan final dan pemeriksaan koneksi
  live sebelum membangun satu pasangan layar percobaan.
- **Kriteria sebelum eksekusi:** simpan salinan sumber yang relevan beserta hash,
  petakan layar dan state yang disetujui, pertahankan provenance Stitch/lokal,
  tandai screenshot lama yang belum sesuai sumber koreksi. Jangan menjanjikan
  impor HTML identik atau menimpa file FigCraft historis.
- **Batas:** belum ada tool MCP FigCraft pada sesi; pencarian executable PATH dan
  proses aktif sebelumnya belum menemukan koneksi. Instalasi/config host di luar
  workspace bukan bagian persiapan yang dilakukan otomatis.
- **Hasil:** `../DBD/figcraft-handoff-v1/manifest.json` membekukan empat HTML
  dan dua PNG dengan hash yang diverifikasi. Tautan otoritas tersedia. README
  menjelaskan sumber Stitch/lokal, render yang masih perlu dibuat, konstruksi
  editable dan perbandingan; artefak historis tidak diubah.
- **Runtime aktual:** instalasi ArtCraft ditemukan di Program Files; CLI mendukung
  attached dan query font engine menemukan Poppins. Peluncuran GUI pertama tidak
  bertahan; percobaan kedua dengan sesi proses tetap aktif berhasil. Probe
  inspect_document pada port loopback 7979 membaca Untitled, dirty=false,
  tanpa layer/perintah edit. Host MCP permanen tidak didaftarkan atau diubah.
- **Batas:** versi attached melaporkan 0.18.1, berbeda metadata executable 0.15.0.
  Bukti runtime disimpan; koneksi diuji melalui subprocess CLI, bukan tool FigCraft
  host yang terdaftar. Sesi GUI masih dijaga proses shell; periksa ulang setelah
  sesi ditutup. Belum ada frame native atau bukti overlay sama piksel.
- **Status:** persiapan paket dan uji koneksi live selesai. Konstruksi pasangan
  desktop/ponsel percobaan menjadi tahap berikut; belum diklaim selesai.

### REVIEW-ST-01: Pemeriksaan kesiapan konsep sebelum penyatuan (2026-11-15)

- **Permintaan:** user meminta memastikan kebutuhan/kelengkapan dahulu.
- **Lingkup:** pemeriksaan konsep dan bukti existing; tidak mengubah aplikasi
  atau menambah kebijakan pembayaran. Dokumen sumber CONTEXT §2.2/§2.7/§5.
- **Kriteria sebelum pemeriksaan:** bedakan persetujuan visual, simulasi yang
  benar-benar teruji, integrasi yang belum ada dan data milik user yang belum
  tersedia. Periksa pembayaran tiap metode, referensi panjang, kembali ke invoice,
  format nota, layout sempit serta keberadaan gateway pada prototype existing.
- **Hasil aktual:** uji browser ketiga metode lulus: tunai kurang ditolak,
  QRIS/transfer wajib pemeriksaan, nota/sisa Rp0 sesuai, print menyembunyikan
  kontrol, kembali mempertahankan invoice final. Referensi transfer 100 karakter
  pada nota dan lebar 320/390/768/1440 tidak overflow; page error kosong.
- **Celah kesiapan:** kembali ke antrean masih pesan penjelasan; daftar/detail/
  invoice belum satu alur terhubung. Prototype existing masih memiliki gateway;
  pergantian metode baru sebatas konsep. Tema gelap lengkap, offline/error/conflict,
  role enforcement dan integrasi penyimpanan belum diuji pada rancangan baru.
- **Data/keputusan yang dibutuhkan nanti:** QRIS asli, bank/rekening/atas nama,
  dan perangkat/ukuran kertas bila cetak khusus diperlukan. Untuk konsep bisa tetap
  memakai penanda kosong dan cetak browser/PDF. Tidak perlu mengulang keputusan
  font/palet/metode yang sudah disetujui.
- **Bukti:** `../DBD/stitch/readiness-review.json`. Uji lanjutan memakai fallback
  font dan tidak menyentuh storage aplikasi. Poppins termuat sudah dibuktikan
  pada uji sebelumnya; font plus semua state baru belum diperiksa bersamaan.
- **Status:** pemeriksaan selesai; konsep cukup untuk dilanjutkan ke penyatuan,
  belum dinyatakan aplikasi siap pakai. Tidak mengubah prototype existing.

### UI-ST-02: Konsep invoice, pembayaran dan nota (2026-11-15)

- **Revisi lingkup sebelum eksekusi 2026-11-15:** user menunda gateway dan
  mengonfirmasi tunai tetap tersedia. Ganti gateway pada konsep lokal dengan QRIS
  statis serta detail bank/rekening/nama pemilik untuk transfer. Data asli belum
  diberikan; jangan membuat QR/nomor rekaan. QRIS/transfer memerlukan pemeriksaan
  dana masuk Kasir/Owner. Uji pilihan metode, penolakan konfirmasi tanpa pemeriksaan,
  label nota QRIS/transfer dan tidak adanya gateway pada pratinjau terbaru.
- **Hasil revisi:** konsep lokal kini hanya tunai/QRIS/transfer. QRIS tidak
  direkayasa; area QRIS menjelaskan aset asli belum diberikan. Transfer menampilkan
  bank/nomor rekening/atas nama dengan status belum diberikan. Konfirmasi QRIS
  memerlukan pengakuan pemeriksaan dana masuk; transfer tetap memerlukan referensi
  dan pemeriksaan mutasi. Nota QRIS/transfer tidak menampilkan kembalian tunai.
  Pratinjau baru: scratch `pos-manual-payments-20261115.html`.
- **Persetujuan user:** konsep pembayaran tanpa gateway diterima 2026-11-15.
  Tujuan QRIS/rekening asli masih belum diberikan; integrasi aplikasi belum
  dikerjakan. Keputusan metode aktif bersumber pada CONTEXT §2.2.
- **Verifikasi revisi:** sembilan kombinasi metode/lebar 320/390/1440 tanpa
  overflow; konfirmasi QRIS tanpa pemeriksaan ditolak, transfer tanpa referensi
  ditolak, label nota sesuai dan gateway tidak muncul. Page error kosong;
  screenshot QRIS ditinjau. Laporan `manual-payments-verification.json`; uji ini
  memakai fallback font, pemuatan Poppins unchanged sudah diverifikasi sebelumnya.
  Dokumen aktif CONTEXT/PRD/AFD/TRD diselaraskan. BSD hanya diberi catatan kontrak
  demo lama; storage/aplikasi existing tidak dimigrasi atau dihapus.
- **Lanjutan metode sebelum eksekusi:** transfer manual meminta referensi dan
  pengakuan pemeriksaan mutasi; nota mengikuti metode tanpa label kembalian tunai.
  Gateway generik menampilkan simulasi Menunggu verifikasi server, bukan tombol
  browser yang menganggap pembayaran berhasil. Tidak menetapkan provider/QR nyata.
  Uji perpindahan metode, penolakan referensi kosong dan hasil nota transfer.
- **Lingkup disetujui:** melengkapi alur kasir setelah detail SO; konsep visual
  invoice draf, pembayaran tunai dan nota lunas, masing-masing desktop/ponsel.
  Palet dan Poppins mengikuti DESIGN_POS_Extend. Aplikasi/data existing tidak diubah.
- **Kriteria sebelum eksekusi:**
  1. Kasir melihat item/qty/harga read-only pada draf; terbitkan invoice merupakan
     aksi eksplisit, pembayaran hanya pada invoice final. Tidak ada DP/cicilan.
  2. Contoh konsisten SO-0261/INV-0144, Rp150.000 + Rp85.000 = Rp235.000;
     tunai Rp250.000, kembalian Rp15.000, pembayaran bersih Rp235.000.
  3. Nota final Lunas menampilkan rincian versi berlaku tanpa riwayat internal;
     contoh ditandai simulasi, bukan bukti pembayaran nyata. Ponsel memiliki jalan
     kembali, tombol/nominal terbaca dan konten tidak terpotong pada screenshot.
- **Batas:** provider gateway dan printer belum dipilih. Konsep tidak menetapkan
  kontrak gateway/refund atau menjanjikan cetak langsung perangkat tertentu.
- **Hasil:** panggilan generate Stitch gagal karena transport HTTP. Pemeriksaan
  list_screens berhasil dan belum menampilkan hasil baru; generation tidak diulang
  agar tidak berisiko duplikasi. Konsep dilanjutkan sebagai HTML lokal mengikuti
  acuan yang sudah disetujui, bukan diklaim sebagai hasil Stitch.
- **Artefak:** `../DBD/stitch/cashier-flow-local.html` dan
  `cashier-flow-verification.json`. Salinan visual interaktif tersedia di scratch
  chat sebagai `pos-cashier-flow-20261115.html`. Tiga tahap memakai satu struktur
  responsif dengan pilihan ukuran ponsel; tidak menyimpan data atau memanggil API.
- **Verifikasi aktual:** Poppins termuat; invoice draf → final → pembayaran →
  nota berfungsi sebagai simulasi. Tunai kurang ditolak; Rp250.000 menghasilkan
  kembalian Rp15.000; kembali dari pembayaran mempertahankan invoice final.
  Tiga tahap pada 320/390/768/1440 px tanpa overflow; page error kosong. Emulasi
  print menyisakan nota dan menyembunyikan kontrol. Screenshot pembayaran desktop
  diperiksa. Pemeriksaan browser memakai runtime Playwright proyek dan akses font
  yang disetujui, bukan uji pembayaran/backend atau perangkat printer.
- **Batas aktual:** contoh interaktif khusus tunai; label transfer/gateway belum
  memiliki pratinjau form tersendiri. Kembali ke antrean menjelaskan destinasi,
  tidak menghubungkan ke data aplikasi. Pemilihan tahap di toolbar adalah kontrol
  tinjauan konsep, bukan cara melewati tahap pada aplikasi. Tema gelap alur lengkap,
  state offline/error jaringan dan integrasi aplikasi belum dikerjakan.
- **Status:** konsep alur tunai desktop/ponsel siap ditinjau; implementasi sistem
  existing belum diubah. Hasil di Stitch belum dapat dikonfirmasi tersedia.
- **Lanjutan metode:** `cashier-flow-local.html` kini memiliki pemilih metode.
  Transfer meminta referensi dan pemeriksaan dana masuk; konfirmasi simulasi
  menghasilkan nota Transfer manual tanpa kembalian tunai. Gateway generik hanya
  menunjukkan Menunggu verifikasi server, tanpa QR, tautan aktif atau tombol yang
  menganggap uang sudah masuk. Provider tidak diputuskan melalui pratinjau ini.
- **Uji lanjutan aktual:** referensi kosong/pemeriksaan belum dicentang ditolak;
  nota transfer berisi referensi; pindah ke tunai mengembalikan nota/kembalian
  tunai tanpa referensi transfer. Tiga metode pada 320/390/1440 px tanpa overflow,
  page error kosong. Screenshot gateway diperiksa. Lihat
  `cashier-methods-verification.json`. Uji perilaku lanjutan memblokir font jaringan
  dan memakai fallback; pemuatan Poppins sudah diuji sebelumnya pada alur dasar.
- **Pratinjau terkini:** scratch `pos-cashier-methods-20261115.html`. State gateway
  berhasil/gagal/expired menunggu kontrak integrasi dan belum dimodelkan; offline,
  tema gelap lengkap dan integrasi aplikasi tetap belum dikerjakan. Tidak ada
  pembayaran nyata, API atau storage aplikasi yang diubah.

### UI-ST-01: Konsep redesign POS Kasir di Stitch (2026-11-15)

- **Lingkup:** satu konsep POS, grid kartu dahulu kemudian detail transaksi,
  dengan adaptasi ponsel. Prototype aplikasi dan data existing tidak diubah.
- **Dasar:** persetujuan Q1–Q2 pada CONTEXT §2.8/§5, screenshot user dan reference
  lock DBD. Biru tetap utama; palet pendukung disetujui dan Poppins dipilih dari
  permintaan Gotham/Poppins pada 2026-11-15; token di DESIGN_POS_Extend.
- **Kriteria sebelum eksekusi:**
  1. Kartu memuat plat, pelanggan, nomor dokumen, waktu, ringkasan item, total
     dan status; tidak memasukkan SO yang belum diserahkan tanpa invoice.
  2. Warna pendukung memiliki peran konsisten, teks status, dan pasangan teks/
     latar yang dihitung. Temuan psikologi warna dipisahkan dari saran desain.
  3. Konsep desktop/ponsel dapat ditinjau; output generator diperiksa sebagai
     desain, bukan bukti implementasi atau pembayaran berhasil. Hasil dan
     keterbatasan dicatat sebelum penutupan irisan.
- **Kriteria revisi font sebelum eksekusi:** Poppins terpakai pada isi, kartu dan
  kontrol; font termuat nyata; contoh terang/gelap tetap tanpa overflow pada
  320/390/768/1440 px; label panjang dan nominal terbaca. Revisi konsep Stitch
  menghapus overflow serta metadata rekaan yang ditemukan pada review awal.
- **Lanjutan setelah persetujuan Poppins:** buat konsep daftar ponsel 390 px
  dan detail SO siap ditagih pada desktop. Detail harus read-only untuk Kasir,
  memiliki Kembali ke antrean dan Buat invoice draf eksplisit, tanpa pembayaran
  sebelum invoice terbit. Nilai contoh SO-0261 tetap Rp235.000 (150.000 + 85.000).
  Periksa screenshot dan source hasil generator sebelum menyerahkan untuk tinjauan.
- **Hasil riset:** sumber primer riset warna dan panduan Google/WCAG ditelusuri.
  Dua belas pasangan teks/latar usulan lolos rasio 4,5:1; hasil perhitungan di
  `../DBD/stitch/color-contrast.json`. Ini pemeriksaan palet, bukan audit aplikasi.
- **Artefak:** proyek Stitch privat `10688800567528588050`, screen desktop
  `b0e4ee3399594b08808cbbcf4a6910a7`; HTML generator disimpan di
  `../DBD/stitch/desktop-generated.html` untuk ditinjau, bukan source aplikasi.
- **Review generator:** grid enam kartu, identitas dan kategori jasa/part terlihat.
  Screenshot terpotong di kanan akibat min-width workspace; generator juga
  menambahkan tanggal/cabang/shift/notifikasi rekaan serta guideline design system
  yang bertentangan dengan brief. Output belum layak menjadi target implementasi.
  Pernyataan generator bahwa seluruh spesifikasi terpenuhi tidak diadopsi.
- **Contoh palet:** HTML mandiri di scratch chat, berisi dua kartu serta toggle
  terang/gelap. Python Playwright runtime proyek memverifikasi 320/390/768/1440 px
  di kedua tema tanpa overflow, toggle bekerja dan page error kosong; screenshot
  terang diperiksa. Alias `python` WindowsApps gagal, lalu executable Python312
  yang tercantum di README dipakai. Tidak ada perubahan aplikasi atau storage.
- **Hasil revisi font:** draf Stitch Poppins dibuat sebagai screen
  `e8eb6ea0e544495a9ea827071ad3c450`; screenshot desktop diperiksa, ketiga kolom
  kini terlihat utuh dan metadata cabang/tanggal/shift/notifikasi rekaan dihapus.
  HTML generator masih mengubah beberapa nilai dummy tanpa diminta; salinan
  `../DBD/stitch/desktop-poppins.html` mengembalikan nilai tersebut. Salinan ini
  belum diunggah ulang atau diuji sebagai aplikasi. Klaim generator bahwa seluruh
  breakpoint lolos tidak diadopsi; pemeriksaan responsif berikut hanya contoh palet.
- **Verifikasi font nyata:** contoh palet baru `pos-poppins-20261115.html` di
  scratch chat memakai Poppins pada body, plat, nominal dan tombol. Browser
  melaporkan font latin 400/600/700 termuat, toggle tema bekerja, 320/390/768/1440 px
  pada dua tema tanpa overflow dan tanpa page error/request gagal. Screenshot
  terang diperiksa. Akses font awal ditolak sandbox (`ERR_NETWORK_ACCESS_DENIED`),
  kemudian pemeriksaan diulang dengan akses jaringan yang disetujui.
- **Status:** permintaan palet dan pergantian font konsep selesai; konsep POS
  utuh masih untuk tinjauan dan penyempurnaan. Varian ponsel Stitch belum dibuat;
  prototype aplikasi belum dimigrasi. Font pratinjau saat ini dimuat dari Google
  Fonts; kesiapan aset font offline pada implementasi aplikasi belum diverifikasi.
- **Lanjutan konsep setelah persetujuan:** daftar ponsel dibuat di Stitch dan
  direvisi menjadi screen `3811ee8a49bd46c98768026ad66fb315`. Review awal menemukan
  nama ligature ikon tampil sebagai teks dan mendorong navigasi; revisi menghapus
  ketergantungan font ikon, footer sinkronisasi rekaan dan pembatasan zoom. Screenshot
  revisi diperiksa: tiga kartu, nominal dan label terlihat, tanpa clipping yang
  terlihat pada render tersebut. Ini bukan hasil uji seluruh breakpoint.
- **Detail desktop:** screen `47ca94e2a62746fa812f6864a057fc31` diperiksa: SO-0261,
  dua item, total Rp235.000, status pekerjaan/tagihan terpisah, kembali ke antrean,
  dan Buat invoice draf eksplisit; belum menyediakan pembayaran sebelum invoice.
  Beberapa deskripsi item tambahan adalah konten dummy generator, bukan fakta usaha.
- **Artefak lanjutan:** `../DBD/stitch/mobile-poppins.html`,
  `../DBD/stitch/detail-so-poppins.html` dan `concept-review.json`; gambar tinjauan
  mandiri di scratch chat. Source menyatakan Poppins, total contoh cocok, dan zoom
  ponsel tidak dinonaktifkan. Klaim fungsional generator tidak dianggap bukti tes.
- **Status terkini:** konsep daftar desktop, daftar ponsel dan detail desktop
  tersedia untuk tinjauan visual. Detail ponsel, state lain, tema gelap lengkap dan
  integrasi ke prototype belum dibuat. Irisan belum dianggap implementasi selesai.

### WEB-10: Jarak indikator dropdown

- **Permintaan:** panah seluruh dropdown tidak menempel pada tepi kanan.
- **Perubahan:** satu aturan select native pada stylesheet prototype; indikator
  berjarak 12 px, ruang teks dicadangkan agar tidak bertumpuk dengan panah.
  Tema gelap dan mode forced-colors tetap terbaca; tidak membuat dropdown custom.
- **Kriteria sebelum implementasi:** semua select single-choice memakai inset
  konsisten; role/filter tidak menimpa padding; tampilan 320/390/1440 px, dua tema
  dan keyboard tetap berfungsi tanpa overflow atau perubahan data.
- **Hasil:** sepuluh dropdown terverifikasi memakai inset dan ruang teks konsisten
  di dua tema pada 320/390/1440 px, tanpa overflow. Screenshot filter ponsel
  diperiksa langsung. Fallback forced-colors native lulus setelah koreksi spesifisitas
  aturan dark. Runner UI dan fokus lulus; ledger tidak berubah saat navigasi.
- **Batas:** Chromium/headless; tampilan popup pilihan native mengikuti OS.
- **Status:** selesai; screenshot probe sementara dibersihkan.

### WEB-09: Penyempurnaan desain visual prototype

- **Permintaan:** perbaiki desain UI setelah perbaikan perilaku WEB-08.
- **Arah:** penyempurnaan native/shadcn existing, bukan redesign identitas.
  Alternatif mengganti palet/library ditolak karena tidak diperlukan dan melawan
  reference lock. Tetap sidebar 240 px, token warna, font, radius dan target sentuh.
- **Bukti awal:** screenshot aktual desktop 1440 dan ponsel 390 px memperlihatkan
  baris daftar berjarak longgar, metadata kecil, header kolom/tombol tidak sejajar,
  serta hierarki navigasi dan formulir yang belum konsisten.
- **Kriteria sebelum implementasi:**
  1. Shell, tabel, form dan ringkasan transaksi memakai hierarki/ritme konsisten;
     kolom header/baris sejajar, teks panjang tidak terpotong atau overflow.
  2. Desktop, tablet dan ponsel 320/390 px tetap dapat dipakai di dua tema;
     target 44 px, label/fokus/error dan kontrol native tetap.
  3. Tidak ada perubahan skema, ledger, izin, alur bisnis atau reset storage;
     suite UI/fokus/UX/POS existing lulus dan screenshot aktual diperiksa.
- **Berkas:** `prototype/styles.css`; dokumentasi visual dan laporan existing.
  Tidak menambah library, aset dekoratif, dashboard atau data statistik buatan.
- **Hasil aktual:** lima runner UI/fokus/UX/POS/Fase 2 lulus; tidak ada error browser
  pada cakupan suite. Screenshot daftar desktop/ponsel, form diagnosa dan invoice
  diperiksa langsung. Probe isi panjang valid lulus pada 320/390/620/768/1050/1440 px
  di dua tema, tanpa overflow; kolom sejajar dan tombol daftar minimal 44 px.
- **Bukti:** laporan `verification-ui.json`, `verification-ux.json`,
  `verification-pos.json`, `verification-phase2.json` dan screenshot existing
  di `prototype/evidence/` diperbarui, bukan diduplikasi. Runner fokus memberi
  hasil PASS di stdout tanpa membuat laporan JSON.
- **Catatan verifikasi:** probe awal memasukkan nama melebihi batas validasi,
  kemudian memakai data valid. Bukan bug tampilan; validasi aplikasi tidak dilonggarkan.
  Detektor tetap memberi warning Inter (pilihan tetap) dan padding total-row
  (tidak sesuai padding aktual pada screenshot). Tidak menambah pengecualian global.
- **Batas:** Chromium headless; bukan pengujian perangkat fisik atau screen reader.
  Source perilaku/storage tidak diubah. Server user tetap berjalan pada port 8765.
- **Status:** selesai; screenshot temporer di luar proyek dibersihkan.

### WEB-08: Perbaikan delapan temuan audit UI/UX

- **Persetujuan:** user meminta menjalankan perbaikan audit. Satu irisan ini
  mempertahankan desain, kontrak storage, riwayat, dan batas peran existing.
- **Kriteria penerimaan sebelum implementasi:**
  1. U1: penyelesaian SO ditolak sebelum realisasi tersimpan; Teknisi tetap
     tidak dapat mengedit SO terminal. Riwayat lama tetap dapat dibaca.
  2. U2: tagihan, uang diterima, dan kembalian tersedia dekat aksi; konfirmasi
     menyebut identitas invoice dan nominal. Transfer tetap harus tepat.
  3. U3: error pembayaran berada dalam formulir dan terkait field invalid;
     koreksi input membersihkan status invalid tanpa mengubah ledger.
  4. U4: daftar diagnosa membedakan kunjungan melalui referensi dan waktu;
     nama aksesibel tombol menyebut kunjungannya.
  5. U5: buang draf memerlukan konfirmasi, hanya menghapus draf registrasi,
     dan mempertahankan isian bila dibatalkan, gagal tulis, atau konflik.
  6. U6: syarat persetujuan terlihat sebelum submit; draf parsial tetap sah.
  7. U7: tombol invoice memiliki nama aksesibel berisi invoice dan pelat.
  8. U8: akses storage terblokir dibedakan dari data rusak; bantuan dan unduh
     salinan mentah lokal tidak mereset, menimpa, atau mengirim data.
- **Pembagian berkas:** pembayaran di `invoices.js`; guard SO dan migrasi
  skenario completion di `service-orders.js`/tes terkait. Integrasi markup,
  styling, draf/pemulihan, diagnosa dan regresi baru ditangani integrator.
- **Verifikasi:** regresi browser terisolasi untuk delapan kriteria dan suite
  existing terkait; periksa desktop/320/390 px, dua tema, error browser,
  konfirmasi batal, kegagalan tulis dan konflik. Jalankan sesudah integrasi,
  bukan selama perubahan parsial. Tidak menguji transaksi nyata atau backend.
- **Hasil aktual:** delapan temuan diterapkan. Sebelas runner browser lulus:
  Fase 1/2/3A/3B/3C/4, POS, preview, UI, fokus, dan UX. Fase 3A kini memiliki
  13 kelompok termasuk penolakan tanpa realisasi/dirty serta replay legacy;
  UX memiliki lima kelompok lintas U2–U8. Tidak ada error browser pada cakupan lulus.
- **Bukti:** `prototype/evidence/verification-ux.json` dan laporan suite existing.
  Empat JS berubah lolos `node --check`; UI diperiksa di 1440/390/320 px dan
  dua tema. Screenshot pembayaran 390 px dilihat langsung, lalu file temporer dihapus.
- **Koreksi selama verifikasi:** assertion hash legacy yang terpaku pada versi
  lama dihapus, bukan dipasang ulang; pemeriksaan hash sebelum/sesudah tetap.
  Zona waktu tes kunjungan ditetapkan UTC. Kontrak error pembayaran dipindahkan
  ke error lokal. Review independen menemukan pesan completion perlu juga terkait
  field realisasi; diperbaiki sebelum regresi 3A terakhir yang lulus.
- **Detektor:** warning Inter merupakan pilihan desain tetap; warning padding
  total-row tidak merepresentasikan padding aktual existing. Tidak mengubah token.
- **Batas:** Chromium/headless dan data dummy; bukan sertifikasi WCAG, perangkat
  fisik, printer atau verifikasi backend/pembayaran nyata. Tidak ada reset data.
- **Status:** selesai.

### AUDIT-UI-01: Audit UI/UX prototype aktif (2026-11-12)

- **Lingkup:** audit read-only `prototype/index.html` dan panduan preview,
  alur registrasi/diagnosa/SO/POS/invoice, desktop/ponsel serta dua tema.
  Legacy ROOT dan FigCraft tidak dinilai sebagai implementasi aktif.
- **Metode:** Impeccable sebagai lead, penilaian UX dan teknis dipisahkan;
  webapp-testing/Playwright existing untuk browser terisolasi. Reference lock
  shadcn/native existing dipertahankan; bukan redesign atau migrasi stack.
- **Kriteria sebelum pemeriksaan:** temuan memuat lokasi, dampak, prioritas,
  bukti source/browser serta skill perbaikan; bedakan celah prototype yang
  diketahui dari regresi. Data dummy hanya di browser audit; tidak menulis
  storage pengguna, source aplikasi, dataset, atau screenshot pengujian existing.
- **Bukti:** gunakan direktori temporer OS selama investigasi; satu laporan
  audit akhir menggantikan dump bertumpuk. Tidak mengklaim audit WCAG penuh,
  perangkat fisik, backend, printer, atau pembayaran nyata telah diverifikasi.
- **Hasil aktual:** delapan temuan (satu P1, tujuh P2). P1: Teknisi dapat menutup
  SO sebelum realisasi tersimpan, lalu tidak dapat menyimpan atau menyerahkan
  tanpa Owner. Tujuh P2 mencakup konteks/konfirmasi pembayaran, error di luar
  viewport, pembeda kunjungan, draf, instruksi persetujuan, nama tombol dan pemulihan.
- **Bukti aktual:** penilaian UX dan teknis independen; 72 snapshot DOM dasar dan
  24 pengukuran terarah pada Chromium 1440/390/320 px, terang/gelap. Dua warning
  detektor terverifikasi sebagai pinned exception/false positive, bukan defect.
  Tidak ada error browser teramati pada cakupan yang diperiksa; bukan sertifikasi
  WCAG atau profiling performa. Tidak menjalankan suite existing atau mengubah UI.
- **Laporan tunggal:** [audit-uiux.md](../../prototype/evidence/audit-uiux.md).
  Impeccable memimpin perbaikan terfokus; better-writing dan fixing-accessibility
  sebagai support, webapp-testing untuk verifikasi. Audit tidak mengaktifkan fix.

### CLEAN-01: Kebersihan berkas proyek POS (2026-11-12)

- **Lingkup disetujui:** pindahkan `prototype/tests/__pycache__/` (enam `.pyc`),
  `debug.log`, `d.registrationId`, dan `{const` ke Recycle Bin. Total sembilan file,
  215.037 byte. Source Python, aplikasi, dataset, desain dan bukti pengujian dipertahankan.
- **Kriteria sebelum eksekusi:** hanya target tersebut yang hilang; hash seluruh
  berkas existing selain IPD tetap sama; ketiga entry HTML dan aset lokalnya
  tetap dapat dilayani melalui HTTP loopback. Tidak membuat bytecode baru untuk verifikasi.
- **Pencegahan:** `.gitignore` lokal mengecualikan cache Python dan log GPU root,
  bukan bukti pengujian, dataset atau sumber desain.
- **Hasil aktual:** sembilan file dipindahkan ke Recycle Bin; 193 file tersisa
  termasuk `.gitignore` baru. Hash 191 berkas existing selain IPD tidak berubah.
  Ketiga entry HTML dan 11 aset lokal mengembalikan HTTP 200; server loopback
  sementara sudah berhenti. Tidak menjalankan ulang UI browser, transaksi,
  printer atau pembayaran; tidak mengubah data browser maupun sumber desain.
- **Rollback:** pulihkan dari Recycle Bin sebelum dikosongkan; batalkan penambahan
  `.gitignore` dan bagian IPD ini bila perlu. Tidak mengubah storage browser.

### WEB-07: Hilangkan ring fokus saat klik (2026-11-11)

- **Lingkup:** seluruh entry HTML (prototype aktif, panduan preview, legacy).
  Pointer/touch tidak menampilkan outline fokus biru; Tab tetap memiliki penanda
  fokus existing. Border validasi error dan status pilihan tetap dipertahankan.
- **Uji sebelum kode:** klik select/input/search/button tanpa outline biru,
  pengetikan tidak mengaktifkan ring, Tab mengembalikan ring; cek tiga entry
  dan tema gelap. Navigasi dan nilai kontrol tidak berubah.
- **Hasil aktual:** `prototype/tests/focus_browser.py` exit 0. Klik select/filter,
  pencarian, tombol dan input serta pengetikan tidak menampilkan ring; Tab
  menampilkan penanda kembali. Prototype light/dark, preview guide dan legacy
  diperiksa pada browser terisolasi. Tidak mengubah aturan bisnis atau data.

### WEB-06: Konsistensi UI/UX dengan acuan shadcn/ui (2026-11-11)

- **Permintaan:** user meminta penerapan langsung pada prototype existing,
  palet netral/satu aksen, navigasi, hierarki, kontrol, responsivitas dan state.
- **Inspeksi:** prototype aktif HTML/CSS/JS, tanpa React/package.json/components.json;
  modul registrasi, diagnosa, SO/realisasi, handoff, POS dan invoice memakai DOM
  native serta stylesheet bersama. Dashboard aktif belum tersedia; index.html ROOT
  adalah prototype legacy dan tidak termasuk perubahan ini.
- **Reference lock:** dokumentasi resmi shadcn/ui Button/Field/Sidebar sebagai
  acuan hierarki/varian dan pengelompokan. Pertahankan identitas plat dan alur
  bengkel existing, kontrol native dan dialog konfirmasi browser yang seragam.
  Satu aksen biru, permukaan netral, border ringan, tanpa shadow pada konten.
  Token hanya di DESIGN_POS_Extend. User mengizinkan perubahan arah visual pada
  permintaan ini; tidak mengubah peran, ledger, validasi, atau aturan workflow.
- **Metode:** Refero Design, direct build menggunakan arah terkunci existing
  dan sumber resmi live. Skill redesign/Impeccable tidak tersedia; tidak memasang
  library atau memigrasi stack untuk penataan prototype.
- **Kriteria sebelum kode:**
  - Navigasi/judul/aksi utama terbaca, sidebar mobile dapat ditutup dengan tombol,
    Escape dan keyboard; label dan pesan validasi tetap terhubung.
  - Semua daftar/form/POS/preview mengikuti token netral terang/gelap, daftar
    menyesuaikan layar sempit, keadaan loading/kosong/error tetap terlihat.
  - Jalankan delapan suite browser existing dan inspeksi screenshot desktop/ponsel,
    termasuk alur registrasi sampai invoice/bayar/cetak serta jalur gagal.
- **Batas:** tidak menambah dashboard, backend, integrasi pembayaran, atau data bisnis.
- **Hasil aktual:** selesai. Seluruh sembilan suite browser exit 0: fase
  1/2/3A/3B/3C/4, POS, preview dan UI. Tujuh suite alur mencakup 103 kelompok
  pemeriksaan existing; suite tambahan memverifikasi isolasi latihan, tim SO,
  label, fokus validasi, menu keyboard, kontras CSS aktual terang/gelap dan ledger
  yang tidak berubah akibat navigasi. Tidak ada console/page error pada uji UI.
- **Visual aktual:** screenshot registrasi desktop, form error ponsel, invoice
  gelap dan halaman utama lain diperiksa. Perbaikan akhir menyembunyikan judul
  kolom saat loading/kosong dan merapikan jarak/panel. Lebar 1440/390/320 diuji
  pada registrasi, form, diagnosa, SO, POS dan invoice; suite existing juga
  memeriksa teks 200%, reduced motion, print dan kegagalan penyimpanan/konflik.
- **Bukti:** `prototype/evidence/verification-ui.json`, `verification-preview.json`,
  JSON hasil suite existing dan screenshot `ui-*.png`. Preview HTTP lokal
  `/prototype/preview.html` mengembalikan 200 pada port 8765.
- **Batas:** uji browser Chromium terisolasi, bukan perangkat fisik/screen reader.
  Dialog tetap native mengikuti OS/browser. Dashboard aktif tidak tersedia;
  root legacy tidak disentuh. Backend, printer fisik dan pembayaran nyata belum
  diverifikasi. Tidak ada perubahan aturan bisnis, schema atau deployment.


### DB-01: Draf relasi dan tabel pelanggan–layanan (2026-11-11)

- **Lingkup disetujui:** rancangan dokumentasi pelanggan, kendaraan, registrasi,
  Diagnosa & Estimasi, SO, penugasan Teknisi, dan revisi. Sumber keputusan:
  CONTEXT §2.1–§2.7, terutama tambahan 2026-11-11. Skema hanya di BSD §1–2;
  invariant di BSD §3.6, validasi §5, dan dependensi migrasi §6.
- **Status (Observed):** draf DB-01 selesai disusun dan direview 2026-11-11;
  siap diperiksa user, belum persetujuan skema fisik atau implementasi.
- **Pendekatan/Ponytail:** UUID tetap untuk dokumen dan baris item, snapshot revisi
  relasional append-only, penunjuk revisi terkini. Dibandingkan tabel current +
  history terpisah, pendekatan ini menghindari dua salinan rincian aktif yang harus
  selalu diselaraskan. Tanpa framework event sourcing atau dependency baru.
- **Kondisi:** aplikasi masih prototype browser; backend belum dibuat. Satu cabang;
  jumlah pengguna bersamaan, volume data, dan target respons belum diketahui.
  Risiko utama rancangan: kehilangan riwayat, akses peran, konflik offline,
  snapshot harga, serta hubungan item SO dengan stok/invoice pada irisan berikutnya.
- **Kriteria sebelum penyusunan:**
  - [x] Cardinality sesuai keputusan, telepon tidak unik, plat normalisasi unik,
        registrasi mempertahankan snapshot dan tidak menetapkan pemilik kendaraan tetap.
  - [x] Semua kolom mempunyai tipe/nullability/default; PK/FK/UNIQUE/CHECK dan
        validasi transaksi/server dibedakan; target FK di luar irisan ditandai.
  - [x] Estimasi disetujui tetap, revisi/item dapat ditelusuri, Teknisi setara dengan
        minimal satu sebelum pengerjaan dimulai,
        versi konflik serta lock terminal/antrean/invoice dijelaskan tanpa izin baru.
  - [x] Skenario gagal dan batas keputusan tercantum; review independen dilakukan;
        tidak ada klaim DDL, concurrency, migrasi, atau keamanan runtime sudah diuji.
- **Bukti dokumentasi (Observed):** Read BSD penuh dan DB-01 IPD; 13 tabel dengan
  konvensi kolom bersama, diagram relasi, matriks 16 skenario dan dependensi terbuka.
  Planner read-only memberi masukan sebelum penyusunan. Reviewer independen
  menemukan nomor §3.5 ganda dan rujukan katalog keliru; diperbaiki menjadi §3.6
  serta §2.8/§2.12 dan reviewer menutup finding melalui pembacaan ulang.
  Review keamanan dokumen terpisah tidak menemukan blocker scoped; kontrol
  otorisasi, audit, data pribadi dan konflik offline masih spesifikasi, bukan
  enforcement yang sudah diuji. Rujukan prinsip SQL diperiksa lewat Context7.
- **Batas bukti:** tidak ada Git/baseline utuh tersimpan untuk diff independen.
  Bagian WEB-05 yang muncul selama pekerjaan dipertahankan. Pemeriksaan berupa
  inspeksi teks/skenario rancangan; tidak ada perintah tes aplikasi/DDL dijalankan.
- **Amendemen setelah review awal (2026-11-11):** user menetapkan penugasan wajib
  sebelum mulai, tanpa Teknisi utama; seluruh Teknisi setara. BSD menghapus penanda
  utama/constraint terkait, memperbarui invariant dan skenario review. Perubahan
  ini diperiksa lewat pembacaan/penelusuran teks; review independen sebelumnya
  berlaku pada draf sebelum amendemen ini, bukan verifikasi ulang amendemen.
  Prototype WEB-05 masih memakai utama/anggota; belum diubah pada irisan dokumen ini.
- **Batas:** invoice/pembayaran/stok/pembelian/retur dan tabel pengguna/katalog belum
  dirancang pada irisan ini. HPP otomatis/profit ditunda. Tidak ada migrasi/data
  yang disentuh. Rollback berupa pengembalian bagian dokumentasi DB-01 saja.

### WEB-05: Preview alur layanan dan tim SO (2026-11-11)

- **Lingkup:** pintu preview dengan panduan registrasi sampai nota dan dataset
  contoh terpisah dari data browser existing; SO mendukung teknisi utama dan anggota.
- **Rujukan:** CONTEXT §2.2–2.3/2.6–2.8, AFD §2, BSD §3, TRD §7, DBD reference lock.
- **Arah terkunci:** pertahankan shell, Inter, permukaan terang/gelap dan seluruh
  token prototype DESIGN_POS_Extend. Primary Shopmonkey sesuai riset existing DBD;
  plat mendahului metadata, petunjuk tahap memakai daftar berurutan. Tanpa media,
  dashboard angka, atau arah visual baru. Refero dipakai untuk mempertahankan lock;
  MCP Refero dan Impeccable tidak tersedia pada sesi ini.
- **Kriteria uji sebelum implementasi:**
  - Preview menyediakan contoh siap diproses dan navigasi tahapan tanpa menimpa
    ledger existing; reload mempertahankan latihan, kegagalan baca tidak direset.
  - Penugasan anggota memiliki riwayat, menolak duplikasi/anggota sama dengan utama,
    dan mengikuti lock/peran SO; workflow lama tetap terbaca.
  - Runner browser existing untuk progres, handoff, invoice dan POS tetap lolos;
    periksa tampilan desktop/ponsel, tema gelap serta error browser.
- **Batas:** data dummy lokal, bukan login/server/stok/pembelian nyata. Perubahan
  master kendaraan dan pembelian 11 November belum termasuk irisan preview ini.
- **Hasil aktual:** selesai untuk lingkup WEB-05. Tujuh suite existing lolos
  (103 kelompok pemeriksaan): fase 1/2/3A/3B/3C/4 dan POS. Suite preview tambahan
  lolos: isolasi dataset, reload, data rusak dipertahankan, anggota tersimpan,
  anggota duplikat/utama/tidak dikenal ditolak, lock peran/antrean serta render
  desktop/ponsel/gelap; console/page error kosong. Bukti di
  `prototype/evidence/verification-preview.json` dan `preview-*.png`.
- **Preview lokal:** server loopback port 8765 dijalankan; endpoint
  `/prototype/preview.html` mengembalikan HTTP 200. Tidak deploy atau mengubah
  skema produksi. Uji browser memakai konteks terisolasi, bukan data user.
- **Batas verifikasi:** otorisasi server, printer fisik, pembayaran dan stok nyata
  belum diuji karena belum diimplementasikan. SOP global OpenCode tidak terbaca;
  skill redesign/Impeccable dan MCP Refero tidak tersedia. Reference lock existing
  DBD dipertahankan melalui metode Refero, tanpa klaim riset live baru.

### WEB-04P: Beranda POS untuk Kasir (2026-11-07)

- **Lingkup:** default Kasir POS, antrean siap/draf/belum lunas dengan pencarian
  plat/nama/SO/invoice, preview SO tanpa write, editor invoice existing di kanan
  desktop dan alur list-detail mobile. Keputusan di CONTEXT §2.8; proyeksi/key
  preferensi pada BSD §3.4. Harga dan pembayaran mengikuti §2.7, bukan izin baru.
- **Rencana minimal:** POS hanya pemilik proyeksi, pilihan dan preview. Antrean
  handoff mendelegasikan renderer/listener; invoice tetap anak langsung main,
  dengan sibling grid dan guard print berdasarkan view aktual. Alternatif landing
  antrean lama lalu pindah halaman lebih kecil tetapi tidak memenuhi dua area.
  Planner read-only mendukung sibling-grid; tidak menambah dependency atau schema.
- **Pilihan demo:** preferensi peran terpisah whitelist, fallback Owner. Kasir clean
  masuk POS; invoice aktif tetap menjadi detail POS. Dirty SO/invoice tidak dipindah
  paksa, peran tetap berganti dengan pemberitahuan dan isian dipertahankan. Filter
  Lunas/Semua tersedia untuk meninjau nota; pilihan tidak otomatis berpindah saat
  pembayaran mengeluarkan baris dari daftar default. Nilai pilihan hanya memori UI.
- **Kriteria sebelum kode (runner Python Playwright existing):**
  - [x] Kasir clean masuk POS dan reload mempertahankan preferensi; nilai invalid/
        kegagalan preferensi tidak mengubah ledger atau menjadi autentikasi palsu.
  - [x] Daftar satu entri/SO mencakup siap, draf, belum lunas; stale ditandai Owner,
        total/sisa tepat, cari empat identitas/filter/kosong bekerja tanpa write.
  - [x] Preview tanpa write lalu create eksplisit; invoice dibuka/dibayar/dicetak
        dari POS dengan editor tunggal dan nota Rp0/uang/kembalian mengikuti WEB-04.
  - [x] Dirty cancel mempertahankan input, pilihan dan konteks; role-switch dirty
        tidak membuang isian; pembayaran tidak memilih baris berikutnya otomatis.
  - [x] Teknisi tidak dapat membuka POS dan DOM daftar/preview dibersihkan; harga
        Owner-only serta handler/replay transaksi existing tetap terjaga.
  - [x] Konflik/offline/failed write tidak replay, tidak mengubah pilihan menjadi
        sukses palsu; cetak hanya detail invoice final yang benar-benar aktif.
  - [x] Dua area desktop dan list-detail mobile, light/dark, 320px/200%, keyboard/
        fokus serta print receipt-only lulus. Seluruh regresi 1/2/3A/3B/3C/4 lulus;
        perubahan ekspektasi hanya untuk navigasi yang memang disetujui.
  - [x] Review correctness dan security terpisah ditutup, dokumentasi diperbarui.
- **Status (Observed):** selesai 2026-11-07. Delapan JS lolos `node --check` exit 0.
  Suite POS exit 0, 12 kelompok lulus pada 05:00:53 UTC. Regresi 1/2/3A/3B/3C/4
  lulus 20/16/12/17/14/12 kelompok pada 05:00:54–05:03:40 UTC; total 103 kelompok,
  seluruh daftar error browser yang direkam kosong. Laporan:
  `../../prototype/evidence/verification-pos.json` dan laporan fase terkait.
- **Red/green:** landing Kasir dan preview awal gagal sebelum implementasi. Tes
  failed-create menemukan tombol tetap disabled setelah reload karena render
  berlangsung saat loading; renderer dipanggil kembali sesudah loading selesai.
  Review menemukan warning pilihan di luar filter hanya pada panel invoice yang
  tersembunyi saat preview; warning kini juga tampil di preview, diuji tanpa write.
- **Regresi:** tes lama mengasumsikan peran Kasir tidak menavigasi dan klik antrean
  langsung ke SO. Jalur diperbarui dengan navigasi eksplisit dan preview → Buka SO;
  invoice final belum lunas kini diuji tetap ada di POS, sedangkan filter Siap
  ditagih kosong. Assertion bisnis/uang/lock tidak dilemahkan. Bukti gagal disimpan.
- **Review:** correctness menutup minor context warning dengan probe Chromium
  independen; security tidak menemukan blocker scoped lewat inspeksi dan bukti tes
  primary. Probe security independen tidak berjalan karena adapter/quoting, sehingga
  tidak diklaim sebagai verifikasi terpisah. Detail:
  `../../prototype/evidence/review-pos.md`.
- **Visual dan batas:** enam screenshot detail light/dark desktop/tablet/mobile,
  satu daftar mobile dan satu print dibuka. Print diuji lewat mock/handler
  beforeprint dan emulasi media, bukan dialog OS/perangkat fisik. Detector hanya
  Inter existing. Chromium headless saja; no-auth, localStorage non-atomik dan
  batas backend/gateway/stok/refund WEB-04 serta PRD §9 produksi tetap berlaku.
- **Rollback:** baseline Fase 4 memahami ledger yang sama; key peran boleh diabaikan.
  Tidak ada migrasi atau penghapusan data. Writer pra-Fase-4 tetap tidak aman untuk
  origin yang sudah memiliki invoice.

### WEB-04: Invoice, pembayaran penuh dan nota demo (2026-11-07)

- **Lingkup:** satu alur dari antrean 3C ke draf, harga Owner, final Kasir/Owner,
  pembayaran penuh tunai/transfer/gateway simulasi, koreksi harga Owner dengan
  saldo/kelebihan terpisah dan cetak browser invoice final. CONTEXT §2.7 menjadi
  sumber keputusan baru; model JSON dummy di BSD §3.3.
- **Pilihan demo:** item/qty invoice tetap snapshot realisasi; perubahan pekerjaan
  lewat tarik/revisi/serahkan SO sebelum invoice final. Draf stale dipulihkan Owner
  dengan muat realisasi terbaru beralasan; tidak otomatis menimpa harga draf lama.
  Final mengunci sumber SO permanen; koreksi hanya harga invoice. Batas 200 event.
  Pembayaran sisa penuh sesudah koreksi bukan dukungan DP/cicilan/tempo. Refund,
  retur, gateway nyata, stok nyata dan layout printer termal bukan implementasi ini.
- **Rencana:** satu modul invoice, ledger berurutan snapshot/pembayaran, reuse parser
  angka/persist/dirty guards existing; tidak menambah dependency. Shared lock final
  menjaga SO, antrean menampilkan draf tetapi mengecualikan final. Printer browser
  memakai print CSS dan snapshot final tersimpan bertanda simulasi. Invoice writes
  mensyaratkan status online browser sebagai guard demo, bukan verifikasi server.
- **Planner:** provider planner gagal TLS; review rencana read-only memakai agent
  general berhasil. Masukan diadopsi: ledger urut tunggal, prefix append-only, cash
  tender terpisah dari penerimaan bersih dan lock final berbeda dari keanggotaan antrean.
- **Seam verifikasi:** Python Playwright existing, browser UI dan storage untuk
  persistensi/failure/conflict serta fixture malicious. Tidak memakai server produksi.
- **Kriteria sebelum kode:**
  - [x] Legacy tanpa invoices terbaca tanpa rewrite; invoice tunggal dari handoff
        aktif, salin realisasi tepat, estimasi/master tetap.
  - [x] Kasir/Owner create/issue/pay; hanya Owner price/correct/rebase; Teknisi baca.
        Guard role ada pada handler dan replay, bukan hanya kontrol disabled.
  - [x] Draf stale setelah withdrawal/requeue tidak dapat diterbitkan atau ditimpa;
        Owner rebase eksplisit menjaga riwayat. Final mengunci withdrawal/progres/biaya SO.
  - [x] Invoice final Rp0 Lunas tanpa event pembayaran; nominal positif belum lunas
        sampai full payment; cash change, transfer reference dan gateway demo teruji.
  - [x] Koreksi tidak mengubah pembayaran; sisa/kelebihan terpisah; tanpa refund
        otomatis. Payment replay/zero/partial/unsafe/duplicate ditolak.
  - [x] Failed writes/conflict/offline/dirty/nav/unload tidak membuang input atau
        replay aksi; basis invoice baru membatalkan persetujuan/input stale.
  - [x] History salah sumber/aktor/urutan/nominal/snapshot dan rewrite prefix ditolak
        tanpa reseed. Tidak ada sumber stok atau uang nyata yang berubah.
  - [x] Cetak hanya final tersimpan; kontrol/riwayat tidak ikut, total/status tepat,
        tanpa side effect; teks/markup aman, riwayat lengkap Owner-only.
  - [x] Light/dark desktop/tablet/mobile, 320px/200%, keyboard/fokus dan seluruh
        regresi 1/2/3A/3B/3C lulus; review correctness/security terpisah ditutup.
- **Status (Observed):** Fase 4 prototype selesai 2026-11-07. Tujuh JS lolos
  `node --check` exit 0. Suite browser Fase 4 exit 0 dengan 12 kelompok lulus,
  termasuk 19 injeksi data invalid. Regresi 1/2/3A/3B/3C lulus 20/16/12/17/14
  kelompok; total 91 kelompok. Laporan `../../prototype/evidence/verification-phase4.json`
  (03:57:31 UTC), regresi pada 03:30:40–54 UTC. Perubahan sesudah run regresi hanya
  print-media CSS dan instrumentasi tes; guard layar/JS tidak diubah lagi.
- **Review:** correctness/security terpisah menemukan guard cetak konflik dapat
  dibuka oleh render. Latch konflik dipisah, hanya clear pada reload sukses;
  beforeprint juga memeriksa revision storage valid dan menutupi receipt stale/dirty.
  Reviewer menutup blocker setelah memeriksa patch, probe independen dan laporan.
  Mereka tidak menjalankan seluruh suite browser secara independen.
- **Visual:** enam screenshot invoice desktop/tablet/mobile light/dark dibuka.
  Inspeksi print-media menemukan canvas HTML masih gelap; assertion membuktikan
  gagal, lalu root print dipaksa putih dan suite utuh lulus. Konfirmasi screenshot
  print terbaru putih. Detector hanya menandai Inter existing; token tidak diganti.
- **Penyesuaian harness:** mock print awal dikoreksi agar tidak memanggil dirinya
  saat dipasang. Dua run kemudian gagal startup karena aset `ERR_CONNECTION_REFUSED`;
  diagnostik dipertahankan. Backlog HTTP tes Python 3.12 terukur 5, dinaikkan ke 128
  untuk burst skrip context baru; setelahnya seluruh suite lulus tanpa melonggarkan
  assertion. Backlog sebagai kontribusi penyebab adalah Inferred, bukan bukti eksklusif.
- **Batas verifikasi:** print memakai handler `beforeprint` terpicu tes dan emulasi
  media cetak, bukan operasi dialog OS/printer fisik. Chromium headless saja;
  screen reader/perangkat asli/browser lain belum diuji. No-auth, localStorage
  non-atomik, gateway demo, tanpa stok/refund/backend nyata tetap berlaku. Gate PRD
  §9 produksi belum tersedia/hijau. Catatan lengkap: `../../prototype/evidence/review-phase4.md`.
- **Rollback:** jangan jalankan writer pra-Fase-4 pada origin berisi invoice;
  build lama mengabaikan ledger/lock final. Gunakan origin/salinan dummy terpisah,
  bukan menghapus history atau mengubah pembayaran.

### WEB-03C: Penyerahan realisasi dan antrean kasir (2026-11-07)

- **Lingkup:** menyerahkan SO terminal dengan realisasi tersimpan, antrean turunan
  Kasir/Owner, penguncian saat mengantre, penarikan Owner beralasan, revisi dan
  penyerahan ulang eksplisit. Keputusan user di CONTEXT §2.6; bukan fase invoice.
- **Kontrak:** field JSON opsional menurut BSD §3.2; pola persist/validasi/role,
  dirty guard, error dan conflict existing dipakai ulang. Tidak ada dependency,
  backend, migrasi, reservasi/pengeluaran stok, pembayaran atau invoice baru.
- **Pilihan demo reversible:** wajib realisasi eksplisit tersimpan, tidak otomatis
  memakai estimasi. SO Selesai Rp0 boleh diserahkan dengan label tanpa biaya;
  SO Dibatalkan Rp0 tidak ditagihkan/tidak mengantre. Ini tidak memutuskan invoice
  Rp0. Hak penyerahan ulang mengikuti hak penyerahan awal; revisi baru tidak wajib
  bila hanya salah tarik, tetapi aksi penyerahan ulang tetap wajib. Batas 100 event.
- **Rancangan minimal:** modul handoff khusus dengan history dua counter; antrean
  dihitung dari SO, tidak disimpan duplikat. Guard biaya/reopen memakai lock bersama
  dan validasi persist menolak pelanggaran historis. Boolean antrean ditolak karena
  tidak menyimpan jejak penarikan/penyerahan ulang. Planner read-only telah menilai.
- **Arah:** reference lock dan ledger WEB-03C di DBD; token existing. Refero tidak
  tersedia, riset live Shopmonkey `/product/workflow` dan `/product/invoices` dibaca.
- **Seam:** runner Python Playwright browser existing seperti 3B; storage hanya
  untuk persistensi, fixture legacy dan injeksi gagal/konflik/history malformed.
- **Kriteria sebelum kode:**
  - [x] Legacy tanpa handoff terbaca tanpa write/reseed; estimasi/master tetap.
  - [x] Owner/Teknisi menyerahkan Selesai; hanya Owner menyerahkan Dibatalkan berbiaya;
        realisasi belum tersimpan, SO aktif, Kasir dan Dibatalkan Rp0 ditolak.
  - [x] Penyerahan dirty/konfirmasi batal/ganda tidak menulis atau mengautosave;
        tampilan memakai realisasi final dan Rp0 tidak ditandai lunas.
  - [x] Queued mengunci revisi/reopen, termasuk handler buatan dan validator persist.
  - [x] Owner menarik dengan alasan/konfirmasi, biaya/progres tetap; setelah revisi
        perlu serahkan ulang, tidak ada duplikasi antrean.
  - [x] Failed write/conflict menjaga isian tanpa sukses palsu; retry tidak replay.
  - [x] History palsu (aktor/status/counter/waktu/urutan/lock) ditolak tanpa reseed.
  - [x] Antrean cari/filter/kosong, detail tepat, role-switch/DOM, keyboard/fokus,
        light/dark desktop/tablet/mobile, 320px dan teks 200% teruji.
  - [x] Regresi 1/2/3A/3B lulus; review correctness dan security terpisah ditutup.
- **Status (Observed):** 3C selesai pada 2026-11-07. Enam file JS lolos
  `node --check` exit 0. Python Playwright 3C exit 0, 14 kelompok lulus termasuk
  15 injeksi history malformed; regresi 1/2/3A/3B lulus 20/16/12/17 kelompok.
  Bukti: `../../prototype/evidence/verification-phase3c.json` dan laporan fase terkait.
- **Red/green dan review:** tracer menu antrean gagal sebelum menu dibuat, lalu
  lulus. Tracer penyerahan gagal sebelum panel/handler dibuat, lalu lulus. Laporan
  gagal tetap disimpan. Reviewer correctness menemukan gap tes gate Kasir dan
  terminal tanpa realisasi yang tertutup oleh gate lain; tes mandiri ditambahkan,
  kedua reviewer menutup gap setelah membaca kode dan hasil browser terbaru.
- **Visual:** enam screenshot antrean desktop/tablet/mobile light/dark dan satu
  detail error/riwayat pada 320 px dibuka; tes teks 200% serta fokus keyboard lulus.
  Detector hanya menandai Inter existing. Catatan: `../../prototype/evidence/review-phase3c.md`.
- **Batas:** role dan audit klien tetap simulasi, localStorage tidak atomik, tidak
  ada backend/invoice/pembayaran/stok nyata. Screen reader, perangkat fisik dan
  browser non-Chromium belum diuji. Isian alasan penarikan yang belum tersimpan
  tidak dijamin pulih dari crash. PRD §9 produksi tetap terbuka. Jangan gunakan
  build pra-3C menulis origin yang sudah memiliki handoff: build lama mengabaikan lock.

### WEB-03B: Realisasi SO dan qty pecahan (2026-11-07)

- **Lingkup:** editor realisasi terpisah dari estimasi disetujui, tambah/hapus item,
  qty/harga lokal, alasan, pengakuan persetujuan tambahan biaya, riwayat Owner.
  Sumber perilaku: CONTEXT §2.1–§2.5. Antrean kasir tetap 3C; invoice tetap Fase 4.
- **Keputusan angka user:** tiga desimal sesuai satuan, pembulatan rupiah terdekat
  per baris dengan setengah naik. Dukungan dipakai pada estimasi dan realisasi agar
  penyalinan SO tetap konsisten. Qty disimpan sebagai teks desimal; kalkulasi skala
  1.000 memakai integer/BigInt. Snapshot SO lama tetap terbaca tanpa rewrite.
- **Pilihan demo reversible:** simpan realisasi eksplisit, satu alasan per revisi;
  item baru atau kenaikan subtotal baris meminta pengakuan persetujuan lisan walau
  total bersih turun. Checkbox direset saat rincian/peran/basis berubah. Realisasi
  kosong sah untuk tanpa biaya; qty nol tidak sah, gunakan hapus. Owner boleh
  menyesuaikan biaya SO Dibatalkan tanpa membuka kembali status. Batas teknis demo:
  100 baris, 200 revisi, qty maksimal 999999,999 dan harga maksimal Rp1.000.000.000;
  bukan batas bisnis atau ambang persetujuan. Tidak ada stok/reservasi nyata.
- **Arah visual:** perluasan reference lock DBD UI-01/WEB-02/03A, mode Operate,
  ENERGY 1 / RHYTHM 2 / MOTION 2. Form realisasi memakai pola estimasi existing,
  estimasi read-only tetap sebagai pembanding. Warna/font/radius hanya token aktif.
  Refero gagal NO_SUBSCRIPTION; tidak mengklaim mendapat referensi baru.
- **Seam pengujian:** browser Python Playwright existing, dikonfirmasi user saat
  memilih qty pecahan; inspeksi storage hanya untuk persistensi dan injeksi kegagalan.
- **Kriteria uji sebelum kode:**
  - [x] SO lama dibuka tanpa write; estimasi/master tidak berubah setelah revisi.
  - [x] Estimasi dan realisasi menerima pecahan sesuai satuan; hitungan setengah naik tepat.
  - [x] Tambah/hapus/ubah dan realisasi kosong tersimpan setelah reload dengan alasan/history.
  - [x] Tambahan biaya tanpa approval ditolak; perubahan/reset role membatalkan checkbox lama.
  - [x] Kasir read-only; Teknisi ditolak pada Selesai/Dibatalkan termasuk submit buatan.
  - [x] Owner dapat revisi biaya terminal tanpa mengubah status atau menerbitkan invoice.
  - [x] Input invalid, no-op, overflow, alasan kosong, history palsu ditolak tanpa write/reseed.
  - [x] Gagal write/conflict menjaga input; retry tidak replay; basis stale tidak menimpa tab lain.
  - [x] Dirty guard navigasi/unload, perubahan role dan progres tidak membuang editor realisasi.
  - [x] Markup menjadi teks; riwayat lengkap tidak tertinggal di DOM setelah Owner berganti peran.
  - [x] Regresi Fase 1/2/3A; light/dark desktop/tablet/mobile, 320px/200%, keyboard/fokus lulus.
- **Status (Observed):** 3B selesai diverifikasi pada 2026-11-07. Lima file JS
  lolos `node --check` (exit 0). Suite 3B lulus 17 kelompok, regresi Fase 1/2/3A
  lulus 20/16/12 kelompok. Laporan segar berada di `../../prototype/evidence/`
  dengan nama `verification-phase3b.json`, `verification-phase1.json`,
  `verification-phase2.json` dan `verification-phase3a.json`.
- **Rencana penutupan 2026-11-07:** jalankan ulang 3B dan regresi 1/2/3A,
  review correctness/keamanan terpisah, lalu selaraskan README dan catatan review.
  Review awal menemukan log harga Diagnosa tetap di DOM non-Owner, kompatibilitas
  qty legacy berawalan nol, serta overflow total estimasi tanpa pesan pemulihan.
  Perbaikan terbatas pada mekanisme tersebut; tidak mengubah arah visual atau 3C.
- **Tambahan kriteria sebelum patch penutupan:**
  - [x] Fixture pra-3B dengan qty SO numerik dan qty diagnosa berawalan nol dibaca
        tanpa rewrite, baik tanpa workflow maupun dengan workflow.
  - [x] Log harga Diagnosa dibersihkan dari DOM setelah Owner berganti ke kedua
        peran lain, termasuk ketika halaman Diagnosa sudah ditinggalkan.
  - [x] Overflow agregat estimasi memberi pesan dan fokus pemulihan; approval tidak
        berhasil. Overflow realisasi menolak write dan mempertahankan rincian.
  - [x] Approval tetap wajib saat total bersih turun; perubahan workflow/basis
        membatalkannya. Pembatalan unload mempertahankan isian dan storage.
  - [x] Batas 100 baris dan 200 revisi diuji pada batas sah dan penolakan berikutnya;
        subtotal pecahan sesudah reload serta snapshot/master tetap diverifikasi.
- **Review dan red/green:** correctness dan security reviewer terpisah menemukan
  tiga masalah pada integrasi Diagnosa/parser bersama. Browser membuktikan ketiganya
  gagal sebelum patch (`failure-phase3b-20261107T013016893007.json`), lalu lulus
  setelah parser menerima leading zero tanpa rewrite, daftar log hanya dirender
  untuk Owner, dan overflow estimasi memberi pesan/fokus. Kedua reviewer menutup
  finding setelah memeriksa patch, tes, serta laporan segar; tidak menjalankan
  ulang browser secara independen. Detail: `../../prototype/evidence/review-phase3b.md`.
- **Visual:** enam screenshot desktop/tablet/mobile light/dark serta dua keadaan
  dirty/error dengan riwayat Owner terbuka pada 320 px/teks 200% dibuka dan diperiksa.
  Token dan layout existing dipertahankan. Detector menandai Inter pada HTML/CSS;
  font tetap karena keputusan proyek. Regresi menghitung 14 pasangan kontras ≥4,5:1.
- **Batas:** role/teknisi/data dummy dan localStorage sequential, bukan autentikasi,
  kerahasiaan storage, audit tahan manipulasi atau transaksi lintas tab atomik.
  Isian realisasi belum tersimpan tidak pulih dari crash/force-close. Chromium
  headless saja; screen reader, browser lain, keyboard ponsel fisik dan printer belum
  diuji. Saat penutupan 3B, backend, reservasi/pengeluaran stok, antrean kasir 3C
  dan invoice Fase 4 belum diimplementasikan; perkembangan antrean lihat WEB-03C.
  PRD §9 belum tersedia; gate keamanan produksi tetap terbuka.

### DATA-01: Keputusan reservasi dan pengeluaran stok (2026-11-06)

- **Lingkup:** menyelaraskan dokumen dengan keputusan user: tanpa Redis dahulu,
  reservasi tersimpan di MySQL dan terlihat melalui API, pengeluaran stok saat
  invoice final diterbitkan. Bukan implementasi backend, migrasi, atau UI.
- **Kriteria verifikasi sebelum penyuntingan:**
  - [x] CONTEXT mencatat keputusan dan menggantikan pemicu pembayaran lama.
  - [x] PRD/AFD/TRD konsisten mengenai reservasi, invoice final, dan pembayaran.
  - [x] BSD mencatat tanggung jawab data tanpa menganggap skema fisik sudah final.
- **Status (Observed):** penyelarasan dokumen selesai. Pemeriksaan teks lintas
  dokumen menemukan aturan pembayaran lama di metaprompt; aturan tersebut diganti
  dengan rujukan keputusan terbaru. Pembacaan ulang bagian yang diubah memeriksa
  pemicu invoice final, transaksi atomik/idempotensi, dan pemisahan status skema.
- **Batas:** belum ada implementasi backend, migrasi, API stok, atau tampilan stok
  yang diuji. Bagian UI ini baru persyaratan, bukan perubahan visual prototype.

### WEB-03A: Daftar SO dan progres pekerjaan (2026-11-04)

- **Permintaan:** user menyetujui mulai 3A setelah pemecahan fase dan rekomendasi
  tombol Mulai pengerjaan. Hanya daftar/detail, penanggung jawab, status dan riwayat.
- **Sumber:** CONTEXT §2.2, PRD F-05, AFD §2.2, arah visual WEB-01/02 dipakai ulang.
- **Pilihan demo 3A, belum aturan produksi final:** SO tanpa workflow dibaca Belum
  dimulai tanpa rewrite. Mulai memerlukan teknisi contoh. Dalam Pengerjaan dapat
  ditunda/diselesaikan/dibatalkan; Ditunda dilanjutkan sebelum bisa diselesaikan.
  Belum dimulai juga boleh dibatalkan. Alasan wajib tunda/batal/buka kembali dan
  pergantian penanggung jawab existing. Selesai/batal/buka kembali dikonfirmasi.
  SO Selesai hanya Owner dapat membuka kembali ke Dalam Pengerjaan; pembatalan
  terminal, kunjungan berikutnya SO baru. Pilihan demo ini dapat ditinjau user.
- **Batas:** rincian dan harga estimasi tetap snapshot read-only; tidak menyatakan
  realisasi/tagihan final. Pembatalan tidak menghapus item, mengurangi stok, atau
  membuat invoice. Penyesuaian biaya di 3B, finalisasi antrean kasir di 3C.
- **Kontrak implementasi:** workflow opsional pada SO version 1; validasi replay
  history memeriksa transisi, penanggung jawab, role, alasan dan timestamp. Aksi
  eksplisit, bukan autosave status. Isian tindakan lokal dipertahankan saat gagal/
  konflik, retry hanya reload dan tidak mengeksekusi aksi otomatis. Navigasi dengan
  isian belum diterapkan meminta konfirmasi; unload memberi peringatan browser.
- **Kriteria uji sebelum kode:**
  - [x] SO Fase 2 terbaca tanpa migrasi/reseed; buka detail tidak menulis data.
  - [x] Daftar cari/filter/kosong dan tautan kunjungan/diagnosa bekerja.
  - [x] Penanggung jawab dapat ditetapkan/diubah dengan alasan yang sesuai.
  - [x] Mulai/tunda/lanjutkan/selesai/batal dan Owner-only reopen tepat serta tercatat.
  - [x] Alasan kosong, transisi ilegal dan pembatalan konfirmasi tidak menulis.
  - [x] Kasir read-only; Teknisi tidak mengubah completed/cancelled lewat handler.
  - [x] Failed write/conflict tidak membuat status/riwayat palsu; retry tidak replay.
  - [x] Isian lokal, pergantian role dan guard meninggalkan form tidak hilang diam-diam.
  - [x] Workflow malformed/replay palsu ditolak; markup menjadi teks; snapshot tetap.
  - [x] Regresi Fase 1/2, keyboard/fokus dan desktop/mobile light/dark lulus.
- **Status (Observed):** 3A selesai. Sintaks tiga file JS exit 0. Python Playwright
  3A exit 0 dengan 12 kelompok uji; regresi Fase 1 20 dan Fase 2 16 lulus. Bukti:
  `../../prototype/evidence/verification-phase3a.json` dan laporan regresi existing.
  Ketiga suite memakai server loopback port dinamis dan browser context terisolasi.
- **Red/green:** tracer browser menu SO gagal ketika fitur belum ada, kemudian
  lulus. Kegagalan test setup (klik reset tersembunyi setelah event sintetis, bukan
  input pengguna) dipertahankan pada laporan failure; setup diperbaiki tanpa
  menghapus assertion penolakan transisi ilegal.
- **Review:** reviewer correctness menemukan fokus reset, relasi error ke kontrol,
  dan bukti narrow/zoom detail belum lengkap. Semuanya diperbaiki; tes fokus/ARIA,
  keyboard submit, detail/form/history 320 px dan teks 200% ditambahkan. Reviewer
  menutup dua finding kode; pembaruan IPD ini menutup finding status dokumentasi.
  Security review tidak menemukan blocker pada scope dummy. Gap keamanan produksi
  tetap terbuka; rujukan persyaratan existing di TRD §4, bukan klaim PRD §9 hijau.
- **Visual:** enam screenshot desktop/tablet/mobile light/dark dan daftar mobile
  dibuka; arah/token existing tetap. Detector hanya menandai Inter yang ditetapkan
  proyek. Catatan gate: `../../prototype/evidence/review-phase3a.md`.
- **Batas:** localStorage sequential, bukan atomik; data/teknisi/role dummy, bukan
  akun atau audit tahan manipulasi. Tidak ada backend, invoice, pengurangan stok,
  atau realisasi biaya. Screen reader, keyboard ponsel fisik dan browser non-Chromium
  belum diuji. Isian tindakan tidak pulih dari crash/force-close; navigasi normal
  memberi peringatan dan tindakan tersimpan tetap terjaga.

### WEB-02: Diagnosa & Estimasi dan handoff SO (2026-11-04)

- **Lingkup sesi:** Fase 2 pada prototype HTML/CSS/JS existing. Registrasi → form
  pemeriksaan/rekomendasi → estimasi itemized → pengakuan persetujuan lisan oleh
  Teknisi/Owner → salinan SO sekali. Preview SO hanya handoff, bukan progres Fase 3.
- **Sumber:** CONTEXT §2.2, PRD F-03/F-13/F-14, AFD §2.2. Reference lock FigCraft
  dan token aktif dipakai ulang; tidak ada arah visual baru atau dependency baru.
- **Pilihan demo:** satu diagnosa aktif per registrasi; state dokumen Draf/Disetujui
  bukan keputusan status pemeriksaan penuh. Qty bilangan bulat 1–999, harga integer
  rupiah 0–1.000.000.000; qty pecahan belum ditentukan. Katalog/harga berlabel contoh.
  Harga berubah hanya lokal, alasan diwajibkan sebelum approval bila berbeda master;
  log perubahan tersimpan hanya ditampilkan Owner. Batas angka adalah validasi demo,
  bukan batas nominal otomatis untuk persetujuan biaya.
  Batas qty bulat 1–999 di atas adalah riwayat penutupan Fase 2, digantikan dukungan
  satuan/qty pecahan pada CONTEXT §2.5 dan implementasi WEB-03B.
- **Kompatibilitas:** collection diagnoses/serviceOrders opsional pada store version 1;
  record/draf registrasi lama dipertahankan, collection malformed ditolak tanpa reseed.
- **Kriteria uji sebelum implementasi:**
  - [x] Buka dari registrasi yang benar; identitas/keluhan tidak dientry ulang.
  - [x] Owner/Teknisi membuat/mengubah; Kasir baca saja, termasuk handler buatan.
  - [x] Baris katalog bisa ditambah/dihapus; qty/harga dan subtotal jasa/part/total tepat.
  - [x] Draf pulih setelah reload; input invalid tetap dapat disimpan sebagai draf.
  - [x] Temuan/rekomendasi/item valid dan persetujuan lisan eksplisit wajib sebelum approval.
  - [x] Persetujuan berhasil membekukan snapshot; gagal write tidak mengubah status.
  - [x] SO tidak bisa dibuat dari Draf; setelah approved salinan independen tepat sekali
        pada alur sequential, bukan jaminan write lintas tab atomik.
  - [x] Storage error/conflict mempertahankan input; retry tidak menimpa versi approved.
  - [x] Collection rusak, ID/referensi tidak valid, negatif/pecahan/overflow, serta markup diuji.
  - [x] Regresi Fase 1 lulus; desktop/mobile light/dark, keyboard/fokus/overflow diperiksa.
- **Status (Observed):** Fase 2 selesai. `node --check` kedua file JS exit 0;
  Python Playwright Fase 2 exit 0 dengan 16 kelompok pemeriksaan; regresi Fase 1
  20 kelompok lulus. Bukti aktual: `../../prototype/evidence/verification-phase2.json`
  dan `../../prototype/evidence/verification-phase1.json`.
- **Visual:** enam screenshot desktop/tablet/mobile light/dark, estimasi disetujui
  dan preview SO dibuka. Overflow diuji sampai 320 px dan teks 200%; tetap memakai
  token existing. Detector hanya memberi peringatan Inter, dipertahankan karena
  pilihan font proyek; bukan alasan mengganti font atau menambah dependency.
- **Review:** temuan harga melewati input invalid, alasan menyusul, dan alias objek
  log saat failed write diperbaiki dengan deep clone dan regresi. Reviewer menutup
  temuan tersebut. Navigasi registrasi diperbaiki agar base style tidak hilang.
  Pemulihan konflik approval diuji dengan menolak/menerima penggantian isian lokal.
- **Batas:** collection data/log belum memiliki anggaran ukuran menyeluruh; tidak
  ada stress test. Role guard hanya simulasi browser, bukan kerahasiaan storage
   atau otorisasi server. Saat penutupan WEB-02, qty pecahan, status pemeriksaan
   lengkap, realisasi/pembatalan SO dan invoice belum dibangun; progres SO dan
   realisasi terbaru mengikuti WEB-03A/03B. Gate keamanan produksi terbuka.
  Catatan delivery dan keputusan visual: `../../prototype/evidence/review-phase2.md`.

### WEB-01: Prototype browser bertahap, Fase 1 registrasi (2026-11-04)

- **Permintaan:** mulai prototype HTML/CSS/JS dengan data dummy, dibagi fase kecil.
- **Rujukan:** CONTEXT §2.2 (keputusan terbaru), PRD F-03, AFD §2, TRD lingkup prototype,
  reference lock DBD dan token aktif DESIGN_POS_Extend. Prototype lama dan FigCraft
  tetap sebagai artefak historis; browser baru berada di `prototype/index.html`.
- **Peta fase:**
  1. Shell, simulasi Owner/Teknisi/Kasir, registrasi daftar/form/detail, pencarian
     registrasi, draf lokal dan penyimpanan gagal yang jujur. **Irisan sesi ini.**
  2. Diagnosa & Estimasi itemized, persetujuan lisan, penyalinan ke SO.
  3. SO, progres, revisi realisasi, pembatalan dengan biaya, penguncian Owner.
  4. Kasir, invoice, pembayaran penuh simulasi gateway/tunai/transfer, cetak.
- **Batas Fase 1:** tidak membuat diagnosa/SO/invoice, tidak ada transaksi gateway,
  dependency baru, backend, login nyata, atau perubahan data legacy. Menu fase
  berikutnya hanya penanda roadmap yang jelas, bukan kontrol palsu.
- **Pilihan prototype:** simpan registrasi eksplisit, autosave draf saat input jeda
  400 ms sebagai nilai demo yang dapat direvisi; plat tidak unik antar kunjungan.
  Validasi format ringan, bukan verifikasi telepon/plat resmi. Data contoh seluruhnya
  fiktif; tidak untuk data pelanggan nyata. Benturan antar-tab ditolak, bukan ditimpa.
- **Cara uji dan kriteria selesai (ditulis sebelum implementasi):**
  - [x] Daftar dummy dapat dicari, difilter, dibuka ke detail yang benar.
  - [x] Owner/Teknisi/Kasir dapat meregistrasi; role switch eksplisit simulasi.
  - [x] Plat/nama/keluhan/telepon wajib; alamat opsional; submit invalid ditolak.
  - [x] Input diperlakukan sebagai teks; tidak mengeksekusi markup/script.
  - [x] Save lalu reload mempertahankan record; draf pulih tanpa menjadi record final.
  - [x] Storage write gagal mempertahankan isian, tidak mengklaim Tersimpan; retry
        berhasil tepat sekali. Storage rusak tidak otomatis diganti seed.
  - [x] Perubahan antar-tab berurutan terdeteksi dan save ditolak sampai data terbaru dimuat.
  - [x] Keyboard/fokus, mobile menu/Escape, light/dark, reduced motion dan layout
        desktop/tablet/mobile diperiksa di browser; screenshot dibuka.
  - [x] Hash `index.html` dan key legacy tidak berubah; console tanpa error aplikasi.
- **Status saat penutupan WEB-01 (Observed):** Fase 1 selesai dan diuji. Pada saat
  penutupan tersebut Fase 2–4 belum dibangun; progres terbaru lihat WEB-02.
  `node --check prototype/app.js` exit 0; Python Playwright Chromium headless exit 0
  dengan 20 kelompok pemeriksaan. Data pengujian memakai context browser terisolasi.
  Bukti: `../../prototype/evidence/verification-phase1.json`, screenshot di folder
  yang sama, dan catatan `../../prototype/evidence/review-phase1.md`.
- **Hasil visual:** desktop 1440, tablet 768, mobile 390 pada light/dark dan form
  desktop/mobile diperiksa. Lebar 320/620/1049/1050/1280 dan teks 200% diuji untuk
  overflow. Empat belas pasangan token kontras lulus ≥4,5:1; bukan audit WCAG penuh.
- **Review terpisah:** tiga temuan correctness (autosave submit invalid, isian lokal
  setelah konflik, normalisasi pencarian telepon) diperbaiki dan dinilai resolved.
  Finding collision ID draf/record juga ditutup; guard baca dan sebelum write diperiksa.
- **Kegagalan yang dipertahankan:** percobaan awal memiliki error test harness
  `Illegal invocation`; percobaan helper server berikutnya `ERR_EMPTY_RESPONSE`.
  Test diperbaiki dan memakai server loopback berport dinamis milik proses tes,
  ditutup dalam finally. Laporan gagal tetap berada di `prototype/evidence/`.
- **Batas:** Chromium headless, tanpa keyboard ponsel nyata/screen reader/printer;
  tanpa backend atau otorisasi server. Konflik localStorage berurutan terdeteksi,
  race penulisan simultan belum dijamin. Inter memakai fallback sistem bila font
  lokal tidak ada. Tidak ada klaim PWA/sinkronisasi atau transaksi produksi.
- **Kebijakan belum diputuskan:** status awal/transisi diagnosa, detail persetujuan
  tambahan, hak edit invoice draf dan refund. Tidak diimplementasikan di Fase 1.

### UI-01: Prototype visual seluruh menu di FigCraft (2026-10-30)
- **Permintaan:** mulai membangun berdasarkan rencana yang disetujui; FigCraft dahulu,
  browser setelah persetujuan visual. Seluruh 11 menu existing masuk cakupan.
- **Satu irisan:** satu artefak desain visual beserta varian desktop/mobile dan
  light/dark. Pembayaran dan detail WO adalah state pendukung, bukan modul backend.
- **Rujukan:** CONTEXT §5, PRD/AFD alur inti, DBD reference lock, token prototype.
- **Cara uji sebelum eksekusi:** inventaris 11 view dari index.html; cocokkan 44
  frame dasar, 4 frame pembayaran, dan state navigasi; periksa font tersedia.
- **Kriteria selesai:** seluruh menu terwakili, menu/tema memiliki tautan frame,
  screenshot desktop/mobile/light/dark diperiksa, kontras pasangan teks dihitung,
  file `.figcraft` dan preview tersimpan serta dapat dibuka kembali.
- **State tambahan:** sidebar ciut/menu mobile, detail WO, pembayaran, komponen
  kosong/memuat/error/offline/validasi/konfirmasi. Ini simulasi desain berlabel.
- **Batas:** tidak mengubah index.html atau data dokterac_v2; tidak memasang komponen
  21st atau mengintegrasikan backend. Seluruh data/harga tampilan adalah contoh.
- **Status:** artefak desain tersimpan dan siap ditinjau, menunggu persetujuan visual user sebelum tahap browser (2026-10-30).
- **Pemulihan sesi (Observed):** FigCraft awal kosong; generator existing gagal pada target `Light/Desktop/detail/collapsed`. Perbaikan dilakukan pada generator, geometri yang melampaui frame, kontras teks aktif, konteks Mekanik tanpa harga, dan tautan contoh yang identitasnya tidak sesuai.
- **Hasil akhir (Observed):** generator dan verifier exit 0: 138 frame, 44 tampilan dasar, empat pembayaran, 11.234 node, 1.462 tautan. Semua target sumber terurai; graf Mekanik hanya menjangkau tugas/detail/menu mekanik tanpa nominal. Kontras pasangan teks yang diperiksa tidak memiliki kegagalan; metode dan batasnya tercatat pada laporan artefak.
- **Penyimpanan (Observed):** `DBD/prototype/pos-ui.figcraft`, 485.762 byte, dibuka ulang setelah tab impor ditutup: empat halaman, 11.234 layer, tanpa repair. Metadata sidebar ciut dan ganti tema diperiksa setelah reopen. Preview desktop/mobile light/dark tersimpan dan dilihat.
- **Review:** review terpisah menemukan tiga masalah navigasi/status/penugasan; verdict pass menilai 3 resolved, 0 partial, 0 unresolved. Ini penutupan tiga temuan, bukan sertifikasi runtime.
- **Artefak dan bukti:** [README prototype](../DBD/prototype/README.md), [verifikasi](../DBD/prototype/verification.json), [manifest](../DBD/prototype/manifest.json). README memuat preview, metode regenerasi, delivery gate statis dan matriks navigasi.
- **Batas verifikasi:** field dan sebagian data statis diberi label; tidak mengklaim click-through, input form, autosave, pembayaran, otorisasi atau sinkronisasi berjalan. Keyboard/reduced-motion/zoom/ukuran antara wajib diuji saat browser. Refero MCP gagal `NO_SUBSCRIPTION`; reference lock tersimpan dipertahankan, Shopmonkey/Calendly dibaca ulang live. `workflow/DESIGN.md` kini ditemukan dan dibaca; catatan ketidakhadirannya pada CONTEXT merupakan state historis yang belum diselaraskan.

### UI-02: Template invoice cetak FigCraft (2026-10-30)
- **Permintaan:** tambahkan template invoice pada prototype yang sama.
- **Lingkup:** satu lembar A4 portrait editable, identitas bengkel/pelanggan/kendaraan,
  nomor invoice dan WO, tabel jasa/part, ringkasan nominal, pembayaran dan catatan.
- **Asumsi:** A4 sebagai format awal karena jenis printer belum diputuskan. Seluruh
  isian memakai placeholder; nama, kontak, harga, pajak dan garansi tidak ditetapkan.
- **Arah:** perluasan reference lock UI-01 dan token prototype existing. Kertas putih,
  Inter untuk tabel, plat menonjol, nominal rata kanan, tanpa chrome aplikasi.
  Dial cetak ENERGY 1 / RHYTHM 2 / MOTION 1 (dokumen statis).
- **Cara uji sebelum eksekusi:** render satu frame; inspeksi batas teks dan ukuran
  A4 595,276 × 841,89 point; periksa placeholder dan kontras; simpan dan buka ulang.
- **Kriteria selesai:** halaman `Invoice · Cetak` tersedia pada file existing;
  PDF satu lembar dan PNG tersimpan serta diperiksa; data contoh tidak menjadi nota resmi.
- **Status (Observed):** template selesai, 44 layer anak pada satu frame A4. Render
  diperiksa dan PDF dibaca satu halaman. Native tersimpan 488.238 byte, ditutup dan
  dibuka kembali tanpa repair: lima halaman, 11.279 layer. Kontras terendah yang
  dipakai 6,04:1. Bukti, delivery gate dan batas regenerasi ada di README prototype.
- **Riset:** Refero MCP gagal `NO_SUBSCRIPTION`; reference lock existing dipertahankan.
  URL Shopmonkey `/features/invoices` 404; homepage berhasil dibaca live.
- **Batas:** cetak fisik, pagination otomatis dan integrasi transaksi belum diuji.

### UI-03: Animasi UX prototype FigCraft (2026-10-30)
- **Permintaan:** terapkan animasi pada prototype FigCraft dahulu.
- **Lingkup:** transisi existing untuk sidebar desktop, menu mobile, tema pada alur
  utama, pembayaran dan status mekanik; tujuan navigasi existing dipertahankan.
- **Motion thesis:** perubahan lebar sidebar menjelaskan ruang kerja; menu masuk dari
  kiri; pembayaran memakai dissolve agar seluruh layar kasir tidak bergeser seperti modal.
  Tidak ada animasi dekoratif, loop, atau transaksi nyata.
- **Cara uji sebelum eksekusi:** periksa interaction index 0 dan tujuan existing;
  patch transition/durasi/easing; inspeksi sampel tiap kelompok dan tema; simpan,
  tutup, buka ulang, periksa persistensi. Screenshot hanya membuktikan frame statis.
- **Kriteria selesai:** transisi tersimpan pada file native dan flow demo dapat dipilih;
  dokumentasi menyebut durasi, batas playback headless dan reduced-motion.
- **Status (Observed):** 112 interaksi diperbarui dan 82 nama container sidebar
  disamakan untuk Smart Animate. Native 489.013 byte dibuka ulang tanpa repair,
  tetap lima halaman/11.279 layer. Sampel tiap kelompok diperiksa, termasuk setelah
  reopen. Frame statis desktop/mobile dilihat. Timing bersumber di DESIGN_POS_Extend.
- **Alternatif (Observed):** `pos-ui-no-motion.figcraft` disimpan, dibuka tanpa repair;
  sampel sidebar/menu mobile memiliki durasi 0 ms. Ini pilihan manual, bukan deteksi OS.
- **Batas verifikasi:** playback/interupsi/kelancaran/keyboard/reduced-motion OS
  belum terbukti pada sesi headless. `proto.present` hanya mengonfirmasi start frame.
  Cara mencoba dan delivery gate ada di README prototype.

### UI-04: Login, peran Owner/Teknisi/Kasir, estimasi WO, koreksi invoice, cari global, state interaksi (2026-10-31)
- **Permintaan:** terapkan keputusan user dari handoff
  `../POS-handoff-login-role-global-search.md` §4 pada prototype FigCraft existing
  dan rekonsiliasi dokumen (CONTEXT/PRD/AFD/TRD/DBD/DESIGN_POS_Extend).
- **Satu irisan:** satu artefak FigCraft yang diperluas + dokumen yang diselaraskan.
  Tanpa backend, tanpa dependency baru, tanpa regenerasi baseline lama, `index.html`
  tidak disentuh.
- **Rujukan:** handoff §4–§7; token prototype di `../DBD/DESIGN_POS_Extend.md`;
  referensi visual cari global `@shadcnuikit/command1` (struktur diadaptasi ke token
  POS; tidak memasang React/shadcn).
- **Lingkup frame baru:** login (desktop+mobile, light+dark), shell Kasir dengan
  navigasi terbatas, cari global (awal/hasil/kosong/memuat/error/varian Teknisi),
  detail WO estimasi (diagnosa terhubung + tabel estimasi itemized + demo edit harga
  lokal), invoice draft/final, koreksi invoice Owner, audit log Owner, galeri state
  interaksi (default/hover/fokus/pressed/disabled).
- **Cara uji sebelum eksekusi (sudah dijalankan, Observed):** inspeksi native
  (5 halaman, 11.284 node, 139 frame); roundtrip `figcraft-cli convert`
  figcraft→json→figcraft terbukti identik byte-per-byte pada `document.json`,
  jadi manipulasi JSON + convert dipakai sebagai jalur edit; scan target rename
  (112 teks "mekanik", 230 nama layer, 8 teks "supervisor", 0 lainnya).
- **Kriteria selesai (ditulis sebelum eksekusi):**
  - [x] Login punya 4 varian (desktop/mobile × light/dark); tiga tombol demo peran
        menuju destinasi yang diizinkan: Owner→Ringkasan, Kasir→shell Kasir terbatas,
        Teknisi→papan tugas Teknisi.
  - [x] Scan artefak: 0 kemunculan "Mekanik"/"mekanik"/"Supervisor" pada teks dan
        nama layer desain aktif (riwayat di dokumen tidak dihitung).
  - [x] Graf navigasi demo Teknisi dan Kasir tidak mencapai frame HPP/laporan/audit/
        koreksi final; graf Owner mencapainya (diperiksa dari metadata interaksi).
  - [x] Estimasi WO: subtotal baris = qty × harga satuan; subtotal jasa + subtotal
        part = total (dihitung ulang dari teks frame); demo edit harga lokal
        menampilkan harga master tidak berubah + entri log perubahan harga.
  - [x] Invoice final terkunci kecuali koreksi Owner; riwayat pembayaran tetap utuh;
        kelebihan bayar / sisa tagihan ditampilkan sebagai catatan terpisah, bukan
        refund otomatis.
  - [x] Cari global: hasil mencakup lebih dari plat (halaman, pelanggan, WO, invoice,
        jasa/part); varian Teknisi tanpa nominal terbatas; state awal/hasil/kosong/
        memuat/error tersedia; baris hasil menuju destinasi relevan.
  - [x] Galeri state interaksi memakai token baru yang dicatat di DESIGN_POS_Extend;
        kontrol UI-04 memakai tinggi 48 px, galeri 44 px (bukan klaim ulang seluruh arsip).
  - [x] `pos-ui-no-motion.figcraft` menerima konten yang sama dengan durasi 0 ms,
        tidak regresi ke versi lama (jumlah halaman/frame/node ≥ file utama sebelum
        irisan ini).
  - [x] Native disimpan, dibuka ulang (MCP, bukan CLI yang tidak tersedia), PNG dilihat;
        kontras pasangan teks baru dihitung (checker antislop-human).
- **Rencana pemulihan 2026-10-31:** seluruh journey UI-04 tersedia desktop/mobile
  dan light/dark. Hover memakai componentSet + instance dengan mouseEnter,
  mouseLeave, mouseDown/mouseUp dan changeTo; galeri bukan pengganti kontrol aktual.
  Verifier membaca native terbaru, menelusuri graf peran termasuk semua state komponen,
  menghitung ulang nominal, membandingkan no-motion dan menjaga invoice cetak.
  Kandidat dibuat dari snapshot native sebelum UI-04; generator baseline tidak dijalankan.
- **Butuh persetujuan user:** tidak ada aksi R2/R3; seluruh keputusan berasal dari
  handoff §4 yang sudah dikonfirmasi user. Kebijakan yang belum diputuskan (batas
  diskon/approval, kebijakan stok, modul harga lain, alur refund) TIDAK dibuat.
- **Status (Observed):** UI-04 tersimpan dan siap persetujuan visual. Main native
  3.456.465 byte; main dan no-motion dibuka ulang dengan `repairs: []`, 6 page dan
  93.861 layer. Ada 252 state layar baru desktop/mobile × light/dark, dua galeri,
  4.516 instance kontrol dengan lima variant. Semua role lama di desain aktif diganti.
- **Verifikasi akhir (Observed):** `verify_ui04.py` pada file native final exit 0:
  12 graf role, referensi/parent-child, seluruh variant (termasuk Focus), label instance
  materialized, angka baris/kategori/total terlihat, adjustment, penerimaan dan saldo.
  Delapan negative checks lolos dengan menolak pelanggaran yang diinjeksi. Template
  A4 identik dengan snapshot pra-UI04; no-motion identik selain motion, durasi nol.
- **Visual (Observed):** preview login light/dark desktop/mobile, estimasi, pencarian,
  koreksi invoice lunas dan galeri diperiksa. Header mobile panjang diperbaiki dan
  diuji geometri; 20 pasangan kontras token dihitung, minimum 4,881:1.
- **Review:** planner/security/review terpisah menemukan jalur role/uang, Focus,
  snippet, materialisasi dan header; diperbaiki. Empat dari lima temuan review
  dikonfirmasi terpisah selesai; sisa header kemudian ditutup lewat render dan gate.
- **Kegagalan yang diperbaiki:** impor awal menolak library page tanpa width;
  verifier menangkap aksi pada disabled nested instance; render mengungkap instance
  referensi tanpa anak/paint tidak terlihat. Konstruktor materialized diperbaiki,
  orphan setelah detach disabled ditutup, dan negative check tak saling menutupi.
  Kegagalan subtotal koreksi lama Rp 480.000 diperbaiki ke Rp 430.000 pada skenario
  pembatalan Rp 350.000 dari Rp 780.000. Revisi lunas mempertahankan pembayaran asal.
- **Artefak/bukti:** README prototype terbaru, `manifest-ui04.json`,
  `verification-ui04.json`, preview `screenshot/ui04-*.png`. Snapshot `pos-ui-before-ui04.figcraft`
  tersedia untuk regenerasi/rollback; generator baseline lama tidak dipakai.
- **Batas:** login/query/perhitungan adalah state simulasi. Playback/scrolling
  presenter, keyboard, reduced-motion OS, dan otorisasi server belum diverifikasi.
  Prototype siap tinjau, bukan aplikasi/backend yang selesai.

### ENV-01: Pembaruan runtime PHP dan target Laravel (2026-10-29)
- **Permintaan:** user menyetujui tetap memakai PHP dan memperbarui PHP/Laravel ke versi yang ditambal.
- **Lingkup:** runtime PHP XAMPP yang dipakai CLI/Apache; pencarian instalasi Laravel POS; penyelarasan target versi dokumen. Aplikasi lain di htdocs tidak di-upgrade tanpa identifikasi.
- **Target:** Laravel 13 untuk backend POS yang belum dibuat; PHP 8.4.27-1 TS x64 dari distribusi resmi Windows, setelah hash dan kompatibilitas diperiksa.
- **Cara uji sebelum aktivasi:** cocokkan SHA-256 ZIP dengan situs resmi; jalankan PHP staging tanpa startup warning; periksa ekstensi; periksa pemuatan modul Apache tanpa membuka listener.
- **Cara uji setelah aktivasi:** `php -v`, `php --ini`, modul dan koneksi TLS Composer; `httpd -t`; smoke test PHP Apache pada loopback dengan konfigurasi uji terpisah, lalu tutup proses uji.
- **Kriteria selesai:** runtime CLI dan modul Apache memakai rilis patched, konfigurasi/ekstensi yang dibutuhkan termuat, backup rollback tersedia; status Laravel dilaporkan berdasarkan instalasi nyata.
- **Rollback:** simpan folder PHP lama utuh dan salinan konfigurasi Apache; jika validasi aktivasi gagal, pulihkan pasangan runtime/konfigurasi. Runtime lama tidak boleh dibuka ke jaringan sebagai solusi keamanan.
- **Status akhir:** runtime PHP 8.4.27 (build Windows 8.4.27-1) berhasil diaktifkan setelah diagnosis gate endpoint. Target dokumen diselaraskan ke Laravel 13 sesuai persetujuan user. Backend POS belum dibuat; aplikasi Laravel lain di htdocs belum di-upgrade. Composer TLS lolos, tetapi audit Composer 2.9.5 melaporkan advisori yang perlu tindak lanjut terpisah.
- **Pemeriksaan lanjutan 2026-10-29 (Observed):** PHP aktif masih 8.2.12. ZIP staging cocok dengan SHA-256 resmi `53db2047139bdfb8e6c7c7d5860a0a6a2a4f1dcac49fcf18ae610a14d8ccdf5b`; pemeriksaan ekstensi staging menghasilkan `Required extensions loaded` (exit 0). Konfigurasi Apache aktif menghasilkan `Syntax OK` (exit 0), tetapi ini masih memakai PHP lama. Tidak ditemukan `composer.json` di Project-Opencode pada pemeriksaan ulang.
- **Blocker historis, sudah teratasi:** eksekusi `test-php-apache-pos.ps1` ditolak PowerShell (`PSSecurityException`, `UnauthorizedAccess`: running scripts is disabled). Pada pemeriksaan awal seluruh scope ExecutionPolicy bernilai Undefined dan belum ada aktivasi atau backup baru. User kemudian menyetujui izin sementara, lihat hasil lanjutan di bawah.
- **Rencana saat pemeriksaan awal, sudah dijalankan:** uji Apache staging; perluas gate aktivasi agar kegagalan pemeriksaan Apache ikut memulihkan runtime; aktifkan dengan backup; verifikasi CLI/Apache/Composer TLS; selaraskan target Laravel 13 pada CONTEXT/TRD. Smoke test memakai pemuatan DLL eksplisit, sehingga `httpd -t` dan `httpd -M` konfigurasi utama tetap wajib setelah aktivasi.
- **Sumber verifikasi:** [metadata resmi PHP Windows](https://downloads.php.net/~windows/releases/releases.json), [rilis Laravel 13](https://laravel.com/docs/13.x/releases) (PHP minimum 8.3; PHP 8.4 didukung).
- **Izin lanjutan:** user menyetujui izin PowerShell sementara. Skrip dijalankan dengan `-ExecutionPolicy Bypass` hanya untuk proses terkait; pemeriksaan setelah selesai menunjukkan semua scope tetap Undefined.
- **Hasil eksekusi lanjutan (Observed):** uji staging pertama gagal karena `extension_dir` menunjuk runtime aktif lama. Setelah path staging dibetulkan sementara, HTTP mengembalikan PHP 8.4.27, `apache2handler`, INI staging, seluruh ekstensi probe aktif, serta listener loopback terverifikasi (exit 0; artefak `C:\Users\user\AppData\Local\Temp\opencode\php-apache-check-8a805b4704974d80be3e4450b21d1608`). Path INI dikembalikan ke lokasi final sebelum aktivasi.
- **Kegagalan aktivasi yang dipertahankan:** kedua percobaan lolos CLI, ekstensi, `httpd -t`, pemuatan `php_module`, dan respons HTTP PHP 8.4.27 dengan seluruh ekstensi probe. Percobaan pertama gagal saat `Get-NetTCPConnection` tidak menemukan listener untuk PID tes; pendekatan alternatif memakai `netstat` juga gagal gate `Unexpected Apache listener`. Keduanya exit 1 dan rollback memulihkan PHP lama. Penyebab ketidaksesuaian pemeriksaan listener belum dipastikan; aktivasi tidak diulang lagi pada sesi ini. Artefak gagal: `php-apache-check-af11b4292e114799a66d72ce67afcd07` dan `php-apache-check-5b82ea8c1a1c49ff84b76df13434f244` di folder temporary OpenCode.
- **State pemulihan historis setelah percobaan kedua (Observed):** runtime baru sempat tersimpan di `C:\xampp\php-upgrade-backup-20261029-pos-retry1\failed-new-php`; konfigurasi asli tersimpan pada subfolder `apache-conf` di kedua folder backup. Saat itu runtime lama aktif kembali, bukan tersimpan di subfolder `php` backup. Tidak ada proses httpd terdeteksi setelah tes; port 18764 tidak tampil di hasil netstat. State akhir menggantikan state ini, lihat backup akhir di bawah.
- **Diagnosis akhir (Observed):** snapshot gagal `php-apache-check-d104c578541b483b92a55a7deee5302d/listeners.txt` menunjukkan endpoint `127.0.0.1:18764` milik Apache berlabel `FIN_WAIT_1`, bersamaan dengan koneksi HTTP aktif. Kegagalan gate bersumber dari ketergantungan pada label `LISTENING`; penyebab sistem operasi melaporkan state tersebut belum dipastikan. Gate diperbaiki untuk memeriksa seluruh endpoint TCP milik PID Apache, semuanya wajib `127.0.0.1:18764`, serta mencocokkan PID pada dua respons HTTP sebelum/sesudah pemeriksaan endpoint. Tiga uji berurutan lolos (exit 0), bukan sekadar menghapus assertion. Artefak: `php-apache-check-3ff034738a4d48029cb00563d6b1d155`, `php-apache-check-c1239d22f11046e5aefe62d893c50ea8`, `php-apache-check-6a46173b8c64482da21e88d32b73e8da` di temporary OpenCode.
- **Aktivasi akhir (Observed):** `activate-php-pos.ps1` exit 0; PHP CLI 8.4.27, ekstensi wajib termuat, konfigurasi utama Apache `Syntax OK`, `php_module (shared)` termuat. Uji HTTP terisolasi mengembalikan PID 4064, PHP 8.4.27, `apache2handler`, INI `C:\xampp\php\php.ini`, seluruh ekstensi probe aktif, endpoint hanya loopback. Artefak: `C:\Users\user\AppData\Local\Temp\opencode\php-apache-check-deae2527286746e18eba8c5cb416ac32`. `php --ini` mengonfirmasi INI aktif yang sama. Proses httpd tidak terdeteksi setelah tes; semua scope ExecutionPolicy tetap Undefined.
- **Backup akhir:** `C:\xampp\php-upgrade-backup-20261029-pos-final\php` menyimpan runtime lama; `apache-conf` menyimpan konfigurasi asli. Konfigurasi Apache utama tidak diubah. Restore memerlukan Apache/PHP berhenti, karantina runtime baru, lalu pindahkan folder PHP lama kembali ke `C:\xampp\php`; verifikasi CLI dan `httpd -t` sebelum digunakan.
- **Composer (Observed):** `php C:\ProgramData\ComposerSetup\bin\composer.phar diagnose` exit 0; platform, HTTP/HTTPS Packagist dan pemeriksaan GitHub lolos, memakai PHP aktif 8.4.27. Namun exit 0 tidak berarti audit hijau: Composer 2.9.5 melaporkan 8 advisori keamanan dan menyarankan 2.10.3. Pembaruan Composer belum dijalankan karena lingkup awal PHP/Laravel. Tindak lanjut: perbarui Composer dengan backup dan verifikasi audit ulang sebelum pemasangan dependency.
- **Batas verifikasi:** HTTP memakai konfigurasi uji loopback terpisah dengan pemuatan DLL eksplisit; konfigurasi utama hanya diuji sintaks/pemuatan modul, bukan seluruh aplikasi htdocs. Koneksi database dan kompatibilitas aplikasi lama belum diuji. Belum ada backend POS atau dependency Laravel untuk diuji. Target Laravel 13 diselaraskan di CONTEXT/TRD; persyaratan PHP pada metaprompt lama mengikuti keputusan CONTEXT yang lebih baru.
- **Review akhir:** review read-only tidak menemukan blocker aktif dalam lingkup ENV-01. Bukti JSON HTTP dan exit code tersedia di output sesi, tidak seluruhnya tersimpan di folder artefak tes. Keberadaan subfolder backup akhir `php` dan `apache-conf` diperiksa langsung; restore akhir tidak dijalankan ulang.
- **Tindak lanjut Composer, disetujui user 2026-10-29:** target pembaruan stable dengan backup bawaan `self-update`; kriteria uji: versi baru aktif, platform/HTTPS lolos, pemeriksaan advisori Composer tidak lagi melaporkan temuan. Rollback menggunakan `self-update --rollback` sesuai dokumentasi resmi.
- **Blocker Composer (Observed):** `php C:\ProgramData\ComposerSetup\bin\composer.phar self-update --stable --no-interaction --no-progress` mencoba memasang 2.10.3 tetapi exit 1: PHAR tidak dapat ditulis (`Permission denied`). ACL memberi Users hanya RX; Administrators/SYSTEM memiliki Full Control. Pemeriksaan ulang menunjukkan Composer tetap 2.9.5 dengan PHP 8.4.27. Channel pembaruan stable sempat tersimpan; penggantian PHAR belum berhasil. Perlu izin proses Administrator/UAC untuk perintah pembaruan tersebut; izin PowerShell sementara sebelumnya tidak memberi hak tulis administrator. Sumber: [self-update dan rollback resmi](https://getcomposer.org/doc/03-cli.md#self-update-selfupdate).
- **Penyelesaian Composer 2026-10-29 (Observed):** user memberikan izin Administrator sementara melalui UAC. Pemanggilan `Start-Process -Verb RunAs` untuk pembaruan menghasilkan error harness `Unknown: ChildProcess.kill`, sehingga exit code pembaruan tidak diperoleh dan perintah mutasi tidak diulang. Pemeriksaan langsung berikutnya mengonfirmasi Composer 2.10.3 aktif dengan PHP 8.4.27 (exit 0). `composer diagnose` selesai exit 0: versi, public keys, platform, Git, HTTP/HTTPS Packagist, akses GitHub, ruang disk, serta pemeriksaan kerentanan Composer dan dependensinya seluruhnya OK. Backup versi lama ditemukan di `C:\Users\user\AppData\Roaming\Composer\2026-01-29_11-40-53-2.9.5-old.phar`. Blocker Composer teratasi; rollback tidak dijalankan dan dependensi aplikasi POS belum dapat diaudit karena backend belum dibuat.

### DOC-01: Target deployment shared hosting (2026-11-01)
- **Permintaan:** user memilih shared hosting setelah penjelasan hosting biasa/cPanel; menggantikan target VPS.
- **Lingkup:** menyelaraskan keputusan deployment di CONTEXT dan TRD; tidak melakukan deployment.
- **Kriteria uji sebelum perubahan:** CONTEXT mencatat keputusan baru; TRD tidak lagi mewajibkan VPS/Nginx/PHP-FPM; penyedia, panel, dan kompatibilitas paket tidak dianggap sudah terverifikasi.
- **Batas:** penyedia/paket dan panel pengelolaan belum dipilih; kompatibilitas PHP, ekstensi, database, HTTPS, document root Laravel, dan kebutuhan proses latar belakang harus diperiksa sebelum deployment.

### DOC-02: Kembali ke target deployment VPS (2026-11-01)
- **Permintaan:** user membatalkan pilihan shared hosting pada DOC-01 dan memilih membeli VPS kemudian.
- **Lingkup:** menyelaraskan CONTEXT dan TRD kembali ke VPS (Nginx + PHP-FPM, HTTPS); tidak melakukan pembelian atau deployment.
- **Kriteria uji sebelum perubahan:** keputusan aktif di CONTEXT dan TRD memakai VPS; shared hosting hanya disebut sebagai keputusan yang dibatalkan; penyedia/paket tetap belum dipilih.
- **Batas:** VPS belum dibeli; spesifikasi, penyedia, dan konfigurasi produksi belum diverifikasi. DOC-01 dipertahankan sebagai riwayat keputusan yang dibatalkan.

### DOC-03: React Aria sebagai referensi utama komponen UI (2026-11-02)
- **Permintaan:** tambahkan https://react-aria.adobe.com/ ke stack sebagai referensi utama komponen UI.
- **Lingkup:** catat keputusan di CONTEXT dan tautkan dari stack TRD serta referensi DBD.
- **Kriteria uji sebelum perubahan:** React Aria tercatat sebagai referensi utama perilaku dan aksesibilitas komponen; token visual tetap bersumber dari DESIGN_POS_Extend; status referensi dibedakan dari pemasangan dependency atau migrasi komponen.
- **Cara verifikasi:** baca dokumentasi resmi melalui Context7, lalu baca ulang bagian dokumen yang diubah dan periksa konsistensi tautan serta batas penerapannya.
- **Status (Observed):** CONTEXT §3.1/§8, TRD §1, dan DBD §2 diperbarui; pencarian ulang mengonfirmasi referensi serta batas penerapannya konsisten. Dokumentasi resmi React Aria melalui Context7 mengonfirmasi komponen tanpa gaya bawaan dan dukungan styling Tailwind. Tidak ada paket dipasang atau kode UI diubah; kompatibilitas runtime belum diuji.

Salin blok ini untuk tiap irisan. Satu irisan = satu perilaku yang bisa diuji sendiri,
selesai dalam satu sesi.

### FS-01: ISI: nama
- **Perilaku:** ISI:
- **Dokumen rujukan:** PRD ISI: · AFD ISI: · TRD ISI: · BSD ISI: · DBD ISI:
- **File terkait:** ISI:
- **Batasan:** ISI:
- **Cara uji (ditulis sebelum eksekusi):**
  - [ ] ISI:
- **Kriteria selesai:**
  - [ ] ISI:
- **Sengaja ditunda:** ISI:
- **Butuh persetujuan user:** ISI: (hapus data, deploy, dll.)

## 3. Risiko dan mitigasi
| Risiko | Mitigasi | Diuji di fase |
|---|---|---|
| Sinkronisasi offline (konflik dua perangkat) | ISI: | |

## 4. Log keputusan dan pelajaran
Kegagalan yang berulang dipindahkan menjadi aturan permanen di `AGENTS.md`.
| Tanggal | Keputusan / kegagalan | Tindak lanjut |
|---|---|---|
| ISI: | | |

## 5. Berkas terkait
- PRD: `../PRD/prd.md` · AFD: `../AFD/afd.md` · TRD: `../TRD/trd.md`
- BSD: `../BSD/bsd.md` · DBD: `../DBD/dbd.md`
