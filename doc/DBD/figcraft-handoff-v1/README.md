# Acuan POS untuk FigCraft live

Paket ini membekukan sumber desain yang sudah ditinjau user. Ini bukan hasil
konversi FigCraft dan belum membuktikan kesamaan piksel. `manifest.json` memetakan
layar, state, sumber, ukuran target, batas verifikasi dan hash berkas.

## Hasil percobaan pertama

Kandidat editable tersedia di
[`trial/pos-first-pair-refined.figcraft`](trial/pos-first-pair-refined.figcraft).
File berisi dua frame, 171 layer teks Poppins dan nol layer image; font yang hilang
tidak ditemukan. File tersimpan sudah diperiksa melalui CLI info. Desktop
1440×1000, ponsel lebar 390 dengan tinggi konten 1179 px. Dokumen baru dibuat dan
ditampilkan melalui koneksi live; file historis tidak disentuh.

Acuaan raster dan render native berdampingan tersedia di `trial/` dengan suffix
`-source.png` dan `-native-refined.png`. `trial/verification.json` memuat hasil
inspeksi dan beda piksel. Beberapa ikon, shadow dan rasterisasi belum identik;
ini hasil trial geometri tetap, belum komponen responsif atau prototype beralur.

## Otoritas

- Keputusan user: `../../CONTEXT.md`, khususnya metode pembayaran aktif.
- Token tunggal: `../DESIGN_POS_Extend.md`; jangan salin token baru ke DESIGN.md global.
- Perilaku: `../../AFD/afd.md` dan source aplikasi untuk kontrak existing.
- Gambar kiriman user menetapkan arah; HTML koreksi lokal mengatasi penyimpangan
  generator, termasuk nilai uang. Pratinjau pembayaran lokal adalah acuan metode
  terbaru: tunai, QRIS statis, transfer manual. Gateway tidak masuk lingkup ini.

## Isi dan batas

`sources/` berisi snapshot HTML; `screenshots/` berisi dua render Stitch yang
ditinjau. Ukuran piksel PNG tidak dianggap sama dengan ukuran viewport CSS.
Render desktop grid dari HTML yang dikoreksi dan setiap state pembayaran masih
perlu dibuat pada ukuran target yang sama sebelum dipakai untuk overlay.

HTML adalah spesifikasi visual/perilaku, bukan jaminan format impor native.
Ambil state DOM yang terlihat, bukan seluruh string dalam source; source masih
memiliki beberapa cabang historis yang ditimpa renderer konsep terbaru.

## Runtime terverifikasi

- Instalasi ditemukan di `C:\Program Files\ArtCraft\FigCraft`.
- `figcraft-cli.exe mcp --help` mengonfirmasi mode `--attach`.
- Probe headless `text.fonts` menemukan Poppins Regular, Medium, SemiBold, Bold
  dan gaya lain. Ini pemeriksaan font engine, bukan pengukuran teks native final.
- Aplikasi live dijalankan pada loopback port 7979. Probe attached berhasil
  membaca dokumen baru Untitled yang belum dirty; tidak ada perintah edit desain.
- Server attached melaporkan versi 0.18.1; metadata executable Windows sebelumnya
  mencantumkan 0.15.0. Gunakan kemampuan yang terbaca dari runtime, bukan angka
  metadata file saja. Bukti: `live-document-check.json` dan `live-tool-schemas.json`.
- Peluncuran pertama tidak bertahan; peluncuran kedua tetap dijaga oleh sesi
  proses shell. Koneksi perlu diperiksa lagi bila sesi/aplikasi sudah ditutup.

Pemeriksaan ulang read-only: jalankan `check_live.py` dengan Python312 proyek
saat aplikasi masih mendengarkan port 7979. Script hanya initialize dan
inspect_document. Ini jalur CLI MCP teruji, bukan registrasi MCP host permanen.
Tidak ada konfigurasi host yang diubah.

## Urutan konstruksi berikutnya

1. Tangkap acuan grid desktop 1440×1000 dan daftar ponsel 390×844 pada state yang
   sama; pastikan Poppins benar-benar dipakai dan aset termuat.
2. Buat dokumen kandidat baru dalam folder ini. Jangan menimpa
   `../prototype/pos-ui.figcraft` atau meregenerasi file historis dari builder lama.
3. Bangun satu pasangan layar dengan frame, teks dan komponen editable. Gunakan
   screenshot sebagai pembanding, bukan pengganti seluruh layer.
4. Periksa font nyata, geometri, pembungkusan, warna, nominal, clip dan scrolling;
   ekspor pada viewport/scale yang sepadan dan bandingkan overlay.
5. Sesudah pasangan pertama cocok, perluas ke detail/invoice/pembayaran/nota;
   hubungkan navigasi dan state, lalu uji playback, keyboard dan penyimpanan ulang.

Nama bengkel final, QRIS asli, bank/rekening/atas nama dan printer belum diberikan.
Penanda kosong dipertahankan; jangan membuat detail pembayaran yang tampak nyata.

## Verifikasi paket

Enam snapshot sumber/gambar memiliki SHA-256 yang dicatat dan diverifikasi saat
pembuatan paket. Seluruh tautan otoritas di manifest sudah diperiksa tersedia.
Log/probe bukan acuan tampilan dan tidak termasuk enam snapshot tersebut.
