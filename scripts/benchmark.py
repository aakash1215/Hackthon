"""Measure the pipeline's latencies on THIS machine (no guessed numbers in the README).

Run from backend/ with llama-server up:
  PYTHONIOENCODING=utf-8 .venv/Scripts/python ../scripts/benchmark.py <speech.wav> [packet.html]

Prints a markdown table. Each LLM/ASR step runs once (they are slow on the CPU tier); fast deterministic steps
are averaged over many runs.
"""
import hashlib
import os
import platform
import shutil
import statistics
import sys
import tempfile
import time
import wave
from datetime import date, time as dtime
from pathlib import Path

os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="ah_bench_"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app import asr, extract, normalize, reconcile  # noqa: E402
from app.config import settings  # noqa: E402
from app.rates import RateContext, load_packs  # noqa: E402
from app.wage_engine import WorkDay, compute  # noqa: E402

CLIP = Path(sys.argv[1]) if len(sys.argv) > 1 else None
PACKET_HTML = Path(sys.argv[2]) if len(sys.argv) > 2 else None
rows: list[tuple[str, str, str]] = []


def timed(fn, n=1):
    ts = []
    out = None
    for _ in range(n):
        t0 = time.perf_counter()
        out = fn()
        ts.append(time.perf_counter() - t0)
    return out, statistics.median(ts)


def fmt(s: float) -> str:
    return f"{s * 1000:.1f} ms" if s < 1 else f"{s:.1f} s"


# 1. save + hash (the first thing that happens to every recording)
blob = os.urandom(1_000_000)
_, t = timed(lambda: hashlib.sha256(blob).hexdigest(), 50)
rows.append(("SHA-256 of a 1 MB recording (hub)", fmt(t), "median of 50"))

# 2. ASR
if CLIP and CLIP.exists():
    with wave.open(str(CLIP)) as w:
        dur = w.getnframes() / w.getframerate()
    tmp = Path(tempfile.mkdtemp())
    src = tmp / CLIP.name
    shutil.copyfile(CLIP, src)
    _, t_tc = timed(lambda: asr.to_wav16k(src, tmp / "16k.wav"))
    rows.append((f"ffmpeg → 16 kHz WAV ({dur:.1f} s clip)", fmt(t_tc), "once"))
    _, t_load = timed(asr._load)
    rows.append((f"ASR model load (cold, {settings.asr_device})", fmt(t_load), "once per hub start"))
    res, t_asr = timed(lambda: asr.transcribe_wav(tmp / "16k.wav", "auto"))
    rows.append((f"ASR {Path(settings.asr_model).name} {settings.asr_device}/{settings.asr_compute_type} "
                 f"on a {dur:.1f} s clip", fmt(t_asr), f"real-time factor {t_asr / dur:.2f} (model warm)"))

# 3. deterministic reading
HI = "आज सुबह नौ बजे से शाम सात बजे तक काम किया, ठेकेदार ने पाँच सौ रुपये दिए।"
_, t = timed(lambda: normalize.normalize(HI, date(2026, 10, 16)), 200)
rows.append(("Normalizer (hi sentence)", fmt(t), "median of 200"))
norm = normalize.normalize(HI, date(2026, 10, 16))
_, t = timed(lambda: reconcile.reconcile("workday", None, norm, HI, date(2026, 10, 16)), 200)
rows.append(("Reconciler", fmt(t), "median of 200"))

# 4. LLM extraction (llama-server)
for kind, text in (("workday", HI),
                   ("hisaab_statement", "ठेकेदार बोला बारा दिन, छह सौ रुपये रोज़, दो हज़ार उचल काटी")):
    try:
        _, t = timed(lambda: extract.extract(kind, text, "2026-10-16"))
        rows.append((f"LLM extraction `{kind}` ({settings.llm_model}, {settings.tier})", fmt(t), "once"))
    except extract.LLMUnavailable as e:
        rows.append((f"LLM extraction `{kind}`", "unavailable", str(e)))
for text in ("मैंने तो पिछले हफ्ते 3000 दे दिए थे", "हाँ भाई, तेरह दिन का हिसाब सही है"):
    try:
        _, t = timed(lambda: extract.extract_reply(text))
        rows.append(("LLM thekedar_reply classification", fmt(t), "once"))
    except extract.LLMUnavailable as e:
        rows.append(("LLM thekedar_reply classification", "unavailable", str(e)))

# 5. wage engine
from app.rates import RateContext  # noqa: E402,F811

ctx = RateContext(sphere="state", state="Maharashtra", employment_sn=11, category="unskilled", zone="I", zone_confirmed=True)
days = [WorkDay(date(2026, 10, d), dtime(9), dtime(19), 60, f"e{d}") for d in range(1, 14)]
packs = load_packs()
_, t = timed(lambda: compute(days, [], ctx, packs, wage_period="monthly"), 200)
rows.append(("Wage engine, 13 days (exact rational arithmetic)", fmt(t), "median of 200"))

# 6. packet PDF
if PACKET_HTML and PACKET_HTML.exists():
    from app.packet import _render_pdf

    out = Path(tempfile.mkdtemp()) / "p.pdf"
    err, t = timed(lambda: _render_pdf(PACKET_HTML, out))
    rows.append(("Evidence packet HTML → PDF (Playwright/Chromium)", fmt(t) if not err else err,
                 f"{out.stat().st_size // 1024} KB" if out.exists() else ""))

cpu = platform.processor() or platform.machine()
print(f"Machine: {platform.system()} {platform.release()}, {cpu}, {os.cpu_count()} logical CPUs, no GPU "
      f"(tier `{settings.tier}`)\n")
print("| Step | Time | Note |\n|---|---|---|")
for r in rows:
    print(f"| {r[0]} | {r[1]} | {r[2]} |")
