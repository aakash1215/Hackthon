# Build-day prompts (copy-paste into Claude Code)

**How to use:**
- One prompt per phase, in a session started at the repo root. `CLAUDE.md` loads automatically and holds the rules, so the prompts stay short.
- After each phase: test on the phone, then paste the next prompt with your findings in the `Notes from Akash` line.
- If usage resets or you start a new session, use the **Resume** prompt.

---

## Kickoff (P0): paste this first

```
We're building Apna Hisaab today (OpenForge PS07, build day Fri 16 Oct 2026, ends 17:00 IST).

Read CLAUDE.md (already loaded), then planning/BUILD_PLAN.md fully. Read planning/IMPLEMENTATION_HANDOFF.md §10 only when a phase needs a module spec. BUILD_PLAN.md overrides every other doc and the wage-theft-evidence-builder skill wherever they differ.

Do Phase P0 now:
- Restore backend/ from HEAD (git restore backend/), unless my notes below say the deletion was intentional. Set up the Python 3.12 venv with uv and run pytest (F1–F9 must pass).
- Add config.py + .env.example and the FastAPI HTTPS skeleton with /api/health, and scaffold frontend/ (Vite React + vite-plugin-pwa).
- Start the model and llama-server downloads in the BACKGROUND for the CPU/dev tier, and tell me the commands for the GPU tier.
- Set up mkcert for localhost + my current LAN IP, and give me the steps to install the root CA on my Android phones.
- Run the smoke tests in the P0 "done when" list.

When P0 is done: update the status table in BUILD_PLAN §1, commit, and report in ≤10 lines, including exactly what I must do by hand (BotFather, phone CA install, hotspot).

Notes from Akash: <GPU status / anything else>
```

## P1: Evidence core backend

```
Do Phase P1 from planning/BUILD_PLAN.md (evidence core backend): db + hash chain, POST /api/entries (save + hash audio/photo/GPS first), ASR wrapper, normalizer, extractor, reconciler, process/confirm, ledger, hisaab, and the profile endpoints. Use Handoff §10.3–§10.10 for module details plus the BUILD_PLAN §5 additions. Write pytest for the normalizer, reconciler and chain. Test with the clips in data/demo_clips/ if they exist, otherwise with a quick synthetic clip.

Finish with the CP1 checks, update the status table, commit + push, report.

Notes from Akash: <e.g. "clips are in data/demo_clips, ground truth in truth.csv">
```

## P2: Mobile PWA cloned from UI/

```
Do Phase P2 from planning/BUILD_PLAN.md. First list UI/ and study every file. Clone the design 100%, mobile-first (360–412 px), following the UI rule in CLAUDE.md. Build onboarding, home, record (voice → optional photo → GPS → saved #hash, plus "Same as yesterday"), confirm card, ledger and hisaab screens against the P1 API. Then add the offline queue (browser SHA-256 + IndexedDB + auto-upload with hash match) and the service worker/PWA install.

Make sure npm run build passes and the app is served by FastAPI on https://<LAN-IP>:8443. Tell me exactly what to test on the phone (including airplane mode). Update the status table, commit + push, report, and list any screens not in UI/ that you composed.

Notes from Akash: <UI/ ready? phone issues from P1?>
```

## P3: Corroboration + packet

```
Do Phase P3 from planning/BUILD_PLAN.md:
- Record thekedar with the unskippable notice (§8);
- worker hisaab check + deterministic differences;
- co-worker confirmation (§9);
- payment-proof and site-board photos;
- corroboration levels per day (§6, with pytest);
- the evidence packet (Jinja2 → Playwright PDF, Devanagari font bundled, the new sections listed in P3, SYNTHETIC watermark, bundle.zip with a hash manifest).

Show the levels in the ledger UI using the UI/ style. Finish with the CP3 checks, update status, commit + push, report.

Notes from Akash: <phone test results from P2>
```

## P4: Telegram thekedar agent

```
Do Phase P4 from planning/BUILD_PLAN.md. Build the Telegram thekedar agent exactly as specified in §7:
- python-telegram-bot long polling in the FastAPI lifespan;
- invite link + QR, language pick, intro notice;
- the DAILY_UPDATE/PAYMENT_ACK/SUMMARY templates;
- inbound text/voice saved + hashed with the Telegram server timestamp;
- thekedar_reply classification and the reply-policy table (template-only; hostile = no reply + alert);
- promise cards in the app.

Write pytest for the reply policy on the 6 scripted messages. The token is in .env (TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME). I'll test with my second account "Kailas".

This is CP4 = feature freeze: update status, commit + push, report.

Notes from Akash: <phone test results from P3>
```

## P5: On-device AI (stretch: only if CP4 is green)

```
CP4 is green. Do Phase P5 from planning/BUILD_PLAN.md: whisper-small (transformers.js, WebGPU→WASM fallback) and, if that works, Qwen3.5-0.8B on the phone, labelled processed_tier "device", re-processed on the server when online, with diffs shown for re-confirmation. My phone test results: <paste chrome://gpu + demo speeds for A33 and Y73>.

Timebox: 40 min. If it's too slow, stop, revert and tell me. Commit + report.
```

## P6: Demo data, README, submission

```
Do Phase P6 from planning/BUILD_PLAN.md:
- scripts/seed_demo.py + a one-command reset (Sunita persona, mixed L1/L2/L3 days, a thekedar recording, a Telegram thread, payment proofs, all synthetic);
- README per Handoff §10.18 plus the P6 additions, with MEASURED latencies from this machine;
- docs/benchmark.md;
- the AC checks from BUILD_PLAN §11.

Run grep -ri "openai\|anthropic\|generativeai" over the product code (it must find no API clients). Make sure LICENSE is Apache-2.0 and no weights, .env, certs or data are tracked. Commit + push, then give me the 3-min demo checklist from §10 with the exact reset command.
```

---

## Resume (new session or after a usage reset)

```
Resume the Apna Hisaab build. Read CLAUDE.md, the status table in planning/BUILD_PLAN.md §1, and `git log --oneline -15`. Continue the first phase that is not ☑. Before writing new code, check what already exists for that phase (don't redo committed work). Current time: <HH:MM>. If we are behind the target times, apply the BUILD_PLAN §4 cut line and tell me what you cut.
```

## Quick fix (between phases)

```
Bug from the phone test (<phone>, <screen>): <what I did> → <what happened> → <what I expected>. Fix it with the smallest change, add a test if it's backend logic, commit, and tell me how to re-test.
```
