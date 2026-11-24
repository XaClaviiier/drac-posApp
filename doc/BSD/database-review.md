# Database POS — DB-02, draf review seluruh sistem

Status: **DRAF UNTUK REVIEW**, 2026-11-17. User memilih cakupan seluruh sistem,
bukan hanya DB-01. Ini bukan persetujuan kebijakan bisnis baru, bukan migrasi
Laravel dan belum diimpor ke database aplikasi.

## Berkas dan penggunaan

- [pos-schema.sql](pos-schema.sql): sumber fisik draf, seluruh kolom, tipe,
  PK, FK, UNIQUE, CHECK, indeks, proyeksi dan seed tiga peran.
- [erd.md](erd.md): ERD fisik dipisahkan menurut modul; kolom relasi memakai
  nama yang sama dengan SQL. FK komposit dan pointer revisi ikut digambar.
- BSD tetap titik masuk dokumentasi. DB-01 di `bsd.md` adalah rancangan awal
  pelanggan–layanan; DB-02 melengkapinya dan menambahkan usulan teknis di bawah.
  Tidak menyalin daftar kolom SQL ke dokumen ini.

Target sintaks adalah **MySQL 8.4, InnoDB, utf8mb4**. Ini usulan versi teknis,
bukan perubahan keputusan MySQL pada CONTEXT. Pemeriksaan executable lokal
menemukan **MariaDB 10.4.32** pada XAMPP, bukan MySQL. Jangan menyamakan keduanya.
Kompatibilitas MySQL aktual tetap harus diuji sebelum migrasi produksi.

SQL tidak memuat `CREATE DATABASE`, `USE`, penghapusan, kredensial atau data bisnis
contoh. Operator harus memilih **database baru yang kosong**. SQL sengaja tidak
memakai `IF NOT EXISTS`: struktur lama yang tidak cocok tidak boleh dilewati diam-diam.
DDL bukan transaksi rollback penuh; impor dapat berhenti setelah membuat sebagian
struktur. Jangan mengimpor ulang atau menggunakannya pada database aplikasi existing.

Setelah database kosong dibuat dan diizinkan secara terpisah, pola impornya:

```sh
mysql --host=127.0.0.1 --user=NAMA_USER --password NAMA_DATABASE_BARU < doc/BSD/pos-schema.sql
```

Masukkan password pada prompt, bukan argumen perintah. Contoh ini bukan perintah
yang telah dijalankan pada database pengguna. Tidak ada perubahan skema/data
existing maupun pemasangan dependency.

## Lingkup yang disertakan

Akses pengguna dan tabel izin paket; pelanggan, kendaraan dan snapshot kunjungan;
revisi registrasi; katalog jasa/part; estimasi dan SO dengan baseline/revisi/item
stabil; Teknisi setara; event antrean kasir; invoice/revisi/pembayaran; tujuan
QRIS/transfer; supplier/pembelian/diskon/penerimaan bertahap/pembayaran supplier;
retur supplier dan penerimaan pengganti/pengembalian uang; retur pelanggan,
pemeriksaan part dan refund; saldo stok awal, reservasi, blokir dan ledger stok;
pengeluaran, audit, idempotensi dan counter nomor dokumen.

Dashboard/laporan/pencarian global merupakan pembacaan data sumber, bukan tabel
saldo/laporan/riwayat kedua. Draf offline berada pada IndexedDB/Dexie; tidak membuat
salinan JSON server sebagai sumber kebenaran kedua. Konflik memakai versi master
atau nomor revisi dokumen. Dokumen dan transaksi keuangan/stok resmi tetap online.

**Tidak diaktifkan:** HPP rata-rata otomatis, laporan profit, gateway, multi-cabang,
DP/cicilan/tempo pelanggan. Nilai harga beli dan saldo awal tetap dicatat, tanpa
menghasilkan klaim profit. Tidak ada QRIS/rekening, identitas bengkel, harga master
atau akun login rekaan.

## Usulan teknis tambahan — belum menjadi keputusan bisnis final

1. UUID bisnis memakai `CHAR(36)` ASCII biner; waktu UTC `DATETIME(6)`. Kapasitas
   uang/qty mengikuti usulan DB-01. Uang selalu desimal tetap, tidak float.
   Validasi input lebih dari tiga desimal dilakukan sebelum konversi SQL; tipe
   DECIMAL sendiri dapat membulatkan nilai sebelum CHECK diperiksa.
2. Identitas pengguna UUID; ID tabel internal paket roles/permissions/token
   menggunakan BIGINT. Nama tabel/pivot mengikuti Spatie/Sanctum. Integrasi paket
   harus mengatur UUID morph key dan model secara eksplisit. Relasi polimorfik
   `model_type/model_id`, `tokenable_type/tokenable_id` dan subject audit tidak
   dapat dijamin FK ke satu tabel. Hanya model User yang digunakan tahap ini.
   Pilihan sesi SPA-cookie/API-token belum diputuskan; tabel token tidak berarti
   aplikasi telah memilih token sebagai cara login. Penyimpanan sesi dapat memakai
   driver file; perubahan ke database session harus memakai migrasi paket yang sesuai.
3. Koreksi registrasi mempunyai snapshot revisi lengkap. Versi pertama dicatat
   ketika membuat registrasi; koreksi berikutnya membutuhkan alasan. Invoice
   menyimpan identitas sendiri dan merujuk revisi registrasi sumber. Ini memperkuat
   audit; tidak memberi izin koreksi baru atau mengubah master otomatis.
4. Penyerahan/penarikan antrean berupa event berurutan yang mengikat revisi SO.
   Penarikan menunjuk event antrean sebelumnya. Tidak ada status antrean mutable
   kedua. Pointer invoice terbit menunjuk revisi penerbitan yang tetap; pointer
   aktif boleh bergerak ke revisi koreksi. Hanya satu invoice per SO.
5. Pembayaran pelanggan aktual disimpan append-only; satu pelunasan per revisi
   invoice. Pembayaran berikutnya hanya untuk seluruh sisa setelah koreksi sah,
   bukan cicilan normal. QRIS/transfer mewajibkan pemeriksa dana dan snapshot tujuan.
   Tunai menyimpan nominal yang melunasi tagihan terpisah dari uang diterima;
   kembalian adalah selisihnya, bukan uang masuk tambahan. Invoice nol tanpa payment.
6. **Usulan perlakuan retur/refund untuk review:** kredit invoice dicatat terpisah
   dari pembayaran/refund aktual. Kredit akibat retur menurunkan hak tagih; refund
   tanpa kredit hanya mengembalikan kelebihan bayar. Tanpa pemisahan ini, refund
   atas layanan gagal dapat keliru dibaca sebagai pelanggan berutang lagi.
   `invoice_credit_notes` merupakan catatan internal, bukan otomatis perubahan nota
   pelanggan atau aturan pajak. Satu otorisasi refund dilunasi satu kali; otorisasi
   lain dapat dicatat untuk kasus berbeda. Besaran, batas kumulatif, pelaksana,
   cara penyajian dokumen pelanggan dan aturan akuntansi **harus disetujui sebelum
   endpoint retur/refund diaktifkan**. Tidak ada refund otomatis.
7. Retur supplier memilih penerimaan asal dan memakai harga beli bersih snapshot.
   Satu dokumen retur memakai satu bentuk penyelesaian: pengganti, pengurangan
   utang atau uang kembali; kasus campuran dipisah menjadi dokumen berbeda.
   Ini usulan pemodelan, bukan batas bisnis yang telah disahkan. Pengurangan utang
   memiliki waktu penerapan; refund supplier hanya dicatat saat uang masuk nyata.
   Pengganti boleh diterima bertahap, belum menjadi stok selama belum diterima.
8. Qty penerimaan dan nilai bersih per penerimaan menyimpan alokasi diskon pembelian
   yang telah dikonfirmasi. Sisa pembulatan dialokasikan pada penerimaan terakhir
   agar jumlah nilai penerimaan tepat sama dengan nilai baris pembelian. Aturan
   pelunasan sebelum penerimaan lengkap dan revisi pembelian perlu review.
9. Ledger stok mempunyai satu sumber bertipe per baris, unik per sumber untuk
   mencegah pengeluaran/penerimaan ganda. Satu receipt item/return item mewakili satu
   kejadian fisik; kejadian berikutnya memakai baris/dokumen baru. Saldo awal satu
   kali per part; koreksi saldo awal belum diberikan endpoint dalam draf ini.
10. Qty blokir mencakup rusak dan karantina. Barang pelanggan yang kembali masuk
    stok fisik sekaligus diblokir sampai diperiksa; rusak tetap diblokir. Event
    perubahan blokir menjadi jejak audit. Ketika barang dikirim balik ke supplier,
    stok tercatat turun dan blokir terkait dilepas secara atomik. Qty yang sudah
    direservasi tidak boleh sekaligus tetap dihitung sebagai blokir: transaksi
    harus menyelesaikan realokasi/konflik terlebih dahulu, bukan menghitung ganda.
11. Idempotency key unik per aktor, operasi dan key; payload diikat hash. Penyelesaian
    dan hasil request harus commit bersama perubahan bisnis. Tidak menetapkan
    penghapusan/masa retensi otomatis. Counter nomor disediakan tanpa mengarang
    format nomor SO/invoice yang belum diputuskan.
12. Pembayaran supplier satu kali per pembelian dan tanpa tanggal jatuh tempo.
    Pengeluaran dicatat ketika benar-benar dibayar; ongkir dapat terhubung ke
    pembelian, tetapi tidak ditambahkan ke harga part. Kanal cash/transfer untuk
    supplier/refund adalah usulan teknis awal; metode lainnya perlu review.

## Apa yang dijamin SQL dan apa yang wajib dilakukan server

FK/UNIQUE menjaga identitas, sumber dokumen, sebagian hubungan lintas agregat,
satu estimasi/SO/invoice per kunjungan/tahap, keunikan plat serta duplikat sumber
stok. CHECK membatasi nilai dasar, satuan/skala, qty positif, subtotal bulat,
jenis event/metode dan pasangan field tertentu. Telepon pelanggan **tidak unik**.
Semua FK memakai RESTRICT; tidak ada penghapusan cascade riwayat.

DDL **tidak** mengimplementasikan otorisasi, immutability/append-only, transaksi
bisnis, urutan event atau semua invariant agregat. Layanan Laravel wajib:

- Mengunci head/part dan memeriksa versi sebelum revisi; pointer bootstrap NULL
  wajib terisi sebelum commit. Histori lama tidak boleh diubah/dihapus oleh writer.
- Memastikan baseline disetujui, sumber item berasal dari revisi yang benar,
  katalog sesuai anchor (termasuk jasa), snapshot awal tidak berubah, revisi urut,
  satuan katalog benar, serta identitas registrasi/invoice sesuai kunjungan.
- Memeriksa peran aktif, transisi sah, minimal satu Teknisi sebelum mulai/lanjut,
  persetujuan biaya tambahan, alasan, master nonaktif dan penguncian terminal.
- Memastikan event antrean bergantian, penarikan hanya terhadap queued aktif,
  draf stale ditinjau Owner, penerbitan tepat satu kali, serta revisi `issued`
  benar-benar yang dirujuk pointer. Koreksi tidak membuka SO final.
- Memeriksa invoice final sebelum bayar/kredit/refund; membayar seluruh sisa
  positif, menolak pembayaran nol/ulang, menolak kredit/refund berlebih, memastikan
  tujuan/metode/pemeriksa dana sesuai, serta mempertahankan pembayaran historis.
- Membatasi total penerimaan/retur/pengganti terhadap sumber dan satuan; memastikan
  penerimaan hanya untuk pembelian terkonfirmasi dan nilai/diskon tidak dihitung
  dua kali. Nilai retur tidak boleh melebihi hak dari penerimaan asal.
- Memastikan retur supplier/pembayaran/credit settlement konsisten, pengurangan
  utang tidak pada pembelian lunas, uang kembali tidak menduplikasi kredit utang,
  dan pembayaran supplier seluruh sisa positif. Pembelian dengan sisa nol tidak
  membutuhkan pembayaran nol.
- Menghitung stok dari ledger; mengecek tersedia di bawah lock part yang sama;
  penerbitan invoice, pergerakan stok dan konversi reservasi harus satu transaksi.
  View tidak memotong stok negatif menjadi nol: keadaan salah harus terlihat.
  Pembayaran/koreksi harga tidak mengeluarkan stok lagi. Pembukaan stok, penerimaan,
  retur dan blokir harus atomik dengan ledger dan auditnya.
- Membatasi akses harga beli/pengeluaran/audit/kredit/refund pada Owner sesuai
  keputusan bisnis. View finansial tidak boleh langsung diberikan ke semua peran.
  Hasil pencarian global wajib difilter server, bukan hanya disembunyikan di UI.

Endpoint yang membutuhkan kebijakan belum final tidak boleh diaktifkan hanya
karena tabel sudah tersedia. Persetujuan draft fisik tidak menyelesaikan aturan
transisi diagnosa, pencairan refund, kriteria garansi, format nomor, deaktivasi
master pada pekerjaan berjalan atau retensi audit.

## Verifikasi

Bukti aktual: [database-verification.json](database-verification.json).
File SQL final berhasil diimpor ke database kosong pada instance privat
MariaDB 10.4.32: **53 tabel, 122 FK dan empat view**. Sebanyak **60 pemeriksaan
SQL/struktur** lulus, mencakup graph kunjungan–invoice, telepon sama, plat unik,
snapshot, qty/satuan/pembulatan, koreksi, pelunasan, refund, stok, retur, utang,
rollback dan idempotensi. Inventaris tabel/kolom dan FK aktual cocok dengan ERD.
Sebelas diagram Mermaid berhasil dirender di Chrome tanpa error parser/render
atau page error. Ini bukan klaim semua jalur bisnis atau seluruh visual telah diuji.

Review independen fisik menemukan CHECK idempotensi yang menerima status respons
NULL; field wajib non-NULL pada state completed telah ditambahkan dan regresinya
lulus. Review finansial tidak menemukan inkonsistensi penting. Dua kesalahan
fixture/query pengujian beserta pemulihannya dicatat pada bukti, bukan disembunyikan
sebagai keberhasilan percobaan awal.

Instance SQL sementara dihentikan dengan exit 0, listener ditutup, serta data
uji dan halaman renderer sementara dihapus. Database aplikasi existing tidak
diubah. MySQL 8.4 aktual, integrasi Laravel/paket, concurrency, otorisasi dan
pemulihan offline **belum diuji**; semuanya gate terpisah sebelum data nyata.

## Referensi teknis

- [MySQL 8.4 CHECK constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html)
- [Spatie: UUID/ULID dan perubahan morph key](https://spatie.be/docs/laravel-permission/v6/advanced-usage/uuid)
- Aturan bisnis aktif: [CONTEXT](../CONTEXT.md); arsitektur: [TRD](../TRD/trd.md).
  Versi paket belum dikunci; dokumentasi Spatie v6 menjadi referensi bentuk tabel,
  bukan bukti kompatibilitas paket tersebut dengan Laravel 13.
