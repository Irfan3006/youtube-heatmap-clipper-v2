import os
import re
import json
import sys
import subprocess
import requests
import shutil
from urllib.parse import urlparse, parse_qs
import argparse
import warnings
warnings.filterwarnings("ignore")

try:
    import cv2
except ImportError:
    cv2 = None

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


OUTPUT_DIR = "clips"      # Directory where generated clips will be saved
MAX_DURATION = 60         # Maximum duration (in seconds) for each clip
MIN_SCORE = 0.20          # Minimum heatmap intensity score to be considered viral
MAX_CLIPS = 10            # Maximum number of clips to generate per video
MAX_WORKERS = 1           # Number of parallel workers (reserved for future concurrency)
PADDING = 10              # Extra seconds added before and after each detected segment
TOP_HEIGHT = 960          # Height for top section (center content) in split mode
BOTTOM_HEIGHT = 320       # Height for bottom section (facecam) in split mode
USE_SUBTITLE = True       # Enable auto subtitle using Faster-Whisper (4-5x faster)
WHISPER_MODEL = "small"    # Whisper model size: tiny, base, small, medium, large
SUBTITLE_FONT = "Arial"
SUBTITLE_FONTS_DIR = None
SUBTITLE_LOCATION = "bottom"
OUTPUT_RATIO = "9:16"
OUT_WIDTH = 720
OUT_HEIGHT = 1280

CPU_THREADS = 4



def set_ratio_preset(preset):
    global OUTPUT_RATIO, OUT_WIDTH, OUT_HEIGHT
    OUTPUT_RATIO = preset
    if preset == "9:16":
        OUT_WIDTH, OUT_HEIGHT = 720, 1280
        return
    if preset == "1:1":
        OUT_WIDTH, OUT_HEIGHT = 720, 720
        return
    if preset == "16:9":
        OUT_WIDTH, OUT_HEIGHT = 1280, 720
        return
    if preset == "original":
        OUT_WIDTH, OUT_HEIGHT = None, None
        return
    raise ValueError("Invalid ratio preset")

def get_ratio_dimensions(preset):
    if preset == "9:16":
        return 720, 1280
    if preset == "1:1":
        return 720, 720
    if preset == "16:9":
        return 1280, 720
    if preset == "original":
        return None, None
    raise ValueError("Invalid ratio preset")

def detect_viral_spikes(heatmap_raw):
    """
    Identify segments in the raw heatmap that show sharp intensity increases (spikes)
    above the local average. Enhance their scores by weighting both raw intensity
    and spike magnitude.
    """
    if not heatmap_raw:
        return []
        
    n = len(heatmap_raw)
    values = []
    for marker in heatmap_raw:
        try:
            values.append(float(marker.get("value", 0)))
        except Exception:
            values.append(0.0)
            
    # Calculate local averages using a moving window (window size 5)
    local_averages = []
    window_size = 5
    half_w = window_size // 2
    for i in range(n):
        start_idx = max(0, i - half_w)
        end_idx = min(n, i + half_w + 1)
        sub_vals = values[start_idx:end_idx]
        local_averages.append(sum(sub_vals) / len(sub_vals) if sub_vals else 0.0)
        
    enhanced_segments = []
    for i in range(n):
        try:
            marker = heatmap_raw[i]
            start = float(marker.get("start_time", 0))
            end = float(marker.get("end_time", 0))
            val = values[i]
            
            # Derivative (difference from previous point)
            if i > 0:
                diff = val - values[i-1]
            else:
                diff = 0.0
                
            # Spike magnitude: positive rise + how much it stands above local average
            above_local = max(0.0, val - local_averages[i])
            spike_magnitude = max(0.0, diff) + above_local
            
            # Final score weighting
            final_score = 0.6 * val + 0.4 * spike_magnitude
            
            if final_score >= MIN_SCORE:
                enhanced_segments.append({
                    "start": start,
                    "duration": min(end - start, MAX_DURATION),
                    "score": final_score
                })
        except Exception:
            continue
            
    return enhanced_segments

def merge_adjacent_segments(segments, gap_limit=5.0):
    """
    Group consecutive/overlapping segments (within gap_limit seconds)
    into a single segment. Capped at MAX_DURATION.
    """
    if not segments:
        return []
    
    # Ensure sorted chronologically by start time
    sorted_segs = sorted(segments, key=lambda x: x["start"])
    
    merged = []
    current = sorted_segs[0].copy()
    
    for next_seg in sorted_segs[1:]:
        current_end = current["start"] + current["duration"]
        if next_seg["start"] <= current_end + gap_limit:
            next_end = next_seg["start"] + next_seg["duration"]
            new_end = max(current_end, next_end)
            if new_end - current["start"] <= MAX_DURATION:
                current["duration"] = new_end - current["start"]
                current["score"] = max(current["score"], next_seg["score"])
            else:
                merged.append(current)
                current = next_seg.copy()
        else:
            merged.append(current)
            current = next_seg.copy()
            
    merged.append(current)
    return merged

def select_non_overlapping(segments, max_count, padding):
    """
    Select up to max_count segments from a list of segments (sorted by score descending),
    ensuring that no selected segment has a padded time range that overlaps significantly (>50%)
    with any already-selected segments.
    """
    selected = []
    for seg in segments:
        if len(selected) >= max_count:
            break
        
        s_c = max(0, seg["start"] - padding)
        e_c = seg["start"] + seg["duration"] + padding
        d_c = e_c - s_c
        
        if d_c <= 0:
            continue
            
        is_overlapping = False
        for sel in selected:
            s_p = max(0, sel["start"] - padding)
            e_p = sel["start"] + sel["duration"] + padding
            
            overlap = max(0, min(e_c, e_p) - max(s_c, s_p))
            if overlap > 0.5 * d_c:
                is_overlapping = True
                break
                
        if not is_overlapping:
            selected.append(seg)
            
    return selected

def ffmpeg_tersedia():
    return bool(shutil.which("ffmpeg"))


def coba_masukkan_ffmpeg_ke_path():
    if ffmpeg_tersedia():
        return True

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return False

    winget_packages = os.path.join(local_app_data, "Microsoft", "WinGet", "Packages")
    gyan_root = os.path.join(winget_packages, "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe")
    if not os.path.isdir(gyan_root):
        return False

    found_bin_dir = None
    for root, dirs, files in os.walk(gyan_root):
        if "ffmpeg.exe" in files and os.path.basename(root).lower() == "bin":
            found_bin_dir = root
            break

    if not found_bin_dir:
        return False

    os.environ["PATH"] = f"{found_bin_dir};{os.environ.get('PATH', '')}"
    return ffmpeg_tersedia()


def parse_args():
    parser = argparse.ArgumentParser(prog="yt-heatmap-clipper")
    parser.add_argument("--url", help="YouTube URL (watch/shorts/youtu.be)")
    parser.add_argument(
        "--crop",
        choices=["default", "split_left", "split_right", "smart"],
        help="Crop mode",
    )
    parser.add_argument(
        "--subtitle",
        choices=["y", "n"],
        help="Enable auto subtitle (y/n)",
    )
    parser.add_argument(
        "--subtitle-lang",
        dest="subtitle_lang",
        choices=["id", "en"],
        default="en",
        help="Subtitle language (id or en, default: en)",
    )
    parser.add_argument("--whisper-model", dest="whisper_model", help="Faster-Whisper model")
    parser.add_argument("--subtitle-font", dest="subtitle_font", help="Subtitle font name (e.g., Poppins)")
    parser.add_argument("--subtitle-fontsdir", dest="subtitle_fontsdir", help="Folder containing .ttf/.otf fonts")
    parser.add_argument(
        "--subtitle-location",
        dest="subtitle_location",
        choices=["center", "bottom"],
        help="Subtitle placement: center or bottom",
    )
    parser.add_argument("--ratio", choices=["9:16", "1:1", "16:9", "original"], help="Output ratio preset")
    parser.add_argument("--check", action="store_true", help="Check dependencies then exit")
    parser.add_argument("--update-ytdlp", action="store_true", help="Auto-update yt-dlp on startup")
    parser.add_argument("--max-clips", type=int, default=10, help="Maximum number of clips to generate")
    parser.add_argument("--workers", type=int, default=0, help="Number of parallel workers for processing (0 for auto)")
    return parser.parse_args()



def escape_subtitles_filter_path(path):
    abs_path = os.path.abspath(path)
    return abs_path.replace("\\", "/").replace(":", "\\:")


def escape_subtitles_filter_dir(path):
    abs_path = os.path.abspath(path)
    return abs_path.replace("\\", "/").replace(":", "\\:")

def build_subtitle_force_style():
    alignment = "2" if SUBTITLE_LOCATION == "bottom" else "5"
    margin_v = "40" if SUBTITLE_LOCATION == "bottom" else "0"
    return (
        f"FontName={SUBTITLE_FONT},FontSize=12,Bold=1,"
        f"PrimaryColour=&HFFFFFF,OutlineColour=&H000000,"
        f"BorderStyle=1,Outline=2,Shadow=1,"
        f"Alignment={alignment},MarginV={margin_v}"
    )


def build_cover_scale_crop_vf(out_w, out_h):
    ar_expr = f"{out_w}/{out_h}"
    scale = f"scale='if(gte(iw/ih,{ar_expr}),-2,{out_w})':'if(gte(iw/ih,{ar_expr}),{out_h},-2)'"
    crop = f"crop={out_w}:{out_h}:(iw-{out_w})/2:(ih-{out_h})/2"
    return f"{scale},{crop}"


def build_cover_scale_vf(out_w, out_h):
    ar_expr = f"{out_w}/{out_h}"
    scale = f"scale='if(gte(iw/ih,{ar_expr}),-2,{out_w})':'if(gte(iw/ih,{ar_expr}),{out_h},-2)'"
    return scale


def get_split_heights(out_h):
    if not out_h:
        return None, None
    bottom = min(BOTTOM_HEIGHT, max(1, out_h - 1))
    top = max(1, out_h - bottom)
    return top, bottom
def extract_video_id(url):
    """
    Extract the YouTube video ID from a given URL.
    Supports standard YouTube URLs, shortened URLs, and Shorts URLs.
    """
    parsed = urlparse(url)

    if parsed.hostname in ("youtu.be", "www.youtu.be"):
        return parsed.path[1:]

    if parsed.hostname in ("youtube.com", "www.youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2]

    return None


def get_model_size(model):
    """
    Get the approximate size of a Whisper model.
    """
    sizes = {
        "tiny": "75 MB",
        "base": "142 MB",
        "small": "466 MB",
        "medium": "1.5 GB",
        "large-v1": "2.9 GB",
        "large-v2": "2.9 GB",
        "large-v3": "2.9 GB"
    }
    return sizes.get(model, "unknown size")


def cek_dependensi(install_whisper=False, fatal=True):
    """
    Ensure required dependencies are available.
    Automatically updates yt-dlp and checks FFmpeg availability.
    """
    global WHISPER_MODEL
    args = getattr(cek_dependensi, "_args", None)
    should_update = bool(getattr(args, "update_ytdlp", False)) if args else False

    if should_update:
        print("Checking/Updating yt-dlp...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    if install_whisper:
        # Check if faster-whisper package is installed
        try:
            import faster_whisper
            print(f"✅ Faster-Whisper package installed.")
            
            # Check if selected model is cached
            cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
            model_name = f"faster-whisper-{WHISPER_MODEL}"
            
            model_cached = False
            if os.path.exists(cache_dir):
                try:
                    cached_items = os.listdir(cache_dir)
                    model_cached = any(model_name in item.lower() for item in cached_items)
                except Exception:
                    pass
            
            if model_cached:
                print(f"✅ Model '{WHISPER_MODEL}' already cached and ready.\n")
            else:
                print(f"⚠️  Model '{WHISPER_MODEL}' not found in cache.")
                print(f"   📥 Will auto-download ~{get_model_size(WHISPER_MODEL)} on first transcribe.")
                print(f"   ⏱️  Download happens only once, then cached for future use.\n")
                
        except ImportError:
            print("📦 Installing Faster-Whisper package...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "faster-whisper"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"✅ Faster-Whisper package installed successfully.")
            print(f"⚠️  Model '{WHISPER_MODEL}' (~{get_model_size(WHISPER_MODEL)}) will be downloaded on first use.\n")

    coba_masukkan_ffmpeg_ke_path()
    if not ffmpeg_tersedia():
        print("FFmpeg not found. Please install FFmpeg and ensure it is in PATH.")
        if fatal:
            sys.exit(1)
        return False
    return True


def ambil_metadata_dan_heatmap(video_id):
    """
    Fetch all video metadata, duration, and heatmap data in a single yt-dlp call.
    """
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--force-ipv4",
        "--quiet", "--no-warnings",
        "--skip-download",
        "--dump-json",
        f"https://youtu.be/{video_id}"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        raw = json.loads(res.stdout)
        
        # Parse and process heatmap
        heatmap_raw = raw.get("heatmap") or []
        spiked_segments = detect_viral_spikes(heatmap_raw)
        merged_segments = merge_adjacent_segments(spiked_segments, gap_limit=5.0)
        
        # Sort by score descending (select_non_overlapping requires sorted candidates)
        heatmap_data = sorted(merged_segments, key=lambda x: x["score"], reverse=True)
        
        duration = int(raw.get("duration") or 3600)
        title = raw.get("title") or "Video"
        
        return {
            "heatmap": heatmap_data,
            "duration": duration,
            "title": title
        }
    except Exception as e:
        print(f"Failed to fetch metadata/heatmap via yt-dlp: {str(e)}")
        return None


def ambil_stream_urls(video_id):
    """
    Get direct video and audio streaming URLs from yt-dlp.
    """
    coba_masukkan_ffmpeg_ke_path()
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--force-ipv4",
        "--quiet", "--no-warnings",
        "-g",
        "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080]+ba/b[height<=1080]/bv*+ba/b",
        f"https://youtu.be/{video_id}"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        urls = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        return urls
    except Exception as e:
        print(f"Failed to fetch direct stream URLs: {str(e)}")
        return None



def unduh_video_penuh(video_id, output_path):
    """
    Download the full YouTube video in one go using yt-dlp at unthrottled speed,
    and merge the audio and video into a single file at the specified output_path.
    """
    coba_masukkan_ffmpeg_ke_path()
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--force-ipv4",
        "--quiet", "--no-warnings",
        "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080]+ba/b[height<=1080]/bv*+ba/b",
        "--merge-output-format", "mkv",
        "-o", output_path,
        f"https://youtu.be/{video_id}"
    ]
    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        # Fallback to downloading best quality if the format selection failed
        cmd_fallback = [
            sys.executable, "-m", "yt_dlp",
            "--force-ipv4",
            "--quiet", "--no-warnings",
            "-f", "bv*+ba/b",
            "--merge-output-format", "mkv",
            "-o", output_path,
            f"https://youtu.be/{video_id}"
        ]
        try:
            subprocess.run(cmd_fallback, check=True)
            return True
        except Exception as e2:
            print(f"Failed to download full video: {str(e2)}")
            return False


def ambil_most_replayed(video_id):
    """
    Fetch and parse YouTube 'Most Replayed' heatmap data.
    Returns a list of high-engagement segments.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {"User-Agent": "Mozilla/5.0"}

    print("Reading YouTube heatmap data...")

    try:
        html = requests.get(url, headers=headers, timeout=20).text
    except Exception:
        return []

    match = re.search(
        r'"markers":\s*(\[.*?\])\s*,\s*"?markersMetadata"?',
        html,
        re.DOTALL
    )

    if not match:
        return []

    try:
        markers = json.loads(match.group(1).replace('\\"', '"'))
    except Exception:
        return []

    raw_markers = []

    for marker in markers:
        if "heatMarkerRenderer" in marker:
            marker = marker["heatMarkerRenderer"]

        try:
            score = float(marker.get("intensityScoreNormalized", 0))
            start = float(marker["startMillis"]) / 1000
            dur = float(marker["durationMillis"]) / 1000
            raw_markers.append({
                "start_time": start,
                "end_time": start + dur,
                "value": score
            })
        except Exception:
            continue

    # Process using our helpers:
    spiked_segments = detect_viral_spikes(raw_markers)
    merged_segments = merge_adjacent_segments(spiked_segments, gap_limit=5.0)
    merged_segments.sort(key=lambda x: x["score"], reverse=True)
    return merged_segments


def get_duration(video_id):
    """
    Retrieve the total duration of a YouTube video in seconds.
    """
    cmd = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--get-duration",
        f"https://youtu.be/{video_id}"
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        time_parts = res.stdout.strip().split(":")

        if len(time_parts) == 2:
            return int(time_parts[0]) * 60 + int(time_parts[1])
        if len(time_parts) == 3:
            return (
                int(time_parts[0]) * 3600 +
                int(time_parts[1]) * 60 +
                int(time_parts[2])
            )
    except Exception:
        pass

    return 3600


def generate_subtitle(video_file, subtitle_file, event_hook=None, language="id"):
    """
    Generate subtitle file using Faster-Whisper for the given video.
    Returns True if successful, False otherwise.
    """
    from faster_whisper import WhisperModel

    def load_and_transcribe():
        if callable(event_hook):
            try:
                event_hook("stage", {"stage": "subtitle_model_load"})
            except Exception:
                pass
        print(f"  Loading Faster-Whisper model '{WHISPER_MODEL}'...")
        print(f"  (If this is first time, downloading ~{get_model_size(WHISPER_MODEL)}...)")
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8", cpu_threads=CPU_THREADS)
        print("  ✅ Model loaded. Transcribing audio (4-5x faster than standard Whisper)...")
        if callable(event_hook):
            try:
                event_hook("stage", {"stage": "subtitle_transcribe"})
            except Exception:
                pass
        segments, info = model.transcribe(video_file, language=language)
        return segments

    try:
        segments = load_and_transcribe()
    except Exception as e:
        msg = str(e)
        if os.name == "nt" and "WinError 1314" in msg:
            print(f"  Failed to generate subtitle: {msg}")
            print("  Windows kamu kelihatan tidak mengizinkan symlink (HuggingFace cache).")
            print("  Retrying sekali lagi (biasanya langsung beres setelah fallback cache aktif)...")
            try:
                segments = load_and_transcribe()
            except Exception as e2:
                print(f"  Failed to generate subtitle: {str(e2)}")
                return False
        else:
            print(f"  Failed to generate subtitle: {msg}")
            return False

    if callable(event_hook):
        try:
            event_hook("stage", {"stage": "subtitle_write"})
        except Exception:
            pass
    print("  Generating subtitle file...")
    with open(subtitle_file, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            start_time = format_timestamp(segment.start)
            end_time = format_timestamp(segment.end)
            text = segment.text.strip()

            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")

    return True


def format_timestamp(seconds):
    """
    Convert seconds to SRT timestamp format (HH:MM:SS,mmm)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


_detected_encoder_cache = None

def get_best_encoder():
    global _detected_encoder_cache
    if _detected_encoder_cache is not None:
        return _detected_encoder_cache

    coba_masukkan_ffmpeg_ke_path()

    encoders_to_try = [
        ("h264_amf", ["-c:v", "h264_amf", "-rc", "cqp", "-qp_i", "22", "-qp_p", "22"]),
        ("h264_nvenc", ["-c:v", "h264_nvenc", "-preset", "p1", "-cq", "24"]),
        ("h264_qsv", ["-c:v", "h264_qsv", "-global_quality", "24"]),
    ]

    for enc_name, args in encoders_to_try:
        try:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=320x240:d=0.1", "-an"] + args + ["-f", "null", "-"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                # Extra check to ensure it printed success/open messages without crash
                if "Error" not in res.stderr and "failed" not in res.stderr.lower():
                    _detected_encoder_cache = args
                    return _detected_encoder_cache
        except Exception:
            pass

    _detected_encoder_cache = ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "26"]
    return _detected_encoder_cache


def smart_crop_video(input_path, output_path, out_width=720, out_height=1280, config=None):
    """
    Perform Auto Face Tracking Smart Crop 9:16 using OpenCV.
    Decodes the input video frame-by-frame, tracks the presenter's face,
    calculates a smooth bounding box center, crops, resizes to out_width x out_height,
    and encodes the output video (silent).
    """
    if cv2 is None:
        raise RuntimeError("OpenCV (opencv-python) tidak terinstall. Silakan jalankan 'pip install opencv-python'.")

    # Load Cascade Classifier
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        # Fallback to local cascade
        if os.path.exists("haarcascade_frontalface_default.xml"):
            face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        else:
            raise RuntimeError("Haar Cascade XML tidak ditemukan. Pastikan cv2.data.haarcascades tersedia.")

    # Parse config
    if config is None:
        config = {}
    smooth_factor = float(config.get("smooth_factor", 0.10))
    deadzone_size = float(config.get("deadzone_size", 0.15))
    tracking_speed = int(config.get("tracking_speed", 15))
    relock_timeout = int(config.get("relock_timeout", 30))
    crop_padding = float(config.get("crop_padding", 0.10))

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Gagal membuka video input: {input_path}")

    # Video specs
    w_orig = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_orig = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0

    # Calculate crop height and width based on crop_padding and target aspect ratio (9:16)
    # The default vertical crop height (when crop_padding=0) is h_orig.
    # When crop_padding > 0, we zoom in, so h_crop = h_orig * (1 - crop_padding).
    h_crop = int(h_orig * (1.0 - crop_padding))
    w_crop = int(h_crop * (9 / 16))
    
    # If the computed width is wider than the original video width, scale down both
    if w_crop > w_orig:
        w_crop = w_orig
        h_crop = int(w_orig * (16 / 9))
    
    # Keep sizes even for video writing
    if w_crop % 2 != 0:
        w_crop -= 1
    if h_crop % 2 != 0:
        h_crop -= 1
        
    # Ensure crop size is at least 100x100
    w_crop = max(100, w_crop)
    h_crop = max(100, h_crop)

    # Initialize crop window center
    current_cx = w_orig / 2.0
    current_cy = h_orig / 2.0

    # Tracking state
    tracking_active = False
    tracker = None
    lost_frames_count = 0
    last_face_bbox = None  # (x, y, w, h)

    def create_tracker():
        try:
            return cv2.TrackerKCF_create()
        except AttributeError:
            try:
                return cv2.legacy.TrackerKCF_create()
            except AttributeError:
                return None

    # Video Writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (out_width, out_height))
    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(output_path, fourcc, fps, (out_width, out_height))

    frame_idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            face_found = False
            face_x, face_y, face_w, face_h = 0, 0, 0, 0

            # 1. Update Tracker if active
            if tracking_active and tracker is not None:
                ok, bbox = tracker.update(frame)
                if ok:
                    tx, ty, tw, th = [int(v) for v in bbox]
                    # Check if tracker bbox is reasonable and intersects with frame
                    if tw > 10 and th > 10 and tx + tw > 0 and ty + th > 0 and tx < w_orig and ty < h_orig:
                        face_x, face_y, face_w, face_h = tx, ty, tw, th
                        face_found = True
                        lost_frames_count = 0
                        last_face_bbox = (face_x, face_y, face_w, face_h)
                
                if not face_found:
                    tracking_active = False
                    tracker = None

            # 2. Run face detection if tracker is not active
            if not face_found:
                scale_ratio = 1.0
                if gray.shape[0] > 360:
                    scale_ratio = 360.0 / gray.shape[0]
                    small_gray = cv2.resize(gray, (0,0), fx=scale_ratio, fy=scale_ratio)
                else:
                    small_gray = gray

                # Detect faces
                faces = face_cascade.detectMultiScale(small_gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                
                if len(faces) > 0:
                    best_face = max(faces, key=lambda f: f[2] * f[3])
                    face_x = int(best_face[0] / scale_ratio)
                    face_y = int(best_face[1] / scale_ratio)
                    face_w = int(best_face[2] / scale_ratio)
                    face_h = int(best_face[3] / scale_ratio)
                    
                    # Clamp to frame boundaries
                    face_x = max(0, min(w_orig - 1, face_x))
                    face_y = max(0, min(h_orig - 1, face_y))
                    face_w = max(10, min(w_orig - face_x, face_w))
                    face_h = max(10, min(h_orig - face_y, face_h))
                    
                    face_found = True
                    lost_frames_count = 0
                    last_face_bbox = (face_x, face_y, face_w, face_h)
                    
                    tracker = create_tracker()
                    if tracker is not None:
                        try:
                            tracker.init(frame, (face_x, face_y, face_w, face_h))
                            tracking_active = True
                        except Exception:
                            tracker = None
                            tracking_active = False

            # 3. Calculate target center
            if face_found:
                target_cx = face_x + face_w / 2.0
                target_cy = face_y + face_h / 2.0
            elif last_face_bbox is not None and lost_frames_count < relock_timeout:
                lost_frames_count += 1
                target_cx = last_face_bbox[0] + last_face_bbox[2] / 2.0
                target_cy = last_face_bbox[1] + last_face_bbox[3] / 2.0
            else:
                # Default to middle of the original screen
                target_cx = w_orig / 2.0
                target_cy = h_orig / 2.0

            # 4. Apply Deadzone
            # The deadzone is defined relative to the crop window size
            deadzone_w = w_crop * deadzone_size
            deadzone_h = h_crop * deadzone_size
            
            # X Deadzone check
            diff_x = target_cx - current_cx
            if abs(diff_x) > deadzone_w / 2.0:
                if diff_x > 0:
                    target_move_x = target_cx - deadzone_w / 2.0
                else:
                    target_move_x = target_cx + deadzone_w / 2.0
            else:
                target_move_x = current_cx

            # Y Deadzone check
            diff_y = target_cy - current_cy
            if abs(diff_y) > deadzone_h / 2.0:
                if diff_y > 0:
                    target_move_y = target_cy - deadzone_h / 2.0
                else:
                    target_move_y = target_cy + deadzone_h / 2.0
            else:
                target_move_y = current_cy

            # 5. LERP smoothing
            smooth_cx = current_cx + (target_move_x - current_cx) * smooth_factor
            smooth_cy = current_cy + (target_move_y - current_cy) * smooth_factor

            # 6. Tracking speed constraint (maximum shift per frame)
            movement_x = smooth_cx - current_cx
            if abs(movement_x) > tracking_speed:
                movement_x = max(-tracking_speed, min(tracking_speed, movement_x))
            smooth_cx = current_cx + movement_x

            movement_y = smooth_cy - current_cy
            if abs(movement_y) > tracking_speed:
                movement_y = max(-tracking_speed, min(tracking_speed, movement_y))
            smooth_cy = current_cy + movement_y

            # 7. Clamp to boundaries (avoid crop going out of bounds)
            left = int(smooth_cx - w_crop / 2.0)
            left = max(0, min(w_orig - w_crop, left))
            current_cx = left + w_crop / 2.0

            top = int(smooth_cy - h_crop / 2.0)
            top = max(0, min(h_orig - h_crop, top))
            current_cy = top + h_crop / 2.0

            # 8. Crop and Resize
            cropped = frame[top:top+h_crop, left:left+w_crop]
            resized = cv2.resize(cropped, (out_width, out_height))
            out.write(resized)
    finally:
        cap.release()
        out.release()



def proses_satu_clip(video_id, item, index, total_duration, crop_mode="default", use_subtitle=False, event_hook=None, stream_urls=None, local_video_path=None, subtitle_lang="en", output_ratio=None, out_w=None, out_h=None, output_dir=None, job_id=None, smart_config=None):
    """
    Download, crop, and export a single vertical clip
    based on a heatmap segment.
    
    Args:
        crop_mode: "default", "split_left", or "split_right"
        use_subtitle: whether to generate and burn subtitle
        stream_urls: optional direct streaming URLs for fast FFmpeg downloading
        local_video_path: optional path to the locally downloaded full video file for instant slicing
        subtitle_lang: optional language code for the subtitle transcription (e.g., "id", "en")
    """
    if smart_config is None:
        smart_config = {
            "smooth_factor": 0.10,
            "deadzone_size": 0.15,
            "tracking_speed": 15,
            "relock_timeout": 30,
            "crop_padding": 0.10
        }
    start_original = item["start"]
    end_original = item["start"] + item["duration"]

    start = max(0, start_original - PADDING)
    end = min(end_original + PADDING, total_duration)

    if end - start < 3:
        return False

    local_output_dir = output_dir if output_dir is not None else OUTPUT_DIR
    temp_file = os.path.join(local_output_dir, f"temp_{video_id}_{index}.mkv")
    subtitle_file = os.path.join(local_output_dir, f"temp_{video_id}_{index}.srt")
    if job_id:
        output_file = os.path.join(local_output_dir, f"clip_{job_id}_{index}.mp4")
    else:
        output_file = os.path.join(local_output_dir, f"clip_{index}.mp4")

    print(
        f"[Clip {index}] Processing segment "
        f"({int(start)}s - {int(end)}s, padding {PADDING}s)"
    )
    if callable(event_hook):
        try:
            event_hook("stage", {"stage": "download", "clip_index": index})
        except Exception:
            pass

    # Use local video file if provided (instant slicing)
    if local_video_path and os.path.exists(local_video_path):
        print(f"  Slicing segment from local video file...")
        duration = end - start
        cmd_download = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", str(start), "-t", str(duration), "-i", local_video_path,
            "-c:v", "copy", "-c:a", "copy",
            temp_file
        ]
        cmd_download_fallback = None
    # Use direct FFmpeg fast-seek copy if stream URLs are provided (with duration -t instead of -to to avoid hangs)
    elif stream_urls and isinstance(stream_urls, list) and len(stream_urls) > 0:
        print(f"  Downloading segment via direct FFmpeg fast-seek copy...")
        duration = end - start
        if len(stream_urls) >= 2:
            cmd_download = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-ss", str(start), "-t", str(duration), "-i", stream_urls[0],
                "-ss", str(start), "-t", str(duration), "-i", stream_urls[1],
                "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "copy",
                temp_file
            ]
        else:
            cmd_download = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-ss", str(start), "-t", str(duration), "-i", stream_urls[0],
                "-c:v", "copy", "-c:a", "copy",
                temp_file
            ]
        cmd_download_fallback = None
    else:
        cmd_download = [
            sys.executable, "-m", "yt_dlp",
            "--force-ipv4",
            "--quiet", "--no-warnings",
            "--concurrent-fragments", "3",
            "--download-sections", f"*{start}-{end}",
            "--merge-output-format", "mkv",
            "-f",
            "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080]+ba/b[height<=1080]/bv*+ba/b",
            "-o", temp_file,
            f"https://youtu.be/{video_id}"
        ]
        cmd_download_fallback = [
            sys.executable, "-m", "yt_dlp",
            "--force-ipv4",
            "--quiet", "--no-warnings",
            "--concurrent-fragments", "3",
            "--download-sections", f"*{start}-{end}",
            "--merge-output-format", "mkv",
            "-f", "bv*+ba/b",
            "-o", temp_file,
            f"https://youtu.be/{video_id}"
        ]

    try:
        try:
            subprocess.run(
                cmd_download,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except subprocess.CalledProcessError as e:
            if cmd_download_fallback:
                stderr = (e.stderr or "").strip()
                if "Requested format is not available" in stderr:
                    subprocess.run(
                        cmd_download_fallback,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                else:
                    raise
            else:
                raise

        if not os.path.exists(temp_file):
            print("Failed to download video segment.")
            return False

        # Generate subtitle from temp_file first (if enabled)
        subtitle_generated = False
        if use_subtitle:
            if callable(event_hook):
                try:
                    event_hook("stage", {"stage": "subtitle", "clip_index": index})
                except Exception:
                    pass
            print("  Generating subtitle...")
            if generate_subtitle(temp_file, subtitle_file, event_hook=event_hook, language=subtitle_lang):
                subtitle_generated = True
            else:
                print("  Subtitle generation failed, continuing without subtitle...")

        # Resolve aspect ratio width/height locally or fall back to globals
        if out_w is not None or out_h is not None or output_ratio == "original":
            local_out_w = out_w
            local_out_h = out_h
            local_output_ratio = output_ratio
        elif output_ratio is not None:
            local_output_ratio = output_ratio
            if output_ratio == "9:16":
                local_out_w, local_out_h = 720, 1280
            elif output_ratio == "1:1":
                local_out_w, local_out_h = 720, 720
            elif output_ratio == "16:9":
                local_out_w, local_out_h = 1280, 720
            elif output_ratio == "original":
                local_out_w, local_out_h = None, None
            else:
                raise ValueError(f"Invalid ratio: {output_ratio}")
        else:
            local_output_ratio = OUTPUT_RATIO
            local_out_w = OUT_WIDTH
            local_out_h = OUT_HEIGHT
        
        # Prepare subtitle filter if generated
        sub_vf = ""
        if subtitle_generated:
            subtitle_path = escape_subtitles_filter_path(subtitle_file)
            fonts_dir = SUBTITLE_FONTS_DIR
            fontsdir_arg = ""
            if fonts_dir and os.path.isdir(fonts_dir):
                fontsdir_arg = f":fontsdir='{escape_subtitles_filter_dir(fonts_dir)}'"
            force_style = build_subtitle_force_style()
            sub_vf = f"subtitles='{subtitle_path}'{fontsdir_arg}:force_style='{force_style}'"

        # Determine crop mode and combine with subtitle filter in a single encoding step
        if crop_mode == "default":
            if local_output_ratio == "original":
                vf = sub_vf
                cmd_crop = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", temp_file,
                    *(["-vf", vf] if vf else []),
                ] + get_best_encoder() + [
                    "-c:a", "aac", "-b:a", "128k",
                    output_file
                ]
            else:
                vf = build_cover_scale_crop_vf(local_out_w, local_out_h)
                if sub_vf:
                    vf = f"{vf},{sub_vf}"
                cmd_crop = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", temp_file,
                    "-vf", vf,
                ] + get_best_encoder() + [
                    "-c:a", "aac", "-b:a", "128k",
                    output_file
                ]
        elif crop_mode == "smart":
            # Smart Crop: Face Tracking mode
            temp_cropped_silent = os.path.join(local_output_dir, f"temp_smart_{video_id}_{index}.mp4")
            
            w_target = local_out_w if local_out_w else 720
            h_target = local_out_h if local_out_h else 1280
            
            if callable(event_hook):
                try:
                    event_hook("stage", {"stage": "crop", "clip_index": index})
                except Exception:
                    pass
                    
            print("  Running Auto Face Tracking Smart Crop...")
            smart_crop_video(temp_file, temp_cropped_silent, w_target, h_target, smart_config)
            
            # Setup FFmpeg to merge audio and burn subtitles
            if sub_vf:
                cmd_crop = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", temp_cropped_silent,
                    "-i", temp_file,
                    "-map", "0:v", "-map", "1:a?",
                    "-vf", sub_vf,
                ] + get_best_encoder() + [
                    "-c:a", "aac", "-b:a", "128k",
                    output_file
                ]
            else:
                cmd_crop = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", temp_cropped_silent,
                    "-i", temp_file,
                    "-map", "0:v", "-map", "1:a?",
                ] + get_best_encoder() + [
                    "-c:a", "aac", "-b:a", "128k",
                    output_file
                ]
        elif crop_mode in ("split_left", "split_right"):
            if local_output_ratio == "original" or not local_out_w or not local_out_h or local_out_h < local_out_w:
                vf = build_cover_scale_crop_vf(local_out_w or 720, local_out_h or 1280) if local_output_ratio != "original" else ""
                if sub_vf:
                    vf = f"{vf},{sub_vf}" if vf else sub_vf
                cmd_crop = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", temp_file,
                    *(["-vf", vf] if vf else []),
                ] + get_best_encoder() + [
                    "-c:a", "aac", "-b:a", "128k",
                    output_file
                ]
            else:
                top_h, bottom_h = get_split_heights(local_out_h)
                scaled = build_cover_scale_vf(local_out_w, local_out_h)
                facecam_x = "0" if crop_mode == "split_left" else f"iw-{local_out_w}"
                
                if sub_vf:
                    vf = (
                        f"{scaled}[scaled];"
                        f"[scaled]split=2[s1][s2];"
                        f"[s1]crop={local_out_w}:{top_h}:(iw-{local_out_w})/2:(ih-{local_out_h})/2[top];"
                        f"[s2]crop={local_out_w}:{bottom_h}:{facecam_x}:ih-{bottom_h}[bottom];"
                        f"[top][bottom]vstack[vsplit];"
                        f"[vsplit]{sub_vf}[out]"
                    )
                else:
                    vf = (
                        f"{scaled}[scaled];"
                        f"[scaled]split=2[s1][s2];"
                        f"[s1]crop={local_out_w}:{top_h}:(iw-{local_out_w})/2:(ih-{local_out_h})/2[top];"
                        f"[s2]crop={local_out_w}:{bottom_h}:{facecam_x}:ih-{bottom_h}[bottom];"
                        f"[top][bottom]vstack[out]"
                    )
                
                cmd_crop = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", temp_file,
                    "-filter_complex", vf,
                    "-map", "[out]", "-map", "0:a?",
                ] + get_best_encoder() + [
                    "-c:a", "aac", "-b:a", "128k",
                    output_file
                ]

        if callable(event_hook):
            try:
                stage_name = "burn_subtitle" if subtitle_generated else "crop"
                event_hook("stage", {"stage": stage_name, "clip_index": index})
            except Exception:
                pass
                
        print("  Processing clip with FFmpeg...")
        result = subprocess.run(
            cmd_crop,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if os.path.exists(temp_file):
            os.remove(temp_file)
        if os.path.exists(subtitle_file):
            os.remove(subtitle_file)
        temp_cropped_silent = os.path.join(local_output_dir, f"temp_smart_{video_id}_{index}.mp4")
        if os.path.exists(temp_cropped_silent):
            try:
                os.remove(temp_cropped_silent)
            except Exception:
                pass

        print("Clip successfully generated.")
        if callable(event_hook):
            try:
                event_hook("stage", {"stage": "done_clip", "clip_index": index})
            except Exception:
                pass
        return True

    except subprocess.CalledProcessError as e:
        for f in [temp_file, subtitle_file, os.path.join(local_output_dir, f"temp_smart_{video_id}_{index}.mp4")]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        print(f"Failed to generate this clip.")
        print(f"Error details: {e.stderr if e.stderr else e.stdout}")
        return False
    except Exception as e:
        for f in [temp_file, subtitle_file, os.path.join(local_output_dir, f"temp_smart_{video_id}_{index}.mp4")]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        print(f"Failed to generate this clip.")
        print(f"Error: {str(e)}")
        return False


def main():
    """
    Main entry point of the application.
    """
    global CPU_THREADS
    args = parse_args()
    cek_dependensi._args = args

    if args.whisper_model:
        global WHISPER_MODEL
        WHISPER_MODEL = args.whisper_model
    if args.subtitle_font:
        global SUBTITLE_FONT
        SUBTITLE_FONT = args.subtitle_font
    if args.subtitle_fontsdir:
        global SUBTITLE_FONTS_DIR
        SUBTITLE_FONTS_DIR = args.subtitle_fontsdir
    if args.subtitle_location:
        global SUBTITLE_LOCATION
        SUBTITLE_LOCATION = args.subtitle_location
    if args.ratio:
        set_ratio_preset(args.ratio)

    if args.check:
        cek_dependensi(install_whisper=False)
        print("✅ Basic dependencies OK.")
        return

    coba_masukkan_ffmpeg_ke_path()
    if not ffmpeg_tersedia():
        print("FFmpeg not found. Please install FFmpeg and ensure it is in PATH.")
        return

    crop_mode = args.crop
    crop_desc = None
    if crop_mode:
        crop_desc = {
            "default": "Default center crop",
            "split_left": "Split crop (bottom-left facecam)",
            "split_right": "Split crop (bottom-right facecam)",
            "smart": "Smart crop (face tracking)",
        }[crop_mode]

    subtitle_choice = args.subtitle
    if subtitle_choice:
        use_subtitle = subtitle_choice == "y"
    else:
        use_subtitle = None

    subtitle_lang = args.subtitle_lang or "id"

    link = args.url

    if crop_mode is None or use_subtitle is None or not link:
        print("\n=== Crop Mode ===")
        print("1. Default (center crop)")
        print("2. Split 1 (top: center, bottom: bottom-left (facecam))")
        print("3. Split 2 (top: center, bottom: bottom-right ((facecam))")
        print("4. Smart Crop (auto face tracking)")

        while crop_mode is None:
            choice = input("\nSelect crop mode (1-4): ").strip()
            if choice == "1":
                crop_mode = "default"
                crop_desc = "Default center crop"
                break
            if choice == "2":
                crop_mode = "split_left"
                crop_desc = "Split crop (bottom-left facecam)"
                break
            if choice == "3":
                crop_mode = "split_right"
                crop_desc = "Split crop (bottom-right facecam)"
                break
            if choice == "4":
                crop_mode = "smart"
                crop_desc = "Smart crop (face tracking)"
                break
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

        print(f"Selected: {crop_desc}")

        print("\n=== Auto Subtitle ===")
        print(f"Available model: {WHISPER_MODEL} (~{get_model_size(WHISPER_MODEL)})")
        while use_subtitle is None:
            subtitle_choice = input("Add auto subtitle using Faster-Whisper? (y/n): ").strip().lower()
            if subtitle_choice in ["y", "yes"]:
                use_subtitle = True
            elif subtitle_choice in ["n", "no"]:
                use_subtitle = False
            else:
                print("Invalid choice. Please enter y or n.")

        if use_subtitle:
            print(f"✅ Subtitle enabled (Model: {WHISPER_MODEL})")
            lang_choice = input("Select subtitle language (id/en) [default: en]: ").strip().lower()
            subtitle_lang = "id" if lang_choice == "id" else "en"
            print(f"   Language: {subtitle_lang}")
        else:
            print("❌ Subtitle disabled")

        print()

        cek_dependensi(install_whisper=use_subtitle)

        if not link:
            link = input("Link YT: ").strip()
    else:
        cek_dependensi(install_whisper=use_subtitle)

    video_id = extract_video_id(link)

    if not video_id:
        print("Invalid YouTube link.")
        return

    # Fetch metadata and heatmap in a single fast call
    print("Fetching video metadata and heatmap info...")
    meta = ambil_metadata_dan_heatmap(video_id)
    if meta:
        heatmap_data = meta["heatmap"]
        total_duration = meta["duration"]
        print(f"Title: {meta['title']}")
    else:
        # Fallback
        heatmap_data = ambil_most_replayed(video_id)
        total_duration = get_duration(video_id)

    if not heatmap_data:
        print("No high-engagement segments found.")
        return

    print(f"Found {len(heatmap_data)} high-engagement segments.")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Download full video locally for fast slicing
    local_video_path = os.path.join(OUTPUT_DIR, f"temp_full_{video_id}.mkv")
    print("Downloading full video locally (unthrottled)...")
    if unduh_video_penuh(video_id, local_video_path):
        print("✅ Full video downloaded successfully.")
    else:
        print("⚠️  Failed to download full video. Falling back to direct streaming URL extraction...")
        local_video_path = None

    stream_urls = None
    if not local_video_path:
        print("Fetching direct stream URLs for fast-seek downloading...")
        stream_urls = ambil_stream_urls(video_id)

    print(
        f"Processing clips with {PADDING}s pre-padding "
        f"and {PADDING}s post-padding."
    )
    print(f"Using crop mode: {crop_desc}")

    max_clips_val = args.max_clips if getattr(args, "max_clips", None) else MAX_CLIPS
    targets = select_non_overlapping(heatmap_data, max_clips_val, PADDING)
    success_count = 0

    workers = getattr(args, "workers", 0)
    import multiprocessing
    try:
        total_cores = multiprocessing.cpu_count()
        if workers <= 0:
            if total_cores >= 12:
                workers = 3
            elif total_cores >= 8:
                workers = 2
            else:
                workers = 1
        CPU_THREADS = max(1, min(4, total_cores // workers))
    except Exception:
        if workers <= 0:
            workers = 2
        CPU_THREADS = 2

    try:
        if workers > 1:
            print(f"Processing clips in parallel with {workers} workers (Whisper threads per worker: {CPU_THREADS})...")
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = []
                for idx, item in enumerate(targets, start=1):
                    futures.append(
                        executor.submit(
                            proses_satu_clip,
                            video_id,
                            item,
                            idx,
                            total_duration,
                            crop_mode,
                            use_subtitle,
                            None,
                            stream_urls,
                            local_video_path,
                            subtitle_lang
                        )
                    )
                for future in concurrent.futures.as_completed(futures):
                    if future.result():
                        success_count += 1
        else:
            for idx, item in enumerate(targets, start=1):
                if proses_satu_clip(
                    video_id,
                    item,
                    idx,
                    total_duration,
                    crop_mode,
                    use_subtitle,
                    stream_urls=stream_urls,
                    local_video_path=local_video_path,
                    subtitle_lang=subtitle_lang
                ):
                    success_count += 1
    finally:
        if local_video_path and os.path.exists(local_video_path):
            print("Cleaning up temporary full video file...")
            try:
                os.remove(local_video_path)
            except Exception as e:
                print(f"Failed to delete temporary full video file: {str(e)}")

    print(
        f"Finished processing. "
        f"{success_count} clip(s) successfully saved to '{OUTPUT_DIR}'."
    )


if __name__ == "__main__":
    main()
