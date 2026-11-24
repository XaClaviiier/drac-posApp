# Metaprompt Pembentukan Sistem Bengkel PWA

Dokumen ini berisi **metaprompt**: prompt yang meminta AI *menyusun sendiri* prompt-prompt pembangunan sistem, lalu mengeksekusinya fase demi fase. Semua konteks proyek sudah ditanam di dalamnya, jadi kamu cukup menyalin dan menempel.

> Catatan: ganti hanya bagian `{{...}}`. Versi paket dan sintaks tetap harus dicek di dokumentasi resmi.

## Cara Pakai (Ringkas)

| Langkah | Prompt | Hasil |
|---|---|---|
| 1 | **M0**: Konteks Proyek | AI memahami proyek, mengajukan pertanyaan klarifikasi |
| 2 | **M1**: Generator Peta Jalan | Daftar fase beserta dependensi dan kriteria selesai |
| 3 | **M2**: Generator Prompt Fase | Prompt siap pakai untuk satu fase |
| 4 | **M3**: Eksekusi Fase | AI mengerjakan fase memakai prompt dari M2 |
| 5 | **M4**: Verifikasi Fase | AI memeriksa hasil sebelum lanjut |
| 6 | **M5**: Serah-Terima | Ringkasan konteks untuk sesi baru |

Ulangi M2 → M3 → M4 → M5 untuk setiap fase. Satu fase = satu sesi/percakapan agar kualitas tetap tinggi.

Jika memakai agen coding (misalnya Claude Code), isi **M0** bisa disimpan sebagai `CLAUDE.md` di root proyek supaya otomatis terbaca setiap sesi.

---

## M0: Konteks Proyek (Tempel Pertama, Sekali per Sesi)

````markdown
# PERAN
Kamu adalah arsitek perangkat lunak sekaligus engineer senior yang memandu dua mahasiswa
membangun sistem nyata untuk kerja praktik. Kamu juga bertugas sebagai "penulis prompt":
kamu menyusun instruksi kerja yang presisi untuk dirimu sendiri sebelum mengerjakannya.

# PROYEK
Sistem Manajemen Layanan dan Transaksi Bengkel berbasis Progressive Web App untuk
Bengkel Dokter AC Mobil (servis AC mobil dan penjualan sparepart), Makassar.

## Masalah bisnis yang harus terjawab
1. Stok sparepart tidak akurat dan tidak terdokumentasi.
2. Arus kas dan rincian transaksi sulit ditelusuri, termasuk kebutuhan bayar vendor.
3. Owner sulit melihat omzet, profit, dan kondisi keuangan secara langsung.

## Role
- Owner: akses penuh (dashboard, pengguna, semua modul, laporan).
- Supervisor: Customer, Kendaraan, Diagnosa, Jasa, Sparepart, Service Order, Transaksi,
  Riwayat Servis, Invoice, Laporan, Pembelian, Pengeluaran.
- Kasir: Customer, Kendaraan, Transaksi, Invoice, Riwayat Servis.
- Teknisi bukan pengguna sistem. Supervisor menginput hasil diagnosa atas informasi teknisi.

## Alur inti
Customer → Kendaraan → Diagnosa → Service Order (Menunggu → Dalam Pengerjaan → Selesai)
→ Pembayaran (→ Dibayar) → Invoice → Riwayat Servis → Dashboard/Laporan.

## Fitur
Inti (dari proposal): login berbasis role; CRUD customer dan kendaraan; diagnosa (keluhan,
hasil pemeriksaan, diagnosa, rekomendasi, catatan); CRUD jasa (nama, deskripsi, harga) dan
sparepart (nama, kode, harga, satuan, stok); Service Order dengan status; transaksi,
pembayaran, metode bayar, cetak invoice; riwayat servis per pelanggan dan kendaraan;
dashboard Owner; laporan transaksi/pendapatan per periode.
Tambahan (usulan tim): supplier, pembelian/stok masuk, pengeluaran, perhitungan profit,
peringatan stok menipis, autosave draft, akses offline terbatas dengan sinkronisasi otomatis.

# STACK (TETAP, TIDAK BOLEH DIGANTI TANPA PERSETUJUAN)
Backend : Laravel (PHP 8.2+) sebagai REST API, Sanctum, spatie/laravel-permission, Eloquent,
          Form Request, primary key UUID, barryvdh/laravel-dompdf, maatwebsite/excel, Pest.
Database: {{MySQL | PostgreSQL}}
Frontend: React + TypeScript (strict) + Vite, React Router, Tailwind CSS + shadcn/ui,
          React Hook Form + Zod, TanStack Query, Dexie.js (IndexedDB),
          vite-plugin-pwa (Workbox), Recharts.
Testing : Pest, Vitest, Playwright, Lighthouse.
Deploy  : VPS (Nginx + PHP-FPM), HTTPS wajib.

# ATURAN ARSITEKTUR (INVARIAN)
1. Logika bisnis di Service class; controller tipis.
2. Otorisasi divalidasi di server (middleware/Policy), bukan hanya disembunyikan di UI.
3. Semua endpoint tulis idempoten (UUID dari klien + idempotency key).
4. Perubahan stok HANYA lewat tabel stock_movements di dalam DB::transaction(),
   dengan lockForUpdate pada baris sparepart.
5. Harga disimpan sebagai snapshot pada item Service Order.
6. Nomor Service Order dan invoice dibuat server.
7. Pembayaran non-tunai, pengurangan stok, dan invoice resmi hanya online.
   Offline terbatas pada draft dan data layanan (Customer, Kendaraan, Diagnosa, Service Order).
8. Uang disimpan sebagai integer rupiah atau decimal, tidak pernah float.
9. Titik pengurangan stok mengikuti keputusan terbaru `CONTEXT.md` §2.4
   (2026-11-06), menggantikan aturan lama saat pembayaran berhasil. Kontrak
   reservasi dan pengeluaran stok dirujuk di `BSD/bsd.md` §3.1.
10. Profit = omzet (transaksi Dibayar) − HPP sparepart terpakai − pengeluaran.

# ATURAN KERJA
- Jangan mengarang nama fungsi, opsi, atau versi paket. Jika ragu, katakan dan arahkan
  ke dokumentasi resmi.
- Jangan menambah library di luar stack tanpa alasan dan alternatif.
- Jangan membuat fitur di luar permintaan fase yang sedang dikerjakan.
- Setiap fitur disertai test untuk jalur utama dan minimal satu jalur gagal.
- Jika ada yang ambigu dan memblokir pekerjaan, tanya dulu, jangan menebak.
- Bahasa penjelasan: Indonesia. Kode, nama file, istilah teknis: bahasa aslinya.
  Nama tabel/kolom: bahasa Inggris. Label UI: bahasa Indonesia.

# TUGAS PERTAMA
Jangan menulis kode. Lakukan ini:
1. Ringkas pemahamanmu tentang proyek dalam maksimal 8 kalimat.
2. Sebutkan asumsi yang kamu buat.
3. Ajukan maksimal 7 pertanyaan klarifikasi paling penting (urutkan dari yang paling
   memblokir), masing-masing dengan usulan jawaban default agar aku bisa menjawab "setuju".
4. Berhenti dan tunggu jawabanku.
````

---

## M1: Generator Peta Jalan

Tempel setelah pertanyaan klarifikasi dijawab.

````markdown
Berdasarkan konteks proyek dan jawabanku, susun peta jalan pembangunan sistem.

# KETENTUAN
- Bagi menjadi fase berurutan, tiap fase dapat dikerjakan dan diuji dalam satu sesi kerja.
- Urutkan berdasarkan dependensi: fondasi → data master → alur layanan → transaksi/stok →
  pendukung → laporan → PWA/offline → pengujian → deploy.
- Fase offline/PWA diletakkan setelah fitur online stabil.

# FORMAT KELUARAN (tabel + detail)
Tabel ringkas dengan kolom: ID Fase, Nama, Tujuan, Bergantung pada, Estimasi (hari kerja,
asumsi 2 orang), Risiko utama.

Lalu untuk tiap fase, berikan:
- **Keluaran** (artefak konkret: endpoint, halaman, tabel, test)
- **Kriteria selesai** (bisa diperiksa, bukan "sudah bagus")
- **Yang sengaja ditunda** ke fase lain
- **Pembagian kerja usulan** untuk dua orang (backend-lean vs frontend-lean) yang bisa
  berjalan paralel tanpa saling menunggu

# AKHIRI DENGAN
1. Jalur kritis (fase yang menentukan total waktu).
2. Tiga risiko terbesar proyek dan mitigasinya.
3. Daftar keputusan yang harus diambil tim sebelum fase tertentu dimulai.
````

---

## M2: Generator Prompt Fase (Inti Metaprompt)

Ini prompt yang menghasilkan prompt. Jalankan sekali per fase.

````markdown
Kamu akan menyusun PROMPT KERJA untuk dirimu sendiri (atau sesi baru) agar mengerjakan
fase berikut dengan benar. Jangan mengerjakan fasenya sekarang.

# FASE
{{ID dan nama fase dari peta jalan}}

# KONTEKS TERKINI
- Fase yang sudah selesai: {{ringkasan, atau "belum ada"}}
- Keputusan yang sudah ditetapkan: {{...}}
- Struktur file saat ini (jika ada): {{tempel pohon folder atau "kosong"}}

# LANGKAH PENYUSUNAN
1. Turunkan spesifikasi rinci fase ini dari konteks proyek: entitas, aturan bisnis,
   validasi, hak akses per role, state yang harus ditangani (kosong, memuat, error,
   offline, konflik jika relevan).
2. Identifikasi 5 cara fase ini paling mungkin salah (kesalahan logika bisnis, keamanan,
   konkurensi, data, UX). Jadikan masing-masing sebagai batasan atau test wajib.
3. Pecah menjadi sub-tugas berurutan yang masing-masing menghasilkan sesuatu yang bisa dijalankan.
4. Tentukan test yang harus ada, termasuk satu skenario yang sengaja mencoba melanggar aturan
   (akses lintas role, stok minus, harga berubah, request ganda).
5. Tentukan cara verifikasi manual (perintah dan langkah klik) dalam bentuk checklist.

# FORMAT PROMPT KERJA YANG DIHASILKAN
Tulis dalam satu blok kode markdown dengan bagian persis berikut:

## TUJUAN
## KONTEKS (apa yang sudah ada, apa yang tidak boleh diubah)
## SPESIFIKASI (per sub-tugas, dengan field, validasi, hak akses)
## BATASAN (termasuk 5 risiko dari langkah 2)
## URUTAN KERJA (sub-tugas berurutan; berhenti dan laporkan setelah tiap sub-tugas)
## TEST WAJIB
## KRITERIA SELESAI (checklist bisa diperiksa)
## FORMAT KELUARAN (path file di atas tiap blok kode, perintah menjalankan, ringkasan akhir)
## PERTANYAAN TERBUKA (jika ada; kerjakan hanya setelah dijawab)

# SETELAH BLOK KODE
Beri 3 hal: (a) bagian prompt yang paling rawan disalahartikan dan cara mengatasinya,
(b) apa yang harus kupersiapkan sebelum menjalankannya, (c) tanda bahwa hasilnya menyimpang.
````

---

## M3: Eksekusi Fase

````markdown
Kerjakan fase berikut persis sesuai prompt kerja di bawah. Ikuti Aturan Arsitektur dan
Aturan Kerja pada konteks proyek.

Protokol:
1. Ulangi pemahamanmu dalam 3 kalimat dan jawab "Pertanyaan Terbuka" bila ada.
   Jika ada yang memblokir, berhenti dan tanya.
2. Kerjakan sub-tugas satu per satu. Setelah tiap sub-tugas: tampilkan file yang dibuat/diubah,
   cara menjalankan, dan hasil test. Lalu tunggu "lanjut" dariku.
3. Jika kamu menemukan bahwa spesifikasi bertentangan dengan Aturan Arsitektur, hentikan
   dan jelaskan konfliknya, jangan diam-diam memilih salah satu.
4. Setelah sub-tugas terakhir, tampilkan checklist Kriteria Selesai dengan status
   Lulus/Gagal/Belum teruji dan bukti singkat tiap butir.

PROMPT KERJA:
"""
{{tempel hasil M2}}
"""
````

---

## M4: Verifikasi Fase (Adversarial)

````markdown
Sekarang berperan sebagai penguji yang skeptis dan berusaha mematahkan hasil fase ini.
Jangan membela pekerjaanmu sendiri.

Periksa dan laporkan:
1. **Kepatuhan pada invarian**: bandingkan kode dengan 10 Aturan Arsitektur satu per satu.
   Nyatakan Patuh/Melanggar dengan bukti (file dan baris).
2. **Keamanan**: otorisasi per endpoint, mass assignment, kebocoran data antar role,
   validasi input, penyimpanan rahasia.
3. **Integritas data**: transaksi DB, race condition, idempotensi, snapshot harga, stok.
4. **Kasus tepi**: kosong, null, nilai negatif, duplikat, request ganda, token kedaluwarsa,
   koneksi putus di tengah proses.
5. **Kualitas test**: apakah test benar-benar bisa gagal jika logika rusak? Usulkan satu
   mutasi sederhana pada kode yang seharusnya membuat test gagal.
6. **Kesesuaian dengan proposal**: butir ruang lingkup mana yang tercakup fase ini.

Format: tabel (Tingkat: Kritis/Tinggi/Sedang/Rendah | Lokasi | Masalah | Perbaikan),
lalu keputusan akhir: **LANJUT**, **LANJUT DENGAN CATATAN**, atau **ULANGI**, dengan alasan.
Jika tidak menemukan masalah di suatu kategori, sebutkan apa yang kamu periksa.
````

---

## M5: Serah-Terima Antar Sesi

````markdown
Fase {{ID}} selesai. Buat ringkasan serah-terima yang bisa kutempel di sesi baru
tepat setelah M0.

Isi (padat, tanpa basa-basi):
1. Fase yang selesai dan statusnya (lulus/lulus dengan catatan).
2. Struktur file penting saat ini (pohon folder dipangkas).
3. Keputusan desain yang diambil beserta alasannya.
4. Perubahan terhadap Aturan Arsitektur (jika ada) dan alasannya.
5. Kontrak yang sudah ada (endpoint, nama tabel, tipe data bersama) yang tidak boleh diubah
   sembarangan.
6. Utang teknis dan masalah terbuka.
7. Fase berikutnya dan apa yang harus dipersiapkan.
````

---

## Prompt Pendukung

### P1: Penyusun Peta Konflik Offline (khusus fase PWA)

````markdown
Untuk fase sinkronisasi offline, buat matriks konflik lengkap.

Untuk setiap entitas yang boleh dibuat/diubah offline (Customer, Kendaraan, Diagnosa,
Service Order), tentukan:
- Operasi yang diizinkan offline dan yang tidak.
- Urutan dependensi saat sinkron.
- Kondisi konflik yang mungkin (versi berbeda, data terhapus, stok tidak cukup, duplikat
  nomor polisi) dan respons server untuk masing-masing.
- Perlakuan di UI (status, pesan, siapa yang berhak menyelesaikan).
- Skenario Playwright yang mensimulasikan konflik tersebut.
Keluarkan sebagai tabel, lalu daftar test E2E.
````

### P2: Uji Kepatuhan Terhadap Proposal

````markdown
Bandingkan sistem yang sudah dibangun dengan Ruang Lingkup proposal (13 butir) dan Tujuan
2.1–2.5. Untuk tiap butir: Terpenuhi/Sebagian/Belum, bukti (fitur/file), dan celahnya.
Tandai juga fitur yang kita buat tetapi belum ada di proposal, lalu tulis kalimat revisi
proposal yang sesuai, dengan gaya bahasa proposal asli.
````

### P3: Generator Data Dummy dan Skenario Demo

````markdown
Buat seeder data dummy realistis (tanpa data pribadi asli) untuk demo:
10 customer, 15 kendaraan, 12 jasa AC mobil, 30 sparepart (dengan sebagian stok menipis),
3 supplier, 20 Service Order di berbagai status, transaksi 3 bulan terakhir, pembelian,
dan pengeluaran. Rancang agar dashboard menampilkan angka yang bervariasi dan
hitung manual omzet serta profit total sebagai pembanding. Sertakan skenario demo
5 menit yang menyorot: alur utama, stok menipis, offline-lalu-sinkron, dan laporan.
````

---

## Contoh Penerapan: Fase 5 (Transaksi, Stok, Invoice)

Berikut contoh bentuk **keluaran M2** agar kamu tahu apa yang diharapkan. Hasil nyata dari AI akan berbeda dan sebaiknya kamu tinjau sebelum dipakai.

````markdown
## TUJUAN
Memproses pembayaran Service Order berstatus Selesai secara atomik: mencatat transaksi,
mengurangi stok, mengubah status menjadi Dibayar, dan menerbitkan invoice.

## KONTEKS
Sudah ada: users+role, master data, diagnoses, service_orders (+items, snapshot harga,
kolom version), stock_movements. Jangan ubah kontrak endpoint fase 3–4.

## SPESIFIKASI
1. POST /api/service-orders/{id}/pay (role: Owner, Supervisor, Kasir)
   - Input: payment_method (cash|transfer|qris), paid_amount, reference (wajib bila non-tunai),
     idempotency_key
   - Validasi: SO berstatus Selesai; paid_amount >= grand_total; reference sesuai metode
2. TransactionService::pay():
   DB::transaction → lock baris sparepart (lockForUpdate) → cek stok → buat transactions →
   buat stock_movements OUT per item → SO ke Dibayar → buat invoices (nomor dari server)
3. GET /api/invoices/{id}/pdf (DomPDF) + tampilan cetak struk (CSS print)
...

## BATASAN (dari 5 risiko)
1. Stok minus saat dua pembayaran bersamaan → lockForUpdate + test konkurensi.
2. Transaksi ganda saat klik dua kali/retry → idempotency_key unik.
3. Pembayaran sebagian terisi saat error di tengah → seluruh proses dalam satu transaksi.
4. Harga master berubah → gunakan snapshot, bukan harga master.
5. Kasir mengakses endpoint stok langsung → otorisasi di server.

## TEST WAJIB
- Pembayaran sukses: stok berkurang tepat, status Dibayar, invoice terbit.
- Stok tidak cukup: gagal, tidak ada perubahan data (rollback penuh).
- Request kembar dengan idempotency_key sama: satu transaksi saja.
- Kasir mencoba mengubah stok langsung: 403.
...
````

---

## Mengapa Struktur Ini Bekerja

| Teknik | Fungsi |
|---|---|
| **Konteks tertanam (M0)** | AI tidak perlu ditanya ulang; aturan bisnis tetap konsisten di semua fase |
| **Clarify-first** | Mencegah AI membangun di atas asumsi yang salah |
| **Prompt yang menghasilkan prompt (M2)** | AI menurunkan spesifikasi rinci dan risiko lebih dulu, hasilnya lebih lengkap dibanding prompt singkat tulisan tangan |
| **Risiko jadi batasan** | Kegagalan yang diprediksi diubah menjadi test dan aturan |
| **Eksekusi bertahap dengan gerbang (M3)** | Kesalahan tertangkap per sub-tugas, bukan setelah ratusan baris |
| **Verifikasi adversarial (M4)** | Mengurangi bias AI yang cenderung menganggap pekerjaannya benar |
| **Serah-terima (M5)** | Konteks tidak hilang saat sesi baru |

## Peringatan

1. Keluaran AI harus ditinjau dan dijalankan. Jangan percaya klaim "test lulus" tanpa melihat hasil nyata di terminal kalian.
2. Jangan menempelkan data pelanggan asli atau kunci rahasia (`.env`) ke AI.
3. Kalian harus memahami setiap bagian kode untuk presentasi dan sidang KP. Pakai AI untuk mempercepat, bukan menggantikan pemahaman.
