# TargetKu

Sistem Informasi Pencatatan Tabungan Pribadi Berbasis Target — dibangun dengan Python Flask untuk UAS Berbasis Project mata kuliah Pengantar Pemrograman.

TargetKu membantu pengguna mencatat progres tabungan untuk mencapai suatu tujuan (misalnya membeli HP baru seharga Rp5.000.000), dengan progress bar otomatis dan ucapan selamat saat target tercapai.

🔗 **Live demo**: https://targetku.my.id
📺 **Video demo**: https://youtu.be/CknnRfcSm28?si=O6bzuYgvoBNZrCMC

## Fitur

**Sisi pengguna (publik, setelah daftar/login):**
- Registrasi & login dengan session, data tersimpan permanen di database
- CRUD Target tabungan (nama, nominal, batas waktu opsional)
- CRUD Setoran (catat uang yang ditabung, bisa dari bank atau celengan)
- Progress bar & grafik otomatis berdasarkan data setoran di database
- Ucapan selamat otomatis saat target 100% tercapai
- Validasi input di sisi client (HTML5) dan server (Python)
- Flash message untuk setiap aksi (berhasil/gagal)

**Sisi admin:**
- Login admin terpisah dengan proteksi halaman (session-based)
- Dashboard admin: total pengguna, total target, total target tercapai, total dana tercatat
- Grafik total setoran per bulan (6 bulan terakhir), diambil langsung dari database
- Daftar seluruh pengguna beserta jumlah target dan total tabungan masing-masing
- Kelola (hapus) akun pengguna
- **Ganti password admin** langsung dari aplikasi (menu "Ganti password" di navbar setelah login admin)

## Teknologi

- Python 3 + Flask
- Flask-SQLAlchemy (ORM) + Flask-Login (autentikasi & session)
- Database: **SQLite** untuk pengembangan lokal, **PostgreSQL** (via [Neon](https://neon.tech)) untuk produksi — otomatis menyesuaikan lewat environment variable `DATABASE_URL`
- Bootstrap 5 + Chart.js (antarmuka & grafik) — aset di-hosting lokal di folder `static/`, tidak bergantung CDN
- Deploy sebagai serverless function di **Vercel** (gratis, tanpa kartu kredit, mendukung custom domain)

## Struktur Proyek

```
targetku/
├── app.py                  # routes, model database, logika utama
├── api/
│   └── index.py            # entry point serverless untuk Vercel (import app dari app.py)
├── vercel.json              # konfigurasi build & routing Vercel
├── .vercelignore             # file/folder yang dikecualikan saat deploy ke Vercel
├── requirements.txt          # daftar dependensi Python (termasuk psycopg2-binary untuk Postgres)
├── Procfile                  # konfigurasi alternatif menjalankan aplikasi via gunicorn (non-Vercel)
├── templates/                # seluruh halaman HTML (Jinja2)
├── static/
│   ├── css/                  # Bootstrap, Bootstrap Icons, style.css kustom (lokal, bukan CDN)
│   └── js/                   # Bootstrap Bundle, Chart.js (lokal, bukan CDN)
└── instance/targetku.db      # database SQLite lokal (dibuat otomatis, hanya untuk mode development)
```

## Cara Instalasi & Menjalankan (Lokal)

1. Clone repository ini:
   ```
   git clone <url-repository-anda>
   cd targetku
   ```

2. Buat virtual environment dan aktifkan:
   ```
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. Install dependensi:
   ```
   pip install -r requirements.txt
   ```

4. Jalankan aplikasi:
   ```
   python app.py
   ```
   Database SQLite (`instance/targetku.db`) beserta akun admin default **otomatis dibuat** saat aplikasi pertama kali dijalankan — tidak perlu perintah tambahan.

   Buka `http://127.0.0.1:5000` di browser.

   *(Command `flask --app app.py init-db` masih tersedia sebagai cara manual alternatif jika diperlukan.)*

## Akun Demo

- **Admin**: username `admin`, password `admin123@` — **segera ganti lewat menu "Ganti password" di navbar setelah login**, terutama sebelum aplikasi diakses publik.
- Pengguna biasa dapat mendaftar sendiri lewat halaman **Daftar**.

## Deployment (Vercel + Neon PostgreSQL)

Aplikasi ini di-deploy sebagai serverless function di Vercel karena mendukung custom domain gratis tanpa kartu kredit. Karena filesystem Vercel bersifat read-only, database **wajib** menggunakan PostgreSQL eksternal (bukan SQLite lokal).

1. **Buat database gratis di [Neon](https://neon.tech)**, salin connection string bagian **Pooled connection** (mengandung `-pooler` di host-nya).
2. **Push kode ke GitHub.**
3. **Import project di [Vercel](https://vercel.com)** dari repo GitHub tersebut — Vercel otomatis mendeteksi `vercel.json` dan `api/index.py`.
4. Tambahkan **Environment Variables** di Vercel:
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | connection string Neon (pooled) |
   | `SECRET_KEY` | string acak yang aman |
5. Deploy. Database (tabel + akun admin default) otomatis diinisialisasi saat aplikasi pertama kali diakses.
6. **Hubungkan custom domain** lewat menu **Settings → Domains** di Vercel, lalu arahkan DNS domain (mis. `.my.id`) sesuai instruksi (biasanya cukup A record atau CNAME, tanpa perlu TXT).

> Untuk hosting lain yang mendukung Procfile/gunicorn (bukan serverless), aplikasi ini juga tetap kompatibel — cukup pastikan environment variable `DATABASE_URL` mengarah ke database PostgreSQL/SQLite yang writable.

## Pengujian

Seluruh fitur wajib (registrasi, login, CRUD target, CRUD setoran, progress otomatis, validasi input, login admin, dashboard admin, ganti password admin) telah diuji secara manual (black-box) — lihat tabel pengujian pada laporan project.

## Lisensi

Proyek ini dibuat untuk keperluan tugas akademik (UAS Pengantar Pemrograman).
