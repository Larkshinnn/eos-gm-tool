# PGR GM Tool

Dashboard web pribadi untuk mengelola data **PGR Local Server** dari MongoDB. Tool ini ditujukan untuk pemakaian lokal dan bekerja dengan database server yang dipilih sendiri; tool ini tidak mengelola akun atau server resmi PGR.

## Fitur

- **Akun:** melihat daftar akun lokal, memilih akun untuk diedit, mengubah password, dan menghapus akun.
- **Profil pemain:** mengubah level dan data profil, termasuk portrait, nameplate, medal, chat board, emoji, dan score title.
- **Karakter:** menambah karakter dan mengatur level, grade/evolution, skill, awakening, trust, fashion, support, serta perlengkapan karakter.
- **Senjata dan memori:** menambah, menghapus, meningkatkan, mengatur resonance, dan mengelola overrun senjata; memasang atau melepas senjata dan memori pada karakter.
- **Item dan stage:** menambah, mengubah, atau menghapus item; mencatat atau menghapus stage yang sudah diselesaikan.
- **Warzone Generator:** membuat konfigurasi lawan/NPC Warzone dari data yang tersedia di tool.
- **Status dan pengelolaan server opsional:** memeriksa status database, SDK, dan game server; jika diaktifkan serta executable dikonfigurasi, dashboard dapat memulai/menghentikan server, menampilkan log, dan mengedit konfigurasi server.
- Antarmuka tanpa proses build frontend terpisah, dengan pilihan bahasa yang tersedia di dashboard.

Perubahan data langsung ditulis ke MongoDB. Pilih akun dengan teliti dan buat backup database sebelum melakukan perubahan besar.

## Persyaratan

- Windows untuk `quick_start.bat`
- Python **3.12+**
- MongoDB yang dapat dijangkau
- Chrome atau Edge versi terkini

Frontend menggunakan HTML, CSS, dan JavaScript module biasa. Node.js tidak diperlukan.

## Menjalankan di Windows

Pastikan MongoDB lokal sudah aktif dan database server yang ingin dikelola tersedia. Jalankan `quick_start.bat` dari folder proyek. Script akan membuat `.venv` jika belum ada, memasang dependency, lalu menjalankan dashboard di:

```text
http://127.0.0.1:8000/login
```

Konfigurasi quick start Windows menonaktifkan kontrol proses server (`ENABLE_SERVER_MANAGEMENT=false`) secara default. Pengelolaan database tetap tersedia. Untuk menjalankan aplikasinya langsung:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
python -m backend.app.main
```

## Koneksi MongoDB dan login

`MONGO_URI` dapat dipakai untuk memberikan connection string lengkap. Jika kosong, koneksi dibentuk dari `MONGO_HOST`, `MONGO_PORT`, `MONGO_DB`, `MONGO_USERNAME`, `MONGO_PASSWORD`, `MONGO_AUTH_SOURCE`, dan `MONGO_TLS`.

Untuk memakai database PGR Local Server, arahkan tool ke database yang sama. Default AscNet adalah `asc_net`; contoh konfigurasi lokal:

```powershell
$env:MONGO_HOST = "127.0.0.1"
$env:MONGO_PORT = "27017"
$env:MONGO_DB = "asc_net"
```

Atur `ADMIN_USERNAME` dan `ADMIN_PASSWORD` bersama-sama untuk mengaktifkan login dashboard. Jika salah satunya kosong, login dinonaktifkan. Saat login aktif, sesi disimpan di memori dan berakhir setelah 12 jam; restart aplikasi menghapus sesi yang sedang berjalan.

File `.env.example` hanya contoh konfigurasi dan tidak dimuat otomatis. Atur environment variable di terminal/script atau gunakan argumen CLI. Urutan prioritas konfigurasi adalah argumen CLI, environment variable, lalu nilai default.

## Pengelolaan server (opsional)

`ENABLE_SERVER_MANAGEMENT` mengatur apakah halaman dan API pengelolaan server tersedia. Nilai default aplikasi adalah `true`; `quick_start.bat` mengubahnya menjadi `false`.

Untuk mengaktifkannya di Windows, ubah nilai pada `quick_start.bat` menjadi `true`, lalu sesuaikan lokasi executable:

```bat
set "ENABLE_SERVER_MANAGEMENT=true"
set "SERVER_PATH=C:\path\to\PGRLocalSever"
set "SERVER_BINARY_FILE=AscNet.exe"
```

Pastikan nama file executable sesuai hasil build dan server berada di `SERVER_PATH`. Jika `SERVER_PATH/Configs/config.json` ditemukan dan valid, alamat SDK, game server, dan MongoDB dibaca dari konfigurasi tersebut. Jika tidak, aplikasi memakai nilai fallback berikut:

| Pengaturan | Default aplikasi | Kegunaan |
| --- | --- | --- |
| `APP_HOST` / `APP_PORT` | `0.0.0.0` / `8000` | Alamat dashboard |
| `ENABLE_SERVER_MANAGEMENT` | `true` | Mengaktifkan halaman kontrol server |
| `SERVER_PATH` | `/root/wacmk-pgr-server` | Folder server yang dikelola |
| `SERVER_BINARY_FILE` | `Wacmk.Pgr.Server` | Nama executable server |
| `SERVER_RUNTIME_LOG_PATH` | `/tmp/rpg-server.log` | File log untuk dashboard |
| `HEALTHY_CHECK_INTERVAL` | `60` detik | Interval pemeriksaan status |
| `SDK_SERVER_SCHEME/HOST/PORT` | `http` / `127.0.0.1` / `80` | Target pemeriksaan SDK |
| `GAME_SERVER_HOST/PORT` | `127.0.0.1` / `2335` | Target pemeriksaan game TCP |

## Pengembangan

```text
backend/app/       FastAPI, konfigurasi, API, akses MongoDB, dan layanan data
backend/assets/    Tabel TSV untuk label dan data yang ditampilkan tool
backend/tests/     Pengujian backend
frontend/          Halaman dashboard, JavaScript, CSS, dan aset visual
quick_start.bat    Bootstrap dan launcher Windows
```

Jalankan aplikasi melalui `python -m backend.app.main` agar argumen CLI diproses. Pengujian backend:

```bash
python -m pytest backend/tests
```

## Kredit dan penggunaan

Tool ini merupakan versi lokal yang dikonfigurasi untuk proyek PGR Local Server saya. Kode dasarnya berasal dari [wacmkxiaoyi/pgr-gm-tool](https://github.com/wacmkxiaoyi/pgr-gm-tool); perubahan lokal dan fitur yang tersedia dapat berbeda dari repository asal. PGR dan aset game adalah milik pemegang hak masing-masing.
