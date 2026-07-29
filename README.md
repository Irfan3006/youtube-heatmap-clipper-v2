# YouTube Heatmap Clipper

[Bahasa Indonesia](README_ID.md) | [English](README.md)

A web application to extract the most engaging segments from YouTube videos using Most Replayed (heatmap) data, and automatically convert them into vertical-ready clips for Shorts, Reels, and TikTok, featuring AI-powered subtitles.

This project is a further development of the project: https://github.com/naufaljct48/youtube-heatmap-clipper which is based on the original project: https://github.com/0xACAB666/yt-heatmap-clipper. The development of this project focuses primarily on improving processing speed and refining the graphical user interface for ease of use.

## Preview

|                            |                            |
| -------------------------- | -------------------------- |
| ![Preview 1](images/1.png) | ![Preview 2](images/2.png) |
| ![Preview 3](images/3.png) | ![Preview 4](images/4.png) |
| ![Preview 5](images/5.png) | ![Preview 6](images/6.png) |

## New and Highlighted Features

This project has been updated with a focus on user experience, processing efficiency, AI accuracy, and viral content curation:

### 1. Smart Face Tracking with 99% Accuracy & Multi-Strategy
*   **Default Cropping Mode**: Smart Crop (Face Tracking) is enabled by default for automated, professional-grade vertical clip creation.
*   **Hybrid Face Detection**: Uses the advanced YuNet DNN Face Detector Deep Learning model as the primary detector (automatically downloaded on first launch) with Haar Cascades (Frontal and Profile) fallback.
*   **Multi-Strategy Face Tracking**:
    *   `hybrid` (Presenter / Recommended): Intelligently tracks the main speaker while ignoring background audiences using distance thresholding.
    *   `center`: Locks strictly onto the face closest to the center of the frame.
    *   `largest`: Locks onto the largest detected face in frame.
*   **Audience Rejection & Distance Threshold**: Prevents unexpected camera jumps by filtering out distant background audience faces.
*   **Scene Change Detection**: Intelligently detects camera cuts or transitions to instantly lock (auto-snap) onto the new face position without delay.
*   **Cinematic Smoothing and Deadzone**: Features a LERP smoothing algorithm for fluid camera panning and adjustable Deadzone configurations to filter out minor, jittery camera movements.

### 2. Smart Virality Metrics & Advanced Heatmap Algorithm
*   **Smart Virality Grade Badges**: Evaluates each segment with a Virality Score (1-99), Hook Score (first 5s attention momentum), Retention Score, and visual Virality Grade Badges (`VIRAL`, `HIGH`, `GOOD`, `A+`, `A`, `A-`, `B+`, etc.).
*   **2.5s Lead-In Hook Capture**: Automatically shifts clip start timestamps 2.5 seconds earlier to capture speech buildup, context, and hook preceding peak engagement moments.
*   **Viral Shorts Optimization Weighting**: Combines 50% Hook, 40% Retention, and 10% Raw Score specifically designed for viral short-form video algorithms.
*   **Smart Intro and Outro Filter**: Automatically filters out the first 10% (intro) and last 10% (outro) of the video to avoid clipping empty scenes or end screens.
*   **Viral Sensitivity and Overlap Filter**: Adjusts sensitivity levels (Low, Medium, High, Extreme) and overlap threshold rules (Strict, Moderate, Loose, None) for optimal clip curation.

### 3. Modern Slate & Cyan UI/UX Redesign
*   **Modern Glassmorphism Aesthetics**: Complete UI redesign featuring a sleek Slate & Cyan dark mode theme, responsive card layouts, top progress bar indicator, and dynamic job badges.
*   **Interactive Heatmap Scan & Selection**: Scans video URLs instantly to display engagement graphs, Virality Grade Badges, individual segment checkboxes, and one-click Select All / Clear options.
*   **Bulk Processing and Custom Ranges**: Select multiple segments to process concurrently or define custom manual start and end timestamps.
*   **Real-time Logs and Built-in Player**: Monitor progress in real-time through the console log panel, and play or download completed clips directly from the browser.

### 4. Automated One-Click Setup (`web_start.bat` / `start.bat`)
*   **Auto Python Installer**: Automatically checks for Python on Windows and downloads/installs it if not present.
*   **Auto Environment & Dependency Setup**: Automatically creates a isolated Python Virtual Environment (`venv`) and installs/updates requirements from `requirements.txt`.
*   **Auto Browser Launch**: Automatically opens your default web browser to `http://127.0.0.1:5000/` upon server startup.

### 5. Multi-Worker Parallel Processing & Faster-Whisper Subtitles
*   **Multi-Worker Parallel Processing**: Processes clips concurrently using a ThreadPoolExecutor with worker counts automatically scaled based on CPU threads.
*   **Fast-Seek Direct Stream Extraction**: Downloads segments rapidly via direct stream URL extraction with FFmpeg or local full-video slicing.
*   **Faster-Whisper AI Subtitles**: Powered by Faster-Whisper, delivering 4-5x faster transcription speed (supports `tiny`, `base`, `small`, `medium`, `large-v3`).
*   **Default English (`en`) & Indonesian (`id`) Support**: Subtitle language defaults to English (`en`) with full support for Indonesian (`id`).
*   **5 Dynamic Subtitle Display Styles**:
    *   `sentence`: Displays the complete sentence normally.
    *   `word_by_word`: Displays text dynamically word-by-word.
    *   `phrase_by_phrase`: Displays short, easy-to-read phrases of up to 3 words.
    *   `line_by_line`: Displays line-by-line, automatically formatting longer text into up to 2 lines.
    *   `karaoke`: A dynamic karaoke effect that highlights the active word in yellow (#FFCC00).
*   **Custom Fonts and Placement**: Supports preferred fonts (Plus Jakarta Sans, Montserrat, Roboto, Arial, or Custom) and screen locations (`bottom` or `center`).

---

## Requirements

### Supported Devices
*   This application **can only be run on desktop or laptop devices** (Windows, macOS, Linux) and **does not support mobile devices** (Android, iOS).

### Minimum Hardware Specifications
*   **Processor (CPU)**: Intel Core i3 / AMD Ryzen 3 or equivalent (minimum 4 cores recommended for good multi-worker performance).
*   **Memory (RAM)**: 4 GB minimum (8 GB or more recommended if using medium or large AI subtitle models).
*   **Storage**: 5 GB of free space minimum (to store temporary raw video files and AI transcription models).

### Software Requirements
- Python 3.8+ (Python 3.11 highly recommended)
- FFmpeg (Required and must be installed)
- Internet Connection
- Python Libraries (automatically installed by the launcher): flask, yt-dlp, opencv-python, faster-whisper (if subtitles are enabled), and related libraries.

## How to Use (Easiest Way)

Double-click the **web_start.bat** (or **start.bat**) file. The script will automatically:
1. Auto-detect and download/install Python on Windows if missing.
2. Create and configure a Python Virtual Environment (`venv`).
3. Verify and install requirements in `requirements.txt`.
4. Check for FFmpeg in the system path.
5. Launch the Flask web server and automatically open your default browser to `http://127.0.0.1:5000/`.

## Installation and Running Manually

### 1. Install Requirements
```powershell
python -m pip install -r requirements.txt
python -m pip install faster-whisper
```
*Note: Skip faster-whisper if you do not require AI subtitle generation.*

### 2. Run the Web App
```powershell
python webapp.py
```
Open your browser and navigate to:
- http://127.0.0.1:5000/

---

## Using the Web GUI

1.  **Paste YouTube URL**: The video metadata (title, channel, thumbnail) will load automatically.
2.  **Select Clipping Mode**:
    *   **Scan Heatmap**: Click **Scan Heatmap** to auto-detect viral segments, review Virality Grade Badges, check desired clips, and click **Create Selected Clips**.
    *   **Custom**: Enter manual **Start** and **End** times to create manual ranges.
3.  **Configure Options**:
    *   **Ratio**: Select 9:16 (Shorts/Reels/TikTok), 1:1 (Square), 16:9 (Horizontal), or Original ratio.
    *   **Crop Mode**: Select **Smart Crop (Face Tracking)** (Default), default (center crop), or split (displays main video on top, facecam on bottom).
    *   **Tracking Strategy**: Choose **Hybrid / Presenter** (Recommended), Center Face Only, or Largest Face Only.
    *   **Subtitle**: Enable subtitles, choose language (EN/ID), Whisper model size, font, display style, and screen location.
    *   **Smart Crop Settings**: Fine-tune the smoothing factor, deadzone, tracking speed, relock timeout, and padding parameters.
4.  **Export**: Track progress in real-time in the progress panel. Once complete, play or download your clips directly from the browser.

---

## Running via CLI (Optional)

If you prefer terminal commands, run:
```powershell
python run.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --crop smart --smart-tracking-strategy hybrid --subtitle y --subtitle-lang en --whisper-model small --subtitle-font "Plus Jakarta Sans" --subtitle-location bottom --subtitle-style karaoke --ratio 9:16
```

### Key CLI Arguments:
*   `--crop`: smart (Default) | default | split_left | split_right
*   `--smart-tracking-strategy`: hybrid (Default) | center | largest
*   `--ratio`: 9:16 | 1:1 | 16:9 | original
*   `--subtitle`: y | n
*   `--subtitle-lang`: en (Default) | id
*   `--whisper-model`: tiny | base | small | medium | large-v3
*   `--subtitle-font`: Font name (e.g. Poppins)
*   `--subtitle-style`: sentence | word_by_word | phrase_by_phrase | line_by_line | karaoke
*   `--subtitle-location`: bottom | center
*   `--workers`: Number of parallel workers (0 for auto)

---

## Whisper Model Comparison

| Model        | Size   | RAM     | Speed (60s) | Accuracy  | Best For                |
| ------------ | ------ | ------- | ----------- | --------- | ----------------------- |
| **tiny**     | 75 MB  | ~500 MB | ~5-7s       | Good      | Quick clips, low-end PC |
| **base**     | 142 MB | ~700 MB | ~8-10s      | Better    | General purpose         |
| **small**    | 466 MB | ~1.5 GB | ~15-20s     | Great     | Quality content         |
| **medium**   | 1.5 GB | ~3 GB   | ~40-50s     | Excellent | Professional work       |
| **large-v3** | 2.9 GB | ~6 GB   | ~90-120s    | Best      | Production quality      |

> **Recommendation**: Use `tiny` for the fastest possible rendering speed, or `small` for a balance between transcription accuracy and processing overhead.

---

## Output Video Specifications

*   **Format**: MP4 (H.264 video + AAC audio)
*   **Supported Aspect Ratios**: 9:16 (720x1280), 1:1 (720x720), 16:9 (1280x720), or the original video's resolution and ratio.
*   **Video Codec**: Hardware Accelerated Encoder (e.g. h264_amf for AMD, h264_nvenc for NVIDIA, h264_qsv for Intel) if supported, with automatic fallback to libx264 (ultrafast preset, CRF 26).
*   **Audio Codec**: AAC, 128 kbps
*   **Subtitles**: Burned-in directly into the video file matching your font, style, and position preferences.

---

## FFmpeg Installation Guide

The application requires FFmpeg to function. On Windows, it attempts to auto-detect FFmpeg if installed via WinGet.

### Windows (Quickest Way):
Open PowerShell as Administrator and run:
```powershell
winget install Gyan.FFmpeg
```
After installation completes, restart your terminal or VS Code to apply PATH changes.

### macOS:
```bash
brew install ffmpeg
```

### Linux:
```bash
sudo apt update && sudo apt install ffmpeg
```

---

## License

This project is licensed under the MIT License.

## Credits and Special Thanks

- **Original Project**: Special thanks to the creator of the original project: https://github.com/0xACAB666/yt-heatmap-clipper
- **GUI Version & Initial Optimizations**: Special thanks to naufaljct48 who created the GUI version and initial optimizations: https://github.com/naufaljct48/youtube-heatmap-clipper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube video downloader
- [FFmpeg](https://ffmpeg.org/) - Video processing suite
- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) - Fast AI speech-to-text library
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model

---

## Support and Contribution

If you find this application helpful, please star the repository. Feel free to open a GitHub Issue for bugs, questions, or feature requests.
