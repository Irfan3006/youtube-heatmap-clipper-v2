# YouTube Heatmap Clipper

[Bahasa Indonesia](README.md) | [English](README_EN.md)

Aplikasi web untuk mengekstrak momen dengan tingkat interaksi tertinggi dari video YouTube berdasarkan data Most Replayed (heatmap), kemudian secara otomatis mengonversinya menjadi klip vertikal yang siap digunakan untuk Shorts, Reels, atau TikTok, lengkap dengan opsi subtitle berbasis kecerdasan buatan (AI).

Proyek ini merupakan pengembangan lebih lanjut dari proyek orisinal: https://github.com/0xACAB666/yt-heatmap-clipper, dengan fokus utama pada peningkatan kecepatan pemrosesan dan penyederhanaan antarmuka grafis agar lebih mudah digunakan.

## Preview

|                            |                            |
| -------------------------- | -------------------------- |
| ![Preview 1](images/1.png) | ![Preview 2](images/2.png) |
| ![Preview 3](images/3.png) | ![Preview 4](images/4.png) |
| ![Preview 5](images/5.png) |                            |

## Fitur Baru dan Unggulan

Proyek ini telah diperbarui secara menyeluruh untuk meningkatkan efisiensi pemrosesan, akurasi pelacakan, dan kemudahan bagi pengguna:

### 1. Smart Face Tracking dengan Akurasi 99%
*   **Hybrid Face Detection**: Menggunakan model Deep Learning YuNet DNN Face Detector sebagai sistem pendeteksi utama (yang otomatis diunduh pada saat pertama kali dijalankan) dengan sistem cadangan Haar Cascades (Frontal dan Profile) jika perangkat keras tidak mendukung DNN.
*   **Scene Change Detection**: Mendeteksi perubahan adegan kamera secara otomatis untuk mengunci posisi wajah baru secara instan tanpa adanya jeda.
*   **Cinematic Smoothing dan Deadzone**: Menggunakan algoritma LERP smoothing untuk menghasilkan gerakan kamera yang mulus serta konfigurasi Deadzone untuk meminimalisasi getaran kecil pada kamera.

### 2. Algoritma Heatmap Lanjutan
*   **Viral Spike Detection**: Algoritma ini menganalisis turunan nilai retensi serta rata-rata lokal untuk mendeteksi lonjakan interaksi yang sebenarnya pada video.
*   **Smart Intro dan Outro Filter**: Mengabaikan 10% bagian awal (intro) dan 10% bagian akhir (outro) video secara otomatis untuk menghindari pemotongan pada segmen kosong atau layar akhir.
*   **Sensitivitas Viral dan Filter Overlap**: Menyediakan pengaturan sensitivitas (Low, Medium, High, Extreme) serta pengaturan batasan tumpang tindih (overlap threshold) untuk hasil kurasi klip terbaik.

### 3. Multi-Worker untuk Pemrosesan Paralel Cepat
*   **Akselerasi Paralel**: Pemrosesan klip dijalankan secara bersamaan menggunakan ThreadPoolExecutor dengan penyesuaian jumlah thread worker secara otomatis berdasarkan kapasitas CPU sistem.
*   **Fast-Seek Direct Stream**: Mengunduh klip secara cepat melalui ekstraksi langsung tautan streaming video menggunakan FFmpeg, atau opsi untuk mengunduh seluruh file video terlebih dahulu secara lokal sebelum melakukan pemotongan secara paralel.

### 4. Antarmuka Grafis (Web GUI) yang Berfokus pada Pengguna
*   **Web UI Lebih Praktis**: Mengembangkan antarmuka berbasis Flask yang sudah ada agar lebih responsif, intuitif, dan memudahkan navigasi pengguna tanpa memerlukan langkah manual yang rumit.
*   **Scan Heatmap Interaktif**: Memindai video untuk menampilkan daftar semua segmen terpopuler beserta grafik tingkat interaksinya secara visual.
*   **Pemrosesan Massal dan Custom Range**: Pengguna dapat memilih beberapa segmen sekaligus untuk diproses atau menentukan rentang waktu mulai dan selesai secara manual.
*   **Log Real-time dan Preview**: Memantau perkembangan pemrosesan klip melalui panel log secara langsung serta memutar atau mengunduh klip hasil pemotongan langsung dari browser.

### 5. Pilihan Gaya Subtitle Dinamis (Faster-Whisper)
*   **Transkripsi Cepat**: Didukung oleh Faster-Whisper yang memiliki kecepatan 4 hingga 5 kali lebih cepat dibandingkan dengan Whisper standar.
*   **5 Gaya Tampilan Subtitle**:
    *   `sentence`: Menampilkan kalimat lengkap secara terstruktur.
    *   `word_by_word`: Menampilkan teks kata demi kata secara dinamis.
    *   `phrase_by_phrase`: Menampilkan frasa pendek (maksimal 3 kata) untuk kemudahan membaca.
    *   `line_by_line`: Menampilkan per baris (membagi otomatis kalimat panjang menjadi maksimal 2 baris yang rapi).
    *   `karaoke`: Memberikan efek karaoke dinamis dengan menandai kata aktif menggunakan warna kuning terang (#FFCC00).
*   **Kustomisasi Font dan Lokasi**: Mendukung berbagai jenis font (Plus Jakarta Sans, Roboto, Montserrat, Arial, atau Font Kustom) serta pilihan penempatan subtitle di posisi tengah (Centered) atau bawah (Bottom).

---

## Persyaratan Sistem

- Python 3.8 ke atas (Python 3.11 sangat direkomendasikan)
- FFmpeg (Diperlukan dan harus terpasang)
- Koneksi Internet
- Pustaka Python (otomatis terpasang melalui skrip pemulai): flask, yt-dlp, opencv-python, faster-whisper (jika fitur subtitle diaktifkan), dan pustaka terkait lainnya.

## Metode Penggunaan Termudah

Jalankan file skrip **web_start.bat** (atau **start.bat**). Skrip ini akan secara otomatis melakukan konfigurasi berikut:
1. Memeriksa dan memasang semua pustaka yang tercantum pada file requirements.txt.
2. Membuat Python Virtual Environment (venv) yang terisolasi dan aman.
3. Memeriksa ketersediaan program FFmpeg pada sistem.
4. Menjalankan Flask web server secara otomatis.

## Instalasi dan Pengoperasian Manual

### 1. Memasang Kebutuhan Pustaka
```powershell
python -m pip install -r requirements.txt
python -m pip install faster-whisper
```
*Catatan: Pemasangan faster-whisper dapat dilewati jika Anda tidak memerlukan fitur subtitle AI.*

### 2. Menjalankan Aplikasi Web
```powershell
python webapp.py
```
Buka peramban (browser) Anda dan akses alamat berikut:
- http://127.0.0.1:5000/

---

## Petunjuk Penggunaan Web GUI

1.  **Masukkan URL YouTube**: Informasi metadata video (judul, pengunggah, durasi, dan gambar mini) akan dimuat secara otomatis.
2.  **Pilih Mode Pemotongan**:
    *   **Scan Heatmap**: Klik tombol **Scan Heatmap** untuk mendeteksi momen terpopuler secara otomatis, pilih segmen yang diinginkan, kemudian klik tombol **Create Selected Clips**.
    *   **Custom**: Masukkan waktu **Start** dan **End** secara manual, kemudian klik tombol untuk membuat klip.
3.  **Pengaturan Tambahan**:
    *   **Ratio**: Pilih rasio keluaran antara 9:16 (Vertikal), 1:1 (Kotak), 16:9 (Horizontal), atau Original.
    *   **Crop Mode**: Pilih antara default (potongan tengah), split (membagi layar untuk menampilkan video utama di atas dan kamera wajah di bawah), atau smart (pemotongan cerdas berbasis pelacakan wajah dengan akurasi 99%).
    *   **Subtitle**: Aktifkan opsi subtitle, pilih bahasa (ID/EN), pilih ukuran model Whisper, font, gaya tampilan, dan lokasi tampilan subtitle.
    *   **Smart Crop Settings**: Konfigurasikan parameter pelacakan seperti smoothing factor, deadzone, tracking speed, dan relock timeout untuk mengoptimalkan pergerakan kamera face tracking.
4.  **Proses Ekspor**: Log proses pembuatan klip akan ditampilkan di bagian bawah halaman. Setelah proses selesai, klip video dapat langsung diputar atau diunduh ke perangkat Anda.

---

## Menjalankan Menggunakan Command Line Interface (CLI)

Jika Anda lebih memilih penggunaan terminal, jalankan perintah berikut:
```powershell
python run.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --crop smart --subtitle y --whisper-model small --subtitle-font "Plus Jakarta Sans" --subtitle-location bottom --subtitle-style karaoke --ratio 9:16
```

### Parameter CLI Utama:
*   `--crop`: default | split_left | split_right | smart (Face Tracking)
*   `--ratio`: 9:16 | 1:1 | 16:9 | original
*   `--subtitle`: y | n
*   `--subtitle-lang`: id | en (Default: en)
*   `--whisper-model`: tiny | base | small | medium | large-v3
*   `--subtitle-font`: Nama font (misalnya Poppins)
*   `--subtitle-style`: sentence | word_by_word | phrase_by_phrase | line_by_line | karaoke
*   `--subtitle-location`: bottom | center
*   `--workers`: Jumlah proses worker paralel (0 untuk otomatis)

---

## Perbandingan Model Whisper

| Model        | Ukuran | Kebutuhan RAM | Kecepatan Transkripsi (60s) | Tingkat Akurasi | Rekomendasi Penggunaan  |
| ------------ | ------ | ------------- | --------------------------- | --------------- | ----------------------- |
| **tiny**     | 75 MB  | ~500 MB       | ~5-7 detik                  | Cukup           | Proses cepat, PC spesifikasi rendah |
| **base**     | 142 MB | ~700 MB       | ~8-10 detik                 | Baik            | Penggunaan umum         |
| **small**    | 466 MB | ~1.5 GB       | ~15-20 detik                | Sangat Baik     | Konten berkualitas      |
| **medium**   | 1.5 GB | ~3 GB         | ~40-50 detik                | Luar Biasa      | Penggunaan profesional  |
| **large-v3** | 2.9 GB | ~6 GB         | ~90-120 detik               | Terbaik         | Kualitas produksi akhir |

> **Rekomendasi**: Gunakan model `tiny` untuk performa kecepatan terbaik, atau model `small` untuk keseimbangan akurasi transkripsi dan kecepatan yang ideal.

---

## Spesifikasi Output Video

*   **Format**: MP4 (H.264 video + AAC audio)
*   **Resolusi Default**: 720x1280 (9:16 Vertikal)
*   **Video Codec**: Penggunaan encoder terakselerasi perangkat keras (seperti h264_amf untuk AMD, h264_nvenc untuk NVIDIA, h264_qsv untuk Intel) jika tersedia, dengan cadangan otomatis ke libx264 (preset ultrafast, CRF 26).
*   **Audio Codec**: AAC, 128 kbps
*   **Subtitles**: Tertanam langsung pada berkas video (burned-in) sesuai dengan font, gaya, dan tata letak yang dikonfigurasi.

---

## Panduan Pemasangan FFmpeg

Aplikasi ini memerlukan FFmpeg untuk pemrosesan video. Di sistem Windows, aplikasi akan mencoba mendeteksi ketersediaan FFmpeg secara otomatis jika dipasang melalui WinGet.

### Windows (Metode Tercepat):
Jalankan perintah berikut pada PowerShell dengan hak akses Administrator:
```powershell
winget install Gyan.FFmpeg
```
Setelah proses pemasangan selesai, silakan mulai ulang (restart) terminal atau VS Code Anda agar perubahan PATH dapat terdeteksi.

### macOS:
```bash
brew install ffmpeg
```

### Linux:
```bash
sudo apt update && sudo apt install ffmpeg
```

---

## Lisensi

Proyek ini dilisensikan di bawah MIT License.

## Kredit dan Apresiasi

- **Proyek Original (CLI Version)**: Apresiasi kepada pembuat proyek asli yang menjadi fondasi utama pengembangan aplikasi ini: https://github.com/0xACAB666/yt-heatmap-clipper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Alat pengunduh media YouTube
- [FFmpeg](https://ffmpeg.org/) - Kakas pemrosesan multimedia
- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) - Pustaka transkripsi audio AI cepat
- [OpenAI Whisper](https://github.com/openai/whisper) - Model pengenalan ucapan berbasis AI

---

## Dukungan dan Kontribusi

Apabila aplikasi ini bermanfaat bagi Anda, silakan berikan bintang (star) pada repositori ini. Untuk melaporkan masalah atau mengajukan pertanyaan, silakan buat issue baru pada repositori GitHub.
