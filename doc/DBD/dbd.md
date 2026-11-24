# DBD: Design Brief Documentation — POS Bengkel AC Mobil

Dokumen ini menjawab: **seperti apa tampilannya dan bagaimana rasanya dipakai.**
Bergantung pada PRD dan AFD.

Sumber awal: `../CONTEXT.md` §5 (arah visual), §6 (konten nyata), §7 (batasan);
token dan aturan visual lengkap ada di `DESIGN_POS_Extend.md` dan
`workflow/DESIGN.md` (di ROOT). Dokumen ini hanya merangkum keputusan dan
menautkan ke sana, tidak menyalin token.

---

## 1. Arah visual
| Hal | Keputusan |
|---|---|
| Kesan | ISI: |
| Warna dominan / hex biru merek | ISI: |
| Terang atau gelap | ISI: |
| Kerapatan | ISI: |
| Yang dilarang | ISI: |

## 2. Referensi

### Konsep redesign Stitch 2026-11-15

Prototype FigCraft aktif kini di
[`prototype/figcraft/pos-kasir.figcraft`](../../prototype/figcraft/pos-kasir.figcraft).
Cara mencoba, batas dan bukti ada di
[`prototype/figcraft/README.md`](../../prototype/figcraft/README.md).
File First pair dan paket handoff di bawah dipertahankan sebagai riwayat.

Paket acuan untuk konstruksi FigCraft live:
[`figcraft-handoff-v1/README.md`](figcraft-handoff-v1/README.md).
Manifest membekukan source/screenshot dan membedakan state yang belum dirender.
Runtime attached digunakan untuk membangun layer kasir native di file utama.
Pelengkapan terbaru mencakup kasir, Registrasi, Diagnosa & Estimasi serta
penugasan, progres, realisasi dan penyerahan SO, serta alur invoice/pembayaran/nota
kunjungan Maya, serta pelanggan/kendaraan dan riwayat lintas kunjungan contoh
pada desktop/ponsel, tema dan komponen;
hasil pemeriksaan serta batas interaksi tercatat di README file utama dan IPD.

Status: arah grid, biru dan palet pendukung disetujui user; Poppins dipilih dari
permintaan Gotham/Poppins. Hasil konsep masih untuk tinjauan. Pelaksanaan
bertahap per irisan mengikuti IPD. Token hanya di DESIGN_POS_Extend.

- Primary: screenshot 3 kiriman user, kartu transaksi dengan identitas di atas,
  waktu, pemisah, dua baris item, total dan status. Plat bengkel mendahului nama.
- Borrow: screenshot 1 untuk pengelompokan rincian/pembayaran setelah memilih
  kartu; screenshot 2 untuk sidebar berlabel dan pemisahan surface putih/abu-abu.
- Role rules: biru untuk aksi utama/pilihan; kategori dan status memakai peran
  warna usulan di DESIGN_POS_Extend. Nominal menggunakan angka tabular.
- Media: ikon garis dan data dummy; tanpa foto makanan, model kendaraan rekaan,
  logo final, pilihan cabang atau metrik restoran.
- Ditolak: panel kanan permanen yang mempersempit grid sebelum ada pilihan,
  status restoran, kartu berwarna acak, dan pembayaran langsung dari SO.
- Alur tetap: SO diserahkan atau memiliki invoice masuk POS; default menunggu
  proses. Klik SO hanya preview; buat invoice draf merupakan aksi eksplisit.
  Ringkasan setelah invoice bersumber snapshot invoice; total/sisa dibedakan.
- Bukti referensi: tiga gambar user, bukan hasil pencarian Refero. MCP Refero
  tidak tersedia pada sesi ini. Riset existing dipakai untuk alur yang tetap.

Riset warna: [Labrecque & Milne](https://doi.org/10.1007/s11747-010-0245-y)
meneliti warna dan persepsi kepribadian merek, bukan performa POS bengkel.
[Elliot](https://pmc.ncbi.nlm.nih.gov/articles/PMC4383146/) menekankan konteks
dan keterbatasan generalisasi. Rekomendasi untuk POS adalah konsistensi makna,
hierarki dan kontras; tidak mengklaim biru otomatis menenangkan atau meningkatkan
kepercayaan semua pengguna. Nilai palet hanya di DESIGN_POS_Extend.

### Referensi existing

3–5 tautan, masing-masing dengan apa yang diambil (kualitas penggarapan, bukan disalin).
| Tautan | Yang disukai |
|---|---|
| https://react-aria.adobe.com/ | Referensi utama komponen UI, keputusan user 2026-11-02. Cakupan perilaku/aksesibilitas dan batas penerapan mengikuti CONTEXT §3.1; token visual tetap di DESIGN_POS_Extend.md. |
| https://www.shopmonkey.io/ | Primary: papan pekerjaan, identitas kendaraan, alur bengkel; hero produk telah dilihat. |
| https://cursor.com/ | Karakter sans-serif dan hierarki clean; font asli belum terverifikasi. |
| https://linear.app/ | Referensi eksplisit user; akses live hanya mengembalikan Loading, tidak diklaim telah diekstrak. |
| https://calendly.com/ | Permukaan terang dan disiplin aksen; warna POS ditentukan sendiri di token, bukan disalin. |
| https://21st.dev/@starc007/components/animated-sidebar | Model sidebar expand/collapse, submenu dan mobile sheet; metadata tersedia, source belum diperoleh. Rekonstruksi diizinkan user. |
| https://shadcnuikit.com/components/command (`@shadcnuikit/command1`) | Referensi visual pencarian global disetujui user 2026-10-31: input atas, baris hasil berikon dalam kelompok, state kosong. Struktur diadaptasi ke token POS; JSON komponen dibaca sesi sebelumnya, tidak dipasang sebagai dependency. |

### Reference lock prototype UI-01

Revisi browser WEB-06 (2026-11-11) memakai [Button](https://ui.shadcn.com/docs/components/button),
[Field](https://ui.shadcn.com/docs/components/field) dan
[Sidebar](https://ui.shadcn.com/docs/components/sidebar) resmi shadcn/ui.
Pembagian peran: shadcn untuk hierarki/varian kontrol, pengelompokan label/input/error,
serta navigasi; identitas kendaraan dan alur tetap dari brief bengkel existing.
Ditolak: migrasi React hanya untuk styling, dashboard baru tanpa kebutuhan, dan
penggantian dialog konfirmasi browser yang berpotensi mengubah kontrak tindakan.
Dialog native tetap seragam dan dapat dioperasikan dengan keyboard; visualnya
mengikuti browser/OS. Token revisi hanya pada DESIGN_POS_Extend.md.

Primary Shopmonkey: identitas kendaraan mendahului metadata, area kerja dipisah dari
navigasi, papan status dan pencarian terlihat. Pinjaman dibatasi pada karakter
tipografi Cursor/Linear, arah warna Calendly dan perilaku sidebar starc007.
Reject: pill untuk semua kontrol, grid dekoratif, font mono untuk seluruh data,
dashboard angka tanpa tindakan. Rancangan menggunakan konten bengkel dan label data
contoh; token hanya di DESIGN_POS_Extend.md bagian prototype.

### Direction contract

- **THESIS:** satu ruang kerja dari plat nomor ke nota; area kerja menjadi fokus.
- **OWN-WORLD:** token prototype pada DESIGN_POS_Extend.md, Inter, biru interaksi,
  hijau keberhasilan, komponen rata kiri dan pemisah yang mengelompokkan data.
- **STORY:** cari kendaraan, catat keluhan, lanjutkan pekerjaan, tinjau tagihan.
- **FIRST VIEWPORT:** sidebar kiri, breadcrumb dan tema di atas; judul serta aksi
  utama sejajar; konten pekerjaan di bawah dengan plat yang langsung terbaca.
- **FORM:** arah dipatok user dan dikonfirmasi; tidak ada undian konsep.
- **FINISH:** frame diperiksa dengan render dan inspeksi; persetujuan visual user
  diperlukan sebelum prototype browser. Interaksi FigCraft bukan bukti backend.

### Decision ledger dan hasil UI-01

| Keputusan | Sumber dan peran | Alasan |
|---|---|---|
| Plat lebih menonjol daripada metadata | Brief alur bengkel dan primary Shopmonkey | Kendaraan dikenali sebelum catatan pekerjaan dibaca. |
| Form penerimaan, papan WO, kasir dua area, riwayat berurutan | 11 menu baseline dan AFD | Komposisi mengikuti tugas, bukan satu pola kartu untuk semua menu. |
| Tipografi UI dan warna semantik | Token prototype DESIGN_POS_Extend | Menjaga keterbacaan tabel/form serta membedakan aksi dari status. |
| Teks utama pada navigasi aktif dan badge biru | Verifier kontras UI-01 | Biru aksi di surface aktif menghasilkan 4,325:1; teks utama existing memenuhi kontras tanpa mengganti token warna. |
| Sidebar ciut dan menu mobile | Brief starc007, rekonstruksi diizinkan | Mengurangi chrome pada ruang sempit dan mempertahankan akses menu. |
| Foto/logo tidak ditambahkan, data diberi label contoh | Nama/logo/harga final belum tersedia | Artefak tidak menyiratkan identitas atau harga produksi. |
| Mekanik memiliki graf navigasi terpisah tanpa harga | CONTEXT §2 dan AFD | Pratinjau tugas tidak mengarah ke kasir/laporan berharga. |
| Kartu/detail contoh terbatas, daftar invoice statis | Review UI-01 | Pilihan tidak boleh membuka kendaraan atau tagihan berbeda tanpa penjelasan. |
| Login dua panel: identitas bengkel kiri, form kanan; demo peran sebagai tombol eksplisit | Handoff §4.1; anti-slop R-26 | Peran demo adalah kontrol nyata beralur, bukan form mati; hindari kartu login generik terpusat. |
| Shell demo per peran (Kasir terbatas) alih-alih menduplikasi 11 menu per peran | Handoff §10 constraints | Satu jalur demo per peran membuktikan destinasi; duplikasi penuh melanggar batas "reuse variants". |
| Palet pencarian = overlay di atas shell dengan scrim, kelompok hasil berlabel | `@shadcnuikit/command1` (pinjaman struktur) | Token warna/radius/tipografi tetap POS; hanya struktur yang dipinjam. |
| Hover/pressed native pada instance kontrol, galeri menampilkan fokus/disabled | Handoff §4.6; constraint reuse | FigCraft memakai changeTo antar-variant via mouseEnter/mouseLeave/mouseDown/mouseUp; tidak menduplikasi layar penuh. Playback/keyboard tetap perlu verifikasi tersendiri. |
| Estimasi WO sebagai tabel itemized dengan total dihitung, demo edit harga menampilkan "harga master tidak berubah" | Handoff §4.3/§4.5 (keputusan user) | Rumus qty×harga dan penyalinan WO→invoice adalah keputusan, bukan dekorasi. |

Artefak dan preview: [prototype/README.md](prototype/README.md). Empat halaman
FigCraft mencakup desktop/mobile dan light/dark. Status pelaksanaan dan bukti akhir
tetap bersumber pada IPD UI-01; nilai token tetap hanya di DESIGN_POS_Extend.

## 3. Komponen utama

### WEB-04P: POS sebagai beranda Kasir

Target direct-build disetujui user pada CONTEXT §2.8. Reference lock existing
tetap: identitas kendaraan, status berteks, Inter dan token prototype. Refero
subscription diketahui tidak tersedia; referensi live Shopmonkey workflow dibaca
ulang pada 2026-11-07. URL bantuan Square yang dicoba mengarah ke artikel login,
bukan bukti layout checkout, sehingga tidak dipakai untuk menjustifikasi komposisi.

| Keputusan | Sumber | Penerapan |
|---|---|---|
| Antrean kiri/detail kanan laptop, daftar dahulu pada mobile | Persetujuan user §2.8; ledger UI-01 kasir dua area | Sibling grid pada main, satu editor invoice existing; tanpa menduplikasi form pembayaran |
| Plat/nama lebih menonjol, status dan nominal mengikuti tugas | Shopmonkey workflow live; primary existing | Nominal final memakai sisa, SO/draf memakai total, label membedakannya |
| Default menunggu proses; filter kerja/tagihan dan pencarian dokumen | Brief POS user | Draf stale bertanda Perlu Owner; nota baru lunas tetap terbuka |
| Pilihan tidak membuat transaksi otomatis | AFD dan dirty/conflict guard existing | Preview SO lalu tombol Buat invoice, callback sukses baru mengganti pilihan |
| Layar cetak hanya receipt | Kontrak WEB-04 | Invoice tetap anak langsung main; layout grid dimatikan pada print |

Mode Operate. Breakpoint shell existing dipakai dan diuji reflow; daftar sempit
memiliki override lokal, bukan mengubah seluruh tabel. Fokus pindah ke detail
setelah pilihan; kembali pada ponsel membawa pengguna ke daftar. Tidak ada token,
dependency atau arah merek baru.

### Ekstensi browser WEB-03C

Ekstensi WEB-04 menggunakan reference lock yang sama dan riset live invoice
Shopmonkey yang sudah dibaca: identitas kendaraan/pelanggan dan rincian transaksi
terhubung tanpa entry ulang. Layar invoice memisahkan rincian tersimpan, harga Owner,
aksi final dan penerimaan uang. Status dokumen dan status pelunasan dibedakan teks;
Rp0 final tetap Lunas. Panel bayar menonjolkan sisa, uang diterima dan kembalian,
bukan menambahkan kartu statistik. Nota cetak putih/hitam statis dengan watermark
simulasi, tanpa navigasi/editor/log. Token baru tidak diperlukan. Perilaku bersumber
pada CONTEXT §2.7 dan AFD §2.4, bukan pemasangan gaya/komponen baru.

Reference lock UI-01/WEB-03B dipertahankan. Riset live 2026-11-07:
`https://www.shopmonkey.io/product/workflow` menjelaskan status pekerjaan dan
riwayat; `https://www.shopmonkey.io/product/invoices` menghubungkan pelanggan,
kendaraan dan rincian tanpa entry ganda. Refero screens gagal `NO_SUBSCRIPTION`;
URL lama `/features/...` mengembalikan 404, lalu jalur `/product/...` dibaca.
Tidak mengklaim ekstraksi screenshot atau computed style baru.

| Keputusan | Sumber | Alasan |
|---|---|---|
| Daftar antrean menonjolkan plat, nama, SO, status asal dan total realisasi | Shopmonkey workflow/invoices dan pola daftar SO existing | Kasir mengenali pekerjaan sebelum membaca nominal; tidak entry ulang |
| Panel penyerahan pada detail SO, terpisah dari progres dan realisasi | CONTEXT §2.6 | Penyerahan tidak disalahartikan sebagai simpan biaya atau pembayaran |
| Tarik dengan alasan dan konfirmasi, lalu serahkan ulang eksplisit | Keputusan user §2.6 | Rincian kasir tidak berubah diam-diam |
| Antrean khusus Kasir/Owner; Teknisi melihat status penyerahan di SO | Peran existing dan pembagian tugas AFD | Ruang kerja mengikuti tugas, bukan tombol invoice palsu |

Token, font, radius, target sentuh dan light/dark mengikuti DESIGN_POS_Extend,
mode Operate, ENERGY 1 / RHYTHM 2 / MOTION 2. Daftar bertumpuk pada mobile,
panel memakai form/error/fokus existing; tanpa media atau gerak dekoratif baru.

### Ekstensi browser WEB-02

Ekstensi berikutnya WEB-03A memakai pola daftar, form dan timeline pada token yang
sama. Menu SO aktif untuk pencarian/filter dan detail progres. Status memakai
label teks, isian tindakan eksplisit, dialog konfirmasi native untuk terminal/
reopen, serta error yang terkait ke kontrol dan memindahkan fokus. Rincian estimasi
tetap read-only; pembatalan/selesai tidak menyiratkan tagihan final. Bukti aktual
dan gate: `../../prototype/evidence/review-phase3a.md`.

Reference lock UI-01/UI-04 dan token prototype tetap berlaku. Alur bisnis terbaru
bersumber pada CONTEXT §2.2: tabel estimasi kini berada pada form Diagnosa &
Estimasi, bukan entry ganda di WO. Form browser memakai kelompok temuan, saran,
baris estimasi, ringkasan biaya dan pengakuan persetujuan lisan. Snapshot approved
read-only dan preview SO membuktikan handoff; progres pekerjaan tetap Fase 3.
Nama Draf/Disetujui adalah state dokumen demo, bukan keputusan seluruh status
pemeriksaan. Preview FigCraft historis tidak diregenerasi atau ditimpa.

Keputusan layout: informasi kunjungan dan keluhan mendahului pemeriksaan; baris
estimasi bertumpuk pada mobile dan memakai kolom qty/harga/subtotal pada desktop.
Ini perluasan pola form/tabel existing untuk tugas operasional, bukan arah visual
baru. Bukti screenshot dan review: `../../prototype/evidence/review-phase2.md`.

| Komponen | Dipakai di | Catatan (ukuran sentuh, status) |
|---|---|---|
| Form login (username, password, tombol demo peran) | P-01 | Target sentuh ≥44 px; label "login simulasi" pada prototype |
| Palet pencarian global (struktur command1) | P-12 | State awal/hasil/kosong/memuat/error/terpilih; scrim + token di `DESIGN_POS_Extend.md` |
| Tabel estimasi WO | P-03 | Kolom jenis/item/qty/satuan/harga satuan/subtotal; subtotal jasa+part=total; demo edit harga lokal |
| Badge status invoice (Draf/Final/Revisi) + form koreksi Owner | P-04, P-14 | Status warna+teks (CONTEXT §7); koreksi wajib alasan; riwayat pembayaran utuh |
| Tabel audit log | P-13 | Kolom waktu/aktor/aksi/dokumen/lama→baru/alasan; Owner-only |
| Galeri state interaksi | UI-04 | default/hover/fokus/pressed/disabled per keluarga kontrol; token hanya di `DESIGN_POS_Extend.md` |

## 4. Responsif dan perangkat
- Laptop: ISI:
- Ponsel: ISI:
- Ukuran target sentuh minimum: ISI:

## 5. Konten
- Bahasa antarmuka: Indonesia, tanpa istilah teknis yang tidak dipahami orang awam.
- Format uang: `Rp 1.250.000`
- Istilah baku dan nama aksi: ISI:

## 6. Aksesibilitas
- Status tidak dibedakan hanya dengan warna.
- Kontras dan ukuran teks: ISI:

## 7. Berkas terkait
- AFD: `../AFD/afd.md`
- Token lengkap: `DESIGN_POS_Extend.md`
