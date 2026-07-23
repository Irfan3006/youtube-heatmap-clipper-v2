import os
import re
import json
import sys
import subprocess
import requests
import shutil
import math
from urllib.parse import urlparse, parse_qs
from types import SimpleNamespace
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

def detect_viral_spikes(heatmap_raw, min_score=0.20, max_duration=60):
    """
    Identify segments in the raw heatmap that show sharp intensity increases (spikes)
    above the local average. Enhance their scores by weighting both raw intensity
    and spike magnitude.
    Filters out the first 10% (intro) and last 10% (outro) of the video.
    """
    if not heatmap_raw:
        return []
        
    # Calculate approximate video duration
    total_duration = 0.0
    for m in heatmap_raw:
        end_t = float(m.get("end_time", 0))
        if end_t > total_duration:
            total_duration = end_t
            
    intro_threshold = total_duration * 0.10
    outro_threshold = total_duration * 0.90
        
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
            
            # Abaikan bagian intro (10% pertama) dan outro (10% terakhir)
            if start < intro_threshold or start > outro_threshold:
                continue
            
            # Derivative (difference from previous point)
            if i > 0:
                diff = val - values[i-1]
            else:
                diff = 0.0
                
            # Spike magnitude: positive rise + how much it stands above local average
            above_local = max(0.0, val - local_averages[i])
            spike_magnitude = max(0.0, diff) + above_local
            
            # Final score weighting:
            # Tingkatkan bobot spike (0.6) agar lebih memilih momen viral/lonjakan
            # daripada adegan datar (boring) yang hanya memiliki retensi tinggi.
            final_score = 0.4 * val + 0.6 * spike_magnitude
            
            if final_score >= min_score:
                duration_cap = max_duration if max_duration > 0 else 999999.0
                enhanced_segments.append({
                    "start": start,
                    "duration": min(end - start, duration_cap),
                    "score": final_score
                })
        except Exception:
            continue

    # Fallback: jika tidak ada segmen yang lolos min_score, tapi data heatmap ada,
    # jalankan ulang dengan min_score = 0.0 agar selalu mendapat segmen terbaik.
    if not enhanced_segments and heatmap_raw:
        for i in range(n):
            try:
                marker = heatmap_raw[i]
                start = float(marker.get("start_time", 0))
                end = float(marker.get("end_time", 0))
                val = values[i]
                
                if start < intro_threshold or start > outro_threshold:
                    continue
                    
                if i > 0:
                    diff = val - values[i-1]
                else:
                    diff = 0.0
                    
                above_local = max(0.0, val - local_averages[i])
                spike_magnitude = max(0.0, diff) + above_local
                final_score = 0.4 * val + 0.6 * spike_magnitude
                
                duration_cap = max_duration if max_duration > 0 else 999999.0
                enhanced_segments.append({
                    "start": start,
                    "duration": min(end - start, duration_cap),
                    "score": final_score
                })
            except Exception:
                continue
            
    return enhanced_segments

def merge_adjacent_segments(segments, gap_limit=5.0, max_duration=60):
    """
    Group consecutive/overlapping segments (within gap_limit seconds)
    into a single segment. Capped at max_duration.
    """
    if not segments:
        return []
    
    # Ensure sorted chronologically by start time
    sorted_segs = sorted(segments, key=lambda x: x["start"])
    
    merged = []
    current = sorted_segs[0].copy()
    
    duration_cap = max_duration if max_duration > 0 else 999999.0
    for next_seg in sorted_segs[1:]:
        current_end = current["start"] + current["duration"]
        if next_seg["start"] <= current_end + gap_limit:
            next_end = next_seg["start"] + next_seg["duration"]
            new_end = max(current_end, next_end)
            if new_end - current["start"] <= duration_cap:
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

def select_non_overlapping(segments, max_count, padding, overlap_threshold=0.0):
    """
    Select up to max_count segments from a list of segments (sorted by score descending),
    ensuring that no selected segment has a padded time range that overlaps beyond the
    overlap_threshold (0.0 to 1.0) with any already-selected segments.
    """
    selected = []
    # Sort segments by score descending to prioritize high-value segments
    sorted_segs = sorted(segments, key=lambda x: float(x.get("score", 0.0) or 0.0), reverse=True)
    
    for seg in sorted_segs:
        if len(selected) >= max_count:
            break
        
        try:
            start_val = float(seg.get("start", 0))
            dur_val = float(seg.get("duration", 0))
        except Exception:
            continue
            
        s_c = max(0.0, start_val - padding)
        e_c = start_val + dur_val + padding
        d_c = e_c - s_c
        
        if d_c <= 0:
            continue
            
        is_overlapping = False
        for sel in selected:
            try:
                sel_start = float(sel.get("start", 0))
                sel_dur = float(sel.get("duration", 0))
            except Exception:
                continue
                
            s_p = max(0.0, sel_start - padding)
            e_p = sel_start + sel_dur + padding
            
            # Check for overlap between padded ranges
            overlap = max(0.0, min(e_c, e_p) - max(s_c, s_p))
            if overlap_threshold >= 1.0:
                # No overlap filter at all
                pass
            elif overlap > overlap_threshold * d_c:
                is_overlapping = True
                break
                
        if not is_overlapping:
            selected.append(seg)
            
    return selected

def calculate_virality_metrics(seg, heatmap_raw=None, total_duration=3600):
    """
    Generate Smart Virality Metrics for a segment:
    - Virality Score (int: 1-99)
    - Hook Score (int: 1-99)
    - Retention Score (int: 1-99)
    - Content Trend Grade (str: A+, A, A-, B+, B, C)
    """
    raw_score = float(seg.get("score", 0.5) or 0.5)
    start_t = float(seg.get("start", 0.0) or 0.0)
    dur = float(seg.get("duration", 30.0) or 30.0)
    end_t = start_t + dur

    retention_val = 60
    hook_val = 60

    if heatmap_raw and isinstance(heatmap_raw, list) and len(heatmap_raw) > 0:
        clip_markers = []
        for m in heatmap_raw:
            try:
                m_start = float(m.get("start_time", 0.0))
                m_end = float(m.get("end_time", 0.0))
                if start_t <= m_start <= end_t or start_t <= m_end <= end_t:
                    clip_markers.append(float(m.get("value", 0.0)))
            except Exception:
                continue

        if clip_markers:
            avg_marker = sum(clip_markers) / len(clip_markers)
            retention_val = min(99, max(25, int(round(avg_marker * 100))))

            hook_marker = clip_markers[0]
            next_marker = clip_markers[1] if len(clip_markers) > 1 else hook_marker
            spike_jump = max(0.0, hook_marker - next_marker)
            hook_val = min(99, max(30, int(round((hook_marker * 0.7 + spike_jump * 0.3) * 100))))
        else:
            retention_val = min(99, max(35, int(round(raw_score * 90))))
            hook_val = min(99, max(40, int(round(raw_score * 95))))
    else:
        base = min(95, max(55, int(round(raw_score * 88 if raw_score > 0 else 72))))
        retention_val = base
        hook_val = min(99, base + 6)

    # Weighted Virality Score calculation: 45% Hook, 45% Retention, 10% Raw Score
    weighted = (hook_val * 0.45) + (retention_val * 0.45) + (min(99, int(raw_score * 90)) * 0.10)
    virality_score = min(99, max(20, int(round(weighted))))

    if virality_score >= 90:
        trend_grade = "A+"
    elif virality_score >= 82:
        trend_grade = "A"
    elif virality_score >= 74:
        trend_grade = "A-"
    elif virality_score >= 65:
        trend_grade = "B+"
    elif virality_score >= 55:
        trend_grade = "B"
    else:
        trend_grade = "C"

    return {
        "score": virality_score,
        "hook": hook_val,
        "retention": retention_val,
        "trend": trend_grade
    }

def enrich_segments_with_virality(segments, heatmap_raw=None, total_duration=3600):
    if not segments:
        return []
    enriched = []
    for s in segments:
        s_copy = dict(s)
        if "virality" not in s_copy:
            s_copy["virality"] = calculate_virality_metrics(s_copy, heatmap_raw, total_duration)
        enriched.append(s_copy)
    return enriched

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
        default="smart",
        help="Crop mode (default: smart)",
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
        default="id",
        help="Subtitle language (id or en, default: id)",
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
    parser.add_argument(
        "--subtitle-style",
        dest="subtitle_style",
        choices=["word_by_word", "phrase_by_phrase", "karaoke", "sentence", "line_by_line"],
        default="sentence",
        help="Subtitle timing and display style (default: sentence)",
    )
    parser.add_argument("--ratio", choices=["9:16", "1:1", "16:9", "original"], help="Output ratio preset")
    parser.add_argument("--check", action="store_true", help="Check dependencies then exit")
    parser.add_argument("--update-ytdlp", action="store_true", help="Auto-update yt-dlp on startup")
    parser.add_argument("--max-clips", type=int, default=10, help="Maximum number of clips to generate")
    parser.add_argument("--max-duration", type=int, default=60, help="Maximum duration of each clip in seconds (0 for no limit)")
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


def ambil_metadata_dan_heatmap(video_id, min_score=0.20, max_duration=60):
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
        spiked_segments = detect_viral_spikes(heatmap_raw, min_score=min_score, max_duration=max_duration)
        merged_segments = merge_adjacent_segments(spiked_segments, gap_limit=5.0, max_duration=max_duration)
        
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


def ambil_most_replayed(video_id, min_score=0.20, max_duration=60):
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
    spiked_segments = detect_viral_spikes(raw_markers, min_score=min_score, max_duration=max_duration)
    merged_segments = merge_adjacent_segments(spiked_segments, gap_limit=5.0, max_duration=max_duration)
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


def transcribe_segment(video_file, language="id", subtitle_style="sentence", event_hook=None):
    """
    Transcribe video_file using Faster-Whisper and return raw segments.
    """
    from faster_whisper import WhisperModel

    word_timestamps = subtitle_style != "sentence"

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
        segments_gen, info = model.transcribe(video_file, language=language, word_timestamps=word_timestamps)
        return list(segments_gen)

    try:
        return load_and_transcribe()
    except Exception as e:
        msg = str(e)
        if os.name == "nt" and "WinError 1314" in msg:
            print(f"  Failed to transcribe: {msg}")
            print("  Windows kamu kelihatan tidak mengizinkan symlink (HuggingFace cache).")
            print("  Retrying sekali lagi (biasanya langsung beres setelah fallback cache aktif)...")
            return load_and_transcribe()
        else:
            raise


def optimize_clip_boundaries(segments, peak_start, peak_end, max_duration, total_draft_duration):
    """
    Finds the best sub-window [A, B] within [0, total_draft_duration] such that:
    - B - A <= max_duration (if max_duration > 0)
    - A aligns with a segment/word start, B aligns with a segment/word end
    - It maximizes overlap with the peak [peak_start, peak_end]
    """
    if not max_duration or max_duration <= 0:
        max_duration = total_draft_duration

    # Fallback default: center the window around the peak
    peak_dur = peak_end - peak_start
    if peak_dur >= max_duration:
        center = (peak_start + peak_end) / 2.0
        fallback_start = max(0.0, center - max_duration / 2.0)
        fallback_end = min(total_draft_duration, fallback_start + max_duration)
    else:
        extra = max_duration - peak_dur
        fallback_start = max(0.0, peak_start - extra / 2.0)
        fallback_end = min(total_draft_duration, fallback_start + max_duration)
        if fallback_end == total_draft_duration:
            fallback_start = max(0.0, fallback_end - max_duration)

    if not segments:
        return fallback_start, fallback_end

    starts = sorted(list({seg.start for seg in segments if 0.0 <= seg.start < total_draft_duration}))
    ends = sorted(list({seg.end for seg in segments if 0.0 < seg.end <= total_draft_duration}))

    if 0.0 not in starts:
        starts.insert(0, 0.0)
    if total_draft_duration not in ends:
        ends.append(total_draft_duration)

    best_start = fallback_start
    best_end = fallback_end
    best_overlap = -1.0
    best_center_dist = 999999.0

    for A in starts:
        for B in ends:
            if B <= A:
                continue
            dur = B - A
            if dur > max_duration:
                continue

            overlap = max(0.0, min(B, peak_end) - max(A, peak_start))
            win_center = (A + B) / 2.0
            peak_center = (peak_start + peak_end) / 2.0
            center_dist = abs(win_center - peak_center)

            r_overlap = round(overlap, 2)
            r_center_dist = round(center_dist, 2)

            if (r_overlap > best_overlap) or (r_overlap == best_overlap and r_center_dist < best_center_dist):
                best_overlap = r_overlap
                best_center_dist = r_center_dist
                best_start = A
                best_end = B

    if best_end - best_start < 2.0:
        return fallback_start, fallback_end

    return best_start, best_end


def write_srt_from_segments(segments, subtitle_file, subtitle_style="sentence", t_start=0.0, t_end=None, event_hook=None):
    if t_end is None:
        t_end = 999999.0

    if callable(event_hook):
        try:
            event_hook("stage", {"stage": "subtitle_write"})
        except Exception:
            pass
    print("  Generating subtitle file...")

    has_words = False
    all_words = []
    for segment in segments:
        if hasattr(segment, "words") and segment.words:
            has_words = True
            for w in segment.words:
                if w.end <= t_start or w.start >= t_end:
                    continue
                shifted_w = SimpleNamespace(
                    start=max(0.0, w.start - t_start),
                    end=min(t_end - t_start, w.end - t_start),
                    word=w.word
                )
                all_words.append(shifted_w)

    if subtitle_style == "sentence" or not has_words:
        with open(subtitle_file, "w", encoding="utf-8") as f:
            srt_index = 1
            for segment in segments:
                if segment.end <= t_start or segment.start >= t_end:
                    continue
                seg_start = max(0.0, segment.start - t_start)
                seg_end = min(t_end - t_start, segment.end - t_start)
                start_time = format_timestamp(seg_start)
                end_time = format_timestamp(seg_end)
                text = segment.text.strip()
                f.write(f"{srt_index}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
                srt_index += 1
        return True

    # Ensure all word timings have valid durations
    for w in all_words:
        if w.end <= w.start:
            w.end = w.start + 0.1

    with open(subtitle_file, "w", encoding="utf-8") as f:
        if subtitle_style == "word_by_word":
            srt_index = 1
            for w in all_words:
                w_text = w.word.strip()
                if not w_text:
                    continue
                start_time = format_timestamp(w.start)
                end_time = format_timestamp(w.end)
                f.write(f"{srt_index}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{w_text}\n\n")
                srt_index += 1

        elif subtitle_style == "phrase_by_phrase":
            phrases = []
            current_phrase = []
            phrase_word_limit = 3
            phrase_char_limit = 18
            pause_limit = 0.8

            for w in all_words:
                w_text = w.word.strip()
                if not w_text:
                    continue

                if current_phrase:
                    last_w = current_phrase[-1]
                    time_gap = w.start - last_w.end
                    curr_text = " ".join([x.word.strip() for x in current_phrase])
                    
                    if (time_gap > pause_limit or 
                        any(last_w.word.strip().endswith(p) for p in [".", ",", "?", "!"]) or
                        len(current_phrase) >= phrase_word_limit or
                        len(curr_text) + len(w_text) + 1 > phrase_char_limit):
                        
                        phrases.append(current_phrase)
                        current_phrase = []

                current_phrase.append(w)

            if current_phrase:
                phrases.append(current_phrase)

            srt_index = 1
            for p_words in phrases:
                start_time = format_timestamp(p_words[0].start)
                end_time = format_timestamp(p_words[-1].end)
                p_text = " ".join([x.word.strip() for x in p_words])
                
                f.write(f"{srt_index}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{p_text}\n\n")
                srt_index += 1

        elif subtitle_style == "karaoke":
            phrases = []
            current_phrase = []
            karaoke_word_limit = 5
            karaoke_char_limit = 30
            pause_limit = 1.0

            for w in all_words:
                w_text = w.word.strip()
                if not w_text:
                    continue

                if current_phrase:
                    last_w = current_phrase[-1]
                    time_gap = w.start - last_w.end
                    curr_text = " ".join([x.word.strip() for x in current_phrase])
                    
                    if (time_gap > pause_limit or 
                        any(last_w.word.strip().endswith(p) for p in [".", "?", "!"]) or
                        len(current_phrase) >= karaoke_word_limit or
                        len(curr_text) + len(w_text) + 1 > karaoke_char_limit):
                        
                        phrases.append(current_phrase)
                        current_phrase = []

                current_phrase.append(w)

            if current_phrase:
                phrases.append(current_phrase)

            srt_index = 1
            for p_words in phrases:
                n_words = len(p_words)
                for i, active_w in enumerate(p_words):
                    sub_start = active_w.start
                    if i < n_words - 1:
                        sub_end = p_words[i+1].start
                    else:
                        sub_end = active_w.end

                    if sub_end <= sub_start:
                        sub_end = sub_start + 0.1

                    start_time = format_timestamp(sub_start)
                    end_time = format_timestamp(sub_end)

                    text_parts = []
                    for j, w_item in enumerate(p_words):
                        w_item_text = w_item.word.strip()
                        if j == i:
                            text_parts.append(f"<font color=\"#FFCC00\">{w_item_text}</font>")
                        else:
                            text_parts.append(w_item_text)
                    p_text = " ".join(text_parts)

                    f.write(f"{srt_index}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{p_text}\n\n")
                    srt_index += 1

        elif subtitle_style == "line_by_line":
            phrases = []
            current_phrase = []
            line_word_limit = 10
            line_char_limit = 50
            pause_limit = 1.0

            for w in all_words:
                w_text = w.word.strip()
                if not w_text:
                    continue

                if current_phrase:
                    last_w = current_phrase[-1]
                    time_gap = w.start - last_w.end
                    curr_text = " ".join([x.word.strip() for x in current_phrase])
                    
                    if (time_gap > pause_limit or 
                        any(last_w.word.strip().endswith(p) for p in [".", "?", "!"]) or
                        len(current_phrase) >= line_word_limit or
                        len(curr_text) + len(w_text) + 1 > line_char_limit):
                        
                        phrases.append(current_phrase)
                        current_phrase = []

                current_phrase.append(w)

            if current_phrase:
                phrases.append(current_phrase)

            srt_index = 1
            for p_words in phrases:
                start_time = format_timestamp(p_words[0].start)
                end_time = format_timestamp(p_words[-1].end)
                
                text_list = [x.word.strip() for x in p_words]
                total_len = sum(len(t) for t in text_list) + len(text_list) - 1
                if total_len <= 28:
                    p_text = " ".join(text_list)
                else:
                    mid = len(text_list) // 2
                    line1 = " ".join(text_list[:mid])
                    line2 = " ".join(text_list[mid:])
                    p_text = f"{line1}\n{line2}"

                f.write(f"{srt_index}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{p_text}\n\n")
                srt_index += 1

    return True


def generate_subtitle(video_file, subtitle_file, event_hook=None, language="id", subtitle_style="sentence"):
    try:
        segments = transcribe_segment(video_file, language, subtitle_style, event_hook)
        return write_srt_from_segments(segments, subtitle_file, subtitle_style, t_start=0.0, t_end=None, event_hook=event_hook)
    except Exception as e:
        print(f"Failed to generate subtitle: {str(e)}")
        return False



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


def smart_crop_video(input_path, output_path, out_width=720, out_height=1280, config=None, start_time=0.0, end_time=None):
    """
    Perform Auto Face Tracking Smart Crop using OpenCV.
    Decodes the input video frame-by-frame, tracks the presenter's face using a hybrid
    YuNet DNN and ROI frontal/profile face detection logic, calculates a smooth bounding box center,
    crops, resizes to out_width x out_height, and encodes the output video (silent).
    """
    if cv2 is None:
        raise RuntimeError("OpenCV (opencv-python) tidak terinstall. Silakan jalankan 'pip install opencv-python'.")

    # Parse config
    if config is None:
        config = {}
    smooth_factor = float(config.get("smooth_factor", 0.10))
    deadzone_size = float(config.get("deadzone_size", 0.15))
    tracking_speed = int(config.get("tracking_speed", 15))
    relock_timeout = int(config.get("relock_timeout", 30))
    crop_padding = float(config.get("crop_padding", 0.10))
    tracking_strategy = config.get("tracking_strategy", "hybrid")

    # Initialize Face Detectors
    # 1. Try YuNet DNN Face Detector first
    yunet_model_path = "face_detection_yunet_2023mar.onnx"
    yunet_available = False
    detector = None

    if hasattr(cv2, 'FaceDetectorYN'):
        if not os.path.exists(yunet_model_path):
            print("  Downloading YuNet face detection model...")
            try:
                import urllib.request
                url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
                urllib.request.urlretrieve(url, yunet_model_path)
                print("  YuNet model downloaded successfully.")
            except Exception as e:
                print(f"  Gagal mendownload YuNet model: {e}. Menggunakan Haar Cascade.")
        
        if os.path.exists(yunet_model_path):
            try:
                # Initialize with a dummy size, we will resize it dynamically per frame if needed
                detector = cv2.FaceDetectorYN.create(yunet_model_path, "", (320, 320))
                yunet_available = True
                print("  Using YuNet DNN Face Detector (More accurate)")
            except Exception as e:
                print(f"  Gagal memuat YuNet model: {e}. Menggunakan Haar Cascade.")

    # 2. Setup Haar Cascade Classifiers as fallback or primary if YuNet is unavailable
    face_cascade = None
    profile_cascade = None
    if not yunet_available:
        print("  Using Haar Cascade Face Detector (Legacy)")
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        if face_cascade.empty():
            if os.path.exists("haarcascade_frontalface_default.xml"):
                face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
            else:
                raise RuntimeError("Haar Cascade Frontal Face XML tidak ditemukan.")

        profile_cascade_path = cv2.data.haarcascades + "haarcascade_profileface.xml"
        profile_cascade = cv2.CascadeClassifier(profile_cascade_path)
        if profile_cascade.empty() and os.path.exists("haarcascade_profileface.xml"):
            profile_cascade = cv2.CascadeClassifier("haarcascade_profileface.xml")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Gagal membuka video input: {input_path}")

    # Video specs
    w_orig = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_orig = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0

    diag = math.sqrt(w_orig**2 + h_orig**2)
    def get_face_score(f, scale=1.0):
        fx, fy, fw, fh = f
        # Convert to original coordinates
        fx = fx / scale
        fy = fy / scale
        fw = fw / scale
        fh = fh / scale
        
        f_cx = fx + fw / 2.0
        f_cy = fy + fh / 2.0
        f_area = fw * fh
        center_dist = math.sqrt((f_cx - w_orig / 2.0)**2 + (f_cy - h_orig / 2.0)**2)
        norm_center_dist = center_dist / (diag / 2.0)
        
        if tracking_strategy == "largest":
            return f_area
        elif tracking_strategy == "center":
            return 1.0 / (1.0 + norm_center_dist)
        else: # "hybrid"
            return f_area / (1.0 + 4.0 * norm_center_dist)

    # Handle start_time and end_time seeking
    if start_time > 0:
        start_frame = int(start_time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    else:
        start_frame = 0

    if end_time is not None:
        end_frame = int(end_time * fps)
    else:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        end_frame = total_frames if total_frames > 0 else 999999

    # Calculate dynamic aspect ratio and crop window size
    aspect_ratio = out_width / out_height
    h_crop = int(h_orig * (1.0 - crop_padding))
    w_crop = int(h_crop * aspect_ratio)
    
    # Keep crop within original video bounds
    if w_crop > w_orig:
        w_crop = w_orig
        h_crop = int(w_orig / aspect_ratio)
    if h_crop > h_orig:
        h_crop = h_orig
        w_crop = int(h_orig * aspect_ratio)
    
    # Ensure crop dimensions are even (required by some encoders)
    if w_crop % 2 != 0:
        w_crop -= 1
    if h_crop % 2 != 0:
        h_crop -= 1
        
    w_crop = max(100, w_crop)
    h_crop = max(100, h_crop)

    # Initialize crop window center at the middle of original screen
    current_cx = w_orig / 2.0
    current_cy = h_orig / 2.0

    # Tracking state (ROI-based tracking-by-detection)
    last_face_bbox = None  # (x, y, w, h) in original resolution coordinates
    lost_frames_count = 0

    # Video Writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (out_width, out_height))
    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(output_path, fourcc, fps, (out_width, out_height))

    frame_idx = start_frame
    try:
        while frame_idx < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_found = False
            face_x, face_y, face_w, face_h = 0, 0, 0, 0

            # --- DETECT USING YUNET (PRIMARY) ---
            if yunet_available and detector is not None:
                # Resize frame to a fixed height (e.g. 360) for fast deep learning inference
                scale_ratio = 1.0
                if frame.shape[0] > 360:
                    scale_ratio = 360.0 / frame.shape[0]
                    w_small = int(frame.shape[1] * scale_ratio)
                    h_small = int(frame.shape[0] * scale_ratio)
                    small_frame = cv2.resize(frame, (w_small, h_small))
                else:
                    small_frame = frame
                    w_small = frame.shape[1]
                    h_small = frame.shape[0]

                detector.setInputSize((w_small, h_small))
                ret_yn, faces_yn = detector.detect(small_frame)

                if faces_yn is not None and len(faces_yn) > 0:
                    faces = []
                    for f in faces_yn:
                        fx = int(f[0] / scale_ratio)
                        fy = int(f[1] / scale_ratio)
                        fw = int(f[2] / scale_ratio)
                        fh = int(f[3] / scale_ratio)
                        score = f[14]
                        # Score threshold: only accept confident detections (>0.5)
                        if score > 0.5:
                            faces.append((fx, fy, fw, fh))

                    if len(faces) > 0:
                        # Choose face closest to last known position if available within distance threshold, else the strategy
                        if last_face_bbox is not None:
                            last_cx = last_face_bbox[0] + last_face_bbox[2]/2.0
                            last_cy = last_face_bbox[1] + last_face_bbox[3]/2.0
                            closest_face = min(faces, key=lambda f: (f[0]+f[2]/2.0 - last_cx)**2 + (f[1]+f[3]/2.0 - last_cy)**2)
                            dist = math.sqrt((closest_face[0]+closest_face[2]/2.0 - last_cx)**2 + (closest_face[1]+closest_face[3]/2.0 - last_cy)**2)
                            if dist < diag * 0.25:
                                best_face = closest_face
                                face_found = True
                            else:
                                # Too far, treat as lost face (don't snap to spectator)
                                face_found = False
                        else:
                            best_face = max(faces, key=lambda f: get_face_score(f, scale=1.0))
                            face_found = True

                        if face_found:
                            face_x, face_y, face_w, face_h = best_face
                            # Clamp to boundaries
                            face_x = max(0, min(w_orig - 1, face_x))
                            face_y = max(0, min(h_orig - 1, face_y))
                            face_w = max(10, min(w_orig - face_x, face_w))
                            face_h = max(10, min(h_orig - face_y, face_h))

            # --- DETECT USING HAAR CASCADES (FALLBACK) ---
            if not face_found and face_cascade is not None:
                # 1. Search in ROI around last known face location (faster & prevents drifting)
                if last_face_bbox is not None:
                    lx, ly, lw, lh = last_face_bbox
                    # Define ROI expanded by 2.5x around the center
                    roi_w = int(lw * 2.5)
                    roi_h = int(lh * 2.5)
                    roi_x = int((lx + lw/2.0) - roi_w/2.0)
                    roi_y = int((ly + lh/2.0) - roi_h/2.0)
                    
                    # Clamp ROI boundaries to frame
                    roi_x = max(0, min(w_orig - 50, roi_x))
                    roi_y = max(0, min(h_orig - 50, roi_y))
                    roi_w = max(50, min(w_orig - roi_x, roi_w))
                    roi_h = max(50, min(h_orig - roi_y, roi_h))
                    
                    gray_roi = gray[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
                    
                    # Constrain search min/max size dynamically based on last face size
                    min_face_size = max(30, int(lw * 0.5))
                    max_face_size = int(lw * 2.0)

                    # Detect frontal face in ROI
                    faces_detected = face_cascade.detectMultiScale(
                        gray_roi, scaleFactor=1.1, minNeighbors=6, 
                        minSize=(min_face_size, min_face_size),
                        maxSize=(max_face_size, max_face_size)
                    )
                    faces = [tuple(f) for f in faces_detected] if len(faces_detected) > 0 else []
                    
                    # Fallback to profile face in ROI if frontal face fails
                    if len(faces) == 0 and not profile_cascade.empty():
                        # Left-profile
                        faces_p = profile_cascade.detectMultiScale(
                            gray_roi, scaleFactor=1.1, minNeighbors=6, 
                            minSize=(min_face_size, min_face_size),
                            maxSize=(max_face_size, max_face_size)
                        )
                        if len(faces_p) > 0:
                            faces.extend([tuple(f) for f in faces_p])
                        
                        # Right-profile (flipped)
                        flipped_roi = cv2.flip(gray_roi, 1)
                        faces_pf = profile_cascade.detectMultiScale(
                            flipped_roi, scaleFactor=1.1, minNeighbors=6, 
                            minSize=(min_face_size, min_face_size),
                            maxSize=(max_face_size, max_face_size)
                        )
                        if len(faces_pf) > 0:
                            for (fx, fy, fw, fh) in faces_pf:
                                mapped_x = roi_w - fx - fw
                                faces.append((mapped_x, fy, fw, fh))
                    
                    if len(faces) > 0:
                        # Choose face closest to ROI center (the previous face position)
                        roi_cx, roi_cy = roi_w / 2.0, roi_h / 2.0
                        best_face = min(faces, key=lambda f: (f[0]+f[2]/2.0 - roi_cx)**2 + (f[1]+f[3]/2.0 - roi_cy)**2)
                        
                        temp_face_x = best_face[0] + roi_x
                        temp_face_y = best_face[1] + roi_y
                        temp_face_w = best_face[2]
                        temp_face_h = best_face[3]
                        
                        last_cx = lx + lw/2.0
                        last_cy = ly + lh/2.0
                        dist = math.sqrt((temp_face_x + temp_face_w/2.0 - last_cx)**2 + (temp_face_y + temp_face_h/2.0 - last_cy)**2)
                        
                        if dist < diag * 0.25:
                            face_x = temp_face_x
                            face_y = temp_face_y
                            face_w = temp_face_w
                            face_h = temp_face_h
                            face_found = True

                # 2. Fallback to Full Frame face detection if not found in ROI (or first frame)
                if not face_found:
                    scale_ratio = 1.0
                    if gray.shape[0] > 360:
                        scale_ratio = 360.0 / gray.shape[0]
                        small_gray = cv2.resize(gray, (0, 0), fx=scale_ratio, fy=scale_ratio)
                    else:
                        small_gray = gray

                    # Detect faces
                    faces_detected = face_cascade.detectMultiScale(small_gray, scaleFactor=1.1, minNeighbors=6, minSize=(30, 30))
                    faces = [tuple(f) for f in faces_detected] if len(faces_detected) > 0 else []
                    
                    if len(faces) == 0 and not profile_cascade.empty():
                        # Left-profile
                        faces_p = profile_cascade.detectMultiScale(small_gray, scaleFactor=1.1, minNeighbors=6, minSize=(30, 30))
                        if len(faces_p) > 0:
                            faces.extend([tuple(f) for f in faces_p])
                        
                        # Right-profile (flipped)
                        flipped_small = cv2.flip(small_gray, 1)
                        faces_pf = profile_cascade.detectMultiScale(flipped_small, scaleFactor=1.1, minNeighbors=6, minSize=(30, 30))
                        if len(faces_pf) > 0:
                            w_small = small_gray.shape[1]
                            for (fx, fy, fw, fh) in faces_pf:
                                mapped_x = w_small - fx - fw
                                faces.append((mapped_x, fy, fw, fh))
                    
                    if len(faces) > 0:
                        # Choose face closest to last known position if available within distance threshold, else the strategy
                        if last_face_bbox is not None:
                            last_cx_small = (last_face_bbox[0] + last_face_bbox[2]/2.0) * scale_ratio
                            last_cy_small = (last_face_bbox[1] + last_face_bbox[3]/2.0) * scale_ratio
                            closest_face = min(faces, key=lambda f: (f[0]+f[2]/2.0 - last_cx_small)**2 + (f[1]+f[3]/2.0 - last_cy_small)**2)
                            
                            # Convert back to original coordinates to calculate distance
                            cf_x = int(closest_face[0] / scale_ratio)
                            cf_y = int(closest_face[1] / scale_ratio)
                            cf_w = int(closest_face[2] / scale_ratio)
                            cf_h = int(closest_face[3] / scale_ratio)
                            cf_cx = cf_x + cf_w / 2.0
                            cf_cy = cf_y + cf_h / 2.0
                            
                            last_cx = last_face_bbox[0] + last_face_bbox[2]/2.0
                            last_cy = last_face_bbox[1] + last_face_bbox[3]/2.0
                            dist = math.sqrt((cf_cx - last_cx)**2 + (cf_cy - last_cy)**2)
                            
                            if dist < diag * 0.25:
                                face_x = cf_x
                                face_y = cf_y
                                face_w = cf_w
                                face_h = cf_h
                                face_found = True
                            else:
                                face_found = False
                        else:
                            best_face = max(faces, key=lambda f: get_face_score(f, scale=scale_ratio))
                            face_x = int(best_face[0] / scale_ratio)
                            face_y = int(best_face[1] / scale_ratio)
                            face_w = int(best_face[2] / scale_ratio)
                            face_h = int(best_face[3] / scale_ratio)
                            face_found = True
                        
                        if face_found:
                            # Clamp to boundaries
                            face_x = max(0, min(w_orig - 1, face_x))
                            face_y = max(0, min(h_orig - 1, face_y))
                            face_w = max(10, min(w_orig - face_x, face_w))
                            face_h = max(10, min(h_orig - face_y, face_h))

            # 3. Calculate target center point
            if face_found:
                target_cx = face_x + face_w / 2.0
                target_cy = face_y + face_h / 2.0
                last_face_bbox = (face_x, face_y, face_w, face_h)
                lost_frames_count = 0
            elif last_face_bbox is not None and lost_frames_count < relock_timeout:
                lost_frames_count += 1
                target_cx = last_face_bbox[0] + last_face_bbox[2] / 2.0
                target_cy = last_face_bbox[1] + last_face_bbox[3] / 2.0
            else:
                # Default to middle of original video
                target_cx = w_orig / 2.0
                target_cy = h_orig / 2.0
                last_face_bbox = None

            # 4. Apply Deadzone
            deadzone_w = w_crop * deadzone_size
            deadzone_h = h_crop * deadzone_size
            
            diff_x = target_cx - current_cx
            if abs(diff_x) > deadzone_w / 2.0:
                if diff_x > 0:
                    target_move_x = target_cx - deadzone_w / 2.0
                else:
                    target_move_x = target_cx + deadzone_w / 2.0
            else:
                target_move_x = current_cx

            diff_y = target_cy - current_cy
            if abs(diff_y) > deadzone_h / 2.0:
                if diff_y > 0:
                    target_move_y = target_cy - deadzone_h / 2.0
                else:
                    target_move_y = target_cy + deadzone_h / 2.0
            else:
                target_move_y = current_cy

            # 5. Scene change / Instant Lock detection
            # Jika jarak antara target dan posisi saat ini sangat jauh (misal > 30% dari layar),
            # ini menandakan pergantian kamera (scene change). Langsung auto-lock (snap).
            jump_threshold_x = w_orig * 0.30
            jump_threshold_y = h_orig * 0.30

            # Only allow instant snap if a face was actually found in this frame
            if face_found and (abs(target_move_x - current_cx) > jump_threshold_x or abs(target_move_y - current_cy) > jump_threshold_y):
                smooth_cx = target_move_x
                smooth_cy = target_move_y
            else:
                # LERP smoothing normal
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



def proses_satu_clip(video_id, item, index, total_duration, crop_mode="smart", use_subtitle=False, event_hook=None, stream_urls=None, local_video_path=None, subtitle_lang="en", output_ratio=None, out_w=None, out_h=None, output_dir=None, job_id=None, smart_config=None, subtitle_style="sentence", max_duration=60):
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
            "relock_timeout": 150,
            "crop_padding": 0.10,
            "tracking_strategy": "hybrid"
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

        # Determine precise t_start and t_end relative to temp_file
        peak_start = max(0.0, start_original - start)
        peak_end = min(end - start, end_original - start)
        draft_duration = end - start

        t_start = 0.0
        t_end = draft_duration
        
        subtitle_generated = False
        if use_subtitle:
            if callable(event_hook):
                try:
                    event_hook("stage", {"stage": "subtitle", "clip_index": index})
                except Exception:
                    pass
            print("  Generating subtitle and optimizing boundaries...")
            try:
                transcribed_segments = transcribe_segment(temp_file, language=subtitle_lang, subtitle_style=subtitle_style, event_hook=event_hook)
                t_start, t_end = optimize_clip_boundaries(transcribed_segments, peak_start, peak_end, max_duration, draft_duration)
                write_srt_from_segments(transcribed_segments, subtitle_file, subtitle_style, t_start, t_end, event_hook=event_hook)
                subtitle_generated = True
            except Exception as e:
                print(f"  Transcription/Alignment failed: {str(e)}")
                print("  Falling back to raw time-centered clip...")
                t_start, t_end = optimize_clip_boundaries([], peak_start, peak_end, max_duration, draft_duration)
        else:
            t_start, t_end = optimize_clip_boundaries([], peak_start, peak_end, max_duration, draft_duration)

        t_SS = t_start
        t_DUR = t_end - t_start
        print(f"  Precise cut selected: {t_SS:.2f}s to {t_end:.2f}s (duration: {t_DUR:.2f}s)")

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
                    "-ss", str(t_SS), "-t", str(t_DUR), "-i", temp_file,
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
                    "-ss", str(t_SS), "-t", str(t_DUR), "-i", temp_file,
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
            smart_crop_video(temp_file, temp_cropped_silent, w_target, h_target, smart_config, start_time=t_SS, end_time=t_end)
            
            # Setup FFmpeg to merge audio and burn subtitles
            if sub_vf:
                cmd_crop = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", temp_cropped_silent,
                    "-ss", str(t_SS), "-t", str(t_DUR), "-i", temp_file,
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
                    "-ss", str(t_SS), "-t", str(t_DUR), "-i", temp_file,
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
                    "-ss", str(t_SS), "-t", str(t_DUR), "-i", temp_file,
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
                    "-ss", str(t_SS), "-t", str(t_DUR), "-i", temp_file,
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
    max_duration_val = args.max_duration if getattr(args, "max_duration", None) is not None else 60

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
    subtitle_style = args.subtitle_style or "sentence"

    link = args.url

    if crop_mode is None or use_subtitle is None or not link:
        if crop_mode is None:
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

            print("\n=== Subtitle Style / Timing ===")
            print("1. Word by Word (Per Kata)")
            print("2. Phrase by Phrase (Per Frasa)")
            print("3. Karaoke / Active Word Highlight")
            print("4. Sentence / Full Sentence [default]")
            print("5. Line by Line (1-2 Baris)")
            style_choice = input("Select subtitle style (1-5) [default: 4]: ").strip()
            if style_choice == "1":
                subtitle_style = "word_by_word"
            elif style_choice == "2":
                subtitle_style = "phrase_by_phrase"
            elif style_choice == "3":
                subtitle_style = "karaoke"
            elif style_choice == "5":
                subtitle_style = "line_by_line"
            else:
                subtitle_style = "sentence"
            print(f"   Style: {subtitle_style}")
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
    meta = ambil_metadata_dan_heatmap(video_id, max_duration=max_duration_val)
    if meta:
        heatmap_data = meta["heatmap"]
        total_duration = meta["duration"]
        print(f"Title: {meta['title']}")
    else:
        # Fallback
        heatmap_data = ambil_most_replayed(video_id, max_duration=max_duration_val)
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
                            subtitle_lang,
                            subtitle_style=subtitle_style,
                            max_duration=max_duration_val
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
                    subtitle_lang=subtitle_lang,
                    subtitle_style=subtitle_style,
                    max_duration=max_duration_val
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
