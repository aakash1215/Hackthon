---
name: "hackathon-build-day"
description: "Use on OpenForge Final Build Day (10-hour offline build) or when planning it: hour-by-hour runbook, scope cuts, fallbacks, Git/README compliance and the 'are we on track?' check."
---

# OpenForge Build Day Runbook (Sat 17 Oct 2026, 07:00–17:00, at the college; solo build)

Goal: a demo that works every single time, tells a human story, and visibly runs open-weight AI offline. Polish comes last.

- **Product:** "Apna Hisaab" (PS07). Full plan: `planning/PS07_Strategy_Report.md`. Build brief: `planning/IMPLEMENTATION_HANDOFF.md`.
- **Confirmed by coordinators (13 Oct):** own laptop, power and **internet available**; prep and an empty repo allowed; submit **repo + README**; **judges come to your desk**.
- **Builder:** **solo**, using Claude Code (Claude Pro, one reset) as a coding assistant.
  - Give it the handoff spec at 07:00, one module at a time with tests.
  - Budget roughly 40% of usage before CP2, 40% for 12:20–15:00, and keep the reset for bug-fixing after 15:00.
  - If the limit is hit, hand-code from the spec.

## Before the day (prep is allowed, product code is not; disclose prep in README)
- **Tier A laptop** (NVIDIA, 8 GB VRAM) plus fallbacks: Tier B (Anuskha's NVIDIA 2–4 GB) and Tier C (Akash's i3, CPU-only).
- **Toolchain:** NVIDIA driver, **Python 3.11/3.12** (not 3.14), Node 22 LTS, Git, ffmpeg, llama.cpp CUDA build (`llama-server`), faster-whisper/CTranslate2, torch (CUDA), transformers + parler-tts, FastAPI, Jinja2, Playwright + Chromium, pytest. Build offline pip and npm caches.
- **Models on SSD and a USB backup:**
  - IndicWhisper hi + mr (→ CTranslate2);
  - Whisper large-v3-turbo CT2;
  - Qwen3-4B-Instruct-2507 Q4_K_M;
  - Indic Parler-TTS (accept the gated terms);
  - Gemma 4 E4B Q4_K_M + mmproj (challenger);
  - Qwen3-1.7B and Whisper small (Tiers B/C);
  - Noto Sans Devanagari.
- **CLI-only benchmarks** on 30 SYNTHETIC clips (12 mr, 12 hi, 6 Hinglish; 5 noisy): entity accuracy for times, amounts and names; latency; peak VRAM with all three models loaded. Write the numbers down.
- **Rate data:** verify the Maharashtra notification 7997 (05.08.2026) original; fill the rate-pack sheet; hand-compute fixtures F1–F9.
- **Content (text, kept in `planning/`):** hi/mr strings, read-back templates, consent script, Saathi FAQ answers, the thekedar statement, the recording notice, the risk note.
- **Repo:** create an empty public repo with LICENSE (Apache-2.0) now; this is allowed.
- **HTTPS for the phone:** mkcert, a cert for the laptop's LAN IP + localhost, root CA installed on the demo Android phone. Check with `npx http-server -S`. Regenerate the cert at the venue if the IP changes.
- **Pack:** 3 laptops, chargers, extension board, USB mic, 2 Android phones, USB SSD, printed runbook and demo script.

## Scope tiers
- **MUST** (demo dies without it):
  - record → audio saved and hashed → ASR → normalizer + LLM → reconcile (green/amber/red);
  - confirm → hash-chained SQLite;
  - deterministic wage engine with provenance → hisaab view → packet (HTML → PDF);
  - seeded synthetic data; offline.
- **SHOULD**, in this order:
  1. TTS read-back;
  2. voice hisaab check;
  3. **Hisaab Saathi:** Saboot (exact clip) → Bhejo (ask, risk note, share) → Samjhao (explain + FAQ) → Bol ke Batao (statement → announced reply → promise);
  4. tamper demo;
  5. coach checklist;
  6. s.17 flags;
  7. witness statement;
  8. tombstones.
- **STRETCH:** site-board photo/OCR, SMS anchor, central-sphere pack, IndicTrans2 gloss, HTTPS hub for Web Share, real-phone PWA sync.
- **Rule:** never start a SHOULD or STRETCH item while any MUST is broken. **Never build** an AI that debates, negotiates with or phones the thekedar.

## Hour-by-hour (solo; you + Claude Code)
| Time | Work | Checkpoint |
|---|---|---|
| 07:00–07:30 | Start `llama-server`; ASR and TTS smoke tests; scaffold FastAPI + Vite React + `vite-plugin-pwa`; regenerate the mkcert cert | Models respond |
| 07:30–09:00 | SQLite + hash chain; **wage engine + fixtures F1–F9**; rate-pack resolver | `pytest` green |
| 09:00–10:30 | Upload → hash → ASR → normalizer → LLM → reconciler; process and confirm APIs | **CP1 10:30:** 1 hi + 1 mr clip correct |
| 10:30–12:00 | React: record (flexible length, "Same as yesterday"), confirm card, ledger, hisaab view; TTS; HTTPS for the phone | **CP2 12:00: MUST path offline; phone opens the app over HTTPS** |
| 12:20–14:00 | Packet PDF + ZIP; demo reset/seed script; Saboot + Bhejo; voice hisaab check | — |
| 14:00–15:00 | Samjhao + FAQ; Bol ke Batao statement (reply/promise if time); PWA install on the phone | **CP3 15:00: freeze; Wi-Fi-off rehearsal** |
| 15:00–16:00 | Edge cases, tamper demo, latencies, README, screenshots, backup video | — |
| 16:00–16:40 | Rehearse the 3-min desk demo and 6-min full demo | — |
| 16:40–17:00 | Final push; verify the repo; leave the app running for judges | — |

**Desk judging:** keep a one-command demo reset and a printed A4 sheet (models with params and licenses, architecture, legal basis, "synthetic data" note).

## "Are we on track?" check (run at every checkpoint)
1. Can we demo the MUST path right now, offline? If not, what is the single blocker?
2. What is the slowest step, and is it acceptable live? Tier A target: ≤12 s from voice note to card; ≤5 s read-back.
3. Which feature in progress can be cut with the least damage to the story?
4. Is the latest working state committed and pushed?

## Cut line (in order, if behind at CP2)
1. Bol ke Batao reply recording (keep the statement).
2. Samjhao Q&A (keep the explanation).
3. Coach/s.17.
4. Voice hisaab-check → manual contractor-claim form.
5. Web Share → download + `wa.me` link.
6. PWA install (keep the HTTPS mobile page).
7. TTS → on-screen card + replay.
8. Playwright → browser Print-to-PDF.
9. Marathi → Hindi-only (last resort).

**Protect** Saboot + the Bhejo prompt: it is the most memorable moment.

## Fallbacks (prepare all)
- Tier A laptop fails → Tier B config (tested beforehand), then Tier C + pre-processed data + backup video.
- ASR weak on a clip → read-back + amber + pickers; tap-first numeric capture.
- LLM bad JSON → schema constraint, T=0, retry once, then normalizer-only values (all amber).
- Mic fails → "upload recording" with pre-recorded demo clips.
- No venue internet → push via phone hotspot.
- Laptop freezes → backup video + screenshots.

## README checklist (Track 1 compliance)
- [ ] Problem + solution summary, screenshots/GIF
- [ ] Architecture diagram
- [ ] Models: exact name, **parameter count**, quantisation, license link (ASR, LLM, TTS)
- [ ] No closed AI API in the product; disclosure of AI-assisted coding tools; "Preparation before the event" list
- [ ] Offline setup steps + model download script; hardware tested on + **measured** latency
- [ ] Wage-rate sources with notification no., date, URL and verification status
- [ ] Apache-2.0 LICENSE file
- [ ] Limitations (not proof; device clock; rates need verification; time-rated work only) + roadmap

## Git hygiene
- Small commits with clear messages; push at each checkpoint.
- Never commit model weights or personal data (`*.gguf`, `*.bin`, `models/`, `data/`, `media/` go in .gitignore); include a model download script instead.
- Commit timestamps are the originality record.
