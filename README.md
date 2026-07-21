# TargetKu

Sistem Informasi Pencatatan Tabungan Pribadi Berbasis Target — dibangun dengan Python Flask untuk UAS Berbasis Project mata kuliah Pengantar Pemrograman.

TargetKu membantu pengguna mencatat progres tabungan untuk mencapai suatu tujuan (misalnya membeli HP baru seharga Rp5.000.000), dengan progress bar otomatis dan ucapan selamat saat target tercapai.

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

## Teknologi

- Python 3 + Flask
- Flask-SQLAlchemy (ORM) + Flask-Login (autentikasi & session)
- SQLite (database, data persisten di `instance/targetku.db`)
- Bootstrap 5 + Chart.js (antarmuka & grafik)

## Struktur Proyek

```
targetku/
├── app.py                 # routes, model database, logika utama
├── requirements.txt       # daftar dependensi Python
├── Procfile                # konfigurasi menjalankan aplikasi di server (gunicorn)
├── templates/              # seluruh halaman HTML (Jinja2)
├── static/css/style.css    # styling kustom
└── instance/targetku.db    # database SQLite (dibuat otomatis)
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

4. Inisialisasi database (membuat tabel & akun admin default):
   ```
   flask --app app.py init-db
   ```
   Akun admin default: `admin` / `admin123` — **wajib diganti passwordnya sebelum deploy ke publik.**

5. Jalankan aplikasi:
   ```
   python app.py
   ```
   Buka `http://127.0.0.1:5000` di browser.

## Akun Demo

- **Admin**: username `admin`, password `admin123`
- Pengguna biasa dapat mendaftar sendiri lewat halaman **Daftar**.

## Deployment

Aplikasi ini menggunakan `gunicorn` sebagai WSGI server (lihat `Procfile`) sehingga siap di-deploy ke berbagai layanan hosting yang mendukung Python/Flask. Sebelum deploy:

1. Ganti `SECRET_KEY` di `app.py` dengan nilai acak yang aman (gunakan environment variable).
2. Jalankan `flask --app app.py init-db` di server untuk membuat database awal, lalu segera ganti password admin default.
3. Pastikan folder `instance/` memiliki permission tulis agar data SQLite tersimpan permanen antar sesi.

## Pengujian

Seluruh fitur wajib (registrasi, login, CRUD target, CRUD setoran, progress otomatis, validasi input, login admin, dashboard admin) telah diuji secara manual (black-box) — lihat tabel pengujian pada laporan project.

## Lisensi

Proyek ini dibuat untuk keperluan tugas akademik (UAS Pengantar Pemrograman).
