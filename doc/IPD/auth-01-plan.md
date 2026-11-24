# AUTH-01 — Fondasi dan autentikasi

Status: implementasi diminta user; izin download dependency dan database terpisah
melalui form setup 2026-11-17. User menyerahkan rekomendasi engine lokal kepada
agent dan menanyakan hosting biasa. MySQL portable dipilih untuk lokal, tanpa
Docker/service; kelayakan shared hosting belum diverifikasi dan keputusan VPS
pada CONTEXT tidak diubah diam-diam.

## Tujuan dan kontrak

Satu aplikasi Laravel 13 pada `application/`, dengan React + TypeScript strict,
Vite, React Router, React Hook Form/Zod, TanStack Query dan Tailwind. Frontend
hasil build disajikan Laravel pada origin yang sama. Ini menghindari kebutuhan
Node server/SSR dan CORS lintas origin pada hosting. Tidak memakai Inertia atau
mengganti stack. PWA/offline fitur bisnis belum menjadi irisan ini.

Sanctum memakai sesi cookie HttpOnly/SameSite Lax dan CSRF, bukan bearer token
atau penyimpanan token di localStorage. Login username/password, session ID
berotasi saat login, logout menghapus sesi server. Sesi tidak aktif 120 menit
mengikuti konfigurasi; produksi mewajibkan HTTPS/cookie Secure. Spatie mengelola
peran Owner/Teknisi/Kasir dan izin server. Pengguna nonaktif ditolak juga ketika
sudah mempunyai sesi. Tidak ada registrasi publik, pemilihan peran di login,
reset password atau akun demo dengan password bawaan.

Landing irisan ini adalah informasi akun/sesi dan akses workspace sesuai peran;
bukan dashboard/layanan POS palsu. Halaman yang tidak berhak ditolak server.
API hanya mengirim identitas akun dan izin yang diperlukan; tidak mengirim hash
password atau data finansial. Modul bisnis tidak dibuat sebagai placeholder.

## Ancaman dan mitigasi

Credential stuffing: throttling username/IP, pesan salah kredensial generik,
hashing Laravel. CSRF/session fixation: middleware framework, CSRF cookie dan
regenerasi session ID. Privilege escalation: peran dari database, bukan request;
cek server setiap akses. XSS: React escaping, tidak ada token auth di storage
browser. Akun nonaktif/sesi lama/logout: middleware aktif dan invalidasi sesi.
Auth event audit disimpan server tanpa password/cookie/token atau raw credentials.
Akun awal dibuat lewat perintah Artisan interaktif dengan input password tersembunyi.

## Desain dan reference lock

Mode Operate; extend visual world existing, bukan arah baru. DESIGN.md ROOT dan
DESIGN_POS_Extend sudah dibaca penuh. Primary: DBD ledger login dua panel;
Poppins, token light/dark dan kontrol minimal 44 px dari DESIGN_POS_Extend.
Pelengkap live: https://ui.shadcn.com/blocks/login (kelompok label/input/error).
Refero MCP tidak tersedia; tidak mengklaim riset MCP. Identitas bengkel berupa
teks netral karena nama/logo final belum ada. Tidak memakai foto/ilustrasi atau
angka operasional palsu. Form di kanan pada desktop, urutan identitas/form pada
ponsel; konten rata kiri, satu aksi Masuk, kontrol tampilkan password dan tema.
Tidak menambah login demo peran pada aplikasi nyata. Gerak hanya state kontrol,
mematuhi reduced motion; fokus keyboard jelas.

## Rencana eksekusi

1. Siapkan MySQL 8.4 portable pada folder lokal diabaikan Git; datadir/port khusus
   loopback. Jangan menyentuh MariaDB, database existing atau Windows service.
2. Adopsi skeleton resmi Laravel 13, Sanctum dan Spatie yang cocok; kunci versi.
   Hanya migrasikan users/roles/permissions dan audit autentikasi untuk AUTH-01.
3. Implementasikan endpoint sesi/login/logout dan workspace berbasis izin, test
   Pest jalur sah/gagal; perintah akun awal tanpa default password.
4. Implementasikan React login dan landing akun menggunakan API nyata; tidak ada
   data bisnis simulasi. Build frontend dan jalankan browser desktop/ponsel.
5. Verifikasi MySQL migration, login tiga peran, password salah, akun nonaktif,
   sesi tamu/kedaluwarsa/logout, CSRF, throttling, manipulasi peran dan akses silang.
   Review keamanan/UI independen sesudah implementasi; catat bukti dan versi.

## Batas dan alternatif

Alternatif frontend terpisah ditolak untuk irisan ini karena menambah konfigurasi
origin/cookie/deploy tanpa kebutuhan. API token untuk first-party SPA ditolak
sesuai dokumentasi Sanctum. Docker tidak diperlukan untuk shared hosting dan
engine lokalnya tidak aktif. Portable MySQL menjaga target stack tanpa mengganti
MariaDB XAMPP atau membutuhkan layanan sistem.

SQL DB-02 tetap draf review; migrasi auth harus menyelaraskan bagian yang dipakai,
bukan mengimpor semua 53 tabel. Aturan refund/retur dan skema bisnis lain tidak
diaktifkan. Tidak deploy, tidak membeli hosting, tidak memakai akun/data nyata.

## Definition of Done

- Migration AUTH-01 berjalan pada MySQL aktual yang terisolasi; dependency terkunci.
- Login/logout dan izin tiga peran terbukti melalui test server dan browser,
  termasuk penolakan utama; tidak ada password bawaan atau kebocoran rahasia.
- Login/landing desktop dan ponsel mengikuti visual existing, serta catatan cara
  menjalankan dan keterbatasan disimpan di dokumen proyek.
