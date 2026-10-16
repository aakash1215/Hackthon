# CLAUDE.md — Apna Hisaab (OpenForge PS07) build rules

You are the coding agent for **Apna Hisaab**, a wage-theft evidence builder for migrant construction workers (OpenForge Hackathon, Track 1, PS07). Akash builds solo with you **today, Fri 16 Oct 2026, until 17:00 IST**. Judges assess the repo and README at his desk.

## Read order (and which file wins)
1. **This file**: rules and how to work.
2. **`planning/BUILD_PLAN.md`**: the execution plan. It covers phases, scope, new feature specs and the status table. **It wins over every other doc.**
3. `planning/IMPLEMENTATION_HANDOFF.md` §10: module details not changed by BUILD_PLAN (normalizer, reconciler, wage engine, hash chain, packet).
4. `planning/suggestions.md`: why the plan changed on 16 Oct.
5. `planning/PS07_Strategy_Report.md`: research background. Read only if needed.

If the `wage-theft-evidence-builder` skill or any older doc says "no GPS", "fully offline" or "AI never messages the thekedar", **BUILD_PLAN.md overrides it** (decisions of 16 Oct).

## Hard rules (never break)
1. **Open-weight AI only in the product.** Never call OpenAI, Gemini, Claude or any other closed AI API. The Telegram Bot API is a message transport, not AI, so it is allowed.
2. **The LLM extracts and classifies; code computes.** No LLM arithmetic, legal reasoning or free text sent to anyone. Read-back and every message to the thekedar come from **fixed templates filled by code**.
3. **Never invent values.** Every extracted field is `{value, evidence}`, and `evidence` must be an exact transcript substring; otherwise the value is null. Only worker-confirmed values reach the wage engine.
4. **Save and SHA-256-hash every original file (audio, photo) before any AI call.** Hash the original bytes, before transcoding.
5. **Recording anyone other than the worker** (thekedar, co-worker) always starts with a notice that can't be skipped, records consent on the tape, and has an instant Stop. No covert recording.
6. **The Telegram agent follows BUILD_PLAN §7 exactly:**
   - it introduces itself and says the chat is recorded;
   - it replies only from templates;
   - it never negotiates, accepts a deal, threatens or cites law;
   - a hostile message means no reply plus an alert to the worker.
7. **GPS is opt-in.** Ask permission, show the coordinates to the worker, and store them with the entry or photo.
8. Wording: **"evidence file", "corroborated record", "estimate"**. Never "proof" or "legally valid".
9. **Synthetic demo data only**, watermarked "SYNTHETIC DEMO DATA". No real people.
10. **Never commit** model weights, `.env`, bot tokens, certificates, `data/` or `media/`. The license is Apache-2.0.
11. **Don't rewrite `backend/app/wage_engine.py`, `rates.py` or `money.py`.** They are tested (F1–F9). Extend them only, and keep `pytest` green.

## UI rule: clone `UI/` 100%, mobile-first only
- `UI/` is Akash's design and the **visual source of truth**. Before building any screen, list `UI/` and open every file (view the images; read any HTML/CSS).
- Reproduce it exactly: layout, spacing, colours, typography, icons, copy and component states. **Never "improve" or redesign it.** Put the extracted tokens in `frontend/src/styles/tokens.css`.
- Design target: **phone portrait, 360–412 CSS px wide** (Samsung A33 5G, Vivo Y73). On a desktop, render the same mobile layout centred, max-width 430 px. There is no desktop layout.
- Touch targets ≥ 48 px. Bundle the Noto Sans Devanagari font and icons locally (no CDN).
- If the plan needs a screen `UI/` doesn't have, compose it from the existing components in the same style, and list it in your phase report.
- If `UI/` breaks a hard rule (for example, it has no recording notice), keep the rule and tell Akash.
- If `UI/` is empty when the UI phase starts, ask Akash once. Meanwhile, build plain screens with a thin component layer so the re-skin is cheap.

## How to work
- **One phase per prompt** (BUILD_PLAN §3). Inside a phase, decide the small steps yourself. Don't ask Akash about routine choices.
- Order within a phase: contracts/schemas → implementation → tests → run → short report.
- Backend logic gets pytest tests (normalizer, reconciler, events/chain, corroboration, Telegram reply policy). Run `pytest` after every change to the engine, normalizer or reconciler.
- UI: `npm run build` must pass. Akash tests on the phone and tells you what's wrong.
- **At the end of each phase:**
  - update the status table in `BUILD_PLAN.md` §1;
  - commit `P<n>: <summary>` (with the Co-Authored-By line);
  - push at checkpoints;
  - report in ≤10 lines: what works, how to test it on the phone, what was cut, and what Akash must do.
- **Model servers are configuration, never hardcoded.** Read `LLM_BASE_URL`, `LLM_MODEL`, `ASR_MODEL`, `ASR_DEVICE`, `ASR_MODE` (local or remote), `TTS_ENABLED`, `TELEGRAM_BOT_TOKEN` and `DEMO_MODE` from `.env`. The app must still run when the LLM, TTS or Telegram is down: degrade, don't crash.
- **Long downloads run in the background**; never block on them.
- **Save Akash's Claude usage:**
  - read only the doc sections you need;
  - don't re-read files you just wrote;
  - keep reports short.
- **When behind schedule**, apply the cut line in BUILD_PLAN §4 and tell Akash what you cut. Never cut a hard rule.

## Environment
- Windows 10. Use the Bash tool (Git Bash) or PowerShell. Python 3.12 via `uv` (`uv venv -p 3.12`), Node 24, ffmpeg, gh.
- The dev box is an i3 laptop with no GPU (CPU-only tier). The demo GPU (6–8 GB VRAM; laptop or cloud) may arrive later, so everything switches by `.env`.
- Ports:
  - app (FastAPI serving the API and the built PWA): **https://<LAN-IP>:8443**;
  - llama-server: **127.0.0.1:8080**.
- HTTPS uses mkcert certificates for the LAN IP and localhost; they live in `certs/` (gitignored). The phone's mic, service worker and Web Share need HTTPS.
- Branch: `master`.
