# Smart Parking Monitoring System (yoloV8n)

Sistem Pemantauan Parkir Pintar berbasis **Computer Vision**, **Artificial Intelligence (YOLOv8)**, **SQLite**, dan **Streamlit**. Sistem ini dirancang untuk memantau ketersediaan petak parkir secara *real-time* melalui kamera pemantau (CCTV), mendeteksi kendaraan (mobil, motor, bus, truk) menggunakan model deteksi objek YOLOv8, dan menyajikan informasinya pada papan LED digital interaktif.

---

## Fitur Utama acong

- **Pemetaan Interaktif (`mapping.py`)**: Alat berbasis OpenCV untuk menggambar poligon petak parkir secara interaktif dengan klik mouse (4 titik per petak). Koordinat disimpan secara otomatis ke format JSON.
- **Deteksi AI Presisi Tinggi (`main.py`, `kamera2.py`, `kamera3.py`)**: Menggunakan model YOLOv8 Nano (`yolov8n.pt`) untuk mendeteksi kendaraan secara efisien tanpa memerlukan GPU berspesifikasi tinggi.
- **Logika Temporal (Filter Frame)**: Sistem dilengkapi dengan *delay frame* (temporal tracker) untuk memastikan objek benar-benar terparkir dan menghindari deteksi palsu dari kendaraan yang hanya melintas.
- **Penyimpanan Data Terpusat (`parkir.db`)**: Menggunakan SQLite untuk mencatat data jumlah kapasitas terisi dan kosong secara terdistribusi dari berbagai kamera pemantau.
- **Dashboard Papan Informasi LED (`app.py`)**: Web dashboard interaktif berbasis Streamlit dengan visualisasi ala papan petunjuk LED digital real-time untuk memudahkan pengguna jalan melihat ketersediaan parkir.

---

## Struktur Repositori

```text
├── parkir_env/               # Virtual Environment Python (opsional/lokal)
├── data/                     # Data tambahan (jika ada)
├── koordinat_parkir.json     # Konfigurasi koordinat petak Kamera 01
├── koordinat_parkir_2.json   # Konfigurasi koordinat petak Kamera 02
├── koordinat_parkir_3.json   # Konfigurasi koordinat petak Kamera 03
├── setup_db.py               # Script untuk membuat & menginisialisasi database SQLite
├── mapping.py                # Script interaktif untuk pemetaan koordinat petak parkir
├── main.py                   # Script pemantauan & deteksi Kamera 01
├── kamera2.py                # Script pemantauan & deteksi Kamera 02
├── kamera3.py                # Script pemantauan & deteksi Kamera 03
├── app.py                    # Aplikasi dashboard Streamlit (Papan Informasi LED)
├── tes.py                    # Script uji coba OpenCV dan YOLOv8
├── yolov8n.pt                # Bobot model terlatih YOLOv8 Nano
├── bus.jpg                   # Gambar sampel untuk pengujian
├── video_parkir.mp4          # Video simulasi parkir 1
├── video_parkir_2.mp4        # Video simulasi parkir 2
├── video_parkir_3.mp4        # Video simulasi parkir 3
└── video_parkir_4.mp4        # Video simulasi parkir 4
```

---

## Persyaratan Sistem

Pastikan Anda telah menginstal Python (versi 3.8 ke atas direkomendasikan). Library utama yang digunakan meliputi:
- `opencv-python`
- `ultralytics` (YOLOv8)
- `streamlit`
- `pandas`
- `sqlite3`

---

## Panduan Penggunaan

Ikuti langkah-langkah di bawah ini untuk menjalankan simulasi sistem secara penuh:

### 1. Inisialisasi Database
Jalankan script ini sekali untuk membuat file database SQLite (`parkir.db`) beserta tabel status kamera yang diperlukan:
```bash
python setup_db.py
```

### 2. Pemetaan Petak Parkir (Mapping)
Petakan area parkir yang ada pada video pemantau.
```bash
python mapping.py
```
* **Instruksi Pemetaan**:
  1. Jendela video akan terbuka. Klik sebanyak **4 kali** pada layar untuk membentuk **satu** petak parkir.
  2. Ulangi proses di atas untuk petak parkir lainnya yang ada pada jalur jalan tersebut.
  3. Jika semua petak sudah selesai dipetakan, tekan tombol **`q`** pada keyboard untuk menyimpan koordinat ke file JSON (`koordinat_parkir_3.json`) dan menutup aplikasi.

### 3. Jalankan Kamera Pemantau (Deteksi Real-Time)
Setelah koordinat parkir tersimpan, aktifkan program pemantauan berbasis AI. Program ini akan mendeteksi kendaraan, mencocokkannya dengan koordinat petak, dan memperbarui status di database secara berkelanjutan:
```bash
python main.py
```
*(Anda juga dapat menjalankan `kamera2.py` atau `kamera3.py` di terminal terpisah untuk mensimulasikan sistem multi-kamera).*

### 4. Jalankan Dashboard Papan Informasi LED
Untuk melihat status total sisa parkir secara real-time melalui tampilan antarmuka LED digital yang elegan, jalankan perintah Streamlit berikut:
```bash
streamlit run app.py
```
Aplikasi secara otomatis akan terbuka di browser Anda pada alamat `http://localhost:8501`.

---

## Cara Kerja Deteksi AI
1. **Pendeteksian Objek**: YOLOv8 mengidentifikasi lokasi kotak pembatas (*bounding box*) untuk kelas kendaraan seperti Mobil, Motor, Bus, dan Truk.
2. **Titik Kontak Jalan**: Sistem mengekstrak titik tengah bagian bawah kotak pembatas (titik ban menyentuh aspal) sebagai representasi posisi presisi kendaraan.
3. **Pemeriksaan Poligon (`pointPolygonTest`)**: Program melakukan uji geometris apakah titik ban kendaraan berada di dalam batas-batas poligon koordinat petak parkir.
4. **Validasi Timer Temporal**: Jika titik terdeteksi di dalam petak secara konsisten selama minimal 3 frame berturut-turut, status petak akan berubah dari **KOSONG** (Hijau) menjadi **TERISI** (Merah), lalu dikirim ke database SQLite.

---

## Kontribusi & Git Remote
Repositori ini terhubung dengan remote origin:
* **URL**: [https://github.com/Nighto-ops/yoloV8n.git](https://github.com/Nighto-ops/yoloV8n.git)
