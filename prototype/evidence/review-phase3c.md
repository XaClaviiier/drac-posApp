# Penutupan WEB-03C — 2026-11-07

## Hasil

**Observed:** penyerahan realisasi SO, antrean kasir turunan, queued lock dan
penarikan Owner beralasan sudah diimplementasikan pada prototype HTML/CSS/JS.
Tidak ada dependency, backend, invoice, pembayaran atau stok nyata baru.

Keputusan user bersumber pada CONTEXT §2.6. Kontrak JSON dummy hanya pada BSD §3.2;
AC, pilihan demo dan status pada IPD WEB-03C. Penyerahan Teknisi tidak memberikan
hak merevisi biaya SO terminal. Selama queued, Owner juga harus menarik sebelum
revisi biaya atau reopen. Antrean bukan invoice/pembayaran.

## Arsitektur dan perubahan

- `handoff.js` menampung eligibility, replay validasi history, panel penyerahan/
  penarikan dan renderer antrean. Antrean dihitung dari SO, bukan collection duplikat.
- `service-orders.js` mengintegrasikan renderer, dirty guard dan lock progres.
- `realization.js` memeriksa queued lock pada handler, bukan hanya disabled kontrol.
- `app.js` menambah navigasi/peran untuk antrean dan mempertahankan mekanisme
  konflik revision/reload existing; `index.html` menambah panel dan halaman terkait.
- Store version 1 dipertahankan; SO tanpa handoff terbaca tanpa rewrite/reseed.
  Tidak ada migrasi database. Boolean antrean saja ditolak karena kehilangan
  riwayat penarikan/penyerahan ulang; model history khusus lebih kecil daripada
  menyatukan seluruh workflow menjadi event engine umum.

## Verifikasi segar

| Pemeriksaan | Hasil | Artefak / waktu UTC |
|---|---|---|
| `node --check` enam JS: items/app/diagnosis/handoff/service-orders/realization | Exit 0 | Output terminal sesi ini |
| Python 3.12 `prototype/tests/phase3c_browser.py` | Exit 0, 14 kelompok lulus | `verification-phase3c.json`, `2026-11-07T02:30:11.945113+00:00` |
| Regresi Fase 1 | 20 kelompok lulus | `verification-phase1.json`, `2026-11-07T02:30:04.006976+00:00` |
| Regresi Fase 2 | 16 kelompok lulus | `verification-phase2.json`, `2026-11-07T02:30:10.703191+00:00` |
| Regresi Fase 3A | 12 kelompok lulus | `verification-phase3a.json`, `2026-11-07T02:30:05.507506+00:00` |
| Regresi Fase 3B | 17 kelompok lulus | `verification-phase3b.json`, `2026-11-07T02:30:16.555051+00:00` |

Interpreter: `C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe`.
Regresi dijalankan melalui `rtk test`; laporan JSON diperiksa untuk hasil lengkap.
Seluruh laporan mencatat `passed: true` dan error aplikasi yang direkam kosong.
Context browser terisolasi; masing-masing runner memiliki server loopback berport
dinamis dan cleanup `finally`, tidak menggunakan profil pelanggan/pengguna.

Tes baru mencakup:

1. Menu/kosong, legacy tanpa write dan penolakan SO aktif.
2. Dirty realisasi dan konfirmasi batal tanpa autosave/write.
3. Teknisi menyerahkan Selesai; Kasir memeriksa kendaraan dan total yang benar.
4. Lock queued pada submit biaya dan reopen Owner, serta duplikasi/handler Kasir.
5. Owner menarik dengan alasan, revisi dan serahkan ulang; tanpa duplikasi,
   snapshot estimasi tetap, teks markup tidak dieksekusi.
6. Pergantian peran membersihkan daftar antrean dan history Owner dari DOM Teknisi.
7. Gagal write penyerahan maupun penarikan, retry tidak replay dan input tetap ada.
8. Konflik penarikan tab lain, alasan lokal dipertahankan, navigasi dirty dibatalkan.
9. Reflow/tema/keyboard/fokus pada halaman dan panel baru.
10. Gate mandiri: terminal tanpa realisasi tersimpan ditolak Owner/Teknisi;
    Kasir ditolak pada SO unqueued yang seluruh syarat lain sudah terpenuhi.
11. Selesai Rp0 diberi label tanpa biaya, Dibatalkan Rp0 ditolak, Dibatalkan
    berbiaya hanya Owner. Nominal memakai realisasi Rp70.000, bukan estimasi Rp100.000.
12. Peristiwa ke-100 tersimpan dan pulih; ke-101 ditolak tanpa pemangkasan history.
13. Lima belas injeksi null/array kosong, aktor, counter, waktu, ID, urutan,
    historical lock, edit biaya dan reopen ketika queued ditolak tanpa reseed.

Nomor daftar mengelompokkan cakupan, bukan mengganti jumlah 14 kelompok pada JSON.

## Red/green dan review terpisah

Tracer awal menu gagal karena `#nav-cashier` belum tersedia:
`failure-phase3c-20261107T015958163264.json`. Setelah menu ditambahkan, tracer lulus.
Tracer penyerahan berikutnya gagal karena `#handoff-send` belum tersedia:
`failure-phase3c-20261107T020335211275.json`, lalu lulus setelah panel/handler dibuat.
Kegagalan disimpan; tidak ada assertion dilemahkan.

Planner mengusulkan field opsional dan counter lintas riwayat. Implementasi
mengikuti rencana tersebut; pilihan demo (biaya nol, submit ulang dan batas event)
dicatat sebelum kode. Tidak ada perluasan ke invoice atau arsitektur produksi.

Reviewer correctness menemukan gap tes: gate Kasir sebelumnya tertutup oleh
penolakan duplikasi, dan gate realisasi belum tersimpan tertutup oleh status aktif.
Tes mandiri ditambahkan, lulus, lalu reviewer menutup gap. Tidak ada defect kode
blocking/important yang dibuktikan oleh review. Security reviewer menjalankan
probe Node callback/validator read-only dan tidak menemukan blocker dalam scope.
Re-review keduanya membaca kode, assertion serta laporan browser segar; tidak
menjalankan ulang seluruh suite secara independen.

## Referensi dan pemeriksaan visual

Reference lock existing tetap. Riset tambahan 3C memakai halaman live:
- https://www.shopmonkey.io/product/workflow — status pekerjaan, riwayat dan
  keterhubungan pekerjaan ke tahap invoice; dipinjam untuk hierarki tugas.
- https://www.shopmonkey.io/product/invoices — pelanggan, kendaraan dan rincian
  terhubung tanpa entry ganda; bukan keputusan metode bayar atau skema harga POS.

Refero gagal `NO_SUBSCRIPTION`; jalur lama `/features/...` gagal 404 sebelum
halaman `/product/...` berhasil dibaca. Tidak mengklaim mengekstrak token atau
melihat screenshot aplikasi Shopmonkey baru. Token POS dan ledger DBD tetap berlaku.

Enam screenshot antrean desktop 1440/tablet 768/mobile 390 light/dark dibuka dan
diperiksa, serta detail `phase3c-handoff-error-320.png` dengan riwayat terbuka.
Tes memeriksa lebar 320/620/1049/1050/1280, teks 200%, Enter pada Periksa SO dan
fokus alasan invalid. Tidak ada perubahan CSS atau token. Detector Impeccable
dijalankan sekali pada file UI terdampak dan hanya menandai Inter existing di HTML;
font dipertahankan karena keputusan proyek. Bukan audit WCAG atau performa penuh.

## Kontrol keamanan scoped

| Kontrol | Bukti | Status |
|---|---|---|
| Peran/status pada handler, termasuk kontrol hidden/disabled | Synthetic send/withdraw/biaya/reopen dan gate mandiri | Green untuk simulasi |
| Queued lock lintas history | Counter/waktu/urutan divalidasi; injeksi edit saat queued dan sebelum withdrawal ditolak | Green, konsistensi lokal |
| Batas transaksi klien | Failed write/konflik/retry tidak menambah event atau replay | Green untuk konflik sequential |
| Output teks dan visibilitas history | Markup sebagai teks, daftar/history dibersihkan pada role-switch | Green untuk DOM |
| Auth, API, audit tahan manipulasi, kerahasiaan storage | Belum ada backend/login nyata | Unverified untuk produksi |

Permukaan yang dinilai: role demo, callback input, persist/reload localStorage,
history dan DOM. Server/session/SQL/upload/gateway bukan permukaan implementasi
3C. PRD §9 belum tersedia; gate keamanan produksi tetap terbuka. Tidak ada klaim
kepatuhan ASVS, otorisasi server atau audit tahan manipulasi.

## Batas, pemulihan dan langkah berikutnya

- Race write simultan localStorage belum dijamin; revision check bukan transaksi atomik.
- Penguasaan storage memungkinkan rekayasa history yang konsisten. Role demo bukan
  boundary autentikasi/kerahasiaan dan data harus tetap fiktif.
- Alasan penarikan yang belum tersimpan tidak pulih otomatis dari crash/force-close.
- Screen reader, browser selain Chromium, ponsel fisik dan printer belum diuji.
- Pilihan demo Rp0/submit ulang tidak menetapkan kebijakan invoice produksi.
- Rollback kode pra-3C pada origin berisi handoff tidak aman karena build lama
  mengabaikan lock. Gunakan origin/salinan data dummy terpisah untuk mencoba build
  lama; jangan menghapus riwayat atau membuka lock dengan mengedit storage.

**Recommended:** irisan berikutnya Fase 4 invoice dan pembayaran, setelah kontrak
hak invoice draf serta perilaku nominal nol diselaraskan. 3C selesai tidak berarti
invoice atau pembayaran sudah tersedia.
