# AGENTS.md — POS Bengkel AC Mobil

Aturan global ada di `../AGENTS.md` (ROOT). File ini hanya menambah aturan khusus POS.
Semua dokumen proyek ada di `doc/`.

## Mode kerja sesi
Ikuti SOP di `~/.config/opencode/AGENTS.md`: Caveman dan RTK aktif otomatis
pada sesi baru, tanpa pertanyaan aktivasi. Hormati perubahan mode oleh user.
Ponytail dipilih bersyarat per tugas setelah menilai kondisi sistem, beban yang
diketahui, risiko, dan potensi overengineering; evaluasi ulang saat tugas berubah.
Aturan aktivasi/persistensi global ini mengalahkan ketentuan lama di skill lokal.
Skill proyek ada di `.claude/skills/`:
- **caveman** (`.claude/skills/caveman/SKILL.md`): balasan chat ringkas, jawaban dulu. Bahasa balasan tetap Indonesia.
- **ponytail** (`.claude/skills/ponytail/SKILL.md`): perubahan terkecil yang menyelesaikan tugas penuh.
- **rtk**: saat aktif, gunakan wrapper eksplisit sesuai skill global; referensi proyek ada di `CLAUDE.md` (dibuat `rtk init`, jangan diedit manual). Hook global tidak dipasang.

Prioritas bila bertabrakan: aturan di file ini dan `../AGENTS.md` (ROOT) menang atas caveman dan ponytail.
- Caveman hanya mengatur gaya chat. Isi dokumen di `doc/`, komentar kode, dan commit ditulis normal.
- Pertanyaan, permintaan approval, dan peringatan risiko ditulis kalimat lengkap.
- Ponytail tidak mengurangi test jalur gagal yang diwajibkan `doc/TRD/trd.md` §7, validasi, dan otorisasi server.
- Laporan akhir tetap memuat asumsi dan hal yang belum diverifikasi (ROOT §12).

## Routing dokumen
Baca yang cocok SEBELUM membuat rencana. Jangan memuat dokumen yang tidak relevan.

| Jenis task | Baca |
|---|---|
| Semua task di POS | `doc/CONTEXT.md` (keputusan user, status keputusan) |
| Perilaku fitur, peran, lingkup | `doc/PRD/prd.md`, `doc/AFD/afd.md` |
| Teknologi, arsitektur, offline, keamanan | `doc/TRD/trd.md` |
| Tabel, kolom, API, validasi | `doc/BSD/bsd.md` |
| UI, tampilan, komponen | `doc/DBD/dbd.md`, `doc/DBD/DESIGN_POS_Extend.md` (lihat catatan di bawah) |
| Apa yang dikerjakan sekarang | `doc/IPD/ipd.md` (ambil satu irisan) |
| Menyusun prompt kerja per fase | `doc/metaprompt-pembentukan-sistem.md` |

Jika file yang dirujuk tidak ditemukan atau tidak terbaca: katakan, jangan mengarang isinya.

## Aturan
- **Satu fakta, satu dokumen sumber.** Skema tabel hanya di BSD, token visual hanya di
  `DESIGN_POS_Extend.md`. Dokumen lain menautkan, tidak menyalin.
- **Bila dokumen bertentangan:** `doc/CONTEXT.md` (keputusan user) menang atas metaprompt.
  Laporkan konflik ke user, jangan memilih diam-diam.
- **`ISI:` = belum diputuskan.** Jangan mengarang isinya; tanyakan bila menentukan hasil.
- **Satu irisan per sesi.** Kriteria uji ditulis di IPD sebelum eksekusi, dan verifikasi memakai
  hasil nyata (test, aplikasi dijalankan), bukan klaim "sudah benar".
- **Aksi yang butuh approval eksplisit:** hapus data, deploy, ubah skema yang sudah dipakai,
  ubah keputusan berstatus DIPUTUSKAN.
- Kegagalan yang berulang dicatat di bagian bawah file ini sebagai aturan permanen.

## Rujukan desain aktif
- `../workflow/DESIGN.md` tersedia di ROOT. Baca bersama `doc/DBD/DESIGN_POS_Extend.md`
  untuk tugas desain sesuai `doc/CONTEXT.md` §9. Catatan ketidakhadiran file adalah
  riwayat yang telah diselaraskan pada `doc/CONTEXT.md` §8, bukan blocker aktif.
- Pemilihan skill mengikuti Routing global; DESIGN.md menjelaskan metode dan
  pembagian tanggung jawab, bukan router aktivasi kedua. Token visual tetap bersumber
  pada `doc/DBD/DESIGN_POS_Extend.md`, dengan keputusan prototype di `doc/CONTEXT.md` §5.

## Pelajaran dari kegagalan
- Playback FigCraft memerlukan jendela yang tersedia untuk UI. Periksa bahwa `ui.inspect.preview.name` dan `frameSize` terisi sebelum menguji klik. Pada FIG-MAYA-INVOICE-01, model/file masih dapat dibaca dan diekspor ketika preview mengembalikan geometri null dan screenshot melaporkan UI tidak tersedia. Bedakan pemeriksaan model native dari playback GUI; catat gate yang tertunda dan jangan menyebutnya lulus hanya karena file valid.
- Uji state FigCraft: pasang instrumentasi sebelum membuka preview dan hapus setelah perjalanan selesai. Pada FIG-MAYA-INVOICE-01, penggantian interaksi saat playback membuat probe membaca kembali nilai awal; probe yang sudah dipasang sebelum perjalanan dapat memeriksa nilai Rp160.000, pilihan Teknisi dan pembayaran tanpa mengubah dokumen di tengah perjalanan. Jangan memakai mutasi dokumen untuk mengukur state runtime yang sedang diuji. Gunakan UTF-8 eksplisit saat membaca source Python sebagai AST pada Windows agar literal Unicode sama dengan source yang dieksekusi.
- FigCraft native: aksi yang diterima engine belum membuktikan state bertahan saat playback. Pada FIG-SERVICE-ORDER-01, `setVariable` diterima tetapi nilai berubah/hilang ketika navigasi dan varian kontrol dijalankan. Per-field finite modes teruji mempertahankan pilihan Teknisi, peran dan nominal pada runtime terpasang. Verifikasi journey berurutan dengan nilai nyata; jangan menyimpulkan perilaku runtime hanya dari keberhasilan konstruksi atau inspeksi action. Bukti ada di `prototype/figcraft/evidence/service-order-verification.json` dan `service-order-map.json`.
- Uji Apache lokal: jangan memakai label state TCP sebagai satu-satunya bukti listener. Pada ENV-01, endpoint HTTP aktif beberapa kali terbaca `FIN_WAIT_1`. Cocokkan PID respons HTTP dengan proses tes, periksa semua endpoint TCP milik PID hanya pada loopback/port uji, dan pastikan proses berhenti setelah tes. Simpan snapshot saat gate gagal; jangan menghapus assertion untuk meloloskan aktivasi.
- Uji browser dengan banyak context baru: bedakan kegagalan aplikasi dari aset lokal yang gagal dimuat. Simpan console/page error dan URL request gagal; jangan melonggarkan assertion startup. WEB-04 memakai backlog server tes 128 setelah runtime Python 3.12 terukur default 5 dan dua run mengalami `ERR_CONNECTION_REFUSED`. Backlog sebagai penyebab bersifat inferensi; sesudah penyesuaian tetap wajib menjalankan suite utuh dan memeriksa error kosong.
- Uji pointer FigCraft setelah navigasi atau gulir: tunggu posisi `presentScroll` dan hotspot tujuan tersedia sebelum mengirim klik. Pada FIG-CUSTOMER-HISTORY-01, preview pernah tetap di frame asal setelah aksi navigasi dan hotspot riwayat sempat tidak ditemukan setelah pembayaran. Runner memakai tunggu geometri terbatas serta satu percobaan klik ulang hanya bila masih di frame asal; tujuan salah dan nilai runtime salah tetap menggagalkan uji. Penyebab internal belum dibuktikan. Run lengkap sesudah perbaikan lulus 312 langkah dan 38 pemeriksaan nilai pada desktop/ponsel. Bukti kegagalan, inferensi dan pemulihan ada di `prototype/figcraft/evidence/customer-history-test-observations.json`; jangan menggabungkan langkah percobaan gagal menjadi klaim satu run lengkap.
