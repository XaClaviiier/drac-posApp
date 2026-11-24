# Review dan delivery Fase 2

## Observed

- `node --check prototype/app.js` dan `node --check prototype/diagnosis.js`: exit 0.
- Python Playwright `phase2_browser.py`: exit 0, 16 kelompok pemeriksaan lulus;
  laporan timestamp dan detail di `verification-phase2.json`.
- Regresi `phase1_browser.py`: exit 0, 20 kelompok lulus. Selector baris registrasi
  kini dibatasi pada daftar registrasi, karena daftar diagnosa menambah baris pada
  section lain. Assertion jumlah/hasil sebelumnya tetap sama.
- Tidak ada console/page error pada alur normal. Store Fase 1 dan draf registrasi
  tetap utuh ketika diagnosa ditambahkan. Legacy index.html tidak diubah.
- Screenshot enam varian desktop/tablet/mobile light/dark dibuka, begitu juga
  approved desktop dan SO desktop. Lebar 320/390/620/768/1049/1050/1440 dan teks
  200% diuji untuk overflow. Bukan audit aksesibilitas menyeluruh.

## Review dan perbaikan

Review correctness terpisah awal menemukan log harga dapat hilang ketika input
sementara invalid dan alasan bisa tertinggal kosong setelah autosave. Perbandingan
harga kini kembali ke nilai valid terakhir/master; pelengkapan alasan mencatat
waktu dan aktor sendiri. Review berikutnya menemukan shallow-copy log mengubah
state sebelum write berhasil; diganti deep clone, diuji gagal alasan A lalu retry
alasan B. Reviewer menilai finding terakhir resolved dan memberi SHIP pada cakupan
finding tersebut. Navigasi registrasi kehilangan base style juga sudah ditutup.

Uji tambahan memeriksa konflik ketika tab lain menyetujui: menolak penggantian
mempertahankan isian dan jalur reload tetap tersedia; menerima menampilkan snapshot
approved. Tidak ada overwrite approved lewat handler setelah konflik.

Review security terpisah menjalankan pemeriksaan normal dan probe tambahan tanpa
menulis source proyek. Verdict terbatas layak prototype dummy. Hardening nonblocking:
collection/log belum dibatasi ukurannya menyeluruh dan belum ada stress test.
Role guard client bukan otorisasi/kerahasiaan server; ini bukan temuan bypass auth
karena UI secara eksplisit menyatakan simulasi.

## Delivery gate

- PASS R-02/R-17/R-18/R-23/R-36/R-38: copy tanpa em dash, data/harga fiktif berlabel,
  tanpa logo/avatar/testimonial/angka pemasaran atau klaim transaksi nyata.
- PASS R-03/R-34: reflow dan light/dark diuji pada tiga kelas lebar; tanpa overflow
  pada lebar yang dicatat. Qty/harga/subtotal reflow menjadi satu kolom di mobile.
- PASS R-24/R-26/R-35: kontrol Buat/Buka diagnosa, tambah/hapus item, simpan draf,
  persetujuan, copy/buka SO, kembali, tema dan role bekerja dalam pengujian.
  Fase 3/4 tetap berupa teks roadmap; tidak ada tombol pembayaran palsu.
- PASS R-25: token/foreground existing dipertahankan. Detector hanya memberi warning
  font Inter yang memang dipatok proyek; tidak ada advisory kontras pada scan ini.
  Pasangan token kontras diuji pada regresi Fase 1, bukan sertifikasi seluruh state.
- PASS R-27: empty item/list, initial loading existing, validasi per field, storage
  error, conflict, saved dan approved tersedia. Tidak ada fetch/loading buatan.
- PASS R-28/R-32: tanpa FAQ; form native berlabel, Tab/fokus, tombol native,
  checkbox verbal dengan label dan dialog konfirmasi native dapat dioperasikan.
- PASS R-33/R-37: source ditulis langsung; reference lock FigCraft dan token existing
  dipakai ulang. Tidak ada riset Refero baru yang diklaim.
- PASS purpose gate: identitas/keluhan di depan, tabel biaya dan total menjawab
  pekerjaan bengkel; tanpa gradien, glow, dekorasi, atau gambar tambahan.
- PASS liveliness/quality locks: mode Operate, ENERGY 1 / RHYTHM 2 / MOTION 2
  diwarisi Fase 1; biru aksi, status dengan teks, whitespace pemisah tugas,
  jumlah/uang tabular. Tidak ada penggantian font atau token sistem.

## Batas

Dokumen demo hanya Draf/Disetujui; status pemeriksaan lengkap belum diputuskan.
Qty pecahan belum didukung. SO baru berupa salinan rincian disetujui tanpa status
pengerjaan/realisasi. Tidak ada invoice/pembayaran/stok nyata. Satu salinan SO
dibuktikan pada urutan sequential, bukan transaksi atomik lintas-tab localStorage.
Belum diuji pada browser lain, screen reader atau keyboard ponsel fisik.
