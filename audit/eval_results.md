# Evaluation results (measured, 16 Oct 2026)

Source: [`docs/benchmark.md`](../docs/benchmark.md) (`scripts/benchmark.py`) and the build-day notes in
`planning/BUILD_PLAN.md` (P0/P1). These numbers are from a CPU tier with a small sample. There is **no**
large labelled benchmark.

## Latency (Intel i3-6006U, 8 GB RAM, no GPU)
| Step | Time |
|---|---|
| ASR faster-whisper-small int8, 9.6 s clip | 21.1 s (real-time factor 2.2) |
| LLM extraction `workday` (Qwen3-1.7B Q4_K_M), first call | 79.7 s |
| LLM `thekedar_reply` classification, repeat | 11.2 s |
| Wage engine, 13 days | 2.9 ms |

## Quality observations
- Qwen3-1.7B returned schema-valid JSON with grounded evidence, but **wrong values** when it did the parsing
  (सात → 5 PM, पाँच सौ → 5000). Fix: a deterministic normalizer parses numbers and times from the quoted span in
  code (`backend/app/normalize.py`); the model only quotes.
- Its quotes were often ungrounded (not exact substrings). Those fields are dropped and flagged for the worker
  (`backend/app/reconcile.py`).
- Qwen3.5-2B was compared: slower (26.6 s vs 18 s) with worse spans, so Qwen3-1.7B was kept.
- It missed a threat ("haath pair tod dunga") that a deterministic word guard catches (`tests/test_telegram.py`).

## Automated tests
`cd backend && pytest`: wage engine F1–F9 (exact arithmetic), normalizer, reconciler, hash chain, corroboration,
Telegram reply policy and agent checks (150+ tests, green on 16 Oct).
