# Prototype FigCraft POS Bengkel

File utama: [pos-kasir.figcraft](pos-kasir.figcraft). **Cukup buka satu file ini.**
Halaman Desktop, Ponsel, Referensi dan Komponen berada di dalam dokumen yang sama.
Dua gambar acuan tertanam di file; seluruh layar kerja memakai layer native editable.
Backup sebelum pelengkapan ada di `archive/before-cashier-finish.zip`.
Backup sebelum penambahan Registrasi ada di `archive/before-registration.zip`.
Backup sebelum Diagnosa & Estimasi ada di `archive/before-diagnosis.zip`.
Backup sebelum pengerjaan SO ada di `archive/before-service-order.zip`.
Backup sebelum penyambungan invoice Maya ada di `archive/before-maya-invoice.zip`.
Backup sebelum pelanggan/riwayat ada di `archive/before-customer-history.zip`.

## Mencoba pelanggan, kendaraan dan riwayat

Jalankan flow **Pelanggan dan Riwayat / Desktop / Demo** atau versi **Ponsel**.
Menu **Riwayat kunjungan** pada POS Maya juga membuka riwayat lintas kunjungan
tanpa mengulang nominal atau status invoice yang sudah dijalankan.

1. **Buka pelanggan** menampilkan Maya (`DEMO-C0147`) dan Arif (`DEMO-C0150`).
   Keduanya memakai nomor contoh yang sama pada awal demo. Pencarian telepon
   menampilkan dua profil saat keduanya cocok; identitas/riwayat tetap terpisah.
2. Pada profil Maya, **Ubah telepon master** mencoba nomor baru atau validasi
   kosong. Snapshot telepon pada kunjungan lama tetap `0812 0000 0147`.
3. **Buka kendaraan** mengarah pada `DEMO-V0147`. Plat tampilan memakai spasi;
   kunci pencocokan kapital tanpa spasi ditampilkan terpisah. Contoh pencarian
   `dd 1248 kl` memakai kendaraan existing, bukan membuat kendaraan kedua.
4. Melalui **Demo: sebagai Owner**, ubah plat menjadi `DD 2248 KL`. Alasan wajib;
   contoh `B 1234 ABC` ditolak karena sudah digunakan. ID kendaraan tetap sama,
   sementara dokumen lama tetap menampilkan `DD 1248 KL`. Riwayat perubahan lengkap
   tersedia pada contoh Owner. Pencarian otomatis memakai plat historis belum dibuat.
5. **Riwayat kendaraan** memuat kunjungan lama 0140, layanan Maya 0147, dan
   registrasi tambahan 0150 bila sudah disimpan. **Riwayat pelanggan** memfilter
   berdasarkan ID pelanggan; kunjungan Arif tidak dimasukkan ke riwayat Maya.
6. Kunjungan 0140 adalah fixture historis tambahan bertanda data contoh: diagnosa,
   SO, invoice dan nota Rp150.000 hanya dibaca. Kunjungan 0147 membuka dokumen yang
   tersedia pada konteks layanan/invoice existing; invoice mengikuti nominal serta
   status sebenarnya pada preview. Teknisi membaca invoice tanpa kontrol pembayaran.
7. **Registrasi kunjungan baru** meminta pemilihan pelanggan secara eksplisit.
   Isi keluhan, periksa, lalu simpan `REG-DEMO-0150`. Kendaraan yang sama dapat
   dibawa Arif. Registrasi baru menyimpan snapshot sendiri dan belum memiliki
   diagnosa/SO/invoice; tombolnya tidak diarahkan ke dokumen 0147.
8. Nonaktifkan lalu aktifkan kembali contoh master Maya atau kendaraan. Riwayat
   tetap terbuka; master nonaktif tidak dapat dipilih untuk kunjungan baru.
   Skenario offline/gagal pada Demo berlaku untuk simpan registrasi tambahan.

Gunakan **Demo: layanan Maya 0147** untuk berpindah ke demo SO/invoice tanpa
mereset master pelanggan, plat atau registrasi tambahan. **POS Kasir** tersedia
di sidebar desktop; tombol **Kembali ke POS** ada pada Demo kedua perangkat.
Teknisi tidak menggunakan tujuan POS pembayaran.

Data historis 0140 dan profil Arif adalah fixture desain, bukan pembacaan
database. Perubahan master berfokus pada contoh telepon dan satu perubahan plat.
Pencarian/isian masih berupa contoh, bukan pengetikan bebas. Satu registrasi
tambahan per reset demo bukan batas produksi. Reset pelanggan/riwayat tidak
menghapus atau mengulang state layanan/invoice Maya.

Irisan ini teruji dalam satu run lengkap: 312 langkah desktop/ponsel dan 38
pemeriksaan nilai runtime, ditambah enam kontrol nonaktif dan 98 pemeriksaan
regresi pilihan jalur lama. Tema Light/Dark, gulir ponsel dan pembukaan ulang
file diperiksa terpisah. Tab, screen reader dan reflow menyeluruh belum diuji.
Bukti: [playback](evidence/customer-history-verification.json),
[regresi](evidence/customer-history-regression.json),
[file dan tampilan](evidence/customer-history-delivery.json), serta
[preservasi perubahan lama](evidence/customer-history-preservation.json).


## Mencoba alur Maya sampai nota

Alur utama desktop/ponsel teruji pada `evidence/maya-invoice-verification.json`.
Pemeriksaan memakai checkpoint yang dilanjutkan setelah koneksi ke jendela
FigCraft pulih. `maya-invoice-delivery.json` merekam file gabungan terakhir;
`maya-invoice-preparation.json` adalah snapshot persiapan sebelum pemeriksaan akhir.

Jalankan flow **Maya / Desktop / Registrasi sampai nota** atau versi **Ponsel**.
Pilih **Mulai dari registrasi Maya** untuk mengulang data contoh pada preview.

1. Isi contoh registrasi, periksa dan simpan. **Buka Diagnosa**, lalu beralih
   melalui **Demo: journey Teknisi**. Buat pemeriksaan dan tambahkan jasa
   Pemeriksaan AC serta part Filter kabin. Setujui estimasi Rp150.000 dengan
   **Setuju**, lalu buat Service Order.
2. **Kelola Service Order**, buka SO, pilih Teknisi dan mulai pengerjaan.
   Salin estimasi ke realisasi untuk diperiksa. Contoh harga jasa Rp60.000
   menghasilkan total Rp160.000; isi alasan dan catat persetujuan tambahan.
3. Simpan realisasi, tandai selesai, lalu serahkan ke kasir. Tombol
   **Demo: buka POS sebagai Kasir** beralih peran secara eksplisit dan membawa
   realisasi yang diserahkan. Owner memakai **Buka POS sebagai Owner**.
4. Pilih kartu Maya untuk melihat rincian. **Buat invoice draf** adalah tindakan
   terpisah; membuka kembali transaksi memakai draf yang sama. Tinjau dan
   **Terbitkan invoice** sebelum menerima pembayaran. Invoice terbit mengunci SO.
5. Tunai memakai contoh Rp100.000/Rp200.000, menolak kekurangan dan menghitung
   kembalian. QRIS meminta pemeriksaan dana; transfer meminta referensi contoh
   dan pemeriksaan dana. Mengganti metode mengosongkan pemeriksaan sebelumnya.
   QRIS dan rekening asli belum diberikan; tidak ada aset/nomor bank buatan.
6. Konfirmasi menampilkan Lunas, lalu buka **Lihat nota**. Transaksi keluar dari
   antrean dan tetap dapat dibuka melalui **Riwayat kunjungan**. Rincian dan
   nominal invoice, pembayaran dan nota mempertahankan snapshot kunjungan Maya.

Kartu, invoice dan nota mengikuti nominal realisasi, termasuk contoh Rp150.000,
Rp160.000, serta pelepasan part menjadi Rp60.000/Rp50.000. Part belum dipakai
ditandai tidak dipakai dan tidak ditagihkan. Estimasi awal tetap Rp150.000.
Pilihan **Demo: SO Selesai Rp0 (ulang data)** menunjukkan invoice langsung Lunas
tanpa transaksi pembayaran. Demo ini mengganti konteks, bukan revisi otomatis.

Penyerahan yang ditarik membuat draf tidak dapat diterbitkan, termasuk setelah
diserahkan kembali dengan nominal sama; snapshot lama dipertahankan untuk
pemeriksaan Owner. Editor koreksi harga/rebase lengkap
belum dibuat. Offline, simpan gagal dan hasil pembayaran belum pasti tidak
mengklaim Lunas. Pemeriksaan status pada skenario belum pasti menampilkan contoh
belum tercatat, kemudian meminta pemeriksaan pembayaran kembali.

Ini simulasi berurutan dalam satu preview, bukan sinkronisasi database atau
antarsesi. Pelanggan dan riwayat lintas kunjungan contoh mengikuti bagian
pelanggan/riwayat di atas; pencarian database seluruh pelanggan belum dibuat. Cetak/PDF berupa pratinjau
nota putih; dialog cetak, ekspor PDF aplikasi dan printer fisik belum dihubungkan.
Pengeluaran stok nyata tidak dijalankan. Contoh kasir Rina tetap tersedia sebagai
skenario lama yang terpisah.

## Mencoba Service Order

Dari salinan awal SO pada journey Diagnosa dua item Rp150.000, pilih **Kelola
Service Order**, lalu **Buka SO**. Alternatifnya, jalankan flow **Service Order /
Desktop / Demo** atau **Service Order / Ponsel / Demo** dan pilih **Mulai SO baru**.
Fixture yang dikelola adalah Maya / DD 1248 KL / SO-DEMO-0147. Alternatif estimasi
satu item dan harga lokal pada modul Diagnosa tetap merupakan skenario terpisah.

1. **Pilih Teknisi**: A saja, B saja, atau keduanya. Semua setara; **Mulai
   pengerjaan** belum aktif sebelum penugasan tersimpan.
2. **Mulai pengerjaan**, lalu konfirmasi. Penundaan meminta alasan; melanjutkan
   mempertahankan penugasan dan realisasi pada journey SO yang sama.
3. **Realisasi jasa / part → Salin estimasi untuk diperiksa** menyiapkan isian
   contoh. Salinan ini belum menjadi realisasi tersimpan. Isi alasan contoh,
   lalu **Periksa dan simpan** untuk mencatat Rp150.000 dalam simulasi.
4. Coba harga jasa Rp60.000. Total menjadi Rp160.000; isi alasan dan pilih
   **Setuju** setelah pelanggan menyetujui biaya tambahan, lalu simpan. Qty
   0,5 pcs ditolak; memperbaiki qty atau mengubah rincian membatalkan centang lama.
5. Contoh **Lepas part** berlaku pada part yang belum dipakai. Kenaikan per
   baris tetap meminta Setuju walaupun total turun setelah part dilepas. Estimasi
   acuan tetap Rp150.000 dan harga katalog tidak ditulis ulang.
6. **Tandai selesai** mengunci revisi bagi Teknisi. **Serahkan ke kasir** perlu
   realisasi tersimpan. Ini mengunci biaya/progres, belum membuat invoice atau
   menerima pembayaran. SO Dibatalkan berbiaya hanya diserahkan Owner;
   pembatalan tanpa biaya tidak ditagihkan.
7. Pada antrean, **Demo: lanjut sebagai Owner** mempertahankan konteks. Owner
   menarik dengan alasan sebelum revisi; penarikan tidak otomatis membuka
   progres atau menyerahkan ulang. Buka kembali SO Selesai memerlukan alasan.
   Invoice final tetap mengunci SO; SO Dibatalkan tidak dibuka kembali.
8. **Demo** menyediakan baca Kasir, Owner, kondisi tanpa realisasi, pembatalan
   tanpa biaya, invoice final, offline, konflik versi dan kegagalan simpan.
   Pilihan skenario Demo memulai ulang datanya; tindakan biasa di journey SO
   mempertahankan pilihan Teknisi dan nominal sampai preview dimulai ulang.

Realisasi dibatasi contoh dua item, harga Rp50.000/Rp60.000 dan pelepasan part;
belum menerima ketikan bebas atau semua kombinasi katalog. Riwayat yang ditampilkan
adalah contoh, bukan audit server. Stok contoh 16 tercatat, 3 reservasi dan 1 rusak
menghasilkan 12 tersedia; prototype tidak melakukan alokasi stok nyata.

Data SO memakai mode native per field karena aksi setVariable yang diterima
engine tidak mempertahankan nilai pada uji runtime sesi ini. Peta aktif ada di
`evidence/service-order-map.json`. Pilihan berjalan dalam satu preview, bukan
penyimpanan produksi atau sinkronisasi seluruh modul. Journey invoice Maya kini
diteruskan melalui tombol POS pada antrean SO, dengan contoh kasir Rina tetap terpisah.

## Mencoba Diagnosa & Estimasi

Dari detail registrasi Maya / DD 1248 KL, pilih **Buka Diagnosa**. Peran tetap
Kasir dan tidak dapat membuat dokumen. Gunakan **Demo: journey Teknisi** untuk
beralih secara eksplisit ke contoh editor. Alternatifnya, jalankan flow
**Diagnosa / Desktop / Teknisi / REG-DEMO-0147** atau versi **Ponsel**.

1. Pilih **Buat diagnosa**. Draf parsial boleh disimpan tanpa persetujuan.
   **Demo: isi pemeriksaan** mengisi contoh temuan dan rekomendasi; identitas
   serta keluhan kunjungan mengambil snapshot Registrasi.
2. Pilih jasa **Pemeriksaan AC** (Rp50.000), lalu part **Filter kabin**
   (Rp100.000). Total contoh dua item Rp150.000. Satu jasa saja juga memiliki
   jalur persetujuan dan salinan SO dengan total Rp50.000.
3. Contoh penghapusan part mempertahankan jasa. Klik kolom jumlah part untuk
   mencoba 0,5 pcs yang tidak valid, lalu **Gunakan qty 1 pcs** untuk memperbaiki.
4. Klik harga jasa untuk mencoba harga lokal Rp45.000. Isi alasan melalui tombol
   demo, lalu tinjau estimasi Rp145.000. Harga katalog tetap Rp50.000. Ini contoh
   perubahan lokal, bukan aturan diskon atau batas persetujuan nominal.
5. **Tinjau dan catat persetujuan**, pilih **Setuju** setelah persetujuan lisan, lalu
   **Catat persetujuan**. Konfirmasi belum aktif sebelum ditandai. Sukses
   mengunci estimasi disetujui dan mempertahankan nominal skenario yang dipilih.
6. **Buat Service Order** membuka tinjauan penyalinan; konfirmasi membuat contoh
   SO-DEMO-0147 berstatus **Belum dimulai**. Buka estimasi acuan lalu **Lihat
   Service Order** untuk kembali pada SO yang sama. Pengelolaan penugasan,
   pengerjaan serta realisasi kini dilanjutkan melalui **Kelola Service Order**
   pada fixture dua item Rp150.000. Reservasi nyata tetap belum diintegrasikan.
7. **Demo** menyediakan tampilan baca Kasir, log harga Owner, draf offline,
   konflik versi, gagal simpan/approval, kosong/pencarian/gagal muat dan hitung
   pecahan. Log harga lengkap ditampilkan pada journey Owner, bukan editor Teknisi.
8. Contoh pecahan terpisah: 0,500 kg × Rp200.001 = Rp100.000,50, dibulatkan
   Rp100.001 per baris. Contoh ini tidak ditambahkan ke estimasi dua item.

Label Draf/Disetujui mengikuti demo existing; daftar status pemeriksaan produksi
lengkap belum ditetapkan. Editor yang disimulasikan adalah Teknisi; Kasir hanya
membaca dan Owner memiliki contoh log harga. Ini bukan autentikasi atau otorisasi
server. Persetujuan lisan, penyimpanan, penyalinan SO dan perubahan input adalah
perpindahan state contoh. State antarmodul belum disinkronkan secara global.

## Mencoba Registrasi

Di preview kasir, pilih menu **Registrasi**, atau pilih flow **Registrasi /
Desktop / Demo kunjungan** maupun **Registrasi / Ponsel / Demo kunjungan**.
Kedua modul tetap berada dalam file utama yang sama.

1. Pilih **Registrasi baru**, lalu **Periksa registrasi** untuk melihat validasi
   empat isian wajib. Alamat boleh dikosongkan.
2. Gunakan **Demo → Isian contoh lengkap**, atau tombol **Demo: isi contoh
   lengkap** di bawah form kosong. Contoh memakai Maya Lestari / DD 1248 KL.
3. Pilih **Periksa registrasi → Simpan registrasi**. State menyimpan kemudian
   membuka detail REG-DEMO-0147; kembali ke daftar menampilkan kunjungan tersebut.
4. **Koreksi registrasi** membuka contoh perubahan keluhan sebelum SO dibuat.
   Simpan koreksi untuk melihat riwayat nilai sebelum/sesudah.
5. Coba **Demo → Plat sudah terdaftar**. Maya datang membawa B 1234 ABC;
   kendaraan yang sama dipakai ulang dan kunjungan baru menjadi REG-DEMO-0148.
   Telepon contoh sama dengan Rina, tetapi pelanggan tetap memiliki ID berbeda.
6. Detail kunjungan Rina yang telah memiliki SO-0261 menampilkan koreksi nonaktif.
   Koreksi setelah SO dibuat memerlukan Owner dan alasan.
7. **Demo** juga menyediakan daftar kosong, pencarian tanpa hasil, gagal memuat,
   offline dan gagal simpan. State gagal tidak menyatakan registrasi tersimpan.
8. **Batal/Escape** pada form terisi meminta konfirmasi. Melanjutkan isian
   mengembalikan form asal, termasuk skenario kendaraan lama atau koreksi.

Seluruh isian tetap memakai state contoh yang telah disiapkan. Form tidak
menerima ketikan bebas atau menyimpan data nyata. Registrasi sendiri tidak
membuat diagnosa, Service Order maupun tagihan. Journey Registrasi menampilkan Kasir.

## Mencoba Kasir

1. Buka halaman **Desktop** atau **Ponsel**, pilih flow **Kasir / Desktop / Demo
   SO-0261** atau **Kasir / Ponsel / Demo SO-0261**, lalu jalankan Preview/Present.
2. Pilih **B 1234 ABC / Rina Prasetyo / SO-0261**, periksa rincian, buat invoice
   draf, kemudian terbitkan invoice. Total contoh Rp235.000.
3. **Tunai:** nominal contoh Rp250.000, kembalian Rp15.000. Klik nominal untuk
   mencoba Rp200.000; konfirmasi nominal kurang tidak menuju nota Lunas.
4. **QRIS:** centang pemeriksaan dana masuk, kemudian konfirmasi. **Transfer
   manual:** klik referensi untuk mengisi `TRF-DEMO-0144`, centang pemeriksaan
   mutasi, lalu konfirmasi. QRIS/rekening asli belum diberikan dan tidak direka.
5. Pada nota Lunas, **Cetak nota** membuka pratinjau sesuai metode pembayaran.
   Tutup pratinjau kembali ke nota yang sama. Ini simulasi tampilan kertas,
   belum mengirim perintah ke printer.
6. Tombol **Demo** di header membuka pilihan antrean kosong, hasil pencarian
   kosong, loading, gagal memuat, offline, draf Perlu Owner, invoice Rp0, dan
   pencatatan pembayaran yang perlu diperiksa.
7. **Tema** mengganti Light/Dark selama preview. Tekan **Escape** untuk kembali
   ke antrean. Gulir layar ponsel jika kontrol berada di bawah viewport.

Invoice Rp0 memakai contoh terpisah **Nadia Putri / SO-0267 / INV-0145**. Penerbitan
langsung menuju Lunas tanpa penerimaan uang atau transaksi pembayaran Rp0.
State offline dan draf Perlu Owner tidak menyediakan konfirmasi aktif.
Skenario pencatatan gagal meminta pemeriksaan status sebelum mencoba lagi.

## Isi dan bukti

- 360 frame: 58 kasir, 48 Registrasi, 104 Diagnosa & Estimasi, 92 pengerjaan SO,
  dan 58 penghubung invoice/pembayaran/nota Maya.
- 236 tautan kasir dan 285 tautan tambahan Registrasi/menu penghubung, ditambah
  timer, kontrol tema, Escape, dan interaksi komponen. Peta kasir ada di
  `evidence/design-completion-map.json`; Registrasi di `evidence/registration-map.json`.
- 552 tautan tambahan Diagnosa & Estimasi/menu penghubung, termasuk jalur satu
  item, harga lokal dan salinan SO. Peta ada di `evidence/diagnosis-map.json`.
- Pengerjaan SO menambah 534 kontrol navigasi/aksi bersyarat, dengan state contoh
  yang dibawa melalui mode native. Verifikasi SO memakai perjalanan berurutan,
  bukan mengklik setiap aksi tanpa konteks status dan peran.
- Integrasi invoice Maya memakai 26 field mode native dengan snapshot invoice
  terpisah dari SO. Peta aksi ada di `evidence/maya-invoice-map.json`; hasil
  playback dan predikat runtime pada `maya-invoice-verification.json` dan
  `maya-invoice-playback.json`. Bukti file gabungan terbaru ada di
  `maya-invoice-delivery.json` dan `maya-invoice-file-info.json`.
  `maya-invoice-model-checks.json` memuat 18 pemeriksaan cabang
  engine dengan mode dokumen eksplisit; ini bukan playback GUI.
  `maya-invoice-withdrawal.json` memeriksa draf yang ditarik lalu diserahkan ulang,
  reset contoh dan penguncian final.
  Catatan perbaikan helper
  serta pelanjutan checkpoint ada di `maya-invoice-test-observations.json`.
- 23 variabel warna native dengan mode Light/Dark; lima text style Poppins.
  Tiga set komponen reusable menyediakan Default, Hover, Pressed, Focus, Disabled;
  empat komponen awal tetap dipertahankan. Jumlah instance akhir dicatat pada
  `evidence/maya-invoice-delivery.json`.
- 25 label kecil dinaikkan minimal 12 px; delapan tautan kembali ponsel diperbaiki
  karena koordinat lama berada di atas layar. Hover/tekan diterapkan pada kontrol
  navigasi demo dan area interaksi alur kasir.
- `evidence/completion-verification.json`: hasil playback, tema, loading, guard dan
  missing-font. `evidence/completed-playback.json`: hasil setiap tautan yang diuji.
- `evidence/registration-verification.json` dan `registration-playback.json`:
  pemeriksaan tambahan Registrasi, identitas, pembatasan akses dan pembatalan.
  `registration-delivery.json` serta `registration-file-info.json` merekam snapshot
  irisan Registrasi; laporan pelengkapan kasir sebelumnya menjadi riwayat.
- `evidence/diagnosis-verification.json` dan `diagnosis-playback.json`: guard,
  identitas/nominal, klik tautan, timer, tema, pembatalan dan regresi jalur lama.
  `diagnosis-delivery.json` dan `diagnosis-file-info.json` merekam snapshot Diagnosa.
- `evidence/service-order-verification.json` serta `service-order-playback.json`
  memuat hasil journey SO dan guard. `service-order-delivery.json` dan
  `service-order-file-info.json` merekam snapshot sebelum integrasi invoice Maya.
  Ada 228 langkah journey SO, 18 pemeriksaan rute penyelesaian sesuai peran,
  dan 80 pemeriksaan pilihan jalur modul sebelumnya pada `service-order-regression.json`.
- `sources/` menyimpan acuan; `generated/` menyimpan hasil generasi awal; `tools/`
  berisi helper native dan pemeriksaan; `evidence/` berisi inspeksi serta render.

## Batas prototype

Input, pencarian, filter dan checkbox belum terhubung ke data nyata. Jalur input
yang aktif menggunakan state contoh, bukan ketikan bebas. Skenario tambahan
dibuka melalui Demo; SO-0261 dan SO-DEMO-0147/Maya memiliki alur pembayaran contoh.
Kartu lain menjadi contoh visual. Tema mengikuti preview, bukan preferensi tersimpan.
State kunjungan belum disinkronkan secara global ketika berpindah antarmodul;
daftar setelah simpan/koreksi tersedia pada alur contoh masing-masing.

Focus tersedia sebagai varian desain; navigasi Tab, pembacaan screen reader dan
reflow otomatis belum diverifikasi. Pada presenter terpasang, state tekan kembali
normal saat pointer keluar; perubahan varian pada mouse-up dihindari karena
menghalangi klik. Nota cetak tetap putih pada tema gelap.

Journey lengkap Owner/Teknisi, katalog realisasi bebas, stok, laporan, koreksi
invoice Owner dan riwayat database seluruh pelanggan belum dibangun. Modul
pelanggan/riwayat di atas memakai fixture contoh yang terbatas.
Tidak ada pembayaran nyata, gateway, penyimpanan, integrasi backend atau
dukungan printer fisik. Prototype browser di folder induk tidak diubah.

## Melanjutkan edit live

Control API FigCraft saat pengerjaan memakai loopback port 7980 dengan izin tulis
di folder ini. Periksa koneksi lagi bila aplikasi ditutup. `tools/native_api.py`
adalah helper koneksi; `tools/verify_completed_cashier.py` dan
`tools/verify_registration.py` memeriksa dokumen aktif tanpa membangun ulang layar.
`tools/verify_diagnosis.py` memeriksa irisan Diagnosa & Estimasi dan regresi
pilihan jalur Registrasi/kasir.
`tools/verify_service_order.py` memeriksa journey SO beserta perubahan konteks.
`tools/verify_maya_invoice.py` memeriksa perjalanan Maya sampai nota dan predikat
nilai di runtime. Hotspot uji dipasang sebelum preview dan dihapus sebelum file
disimpan; perubahan interaksi di tengah perjalanan dapat mengulang state preview.
`tools/verify_customer_history.py` memeriksa master, snapshot kunjungan, batas
peran, registrasi tambahan dan integrasi invoice existing pada desktop/ponsel.
`tools/deliver_customer_history.py` memeriksa tema, gulir, render, font, integritas
file dan pembukaan ulang setelah pengujian selesai.
`activate_service_order_modes.py` adalah migrasi satu kali untuk runtime yang
diamati; jangan menjalankan ulang script konstruksi pada file yang sudah diedit.
Script konstruksi dan migrasi hanya
untuk riwayat; jangan menjalankannya kembali di atas perubahan manual.
`verify_playback.py` lama mengatur ulang fill statis: gunakan pemeriksaan baru.

Token tetap bersumber pada [DESIGN_POS_Extend.md](../../doc/DBD/DESIGN_POS_Extend.md),
aturan bisnis pada [CONTEXT.md](../../doc/CONTEXT.md). Bukti file lama adalah riwayat;
laporan `maya-invoice-*` menjelaskan irisan dan file gabungan terakhir.
Jendela FigCraft perlu terlihat untuk screenshot dan input. Bila preview tidak
memiliki nama/geometri, pulihkan jendelanya sebelum melanjutkan playback.
