# POS Bengkel AC Mobil — aplikasi

Irisan AUTH-01: login username/password, sesi cookie Sanctum, logout dan akses
workspace Owner/Teknisi/Kasir dari database. Ini aplikasi nyata, bukan pemilih
peran demo. Landing menampilkan informasi akun/izin, bukan dashboard atau
transaksi bisnis yang belum diimplementasikan.

## Menjalankan lokal yang sudah disiapkan

Dari folder `application`, jalankan MySQL di terminal terpisah:

```powershell
powershell -NoProfile -File scripts/local-db.ps1 start
```

Jalankan aplikasi memakai hasil build frontend:

```sh
composer dev
```

Buka `http://127.0.0.1:8088/login`. Buat akun awal pada terminal interaktif:

```sh
php artisan pos:create-user
```

Pilih peran dan masukkan password tersembunyi minimal 12 karakter, maksimal
72 byte. Tidak ada password bawaan, registrasi publik atau akun demo produksi.
Jangan menaruh password pada argumen shell atau mengirimkannya melalui chat.
Perintah tersebut mencatat pembuatan akun dalam audit internal.

Untuk menghentikan database secara bersih, gunakan terminal lain:

```powershell
powershell -NoProfile -File scripts/local-db.ps1 stop
```

Jangan mematikan paksa MySQL atau menjalankan dua instance pada datadir yang sama.

## Instalasi dari checkout baru

Prasyarat: PHP 8.3+ dengan ekstensi Laravel/PDO MySQL, Composer dan Node yang
kompatibel dengan lockfile Vite. Runtime yang digunakan dan bukti hasil dicatat
pada `../doc/IPD/auth-01-verification.json`.

1. Pasang dependency terkunci dengan `composer install`.
2. Untuk Windows lokal, ekstrak ZIP **resmi MySQL 8.4.13 winx64** yang diperiksa
   checksum-nya ke `../.local/mysql-8.4.13-winx64/`. Tidak perlu Docker/service.
3. Hanya pada setup baru tanpa datadir/`.env`, jalankan
   `php scripts/initialize-local.php`. Script membuat kredensial acak dan tiga
   database lokal terpisah, lalu menghentikan bootstrap. File lama tidak ditimpa.
4. Jalankan MySQL dengan perintah start di atas.
5. Jalankan `php artisan migrate --seed` pada database development baru yang telah
   dipilih. Jangan gunakan konfigurasi database existing/produksi.
6. Jalankan `npm ci` dan `npm run build`, lalu `composer dev`.
7. Buat akun melalui perintah interaktif, bukan mengedit database langsung.

Database lokal hanya mendengarkan `127.0.0.1:13306`; MySQL X Protocol dimatikan.
MariaDB XAMPP dan database existing tidak digunakan atau diubah. Akun aplikasi
hanya diberi hak pada tiga database POS lokal, bukan database sistem MySQL.
Kredensial berada pada `.env*` dan `../.local/`, diabaikan Git dan berada di luar
document root. Jangan mengunggah folder runtime/data lokal atau file test ke hosting.
Bootstrap Windows bukan installer produksi dan tidak dipakai pada database lama.

## Stack dan struktur

- Laravel 13, Sanctum, Spatie Permission dan MySQL 8.4.
- React + TypeScript strict, React Router, React Hook Form + Zod, TanStack Query.
- Vite, Tailwind dan Poppins yang di-host sendiri.
- `app/Services`: login/audit; controller tipis dan izin diperiksa server.
- `resources/js`: UI dan pemanggilan API same-origin.
- `database/migrations`: irisan auth serta infrastruktur framework.
- `tests/Feature`: Pest/MySQL terisolasi; `tests/e2e`: browser/CSRF nyata.

Versi tepat mengikuti `composer.lock` dan `package-lock.json`. Tidak memakai
Inertia, JWT/localStorage auth, SSR atau Node server di hosting. Theme boleh
tersimpan pada browser; sesi dan peran selalu berasal dari server.

## Pengujian

Pest hanya diizinkan menuju MySQL lokal `pos_auth_testing`; guard menolak target
lain sebelum RefreshDatabase. Jangan mengganti guard agar test berjalan pada
database development/produksi.

```sh
composer test
npm test
npm run build
php artisan migrate --env=e2e --no-interaction
php scripts/e2e-fixtures.php setup
npx playwright test
php scripts/e2e-fixtures.php cleanup
```

Browser memakai Chrome yang sudah terpasang. Database `pos_auth_e2e` terpisah dan
aplikasi berjalan pada `127.0.0.1:8089`. Konfigurasi e2e memakai APP_ENV lokal agar
middleware CSRF benar-benar aktif. Trace/video dimatikan supaya cookie/password
fixture tidak ikut direkam. Screenshot hanya diambil ketika password tidak terlihat.
Setelah pengujian, cleanup menonaktifkan akun uji, merotasi password dan menghapus
file kredensial sementara; audit dipertahankan. Ini tidak membuat akun pada
database development.

## Batas keamanan dan produksi

Cookie sesi HttpOnly, SameSite Lax, sesi terenkripsi dan kedaluwarsa setelah
120 menit tidak aktif. Password di-hash framework; login dibatasi per username/IP.
Mode lokal HTTP memakai cookie non-Secure; **produksi wajib HTTPS dan
`SESSION_SECURE_COOKIE=true`, `APP_ENV=production`, `APP_DEBUG=false`**.
Tidak menyediakan pendaftaran/reset password publik atau hak admin melalui UI.
Audit autentikasi internal mencatat kejadian, aktor bila ada, hash identifier dan
IP; jangan menyajikannya ke peran umum. Retensi audit perlu ditetapkan sebelum
pemakaian data nyata.

Untuk shared hosting, pastikan PHP/ekstensi sesuai, versi database didukung,
document root menunjuk `public`, direktori storage/cache dapat ditulis, HTTPS
tersedia dan migration/command akun dapat dijalankan secara terkontrol. Aset React
dibuild lokal lalu diunggah; Node tidak perlu berjalan sebagai server. Jangan
memindahkan `.env` ke `public`. Belum ada provider/paket yang diuji atau deployment.

Skema lengkap DB-02 pada `../doc/BSD/` masih draf; tidak diimpor sekaligus.
Registrasi, diagnosa, SO, stok, invoice, laporan dan PWA/offline bukan bagian AUTH-01.
Prototype FigCraft/browser existing tetap dipertahankan.
