# TRD: Technical Requirement Documentation — POS Bengkel AC Mobil

Dokumen ini menjawab: **dengan teknologi dan batasan teknis apa sistem dibangun.**
Bergantung pada PRD dan AFD. Skema data dan endpoint ada di BSD, bukan di sini.

Label: **[DIPUTUSKAN]** keputusan user · **[ASUMSI]** · **[REKOMENDASI]** · `ISI:` belum diputuskan.
Sumber: `../CONTEXT.md` §3; `../metaprompt-pembentukan-sistem.md` (STACK TETAP, ATURAN ARSITEKTUR, ATURAN KERJA).
Bila keduanya berbeda, `CONTEXT.md` menang. Perbedaan dicatat di §9.

---

## 1. Stack **[DIPUTUSKAN 2026-10-14, hasil M0]**
Stack tetap; tidak boleh diganti tanpa persetujuan.

| Lapisan | Pilihan | Alasan |
|---|---|---|
| Bentuk aplikasi | PWA | Satu kode untuk laptop dan ponsel, tanpa toko aplikasi, bisa jalan offline |
| Frontend | React + TypeScript (strict) + Vite, React Router, React Hook Form + Zod, TanStack Query, Dexie (IndexedDB), vite-plugin-pwa (Workbox), Recharts | Sesuai metaprompt; berevolusi dari `index.html` prototype (dipecah bertahap, tidak dibuang) |
| Gaya | Tailwind + token Buddy (`../DBD/DESIGN_POS_Extend.md`); shadcn/ui di-styling ulang ikut token | Lihat DBD |
| Referensi utama komponen UI | [React Aria](https://react-aria.adobe.com/) | Keputusan 2026-11-02; cakupan, hubungan dengan shadcn/ui, dan batas pemasangan/migrasi mengikuti CONTEXT §3.1 |
| Backend | Target Laravel 13 (PHP 8.3+) REST API, Sanctum, spatie/laravel-permission, Eloquent, Form Request, UUID sebagai primary key | Pembaruan versi disetujui user 2026-10-29; runtime lokal dan bukti di IPD ENV-01. AUTH-01 mengimplementasikan fondasi/login di `application/`; modul bisnis belum dibuat. MySQL portable lokal terpisah dari MariaDB XAMPP. |
| Database | MySQL (XAMPP lokal, VPS produksi) | XAMPP tersedia dan umum untuk KP |
| PDF dan ekspor | barryvdh/laravel-dompdf, maatwebsite/excel | Metaprompt |
| Testing | Pest, Vitest, Playwright, Lighthouse | Metaprompt |
| Deploy | VPS (Nginx + PHP-FPM), HTTPS wajib; penyedia/paket belum dipilih | Keputusan user 2026-11-01, CONTEXT §3.1; pilihan shared hosting dibatalkan dan target VPS dipulihkan. Pembelian direncanakan kemudian; deployment belum dilakukan. |
| Pembayaran | Tunai/QRIS statis/transfer manual, langsung lunas; tanpa DP/cicilan/tempo | CONTEXT §2.2, revisi 2026-11-15; gateway ditunda |

Versi paket dan sintaks harus dicek di dokumentasi resmi sebelum dipakai; jangan mengarang nama fungsi atau opsi.

## 2. Aturan arsitektur (invarian)
Dari metaprompt; tidak boleh dilanggar agent tanpa persetujuan. Aturan 7 sudah ditimpa CONTEXT.
1. Logika bisnis di Service class; controller tipis.
2. Otorisasi divalidasi di server (middleware/Policy), bukan hanya disembunyikan di UI.
3. Semua endpoint tulis idempoten (UUID dari klien + idempotency key).
4. Perubahan stok hanya lewat tabel `stock_movements` di dalam `DB::transaction()`, dengan `lockForUpdate` pada baris sparepart.
5. Harga estimasi disimpan sebagai snapshot pada Diagnosa & Estimasi; setelah
   persetujuan, salin ke SO. Realisasi SO dan riwayat revisinya terpisah dari estimasi.
6. Nomor work order dan invoice dibuat server.
7. Pembayaran non-tunai, pengurangan stok, dan invoice resmi hanya online. Offline terbatas pada draf (lihat §3).
8. Uang disimpan sebagai integer rupiah atau decimal, tidak pernah float.
9. Titik pengurangan stok: saat invoice final diterbitkan, meskipun belum dibayar
   (CONTEXT §2.4, keputusan 2026-11-06). Reservasi dan pengeluaran stok mengikuti
   kontrak data BSD §3.1; pembayaran tidak mengurangi stok lagi.
10. Acuan perhitungan profit untuk tahap mendatang: omzet (transaksi Dibayar) − HPP
    suku cadang terpakai − pengeluaran. HPP otomatis dan laporan profit ditunda
    dari lingkup tahap sekarang sesuai CONTEXT §2.4 (2026-11-11).

Catatan: reservasi dan pemicu pengeluaran stok pada aturan 4/9 sudah diputuskan
di CONTEXT §2.4. Lingkup pembelian, retur fisik, serta laporan/profit pada aturan
10 belum seluruhnya final (PRD §6 #1).

Reservasi disimpan di MySQL; Redis tidak digunakan pada tahap awal. Pembacaan
API menyediakan tiga angka stok sesuai CONTEXT §2.4. Validasi alokasi stok
dilakukan server dalam transaksi dengan penguncian baris sparepart, termasuk
ketika dua SO memesan part yang sama. Draf offline belum menjadi reservasi.

## 3. Offline dan sinkronisasi **[DIPUTUSKAN 2026-10-14]**
- Teknologi: service worker + IndexedDB (Dexie).
- **Boleh offline (terbatas):** draf Customer, Kendaraan, Diagnosa, Work order.
- **Wajib online:** pembayaran, perubahan stok, invoice resmi.
- Aturan konflik **[REKOMENDASI]**: tiap perubahan membawa nomor versi; bila bentrok, tampilkan pilihan ke pengguna, jangan menimpa diam-diam.
- **Risiko utama proyek:** sinkronisasi offline (dua perangkat mengubah work order yang sama). Uji lebih awal.
- Matriks konflik lengkap per entitas: `ISI:` (disusun di fase PWA, lihat prompt P1 di metaprompt).

## 4. Keamanan dan otorisasi
- Revisi 2026-11-04: SO Selesai hanya dapat diubah Owner; invoice diterbitkan dari
  realisasi final sebelum pembayaran. Pembatalan dengan biaya tidak menghapus
  realisasi dan pembayaran. Gateway memerlukan verifikasi server dan idempotensi;
  tombol simulasi prototype tidak membuktikan transaksi nyata. Hak edit invoice
  draf dan rancangan refund rinci tetap terbuka (CONTEXT §2.2).
- Autentikasi: Sanctum **[DIPUTUSKAN]**; login username + password **[DIPUTUSKAN 2026-10-31]**. Implementasi AUTH-01 memakai SPA cookie/session same-origin dengan CSRF; bukan bearer token. Kontrak, batas dan sumber migration pada `../BSD/auth-01.md`.
- Otorisasi: spatie/laravel-permission; peran **Owner, Teknisi, Kasir** (Supervisor dihapus, 2026-10-31). Divalidasi di server.
- HPP/pengeluaran terbatas hanya dikirim API ke Owner. Teknisi/Kasir boleh menerima harga jual dalam konteks WO/invoice/transaksi; endpoint laporan profit dan audit log Owner-only. **[DIPUTUSKAN 2026-10-31, CONTEXT §2.1]**
- Edit harga jual transaction-local: server menyimpan snapshot master + nilai hasil edit per baris dokumen, dan menulis entri log perubahan harga (nilai lama, baru, aktor, waktu, identitas dokumen/baris, alasan). Log lengkap hanya terbaca Owner. Skema kolom log: BSD (belum diisi).
- Koreksi invoice final: endpoint Owner-only; server menolak koreksi dari peran lain; riwayat pembayaran tidak boleh ditulis ulang oleh koreksi.
- UI yang menyembunyikan elemen bukan pengganti otorisasi server (aturan arsitektur 2); visibility di FigCraft bukan bukti keamanan.
- Rahasia (`.env`, kunci gateway) tidak ditempel ke AI dan tidak masuk repo.
- Mass assignment dan validasi input: Form Request.

## 5. Perangkat dan integrasi
- Perangkat target: laptop dan ponsel **[DIPUTUSKAN]**.
- Printer/pemindai: sudah ada tapi belum pernah dipakai. Merek dan jenis: `ISI:`.
- Sistem ponsel: `ISI:` (Android atau iPhone; menentukan cara cetak).
- Cara cetak nota dari ponsel: **BELUM DIPUTUSKAN [ASUMSI]**. Web Bluetooth tidak didukung semua browser (CONTEXT §3.2 mengutip MDN: bukan Baseline, eksperimental). Android + Chrome mungkin bisa langsung cetak, perlu uji dengan printer asli; iPhone butuh alternatif (dialog cetak, PDF, atau cetak dari laptop).
- Jalur cadangan pasti: nota sebagai PDF atau tampilan cetak biasa.

## 6. Non-fungsional
Belum ada target terukur yang diputuskan.
| Hal | Target |
|---|---|
| Waktu muat halaman utama | ISI: |
| Penerimaan kendaraan (jumlah langkah/waktu) | ISI: (lihat PRD §3) |
| Cadangan data dan pemulihan | ISI: |
| Skor Lighthouse PWA | ISI: |
| Jumlah pengguna dan cabang | ISI: (PRD §6 #6) |

## 7. Strategi pengujian
Aturan kerja (metaprompt): setiap fitur disertai test jalur utama dan minimal satu jalur gagal.
- Backend: Pest. Frontend: Vitest. E2E: Playwright. Kinerja/PWA: Lighthouse.
- Skenario wajib yang sengaja melanggar aturan: akses lintas peran (harus 403), stok minus, harga master berubah setelah item ditambahkan, request ganda dengan idempotency key sama, koneksi putus di tengah proses.
- Test harus benar-benar bisa gagal bila logika rusak; jangan percaya klaim "test lulus" tanpa hasil nyata di terminal.

## 8. Aturan kerja agent (dari metaprompt)
- Jangan menambah library di luar stack tanpa alasan dan alternatif.
- Jangan membuat fitur di luar irisan yang sedang dikerjakan.
- Bahasa: penjelasan Indonesia; kode, nama file, istilah teknis bahasa aslinya; nama tabel/kolom bahasa Inggris; label UI bahasa Indonesia.

## 9. Perbedaan antar sumber dan hal terbuka
| Hal | Metaprompt | CONTEXT.md | Dipakai |
|---|---|---|---|
| Database | `{{MySQL \| PostgreSQL}}` (belum dipilih) | MySQL | MySQL |
| Laravel | "Laravel" tanpa versi; PHP 8.2+ | Target Laravel 13, PHP 8.3+ (pembaruan 2026-10-29) | CONTEXT; [rilis resmi Laravel 13](https://laravel.com/docs/13.x/releases) mendukung PHP 8.3–8.5 |
| Role | Teknisi bukan pengguna | Owner/Teknisi/Kasir; harga jual lokal WO/invoice, HPP Owner-only | CONTEXT §2.1 (2026-10-31) |
| Offline | "akses offline terbatas" | draf saja; bayar/stok/invoice online | CONTEXT |
| Payment gateway | tidak ada | Ditunda ke pengembangan berikutnya | Pembayaran saat ini mengikuti CONTEXT §2.2; tanpa integrasi gateway |
| Pengeluaran stok | Saat pembayaran berhasil | Saat invoice final diterbitkan; reservasi MySQL, tanpa Redis dahulu (2026-11-06) | CONTEXT §2.4; menggantikan aturan lama |

### Lingkup prototype browser 2026-11-04

User meminta HTML/CSS/JS dengan data dummy, bertahap (IPD WEB-01). Ini pengecualian
implementasi prototype terhadap stack produksi §1, bukan migrasi stack. Penyimpanan
lokal prototype terisolasi dari `dokterac_v2`; bukan database produksi, sinkronisasi,
PWA, atau autentikasi server. Revisit saat migrasi ke stack produksi.
| Deployment | VPS (Nginx + PHP-FPM) | Kembali ke VPS (2026-11-01); pilihan shared hosting dibatalkan, penyedia/paket belum dipilih | VPS (Nginx + PHP-FPM), HTTPS wajib |

## 10. Berkas terkait
- PRD: `../PRD/prd.md` · AFD: `../AFD/afd.md` · BSD: `../BSD/bsd.md` · IPD: `../IPD/ipd.md`
