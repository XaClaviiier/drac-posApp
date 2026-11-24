# CONTEXT: POS Bengkel AC Mobil

Letak file: `POS/doc/CONTEXT.md`. Dibaca agent sebelum mengerjakan task apa pun di
project ini (lihat tabel routing di `POS/AGENTS.md`).

Aturan pakai:
- Isi di sini adalah keputusan user. Agent mengikutinya dan tidak mengubahnya
  sendiri.
- **[ASUMSI]** belum dipastikan; agent boleh mempertanyakannya.
- **[REKOMENDASI]** usulan agent yang belum disetujui user; jangan diperlakukan
  sebagai keputusan final sampai statusnya berubah.
- `ISI:` berarti belum diputuskan. Agent tidak boleh mengarang isinya; ia
  bertanya bila bagian itu menentukan hasil.
- Jaga file ini tetap pendek. Detail panjang taruh di file lain dan tautkan
  dari sini.

---

## 1. Ringkasan

Aplikasi manajemen bengkel AC mobil: mencatat kendaraan yang masuk, diagnosa
awal, pekerjaan (jasa dan suku cadang), sampai nota dan pembayaran. Dipakai
oleh orang awam, jadi kemudahan baca dan pakai lebih penting daripada gaya.

Nama bengkel / nama aplikasi: ISI:
Logo: ISI:

Repositori pengembangan **[DIPUTUSKAN 2026-11-24]**:
https://github.com/XaClaviiier/drac-posApp. User memilih seluruh proyek:
`application/`, `doc/` dan `prototype/` dalam satu repositori. Aplikasi aktif
tetap pada `application/`; riwayat remote dipertahankan tanpa force-push.
Kredensial, file `.env`, database/runtime lokal dan dependency tidak diunggah.

---

## 2. Pengguna dan situasi pakai

| Hal | Keputusan |
|---|---|
| Pengguna utama | Kasir/admin dan pemilik. Keduanya memakai aplikasi. |
| Kemahiran | Cukup terbiasa dengan aplikasi, tetapi semua pengguna orang awam (bukan teknis). |
| Lokasi pakai | Berpindah-pindah dan tidak menentu; tidak terikat satu meja. |
| Kepadatan | Kadang ramai, kebanyakan santai. |
| Mekanik memakai aplikasi? | Ya. Sejak 2026-10-31 peran bernama **Teknisi** (dulu Mekanik); rincian hak akses di §2.1. |
| Jumlah pengguna / cabang | ISI: |

Yang menentukan desain: karena dipakai sambil berpindah dan oleh orang awam,
target sentuh harus besar, teks mudah dibaca, dan satu layar mengerjakan satu
hal. Karena kadang ramai, alur penerimaan kendaraan tidak boleh panjang.

### 2.1 Peran dan akses finansial **[DIPUTUSKAN 2026-10-31]** (menimpa kebijakan peran 2026-10-14)

Sumber: keputusan user di `POS-handoff-login-role-global-search.md` §4.

- Peran tepat **Owner, Teknisi, Kasir**. Supervisor dihapus; Mekanik diganti nama
  menjadi Teknisi. Tugas operasional Supervisor pindah ke Teknisi **dengan batasan
  finansial di bawah**, tidak diwarisi utuh. Sisi "admin" pada audit log = Owner,
  bukan peran keempat.
- Satu cabang saja. Multi-cabang kemungkinan masa depan, di luar cakupan sekarang.
- Login: username + password; prototype menyediakan journey demo per peran.
- HPP/harga beli dan pengeluaran terbatas: **hanya Owner**. Teknisi boleh melihat
  harga jual untuk pelanggan di WO dan invoice.
- Terima/konfirmasi pembayaran: **hanya Kasir dan Owner**.
- Teknisi boleh mengubah harga jual **lokal per dokumen** pada baris WO yang diizinkan;
  hak harga invoice draf kini mengikuti §2.7, menggantikan izin lama Teknisi.
  hanya berlaku untuk baris dokumen itu, tidak mengubah harga master; baris baru
  mulai dari snapshot harga master. Setiap perubahan harga dicatat (lama, baru,
  aktor, waktu, dokumen/baris, alasan); log lengkap hanya Owner.
- Invoice yang sudah final (termasuk yang belum lunas) terkunci; **hanya Owner yang
  mengoreksi**. Koreksi tidak menulis ulang uang yang sudah diterima: penurunan
  total dapat menimbulkan kelebihan bayar, kenaikan menimbulkan sisa tagihan;
  refund nyata adalah pergerakan uang terpisah yang dicatat, tidak otomatis.
- Estimasi dan realisasi mengikuti keputusan terbaru pada §2.2; penempatan estimasi
  di WO pada keputusan 2026-10-31 digantikan oleh form Diagnosa & Estimasi.
- Pencarian sidebar = **pencarian global** (halaman, pelanggan/kendaraan, WO,
  invoice, jasa/part), difilter peran; nominal terbatas tidak boleh bocor lewat
  snippet/hasil. Referensi visual disetujui user: `@shadcnuikit/command1`.
- Animasi hover untuk **semua kontrol interaktif yang enabled** (setara focus dan
  pressed disertakan; perangkat sentuh tidak bergantung hover). Invoice cetak tetap
  statis.
- **Belum diputuskan, jangan dikarang:** batas rentang edit harga/approval,
  persentase diskon, modul lain yang
  butuh entry harga, workflow refund dan perlakuan akuntansi koreksi.

### 2.2 Alur layanan terbaru [DIPUTUSKAN 2026-11-04]

Keputusan percakapan user menggantikan bagian alur/status/metode pembayaran lama
yang bertentangan. Service Order (SO) dan Work Order (WO) adalah dokumen pekerjaan
yang sama; istilah aktif untuk prototype baru adalah Service Order.

- Registrasi dilakukan Teknisi/Kasir (Owner memiliki akses semua fitur): nomor
  plat, nama pelanggan, keluhan awal, dan nomor telepon wajib; alamat opsional.
- Dari registrasi, Teknisi membuat Diagnosa & Estimasi: hasil pemeriksaan,
  rekomendasi tindakan, jasa/part, qty, harga satuan, subtotal dan total estimasi.
- Pelanggan menyetujui secara lisan; Teknisi kemudian melanjutkan ke SO. Rincian
  disalin tanpa entry ulang; estimasi yang disetujui tetap menjadi acuan.
- Perubahan jasa/part dan realisasi dicatat di SO dengan jejak perubahan, bukan
  menimpa estimasi awal. Tambahan biaya memerlukan persetujuan pelanggan; tidak
  ada batas nominal otomatis.
- SO dapat Dalam Pengerjaan, Ditunda, Selesai, atau Dibatalkan. Status awal dan
  rincian transisi diagnosa belum difinalkan. Hak revisi dan penguncian SO mengikuti
  §2.3. Invoice final tetap mengikuti aturan koreksi pada §2.1.
- Pembatalan sisa pekerjaan tidak menghapus biaya yang sudah timbul. SO disesuaikan
  sesuai realisasi, kemudian tetap diterbitkan invoice bila ada biaya. Pelanggan
  kembali setelah pembatalan memakai SO baru yang terhubung ke riwayat sebelumnya.
- SO Selesai masuk antrean kasir; SO Dibatalkan dengan biaya juga dapat ditagihkan
  setelah realisasi akhir ditetapkan. Kasir/Owner menerbitkan invoice sebelum bayar.
- Pembayaran hanya setelah pekerjaan selesai/ditutup dan invoice terbit, langsung
  lunas. Tidak ada DP, cicilan, atau tempo. **[DIPUTUSKAN 2026-11-15]** Metode
  sekarang: tunai, QRIS statis milik Owner, dan transfer manual ke rekening Owner.
  Gateway ditunda ke pengembangan berikutnya. QRIS/rekening hanya ditampilkan
  sebagai tujuan pembayaran; Kasir/Owner mengonfirmasi setelah dana masuk diperiksa,
  bukan otomatis dari scan QR, tombol pelanggan atau gambar bukti transfer.
  QRIS asli, nama bank, nomor rekening dan nama pemilik belum diberikan.
  **Persetujuan lanjutan 2026-11-15:** user menyetujui pratinjau pembayaran tanpa
  gateway, termasuk tunai tetap tersedia dan konfirmasi manual QRIS/transfer.
  Penanda tujuan pembayaran belum tersedia dipertahankan sampai data asli
  diberikan. Persetujuan ini tidak menyatakan aplikasi existing sudah dimigrasi.
- Hak edit invoice draf yang sebelumnya diberikan kepada Teknisi telah diselaraskan
  pada fase kasir melalui keputusan §2.7.
- User meminta prototype browser bertahap memakai HTML/CSS/JS dan data dummy.
  Ini lingkup prototype, bukan penggantian stack produksi. Arah FigCraft tetap
  dipakai; instruksi memulai browser ini menggantikan gate menunggu visual UI-04.
- User melanjutkan ke 3A: daftar SO, penanggung jawab dan progres dengan tombol
  Mulai pengerjaan. SO baru pada demo belum dianggap mulai otomatis. Pilihan
  transisi dan batas irisan prototype dijelaskan pada IPD WEB-03A; realisasi biaya
  tetap 3B, antrean kasir 3C. Ini tidak memfinalkan seluruh kebijakan produksi.

### 2.3 Klarifikasi data dan revisi [DIPUTUSKAN 2026-11-06]

Sumber: jawaban user pada pemeriksaan ulang susunan database. Bagian ini
melengkapi §2.1–§2.2 dan menggantikan ketentuan lama yang bertentangan.

- SO yang belum Selesai atau Dibatalkan dapat direvisi Teknisi dan Owner.
  SO Selesai hanya dapat direvisi Owner. SO Dibatalkan dikunci terhadap revisi
  Teknisi juga; keputusan ini tidak menetapkan mekanisme pembukaan kembali SO
  Dibatalkan. Estimasi yang sudah disetujui tetap menjadi acuan, dan perubahan
  realisasi tetap memiliki jejak perubahan sesuai §2.2.
- Qty harus positif dan mengikuti satuan item: pcs/unit memakai bilangan bulat;
  kg/liter/meter boleh pecahan; jasa mengikuti satuan penagihan, misalnya pekerjaan
  atau jam. Qty pecahan disimpan dengan presisi desimal tetap, bukan float.
  Batas qty 999 pada prototype bukan batas bisnis produksi. Skala presisi dan
  kapasitas kolom ditetapkan dalam rancangan BSD.
- Setiap kedatangan dibuatkan registrasi baru, termasuk ketika kendaraan yang sama
  dibawa pelanggan/pemilik berbeda. Data pelanggan pada registrasi sebelumnya
  tetap dipertahankan. Tidak diperlukan alur khusus perpindahan kepemilikan untuk
   registrasi; identitas kendaraan mengikuti keputusan tambahan di bawah.
- Identitas kendaraan cukup menggunakan nomor plat **[DIPUTUSKAN 2026-11-11]**.
  Nomor rangka tidak diperlukan sebagai pembeda kendaraan.
- Plat yang sama menggunakan satu data kendaraan **[DIPUTUSKAN 2026-11-11]**.
  Sistem menyeragamkan huruf menjadi kapital dan menghapus spasi untuk pencocokan
  sebelum pencarian atau penyimpanan. Contoh `B 1234 ABC` dan `b1234abc` mengacu
  kendaraan yang sama. Nilai plat hasil normalisasi harus unik pada data kendaraan;
  detail constraint fisik dirancang di BSD.
- Owner boleh mengganti plat pada data kendaraan yang sama ketika plat berubah
  **[DIPUTUSKAN 2026-11-11]**. Riwayat servis tetap terhubung ke kendaraan tersebut
  dan perubahan plat memiliki riwayat. Dokumen kunjungan lama mempertahankan
  snapshot plat saat kunjungan. Plat baru tetap mengikuti aturan normalisasi dan
  keunikan di atas; perubahan tidak menggabungkan dua data kendaraan secara otomatis.
- Satu registrasi kunjungan memiliki paling banyak satu Diagnosa & Estimasi dan
  satu SO **[DIPUTUSKAN 2026-11-11]**. Dokumen dibuat sesuai tahap layanan;
  perubahan dicatat sebagai revisi, bukan membuat dokumen kedua untuk kunjungan
  yang sama. Estimasi yang telah disetujui tetap dipertahankan sesuai §2.2.
- Nomor telepon boleh digunakan oleh beberapa pelanggan
  **[DIPUTUSKAN 2026-11-11]**. Setiap pelanggan memiliki ID internal tersendiri;
  nomor telepon bukan identitas unik dan kesamaan nomor tidak otomatis
  menggabungkan pelanggan. Kewajiban telepon saat registrasi pada §2.2 tetap berlaku.
- Registrasi menyimpan snapshot nama pelanggan, nomor telepon, alamat (bila diisi),
  dan nomor plat saat kunjungan, serta tetap terhubung ke master pelanggan dan
  kendaraan **[DIPUTUSKAN 2026-11-11]**. Perubahan data master berikutnya tidak
  mengubah snapshot registrasi atau identitas pada dokumen kunjungan lama.
- Koreksi salah input registrasi (nama, telepon, plat, atau keluhan) diperbolehkan
  dengan riwayat perubahan **[DIPUTUSKAN 2026-11-11]**. Sebelum SO dibuat, koreksi
  boleh dilakukan petugas yang berhak melakukan registrasi. Setelah SO dibuat,
  koreksi hanya boleh dilakukan Owner dan wajib alasan. Koreksi registrasi tidak
  otomatis mengubah master pelanggan/kendaraan atau dokumen yang sudah final.
  Aturan ini membedakan koreksi eksplisit dari perubahan otomatis akibat master.
- Master pelanggan, kendaraan, jasa, dan part yang sudah digunakan dalam transaksi
  dinonaktifkan, bukan dihapus permanen **[DIPUTUSKAN 2026-11-11]**. Data nonaktif
  tidak dapat dipilih untuk transaksi baru; riwayat dan dokumen lama tetap utuh.
  Data dapat diaktifkan kembali ketika diperlukan. Keputusan ini tidak menetapkan
  aturan penghapusan data yang belum pernah digunakan dalam transaksi.
- Satu SO dapat dikerjakan beberapa Teknisi yang semuanya setara, tanpa Teknisi
  utama atau hierarki penanggung jawab/anggota **[DIPUTUSKAN 2026-11-11;
  menggantikan keputusan Teknisi utama sebelumnya]**. Minimal satu Teknisi harus
  dipilih sebelum pengerjaan dimulai; SO Belum dimulai boleh disiapkan tanpa
  penugasan. Penugasan tidak mengubah batas hak revisi atau akses finansial pada
  §2.1–§2.3. Prototype yang masih memakai utama/anggota belum mencerminkan keputusan ini.
- Jumlah stok boleh dilihat Owner, Teknisi, dan Kasir. HPP/harga beli hanya boleh
  diakses Owner. Hak melihat stok tidak memberikan hak mengubah stok. Keputusan ini
  menetapkan visibilitas, bukan memfinalkan seluruh lingkup stok/pembelian/laporan.

---

### 2.4 Reservasi dan pengeluaran stok [DIPUTUSKAN 2026-11-06]

- Redis tidak digunakan untuk tahap awal. Reservasi stok disimpan di MySQL dan
  tersedia melalui API untuk ditampilkan pada interface.
- Part yang masuk SO dan tervalidasi server membuat reservasi: stok tersedia
  berkurang, tetapi stok tercatat belum berkurang. Draf offline belum menjamin
  reservasi sampai server menerima dan memvalidasinya.
- Interface menampilkan stok tercatat, stok direservasi, dan stok tersedia.
  Stok tersedia memperhitungkan reservasi aktif dan barang rusak yang diblokir
  sesuai keputusan tambahan di bawah. Ketiga peran boleh
  melihat jumlahnya; batas akses HPP/harga beli pada §2.1 tetap berlaku.
- Pengeluaran stok final terjadi saat invoice final diterbitkan, meskipun belum
  dibayar. Ini menggantikan aturan lama pengurangan stok saat pembayaran berhasil.
  Invoice draf belum memicu pengeluaran stok; pembayaran tidak menguranginya lagi.
- Pengeluaran stok dan penyelesaian reservasi harus satu transaksi MySQL dan
  idempoten. Part yang dilepas sebelum dipakai melepaskan reservasinya. Pembatalan
  tidak otomatis mengembalikan part yang sudah dipakai; tetap mengikuti realisasi.
- Koreksi harga invoice tidak otomatis mengembalikan stok. Aturan retur fisik,
  pembelian, dan laporan stok rinci belum diputuskan.
- SO Ditunda tetap menahan reservasi part selama part masih dibutuhkan SO tersebut
  **[DIPUTUSKAN 2026-11-11]**. Penundaan tidak otomatis melepaskan reservasi.
  Part yang dilepas dari SO membebaskan reservasinya selama belum dipakai;
  part yang sudah dipakai tetap mengikuti realisasi, bukan otomatis kembali tersedia.
- Satu pembelian dapat diterima sekaligus atau melalui beberapa penerimaan barang
  bertahap **[DIPUTUSKAN 2026-11-11]**. Penerimaan bertahap tetap terhubung ke
  pembelian yang sama. Keputusan ini menetapkan dukungan pola penerimaan, bukan
  seluruh alur pembelian, pembayaran supplier, retur, atau perhitungan HPP.
- Stok pembelian hanya bertambah setelah barang benar-benar diterima dan
  penerimaannya dicatat **[DIPUTUSKAN 2026-11-11]**. Penambahan mengikuti jumlah
  aktual pada setiap penerimaan; jumlah pesanan yang belum diterima tidak menambah
  stok. Pencatatan pesanan pembelian saja tidak menambah stok.
- Mayoritas pembelian ke supplier dibayar langsung lunas
  **[KETERANGAN USER 2026-11-11]**.
- Pembayaran pembelian ke supplier mendukung langsung lunas maupun dibayar
  belakangan **[DIPUTUSKAN 2026-11-11]**. Sistem mencatat sisa utang supplier dan
  pembayaran sampai lunas. Pembayaran dilakukan penuh dalam satu pembayaran,
  baik langsung maupun belakangan; tidak mendukung pembayaran sebagian/cicilan
  **[DIPUTUSKAN 2026-11-11]**. Penerimaan barang tetap dapat bertahap sesuai aturan di atas.
  Aturan ini khusus pembelian supplier; pembayaran pelanggan tetap mengikuti §2.2.
- Utang supplier tidak memerlukan pencatatan tanggal jatuh tempo maupun penanda
  mendekati/melewati jatuh tempo **[DIPUTUSKAN 2026-11-11]**. Status belum dibayar
  dan lunas tetap dicatat sesuai aturan pembayaran pembelian di atas.
- **Keputusan terbaru [DIPUTUSKAN 2026-11-11]: perhitungan HPP otomatis dan laporan
  profit ditunda dari lingkup tahap sekarang.** Keputusan ini menggantikan aktivasi
  HPP rata-rata bergerak dan snapshot HPP saat invoice final yang dicatat sebelumnya
  di bawah. Harga beli setelah diskon, jumlah/tanggal penerimaan, stok awal,
  pergerakan stok, asal barang retur, pengeluaran, dan pembayaran supplier tetap
  dicatat. Omzet, uang masuk/keluar, dan utang supplier tidak dibatalkan oleh
  penundaan ini; laporan tersebut tidak boleh disebut sebagai laba/profit lengkap.
  Ketentuan HPP pada bagian lain dokumen menjadi acuan tertunda, bukan kewajiban
  implementasi tahap sekarang. Hak akses harga beli tetap hanya Owner.
- Riwayat keputusan sebelum penundaan terbaru: HPP part memakai metode
  **rata-rata bergerak [DIPUTUSKAN 2026-11-11; kini ditunda]**,
  menggantikan keputusan penundaan sebelumnya. Rata-rata dihitung ulang setiap
  penerimaan barang, termasuk penerimaan bertahap: nilai stok sebelum penerimaan
  ditambah nilai barang diterima, dibagi qty stok setelah penerimaan. Dasarnya stok
  tercatat, termasuk qty yang sedang direservasi, bukan hanya stok tersedia.
- Riwayat keputusan sebelum penundaan terbaru: saat invoice final diterbitkan dan
  stok dikeluarkan, HPP part terpakai disimpan
  sebagai snapshot **[DIPUTUSKAN 2026-11-11]**. Pembelian berikutnya tidak mengubah
  HPP transaksi lama. Waktu pembayaran supplier tidak mengubah perhitungan modal.
  HPP memakai desimal tetap, bukan float; skala penyimpanan dan pembulatan dirancang
   di BSD. Pencatatan retur supplier mengikuti keputusan di bawah; perlakuan HPP
  dan penyelesaian nilai retur masih perlu ditetapkan.
- Ongkir pembelian dicatat sebagai pengeluaran bengkel terpisah, tidak dimasukkan
  ke modal part **[DIPUTUSKAN 2026-11-11]**. Diskon pembelian mengurangi harga beli
  part yang menjadi dasar HPP rata-rata bergerak. Ongkir tidak boleh dihitung lagi
  sebagai bagian HPP agar biaya tidak tercatat dua kali.
- Diskon pembelian mendukung diskon per part maupun potongan total nota pembelian
  **[DIPUTUSKAN 2026-11-11]**. Potongan total nota dialokasikan otomatis secara
  proporsional berdasarkan nilai masing-masing baris part setelah diskon per part
  **[DIPUTUSKAN 2026-11-11]**. Alokasi tersebut mengurangi modal masing-masing part
  untuk perhitungan HPP. Detail presisi, pembulatan, dan penanganan sisa alokasi
  dirancang di BSD agar jumlah alokasi tepat sama dengan potongan total nota.
- Pengembalian barang ke supplier setelah penerimaan, misalnya karena rusak atau
  salah kirim, perlu dicatat dalam sistem **[DIPUTUSKAN 2026-11-11]**.
- Penyelesaian retur supplier mendukung penggantian barang maupun pengembalian
  uang/pengurangan tagihan **[DIPUTUSKAN 2026-11-11]**. Detail mekanisme stok,
  dan perlakuan HPP retur belum seluruhnya ditetapkan. Dukungan kedua
  bentuk penyelesaian ini tidak menetapkan bahwa satu retur harus memakai keduanya.
- Retur yang diselesaikan dengan pengurangan tagihan pada pembelian belum dibayar
  mengurangi utang supplier sebesar nilai retur **[DIPUTUSKAN 2026-11-11]**.
  Pada pembelian yang sudah lunas, pembayaran awal tetap dipertahankan;
  pengembalian uang supplier dicatat terpisah hanya saat uang benar-benar diterima.
  Selama uang belum diterima, retur berstatus menunggu pengembalian uang.
- Retur supplier terhubung ke penerimaan barang asal yang dipilih saat pencatatan
  **[DIPUTUSKAN 2026-11-11]**. Hubungan ini memungkinkan penelusuran supplier,
  baris part, dan harga beli setelah diskon pada penerimaan asal. Harga beli asal
  menjadi acuan nilai retur, bukan harga pembelian terbaru. Detail penyesuaian
  nilai persediaan dan HPP rata-rata akibat retur masih perlu dirancang.
- Untuk retur dengan barang pengganti, barang yang dikembalikan keluar dari stok
  saat diserahkan ke supplier; barang pengganti menambah stok hanya setelah
  benar-benar diterima **[DIPUTUSKAN 2026-11-11]**. Selama menunggu penerimaan,
  barang pengganti belum dihitung sebagai stok tersedia. Perlakuan nilai HPP
  retur belum ditetapkan.
- Barang rusak langsung ditandai tidak tersedia untuk dipakai, meskipun masih
  tercatat secara fisik di bengkel sampai dikembalikan ke supplier
  **[DIPUTUSKAN 2026-11-11]**. Qty rusak yang diblokir tidak dapat dialokasikan
  untuk pekerjaan baru. Untuk qty rusak yang masih termasuk stok tercatat,
  stok tersedia = stok tercatat − reservasi aktif − qty rusak yang diblokir;
  qty yang sama tidak boleh dikurangkan dua kali. Aturan ini melengkapi rumus
  stok tersedia pada §2.4; detail penyimpanan dan penanganan part yang sudah
  direservasi sebelum diketahui rusak dirancang lebih lanjut.
- Struktur tabel menjadi tanggung jawab BSD; keputusan ini belum mengesahkan
  seluruh kolom, indeks, atau implementasi database.

### 2.4.1 Akses operasional stok dan retur pelanggan [DIPUTUSKAN 2026-11-11]

- Pencatatan pembelian, penerimaan barang, barang rusak, retur supplier, dan
  pembayaran supplier hanya dilakukan Owner. Visibilitas jumlah stok untuk
  Teknisi/Kasir tetap mengikuti §2.3–§2.4.
- Untuk kondisi kegagalan layanan/part yang diselesaikan melalui retur pelanggan,
  sistem perlu mendukung pengembalian part dari pelanggan dan pengembalian uang
  kepada pelanggan. Ini tidak menetapkan refund otomatis untuk setiap kegagalan.
  Pengembalian uang tetap dicatat terpisah dari pembayaran awal sesuai §2.1.
- Retur pelanggan terhubung ke invoice dan part asal. Owner menyetujui nilai
  refund berdasarkan kasus, termasuk apakah mencakup harga part saja atau juga
  jasa. Pembayaran awal tetap tersimpan. Part yang kembali diperiksa sebelum
  menjadi stok siap pakai; part rusak tetap diblokir. Kriteria garansi, pelaksana
  pencairan refund, dan detail penyesuaian HPP masih perlu dirancang.

### 2.4.2 Status produksi SO [DIPUTUSKAN 2026-11-11]

Keputusan ini melengkapi §2.2–§2.3 dan menggantikan keterangan sebelumnya bahwa
status awal SO belum final; transisi Diagnosa & Estimasi tetap belum dirinci.

- Alur utama SO: Belum dimulai → Dalam Pengerjaan → Selesai.
- SO Dalam Pengerjaan dapat Ditunda, kemudian dilanjutkan kembali.
- Pekerjaan dapat Dibatalkan; biaya aktual yang sudah timbul tetap dicatat.
- SO Selesai hanya dapat dibuka kembali oleh Owner dengan alasan. Jika sedang
  mengantre di kasir, Owner harus menariknya dahulu sesuai §2.6.
- Sesudah invoice final terbit, SO tetap terkunci; koreksi memakai alur invoice
  atau retur. SO Dibatalkan tetap terkunci; pelanggan kembali memakai SO baru.
- Hak revisi dan penyerahan antrean tetap mengikuti §2.3 dan §2.6. Matriks izin
  rinci untuk tiap aksi transisi harus dituangkan dalam rancangan berikutnya.

### 2.4.3 Konflik draf offline [DIPUTUSKAN 2026-11-11]

Keputusan ini mengesahkan pendekatan versi yang sebelumnya direkomendasikan di §3.1.

- Setiap perubahan membawa versi data. Perubahan pertama yang valid diterima
  server; perubahan dari versi lama ditahan tanpa menimpa versi server.
- Salinan perubahan lokal tetap disimpan. Pengguna membandingkan versi server
  dan perubahan lokal, lalu memilih perubahan yang diterapkan ulang.
- Server memvalidasi ulang versi, izin, status dokumen, dan ketersediaan stok
  sebelum menerima hasil penyelesaian konflik. Draf offline belum menjamin reservasi.
- Perubahan offline tidak boleh membuka kembali SO terkunci atau melewati
  penguncian invoice final. Pembayaran, stok, dan invoice resmi tetap wajib online.

### 2.4.4 Saldo stok awal [DIPUTUSKAN 2026-11-11]

- Saat mulai menggunakan sistem, Owner menghitung stok fisik dan mencatat part,
  jumlah awal, serta modal rata-rata per unit dari catatan pembelian yang tersedia.
  Barang rusak dibedakan dari barang siap pakai.
- Pencatatan menjadi saldo awal, bukan pembelian baru atau uang keluar baru.
  Nilai saldo awal menjadi dasar perhitungan HPP rata-rata berikutnya.
- Modal awal yang belum diketahui ditandai belum lengkap, bukan otomatis Rp0.
  Laporan profit yang bergantung pada modal tersebut belum dapat dianggap akurat.

### 2.5 Qty dan pembulatan biaya [DIPUTUSKAN 2026-11-07]

- User memilih dukungan qty pecahan sekarang, termasuk prototype Fase 3B.
- Kg, liter, meter, dan jasa per jam mendukung maksimal tiga angka desimal.
  Pcs, unit, dan jasa per pekerjaan tetap bilangan bulat positif.
- Subtotal setiap baris dibulatkan ke rupiah terdekat; pecahan Rp0,50 dibulatkan
  naik. Total dokumen menjumlahkan subtotal baris yang sudah dibulatkan.
- Perhitungan dan penyimpanan qty memakai desimal tetap, bukan float. Keputusan
  ini menetapkan presisi bisnis, bukan seluruh kapasitas kolom database produksi.

### 2.6 Penyerahan ke antrean kasir [DIPUTUSKAN 2026-11-07]

- Teknisi dan Owner boleh menetapkan realisasi tersimpan sebagai rincian akhir dan
  menyerahkan SO Selesai ke antrean kasir. Ini pengecualian untuk aksi penyerahan,
  bukan izin Teknisi merevisi biaya atau progres SO Selesai.
- SO Dibatalkan dengan biaya diserahkan Owner setelah rincian aktual diperiksa.
- Selama berada dalam antrean, realisasi dan progres tidak boleh diubah. Owner
  menarik SO dari antrean dengan alasan sebelum merevisi, kemudian menyerahkannya
  kembali setelah diperiksa. Penarikan tidak menghapus riwayat atau mengubah biaya.
- Antrean bukan invoice atau pembayaran. Penerbitan invoice dan pengeluaran stok
  tetap mengikuti §2.2 dan §2.4; pada prototype merupakan fase berikutnya.

### 2.7 Invoice draf dan nominal nol [DIPUTUSKAN 2026-11-07]

- Harga jual invoice draf hanya dapat diubah Owner. Ini menggantikan izin invoice
  draf Teknisi pada §2.1; hak harga lokal SO yang diizinkan tetap berlaku.
- Penerbitan invoice dan penerimaan/konfirmasi pembayaran tetap Kasir/Owner.
- Invoice final dengan total Rp0 langsung berstatus **Lunas**, tanpa transaksi
  pembayaran Rp0 dan tanpa pencatatan uang masuk. Nota tetap menampilkan total Rp0.
- Invoice positif berstatus Lunas setelah pembayaran penuh. Usulan status terpisah
  “Tanpa tagihan” tidak dipakai. Koreksi dan uang tercatat tetap mengikuti §2.1.
- Satu SO memiliki paling banyak satu invoice **[DIPUTUSKAN 2026-11-11]**.
  Koreksi disimpan sebagai riwayat internal pada invoice yang sama, bukan membuat
  invoice kedua. Riwayat koreksi tidak ditampilkan pada invoice/nota yang diberikan
  kepada pelanggan, termasuk tampilan cetak atau PDF. Dokumen pelanggan menampilkan
  rincian invoice versi berlaku; riwayat internal tetap mengikuti akses Owner pada §2.1.

### 2.8 Beranda Kasir berupa POS [DIPUTUSKAN 2026-11-07]

- Peran Kasir langsung membuka ruang kerja POS sebagai menu utama/default.
- POS berpusat pada SO siap ditagih serta invoice draf/belum lunas: pilih
  kendaraan/pelanggan, periksa rincian, terbitkan invoice, bayar lalu cetak nota.
- **[DIPUTUSKAN 2026-11-15, jawaban Q1 redesign]** Tampilan awal POS berupa
  grid kartu transaksi yang memenuhi area utama. Memilih kartu membuka rincian
  transaksi; keputusan ini menggantikan tata letak antrean kiri/rincian kanan
  permanen pada laptop. Ponsel juga menampilkan daftar dahulu, kemudian rincian.
  Pencarian memakai plat, nama, nomor SO/invoice. Registrasi tetap dapat dibuka
  dari menu. Perubahan ini baru arah redesign; prototype existing belum diubah.
- Hak harga/pembayaran pada §2.1/§2.7 tetap berlaku; arah POS tidak memberikan
  hak edit harga kepada Kasir.

## 3. Perangkat dan teknis

| Hal | Keputusan |
|---|---|
| Perangkat utama | Laptop dan ponsel. |
| Alat pendukung | Printer dan/atau pemindai sudah ada, tetapi belum pernah dipakai. Merek dan jenisnya: ISI: |
| Sistem ponsel | ISI: (Android atau iPhone; ini menentukan cara cetak, lihat 3.2) |
| Offline | Harus bisa jalan tanpa internet. |
| Autosave | Ya: data tersimpan otomatis seperti di Accurate. **[ASUMSI]** artinya draf tersimpan setiap ada perubahan tanpa harus menekan tombol simpan, dan tetap aman saat offline atau koneksi putus. |

### 3.1 Stack **[DIPUTUSKAN 2026-10-14, hasil M0]** (menimpa usulan Supabase; ikut metaprompt STACK TETAP)

| Lapisan | Pilihan | Alasan |
|---|---|---|
| Bentuk aplikasi | PWA (aplikasi web yang bisa dipasang) | Satu kode untuk laptop dan ponsel, tanpa toko aplikasi, dan bisa jalan offline |
| Frontend | React + TypeScript (strict) + Vite, React Router, RHF+Zod, TanStack Query, Dexie, vite-plugin-pwa, Recharts | Sesuai metaprompt; evolusi dari `index.html` prototype (dipecah bertahap, bukan dibuang) |
| Gaya | Tailwind + token Buddy (`DESIGN_POS_Extend.md`); komponen shadcn/ui di-styling ulang ikut token | Sesuai metaprompt + Buddy; hindari tampilan templat generik |
| Referensi utama komponen UI | [React Aria](https://react-aria.adobe.com/) | DIPUTUSKAN 2026-11-02; cakupan dan hubungan dengan stack existing di bawah |
| Offline dan autosave | Service worker + IndexedDB (Dexie); TERBATAS: draft Customer/Kendaraan/Diagnosa/SO offline, bayar/stok/invoice wajib online | Aturan Arsitektur 7 metaprompt (DIPUTUSKAN 2026-10-14) |
| Backend | Target Laravel 13 (PHP 8.3+) REST API, Sanctum, spatie/laravel-permission, MySQL (XAMPP lokal, VPS produksi). Runtime lokal PHP 8.4.27, build Windows 8.4.27-1. | Pembaruan versi disetujui user 2026-10-29 (ENV-01). AUTH-01 mulai mengimplementasikan fondasi/login pada `application/`; modul bisnis belum dibuat. XAMPP terdeteksi MariaDB; pengembangan AUTH-01 memakai MySQL 8.4 portable terpisah, tanpa mengubah XAMPP. |
| Deployment produksi | VPS; HTTPS wajib. Penyedia dan paket belum dipilih; pembelian direncanakan kemudian. | DIPUTUSKAN 2026-11-01; user membatalkan pilihan shared hosting dan kembali ke VPS. Persyaratan teknis deployment di TRD §1. |
| Pembayaran | Tunai, QRIS statis dan transfer manual ke rekening Owner; langsung lunas | DIPUTUSKAN 2026-11-15; gateway ditunda, detail tujuan pembayaran belum diberikan |

**Preferensi terbaru 2026-11-17:** user menyatakan ingin “hosting biasa” saat
meminta rekomendasi setup lokal. Penyedia/paket belum diberikan dan kelayakan
shared hosting belum diverifikasi; keputusan VPS belum diganti. MySQL portable
AUTH-01 hanya untuk pengembangan lokal dan tidak mewajibkan Docker pada hosting.

**Referensi komponen UI [DIPUTUSKAN 2026-11-02]:** React Aria menjadi rujukan
utama perilaku dan aksesibilitas komponen (keyboard, fokus, semantik, dan state
interaksi). React Aria menyediakan komponen tanpa gaya bawaan; styling tetap
mengikuti Tailwind dan token aktif di `DBD/DESIGN_POS_Extend.md`, dengan arah
prototype pada §5. Penambahan ini menetapkan referensi, bukan pemasangan paket
atau migrasi otomatis dari shadcn/ui. Pemakaian dependency React Aria dan perubahan
komponen existing harus dinilai serta diuji pada irisan implementasi terkait.
Referensi visual khusus yang sudah disetujui tetap berlaku pada cakupannya.

Risiko utama yang harus diuji lebih awal: **sinkronisasi offline** (konflik
bila dua perangkat mengubah work order yang sama). Aturan awal yang disarankan:
setiap perubahan membawa nomor versi; bila bentrok, tampilkan pilihan ke
pengguna, jangan menimpa diam-diam.

### 3.2 Cetak nota dari ponsel **[ASUMSI]** bergantung pada jenis ponsel

Cetak langsung dari browser ke printer termal lewat Web Bluetooth tidak
didukung di semua browser (MDN menyatakan API ini bukan Baseline dan eksperimental).
Karena itu cara cetak diputuskan setelah jenis ponsel dan printer diketahui:

- Android + Chrome: kemungkinan bisa langsung cetak (perlu diuji dengan printer asli).
- iPhone: siapkan alternatif, yaitu cetak lewat dialog cetak browser, simpan PDF
  lalu bagikan, atau cetak dari laptop.

Nota selalu bisa dibuat sebagai PDF/tampilan cetak biasa sebagai jalur cadangan.

---

## 4. Alur dan layar prioritas

Alur inti (dari jawaban user: nota servis untuk diagnosa awal, lalu work order):

1. **Nota servis (penerimaan)**: plat nomor, data pelanggan, keluhan, diagnosa awal.
2. **Work order**: pekerjaan yang dikerjakan, berisi jasa dan suku cadang.
3. **Nota akhir dan pembayaran**. **[ASUMSI]**

Alur paling kritis yang harus tercepat: penerimaan kendaraan (nota servis).

Layar prioritas, urut: ISI: (usulan agent: 1 Nota servis, 2 Work order,
3 Riwayat kendaraan per plat nomor)

**[ASUMSI]** Pelanggan sering kembali, jadi riwayat servis dan garansi per plat
nomor berguna. Stok suku cadang, laporan, dan notifikasi ke pelanggan:
ISI: (perlu atau belum)

Alur dan status aktif mengikuti §2.2. Urutan WO 2026-10-14 adalah riwayat;
status pembayaran dipisahkan dari status pengerjaan SO.

---

## 5. Arah visual (keputusan user)

**[DIPUTUSKAN 2026-11-15, label persetujuan estimasi]** User meminta label
"Pelanggan menyetujui lisan" diganti menjadi "Setuju". Keterangan persetujuan
lisan dan aturan sebelum pencatatan tetap mengikuti §2.2.

**[DIPUTUSKAN 2026-11-15, penerimaan hasil prototype Registrasi]** User menerima
hasil penambahan Registrasi pada file FigCraft utama dengan tanggapan
"oke aman" setelah laporan hasil dan batas simulasi diberikan. Lingkup dan bukti
mengikuti IPD FIG-REGISTRATION-01 serta README prototype. Pada saat penerimaan
tersebut, Diagnosa & Estimasi belum dibangun pada file ini. User kemudian
meminta lanjut ke tahap berikutnya; pelaksanaannya mengikuti IPD FIG-DIAGNOSIS-01.

**[DIPUTUSKAN 2026-11-15, persetujuan hasil prototype kasir]** User menyetujui
hasil pelengkapan kasir pada file utama `prototype/figcraft/pos-kasir.figcraft`
setelah menerima laporan hasil dan batas simulasi. Rincian lingkup, bukti
verifikasi dan hal yang belum terintegrasi mengikuti IPD FIG-CASHIER-FINISH-01
serta README prototype. Persetujuan ini berlaku untuk hasil prototype kasir
yang dilaporkan; modul lain tetap mengikuti lingkup masing-masing.

**[DIPUTUSKAN 2026-11-15, satu file kerja FigCraft]** User meminta layar yang
sedang dikembangkan disatukan dalam satu file. File utama
`prototype/figcraft/pos-kasir.figcraft` memuat halaman Desktop, Ponsel, Referensi
dan Komponen. User kemudian meminta kasir dituntaskan pada file yang sama;
pelaksanaan dan hasil pemeriksaan dicatat di IPD FIG-CASHIER-FINISH-01.
Referensi pasangan awal menjadi aset pembanding di dalam file, bukan dokumen
terpisah yang harus dibuka. Arsip historis tetap dipertahankan.

**[DIPUTUSKAN 2026-11-15, persetujuan konsep alur kasir lokal]** User menerima
pratinjau invoice draf, pembayaran tunai dan nota lunas dengan Poppins/palet
pendukung. Ini persetujuan konsep visual simulasi, bukan pembayaran nyata atau
persetujuan hasil integrasi aplikasi. Metode pembayaran aktif mengikuti §2.2;
catatan kebutuhan pratinjau gateway sebelumnya sudah digantikan keputusan user
untuk menunda gateway. Detail tujuan pembayaran asli tetap belum diberikan.

**[DIPUTUSKAN 2026-11-15, persetujuan palet dan permintaan font]** User menerima
contoh pembagian warna pendukung dan meminta font Gotham/Poppins. Pilihan
implementasi untuk konsep redesign adalah Poppins. Ini menggantikan Inter pada
konsep baru; artefak historis dan prototype aplikasi belum otomatis dimigrasi.
Peran palet serta tipografi bersumber pada `DBD/DESIGN_POS_Extend.md`. Persetujuan
ini mengunci palet contoh, bukan menyetujui seluruh hasil generator Stitch.

**[DIPUTUSKAN 2026-11-15, persetujuan pratinjau Poppins]** User menyetujui
pratinjau Poppins dengan palet pendukung. Poppins kini menjadi acuan tipografi
konsep redesign. Konsep POS dilanjutkan ke ponsel dan detail setelah memilih
kartu; persetujuan ini tidak menyatakan seluruh halaman generator atau aplikasi
existing sudah selesai diuji.

**[DIPUTUSKAN 2026-11-15, jawaban Q1–Q2 redesign]** User menyetujui grid kartu
POS dahulu, kemudian rincian transaksi setelah dipilih, serta mempertahankan
biru existing sebagai aksen utama. User meminta warna pendukung agar antarmuka
tidak terasa sangat monokrom. Tiga screenshot restoran/POS kiriman user menjadi
referensi baru: gambar 3 untuk rincian kartu SO, gambar 1 untuk pemisahan rincian
transaksi, gambar 2 untuk pengelompokan permukaan dan navigasi. Konten disesuaikan
ke bengkel dan aturan sistem existing. Izin warna pendukung memperbarui pembatasan
palet netral/satu aksen lama; nilai dan peran warna usulan hanya di
`DBD/DESIGN_POS_Extend.md`. User meminta penelusuran psikologi warna dan konfirmasi
rancangan sebelum diterapkan pada prototype. Tahap berikut berupa konsep Stitch,
bukan perubahan alur bisnis atau migrasi stack. Persetujuan palet lanjutan
dicatat pada keputusan di atas; hasil visual tetap ditinjau tersendiri.

**[DIPUTUSKAN 2026-11-11, revisi prototype browser]** User meminta shadcn/ui
sebagai acuan visual, palet netral dengan satu aksen, serta konsistensi navigasi,
layout, daftar, formulir dan state. Terapkan pola dengan komponen existing bila
stack tidak cocok; fitur dan alur bisnis dipertahankan. Keputusan ini memperbarui
arah permukaan/komponen prototype lama yang bertentangan, tanpa migrasi stack.
Nilai visual tetap hanya di `DBD/DESIGN_POS_Extend.md`. Pelaksanaan: IPD WEB-06.

**[DIPUTUSKAN 2026-10-30, prototype UI]** User menyetujui seluruh 11 menu existing
dirancang di FigCraft dahulu, kemudian dibuat prototype browser setelah persetujuan
visual. Referensi: Shopmonkey untuk alur bengkel; Cursor dan Linear untuk karakter
tipografi clean; Calendly untuk permukaan putih/cerah dengan biru dan hijau. Light
dan dark wajib tersedia. Sidebar mengikuti model animated-sidebar starc007; user
mengizinkan rekonstruksi bila source asli tidak tersedia. Anti-slop diterapkan selama
perancangan. Brief ini menggantikan Buddy khusus prototype baru; token di
`DBD/DESIGN_POS_Extend.md` bagian "Prototype 2026-10-30" menjadi sumbernya.
Nama/logo final tetap terbuka. Menu stok/laporan existing direpresentasikan sebagai
mockup, bukan keputusan baru tentang backend. Rincian pelaksanaan: IPD UI-01.

| Hal | Keputusan |
|---|---|
| Kesan | Modern dan simple. Mudah dibaca dan mudah dipakai oleh orang awam. |
| Warna dominan | Nuansa biru. Warna biru merek (hex): ISI: |
| Terang atau gelap | ISI: (agent mengusulkan terang sebagai awal, **[REKOMENDASI]**) |
| Kerapatan | **[ASUMSI]** Lega: teks besar, target sentuh besar, informasi sedikit per layar. |
| Tujuan utama | Tidak terlihat seperti hasil AI generik ("slop"). |
| Benchmark kualitas | Dribbble dan Awwwards (lihat catatan di bawah). |
| Warna/gaya yang dilarang | Gradien biru-ungu generik; ISI: |

Catatan benchmark:
- Dipakai untuk **kualitas penggarapan** (hierarki, tipografi, ritme jarak),
  bukan untuk disalin. Ini aplikasi kerja harian: keterbacaan dan kecepatan
  menang atas gaya yang mencolok.
- Agent tidak boleh mengaku telah "mengikuti Awwwards" tanpa menyebut contoh
  spesifik yang diacu dan apa yang diambil. Tautan referensi dari user:
  ISI: (usulan: 3 sampai 5 tautan beserta apa yang disukai dari masing-masing)

Panduan anti-klise lengkap ada di `workflow/DESIGN.md`, terutama Bagian 5.

---

## 6. Konten nyata

- Bahasa antarmuka: Indonesia, tanpa istilah teknis yang tidak dipahami orang awam.
- Mata uang dan angka: Rupiah, format `Rp 1.250.000`.
- Istilah yang dipakai: nota servis, work order, plat nomor, diagnosa, jasa,
  suku cadang. Istilah lain dari tim: ISI:
- Metode dan aturan pembayaran aktif mengikuti §2.2. QRIS statis tidak memerlukan
  integrasi gateway; pembayaran kartu dan integrasi gateway di luar lingkup sekarang.
- Nada tulisan: singkat, langsung, ramah, tanpa basa-basi. Nama aksi konsisten
  di seluruh alur.

Contoh jasa dan paket (**contoh untuk desain; harga dan daftar asli: ISI:**):

- Paket cuci kristal AC
- Paket bongkar dashboard
- Isi freon
- Kuras evaporator
- Servis AC rutin
- Cek kebocoran
- Ganti filter kabin
- Ganti blower
- Ganti kompresor
- Ganti kondensor

Agent memakai contoh ini untuk data tampilan, tetapi tidak boleh mengarang
harga. Gunakan harga asli bila ada, atau tandai jelas sebagai contoh.

---

## 7. Batasan dan larangan

- Tidak ada animasi yang menunda atau menghalangi input.
- Tidak ada istilah teknis di antarmuka yang tidak dipahami orang awam.
- Jangan membedakan status hanya dengan warna; sertakan teks atau ikon.
- Data tidak boleh hilang diam-diam. Tampilkan status penyimpanan yang jelas:
  Tersimpan, Menyimpan, atau Belum tersinkron.
- Aksi yang tidak bisa dibatalkan (hapus work order, batalkan pembayaran)
  selalu minta konfirmasi.
- ISI:

---

## 8. Status keputusan

| Hal | Status |
|---|---|
| Jenis usaha: bengkel AC mobil | FAKTA |
| Pengguna: kasir/admin dan pemilik, orang awam | FAKTA |
| Perangkat: laptop dan ponsel | FAKTA |
| Wajib offline dan autosave | FAKTA |
| Alur: nota servis lalu work order | FAKTA |
| Pembayaran: tunai/QRIS statis/transfer manual, lunas setelah invoice, tanpa DP/cicilan/tempo | DIPUTUSKAN 2026-11-15; §2.2; gateway ditunda |
| Arah visual: biru, modern, simple, mudah dipakai, bukan slop AI | FAKTA |
| Stack produksi PWA, React+TS, Laravel+MySQL; prototype HTML/CSS/JS dummy bertahap | DIPUTUSKAN 2026-10-14; lingkup prototype 2026-11-04 di §2.2 |
| Referensi utama komponen UI: React Aria; cakupan di §3.1 | DIPUTUSKAN 2026-11-02 |
| Pembaruan backend: target Laravel 13; runtime lokal PHP 8.4.27 (build Windows 8.4.27-1) | DIPUTUSKAN 2026-10-29; verifikasi dan batasan di `IPD/ipd.md` ENV-01 |
| Deployment produksi: VPS; pilihan shared hosting dibatalkan; penyedia/paket belum dipilih | DIPUTUSKAN 2026-11-01 |
| Role: Owner/Teknisi/Kasir; Supervisor dihapus; akses finansial per §2.1 | DIPUTUSKAN 2026-10-31 (menimpa keputusan 2026-10-14) |
| Status layanan mengikuti §2.2; offline tetap terbatas draf | DIPUTUSKAN 2026-11-04; offline 2026-10-14 |
| Cara cetak dari ponsel | BELUM DIPUTUSKAN (butuh jenis ponsel dan printer) |
| Alur nota→WO→bayar; status WO metaprompt | DIPUTUSKAN 2026-10-14 (M0) |
| Desain: DESIGN_POS_Extend + `workflow/DESIGN.md` ROOT (file ditemukan; deviasi 2026-10-14 dibuat saat file dianggap tidak ada) | DIPUTUSKAN 2026-10-14; diselaraskan 2026-10-31 |
| Nota akhir sebagai langkah ke-3, daftar status | ASUMSI |
| Terang atau gelap, hex biru merek, logo, nama | BELUM DIPUTUSKAN |
| Lingkup lanjutan stok/pembelian, laporan, notifikasi | BELUM DIPUTUSKAN seluruhnya; reservasi, visibilitas jumlah, dan pemicu pengeluaran sudah diputuskan di §2.3–§2.4 |
| Reservasi stok di MySQL, tampil melalui API, tanpa Redis dahulu; stok keluar saat invoice final terbit | DIPUTUSKAN 2026-11-06; §2.4. Lingkup pembelian/laporan/notifikasi tetap terbuka |

---

## 9. Berkas terkait

## ⛔ WAJIB DIBACA SEBELUM MULAI (BLOCKING)

Bagian ini **bukan opsional**. Kamu **DILARANG** menulis, mengubah, atau
menyarankan kode/UI/desain apa pun sebelum semua langkah di bawah selesai.

### File wajib baca (SEMUA, tanpa pengecualian)
| # | File | Lokasi |
|---|------|--------|
| 1 | `DESIGN.md` | `workflow/DESIGN.md` |
| 2 | `DESIGN_POS_Extend.md` | `POS/doc/DBD/DESIGN_POS_Extend.md` |

`DESIGN_POS_Extend.md` adalah **kelanjutan/tambahan** dari `DESIGN.md`. Jika ada
aturan yang bentrok, aturan di `DESIGN_POS_Extend.md` **menang** untuk
konteks POS. Membaca salah satu saja = **pelanggaran**.

### Langkah wajib (urut, tidak boleh dilewati)
1. **BACA** `workflow/DESIGN.md` secara penuh (bukan sebagian/ringkasan).
2. **BACA** `DESIGN_POS_Extend.md` secara penuh, di `POS/doc/DBD/`.
3. **BUKA registry skill desain** di `workflow/DESIGN.md`, lalu pilih skill yang
   relevan dengan tugas. Jika ada beberapa yang cocok, gunakan semuanya.
4. **MUAT skill terpilih** dan ikuti instruksinya. Jangan mengandalkan
   asumsi atau kebiasaan sendiri.
5. **NYATAKAN di awal respons** (format baku di bawah) sebelum mengerjakan tugas.

### Bukti kepatuhan (wajib ditulis di awal respons)
Respons tanpa blok ini dianggap **tidak valid** dan harus diulang.

### Larangan
- **JANGAN** mengasumsikan isi kedua file dari ingatan atau dari proyek lain.
- **JANGAN** melewati langkah ini karena tugas terlihat "kecil" atau "sepele".
  Berlaku untuk **semua** tugas yang menyentuh tampilan.
- **JANGAN** memilih gaya, warna, font, atau komponen di luar yang ditetapkan
  di `DESIGN.md` dan `DESIGN_POS_Extend.md`.
- Jika salah satu file **tidak ditemukan atau tidak bisa dibaca**: **BERHENTI**
  dan laporkan ke pengguna. Jangan lanjut dengan tebakan.

### Pemeriksaan akhir (sebelum menyatakan selesai)
- [ ] Hasil sudah dicocokkan dengan aturan di `DESIGN.md`
- [ ] Hasil sudah dicocokkan dengan aturan di `DESIGN_POS_Extend.md`
- [ ] Skill desain yang relevan benar-benar dipakai
- [ ] Tidak ada penyimpangan, atau penyimpangan dilaporkan beserta alasannya

### Referensi
- Desain: `workflow/DESIGN.md`
- Desain POS (extend): `POS/doc/DBD/DESIGN_POS_Extend.md`
- Skill desain: lihat registry di `workflow/DESIGN.md`
- Lainnya: ISI:
