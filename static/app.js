const $ = (id) => document.getElementById(id);

const I18N = {
  id: {
    "top.tagline": "Scan Most Replayed, potong otomatis, subtitle rapi.",
    "label.url": "YouTube URL",
    "ph.url": "https://www.youtube.com/watch?v=...",
    "help.url": "Tempel link video/shorts. Nanti keluar preview.",
    "label.mode": "Mode",
    "opt.mode.heatmap": "Scan heatmap (Most Replayed)",
    "opt.mode.custom": "Custom start/end (manual)",
    "help.mode": "Scan = cari momen paling rame. Custom = potong dari waktu yang kamu tentuin.",
    "label.ratio": "Ratio",
    "opt.ratio.9_16": "9:16 (Shorts)",
    "opt.ratio.original": "Original",
    "help.ratio": "Pilih bentuk output video. 9:16 buat Shorts/Reels/TikTok.",
    "label.crop": "Crop",
    "opt.crop.default": "Default",
    "opt.crop.split_left": "Split Left",
    "opt.crop.split_right": "Split Right",
    "opt.crop.smart": "Smart Crop (Face Tracking)",
    "help.crop": "Split itu buat gaming: atas gameplay, bawah facecam. Smart Crop buat track wajah otomatis.",
    "label.smart_tracking_strategy": "Strategi Tracking",
    "opt.smart_tracking_strategy.hybrid": "Hybrid / Presenter (Direkomendasikan)",
    "opt.smart_tracking_strategy.center": "Hanya Wajah Tengah",
    "opt.smart_tracking_strategy.largest": "Hanya Wajah Terbesar",
    "help.smart_tracking_strategy": "Strategi memilih wajah jika ada banyak orang di video.",
    "label.max_duration": "Durasi Maksimal Clip",
    "opt.max_duration.none": "Bebas (Tanpa Batas)",
    "help.max_duration": "Membatasi durasi maksimal tiap potongan video clip.",
    "label.padding": "Padding (detik)",
    "help.padding": "Nambah detik sebelum & sesudah momen biar nggak “kepotong nanggung”.",
    "label.max_clips": "Max clips",
    "help.max_clips": "Berapa potongan yang mau dihasilkan dari heatmap.",
    "label.subtitle": "Subtitle",
    "opt.no": "No",
    "opt.yes": "Yes",
    "help.subtitle": "Kalau Yes, audio ditranskrip jadi teks lalu dibakar ke video.",
    "label.whisper_model": "Model (Whisper)",
    "help.whisper_model": "Ini model AI buat transkripsi suara ke teks. Makin besar makin akurat, makin berat.",
    "label.subtitle_font": "Font Subtitle",
    "opt.custom": "Custom…",
    "ph.subtitle_font_custom": "Nama font custom (mis. Poppins)",
    "help.subtitle_font": "Kalau font-nya ada di folder fonts, isi Fonts dir = fonts.",
    "label.subtitle_location": "Subtitle Location",
    "opt.subtitle_location.bottom": "Bottom",
    "opt.subtitle_location.center": "Centered",
    "help.subtitle_location": "Bottom = lebih natural buat Shorts. Centered = lebih “in your face”.",
    "label.subtitle_style": "Gaya Subtitle / Timing",
    "opt.subtitle_style.sentence": "Kalimat Penuh (Standard)",
    "opt.subtitle_style.word_by_word": "Per Kata (Word by Word)",
    "opt.subtitle_style.phrase_by_phrase": "Per Frasa (Phrase by Phrase)",
    "opt.subtitle_style.karaoke": "Karaoke / Sorot Kata",
    "opt.subtitle_style.line_by_line": "1-2 Baris (Line by Line)",
    "help.subtitle_style": "Pilih timing dan gaya pemotongan teks subtitle di video.",
    "label.subtitle_lang": "Bahasa Subtitle",
    "opt.subtitle_lang.id": "Indonesia",
    "opt.subtitle_lang.en": "Inggris",
    "help.subtitle_lang": "Pilih bahasa audio asal untuk hasil transkripsi subtitle terbaik.",
    "label.subtitle_fontsdir": "Fonts dir (opsional)",
    "help.subtitle_fontsdir": "Folder berisi file .ttf/.otf buat subtitle. Default: folder project <b>fonts</b>.",
    "label.start": "Start (detik atau mm:ss)",
    "ph.start": "689 atau 11:29",
    "label.end": "End (detik atau mm:ss)",
    "ph.end": "742 atau 12:22",
    "btn.scan": "Scan Heatmap",
    "btn.clip": "Buat Clip",
    "help.actions": "Scan Heatmap = ambil daftar momen “Most Replayed”. Buat Clip = download + crop + (opsional) subtitle.",
    "panel.segments": "Segments",
    "btn.select_all": "Select All",
    "btn.clear": "Clear",
    "btn.create_selected": "Create Selected Clip",
    "panel.progress": "Progress",
    "js.modal.preview_segment": "Preview Segment",
    "js.modal.preview_clip": "Preview Clip",
    "js.segments.empty": "Belum ada segment. Klik Scan Heatmap dulu.",
    "js.preview.loading": "Loading preview…",
    "js.progress.count": "{done}/{total} selesai • {success} sukses",
    "js.selected.count": "{count} dipilih",
    "js.stage.download": "Download",
    "js.stage.crop": "Crop",
    "js.stage.subtitle": "Subtitle",
    "js.stage.subtitle_model_load": "Load model",
    "js.stage.subtitle_transcribe": "Transcribe",
    "js.stage.subtitle_write": "Tulis subtitle",
    "js.stage.burn_subtitle": "Burn subtitle",
    "js.stage.finalize": "Finalize",
    "js.stage.done_clip": "Selesai",
    "js.topprogress.processing": "Processing",
  },
  en: {
    "top.tagline": "Scan Most Replayed, auto cut, clean subtitles.",
    "label.url": "YouTube URL",
    "ph.url": "https://www.youtube.com/watch?v=...",
    "help.url": "Paste a video/shorts link. Preview will show up.",
    "label.mode": "Mode",
    "opt.mode.heatmap": "Scan heatmap (Most Replayed)",
    "opt.mode.custom": "Custom start/end (manual)",
    "help.mode": "Scan = find the hottest moments. Custom = cut by your timestamps.",
    "label.ratio": "Ratio",
    "opt.ratio.9_16": "9:16 (Shorts)",
    "opt.ratio.original": "Original",
    "help.ratio": "Choose output aspect ratio. 9:16 is for Shorts/Reels/TikTok.",
    "label.crop": "Crop",
    "opt.crop.default": "Default",
    "opt.crop.split_left": "Split Left",
    "opt.crop.split_right": "Split Right",
    "opt.crop.smart": "Smart Crop (Face Tracking)",
    "help.crop": "Split is for gaming: gameplay on top, facecam below. Smart Crop tracks the main speaker automatically.",
    "label.smart_tracking_strategy": "Tracking Strategy",
    "opt.smart_tracking_strategy.hybrid": "Hybrid / Presenter (Recommended)",
    "opt.smart_tracking_strategy.center": "Center Face Only",
    "opt.smart_tracking_strategy.largest": "Largest Face Only",
    "help.smart_tracking_strategy": "Strategy for choosing a face when there are multiple people.",
    "label.max_duration": "Max Clip Duration",
    "opt.max_duration.none": "No Limit",
    "help.max_duration": "Caps the maximum duration of each generated video clip.",
    "label.padding": "Padding (seconds)",
    "help.padding": "Adds seconds before & after, so it doesn’t cut awkwardly.",
    "label.max_clips": "Max clips",
    "help.max_clips": "How many clips to generate from the heatmap.",
    "label.subtitle": "Subtitle",
    "opt.no": "No",
    "opt.yes": "Yes",
    "help.subtitle": "If Yes, audio is transcribed to text and burned into the video.",
    "label.whisper_model": "Model (Whisper)",
    "help.whisper_model": "AI model for speech-to-text. Bigger = more accurate, heavier.",
    "label.subtitle_font": "Subtitle Font",
    "opt.custom": "Custom…",
    "ph.subtitle_font_custom": "Custom font name (e.g. Poppins)",
    "help.subtitle_font": "If the font is in fonts folder, set Fonts dir = fonts.",
    "label.subtitle_location": "Subtitle Location",
    "opt.subtitle_location.bottom": "Bottom",
    "opt.subtitle_location.center": "Centered",
    "help.subtitle_location": "Bottom looks natural for Shorts. Centered is more “in your face”.",
    "label.subtitle_style": "Subtitle Style / Timing",
    "opt.subtitle_style.sentence": "Full Sentence (Standard)",
    "opt.subtitle_style.word_by_word": "Word by Word",
    "opt.subtitle_style.phrase_by_phrase": "Phrase by Phrase",
    "opt.subtitle_style.karaoke": "Karaoke / Highlight Active Word",
    "opt.subtitle_style.line_by_line": "Line by Line (1-2 lines)",
    "help.subtitle_style": "Choose subtitle timing and display format for the video.",
    "label.subtitle_lang": "Subtitle Language",
    "opt.subtitle_lang.id": "Indonesian",
    "opt.subtitle_lang.en": "English",
    "help.subtitle_lang": "Choose source audio language for the best transcription accuracy.",
    "label.subtitle_fontsdir": "Fonts dir (optional)",
    "help.subtitle_fontsdir": "Folder containing .ttf/.otf for subtitles. Default: project <b>fonts</b> folder.",
    "label.start": "Start (seconds or mm:ss)",
    "ph.start": "689 or 11:29",
    "label.end": "End (seconds or mm:ss)",
    "ph.end": "742 or 12:22",
    "btn.scan": "Scan Heatmap",
    "btn.clip": "Create Clip",
    "help.actions": "Scan Heatmap = fetch “Most Replayed” moments. Create Clip = download + crop + (optional) subtitles.",
    "panel.segments": "Segments",
    "btn.select_all": "Select All",
    "btn.clear": "Clear",
    "btn.create_selected": "Create Selected Clip",
    "panel.progress": "Progress",
    "js.modal.preview_segment": "Preview Segment",
    "js.modal.preview_clip": "Preview Clip",
    "js.segments.empty": "No segments yet. Click Scan Heatmap first.",
    "js.preview.loading": "Loading preview…",
    "js.progress.count": "{done}/{total} done • {success} success",
    "js.selected.count": "{count} selected",
    "js.stage.download": "Download",
    "js.stage.crop": "Crop",
    "js.stage.subtitle": "Subtitle",
    "js.stage.subtitle_model_load": "Load model",
    "js.stage.subtitle_transcribe": "Transcribe",
    "js.stage.subtitle_write": "Write subtitles",
    "js.stage.burn_subtitle": "Burn subtitles",
    "js.stage.finalize": "Finalize",
    "js.stage.done_clip": "Done",
    "js.topprogress.processing": "Processing",
  },
};

let currentLang = "id";

function t(key, vars) {
  const base = I18N[currentLang] || I18N.id;
  const fallback = I18N.id || {};
  let s = base[key] ?? fallback[key] ?? key;
  if (vars && typeof s === "string") {
    Object.entries(vars).forEach(([k, v]) => {
      s = s.replaceAll(`{${k}}`, String(v));
    });
  }
  return s;
}

const TOP_PROGRESS = {
  pct: 0,
  titleBase: document.title || "YouTube Heatmap Clipper",
  hideTimer: null,
};

function clamp(n, a, b) {
  return Math.min(b, Math.max(a, n));
}

function easeOutCubic(x) {
  const t = clamp(x, 0, 1);
  return 1 - Math.pow(1 - t, 3);
}

function stageLabel(stage) {
  const key = {
    download: "js.stage.download",
    crop: "js.stage.crop",
    subtitle: "js.stage.subtitle",
    subtitle_model_load: "js.stage.subtitle_model_load",
    subtitle_transcribe: "js.stage.subtitle_transcribe",
    subtitle_write: "js.stage.subtitle_write",
    burn_subtitle: "js.stage.burn_subtitle",
    finalize: "js.stage.finalize",
    done_clip: "js.stage.done_clip",
  }[stage];
  return key ? t(key) : stage || "";
}

function computeJobPct(job) {
  if (!job) return { pct: 0, text: "", active: false };
  const status = job.status || "";
  if (status !== "running" && status !== "queued") {
    const done = Number(job.done || 0);
    const total = Number(job.total || 0);
    const pct = total > 0 ? clamp((done / total) * 100, 0, 100) : 0;
    return { pct, text: "", active: false };
  }

  const total = Math.max(1, Number(job.total || 1));
  const done = clamp(Number(job.done || 0), 0, total);
  const subtitleEnabled = Boolean(job.subtitle_enabled);
  const stage = job.stage || "";
  const stageAt = job.stage_at ? Number(job.stage_at) : 0;
  const elapsed = stageAt ? Date.now() - stageAt : 0;
  const clipIndexRaw = Number(job.stage_clip || job.current || (done + 1) || 1);
  const clipIndex = clamp(clipIndexRaw, 1, total);

  const mapNoSub = {
    download: { a: 0.04, b: 0.62, d: 14000 },
    crop: { a: 0.62, b: 0.96, d: 9000 },
    finalize: { a: 0.96, b: 0.995, d: 2500 },
    done_clip: { a: 1, b: 1, d: 0 },
  };
  const mapSub = {
    download: { a: 0.03, b: 0.55, d: 14000 },
    crop: { a: 0.55, b: 0.86, d: 9000 },
    subtitle: { a: 0.86, b: 0.87, d: 1200 },
    subtitle_model_load: { a: 0.87, b: 0.885, d: 2500 },
    subtitle_transcribe: { a: 0.885, b: 0.93, d: 20000 },
    subtitle_write: { a: 0.93, b: 0.94, d: 1800 },
    burn_subtitle: { a: 0.94, b: 0.985, d: 12000 },
    finalize: { a: 0.985, b: 0.995, d: 2500 },
    done_clip: { a: 1, b: 1, d: 0 },
  };

  const table = subtitleEnabled ? mapSub : mapNoSub;
  const s = table[stage] || (subtitleEnabled ? mapSub.download : mapNoSub.download);
  const within = s.d > 0 ? s.a + (s.b - s.a) * easeOutCubic(clamp(elapsed / s.d, 0, 0.98)) : s.a;
  const pctBase = ((clipIndex - 1) + within) / total * 100;
  const pctFloor = (done / total) * 100;
  const pct = clamp(Math.max(pctBase, pctFloor), 0, 99.5);

  const clipText = total > 0 ? `clip ${clipIndex}/${total}` : "";
  const sLabel = stageLabel(stage);
  const text = [t("js.topprogress.processing"), clipText, sLabel].filter(Boolean).join(" • ");
  return { pct, text, active: true };
}

function renderTopProgress(job) {
  const wrap = $("topProgressWrap");
  const bar = $("topProgressBar");
  const textEl = $("topProgressText");
  if (!wrap || !bar || !textEl) return;

  const { pct, text, active } = computeJobPct(job);

  if (!active) {
    if (job && (job.status === "done" || job.status === "error")) {
      bar.style.width = "100%";
      textEl.textContent = job.status === "error" ? "Error" : "";
      wrap.classList.remove("hide");
      clearTimeout(TOP_PROGRESS.hideTimer);
      TOP_PROGRESS.hideTimer = setTimeout(() => {
        wrap.classList.add("hide");
        bar.style.width = "0%";
        textEl.textContent = "";
      }, 650);
      document.title = TOP_PROGRESS.titleBase;
      TOP_PROGRESS.pct = 0;
      return;
    }
    wrap.classList.add("hide");
    bar.style.width = "0%";
    textEl.textContent = "";
    document.title = TOP_PROGRESS.titleBase;
    TOP_PROGRESS.pct = 0;
    return;
  }

  clearTimeout(TOP_PROGRESS.hideTimer);
  wrap.classList.remove("hide");
  TOP_PROGRESS.pct = Math.max(TOP_PROGRESS.pct, pct);
  bar.style.width = `${TOP_PROGRESS.pct.toFixed(1)}%`;
  textEl.textContent = text;
  document.title = `${TOP_PROGRESS.titleBase} (${Math.round(TOP_PROGRESS.pct)}%)`;
}

function applyI18n() {
  document.documentElement.lang = currentLang;
  $("langId")?.classList.toggle("isActive", currentLang === "id");
  $("langEn")?.classList.toggle("isActive", currentLang === "en");

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    if (!key) return;
    el.innerHTML = t(key);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.dataset.i18nPlaceholder;
    if (!key) return;
    el.setAttribute("placeholder", t(key));
  });
}

function setLang(lang) {
  currentLang = lang === "en" ? "en" : "id";
  localStorage.setItem("lang", currentLang);
  applyI18n();
  renderSegments(lastScanSegments);
  updateSelectedUi();
}

function fmtTime(s) {
  const sec = Math.max(0, Math.floor(Number(s) || 0));
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const r = sec % 60;
  if (h > 0) return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(r).padStart(2, "0")}`;
  return `${String(m).padStart(2, "0")}:${String(r).padStart(2, "0")}`;
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.ok === false) {
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return data;
}

function openModal(title, bodyEl) {
  $("modalTitle").textContent = title || "";
  const root = $("modalBody");
  root.innerHTML = "";
  root.appendChild(bodyEl);
  $("modal").classList.remove("hide");
}

function closeModal() {
  $("modal").classList.add("hide");
  $("modalBody").innerHTML = "";
}

function debounce(fn, wait) {
  let t = null;
  return (...args) => {
    if (t) clearTimeout(t);
    t = setTimeout(() => fn(...args), wait);
  };
}

function readPayload() {
  const fontSel = $("subtitle_font_select").value;
  const fontCustom = ($("subtitle_font_custom").value || "").trim();
  const subtitleFont = fontSel === "custom" ? fontCustom : fontSel;
  const customSegments = [];
  if ($("mode").value === "custom") {
    const container = $("manualClipsContainer");
    if (container) {
      container.querySelectorAll(".manual-clip-row").forEach(row => {
        const startIn = row.querySelector(".manual-start");
        const endIn = row.querySelector(".manual-end");
        const startVal = startIn ? (startIn.value || "").trim() : "";
        const endVal = endIn ? (endIn.value || "").trim() : "";
        if (startVal && endVal) {
          customSegments.push({ start: startVal, end: endVal });
        }
      });
    }
  }
  return {
    url: $("url").value,
    mode: $("mode").value,
    ratio: $("ratio").value,
    crop: $("crop").value,
    padding: Number($("padding").value || 0),
    max_clips: Number($("max_clips").value || 6),
    max_duration: Number($("max_duration")?.value || 60),
    subtitle: $("subtitle").value === "y",
    whisper_model: $("whisper_model").value,
    subtitle_font: subtitleFont,
    subtitle_location: $("subtitle_location").value,
    subtitle_fontsdir: $("subtitle_fontsdir").value || "",
    subtitle_lang: $("subtitle_lang").value || "en",
    subtitle_style: $("subtitle_style").value,
    custom_segments: customSegments,
    smart_smooth_factor: Number($("smart_smooth_factor")?.value || 0.10),
    smart_deadzone_size: Number($("smart_deadzone_size")?.value || 0.15),
    smart_tracking_speed: Number($("smart_tracking_speed")?.value || 15),
    smart_relock_timeout: Number($("smart_relock_timeout")?.value || 30),
    smart_crop_padding: Number($("smart_crop_padding")?.value || 0.10),
    smart_tracking_strategy: $("smart_tracking_strategy")?.value || "hybrid",
    viral_sensitivity: $("viral_sensitivity")?.value || "medium",
    duplicate_mode: $("duplicate_mode")?.value || "strict"
  };
}

function setBusy(busy) {
  $("scanBtn").disabled = busy;
  $("clipBtn").disabled = busy;
  $("segSelectAllBtn").disabled = busy;
  $("segClearBtn").disabled = busy;
  $("segCreateBtn").disabled = busy || selectedKeys.size === 0;
}

function getVideoThumb(videoId, fallback) {
  if (!videoId) return fallback || "";
  return `https://i.ytimg.com/vi_webp/${videoId}/hqdefault.webp`;
}

function openYouTubePreview(videoId, startSec, endSec, title) {
  const start = Math.max(0, Math.floor(Number(startSec) || 0));
  const end = Math.max(0, Math.floor(Number(endSec) || 0));
  const url = `https://www.youtube.com/embed/${encodeURIComponent(videoId)}?start=${start}${end > start ? `&end=${end}` : ""}&autoplay=1&playsinline=1&rel=0`;
  const iframe = document.createElement("iframe");
  iframe.className = "embed";
  iframe.src = url;
  iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
  iframe.allowFullscreen = true;
  openModal(title || t("js.modal.preview_segment"), iframe);
}

function openClipPreview(title, src) {
  const v = document.createElement("video");
  v.className = "video";
  v.controls = true;
  v.autoplay = true;
  v.muted = true;
  v.playsInline = true;
  v.src = src;
  openModal(title || t("js.modal.preview_clip"), v);
}

function segKey(seg) {
  const start = Math.round(Number(seg.start || 0) * 1000);
  const dur = Math.round(Number(seg.duration || 0) * 1000);
  return `${start}:${dur}`;
}

function setSegControlsVisible(visible) {
  $("segControls").classList.toggle("hide", !visible);
}

function updateSelectedUi() {
  const count = selectedKeys.size;
  $("segSelectedMeta").textContent = count > 0 ? t("js.selected.count", { count }) : "";
  $("segCreateBtn").disabled = count === 0 || $("scanBtn").disabled;
  setSegControlsVisible($("mode").value === "heatmap" && lastScanSegments.length > 0);
}

function selectAllSegments() {
  selectedKeys = new Set(lastScanSegments.map(segKey));
  renderSegments(lastScanSegments);
  updateSelectedUi();
}

function clearSelectedSegments() {
  selectedKeys = new Set();
  renderSegments(lastScanSegments);
  updateSelectedUi();
}

async function clipSelected() {
  if ($("mode").value !== "heatmap") return;
  if (selectedKeys.size === 0) return;
  setBusy(true);
  try {
    const payload = readPayload();
    const picked = lastScanSegments.filter((s) => selectedKeys.has(segKey(s)));
    const data = await postJson("/api/clip", { ...payload, segments: picked });
    const jobId = data.job_id;
    await pollJob(jobId);
  } catch (e) {
    renderProgress({ status: "error", error: e.message, total: 0, done: 0, id: "" });
  } finally {
    setBusy(false);
    updateSelectedUi();
  }
}

function renderSegments(segments) {
  const root = $("segments");
  root.innerHTML = "";
  if (!segments || segments.length === 0) {
    root.innerHTML = `<div class="small">${t("js.segments.empty")}</div>`;
    updateSelectedUi();
    return;
  }
  segments.forEach((s, idx) => {
    const start = Number(s.start || 0);
    const dur = Number(s.duration || 0);
    const end = start + dur;
    const score = Number(s.score || 0);
    const virality = s.virality || { score: Math.min(99, Math.round(score * 90) || 75), hook: 80, retention: 80, trend: "A" };
    const trendGrade = virality.trend || "A";
    const trendClass = `grade-${trendGrade.replace("+", "plus").replace("-", "minus")}`;

    const el = document.createElement("div");
    el.className = "seg";
    const key = segKey(s);
    if (selectedKeys.has(key)) el.classList.add("selected");
    const thumb = getVideoThumb(currentVideoId, currentPreview?.thumbnail);
    el.innerHTML = `
      <div class="segThumb">
        <img alt="" src="${thumb}" />
        <div class="segTime">${fmtTime(start)}</div>
      </div>
      <div class="segMain">
        <div class="t">#${idx + 1} ${fmtTime(start)} → ${fmtTime(end)}</div>
        <div class="m">durasi ${Math.round(dur)}s • <span class="viralitySub">Hook: ${virality.hook} | Retention: ${virality.retention}</span></div>
      </div>
      <div class="segSide">
        <div class="viralityCard" title="Score: ${virality.score} | Hook: ${virality.hook} | Retention: ${virality.retention}">
          <span class="trendBadge ${trendClass}">${trendGrade}</span>
        </div>
        <button class="btn ghost smallBtn" type="button" data-preview="1">Preview</button>
      </div>
    `;
    el.addEventListener("click", (ev) => {
      const target = ev.target;
      if (target && target.dataset && target.dataset.preview) {
        ev.preventDefault();
        ev.stopPropagation();
        if (currentVideoId) openYouTubePreview(currentVideoId, start, end, currentPreview?.title || "Preview Segment");
        return;
      }
      if ($("mode").value === "custom") {
        const container = $("manualClipsContainer");
        if (container) {
          const rows = container.querySelectorAll(".manual-clip-row");
          let populated = false;
          for (let row of rows) {
            const startIn = row.querySelector(".manual-start");
            const endIn = row.querySelector(".manual-end");
            if (startIn && endIn && !startIn.value && !endIn.value) {
              startIn.value = Math.floor(start);
              endIn.value = Math.floor(end);
              populated = true;
              break;
            }
          }
          if (!populated) {
            const newCount = rows.length + 1;
            $("manual_clips_count").value = newCount;
            renderManualClipRows();
            const newRows = container.querySelectorAll(".manual-clip-row");
            const lastRow = newRows[newRows.length - 1];
            if (lastRow) {
              const startIn = lastRow.querySelector(".manual-start");
              const endIn = lastRow.querySelector(".manual-end");
              if (startIn && endIn) {
                startIn.value = Math.floor(start);
                endIn.value = Math.floor(end);
              }
            }
          }
        }
        return;
      }
      if (selectedKeys.has(key)) selectedKeys.delete(key);
      else selectedKeys.add(key);
      el.classList.toggle("selected");
      updateSelectedUi();
    });
    root.appendChild(el);
  });
  updateSelectedUi();
}

function renderProgress(job) {
  const root = $("progress");
  const meta = $("jobMeta");
  const out = $("outputs");
  root.innerHTML = "";
  out.innerHTML = "";
  meta.textContent = "";
  if (!job) return;
  renderTopProgress(job);
  const total = Number(job.total || 0);
  const done = Number(job.done || 0);
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  const stage = stageLabel(job.stage || "");
  meta.textContent = `${job.status} • ${(job.status_text || "").trim()}${stage ? " • " + stage : ""}`.trim();

  const bar = document.createElement("div");
  bar.innerHTML = `<div class="bar"><div class="fill" style="width:${pct}%"></div><div class="pct">${pct}%</div></div>`;
  root.appendChild(bar);

  const line = document.createElement("div");
  line.className = "small";
  line.textContent =
    total > 0
      ? t("js.progress.count", { done, total, success: job.success || 0 })
      : "";
  root.appendChild(line);

  if (job.status === "error") {
    const err = document.createElement("div");
    err.className = "small";
    err.textContent = job.error || "error";
    root.appendChild(err);
  }

  if (Array.isArray(job.outputs) && job.outputs.length > 0) {
    job.outputs.forEach((f) => {
      const el = document.createElement("div");
      el.className = "out";
      const href = `/clips/${job.id}/${encodeURIComponent(f.name)}`;
      const v = f.virality;
      const vMeta = v ? `<span class="trendBadge ${`grade-${v.trend.replace("+", "plus").replace("-", "minus")}`}">${v.trend}</span>` : "";
      el.innerHTML = `
        <div class="outLeft">
          <a href="${href}" target="_blank" rel="noreferrer">${f.name}</a>
          <div class="small">${Math.round((f.size || 0) / 1024)} KB ${vMeta ? "• " + vMeta : ""}</div>
        </div>
        <div class="outRight">
          <button class="btn ghost smallBtn" type="button" data-play="1">Play</button>
          <a class="btn smallBtn" href="${href}" download>Download</a>
        </div>
      `;
      el.querySelector("[data-play]")?.addEventListener("click", (ev) => {
        ev.preventDefault();
        openClipPreview(f.name, href);
      });
      out.appendChild(el);
    });
  }
}

let lastScanSegments = [];
let lastPreviewUrl = "";
let currentPreview = null;
let currentVideoId = "";
let selectedKeys = new Set();

async function scan() {
  setBusy(true);
  try {
    const payload = readPayload();
    const data = await postJson("/api/scan", {
      url: payload.url,
      padding: payload.padding,
      viral_sensitivity: payload.viral_sensitivity,
      duplicate_mode: payload.duplicate_mode,
      max_duration: payload.max_duration
    });
    lastScanSegments = data.segments || [];
    selectedKeys = new Set();
    currentVideoId = data.video_id || currentVideoId;
    $("segMeta").textContent = `${lastScanSegments.length} segments • durasi ~${fmtTime(data.duration || 0)}`;
    renderSegments(lastScanSegments);
  } catch (e) {
    $("segMeta").textContent = e.message;
    renderSegments([]);
  } finally {
    setBusy(false);
    updateSelectedUi();
  }
}

async function preview() {
  const url = $("url").value.trim();
  if (!url || url === lastPreviewUrl) return;
  lastPreviewUrl = url;
  const box = $("preview");
  const title = $("pvTitle");
  const sub = $("pvSub");
  const img = $("thumbImg");
  try {
    title.textContent = t("js.preview.loading");
    sub.textContent = "";
    img.removeAttribute("src");
    box.classList.remove("hide");
    const data = await postJson("/api/preview", { url });
    const p = data.preview || {};
    currentPreview = p;
    if (p.id) currentVideoId = p.id;
    title.textContent = p.title || "Untitled";
    const dur = p.duration != null ? fmtTime(p.duration) : "";
    const uploader = p.uploader || "";
    sub.textContent = [uploader, dur].filter(Boolean).join(" • ");
    if (p.thumbnail) img.src = p.thumbnail;
  } catch (e) {
    box.classList.add("hide");
  }
}

async function clip() {
  setBusy(true);
  try {
    const payload = readPayload();
    const data = await postJson("/api/clip", payload);
    const jobId = data.job_id;
    await pollJob(jobId);
  } catch (e) {
    renderProgress({ status: "error", error: e.message, total: 0, done: 0, id: "" });
  } finally {
    setBusy(false);
  }
}

async function pollJob(jobId) {
  const started = Date.now();
  while (true) {
    const res = await fetch(`/api/job/${jobId}`);
    const data = await res.json().catch(() => null);
    if (!data || !data.ok) throw new Error("Job not found");
    renderProgress(data.job);
    if (data.job.status === "done" || data.job.status === "error") return;
    if (Date.now() - started > 1000 * 60 * 30) throw new Error("Timeout");
    await new Promise((r) => setTimeout(r, 1500));
  }
}

function renderManualClipRows() {
  const container = $("manualClipsContainer");
  if (!container) return;
  const countInput = $("manual_clips_count");
  if (!countInput) return;
  const count = Math.max(1, parseInt(countInput.value) || 1);
  
  // Store existing values to preserve them
  const existingValues = [];
  container.querySelectorAll(".manual-clip-row").forEach(row => {
    const sInput = row.querySelector(".manual-start");
    const eInput = row.querySelector(".manual-end");
    existingValues.push({
      start: sInput ? sInput.value : "",
      end: eInput ? eInput.value : ""
    });
  });
  
  container.innerHTML = "";
  for (let i = 1; i <= count; i++) {
    const row = document.createElement("div");
    row.className = "manual-clip-row grid2";
    row.style.marginBottom = "8px";
    row.style.gap = "12px";
    
    const startVal = existingValues[i - 1]?.start || "";
    const endVal = existingValues[i - 1]?.end || "";
    
    row.innerHTML = `
      <div class="row">
        <label class="label">Clip #${i} Start</label>
        <input class="input manual-start" value="${startVal}" placeholder="689 atau 11:29" />
      </div>
      <div class="row">
        <label class="label">Clip #${i} End</label>
        <input class="input manual-end" value="${endVal}" placeholder="742 atau 12:22" />
      </div>
    `;
    container.appendChild(row);
  }
}

function toggleMode() {
  const isCustom = $("mode").value === "custom";
  $("customBox").classList.toggle("hide", !isCustom);
  $("scanBtn").classList.toggle("hide", isCustom);
  $("heatmapSettingsBox")?.classList.toggle("hide", isCustom);
  if (isCustom) {
    setSegControlsVisible(false);
    $("segSelectedMeta").textContent = "";
  } else {
    setSegControlsVisible(lastScanSegments.length > 0);
    updateSelectedUi();
  }
}

function toggleFont() {
  const isCustom = $("subtitle_font_select").value === "custom";
  $("subtitle_font_custom").classList.toggle("hide", !isCustom);
}

function toggleSmartCropBox() {
  const isSmart = $("crop").value === "smart";
  $("smartCropBox")?.classList.toggle("hide", !isSmart);
}

$("mode").addEventListener("change", toggleMode);
$("subtitle_font_select").addEventListener("change", toggleFont);
$("crop").addEventListener("change", toggleSmartCropBox);
$("manual_clips_count")?.addEventListener("input", renderManualClipRows);
$("manual_clips_count")?.addEventListener("change", renderManualClipRows);
$("url").addEventListener("input", debounce(preview, 500));
$("scanBtn").addEventListener("click", scan);
$("clipBtn").addEventListener("click", clip);
$("segSelectAllBtn").addEventListener("click", selectAllSegments);
$("segClearBtn").addEventListener("click", clearSelectedSegments);
$("segCreateBtn").addEventListener("click", clipSelected);
$("modalClose").addEventListener("click", closeModal);
$("modalBackdrop").addEventListener("click", closeModal);
$("langId")?.addEventListener("click", () => setLang("id"));
$("langEn")?.addEventListener("click", () => setLang("en"));
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

currentLang = localStorage.getItem("lang") || document.documentElement.lang || "id";
currentLang = currentLang === "en" ? "en" : "id";
applyI18n();
toggleMode();
toggleFont();
toggleSmartCropBox();
renderManualClipRows();
renderSegments([]);
