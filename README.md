# POS Bengkel AC Mobil

Repositori pengembangan aplikasi bengkel, dokumentasi sistem dan prototype.
Aplikasi nyata berada di `application/`; bukan pada root repositori.

- [Menjalankan aplikasi dan membuat akun](application/README.md)
- [Keputusan dan status proyek](doc/CONTEXT.md)
- [SQL database](doc/BSD/pos-schema.sql) dan [ERD](doc/BSD/erd.md), berstatus draf review
- [Prototype browser](prototype/README.md)
- [Prototype FigCraft](prototype/figcraft/README.md)

Irisan aplikasi yang sudah diimplementasikan adalah fondasi dan autentikasi
Owner/Teknisi/Kasir. Cakupan serta bukti pengujian mengikuti dokumentasi aplikasi;
prototype dan rancangan database tidak berarti seluruh modul bisnis sudah berjalan.

Folder `.local/`, file `.env`, kredensial, database lokal, session/cache, dependency
`vendor/` dan `node_modules/` tidak disimpan di Git. Siapkan lingkungan lokal sesuai
README aplikasi sebelum menjalankan source dari clone baru.
