# PRD: Product Requirement Documentation — POS Bengkel AC Mobil

Dokumen ini menjawab: **apa yang dibangun dan untuk siapa.**
Tidak memuat teknologi (TRD), skema data (BSD), atau tampilan (DBD).

Aturan pakai (sama seperti `../CONTEXT.md`):
- **[DIPUTUSKAN]** keputusan user; agent tidak mengubahnya.
- **[ASUMSI]** belum dipastikan; boleh dipertanyakan.
- **[REKOMENDASI]** usulan agent yang belum disetujui user.
- `ISI:` belum diputuskan; agent tidak boleh mengarang, tanyakan bila menentukan hasil.
- Satu fakta, satu dokumen sumber. Tautkan, jangan salin.

Sumber isi: `../CONTEXT.md` §1, §2, §4, §8 dan `../metaprompt-pembentukan-sistem.md`
(bagian PROYEK, Role, Fitur). Bila keduanya bertentangan, `CONTEXT.md` menang
(sudah dinyatakan di `CONTEXT.md` §2 dan §8).

---

## 1. Ringkasan
Sistem manajemen layanan dan transaksi bengkel berbasis PWA untuk bengkel AC mobil
(servis AC dan penjualan suku cadang), Makassar. Mencatat kendaraan yang masuk,
diagnosa awal, pekerjaan (jasa dan suku cadang), sampai nota dan pembayaran.
Dipakai orang awam, jadi kemudahan baca dan pakai lebih penting daripada gaya.

- Nama aplikasi / bengkel: ISI: (nama resmi; metaprompt hanya menyebut "Bengkel Dokter AC Mobil")
- Logo: ISI:

### Masalah bisnis yang harus terjawab (sumber: metaprompt)
1. Stok suku cadang tidak akurat dan tidak terdokumentasi.
2. Arus kas dan rincian transaksi sulit ditelusuri, termasuk kebutuhan bayar vendor.
3. Owner sulit melihat omzet, profit, dan kondisi keuangan secara langsung.

## 2. Pengguna dan peran
**[DIPUTUSKAN 2026-10-31]** Tepat tiga peran: **Owner, Teknisi, Kasir**. Menimpa
keputusan 2026-10-14 (Owner/Supervisor/Kasir + Mekanik): Supervisor dihapus,
Mekanik berganti nama Teknisi. Sumber: `../POS-handoff-login-role-global-search.md` §4;
rincian akses finansial di `../CONTEXT.md` §2.1 (satu fakta satu sumber, tidak disalin ke sini).

| Peran | Tugas utama | Harga jual | HPP/pengeluaran terbatas |
|---|---|---|---|
| Owner | Akses penuh: dashboard, pengguna, semua modul, laporan, koreksi invoice final, audit log | Ya | Ya (satu-satunya peran) |
| Teknisi | Registrasi, Diagnosa & Estimasi, realisasi dan progres SO; tidak mengubah SO Selesai | Ya (dokumen yang diizinkan); invoice dibaca, hak harga draf mengikuti CONTEXT §2.7 | Tidak |
| Kasir | Customer dan kendaraan, transaksi, terima/konfirmasi pembayaran, invoice, riwayat servis | Ya | Tidak |

Aturan kunci (keputusan user, detail di CONTEXT §2.1): pembayaran hanya Kasir dan
Owner; koreksi invoice final hanya Owner; log perubahan harga lengkap dan audit log
hanya Owner; satu cabang; login username + password.

Situasi pakai (CONTEXT §2): berpindah-pindah, bukan terikat satu meja; kadang ramai, kebanyakan santai;
pengguna cukup terbiasa aplikasi tapi non-teknis.
- Jumlah pengguna: ISI: · Cabang: satu **[DIPUTUSKAN 2026-10-31]**; multi-cabang di luar cakupan.

## 3. Tujuan dan kriteria sukses
Belum ada kriteria terukur yang diputuskan user. Usulan di bawah **[REKOMENDASI]**, diturunkan dari 3 masalah bisnis di §1.

| Masalah | Usulan kriteria yang bisa dicek | Status |
|---|---|---|
| Stok tidak akurat | Setiap perubahan stok tercatat dengan sumber dan waktu; stok sistem dan stok fisik bisa dicocokkan | [REKOMENDASI] |
| Transaksi sulit ditelusuri | Setiap pembayaran bisa dilacak ke work order, metode, dan petugas | [REKOMENDASI] |
| Owner tidak bisa lihat keuangan | Owner melihat omzet dan profit periode tertentu tanpa hitung manual | [REKOMENDASI] |
| Penerimaan kendaraan harus cepat | Batas waktu atau jumlah langkah penerimaan: ISI: | belum ditetapkan |

## 4. Fitur
Alur inti **[DIPUTUSKAN 2026-10-14]**: Nota servis (penerimaan) → Work order → Nota akhir dan pembayaran.
Alur aktif, status, pembatalan, dan pembayaran mengikuti CONTEXT §2.2
(keputusan 2026-11-04). Status pembayaran terpisah dari status pengerjaan SO.

| ID | Fitur | Kelompok | Peran | Status keputusan |
|---|---|---|---|---|
| F-01 | Login berbasis peran (username + password) | Inti | Semua | DIPUTUSKAN 2026-10-31 |
| F-02 | Customer dan kendaraan (CRUD, per plat nomor) | Inti | Owner, Teknisi, Kasir | Metaprompt; peran disesuaikan 2026-10-31 |
| F-03 | Registrasi kunjungan, lalu form Diagnosa & Estimasi terhubung | Inti | Registrasi: Owner/Teknisi/Kasir; diagnosa: Owner/Teknisi | DIPUTUSKAN 2026-11-04; CONTEXT §2.2 |
| F-04 | Master jasa (nama, deskripsi harga) dan suku cadang (nama, kode, harga, satuan, stok) | Inti | Owner (kelola, termasuk HPP); Teknisi/Kasir baca harga jual saat transaksi | Metaprompt; HPP Owner-only DIPUTUSKAN 2026-10-31; stok: lihat §6 |
| F-05 | Service Order: rincian disetujui, progres dan realisasi; pembatalan dengan biaya tetap ditagihkan | Inti | Owner, Teknisi; setelah Selesai hanya Owner dapat mengubah | DIPUTUSKAN 2026-11-04; CONTEXT §2.2 |
| F-06 | Invoice sebelum pembayaran; tunai/QRIS statis/transfer manual, langsung lunas tanpa DP/cicilan/tempo; cetak | Inti | Owner, Kasir | CONTEXT §2.2, revisi 2026-11-15; gateway ditunda |
| F-07 | Riwayat servis per pelanggan dan kendaraan | Inti | Owner, Teknisi, Kasir | Metaprompt; ASUMSI pelanggan sering kembali |
| F-08 | Dashboard Owner | Inti | Owner | Metaprompt |
| F-09 | Laporan transaksi/pendapatan per periode | Inti | Owner | Metaprompt; akses laporan TIDAK diwariskan ke Teknisi (handoff §4.2); lihat §6 |
| F-10 | Supplier, pembelian/stok masuk, pengeluaran | Tambahan (usulan tim) | Owner | Metaprompt; lihat §6 |
| F-11 | Perhitungan profit, peringatan stok menipis | Tambahan (usulan tim) | Owner | HPP otomatis dan laporan profit ditunda sesuai CONTEXT §2.4 (2026-11-11); status peringatan stok tetap usulan |
| F-12 | Autosave draf dan akses offline terbatas dengan sinkronisasi otomatis | Tambahan | Semua | DIPUTUSKAN (draf saja; bayar/stok/invoice wajib online) |
| F-13 | Estimasi itemized pada Diagnosa & Estimasi, persetujuan lisan, salin ke SO; invoice mengambil realisasi akhir | Inti | Teknisi (isi), Owner/Kasir (baca harga jual) | DIPUTUSKAN 2026-11-04; CONTEXT §2.2 |
| F-14 | Edit harga jual lokal per baris dokumen + log perubahan harga (log lengkap Owner-only) | Inti | Sesuai CONTEXT §2.1 dan §2.7; invoice draf hanya Owner | DIPUTUSKAN 2026-10-31; penyelarasan 2026-11-07 |
| F-15 | Invoice final terkunci; koreksi hanya Owner dengan alasan + riwayat revisi; kelebihan bayar/sisa tagihan dicatat terpisah dari riwayat pembayaran | Inti | Owner | DIPUTUSKAN 2026-10-31 |
| F-16 | Pencarian global (halaman, pelanggan/kendaraan, WO, invoice, jasa/part) dengan hasil terfilter peran; referensi visual `@shadcnuikit/command1` | Inti | Semua (hasil per peran) | DIPUTUSKAN 2026-10-31 |
| F-17 | Audit log (aksi, aktor, waktu, nilai lama→baru, alasan) | Inti | Owner | DIPUTUSKAN 2026-10-31 |
| F-18 | Reservasi part pada SO; tampilkan stok tercatat, direservasi, dan tersedia; pengeluaran stok saat invoice final terbit, bukan saat pembayaran | Inti | Owner, Teknisi, Kasir melihat jumlah; hak perubahan mengikuti dokumen terkait | DIPUTUSKAN 2026-11-06; CONTEXT §2.4; rancangan data di BSD §3.1 |

Penyerahan realisasi akhir F-05/F-13 ke antrean F-06 mengikuti CONTEXT §2.6.
Teknisi dapat menyerahkan SO Selesai, tanpa memperoleh hak revisi biaya terminal.
Revisi SO yang sedang mengantre memerlukan penarikan oleh Owner terlebih dahulu.
Hak harga invoice draf dan perlakuan total Rp0 mengikuti CONTEXT §2.7, menggantikan
izin draf Teknisi pada keputusan lama. Tidak menambah metode atau integrasi bayar.
Beranda peran Kasir dan layout POS mengikuti CONTEXT §2.8; transaksi tetap memakai
alur dan kewenangan F-05/F-06/F-14 yang sama.

## 5. Di luar cakupan
- Integrasi payment gateway ditunda ke pengembangan berikutnya. Lingkup sekarang
  mengikuti CONTEXT §2.2: tunai, QRIS statis dan rekening Owner; konfirmasi manual.
- Notifikasi ke pelanggan: belum diputuskan (lihat §6).
- ISI: lainnya

## 6. Asumsi, konflik, dan pertanyaan terbuka
| # | Hal | Dampak bila salah | Pemilik keputusan |
|---|---|---|---|
| 1 | **Stok suku cadang, laporan, notifikasi:** reservasi, visibilitas jumlah, dan pengeluaran saat invoice final sudah diputuskan (CONTEXT §2.3–§2.4). Lingkup pembelian, laporan, notifikasi, dan retur fisik tetap terbuka. | Rincian F-04, F-09, F-10, F-11 belum seluruhnya final | User |
| 2 | Urutan invoice sebelum bayar telah diputuskan; kebijakan koreksi/refund rinci tetap terbuka | Alur F-06 | User |
| 3 | ~~Harga: apakah Supervisor dan Kasir boleh melihat harga modal (HPP)?~~ **Terjawab 2026-10-31:** HPP hanya Owner; Supervisor dihapus (CONTEXT §2.1) | Hak akses, laporan profit | Selesai |
| 4 | Kartu: lewat mesin EDC terpisah atau gateway? | F-06 | User |
| 5 | Layar prioritas urut (usulan agent: nota servis, work order, riwayat kendaraan) | Urutan IPD | User |
| 6 | Jumlah pengguna dan cabang | Skala TRD | User |

## 7. Berkas terkait
- AFD: `../AFD/afd.md`
- TRD: `../TRD/trd.md`
- Konteks keputusan: `../CONTEXT.md`
