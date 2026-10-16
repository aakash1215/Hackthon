# Measured latencies (CPU tier)

Measured on build day (16 Oct 2026, 14:40 IST) with `scripts/benchmark.py` on an idle machine:

**Intel Core i3-6006U (2 cores / 4 threads, 2.0 GHz, 2015), 8 GB RAM, no GPU, Windows 10.**
llama-server: one slot, 2 threads (`bash scripts/start_llm.sh cpu`). ASR: faster-whisper-small int8 on CPU,
greedy decoding (temperature 0), VAD on. The speech clip is a 9.6 s synthetic English sentence (Windows SAPI). ASR
cost depends on audio length, not language.

| Step | Time | Note |
|---|---|---|
| SHA-256 of a 1 MB recording (hub) | 7 ms | median of 50; the phone hashes in the browser before upload |
| ffmpeg → 16 kHz WAV (9.6 s clip) | 0.19 s | |
| ASR model load (cold) | 5.1 s | once per hub start |
| ASR faster-whisper-small int8, 9.6 s clip | 21.1 s | real-time factor 2.2 |
| Normalizer (Hindi sentence) | 0.9 ms | deterministic second reader |
| Reconciler | 0.1 ms | grounding + two-reader merge |
| LLM extraction `workday` (Qwen3-1.7B Q4_K_M) | 79.7 s | first call: the few-shot prompt (~1,000 tokens) is evaluated |
| LLM extraction `hisaab_statement` | 29.3 s | |
| LLM `thekedar_reply` classification (first) | 36.6 s | |
| LLM `thekedar_reply` classification (repeat) | 11.2 s | prompt prefix cached by llama-server |
| Wage engine, 13 days (exact `Fraction` arithmetic) | 2.9 ms | |
| Evidence packet HTML → PDF (Playwright/Chromium) | 6.2 s | 113 KB |

**End to end on this laptop:** a 10 s voice note is saved and hashed instantly (online or offline), and appears as
a confirm card about **1–2 minutes** later (ASR ~20 s + LLM 30–80 s). Notes are processed in the background, one at a
time. Observed on Akash's phone after the queue fix: 84 s for a real note (ASR + LLM).

**What made it slow before** (fixed): llama-server's default 4 parallel slots split the context and let concurrent
requests starve each other on 2 cores; Whisper's temperature-fallback loop on a noisy 5 s Marathi clip ran for minutes.

**GPU tier** (Qwen3-4B + Whisper large-v3-turbo on a 6–8 GB GPU) is configured in `.env` but was **not measured**
on build day: no GPU was available.

Reproduce: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python ../scripts/benchmark.py <speech.wav> [packet.html]`.
