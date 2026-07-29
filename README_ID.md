# YouTube Heatmap Clipper

[Bahasa Indonesia](README_ID.md) | [English](README.md)

Aplikasi web untuk mengekstrak momen dengan tingkat interaksi tertinggi dari video YouTube berdasarkan data Most Replayed (heatmap), kemudian secara otomatis mengonversinya menjadi klip vertikal yang siap digunakan untuk Shorts, Reels, atau TikTok, lengkap dengan opsi subtitle berbasis kecerdasan buatan (AI).

Proyek ini merupakan pengembangan lebih lanjut dari proyek: https://github.com/naufaljct48/youtube-heatmap-clipper yang berbasis pada proyek orisinal: https://github.com/0xACAB666/yt-heatmap-clipper. Pengembangan pada proyek ini dilakukan dengan fokus utama pada peningkatan kecepatan pemrosesan dan penyederhanaan antarmuka grafis agar lebih mudah digunakan.

## Preview

|                            |                            |
| -------------------------- | -------------------------- |
| ![Preview 1](images/1.png) | ![Preview 2](images/2.png) |
| ![Preview 3](images/3.png) | ![Preview 4](images/4.png) |
| ![Preview 5](images/5.png) | ![Preview 6](images/6.png) |

## Fitur Baru dan Unggulan

Proyek ini telah diperbarui secara menyeluruh untuk meningkatkan efisiensi pemrosesan, akurasi pelacakan, pengalaman pengguna, dan kurasi konten viral:

### 1. Smart Face Tracking dengan Akurasi 99% & Multi-Strategi
*   **Mode Pemotongan Default**: Smart Crop (Face Tracking) kini diaktifkan secara default untuk pembuatan klip vertikal otomatis yang profesional.
*   **Hybrid Face Detection**: Menggunakan model Deep Learning YuNet DNN Face Detector sebagai sistem pendeteksi utama (yang otomatis diunduh pada saat pertama kali dijalankan) dengan sistem cadangan Haar Cascades (Frontal dan Profile).
*   **Mode Multi-Strategi Pelacakan Wajah**:
    *   `hybrid` (Presenter / Direkomendasikan): Secara cerdas melacak pembicara utama serta mengabaikan penonton di latar belakang menggunakan ambang batas jarak.
    *   `center`: Mengunci wajah yang berada paling dekat dengan pusat layar secara ketat.
    *   `largest`: Mengunci wajah dengan ukuran terbesar di dalam bingkai video.
*   **Penolakan Penonton & Batas Jarak**: Mencegah pergerakan kamera mendadak dengan memfilter wajah penonton atau latar belakang yang jauh.
*   **Scene Change Detection**: Mendeteksi perpindahan adegan kamera secara otomatis untuk mengunci posisi wajah baru secara instan tanpa jeda.
*   **Cinematic Smoothing dan Deadzone**: Menggunakan algoritma LERP smoothing untuk gerakan kamera yang mulus serta konfigurasi Deadzone untuk meminimalisasi getaran kecil pada kamera.

### 2. Metrik Virallitas Cerdas & Algoritma Heatmap Lanjutan
*   **Badge Tingkat Virallitas Cerdas**: Mengevaluasi setiap segmen dengan Skor Virallitas (1-99), Skor Hook (momentum perhatian 5 detik pertama), Skor Retensi, dan Badge Tingkatan visual (`VIRAL`, `HIGH`, `GOOD`, `A+`, `A`, `A-`, `B+`, dll.).
*   **Tangkapan Hook Awal 2,5 Detik**: Otomatis memajukan waktu mulai klip 2,5 detik lebih awal untuk menangkap pembukaan kalimat, konteks pembicaraan, dan hook sebelum puncak interaksi.
*   **Bobot Optimasi Video Pendek Viral**: Menggabungkan 50% Hook, 40% Retensi, dan 10% Skor Mentah yang dirancang khusus untuk algoritma platform video pendek (Shorts/Reels/TikTok).
*   **Smart Intro dan Outro Filter**: Mengabaikan 10% bagian awal (intro) dan 10% bagian akhir (outro) video secara otomatis untuk menghindari pemotongan segmen kosong atau layar akhir.
*   **Sensitivitas Viral dan Filter Overlap**: Pengaturan sensitivitas (Low, Medium, High, Extreme) serta batasan tumpang tindih (Strict, Moderate, Loose, None) untuk hasil kurasi klip terbaik.

### 3. Redesain Antarmuka Modern (Tema Slate & Cyan)
*   **Estetika Glassmorphism Modern**: Redesain total antarmuka dengan tema dark mode Slate & Cyan yang elegan, tata letak kartu responsif, bilah kemajuan utama di bagian atas (top progress bar), serta badge status dinamis.
*   **Scan Heatmap Interaktif & Seleksi Segmen**: Memindai tautan YouTube untuk menampilkan grafik tingkat interaksi, Badge Virallitas, kotak centang segmen individu, serta tombol Select All / Clear sekali klik.
*   **Pemrosesan Massal & Rentang Manual**: Memproses banyak segmen pilihan sekaligus secara paralel atau menentukan rentang waktu mulai/selesai secara manual.
*   **Log Real-time & Pemutar Video Terintegrasi**: Memantau perkembangan secara langsung melalui panel log, serta memutar atau mengunduh klip hasil pemotongan langsung dari browser.

### 4. Konfigurasi Otomatis Sekali Klik (`web_start.bat` / `start.bat`)
*   **Pemasang Otomatis Python**: Mengidentifikasi ketersediaan Python pada Windows dan mengunduh/mempersiapkannya secara otomatis jika belum terpasang.
*   **Lingkungan & Pustaka Otomatis**: Membuat Python Virtual Environment (`venv`) dan memasang/memperbarui pustaka dari `requirements.txt` secara otomatis.
*   **Buka Peramban Otomatis**: Membuka peramban (browser) default secara otomatis ke alamat `http://127.0.0.1:5000/` begitu server siap.

### 5. Pemrosesan Paralel Multi-Worker & Subtitle Faster-Whisper
*   **Pemrosesan Paralel Multi-Worker**: Pemrosesan klip dijalankan secara bersamaan menggunakan ThreadPoolExecutor dengan penyesuaian jumlah thread worker secara otomatis berdasarkan kapasitas CPU.
*   **Fast-Seek Direct Stream**: Mengunduh segmen secara cepat melalui ekstraksi langsung tautan streaming video atau pemotongan berkas lokal.
*   **Subtitle AI Faster-Whisper**: Didukung oleh Faster-Whisper yang memiliki kecepatan transkripsi 4 hingga 5 kali lebih cepat (mendukung model `tiny`, `base`, `small`, `medium`, `large-v3`).
*   **Dukungan Default Inggris (`en`) & Indonesia (`id`)**: Bahasa default subtitle disetel ke Bahasa Inggris (`en`) dengan dukungan penuh untuk Bahasa Indonesia (`id`).
*   **5 Gaya Tampilan Subtitle Dinamis**:
    *   `sentence`: Menampilkan kalimat lengkap secara terstruktur.
    *   `word_by_word`: Menampilkan teks kata demi kata secara dinamis.
    *   `phrase_by_phrase`: Menampilkan frasa pendek (maksimal 3 kata) untuk kemudahan membaca.
    *   `line_by_line`: Menampilkan per baris (membagi otomatis kalimat panjang menjadi maksimal 2 baris yang rapi).
    *   `karaoke`: Memberikan efek karaoke dinamis dengan menandai kata aktif menggunakan warna kuning terang (#FFCC00).
*   **Kustomisasi Font dan Lokasi**: Mendukung berbagai jenis font (Plus Jakarta Sans, Montserrat, Roboto, Arial, atau Font Kustom) serta penempatan posisi subtitle (`bottom` atau `center`).

---

## Persyaratan Sistem

### Perangkat yang Didukung
*   Aplikasi ini **hanya dapat dijalankan pada perangkat desktop atau laptop** (Windows, macOS, Linux) dan **tidak mendukung perangkat mobile** (Android, iOS).

### Spesifikasi Perangkat Keras Minimal
*   **Prosesor (CPU)**: Intel Core i3 / AMD Ryzen 3 atau setara (disarankan minimal 4 core untuk performa multi-worker yang baik).
*   **Memori (RAM)**: minimal 4 GB (disarankan 8 GB ke atas jika menggunakan model subtitle AI ukuran sedang atau besar).
*   **Penyimpanan**: minimal 5 GB ruang kosong (untuk menampung berkas video mentah sementara dan model transkripsi AI).

### Persyaratan Perangkat Lunak
- Python 3.8 ke atas (Python 3.11 sangat direkomendasikan)
- FFmpeg (Diperlukan dan harus terpasang)
- Koneksi Internet
- Pustaka Python (otomatis terpasang melalui skrip pemulai): flask, yt-dlp, opencv-python, faster-whisper (jika fitur subtitle diaktifkan), dan pustaka terkait lainnya.

## Metode Penggunaan Termudah

Jalankan file skrip **web_start.bat** (atau **start.bat**). Skrip ini akan secara otomatis melakukan konfigurasi berikut:
1. Mendeteksi dan mengunduh/mempersiapkan Python di Windows secara otomatis jika belum ada.
2. Membuat dan mengonfigurasi Python Virtual Environment (`venv`).
3. Memeriksa dan memasang semua pustaka yang tercantum pada file `requirements.txt`.
4. Memeriksa ketersediaan program FFmpeg pada sistem.
5. Menjalankan Flask web server dan secara otomatis membuka peramban default ke `http://127.0.0.1:5000/`.

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
    *   **Scan Heatmap**: Klik tombol **Scan Heatmap** untuk mendeteksi momen terpopuler secara otomatis, meninjau Badge Virallitas, memilih segmen yang diinginkan, kemudian klik tombol **Create Selected Clips**.
    *   **Custom**: Masukkan waktu **Start** dan **End** secara manual untuk membuat klip custom.
3.  **Pengaturan Tambahan**:
    *   **Ratio**: Pilih rasio keluaran antara 9:16 (Shorts/Reels/TikTok), 1:1 (Kotak), 16:9 (Horizontal), atau Original.
    *   **Crop Mode**: Pilih **Smart Crop (Face Tracking)** (Default), default (potongan tengah), atau split (video utama di atas, facecam di bawah).
    *   **Strategi Pelacakan**: Pilih **Hybrid / Presenter** (Direkomendasikan), Center Face Only, atau Largest Face Only.
    *   **Subtitle**: Aktifkan opsi subtitle, pilih bahasa (EN/ID), pilih ukuran model Whisper, font, gaya tampilan, dan lokasi tampilan subtitle.
    *   **Smart Crop Settings**: Konfigurasikan parameter pelacakan seperti smoothing factor, deadzone, tracking speed, relock timeout, dan crop padding.
4.  **Proses Ekspor**: Pantau kemajuan pada panel progress secara real-time. Setelah proses selesai, klip video dapat langsung diputar atau diunduh ke perangkat Anda.

---

## Menjalankan Menggunakan Command Line Interface (CLI)

Jika Anda lebih memilih penggunaan terminal, jalankan perintah berikut:
```powershell
python run.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --crop smart --smart-tracking-strategy hybrid --subtitle y --subtitle-lang en --whisper-model small --subtitle-font "Plus Jakarta Sans" --subtitle-location bottom --subtitle-style karaoke --ratio 9:16
```

### Parameter CLI Utama:
*   `--crop`: smart (Default) | default | split_left | split_right
*   `--smart-tracking-strategy`: hybrid (Default) | center | largest
*   `--ratio`: 9:16 | 1:1 | 16:9 | original
*   `--subtitle`: y | n
*   `--subtitle-lang`: en (Default) | id
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
*   **Rasio Aspek yang Didukung**: 9:16 (720x1280), 1:1 (720x720), 16:9 (1280x720), atau menggunakan rasio dan resolusi asli video.
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

- **Proyek Original**: Apresiasi kepada pembuat proyek asli: https://github.com/0xACAB666/yt-heatmap-clipper
- **Pengembangan GUI & Optimasi Awal**: Apresiasi kepada naufaljct48 yang mengembangkan versi GUI dan melakukan optimasi awal: https://github.com/naufaljct48/youtube-heatmap-clipper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Alat pengunduh media YouTube
- [FFmpeg](https://ffmpeg.org/) - Kakas pemrosesan multimedia
- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) - Pustaka transkripsi audio AI cepat
- [OpenAI Whisper](https://github.com/openai/whisper) - Model pengenalan ucapan berbasis AI

---

## Dukungan dan Kontribusi

Apabila aplikasi ini bermanfaat bagi Anda, silakan berikan bintang (star) pada repositori ini. Untuk melaporkan masalah atau mengajukan pertanyaan, silakan buat issue baru pada repositori GitHub.
