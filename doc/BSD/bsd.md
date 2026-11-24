# BSD: Backend Schema Documentation — POS Bengkel AC Mobil

Dokumen ini menjawab: **data apa yang disimpan dan API apa yang tersedia.**
Satu-satunya sumber kebenaran untuk skema tabel dan kontrak API. Dokumen lain
hanya menautkan ke sini.

Bergantung pada AFD dan TRD.

Sumber awal: `../metaprompt-pembentukan-sistem.md` (Fitur, Aturan Arsitektur 3–10).

---

## DB-02 — SQL dan ERD seluruh sistem [DRAF UNTUK REVIEW 2026-11-17]

User memilih cakupan seluruh sistem sebagai draf review, bukan hanya DB-01.
Definisi fisik lengkap bersumber pada [pos-schema.sql](pos-schema.sql); relasinya
ada pada [erd.md](erd.md). [database-review.md](database-review.md) mencatat
usulan teknis tambahan, batas penegakan SQL/server, cara penggunaan yang aman,
dan hasil verifikasi. Tabel/kolom tidak disalin ulang ke bagian DB-01 di bawah.

DB-01 tetap menjadi konteks rancangan awal pelanggan–layanan. DB-02 melengkapinya
dengan skema dependensi dan modul lain; belum mengesahkan kebijakan bisnis yang
terbuka atau menyatakan database siap produksi. Database aplikasi existing tidak
diubah. HPP otomatis, profit dan gateway tetap ditunda sesuai CONTEXT.

Implementasi parsial pertama berada di [AUTH-01](auth-01.md): akun UUID,
Spatie permission, sesi cookie Sanctum dan audit autentikasi. Kontrak tersebut
menautkan migration aktif dan endpoint nyata; SQL DB-02 tetap draf seluruh
sistem, bukan migration yang diimpor otomatis pada aplikasi.


## 1. Entitas dan relasi

### 1.1 DB-01 — pelanggan dan layanan [DRAF UNTUK REVIEW 2026-11-11]

Dasar keputusan bisnis: CONTEXT §2.1–§2.7, termasuk keputusan terbaru HPP ditunda
pada §2.4. Tipe, kapasitas, nama tabel dan strategi revisi di bawah adalah
**usulan teknis**, belum persetujuan skema fisik dan belum migrasi produksi.
Diagram ini hanya mencakup irisan pelanggan–layanan, bukan seluruh database.

```text
customers 1 ── 0..N visit_registrations 0..N ── 1 vehicles
vehicles 1 ── 0..N vehicle_plate_changes
visit_registrations 1 ── 0..1 diagnosis_estimates
diagnosis_estimates 1 ── 1..N diagnosis_estimate_revisions
diagnosis_estimates 1 ── 0..N diagnosis_estimate_items (identitas baris tetap)
diagnosis_estimate_revisions 1 ── 0..N diagnosis_estimate_revision_items
diagnosis_estimate_items 1 ── 0..N diagnosis_estimate_revision_items
visit_registrations 1 ── 0..1 service_orders
diagnosis_estimate_revisions 1 ── 0..1 service_orders (baseline disetujui)
service_orders 1 ── 1..N service_order_revisions
service_orders 1 ── 0..N service_order_items (identitas baris tetap)
service_order_revisions 1 ── 0..N service_order_revision_items
service_order_items 1 ── 0..N service_order_revision_items
service_order_revisions 1 ── 0..N service_order_revision_technicians 0..N ── 1 users*
```

`users*`, `services*`, dan `spare_parts*` merupakan dependensi luar irisan, dengan
nama sementara sampai skema autentikasi/katalog dirancang. Bukan tabel baru yang
sudah lengkap di dokumen ini. Relasi item ke katalog dijelaskan di §2.8/§2.12.
Kardinalitas revisi minimal satu berlaku setelah transaksi pembuatan commit.
Minimal satu Teknisi dipilih sebelum pengerjaan dimulai, tanpa hierarki Teknisi
utama/anggota; SO Belum dimulai boleh tanpa penugasan (§3.6).

Tidak ada hubungan kepemilikan permanen pelanggan pada kendaraan. Satu pelanggan
dapat datang dengan beberapa kendaraan, satu kendaraan dapat dibawa pelanggan
berbeda; hubungan nyata tersimpan pada setiap registrasi. SO lanjutan dapat
menunjuk SO sebelumnya tanpa memakai ulang registrasi lama.

### 1.2 Batas dengan irisan berikutnya

- Invoice kelak memakai `UNIQUE(service_order_id)` dan merujuk revisi realisasi
  yang diserahkan; tabel invoice/pembayaran/refund belum dirancang di DB-01.
- Reservasi/mutasi stok kelak merujuk identitas item SO tetap, bukan posisi baris
  atau ID snapshot yang berganti. Pengeluaran stok tetap saat invoice final.
- Penyerahan/penarikan antrean kelak mengikat revisi SO tertentu. Tidak membuat
  flag antrean/invoice terpisah yang menjadi sumber kebenaran kedua pada SO.
- Pembelian, retur, saldo stok awal dan autentikasi/katalog menjadi irisan berikutnya.
  HPP otomatis/profit tidak ditambahkan pada DB-01. Kontrak JSON demo §3.2–§3.5
  dipertahankan sebagai kontrak prototype, bukan DDL produksi.

## 2. Tabel
Nama tabel/kolom: bahasa Inggris. Uang: integer rupiah atau decimal, tidak pernah float.

### 2.1 Konvensi fisik usulan DB-01

Setiap tabel di §2.2–§2.14 memiliki `id UUID PK`; definisi alias berikut adalah
bagian skema setiap tabel, bukan tipe SQL baru. `—` berarti tanpa default, nilai
wajib disuplai server (ID draf boleh berasal dari klien lalu divalidasi).

| Alias/kolom bersama | Tipe fisik usulan | Null? | Default | Aturan |
|---|---|---|---|---|
| UUID / `id` | CHAR(36), ASCII collation biner | Tidak | — | UUID tervalidasi, PK; PK/FK memakai tipe dan collation sama |
| TIME | DATETIME(6) | Tidak kecuali tertulis Ya | — | Waktu UTC dari server, bukan waktu klien sebagai otoritas |
| REV | BIGINT UNSIGNED | Tidak kecuali tertulis Ya | — | Positif; counter revisi/versi, bukan timestamp |
| QTY | DECIMAL(15,3) | Tidak | — | > 0, kapasitas teknis bukan batas bisnis yang telah disetujui |
| MONEY | DECIMAL(18,0) | Tidak | — | Rupiah bulat >= 0; presisi harga satuan ini usulan teknis |
| AMOUNT | DECIMAL(30,0) | Tidak | — | Subtotal baris >= 0; hasil hitung server |

Usulan engine InnoDB; teks umum utf8mb4. Versi/produk server aktual perlu
dikonfirmasi sebelum DDL: sebutan XAMPP tidak membuktikan MySQL atau kemampuan
CHECK tertentu. Semua FK historis memakai `ON DELETE RESTRICT`, `ON UPDATE RESTRICT`.
Kolom FK diberi indeks dengan urutan sama seperti referenced key, seluruh target
composite FK memiliki PK/UNIQUE eksplisit. Tidak ada cascade delete riwayat.
Default boolean wajib dibatasi 0/1; `BOOLEAN` saja bukan jaminan nilai valid.

### 2.2 `customers`

Identitas pelanggan; telepon bukan kunci identitas. Kolom `id` mengikuti §2.1.

| Kolom | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| name | VARCHAR(200) | Tidak | — | Nama tidak kosong setelah trim |
| phone | VARCHAR(40) | Tidak | — | Nomor telepon, bukan angka aritmetika |
| address | TEXT | Ya | NULL | Alamat opsional |
| is_active | BOOLEAN | Tidak | TRUE | Nonaktif tidak dapat dipilih untuk transaksi baru |
| version | REV | Tidak | 1 | Naik tiap perubahan master |
| created_at | TIME | Tidak | — | Waktu dibuat |
| updated_at | TIME | Tidak | — | Waktu terakhir diperbarui |

Indeks nonunik `phone`, `name`. CHECK `version > 0`, `is_active IN (0,1)` dan
nama/telepon tidak kosong. Tidak ada UNIQUE nama atau telepon. Nomor sama tidak
menggabungkan pelanggan. Pencarian substring/indeks lebih lanjut menunggu bukti beban.

### 2.3 `vehicles`

| Kolom | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| plate_normalized | VARCHAR(32), ASCII collation biner | Tidak | — | Kapital tanpa spasi, UNIQUE |
| is_active | BOOLEAN | Tidak | TRUE | Berlaku juga pada pemeriksaan pemilihan master |
| version | REV | Tidak | 1 | Versi master |
| created_at | TIME | Tidak | — | Waktu dibuat |
| updated_at | TIME | Tidak | — | Waktu terakhir diperbarui |

CHECK plat tidak kosong, versi positif, boolean valid. Server memastikan normalisasi
sebelum pencarian/simpan; format plat rinci dan kapasitas 32 karakter perlu review.
UNIQUE tetap mencakup kendaraan nonaktif. Tidak ada `customer_id` atau nomor rangka.
Tidak menambahkan merek/model/tahun sebagai field wajib yang belum diputuskan.

### 2.4 `vehicle_plate_changes`

| Kolom | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| vehicle_id | UUID | Tidak | — | FK vehicles.id |
| vehicle_version | REV | Tidak | — | Versi kendaraan sesudah perubahan |
| old_plate | VARCHAR(32), ASCII collation biner | Tidak | — | Plat normalisasi sebelumnya |
| new_plate | VARCHAR(32), ASCII collation biner | Tidak | — | Plat normalisasi pengganti |
| changed_by | UUID | Tidak | — | FK users*.id; aktor server |
| actor_name_snapshot | VARCHAR(200) | Tidak | — | Nama aktor saat kejadian |
| changed_at | TIME | Tidak | — | Urutan perubahan berdasarkan versi, bukan waktu saja |

UNIQUE `(vehicle_id, vehicle_version)`; CHECK versi > 1 dan `old_plate <> new_plate`.
Plat historis tidak UNIQUE global. Server mengunci kendaraan, memastikan versi,
memperbarui plat dan menulis history dalam satu transaksi; hanya Owner. Tidak
menggabungkan kendaraan jika plat tujuan sudah ada. Pencarian plat historis dan
aturan pemakaian ulang plat lama belum ditetapkan sebagai fitur.

### 2.5 `visit_registrations`

| Kolom | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| customer_id | UUID | Tidak | — | FK customers.id |
| vehicle_id | UUID | Tidak | — | FK vehicles.id |
| customer_name_snapshot | VARCHAR(200) | Tidak | — | Nama pada kunjungan |
| phone_snapshot | VARCHAR(40) | Tidak | — | Telepon pada kunjungan |
| address_snapshot | TEXT | Ya | NULL | Alamat saat kunjungan bila diisi |
| plate_snapshot | VARCHAR(32), ASCII collation biner | Tidak | — | Plat normalisasi saat kunjungan |
| initial_complaint | TEXT | Tidak | — | Keluhan awal |
| registered_at | TIME | Tidak | — | Waktu registrasi server |
| created_by | UUID | Tidak | — | FK users*.id |
| version | REV | Tidak | 1 | Versi untuk pemeriksaan konflik |

Indeks `(vehicle_id, registered_at)`, `(customer_id, registered_at)`.
CHECK versi positif dan snapshot wajib/keluhan tidak kosong. Tidak ada UNIQUE
pelanggan–kendaraan atau tanggal kunjungan; kedatangan berulang membuat ID baru.
Perubahan master tidak menulis ulang snapshot. Koreksi eksplisit nama, telepon,
plat atau keluhan mengikuti CONTEXT §2.3: sebelum SO dibuat oleh petugas yang
berhak registrasi; setelah SO dibuat hanya Owner, wajib alasan. Setiap koreksi
memiliki riwayat, tidak otomatis mengubah master atau dokumen final. Struktur
penyimpanan audit koreksi dan konsistensi FK terhadap snapshot yang dikoreksi
masih perlu dirancang; endpoint update bebas belum dapat diimplementasikan.

### 2.6 `diagnosis_estimates`

| Kolom | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| registration_id | UUID | Tidak | — | FK visit_registrations.id, UNIQUE |
| current_revision_no | REV | Ya | NULL | Pointer revisi terkini; NULL hanya bootstrap transaksi |
| created_by | UUID | Tidak | — | FK users*.id |
| created_at | TIME | Tidak | — | Identitas dokumen tidak ditulis ulang |

UNIQUE `(registration_id, id)` sebagai target FK SO. Composite FK
`(id, current_revision_no)` → diagnosis_estimate_revisions `(estimate_id, revision_no)`.
Pointer wajib terisi sebelum commit. Satu registrasi maksimal satu dokumen estimasi,
bukan satu dokumen baru setiap revisi. Belum menambah status diagnosa produksi.

### 2.7 `diagnosis_estimate_revisions`

| Kolom | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| estimate_id | UUID | Tidak | — | FK diagnosis_estimates.id |
| revision_no | REV | Tidak | — | Mulai 1, urut per estimasi |
| findings | TEXT | Ya | NULL | Hasil pemeriksaan; draf dapat belum lengkap |
| recommended_action | TEXT | Ya | NULL | Rekomendasi tindakan |
| created_by | UUID | Tidak | — | FK users*.id |
| actor_name_snapshot | VARCHAR(200) | Tidak | — | Audit |
| actor_role_snapshot | VARCHAR(20) | Tidak | — | Owner/Teknisi saat aksi; bukan sumber izin |
| created_at | TIME | Tidak | — | Waktu server |
| reason | TEXT | Ya | NULL | Alasan revisi bila relevan; aturan harga di §3.6 |

UNIQUE `(estimate_id, revision_no)`; CHECK revisi positif. Revisi append-only.
Server memeriksa kelengkapan temuan/rekomendasi sebelum persetujuan, bukan mewajibkan
draf parsial langsung lengkap. Kelengkapan lain dan siklus diagnosa masih terbuka.

### 2.8 `diagnosis_estimate_items`

Anchor identitas baris; nama/satuan/harga/qty berada di snapshot revisi §2.9.

| Kolom | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| estimate_id | UUID | Tidak | — | FK diagnosis_estimates.id |
| service_id | UUID | Ya | NULL | Target FK services*.id |
| spare_part_id | UUID | Ya | NULL | Target FK spare_parts*.id |

UNIQUE `(estimate_id, id)`; CHECK tepat satu dari service_id/spare_part_id terisi.
Referensi katalog anchor tidak ditukar menjadi item lain ketika direvisi; item baru
memakai ID baru. Item bebas nonkatalog belum diputuskan, sehingga belum dicakup draf.

### 2.9 `diagnosis_estimate_revision_items`

Setiap baris memiliki `id` (§2.1) dan seluruh kolom bersama berikut. Kolom nilai
yang sama juga menjadi bagian skema `service_order_revision_items` (§2.13).

| Kolom nilai snapshot bersama | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| position | INT UNSIGNED | Tidak | — | Urutan tampilan > 0, bukan identitas baris |
| name_snapshot | VARCHAR(200) | Tidak | — | Nama jasa/part saat snapshot |
| unit_code | VARCHAR(20) | Tidak | — | pcs/unit/kg/liter/meter/job/hour; kode usulan |
| quantity_scale | TINYINT UNSIGNED | Tidak | — | 0 atau 3 sesuai satuan |
| qty | QTY | Tidak | — | Positif; skala 0 harus bulat |
| master_unit_price_snapshot | MONEY | Tidak | — | Harga master awal saat baris ditambahkan |
| unit_price | MONEY | Tidak | — | Harga jual lokal dokumen |
| subtotal_rupiah | AMOUNT | Tidak | — | ROUND(qty × unit_price, 0), setengah naik |
| price_change_reason | TEXT | Ya | NULL | Wajib untuk perubahan harga lokal, lihat §3.6 |

| Kolom pengikat khusus estimasi | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| estimate_id | UUID | Tidak | — | Bagian kedua FK komposit berikut |
| revision_no | REV | Tidak | — | FK (estimate_id, revision_no) ke §2.7 |
| item_id | UUID | Tidak | — | FK (estimate_id, item_id) ke §2.8 (estimate_id, id) |

UNIQUE `(estimate_id, revision_no, item_id)` dan `(estimate_id, revision_no, position)`.
CHECK nilai positif/nonnegatif, `quantity_scale IN (0,3)`, qty bulat untuk skala 0,
nama/satuan tidak kosong. Kecocokan satuan/skala dan subtotal diperiksa server.
Total dokumen = jumlah subtotal revisi yang dipilih; tidak menyimpan total mutable kedua.

### 2.10 `service_orders`

| Kolom | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| registration_id | UUID | Tidak | — | FK visit_registrations.id, UNIQUE |
| estimate_id | UUID | Tidak | — | Estimasi dari registrasi yang sama |
| approved_estimate_revision_no | REV | Tidak | — | Baseline persetujuan tetap |
| approval_recorded_by | UUID | Tidak | — | FK users*.id, petugas pencatat persetujuan lisan |
| approval_recorded_at | TIME | Tidak | — | Waktu pencatatan server |
| current_revision_no | REV | Ya | NULL | NULL hanya bootstrap transaksi |
| previous_service_order_id | UUID | Ya | NULL | FK service_orders.id, riwayat pekerjaan sebelumnya |
| reference | VARCHAR(64), ASCII collation biner | Tidak | — | UNIQUE, nomor SO dari server |
| created_by | UUID | Tidak | — | FK users*.id |
| created_at | TIME | Tidak | — | Waktu pembuatan |

FK `(registration_id, estimate_id)` → diagnosis_estimates `(registration_id, id)`;
FK `(estimate_id, approved_estimate_revision_no)` → §2.7 `(estimate_id, revision_no)`;
FK `(id, current_revision_no)` → §2.11 `(service_order_id, revision_no)`.
UNIQUE `estimate_id` menegakkan maksimal satu SO dari satu estimasi.
CHECK tidak merujuk diri sendiri sebagai SO sebelumnya. Server memeriksa hubungan
riwayat pada kendaraan sama, registrasi berbeda, tidak bersiklus; ini usulan
validasi teknis yang perlu review, bukan alur penggabungan kendaraan.
Format nomor SO belum diputuskan; UNIQUE saja tidak menjamin idempotensi payload.

### 2.11 `service_order_revisions`

| Kolom | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| service_order_id | UUID | Tidak | — | FK service_orders.id |
| revision_no | REV | Tidak | — | Urutan revisi mulai 1, juga versi konflik |
| status | VARCHAR(24) | Tidak | — | not_started/in_progress/paused/completed/cancelled |
| created_by | UUID | Tidak | — | FK users*.id |
| actor_name_snapshot | VARCHAR(200) | Tidak | — | Audit |
| actor_role_snapshot | VARCHAR(20) | Tidak | — | Owner/Teknisi saat aksi, bukan otorisasi |
| created_at | TIME | Tidak | — | Waktu server |
| reason | TEXT | Ya | NULL | Wajib saat buka kembali dan perubahan yang perlu alasan |
| customer_approval_recorded_by | UUID | Ya | NULL | FK users*.id, persetujuan biaya tambahan |
| customer_approval_recorded_at | TIME | Ya | NULL | Pasangan aktor/waktu harus sama-sama terisi/kosong |
| customer_approval_note | TEXT | Ya | NULL | Catatan persetujuan revisi ini |

UNIQUE `(service_order_id, revision_no)`; CHECK versi positif, whitelist status dan
pasangan aktor/waktu. Revisi append-only. Setiap perubahan status, realisasi atau
penugasan membuat revisi lengkap berikutnya. Status awal `not_started` ditetapkan
server ketika membuat SO; tidak dipercayakan pada default/input klien.
Persetujuan tambahan terkait revisi tertentu, bukan boolean permanen pada SO.
Matriks transisi/izin rinci dan bentuk bukti persetujuan perlu review (§3.6).

### 2.12 `service_order_items`

| Kolom | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| service_order_id | UUID | Tidak | — | FK service_orders.id |
| source_estimate_item_id | UUID | Ya | NULL | FK diagnosis_estimate_items.id; NULL untuk tambahan SO |
| service_id | UUID | Ya | NULL | Target FK services*.id |
| spare_part_id | UUID | Ya | NULL | Target FK spare_parts*.id |

UNIQUE `(service_order_id, id)`; CHECK tepat satu referensi katalog terisi.
Server memastikan sumber termasuk revisi estimasi yang disetujui SO tersebut dan
referensi katalog sesuai sumber. FK source tunggal tidak cukup untuk itu.
Tidak memakai posisi baris sebagai sumber reservasi. Baris hasil salinan mendapat
ID SO baru; identitas asal tetap terhubung. Aturan pecah/gabung baris belum diputuskan.

### 2.13 `service_order_revision_items`

Setiap baris memiliki `id` (§2.1), seluruh kolom nilai snapshot bersama §2.9, dan:

| Kolom pengikat khusus SO | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| service_order_id | UUID | Tidak | — | Bagian kedua FK komposit berikut |
| revision_no | REV | Tidak | — | FK (service_order_id, revision_no) ke §2.11 |
| item_id | UUID | Tidak | — | FK (service_order_id, item_id) ke §2.12 (service_order_id, id) |

UNIQUE `(service_order_id, revision_no, item_id)` dan
`(service_order_id, revision_no, position)`. CHECK nilai snapshot mengikuti §2.9.
Revisi pertama menyalin tepat nama/satuan/qty/harga/subtotal dari estimasi disetujui,
bukan membaca ulang master. Revisi realisasi berikutnya tidak menulis ulang baseline.
Tidak ada kolom harga beli/HPP dalam snapshot layanan ini.

### 2.14 `service_order_revision_technicians`

| Kolom | Tipe | Null? | Default | Keterangan |
|---|---|---|---|---|
| service_order_id | UUID | Tidak | — | Bagian FK komposit ke revisi |
| revision_no | REV | Tidak | — | FK (service_order_id, revision_no) ke §2.11 |
| technician_id | UUID | Tidak | — | FK users*.id; server memeriksa peran Teknisi |
| technician_name_snapshot | VARCHAR(200) | Tidak | — | Nama saat penugasan |

UNIQUE `(service_order_id, revision_no, technician_id)` mencegah penugasan ganda.
Semua Teknisi setara; tidak ada kolom penanda utama atau tingkat penugasan.
Server memastikan **minimal satu Teknisi sebelum mulai pengerjaan**, dalam
transaksi revisi yang sama. UNIQUE tidak menjamin jumlah minimal baris penugasan.
Revisi berstatus Dalam Pengerjaan tidak boleh mengosongkan seluruh penugasan.
Riwayat penugasan mengikuti revisi; pergantian nama/peran user tidak mengubah snapshot.

## 3. Aturan data
| Aturan | Penjelasan |
|---|---|
| Snapshot harga | Rancangan pelanggan–layanan §2.9/§2.13 dan §3.6; harga master tidak menulis ulang dokumen lama |
| Perubahan stok | Reservasi saat part masuk SO tervalidasi server; pengeluaran final saat invoice final diterbitkan. Lihat §3.1. |
| Penomoran dokumen | Nomor SO server, UNIQUE; format dan alokasi nomor belum final, lihat §2.10/§3.6 |
| Idempotensi tulis | UUID klien + idempotency key sesuai TRD; payload/versi divalidasi, lihat §3.6; skema penyimpanan key belum final |

### 3.1 Kontrak data stok [DIPUTUSKAN 2026-11-06]

Sumber keputusan: CONTEXT §2.3–§2.4. Bagian ini menetapkan tanggung jawab data,
bukan skema fisik final; §2 masih perlu dilengkapi sebelum migrasi dibuat.

| Data/tabel | Tanggung jawab | Status rancangan |
|---|---|---|
| `stock_reservations` | Mencatat alokasi sementara part per baris SO, qty, status aktif/dilepas/dikonversi, aktor dan waktu | Nama tabel usulan; kolom, tipe, constraint, dan riwayat perubahan belum final |
| `stock_movements` | Mencatat pergerakan stok final dengan sumber dokumen; pengeluaran terkait penerbitan invoice final | Nama tabel mengikuti TRD; skema fisik belum final |
| Saldo stok | Stok tersedia mengikuti CONTEXT §2.4, termasuk pengurangan qty rusak yang diblokir tanpa menghitung ganda reservasi | Strategi perhitungan/agregasi belum final; tanpa Redis dahulu |

Invarian untuk implementasi berikutnya:
- Reservasi tersimpan di MySQL, bukan hanya state browser atau cache. API
  menyediakan ketiga angka stok; endpoint dan bentuk response belum ditetapkan.
- Alokasi hanya sah setelah validasi server. Pemeriksaan ketersediaan dan
  perubahan reservasi dilakukan dalam transaksi dengan penguncian baris
  sparepart yang sama untuk mencegah alokasi berlebih antar-SO.
- Penerbitan invoice final, pencatatan pengeluaran stok, dan penyelesaian
  reservasi terkait harus atomik dalam satu transaksi MySQL. Jika gagal,
  seluruh perubahan transaksi dibatalkan. Request ulang tidak menggandakan
  invoice atau pengeluaran stok; detail kunci idempotensi/constraint belum final.
- Konversi qty reservasi menjadi pengeluaran tidak mengurangi stok tersedia dua
  kali. Pembayaran invoice tidak membuat pengeluaran stok kedua.
- Pelepasan part sebelum dipakai membebaskan reservasi. Part terpakai tetap
  mengikuti realisasi, termasuk pada pembatalan SO. Qty yang dikonversi harus
  sesuai realisasi final, bukan otomatis mengikuti total estimasi.
- Qty memakai desimal tetap dan aturan satuan pada CONTEXT §2.3; presisi serta
  kapasitas kolom belum ditetapkan. Presisi qty dan pembulatan subtotal mengikuti
  CONTEXT §2.5 (tiga desimal, rupiah terdekat per baris, setengah naik). Nilai uang
  tidak menggunakan float.
- Koreksi harga tidak otomatis membuat retur stok. Reservasi SO Ditunda,
  penerimaan pembelian, barang rusak dan retur mengikuti keputusan terbaru CONTEXT
  §2.4–§2.4.1; skema fisiknya menunggu irisan stok/retur. SO setelah invoice final
  tetap terkunci; rincian koreksi qty/retur tidak diimplementasikan pada DB-01.
- Visibilitas jumlah stok untuk ketiga peran tidak memberikan izin mengubah
  stok atau mengakses HPP. Otorisasi tetap divalidasi server.

### 3.2 Kontrak penyimpanan prototype WEB-03C

Ini kontrak JSON dummy browser, bukan tabel atau API produksi. Store version 1
dipertahankan; field `handoff` opsional pada SO, berbentuk `{history: [...]}`.
Tidak ada collection antrean terpisah atau salinan item/harga kedua.

Event history memiliki `id`, `state` (`queued`/`withdrawn`), `actor`, `at`, `reason`,
`realizationRevision` (jumlah entri realisasi tersimpan) dan `workflowCount`.
Status berasal dari event terakhir; tanpa field berarti belum pernah diserahkan.
Queued merujuk revisi realisasi dan workflow terminal yang telah tersimpan.
Withdrawn hanya Owner dan wajib alasan; pasangan queued/withdrawn memiliki kedua
counter sama. Selama queued tidak boleh ada revisi realisasi atau progres.
Counter/waktu historis harus konsisten, ID unik dan state bergantian. Antrean
menampilkan total dari revisi realisasi yang dirujuk, bukan total estimasi.
Batas teknis demo 100 event per SO; tidak memangkas history. Rincian gate uji di IPD.

### 3.3 Kontrak JSON dummy invoice WEB-04

Collection opsional `invoices` pada store version 1; satu invoice per `orderId`.
Identitas: `id`, `reference`, `orderId`, `createdAt`, `createdBy`; tidak ditulis ulang.
`history` append-only, maksimal 200 event, menyatukan revisi dan pembayaran agar
urutan koreksi/pembayaran tidak bergantung pada timestamp yang mungkin sama.

Event snapshot: `id`, `kind` (`created`, `price`, `rebased`, `issued`, `corrected`),
`at`, `actor`, `handoffId`, `items`, `reason`. Created/rebased menyalin tepat revisi
realisasi penyerahan terkait. Price/corrected hanya mengubah `unitPrice`, tanpa
mengubah identitas/baris/qty/satuan/nama. Issued menyalin snapshot draf terakhir.
Price/corrected/rebased hanya Owner dan wajib alasan. Created/issued Kasir/Owner.
Maksimal satu issued; corrected hanya sesudah issued. Rebased hanya sebelum issued,
ke penyerahan aktif yang lebih baru. Waktu snapshot harus berada dalam interval
penyerahan yang dirujuk. Sesudah issued, penyerahan SO tersebut tidak dapat ditarik.

Event pembayaran: `id`, `kind: payment`, `at`, `actor`, `invoiceRevision`, `method`

**Catatan lingkup 2026-11-15:** kontrak di bawah mendokumentasikan storage demo
existing, termasuk gateway-demo historis. Metode aktif konsep baru mengikuti
CONTEXT §2.2 (tunai/QRIS statis/transfer manual). Penyimpanan QRIS serta konfigurasi
tujuan pembayaran belum dimigrasi; catatan ini tidak mengubah skema/data terpakai.

(`cash`, `transfer`, `gateway-demo`), `amount`, `received`, `reference`,
`gatewayAcknowledged`. InvoiceRevision adalah nomor snapshot terkini saat event
dibaca berurutan. Amount harus seluruh sisa positif saat itu; received tunai boleh
lebih besar (selisih menjadi kembalian), non-tunai harus sama. Transfer wajib
referensi, gateway-demo wajib pengakuan simulasi. Seluruh nominal integer aman;
saldo memakai jumlah amount, bukan received. Tidak ada event pembayaran nol/refund.

Status draf/final, Lunas/Belum Lunas, sisa dan kelebihan bayar dihitung dari ledger;
tidak disimpan sebagai flag terpisah. Persist menjaga prefix history/identitas lama
dan hanya menambah event; validasi replay memeriksa peran, sumber dan nominal.
Kontrak ini bukan skema produksi, transaksi database atau bukti gateway nyata.

### 3.4 Preferensi dan proyeksi POS demo

Peran demo terpilih disimpan terpisah pada key `pos_browser_prototype_role`, hanya
menerima Owner/Teknisi/Kasir; nilai salah atau read failure memakai fallback Owner.
Ini preferensi UI, bukan sesi login/otorisasi. Gagal menulis preferensi tidak
mengubah ledger atau memblokir penyimpanan transaksi. Store finansial tidak dimigrasi.

Antrean POS adalah proyeksi read-only satu entri per SO: queued tanpa invoice,
invoice draf (termasuk stale), serta final bersisa positif. Filter Lunas/Semua
boleh menampilkan invoice final dengan sisa nol. Tidak ada collection POS baru,
duplikasi ledger atau penulisan saat pencarian/pemilihan preview.

### 3.5 Kontrak preview dan tim SO WEB-05

Mode `?demo=flow` memakai key `pos_browser_preview_flow_v1`, dengan format store
version 1 yang sama. Inisialisasi hanya saat key belum ada, dari `preview-store.json`;
data rusak atau gagal dibaca tidak direset. Key prototype utama tetap utuh.
Preferensi tema/peran masih menggunakan key UI existing, bukan otorisasi.

Workflow SO menambahkan `memberIds` opsional (array ID teknisi contoh unik),
tanpa memasukkan `technicianId` utama. Data lama tanpa array berarti tanpa anggota.
Event penugasan/progres baru yang memiliki anggota mencatat `memberBefore` dan
`memberAfter`; replay memvalidasi snapshot dan kesesuaian keadaan akhir. Anggota
hanya diubah pada tindakan `assigned`/`started`, mengikuti izin dan lock SO existing.
Field ini kontrak JSON demo, bukan perubahan skema produksi.

Catatan keputusan terbaru CONTEXT §2.3: produksi memakai penugasan Teknisi setara,
tanpa utama/anggota. Kontrak WEB-05 di atas merekam perilaku prototype existing;
penyesuaian prototype menjadi irisan implementasi terpisah.

### 3.6 Invariant produksi usulan DB-01

**Snapshot dan revisi.** Head hanya menyimpan identitas, baseline dan pointer;
seluruh rincian aktif dibaca dari revisi yang ditunjuk. Revisi terdahulu beserta
anak-anaknya tidak diubah/dihapus. Item dihapus dari rincian baru dengan tidak
menyertakannya pada snapshot baru, bukan menghapus anchor/history. ID item tidak
didaur ulang. Revisi berurutan, tidak mengandalkan timestamp yang dapat sama.
Append-only merupakan tanggung jawab writer/izin database, bukan akibat FK saja.

**Transaksi pembuatan/revisi.** Server mengunci head, memeriksa versi request,
otorisasi terkini, status dan lock antrean/invoice; kemudian menulis revisi lengkap
beserta item/penugasan dan memindahkan pointer dalam satu transaksi. Pointer NULL
diizinkan secara fisik hanya untuk memutus siklus FK saat bootstrap; tidak boleh
ada dokumen committed tanpa revisi pertama. FK pointer dipasang setelah tabel
head dan revisi tersedia, tanpa menonaktifkan pemeriksaan FK saat operasi normal.
Master pelanggan/kendaraan menggunakan `version`; revisi dokumen menggunakan
`current_revision_no` sebagai versi, tanpa counter kedua yang dapat berbeda.

**Persetujuan estimasi.** Dalam satu transaksi, validasi versi estimasi, catat
persetujuan lisan, buat SO dan revisi pertamanya dari baseline yang tepat. Tidak
ada SO kedua ketika retry. Revisi estimasi yang dirujuk tidak berubah; perubahan
pekerjaan selanjutnya berada di SO. Jangan membuka siklus revisi estimasi baru
setelah persetujuan sebelum kebijakan siklus diagnosa diputuskan.

**Harga dan tambahan biaya.** Snapshot master ditetapkan ketika item ditambahkan,
bukan disegarkan setiap revisi. Untuk item SO hasil salinan, snapshot awal diwarisi
dari estimasi. Server membandingkan item ber-ID sama pada revisi sebelum/sesudah;
perubahan harga lokal wajib alasan (juga saat harga awal berbeda dari master).
Nilai lama/baru, aktor, waktu dan identitas item dapat ditelusuri lewat revisi.
Alasan pada snapshot tidak menggantikan perbandingan perubahan per revisi.
Tambahan biaya memerlukan pencatatan persetujuan pelanggan pada revisi terkait.
Aturan perubahan item dengan total tetap/lebih rendah serta bentuk bukti persetujuan
masih perlu review; tidak ditambahkan batas nominal otomatis. Subtotal dihitung
ulang server dengan desimal tetap; request tidak boleh menyuplai total tepercaya.

**Penugasan dan status.** Semua Teknisi dalam SO setara. SO Belum dimulai boleh
tanpa penugasan; minimal satu Teknisi wajib ada sebelum memulai atau melanjutkan
pengerjaan. Writer memeriksa jumlah minimal, validitas peran dan versi dalam
transaksi revisi; perubahan penugasan saat Dalam Pengerjaan tidak boleh membuat
jumlahnya nol. Siapa mengubah penugasan dan matriks tiap transisi masih perlu dirinci.
Whitelist status tidak mengesahkan semua perpindahan status. Batas Owner,
Selesai/Dibatalkan, penarikan antrean dan invoice final mengikuti CONTEXT §2.3,
§2.4.2 dan §2.6. Jangan menyediakan transisi yang belum ada izin bisnisnya.

**Offline/idempotensi.** Versi lama menghasilkan konflik tanpa write parsial;
perubahan lokal tidak dihapus. Hasil pilihan pengguna menjadi request baru dengan
versi server terbaru dan tetap melalui validasi lengkap. Salinan offline tidak
membuktikan persetujuan, reservasi atau keberhasilan server. Kunci idempotensi
terikat aktor, operasi dan payload; retry identik mengembalikan hasil yang sama,
key sama dengan payload berbeda ditolak. Persistensi key, retensi, transaksi
penyimpanannya dan nomor dokumen menjadi dependensi irisan API; belum tersedia DDL.

**Master/privasi.** Menonaktifkan master tidak menghapus dokumen. Pembuatan referensi
baru ke master nonaktif ditolak; pembacaan dokumen lama tetap memakai snapshot.
Efek nonaktif pada dokumen yang sedang berjalan perlu diputuskan sebelum endpoint
revisi dibuka. Aktor, role snapshot dan waktu ditetapkan server. Nama/peran historis
bukan sumber otorisasi. Audit harga lengkap/riwayat internal hanya Owner;
serializer transaksi untuk peran lain memakai field yang diizinkan, bukan mengirim
history lalu menyembunyikannya di UI. Riwayat koreksi tidak dicetak pada nota
pelanggan sesuai CONTEXT §2.7. Tidak memasukkan harga beli/HPP pada payload layanan.

**Dependensi yang memblokir implementasi lengkap.** Revisi SO berisi part harus
bertransaksi dengan reservasi, pemeriksaan stok dan lock baris part. DB-01 belum
mendesain tabel stok sehingga tidak boleh diklaim siap dijalankan sendiri.
Handoff/finalisasi invoice harus memeriksa sumber revisi dan ikut mencegah revisi
SO yang terkunci. Struktur autentikasi/katalog, audit registrasi, mekanisme
idempotensi, urutan lock lintas agregat, dan matriks izin perlu selesai sebelum migrasi.

Rujukan teknis yang diperiksa melalui Context7: dokumentasi resmi MySQL tentang
[CHECK](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html),
[foreign key](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html),
dan [UNIQUE](https://dev.mysql.com/doc/refman/8.4/en/create-index.html).
Hasil pencarian mencakup manual versi lain; ini mendukung prinsip constraint,
bukan verifikasi kompatibilitas engine lokal. CHECK tidak menggantikan pemeriksaan
lintas tabel/otorisasi. Kesesuaian DDL aktual harus diuji terpisah.

## 4. Endpoint API
| Metode | Path | Peran yang boleh | Request | Response | Error |
|---|---|---|---|---|---|
| ISI: | | | | | |

## 5. Validasi

### 5.1 Matriks penegakan dan walkthrough DB-01

Skenario berikut merupakan kriteria review rancangan, **belum hasil tes SQL/runtime**.
Aturan panjang/tipe/default ada di §2; bukan disalin ulang pada dokumen lain.

| Skenario | Penegakan DB | Penegakan transaksi/server / hasil yang diharapkan |
|---|---|---|
| Dua pelanggan memakai telepon sama | Tidak ada UNIQUE phone | ID berbeda, tidak auto-merge |
| Plat berbeda kapital/spasi | UNIQUE plate_normalized | Normalisasi dahulu; konflik tidak membuat kendaraan kedua |
| Owner mengganti plat, lalu master pelanggan berubah | FK historis RESTRICT | History plat atomik; snapshot kunjungan lama tetap |
| Dua request membuat estimasi/SO pada kunjungan sama | UNIQUE registration_id di masing-masing head | Satu dokumen; retry identik mengembalikan hasil sama |
| SO memakai estimasi kunjungan lain | FK komposit registrasi–estimasi | Ditolak tanpa perubahan parsial |
| Snapshot menunjuk item/revisi dokumen lain | Dua FK komposit pada snapshot | Ditolak; item sumber SO juga diverifikasi terhadap baseline |
| Qty 0/negatif atau pcs 1,5 | CHECK qty/skala; nilai tetap | Server memeriksa kecocokan unit, menolak lebih dari 3 desimal sebelum konversi SQL |
| Qty 0,125 × harga Rp100 | Tipe desimal, subtotal nonnegatif | Subtotal Rp13; total menjumlahkan baris dibulatkan, bukan membulatkan jumlah mentah |
| Harga master berubah / realisasi direvisi | Snapshot terpisah, identitas anchor tetap | Baseline disetujui tetap; item lama/baru dan alasan harga dapat ditelusuri |
| Item dihapus dari revisi baru | Anchor/history tidak cascade | Snapshot sebelumnya tetap utuh; reservasi disesuaikan hanya lewat transaksi stok |
| Teknisi sama dipilih dua kali / mulai tanpa Teknisi | UNIQUE technician_id per revisi | Duplikat ditolak; server menolak mulai/lanjut atau revisi Dalam Pengerjaan tanpa Teknisi; beberapa Teknisi berbeda sah dan setara |
| Dua perangkat merevisi versi yang sama | UNIQUE revision_no, FK pointer | Lock dan pemeriksaan versi; satu commit, lainnya konflik, salinan lokal dipertahankan |
| Gagal setelah menulis sebagian snapshot | FK menjaga referensi, bukan kelengkapan | Rollback seluruh transaksi; head/pointer/history/anak tidak tertinggal separuh |
| Teknisi revisi SO terminal atau SO sedang antre/final invoice | Tidak dijamin CHECK | Policy + lock sumber menolak; Owner menarik antrean sebelum revisi yang diizinkan |
| Harga/log internal dibaca peran tidak berhak | Tidak dijamin FK | Policy/serializer mencegah akses history lengkap; tidak mengirim data terlarang |
| UUID/aktor/subtotal/status disuntikkan dari klien | PK/tipe/CHECK hanya lapis tambahan | Validasi UUID, allowlist field dan izin server; aktor/waktu/hitungan ditetapkan ulang |

### 5.2 Keputusan/dependensi terbuka sebelum DDL

- Konfirmasi engine/versi SQL, format penyimpanan UUID dan kapasitas tipe usulan.
- Batas panjang data, format nomor SO, skala harga satuan dan overflow subtotal.
- Izin perubahan penugasan dan matriks transisi terperinci; waktu minimal penugasan
  sudah diputuskan sebelum pengerjaan dimulai, tanpa Teknisi utama.
- Kebijakan koreksi registrasi sudah diputuskan di CONTEXT §2.3 dan dirujuk §2.5;
  yang masih terbuka adalah struktur history, konsistensi FK/snapshot, dan
  pengikatan versi registrasi pada dokumen final. Siklus diagnosa setelah
  persetujuan masih perlu ditetapkan.
- Bentuk bukti persetujuan tambahan dan aturan item dengan total sama/lebih rendah.
- Item nonkatalog, pecah/gabung baris dan perubahan satuan item existing.
- Efek menonaktifkan master terhadap dokumen berjalan, bukan dokumen baru saja.
- FK pengguna/katalog, tabel stok/antrean/invoice dan idempotensi lintas operasi.
- Arti plat lama dipakai ulang/pencarian historis dan aturan penghapusan master
  yang belum pernah dipakai. Tidak menganggap keputusan ini sudah final.

## 6. Migrasi dan data awal

**Belum membuat migrasi.** Rancangan DB-01 hanya dokumentasi. Urutan dependensi
yang diusulkan untuk diuji sesudah persetujuan skema fisik:

1. Selesaikan skema users/roles dan katalog (services/spare_parts) serta engine.
2. Buat customers/vehicles, vehicle_plate_changes, visit_registrations.
3. Buat head diagnosis_estimates tanpa FK pointer dahulu, lalu revisi/anchor/item;
   tambahkan FK pointer setelah targetnya tersedia.
4. Buat service_orders beserta FK baseline, lalu revisi/anchor/item/penugasan;
   tambahkan FK pointer SO setelah targetnya tersedia.
5. Hubungkan stok/antrean/invoice/idempotensi pada irisan terkait, baru uji transaksi
   lengkap, concurrency, kegagalan parsial, dan otorisasi dengan engine aktual.

Seed produksi belum ditetapkan; tidak menyalin identitas/harga dummy prototype
menjadi master produksi. Tidak ada migrasi otomatis dari JSON localStorage.
Rollback DB-01 cukup mengembalikan bagian dokumen; tidak menyentuh data aplikasi.

## 7. Berkas terkait
- TRD: `../TRD/trd.md`
- AFD: `../AFD/afd.md`
