# Audit UI/UX POS — 12 November 2026

## Ringkasan dan cakupan

**Rekomendasi lead: Impeccable.** Masalah utama ada pada urutan tindakan, pencegahan kesalahan dan pemulihan, bukan kebutuhan mengganti identitas visual.

Target: `prototype/index.html`, halaman panduan preview, serta CSS/JS aktif. Pengguna: Owner, Teknisi dan Kasir yang non-teknis. Mode Operate. Reference lock existing pada DBD dan token `DESIGN_POS_Extend.md` dipertahankan: shadcn/native, aksen biru, terang/gelap. Legacy `index.html` ROOT, FigCraft historis dan kelengkapan backend produksi bukan target penilaian implementasi.

Metode: dua penilaian terpisah, A `UxDesignAssessment` (UX/source/browser) dan B `UiTechnicalAssessment` (detektor dan pengukuran browser). A selesai sebelum hasil detektor B masuk sintesis. Parent juga memeriksa alur/error dan membaca screenshot. Bukan pelaksanaan lengkap command critique: overlay/injeksi/live-server Impeccable dan snapshot critique bertanggal tidak dijalankan. Audit tidak mengubah UI, data pengguna, konfigurasi atau dependency. Hanya laporan ini dan catatan IPD ditambahkan/diperbarui.

**8 temuan: 1 P1, 7 P2.** P1 mengganggu penyelesaian pekerjaan; P2 memiliki workaround tetapi membebani pengguna. Tidak ada P0 yang ditemukan pada sampel ini; bukan jaminan seluruh kombinasi state bebas blocker.

## Temuan prioritas

### U1 — P1: Teknisi bisa menutup SO sebelum realisasi tersimpan

- **Lokasi:** `prototype/service-orders.js:12,218-228`, `prototype/realization.js:6,134-142`, `prototype/handoff.js:10-17`.
- **Repro teramati:** context latihan baru, peran Teknisi, buka DD 1248 KL, pilih **Tandai selesai**, konfirmasi sebelum realisasi pertama tersimpan. Pesan sukses muncul, lalu input realisasi terkunci dan **Serahkan ke kasir** tidak bisa dipakai karena realisasi belum disimpan. Owner diperlukan untuk memulihkan.
- **Dampak:** tindakan yang tampak berhasil justru membuat Teknisi tidak dapat menyelesaikan alur operasionalnya sendiri. Ini konflik urutan UX, bukan alasan membuka hak edit Teknisi pada SO terminal.
- **Rekomendasi:** sebelum menutup, periksa kesiapan realisasi dan arahkan ke **Simpan realisasi** jika belum ada. Konfirmasi menjelaskan konsekuensi penguncian. Pertahankan batas peran dan riwayat. Realisasi tanpa biaya tetap harus dicatat eksplisit bila memang tidak ada biaya.
- **Skill:** Impeccable `harden`; verifikasi lintas progres–realisasi–handoff dengan Playwright existing.

### U2 — P2: Uang diterima dan kembalian tidak diringkas sebelum konfirmasi tunai

- **Lokasi:** `prototype/index.html:194,198`, `prototype/invoices.js:159-160,227-235,242-243`.
- **Repro teramati:** invoice contoh Rp100.000 di viewport ponsel; isi uang diterima `1000000`. Tidak ada preview kembalian Rp900.000 sebelum konfirmasi; dialog tidak menyebut nominal. Pada sampel 390×844, sisa tagihan berada sekitar 962 px di atas tombol pembayaran. Dialog dibatalkan.
- **Dampak:** Kasir harus mengingat nominal dan menghitung kembalian sebelum keputusan terakhir. Ini bukan bukti ledger menghitung salah; penerimaan bersih dan kembalian sesudah penyimpanan tidak dinilai ulang.
- **Rekomendasi:** tampilkan sisa tagihan, uang diterima, dan kembalian berdampingan dengan aksi pembayaran; konfirmasi menyebut nominal serta identitas invoice. Pertahankan aturan lunas penuh dan tunai boleh lebih.
- **Skill:** Impeccable `harden`/`clarify`; `better-writing` untuk kalimat konfirmasi.

### U3 — P2: Pesan error pembayaran berada di luar viewport

- **Lokasi:** `prototype/index.html:196-198`, `prototype/invoices.js:95,227-232`.
- **Repro teramati dua penilaian:** nominal kosong atau 0 pada invoice belum lunas, lalu **Catat pembayaran penuh**. Fokus kembali ke nominal, tetapi pesan berada di atas viewport. B mengukur pada 390×900: error y=-145,72 px, input y=259,06 px; pada 320 px: error y=-192,22 px. Parent juga mengamati error sepenuhnya di atas viewport pada desktop.
- **Dampak:** pengguna visual mendapat fokus tanpa alasan penolakan yang terlihat. `aria-describedby` dan `role=alert` tersedia; `aria-invalid` input belum ditandai. Screen reader tidak diuji.
- **Rekomendasi:** error lokal di dalam form pembayaran dekat field yang gagal, berikut status invalid yang disetel/dibersihkan; simpan error global untuk masalah invoice menyeluruh. Gunakan pola validasi registrasi yang sudah baik.
- **Skill:** Impeccable `harden`, `fixing-accessibility`.
- **Batas standar:** relevan dengan identifikasi error, tetapi penempatan di atas form tidak otomatis melanggar WCAG. Temuan ini adalah visibilitas error pada repro tersebut, bukan putusan kepatuhan.

### U4 — P2: Kunjungan berulang sulit dibedakan pada daftar diagnosa

- **Lokasi:** `prototype/diagnosis.js:315-332`, `prototype/index.html:131-134`.
- **Repro teramati:** dua registrasi dengan plat, nama dan keluhan sama tampil identik pada daftar diagnosa. Nomor/waktu kunjungan tidak ditampilkan; nama aksesibel tombol juga hanya aksi dan plat.
- **Dampak:** petugas berisiko membuka kunjungan lama ketika pelanggan kembali. Kunjungan berulang memang diperbolehkan; bukan data duplikat yang boleh dihapus otomatis.
- **Rekomendasi:** tampilkan nomor registrasi dan waktu kunjungan; sertakan pembeda pada nama tombol. Pencarian/filter mengikuti pola daftar registrasi bila diperlukan.
- **Skill:** Impeccable `clarify`, `fixing-accessibility` untuk nama berkonteks.

### U5 — P2: Draf registrasi tidak memiliki tindakan buang/mulai kosong

- **Lokasi:** `prototype/app.js:120-137,222-227`, `prototype/index.html:70-74,96-118`.
- **Repro teramati:** isi lima kolom, kembali, lalu buka registrasi. Seluruh isian dipulihkan dan aksi utama berubah menjadi **Lanjutkan registrasi**, tetapi tidak ada tindakan eksplisit membuang draf pelanggan yang batal.
- **Dampak:** petugas harus mengosongkan atau menimpa kolom satu per satu untuk pelanggan berikutnya. Autosave/pemulihan itu sendiri adalah kekuatan, bukan bug.
- **Rekomendasi:** tindakan sekunder **Buang draf dan mulai baru**, dengan konfirmasi yang jelas. Hapus draf terkait saja, bukan seluruh localStorage atau registrasi tersimpan.
- **Skill:** Impeccable `harden`/`clarify`, `better-writing` untuk konsekuensi aksi.

### U6 — P2: Kelengkapan wajib untuk persetujuan diagnosa baru dijelaskan setelah ditolak

- **Lokasi:** `prototype/index.html:143-154`, `prototype/diagnosis.js:251-280`.
- **Repro teramati:** tekan **Catat persetujuan lisan** saat kosong; baru kemudian muncul syarat hasil pemeriksaan, saran, minimal satu item dan konfirmasi lisan. Label belum menjelaskan kewajiban kontekstual tersebut.
- **Dampak:** Teknisi mengetahui kontrak penyelesaian lewat percobaan yang gagal.
- **Rekomendasi:** jelaskan empat syarat sebelum aksi persetujuan, berbeda dari **Simpan draf** yang boleh parsial. Jangan menambahkan `required` secara global sehingga draf parsial gagal disimpan.
- **Skill:** `better-writing`, Impeccable `clarify`; `fixing-accessibility` untuk semantik kondisional.

### U7 — P2: Nama tombol invoice tidak membedakan dokumen

- **Lokasi:** `prototype/invoices.js:111-116`.
- **Repro teramati:** dua invoice berbeda sama-sama memiliki tombol bernama **Buka invoice**, tanpa `aria-label`/`aria-labelledby` yang mengaitkannya dengan identitas baris.
- **Dampak:** navigasi berdasarkan daftar tombol sulit membedakan tujuan tanpa membaca ulang article. Efek nyata pada screen reader belum diuji; tombol memiliki nama dasar, jadi tidak dinyatakan sebagai kegagalan WCAG 4.1.2.
- **Rekomendasi:** nama aksesibel mencakup nomor invoice/plat, mengikuti pola daftar existing. Teks visual boleh tetap pendek.
- **Skill:** `fixing-accessibility`, Impeccable `clarify`.

### U8 — P2: Jalur pemulihan data lokal rusak masih meminta pengetahuan teknis

- **Lokasi:** `prototype/app.js:298-344,417-422`, `prototype/index.html:61-64`.
- **Repro teramati parent:** raw localStorage yang tidak valid dipertahankan; muncul **Pulihkan akses/data prototype, lalu coba lagi**. Menekan **Coba lagi** menampilkan pesan yang sama tanpa panduan pemulihan yang bisa diikuti pengguna awam.
- **Dampak:** sistem gagal dengan aman, tetapi petugas tidak tahu langkah berikutnya ketika akses/data belum dipulihkan.
- **Rekomendasi:** pisahkan panduan izin penyimpanan dari data rusak; sediakan bantuan pemulihan atau jalur ekspor salinan untuk dukungan. Jangan reset otomatis, menimpa raw data, atau membuat fallback seed palsu.
- **Skill:** Impeccable `harden`, `better-writing`.

## Gap kontrak yang sudah diketahui, bukan temuan baru

UI SO masih membedakan teknisi utama/anggota pada `prototype/index.html:209-219` dan `prototype/service-orders.js:20-23`. CONTEXT §2.3 keputusan 11 November menetapkan semua Teknisi setara. IPD DB-01 sudah mencatat prototype belum diselaraskan. Penyelarasan perlu mencakup model/validasi dan riwayat, bukan sekadar mengganti label. Tidak dimasukkan kembali ke delapan temuan di atas.

## Yang perlu dipertahankan

- Bahasa visual operasional konsisten, identitas kendaraan menonjol, tanpa dekorasi yang tidak melayani tugas. POS dua panel desktop menjadi detail mobile.
- Validasi registrasi menjelaskan kesalahan di dekat field, menandai invalid dan memfokuskan field pertama. Draf dapat dipulihkan.
- Tidak ditemukan overflow horizontal pada 72 snapshot dasar: 1440/390/320 px, terang/gelap. Probe root font 32 px pada registrasi/invoice juga tidak meluber. Ini bukan sertifikasi zoom/browser/perangkat fisik.
- Tab mengembalikan ring fokus 2 px; menu mobile, Escape dan pengembalian fokus bekerja pada kasus yang diperiksa. Target sentuh label checkbox diuji, bukan dinilai dari kotak checkbox kecil saja.
- Tidak ditemukan rasio teks enabled sampel yang settled di bawah 4,5:1 setelah komposit warna foreground/background solid. Tidak mencakup seluruh kontrol native, gambar/pseudo-element atau semua state.
- Pengukuran reduced-motion mempertahankan status/fokus statis. Tidak teramati error console/page/request pada perjalanan yang selesai diamati.

## Detektor dan batas skor

Detektor bundled dijalankan sekali, exit 2: dua warning, bukan crash. `overused-font` adalah pengecualian yang dipin (Inter dipilih dalam token proyek). `cramped-padding` tidak terbukti pada total-row yang diperiksa: padding computed 16 px atau container 20 px memang tersedia. Keduanya tidak dihitung sebagai defect dan tidak menjadi alasan mengganti font atau menambah padding secara membabi buta. Detector melaporkan line 0; lokasi itu tidak diperlakukan sebagai baris source yang valid.

Skor heuristik A berikut bersifat subjektif atas sampel, bukan benchmark, sertifikasi atau ukuran keseluruhan sistem.

| Heuristik Nielsen | Skor /4 |
|---|---:|
| Status sistem terlihat | 3 |
| Sesuai dunia pengguna | 3 |
| Kendali dan kebebasan | 2 |
| Konsistensi | 3 |
| Pencegahan error | 2 |
| Mengenali, bukan mengingat | 2 |
| Efisiensi | 2 |
| Minimalisme visual | 3 |
| Pemulihan error | 2 |
| Bantuan/panduan | 3 |
| **Total sampel** | **25/40** |

B memberi indikasi aksesibilitas/theming/responsif 3/4 dan integritas implementasi 4/4 pada cakupan teknisnya. **Performa tidak diberi skor:** tidak ada tracing, throttling, Core Web Vitals atau profiling. Tidak ada total teknis /20 agar aspek yang belum diperiksa tidak tampak lulus.

## Skill yang disarankan dan urutannya

| Peran | Skill | Kapan dipakai |
|---|---|---|
| Lead | **impeccable** | `harden` untuk U1/U2/U3/U5/U8; `clarify` untuk U4/U6/U7; `polish` hanya setelah perbaikan terfokus. Satu owner, bukan beberapa workflow desain paralel. |
| Microcopy terfokus | **better-writing** | Instruksi persetujuan, nominal/konsekuensi konfirmasi dan panduan pemulihan; bukan mengganti istilah bisnis tanpa keputusan. |
| Aksesibilitas lokal | **fixing-accessibility** | Error field dan nama tombol berkonteks; bukan klaim audit WCAG menyeluruh. |
| Verifikasi | **webapp-testing** | Gunakan Python Playwright existing, context/data dummy terisolasi; uji regresi lintas tahap, bukan screenshot saja. |
| Audit tambahan opsional | **accessibility** | Jika user menghendaki cakupan WCAG 2.2 menyeluruh, termasuk teknologi bantu. Tidak perlu menjadi reviewer kedua untuk seluruh UI saat ini. |

Tidak perlu memasang skill/dependency baru, mengganti library, mengaktifkan Taste/Hallmark/Unslop, atau melakukan redesign besar untuk temuan ini. Refero/reference lock existing dipakai ulang; tidak ada riset Refero MCP baru atau klaim hasil layanan berlangganan. Helper context Impeccable melaporkan pembaruan tersedia, tetapi tidak ada update/install dijalankan.

## Verifikasi dan keterbatasan

B: 72 snapshot dasar + 24 pengukuran terarah pada Chromium headless. A: desktop 1440×1000 dan ponsel emulasi 390×844; B memakai tinggi 900. Parent menguji error registrasi, pembayaran dan data lokal rusak. Navigasi/percobaan invalid parent tidak mengubah ledger latihan; raw data rusak tetap sama. Dialog pembayaran A dibatalkan. Tidak ada pembayaran riil, browser profile pengguna atau akses akun.

Dua probe sementara sempat salah memilih elemen (parent mengasumsikan satu H1 pada POS dua panel; B memilih draf bukan invoice final). Keduanya dikoreksi sebagai error probe, bukan dilaporkan sebagai bug aplikasi. Build/lint/suite regression existing tidak dijalankan, supaya evidence existing tidak ditimpa. Tidak ada implementasi perbaikan pada pekerjaan ini.

Belum diperiksa: screen reader/perangkat fisik, Firefox/WebKit, seluruh kombinasi role/status, semua konflik/offline boundary, cetak OS/printer dan backend/gateway/stok produksi. Dampak perilaku pengguna adalah penilaian ahli, bukan hasil studi dengan petugas bengkel.

Source utama: `doc/CONTEXT.md`, `doc/AFD/afd.md`, `doc/DBD/dbd.md`, `doc/DBD/DESIGN_POS_Extend.md`, ROOT `workflow/DESIGN.md`, source dan browser prototype aktif.

Standar primer yang dirujuk (bukan sertifikasi):
- https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html — minimum AA 24×24 dengan pengecualian; target proyek sendiri 44 px, bukan otomatis ambang AA.
- https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html — identifikasi error dengan teks; standar tidak mewajibkan satu pola penempatan tertentu.

Bukti mentah/screenshot diperiksa di direktori temporer OS lalu dibersihkan. Laporan tunggal ini dan catatan IPD dipertahankan agar folder proyek tidak dipenuhi dump audit berulang. Server loopback khusus audit sudah dihentikan.

## Penutupan perbaikan WEB-08

Setelah persetujuan user, U1–U8 diterapkan tanpa redesign atau perubahan skema.
Sebelas runner browser lulus (Fase 1/2/3A/3B/3C/4, POS, preview, UI, fokus, UX).
Guard completion diuji untuk Owner/Teknisi, tanpa realisasi, realisasi dirty,
konfirmasi batal, terminal dan pembacaan riwayat lama. Lima kelompok UX tambahan
menguji draf batal/quota/konflik, kunjungan berplat sama, draf diagnosa parsial,
nominal/error pembayaran, nama invoice dan backup raw rusak tanpa overwrite.
Ringkasan bukti: `verification-ux.json`; detail pelaksanaan: IPD WEB-08.

Keterangan read-only dan keterbatasan di atas merekam tahap audit awal, bukan
status implementasi sesudah persetujuan. Batas produksi/perangkat fisik tetap.
