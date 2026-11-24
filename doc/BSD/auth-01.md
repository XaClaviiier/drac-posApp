# AUTH-01 — kontrak implementasi autentikasi

Dokumentasi skema/API aktif untuk irisan login, bukan pengesahan seluruh DB-02.
Rancangan dan batas: [rencana AUTH-01](../IPD/auth-01-plan.md).

## Sumber fisik

Definisi kolom/indeks/constraint aktif berada pada migration di
`../../application/database/migrations/`. Migration akun memakai UUID ASCII biner
untuk `users.id`; username unik, tanpa email wajib. Migration Spatie memakai ID
BIGINT roles/permissions dan UUID morph key. Tabel sesi framework memakai UUID
nullable untuk user; driver lokal default file, driver database ikut diuji.
Migration cache/jobs dari skeleton merupakan infrastruktur, bukan modul bisnis.

Tambahan terhadap draf SQL DB-02: `auth_events` dengan aktor nullable, event,
identifier HMAC, IP opsional dan waktu. Aktor yang tidak diketahui pada login gagal
bukan pengguna rekaan. Ini berbeda dari audit domain DB-02 yang aktornya wajib.
FK aktor historis memakai RESTRICT. Audit tidak menyimpan password, cookie, token
atau username mentah untuk percobaan login anonim. Retensi IP/audit belum ditetapkan.
DB-02 tetap snapshot rancangan seluruh sistem; bukan file migration runtime AUTH-01.

## HTTP same-origin

| Metode | Path | Perilaku | Penolakan |
|---|---|---|---|
| GET | `/sanctum/csrf-cookie` | Framework membentuk cookie CSRF/sesi | Tidak memberi sesi login |
| POST | `/login` | Username/password, respons identitas akun dan path workspace | 422 validasi/kredensial generik; 429 limit; 419 CSRF |
| GET | `/api/session` | Identitas pengguna dan workspace default dari server | 401 tamu/nonaktif/tanpa akses |
| POST | `/logout` | 204; invalidasi sesi server dan rotasi CSRF | 401/419 bila sesi/form tidak sah |
| GET | `/api/workspaces/{workspace}` | Identitas akun, workspace dan izin yang diberikan | 401 belum login; 403 tidak berhak; 404 workspace tidak dikenal |

Identitas yang dikirim: `id` UUID string, `username`, `name`, array `roles`.
Workspace default adalah `/workspace/owner`, `/workspace/teknisi`, atau
`/workspace/kasir`; user tidak memilih peran lewat request login. Respons tidak
menyertakan hash password atau remember token. Endpoint API yang tidak dikenal
menghasilkan JSON 404, bukan template HTML.

Route workspace memerlukan sesi web, Sanctum, akun aktif, peran dan permission
workspace yang sesuai. Owner boleh memasuki ketiganya; Teknisi hanya Teknisi,
Kasir hanya Kasir. Permission langsung yang diberikan tanpa peran terkait tidak
mempromosikan Kasir menjadi Owner. Permission `workspace.*` hanya untuk irisan
akses akun, bukan izin bisnis pembayaran/stok yang belum diimplementasikan.

Login menormalisasi username ke lowercase/trim, tetapi tidak memangkas password.
Field role/roles/permissions/is_active dilarang pada login. Lima percobaan per
username ternormalisasi dan IP selama 60 detik; hasil throttled tidak membedakan
akun ada/tidak. Limit tersebut tidak menggantikan proteksi distributed attack di
hosting. Username pada perintah akun dibatasi huruf ASCII kecil/angka/titik/garis
bawah/hubung, diawali huruf/angka. Password akun baru minimal 12 karakter dan
maksimal 72 byte sesuai hashing bcrypt; input tersembunyi dan dikonfirmasi.

Sesi cookie, bukan token API: HttpOnly/SameSite Lax, ID diregenerasi saat login,
logout menghapus sesi lama. HTTP lokal memakai Secure=false; produksi wajib
HTTPS/Secure=true. Tidak ada signup publik, endpoint ganti peran atau password
bawaan. Pembuatan akun melalui `php artisan pos:create-user` memerlukan akses
terminal yang sah dan mencatat event tanpa membocorkan password.

## Batas aplikasi

`/login` dan `/workspace/*` menyajikan shell React; server memeriksa data dan izin
pada API. Shell sendiri tidak memuat data pengguna/keuangan. Login tidak memberi
akses otomatis ke modul POS yang belum dibuat. Tidak mengaktifkan seluruh SQL
DB-02, fitur pembayaran, PWA offline atau sinkronisasi data bisnis.

Cara menjalankan dan test: [README aplikasi](../../application/README.md).
Hasil nyata: [verifikasi AUTH-01](../IPD/auth-01-verification.json).
