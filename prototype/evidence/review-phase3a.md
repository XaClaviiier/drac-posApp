# Review dan delivery 3A

## Bukti aktual

- Sintaks `app.js`, `diagnosis.js`, `service-orders.js`: `node --check`, exit 0.
- Python Playwright 3A: exit 0, **12 kelompok** lulus. Regresi Fase 1: **20**;
  Fase 2: **16**, keduanya exit 0. Laporan JSON masing-masing di folder ini.
- Tracer menu SO dijalankan sebelum implementasi dan gagal, lalu lulus setelah
  wiring fitur. Laporan failure red dipertahankan. Satu setup tes berikutnya
  mencoba klik reset tersembunyi setelah event sintetis (tanpa input); setup
  diperbaiki, assertion penolakan transisi ilegal tetap ada.
- Tujuh screenshot dibuka: desktop/tablet/mobile light/dark dan daftar mobile.
  Detail/form/history serta daftar diuji sampai 320 px dan font 200%. Keyboard Tab,
  submit Enter, fokus error dan reset diperiksa; bukan audit screen reader penuh.

## Review terpisah

Reviewer correctness menemukan tiga finding minor: reset kehilangan fokus,
error tidak terkait/fokus ke kontrol, serta bukti narrow/keyboard dan IPD belum
lengkap. Kode/fokus/ARIA dan tes diperbaiki. Reviewer closure menutup dua finding
kode; bagian tes pada finding ketiga ditutup, status IPD diperbarui primary sesudah
closure. Tidak ada blocker kode tersisa dari finding tersebut. Fallback fokus
heading saat read-only ada pada kode, belum diuji khusus.

Reviewer security menjalankan ketiga suite pada konteks terisolasi tanpa menulis
artefak proyek, menemukan tidak ada blocker di scope dummy. Replay tambahan untuk
duplikasi ID, teknisi palsu, from palsu dan timestamp mundur dipromosikan menjadi
regresi permanen oleh primary. Peran/audit browser bukan autentikasi atau bukti
tahan manipulasi; penyunting localStorage dapat mengarang riwayat konsisten.

## Delivery gate

- PASS R-02/R-17/R-18/R-23/R-36/R-38: copy UI baru tanpa em dash, teknisi/data/harga
  contoh berlabel, tanpa logo/avatar/testimoni/klaim transaksi produksi.
- PASS R-03/R-34: reflow desktop/tablet/mobile pada light/dark diperiksa, tidak ada
  overflow pada lebar/zoom yang diuji. Tidak menyatakan keyboard ponsel fisik diuji.
- PASS R-24/R-26/R-35: menu SO, cari/filter, buka detail, tautan registrasi/diagnosa,
  pilih teknisi, mulai/tunda/lanjut/selesai/batal/reopen, reset, konfirmasi, retry,
  role dan tema memiliki perilaku. Kasir/invoice Fase 4 masih teks roadmap.
- PASS R-25: warna/token existing; detector tidak memberi advisory kontras baru.
  Warning Inter dipertahankan karena pilihan proyek. Pasangan token diuji pada
  regresi Fase 1; bukan klaim WCAG menyeluruh.
- PASS R-27: daftar kosong/tidak ada hasil, loading lokal existing, validasi,
  storage error, conflict, pending action dan sukses terpisah. Retry tidak replay.
- PASS R-28/R-32: tanpa FAQ; elemen native berlabel dan fokus terlihat. Error
  memakai aria-describedby/aria-invalid dan fokus field; reset fokus ke action.
- PASS R-33/R-37: source melalui patch langsung, reference lock dan token existing
  dipakai ulang. Tidak ada riset Refero baru atau perubahan identitas visual.
- PASS purpose/liveliness/quality locks: Operate, ENERGY 1 / RHYTHM 2 / MOTION 2
  seperti fase sebelumnya. Plat menonjol, progres dan riwayat untuk tugas bengkel,
  tanpa gradien/glow/ilustrasi tambahan. Status selalu berlabel teks.

## Keputusan dan batas

Pilihan transisi demo dan batas penerapan bersumber di IPD WEB-03A, bukan keputusan
seluruh aturan produksi. SO tanpa workflow dibaca Belum dimulai, tanpa rewrite;
workflow malformed ditolak, bukan direseed. Snapshot finansial tetap identik dengan
estimasi disetujui. Progres Selesai/Dibatalkan belum finalisasi realisasi/antrean
kasir. Realisasi/revisi biaya 3B dan penyerahan kasir 3C belum dibangun.

localStorage hanya deteksi konflik sequential, bukan transaksi atomik. Isian
tindakan lokal tidak disimpan permanen sebelum apply; navigasi/unload normal
memperingatkan, crash/force-close dapat kehilangan isian tersebut. Histori/data
besar, browser selain Chromium, screen reader dan perangkat ponsel fisik belum diuji.
Gap keamanan produksi tetap terbuka; persyaratan existing pada TRD §4, bukan klaim
PRD §9 selesai. Tidak ada login server, invoice, gateway, stok atau pembayaran nyata.
