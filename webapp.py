import os
import json
import subprocess
import sys
import threading
import time
import uuid
from types import SimpleNamespace

from flask import Flask, jsonify, render_template, request, send_from_directory

import run as core


app = Flask(__name__, static_folder="static", template_folder="templates")

jobs_lock = threading.Lock()
jobs = {}
preview_lock = threading.Lock()
preview_cache = {}


def now_ms():
    return int(time.time() * 1000)


def safe_int(value, default=None):
    try:
        return int(value)
    except Exception:
        return default


def parse_time_to_seconds(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip()
    if not s:
        return None
    if s.isdigit():
        return int(s)
    parts = s.split(":")
    if len(parts) == 2:
        m, sec = parts
        return int(m) * 60 + int(float(sec))
    if len(parts) == 3:
        h, m, sec = parts
        return int(h) * 3600 + int(m) * 60 + int(float(sec))
    return None


def set_job(job_id, **patch):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return
        job.update(patch)


def add_log(job_id, line):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return
        job["logs"].append(line)
        if len(job["logs"]) > 300:
            job["logs"] = job["logs"][-300:]


def list_outputs(job_dir, job_id=None):
    if not os.path.isdir(job_dir):
        return []
    items = []
    for name in os.listdir(job_dir):
        path = os.path.join(job_dir, name)
        if os.path.isfile(path) and name.lower().endswith(".mp4"):
            if job_id is None or name.startswith(f"clip_{job_id}_"):
                items.append({"name": name, "size": os.path.getsize(path)})
    items.sort(key=lambda x: x["name"])
    return items


def run_job(job_id, payload):
    started = now_ms()
    try:
        set_job(job_id, status="running", started_at=started)

        url = (payload.get("url") or "").strip()
        if not url:
            raise ValueError("URL kosong")

        crop = payload.get("crop") or "smart"
        ratio = payload.get("ratio") or "9:16"
        subtitle = bool(payload.get("subtitle"))
        subtitle_lang = payload.get("subtitle_lang") or "en"
        subtitle_style = payload.get("subtitle_style") or "sentence"
        whisper_model = payload.get("whisper_model") or "small"
        subtitle_font = payload.get("subtitle_font") or "Arial"
        subtitle_location = payload.get("subtitle_location") or "bottom"
        subtitle_fontsdir = payload.get("subtitle_fontsdir") or None
        if not subtitle_fontsdir and os.path.isdir("fonts"):
            subtitle_fontsdir = "fonts"
        padding = safe_int(payload.get("padding"), 10)
        max_clips = safe_int(payload.get("max_clips"), 10)
        max_duration = safe_int(payload.get("max_duration"), 60)
        mode = payload.get("mode") or "heatmap"
        set_job(job_id, subtitle_enabled=subtitle)
 
        smart_config = {
            "smooth_factor": float(payload.get("smart_smooth_factor") or 0.10),
            "deadzone_size": float(payload.get("smart_deadzone_size") or 0.15),
            "tracking_speed": int(payload.get("smart_tracking_speed") or 15),
            "relock_timeout": int(payload.get("smart_relock_timeout") or 150),
            "crop_padding": float(payload.get("smart_crop_padding") or 0.10)
        }

        # Read viral sensitivity and overlap threshold
        viral_sensitivity = payload.get("viral_sensitivity") or "medium"
        duplicate_mode = payload.get("duplicate_mode") or "strict"
        
        min_score = 0.20
        if viral_sensitivity == "high":
            min_score = 0.10
        elif viral_sensitivity == "extreme":
            min_score = 0.02
        elif viral_sensitivity == "low":
            min_score = 0.30
            
        overlap_threshold = 0.0
        if duplicate_mode == "moderate":
            overlap_threshold = 0.25
        elif duplicate_mode == "loose":
            overlap_threshold = 0.50
        elif duplicate_mode == "none":
            overlap_threshold = 1.0

        core.WHISPER_MODEL = whisper_model
        core.SUBTITLE_FONT = subtitle_font
        core.SUBTITLE_FONTS_DIR = subtitle_fontsdir
        core.SUBTITLE_LOCATION = subtitle_location
        with jobs_lock:
            core.PADDING = max(0, padding if padding is not None else 10)
            core.set_ratio_preset(ratio)
            out_w = core.OUT_WIDTH
            out_h = core.OUT_HEIGHT

        job_dir = "clips"
        os.makedirs(job_dir, exist_ok=True)

        core.cek_dependensi._args = SimpleNamespace(update_ytdlp=False)
        ok = core.cek_dependensi(install_whisper=subtitle, fatal=False)
        if not ok:
            raise RuntimeError("FFmpeg tidak ketemu")

        video_id = core.extract_video_id(url)
        if not video_id:
            raise ValueError("URL YouTube invalid")

        add_log(job_id, "Fetching video metadata and heatmap info...")
        meta = core.ambil_metadata_dan_heatmap(video_id, min_score=min_score, max_duration=max_duration)
        if meta:
            targets_heatmap = meta["heatmap"]
            total_duration = meta["duration"]
        else:
            targets_heatmap = core.ambil_most_replayed(video_id, min_score=min_score, max_duration=max_duration)
            total_duration = core.get_duration(video_id)

        targets = []
        picked = payload.get("segments")
        if isinstance(picked, list) and len(picked) > 0:
            add_log(job_id, f"Pakai {len(picked)} segment yang dipilih...")
            for seg in picked:
                try:
                    start = float(seg.get("start"))
                    dur = float(seg.get("duration"))
                    score = float(seg.get("score", 1.0))
                except Exception:
                    continue
                if dur <= 0:
                    continue
                targets.append({"start": start, "duration": dur, "score": score})
            if not targets:
                raise ValueError("Segment pilihan invalid")
            targets = core.select_non_overlapping(targets, len(targets), padding, overlap_threshold=overlap_threshold)
        elif mode == "custom":
            custom_segs = payload.get("custom_segments")
            if isinstance(custom_segs, list) and len(custom_segs) > 0:
                for seg in custom_segs:
                    start_s = parse_time_to_seconds(seg.get("start"))
                    end_s = parse_time_to_seconds(seg.get("end"))
                    if start_s is not None and end_s is not None:
                        if end_s <= start_s:
                            raise ValueError(f"End ({seg.get('end')}) harus lebih besar dari Start ({seg.get('start')})")
                        targets.append({"start": float(start_s), "duration": float(end_s - start_s), "score": 1.0})
                if not targets:
                    raise ValueError("Manual timestamp tidak ada yang valid")
            else:
                start_s = parse_time_to_seconds(payload.get("start"))
                end_s = parse_time_to_seconds(payload.get("end"))
                if start_s is None or end_s is None:
                    raise ValueError("Start/End belum diisi")
                if end_s <= start_s:
                    raise ValueError("End harus lebih besar dari Start")
                targets = [{"start": float(start_s), "duration": float(end_s - start_s), "score": 1.0}]
        else:
            if not targets_heatmap:
                add_log(job_id, "⚠️ Video tidak memiliki data interaksi (heatmap) dari YouTube. Membuat segmen default secara merata...")
                total_duration_val = total_duration or 600
                start_margin = total_duration_val * 0.10
                end_margin = total_duration_val * 0.90
                available_dur = end_margin - start_margin
                num_clips = max(1, max_clips or 10)
                segment_len = float(max_duration or 30)
                
                if available_dur > segment_len * num_clips:
                    step = (available_dur - segment_len) / (num_clips - 1) if num_clips > 1 else available_dur
                    for i in range(num_clips):
                        t_start = start_margin + i * step
                        targets.append({"start": t_start, "duration": segment_len, "score": 0.5})
                else:
                    step = available_dur / num_clips
                    for i in range(num_clips):
                        t_start = start_margin + i * step
                        targets.append({"start": t_start, "duration": min(step, segment_len), "score": 0.5})
            else:
                targets = core.select_non_overlapping(targets_heatmap, max(1, max_clips or 10), padding, overlap_threshold=overlap_threshold)

        set_job(job_id, total=len(targets), done=0, status_text="processing")

        local_video_path = os.path.join(job_dir, f"temp_full_{job_id}_{video_id}.mkv")
        add_log(job_id, "Downloading full video locally (unthrottled)...")
        if core.unduh_video_penuh(video_id, local_video_path):
            add_log(job_id, "✅ Full video downloaded successfully.")
        else:
            add_log(job_id, "⚠️  Failed to download full video. Falling back to direct streaming URL extraction...")
            local_video_path = None

        stream_urls = None
        if not local_video_path:
            add_log(job_id, "Fetching direct stream URLs for fast-seek downloading...")
            stream_urls = core.ambil_stream_urls(video_id)

        def event_hook(kind, data):
            if kind != "stage" or not isinstance(data, dict):
                return
            stage = data.get("stage") or ""
            clip_index = safe_int(data.get("clip_index"), 0) or 0
            set_job(job_id, stage=stage, stage_at=now_ms(), stage_clip=clip_index)

        # Process clips in parallel using ThreadPoolExecutor
        # Dynamically set worker count based on system threads for maximum parallel performance
        import multiprocessing
        try:
            total_cores = multiprocessing.cpu_count()
            if total_cores >= 12:
                workers = 3
            elif total_cores >= 8:
                workers = 2
            else:
                workers = 1
            core.CPU_THREADS = max(1, min(4, total_cores // workers))
        except Exception:
            workers = 2
            core.CPU_THREADS = 2

        success = 0
        import concurrent.futures
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {}
                for idx, item in enumerate(targets, start=1):
                    f = executor.submit(
                        core.proses_satu_clip,
                        video_id,
                        item,
                        idx,
                        total_duration,
                        crop,
                        subtitle,
                        event_hook=event_hook,
                        stream_urls=stream_urls,
                        local_video_path=local_video_path,
                        subtitle_lang=subtitle_lang,
                        output_ratio=ratio,
                        out_w=out_w,
                        out_h=out_h,
                        output_dir=job_dir,
                        job_id=job_id,
                        smart_config=smart_config,
                        subtitle_style=subtitle_style,
                        max_duration=max_duration
                    )
                    futures[f] = idx

                done_count = 0
                for f in concurrent.futures.as_completed(futures):
                    idx = futures[f]
                    ok = f.result()
                    done_count += 1
                    if ok:
                        success += 1
                    set_job(job_id, done=done_count, success=success, outputs=list_outputs(job_dir, job_id))
        finally:
            if local_video_path and os.path.exists(local_video_path):
                add_log(job_id, "Cleaning up temporary full video file...")
                try:
                    os.remove(local_video_path)
                except Exception:
                    pass

        set_job(job_id, status="done", finished_at=now_ms(), outputs=list_outputs(job_dir, job_id))
    except Exception as e:
        set_job(job_id, status="error", error=str(e), finished_at=now_ms())


@app.get("/")
def index():
    return render_template("index.html")

@app.get("/assets/fonts/<path:filename>")
def serve_font(filename):
    return send_from_directory("fonts", filename, as_attachment=False)


def get_preview(url):
    key = url.strip()
    if not key:
        raise ValueError("URL kosong")

    with preview_lock:
        cached = preview_cache.get(key)
        if cached:
            return cached

    cmd = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--skip-download",
        "-J",
        key,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError((res.stderr or res.stdout or "Gagal ambil metadata").strip())

    raw = json.loads(res.stdout)
    item = raw["entries"][0] if isinstance(raw, dict) and "entries" in raw and raw.get("entries") else raw

    preview = {
        "title": item.get("title"),
        "thumbnail": item.get("thumbnail"),
        "uploader": item.get("uploader"),
        "duration": item.get("duration"),
        "webpage_url": item.get("webpage_url") or key,
        "id": item.get("id"),
    }

    with preview_lock:
        preview_cache[key] = preview
        if len(preview_cache) > 200:
            preview_cache.clear()

    return preview


@app.post("/api/preview")
def api_preview():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    try:
        preview = get_preview(url)
        return jsonify({"ok": True, "preview": preview})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/api/scan")
def api_scan():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    padding = safe_int(data.get("padding"), 10)
    max_duration = safe_int(data.get("max_duration"), 60)
    
    viral_sensitivity = data.get("viral_sensitivity") or "medium"
    duplicate_mode = data.get("duplicate_mode") or "strict"
    
    min_score = 0.20
    if viral_sensitivity == "high":
        min_score = 0.10
    elif viral_sensitivity == "extreme":
        min_score = 0.02
    elif viral_sensitivity == "low":
        min_score = 0.30
        
    overlap_threshold = 0.0
    if duplicate_mode == "moderate":
        overlap_threshold = 0.25
    elif duplicate_mode == "loose":
        overlap_threshold = 0.50
    elif duplicate_mode == "none":
        overlap_threshold = 1.0

    video_id = core.extract_video_id(url)
    if not video_id:
        return jsonify({"ok": False, "error": "URL YouTube invalid"}), 400

    core.cek_dependensi._args = SimpleNamespace(no_update_ytdlp=True)
    ok = core.cek_dependensi(install_whisper=False, fatal=False)
    if not ok:
        return jsonify({"ok": False, "error": "FFmpeg tidak ketemu"}), 400

    segments = core.ambil_most_replayed(video_id, min_score=min_score, max_duration=max_duration)
    segments = core.select_non_overlapping(segments, 100, padding, overlap_threshold=overlap_threshold)
    total = core.get_duration(video_id) or 600

    if not segments:
        # Generate default segments evenly spaced
        start_margin = total * 0.10
        end_margin = total * 0.90
        available_dur = end_margin - start_margin
        num_clips = 5  # default to 5 clips on scan
        segment_len = float(max_duration or 30)
        
        if available_dur > segment_len * num_clips:
            step = (available_dur - segment_len) / (num_clips - 1) if num_clips > 1 else available_dur
            for i in range(num_clips):
                t_start = start_margin + i * step
                segments.append({"start": t_start, "duration": segment_len, "score": 0.5})
        else:
            step = available_dur / num_clips
            for i in range(num_clips):
                t_start = start_margin + i * step
                segments.append({"start": t_start, "duration": min(step, segment_len), "score": 0.5})

    segments.sort(key=lambda x: float(x.get("start", 0)))
    return jsonify({"ok": True, "video_id": video_id, "duration": total, "segments": segments})


@app.post("/api/clip")
def api_clip():
    payload = request.get_json(silent=True) or {}
    job_id = uuid.uuid4().hex[:12]
    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "created_at": now_ms(),
            "started_at": None,
            "finished_at": None,
            "error": None,
            "total": 0,
            "done": 0,
            "success": 0,
            "current": 0,
            "status_text": "",
            "stage": "",
            "stage_at": None,
            "stage_clip": 0,
            "subtitle_enabled": False,
            "outputs": [],
            "logs": [],
        }

    t = threading.Thread(target=run_job, args=(job_id, payload), daemon=True)
    t.start()
    return jsonify({"ok": True, "job_id": job_id})


@app.get("/api/job/<job_id>")
def api_job(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"ok": False, "error": "Job not found"}), 404
        return jsonify({"ok": True, "job": job})


@app.get("/clips/<job_id>/<path:filename>")
def serve_clip(job_id, filename):
    return send_from_directory("clips", filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

