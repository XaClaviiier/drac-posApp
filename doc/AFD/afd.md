# AFD: App Flow Documentation — POS Bengkel AC Mobil

Dokumen ini menjawab: **bagaimana pengguna bergerak di dalam aplikasi.**
Bergantung pada PRD (`../PRD/prd.md`). Fitur yang tidak ada di PRD tidak muncul di sini.

Label: **[DIPUTUSKAN]** keputusan user · **[ASUMSI]** belum dipastikan · **[REKOMENDASI]** usulan agent,
belum disetujui · `ISI:` belum diputuskan, jangan dikarang.

Sumber: `../CONTEXT.md` §2, §4, §7; `../metaprompt-pembentukan-sistem.md` (Alur inti, Role).

**Prinsip alur (CONTEXT §2, §7) [DIPUTUSKAN]:** dipakai sambil berpindah dan oleh orang awam, jadi satu layar
mengerjakan satu hal, target sentuh besar, dan alur penerimaan kendaraan tidak boleh panjang.

---

## 1. Peta halaman
Daftar halaman diturunkan dari modul peran di PRD §2. Nama dan jumlah layar final belum diputuskan.
Layar prioritas urut (CONTEXT §4): `ISI:` (usulan agent **[REKOMENDASI]**: 1 Nota servis, 2 Work order, 3 Riwayat kendaraan per plat nomor).

| ID | Halaman | Peran | Prioritas | Status |
|---|---|---|---|---|
| P-01 | Login (username + password; demo journey per peran) | Semua | Inti | [DIPUTUSKAN 2026-10-31] |
| P-02 | Registrasi kendaraan: plat, nama, keluhan, telepon; alamat opsional | Owner, Teknisi, Kasir | 1 (paling kritis) | [DIPUTUSKAN 2026-11-04] |
| P-03 | Service Order: salinan estimasi disetujui, realisasi, dan progres | Owner, Teknisi; SO Selesai hanya Owner dapat mengubah | 2 | [DIPUTUSKAN 2026-11-04] |
| P-04 | Penerbitan invoice, kemudian pembayaran lunas | Owner, Kasir | Inti | Tunai/QRIS statis/transfer manual; CONTEXT §2.2 |
| P-05 | Riwayat servis per plat nomor / pelanggan | Owner, Teknisi, Kasir | 3 | [ASUMSI] pelanggan sering kembali |
| P-06 | Customer dan kendaraan (daftar, ubah) | Owner, Teknisi, Kasir | Inti | PRD F-02 |
| P-07 | Master jasa dan suku cadang | Owner (kelola + HPP); Teknisi/Kasir baca harga jual saat transaksi | Inti | PRD F-04; CONTEXT §2.1 |
| P-08 | Dashboard Owner | Owner | Inti | PRD F-08 |
| P-09 | Laporan | Owner | ISI: | Bergantung keputusan PRD §6 #1 |
| P-10 | Supplier, pembelian, pengeluaran | Owner | ISI: | Bergantung keputusan PRD §6 #1 |
| P-11 | Pengguna dan peran | Owner | Inti | [ASUMSI] dari "akses penuh Owner" |
| P-12 | Pencarian global (halaman, pelanggan/kendaraan, WO, invoice, jasa/part; hasil terfilter peran) | Semua | Inti | [DIPUTUSKAN 2026-10-31]; referensi `@shadcnuikit/command1` |
| P-13 | Audit log + log perubahan harga lengkap | Owner | Inti | [DIPUTUSKAN 2026-10-31] |
| P-14 | Koreksi invoice final (alasan, nilai sebelum/sesudah, riwayat revisi) | Owner | Inti | [DIPUTUSKAN 2026-10-31] |
| P-15 | Diagnosa & Estimasi terhubung registrasi | Owner, Teknisi | Inti | [DIPUTUSKAN 2026-11-04] |

## 2. Alur utama

**Revisi aktif 2026-11-04:** keputusan bersumber pada CONTEXT §2.2. Urutan saat ini:

1. Teknisi/Kasir meregistrasi kunjungan: plat, nama, keluhan, telepon; alamat opsional.
2. Teknisi membuat Diagnosa & Estimasi dari registrasi, tanpa entry ulang identitas.
3. Pelanggan menyetujui secara lisan; rincian estimasi disalin ke Service Order.
4. Teknisi mengelola progres dan realisasi SO; estimasi awal dan perubahan tetap terlacak.
5. SO Selesai hanya dapat diubah Owner. SO Dibatalkan dengan biaya dapat ditagihkan
   setelah rincian aktual ditetapkan; kunjungan berikutnya memakai SO baru.
6. Kasir menerbitkan invoice dari realisasi akhir, lalu menerima pembayaran penuh
   melalui tunai/QRIS statis/transfer manual. Tidak ada DP/cicilan/tempo.

Status pekerjaan dan pembayaran terpisah. Daftar status awal/transisi diagnosa,
hak edit invoice draf, dan perilaku refund rinci tetap belum diputuskan.
Fase prototype browser dan cakupan setiap irisan bersumber pada IPD WEB-01.
Urutan data: Customer → Kendaraan → Registrasi → Diagnosa & Estimasi → Service Order
→ Invoice → Pembayaran → Riwayat servis.

### 2.0 Login **[DIPUTUSKAN 2026-10-31]**
1. Username + password (bukan OTP/magic link).
2. Setelah masuk, aplikasi menampilkan tujuan sesuai peran: Owner → dashboard;
   Kasir → kasir/transaksi; Teknisi → papan tugas. Navigasi dan hasil pencarian
   difilter peran (CONTEXT §2.1).
3. Sesi berakhir → kembali ke login. Prototype FigCraft mensimulasikan ini dengan
   tombol demo per peran; autentikasi nyata adalah pekerjaan backend (TRD §4).

### 2.1 Penerimaan kendaraan
1. Teknisi/Kasir mencatat field yang diputuskan pada CONTEXT §2.2.
2. Simpan registrasi kunjungan. Plat sama dapat muncul pada kunjungan berbeda.
3. Teknisi membuat Diagnosa & Estimasi setelah pemeriksaan lanjutan. Diagnosa
   tidak diwajibkan saat registrasi awal.
Batas jumlah langkah atau waktu: `ISI:`. Pencarian/pemakaian ulang master pelanggan
merupakan pekerjaan fase berikutnya, bukan klaim Fase 1.

### 2.2 Diagnosa & Estimasi, lalu Service Order
1. Teknisi mencatat temuan, rekomendasi dan estimasi itemized di form diagnosa.
2. Qty, subtotal baris dan pembulatan total mengikuti CONTEXT §2.5; total menjumlahkan
   subtotal baris yang sudah dibulatkan.
3. Pelanggan menyetujui secara lisan; Teknisi melanjutkan ke SO tanpa entry ulang.
4. SO menyimpan salinan yang disetujui dan rincian realisasi. Penambahan/pengurangan
   dilakukan di SO dengan riwayat, tanpa menimpa estimasi awal atau harga master.
5. Tambahan biaya meminta persetujuan pelanggan; tidak ada batas nominal otomatis.
6. Teknisi mengelola progres; setelah Selesai hanya Owner dapat mengubah SO.
7. Pembatalan mempertahankan biaya aktual yang ditagihkan. Kunjungan setelah
   pembatalan memakai SO baru dengan hubungan ke riwayat sebelumnya.

Prototype 3A kini menguji progres sebelum realisasi: SO baru Belum dimulai, pilih
teknisi lalu Mulai pengerjaan. Pilihan transisi demo, pembukaan kembali Owner,
penundaan/pembatalan beralasan dan riwayat bersumber pada IPD WEB-03A. Status
Selesai/Dibatalkan pada irisan ini belum memfinalkan biaya atau mengirim invoice.
Realisasi tetap 3B, penyerahan ke kasir 3C; tidak menganggap total estimasi sebagai
tagihan pembatalan otomatis.

### 2.3 Kasir, invoice dan pembayaran
Penyerahan dan penarikan antrean mengikuti CONTEXT §2.6. Setelah realisasi tersimpan
dan pekerjaan ditutup, petugas menyerahkan SO secara eksplisit. Selama mengantre,
progres dan realisasi terkunci. Owner menarik dengan alasan sebelum merevisi;
perubahan sesudah penarikan tidak otomatis menyerahkan kembali SO.

1. SO Selesai atau Dibatalkan dengan biaya masuk antrean kasir setelah realisasi final.
2. Kasir/Owner menerbitkan invoice berdasarkan realisasi SO sebelum pembayaran.
3. Pembayaran langsung lunas melalui tunai/QRIS statis/transfer manual. Tidak ada
   DP, cicilan atau tempo. QRIS/rekening Owner ditampilkan sebagai tujuan bayar;
   Kasir/Owner memeriksa dana masuk sebelum konfirmasi manual. Nominal kurang
   tidak boleh ditandai Lunas. Gateway ditunda (CONTEXT §2.2).
4. Pengeluaran stok terjadi saat invoice final diterbitkan, bersamaan dengan
   penyelesaian reservasi (CONTEXT §2.4, 2026-11-06). Invoice draf belum mengurangi
   stok tercatat; pembayaran tidak menguranginya lagi. Ini kontrak produksi,
   belum implementasi stok pada prototype.
5. Cetak atau simpan PDF. Cara cetak ponsel belum diputuskan (TRD §5).

### 2.3.1 Reservasi part pada SO **[DIPUTUSKAN 2026-11-06]**

1. Penambahan part ke SO dikirim ke server untuk memvalidasi ketersediaan dan
   mencatat reservasi di MySQL. Draf offline belum menjamin alokasi part.
2. Setelah server mengonfirmasi, interface menampilkan stok tercatat, direservasi,
   dan tersedia melalui API. Jumlah terlihat oleh Owner, Teknisi, dan Kasir;
   HPP tetap hanya Owner.
3. Pelepasan part sebelum dipakai melepaskan reservasinya. Part yang sudah dipakai
   pada SO dibatalkan tetap mengikuti realisasi; tidak otomatis kembali tersedia.
4. Invoice final mengonversi reservasi menjadi pengeluaran stok satu kali.
   Rancangan data dan invarian transaksi dirujuk di BSD §3.1.

### 2.4 Invoice final dan koreksi **[DIPUTUSKAN 2026-10-31]**
1. Invoice draf: harga jual lokal hanya disesuaikan Owner (CONTEXT §2.7, menggantikan
   izin lama Teknisi). Setelah difinalkan, invoice **terkunci** walau belum lunas; Teknisi
   dan Kasir tidak dapat mengoreksi.
2. Koreksi hanya oleh Owner, wajib alasan; simpan nilai sebelum/sesudah, aktor, waktu,
   dan riwayat revisi. Dokumen asli dan jejak pembayaran tidak ditimpa diam-diam.
3. Koreksi **tidak menulis ulang uang yang sudah diterima**. Bandingkan total baru
   dengan pembayaran bersih tercatat: total lebih rendah menghasilkan kelebihan
   bayar, total lebih tinggi menghasilkan sisa tagihan, sama berarti lunas.
   Selisih ditampilkan sebagai catatan terpisah. Refund nyata adalah
   pergerakan uang yang dicatat terpisah; tidak ada refund/pembatalan pembayaran
    otomatis. Workflow refund final belum diputuskan (handoff §6.4).

Invoice final Rp0 memakai status Lunas sesuai CONTEXT §2.7, tanpa membuat pembayaran.

#### Ekstensi demo WEB-04

Beranda Kasir berupa POS (CONTEXT §2.8): antrean menggabungkan SO siap ditagih,
invoice draf dan invoice final dengan sisa positif. Memilih SO menampilkan preview
tanpa write; membuat draf tetap aksi eksplisit. Sesudah pembayaran, detail/nota
yang baru lunas tetap terbuka meskipun baris keluar dari antrean default. Pindah
transaksi mengikuti dirty guard invoice existing dan tidak memilih transaksi lain
otomatis. Draf kedaluwarsa ditandai perlu pemeriksaan Owner.

Kasir/Owner membuat satu invoice draf dari penyerahan SO yang masih aktif.
Perubahan harga lokal invoice tidak mengubah realisasi SO atau katalog. Pada demo,
item/qty tidak diedit di invoice: Owner menarik SO sebelum invoice final untuk
merevisi realisasi, lalu menyerahkannya ulang. Draf lama menjadi kedaluwarsa;
Owner memuat ulang realisasi baru secara eksplisit dengan alasan, tanpa menghapus
riwayat draf. Invoice final mempertahankan lock SO; koreksi berikutnya hanya harga
invoice oleh Owner. Refund/retur fisik tetap belum diimplementasikan.

Pembayaran demo mencatat sisa tagihan penuh: tunai menghitung kembalian dari uang
diterima, transfer manual meminta referensi. Gateway pada demo lama adalah artefak
historis; konsep baru menampilkan QRIS statis dan rekening Owner sesuai CONTEXT §2.2.
Koreksi yang menaikkan total dapat dibayar sebesar seluruh sisa baru, bukan cicilan
normal. Kelebihan bayar ditampilkan terpisah; uang tercatat tidak ditulis ulang.
Nota cetak browser hanya memakai invoice final tersimpan, bertanda simulasi.

### 2.5 Pencarian global **[DIPUTUSKAN 2026-10-31]**
1. Pemicu: kontrol pencarian di sidebar (bukan hanya plat nomor).
2. Kelompok hasil: halaman, pelanggan/kendaraan, work order, invoice, jasa/part —
   hanya entitas yang ada dan diizinkan peran pengguna.
3. Nominal terbatas (HPP, pengeluaran, profit) tidak boleh muncul di snippet, total,
   tautan, atau ekspor hasil pencarian. Untuk Teknisi, harga jual hanya pada konteks
   transaksi yang diizinkan.
4. State yang dibutuhkan: awal (saran), hasil, tanpa hasil, memuat, error, dan baris
   terpilih; baris hasil membuka destinasi yang relevan.
5. Referensi visual: `@shadcnuikit/command1` (struktur diadaptasi ke token POS;
   bukan pemasangan komponen React).

## 3. Status dan transisi
| Objek | Status | Aturan |
|---|---|---|
| SO | Dalam Pengerjaan / Ditunda / Selesai / Dibatalkan | Status awal dan transisi rinci belum difinalkan; CONTEXT §2.2 |
| SO Selesai | Hanya Owner dapat mengubah | Hak Teknisi berhenti setelah Selesai |
| Invoice | Belum Lunas / Lunas | Pembayaran penuh oleh Kasir/Owner; QRIS/transfer dikonfirmasi setelah dana masuk diperiksa |
| Pembatalan | Pertahankan realisasi biaya; terbitkan invoice bila ada biaya | Pelanggan kembali memakai SO baru |

## 4. Kondisi khusus per halaman
Setiap halaman perlu: kosong, memuat, error, offline, konflik sinkron. Rincian per halaman: `ISI:`.

Aturan offline **[DIPUTUSKAN 2026-10-14]**: offline terbatas pada draf Customer, Kendaraan, Diagnosa, Work order.
Pembayaran, perubahan stok, dan invoice resmi wajib online. Layar yang butuh online harus menjelaskan
mengapa aksi dinonaktifkan, bukan sekadar abu-abu.

| Kondisi | Perilaku yang diwajibkan CONTEXT §7 |
|---|---|
| Status penyimpanan | Selalu tampil salah satu: **Tersimpan**, **Menyimpan**, **Belum tersinkron** |
| Konflik (dua perangkat mengubah WO yang sama) | Perubahan membawa nomor versi; bila bentrok tampilkan pilihan ke pengguna, jangan menimpa diam-diam. **[REKOMENDASI]** dari CONTEXT §3.1 |
| Data tidak boleh hilang diam-diam | Wajib |
| Status tidak hanya dibedakan warna | Sertakan teks atau ikon |
| Animasi | Tidak boleh menunda atau menghalangi input |

## 5. Autosave
**[ASUMSI]** (CONTEXT §3): draf tersimpan setiap ada perubahan tanpa menekan tombol simpan, dan aman saat koneksi putus.
Pemicu simpan (tiap ketikan atau jeda tertentu): `ISI:`.

## 6. Aksi yang tidak bisa dibatalkan
Wajib konfirmasi (CONTEXT §7) **[DIPUTUSKAN]**: hapus work order, batalkan pembayaran.
Teks konfirmasi per aksi: `ISI:`. Aksi lain yang tergolong tak terbalik: `ISI:`.

## 7. Pertanyaan terbuka
| # | Pertanyaan | Mempengaruhi |
|---|---|---|
| 1 | Daftar layar prioritas yang final | §1, IPD |
| 2 | Keputusan stok, laporan, notifikasi (PRD §6 #1) | P-09, P-10 |
| 3 | Siapa menggeser tiap status WO, dan aturan pembatalan | §3 |
| 4 | Teks konfirmasi dan aturan batal pembayaran | §6 |

## 8. Berkas terkait
- PRD: `../PRD/prd.md` · TRD: `../TRD/trd.md` · BSD: `../BSD/bsd.md` · DBD: `../DBD/dbd.md`
