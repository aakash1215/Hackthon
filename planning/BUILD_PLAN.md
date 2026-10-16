# Apna Hisaab: Build Plan v2 (Fri 16 Oct 2026, build day)

> **This is the execution plan, and it overrides every other doc where they differ.**
> It folds in the decisions of 16 Oct (`planning/suggestions.md`):
> - GPS allowed;
> - online + offline tiers;
> - voice plus an optional photo per entry;
> - consented thekedar recording;
> - co-worker confirmation;
> - a Telegram agent that talks with the thekedar;
> - the UI cloned from `UI/`, mobile-first.
>
> For modules this file doesn't respecify, use `IMPLEMENTATION_HANDOFF.md` §10 (normalizer §10.5, reconciler §10.6, wage engine §10.7, rate pack §10.8, hash chain §10.9, packet §10.13).

---

## 1. Status (the agent updates this table at the end of each phase)

| Phase | Target end | Status | Notes |
|---|---|---|---|
| P0 Setup, restore, model servers, HTTPS | 10:30 | ✅ 10:55 | pytest 19 green (F1–F9 + health). HTTPS `/api/health` OK on LAN IP (curl, verified chain); phone check pending (CA install). llama-server CPU + Qwen3-1.7B: schema JSON in 18 s, grounded evidence, but **wrong values** (सात→5 PM, पाँच सौ→5000) → normalizer must parse evidence spans in code. whisper-small int8: 7.4 s clip in 11.4 s. `av` pinned 15.1 (faster-whisper compat). Qwen3.5-2B compared: slower (26.6 s) and worse spans → **keep Qwen3-1.7B** on CPU. Scripts: `scripts/download_models.sh cpu\|gpu\|indic`, `start_llm.sh`, `make_certs.sh`, `smoke_llm.py`. |
| P1 Evidence core backend | 12:00 (**CP1**) | ◐ 11:10 | Backend done: save+hash first, hash chain + verify, process/confirm, normalizer, reconciler, LLM extract, ledger, hisaab (wraps engine), profiles, chain verify. pytest 58 green (incl. F1–F9). Real ASR + real LLM over HTTP verified on an English clip. **Open:** 1 hi + 1 mr clip through the app needs Akash's recordings in `data/demo_clips/`; text-level hi/mr check run with `scripts/p1_text_check.py`. Qwen3-1.7B on CPU: 20–80 s per entry, and quotes often ungrounded (dropped, flagged). |
| P2 Mobile PWA cloned from `UI/` + offline queue | 13:30 (**CP2**) | ✅ 12:07 (phone test pending) | Screens cloned from UI/: splash, O2, O3, O5, O6, O7, D1–D6, H1, H2, F2 (subset). Offline: browser SHA-256 + IndexedDB job queue + auto-upload; hub hash must match. PWA installs (SW precache, icons). Headless E2E `scripts/e2e_pwa.py` (Chromium 390 px, fake mic/GPS) green: onboarding → record → photo/GPS → saved → process → confirm → ledger → hisaab; airplane mode → reload offline → reconnect → upload `hash_match=1`. New `POST /api/entries/copy-yesterday` (amber, no audio). Cut: PIN (O4), profile picker (A1) per §4 #7. H3/H4/S*/F1 → P3/P4 placeholders. JS numeral parser not done (→ P5). pytest 60 green. |
| P3 Corroboration layer + evidence packet | 15:00 (**CP3**) | ☐ | |
| P4 Telegram thekedar agent | 16:00 (**CP4**, feature freeze) | ☐ | |
| P5 On-device AI (stretch, only if CP4 is green) | — | ☐ | |
| P6 Demo data, README, rehearsal, push | 17:00 | ☐ | |

**Already done (commit `6e639cb`):** the deterministic wage engine (`Fraction` arithmetic), the rate loader and resolver, Maharashtra SN11 Jul–Dec 2026 and central-sphere rate packs with provenance, and tests F1–F9.
⚠️ At 09:53 the working tree showed `backend/` **deleted** (not committed). P0 restores it with `git restore backend/` unless Akash says the deletion was intentional.

---

## 2. What we're building (one paragraph)

A worker speaks a short daily note (Hindi/Marathi/Hinglish), optionally adds a photo, and the phone attaches GPS.
1. Everything is saved and hashed first.
2. Open-weight ASR and an LLM extract the fields; a deterministic parser cross-checks them.
3. The worker confirms, and the entry goes into a hash-chained ledger.
4. The deterministic wage engine compares work and pay against the provenance-stamped Maharashtra rate pack.

Because a worker-only log can be challenged, each day carries a **corroboration level**:
- a photo and GPS at the site;
- a co-worker's consented voice confirmation;
- payment-proof photos;
- **the thekedar's own words**, from a consented recording or from his messages to the Telegram agent (with Telegram server timestamps).

A bilingual, hash-indexed **evidence packet** comes out for a paralegal or union.
**Pitch line:** *"We don't replace the employer's record — we fill the gap his missing record leaves. No internet never means no record."*

---

## 3. Phases (major steps; the agent decides the small steps)

### P0 Setup, restore, model servers, HTTPS (→ 10:30)

**Goal:** everything needed to build and demo is running, and no phase waits on downloads.

- **Restore the backend.** Run `git restore backend/` unless told otherwise. Create the venv (`uv venv -p 3.12`), install `requirements.txt`, run `pytest` (F1–F9 must be green).
- **Add `backend/app/config.py`.** It reads `.env`:
  - `LLM_BASE_URL`, `LLM_MODEL`;
  - `ASR_MODE` (`local` | `remote`), `ASR_URL`, `ASR_MODEL`, `ASR_DEVICE`, `ASR_COMPUTE_TYPE`;
  - `TTS_ENABLED`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, `DEMO_MODE`, `DATA_DIR`.

  Commit `.env.example` (never `.env`).
- **Start the model downloads in the background** (into `models/`, which is gitignored). The full list with URLs and commands is in `planning/requirements_download.md`:
  - llama.cpp `llama-server`: Windows CPU (AVX2) build now; CUDA build on the GPU box;
  - LLM, CPU/dev: `Qwen3-1.7B` Q4_K_M, or `Qwen3.5-2B` Q4_K_M (1.28 GB). Keep whichever returns valid schema JSON faster in the smoke test. Disable thinking (`chat_template_kwargs: {"enable_thinking": false}`, `--jinja`);
  - LLM, GPU/demo: `Qwen3-4B-Instruct-2507` Q4_K_M (2.50 GB);
  - ASR, CPU/dev: faster-whisper `small` int8;
  - ASR, GPU/demo: `deepdml/faster-whisper-large-v3-turbo-ct2` first (ready-made, ungated). Then AI4Bharat IndicWhisper hi/mr converted to CTranslate2, **if** the download and conversion finish in the background;
  - TTS, GPU only: `ai4bharat/indic-parler-tts` (gated: accept the terms). With no GPU, TTS stays off: show the on-screen card and replay the worker's own recording.
- **Where the GPU runs.** If it's a GPU laptop, the whole backend runs on it. If it's a cloud GPU:
  - run `llama-server` there and, with `ASR_MODE=remote`, the same backend in "model server" mode exposing `POST /internal/asr`;
  - the laptop keeps the app, the DB and the Telegram bot, and points `LLM_BASE_URL`/`ASR_URL` at the cloud.
- **HTTPS.**
  - Run mkcert for `localhost` plus the laptop's **current LAN IP**; install the root CA on both phones; put the certificates in `certs/`.
  - Venue Wi-Fi often blocks phone-to-laptop traffic, so **use the laptop's or a phone's hotspot**. Regenerate the certificate if the IP changes.
- **Scaffold.**
  - `backend/app/main.py`: FastAPI on HTTPS :8443, serving `/api/*` and the built PWA from one origin, plus `GET /api/health` (shows the model, TTS and Telegram status and the tier).
  - `frontend/`: Vite + React + `vite-plugin-pwa` + `idb-keyval`.

**Done when:**
- `pytest` is green;
- `llama-server` answers a schema-constrained request;
- faster-whisper transcribes a test clip;
- `https://<LAN-IP>:8443/api/health` opens on the phone with a valid lock.

### P1 Evidence core backend (→ 12:00, CP1)

**Goal:** save → hash → ASR → extract → reconcile → confirm → ledger → hisaab, working through the API.

- **`db.py`:** SQLite in WAL mode. Tables from Handoff §10.3 plus the v2 additions in §5 below.
- **`events.py`:** an append-only hash chain with `verify()` (Handoff §10.9).
- **`POST /api/entries`** (multipart):
  - fields: `audio`, optional `photo`, `kind`, `worker_id`, `client_ts`, `client_sha256`, optional `lat`/`lon`/`gps_accuracy_m`/`gps_ts`;
  - **writes the original bytes and their SHA-256 first** (`AUDIO_SAVED`, `PHOTO_SAVED`);
  - if `client_sha256` is present it must match; a mismatch is flagged, never silently fixed;
  - returns `{entry_id, audio_sha256, status:"saved"}` at once.
- **`asr.py`:**
  - faster-whisper with the language forced from the worker profile (`auto` allowed for thekedar recordings);
  - returns segments, word timestamps and confidences;
  - transcodes to 16 kHz WAV with ffmpeg;
  - supports local or remote mode.
- **`normalize.py`:** Handoff §10.5, with pytest.
- **`extract.py`:** llama-server, JSON schema, temperature 0; the schemas in Handoff §10.4 plus the new ones in §5.
- **`reconcile.py`:** Handoff §10.6, with pytest.
- **Processing endpoints:**
  - `POST /api/entries/{id}/process` and `POST /api/entries/{id}/confirm` (Handoff §10.10);
  - processing is async-safe: the entry stays `saved` if a model is down;
  - on restart, unprocessed entries are listed.
- **Read endpoints:**
  - `GET /api/ledger` and `GET /api/hisaab`, which wraps the existing `wage_engine.compute`. Errors are returned as codes, never as amounts;
  - minimal profile endpoints: worker (language, category), site (name, sphere, zone confirmed, and a **site GPS point** set from the first fix at the site), and parties (thekedar name and phone, builder).

**Done when (CP1):**
- over HTTP, 1 Hindi clip and 1 Marathi clip return colour-coded fields;
- confirm returns a chain head;
- `/api/hisaab` returns correct totals on a few confirmed days;
- `pytest` is green;
- committed and pushed.

### P2 Mobile PWA cloned from `UI/` + offline queue (→ 13:30, CP2)

**Goal:** the worker can do the core flow on the phone, and recording works with no connection.

- **Inventory `UI/` first** and clone it 100% (CLAUDE.md UI rule). Mobile-first, 360–412 px.
- **Screens.** Where `UI/` has a screen for a step, use it; otherwise compose one in the same style:
  1. **Onboarding:** language (hi/mr), consent (keep audio; GPS opt-in), category, site + zone confirm, thekedar name/phone, usual hours.
  2. **Home:** 🎙️ Work · 💵 Paid · 🧾 Record thekedar · 📒 Hisaab · 📁 Packet.
  3. **Record:**
     - tap to start/stop, flexible length, soft cap 60 s;
     - then an **optional photo** (`<input type="file" accept="image/*" capture="environment">`);
     - GPS from `navigator.geolocation` if the worker allowed it;
     - then **"Saved ✓ #7F3A-9C21"** at once;
     - one-tap **"Same as yesterday / कालसारखं / कल जैसा"** creates an amber entry that still needs confirming.
  4. **Confirm card:** green/amber/red chips; tap to fix with a picker; ▶ read-back if TTS is on, otherwise ▶ replay own recording; ✅ / ✏️.
  5. **Ledger:** days list with corroboration badges (§6).
  6. **Hisaab:** totals, per-day table, a "why?" drawer showing the formula, notification number, zone, validity and `verification_status`.
- **Offline (hard requirement):**
  - the service worker precaches the app shell;
  - while offline, the phone computes **SHA-256 in the browser** (`crypto.subtle`) on the original audio and photo bytes;
  - it stores `{audio, photo, gps, client_ts, client_sha256}` in an IndexedDB queue and shows "Saved on phone ✓ #hash";
  - it uploads automatically when the hub is reachable (`client_sha256` must match the server's hash), then processes and asks the worker to confirm.
- **JS numeral parser** (`frontend/src/lib/normalize.js`): a port of the number words, fractions and parts of day, so an offline entry shows an instant amber "device estimate" preview. Do it if P2 is on time; otherwise it moves to P5.

**Done when (CP2):** on the phone over HTTPS:
- record → photo → GPS chip → saved → confirm → shows in the ledger and hisaab;
- in airplane mode, a recording queues and later uploads with the same hash;
- the PWA installs to the home screen.

*Lunch 13:30–13:50.*

### P3 Corroboration layer + evidence packet (→ 15:00, CP3)

**Goal:** the record is no longer only "the worker says", and the packet shows that.

- **Record thekedar (consented):** spec in §8.
- **Hisaab check (worker narrates the settlement):**
  - the same `hisaab_statement` extraction with `speaker:"worker"`;
  - deterministic comparison with the ledger → itemised differences (`DAYS_DIFF`, `RATE_BELOW_MIN`, `PAID_DIFF`, `DEDUCTION_DISPUTED`).
- **Co-worker confirmation:** spec in §9.
- **Payment proof:** attach a photo of the UPI/SMS/cash slip to a payment entry, hashed (`PHOTO_SAVED`, kind `payment_proof`).
- **Site-board photo** in the profile (builder name, MahaRERA number).
- **Corroboration level per day:** §6. Computed deterministically, shown in the ledger and the packet. Add pytest.
- **Packet:**
  - Jinja2 HTML → PDF with Playwright/Chromium (fallback: the browser's Print-to-PDF);
  - Noto Sans Devanagari bundled;
  - sections from Handoff §10.13, plus:
    - (a) a corroboration column in the day table;
    - (b) photo thumbnails with SHA-256, device time and GPS;
    - (c) "Thekedar's own words": recording transcripts plus the Telegram log, with Telegram timestamps;
    - (d) co-worker confirmations;
  - "SYNTHETIC DEMO DATA" watermark in demo mode;
  - `bundle.zip` with a hash manifest.

**Done when (CP3):**
- a thekedar recording produces a differences list;
- a co-worker confirmation raises a day to L3;
- the packet PDF opens on the phone with correct Devanagari;
- committed and pushed.

### P4 Telegram thekedar agent (→ 16:00, CP4: feature freeze)

**Goal:** the thekedar receives factual updates and his replies become timestamped, hashed evidence. Spec in §7.

**Done when:**
- a second Telegram account ("Kailas") opens the worker's invite link and gets the intro notice;
- confirming a day sends the daily update;
- "Somvaar ko 5000 dunga" → a pending promise card appears in the worker's app;
- an abusive message gets no reply and the worker sees an alert;
- every message in and out is in the chain and the packet.

### P5 On-device AI (stretch, only if CP4 is green and Akash's phone test passed)

- Phone ASR: `onnx-community/whisper-small` via transformers.js in a Web Worker (WebGPU if `requestAdapter()` succeeds, otherwise WASM), language forced.
- Phone LLM: `Qwen3.5-0.8B` (transformers.js/WebGPU) with the same schema prompt; the JS parser is the second reader.
- Results are labelled `processed_tier:"device"`. When the hub is reachable they are **re-processed on the server**, and any differences are shown to the worker to re-confirm ("reassessed").
- If either model is too slow on the A33 or Y73, drop it. Offline capture already works without it.

### P6 Demo data, README, rehearsal, push (→ 17:00)

- **`scripts/seed_demo.py` + one-command reset:**
  - persona Sunita (Marathi helper), thekedar "Kailas", builder "Example Developers", Zone I, 13 days 09:00–19:00 with a 1 h break, paid ₹4,500;
  - a mix of L1, L2 and L3 days, one thekedar recording, a Telegram thread, and two payment-proof photos;
  - everything watermarked synthetic.
- **README** (Handoff §10.18), plus:
  - the tier table (online / CPU / on-device) with **measured** latencies;
  - Telegram as a stand-in transport for WhatsApp (the WhatsApp Business API is paid);
  - the GPS opt-in and privacy note;
  - "No closed AI API is used in the product";
  - disclosure of Claude Code as the AI coding assistant;
  - architecture diagram, screenshots, limitations, roadmap (native app with Gemma 4 E2B; WhatsApp Cloud API; multi-device crew attestation).
- **Before submitting:**
  - record a backup screen video;
  - rehearse the 3-min desk demo (§10) ×2;
  - make the final push; check the repo is public, the README renders and LICENSE is present;
  - **leave the app running for the judges.**

---

## 4. Cut line (apply at CP2/CP3 if behind; top = cut first)

1. P5 on-device AI (already stretch).
2. TTS read-back → on-screen card + replay of the worker's own recording.
3. Telegram inbound LLM classification → log inbound messages as evidence only and alert the worker. Keep linking + daily update.
4. JS numeral parser → offline entries show "will be processed when online".
5. Playwright PDF → browser Print-to-PDF of the packet HTML.
6. Co-worker confirmation by voice → one tap "Co-worker present: <name>" (stated, L1 only).
7. PIN / multi-profile.
8. Marathi → Hindi only (last resort).

**Protect at all costs:**
- save + hash before AI;
- record → photo → GPS → confirm → ledger → hisaab;
- thekedar recording with notice;
- Telegram link + daily update + message logging;
- the packet.

---

## 5. Data-model additions (on top of Handoff §10.3)

- `entries.kind`: `workday` | `payment` | `hisaab_statement` | `coworker_confirm`.
- New `entries` columns:
  - `speaker` (`worker` | `thekedar` | `coworker`), `language`;
  - `client_sha256`, `hash_match` (bool);
  - `lat`, `lon`, `gps_accuracy_m`, `gps_ts`;
  - `processed_tier` (`server` | `device`), `notice_played` (bool), `linked_day_ids` (JSON).
- `evidence.kind`: `photo` | `payment_proof` | `site_board` | `witness_audio`; plus `entry_id`, `lat`, `lon`, `gps_accuracy_m`, `taken_ts`. EXIF is kept, so GPS stays in the file.
- `sites`: add `site_lat`, `site_lon` (set from the first GPS fix at the site; the worker confirms).
- `tg_links(id, worker_id, party_id, invite_token, chat_id NULL, tg_user_id NULL, tg_username NULL, lang, linked_at, auto_daily BOOL default 1, paused BOOL)`.
- `tg_messages(id, worker_id, chat_id, direction 'in'|'out', tg_message_id, tg_date (Telegram server UTC), text, voice_path, voice_sha256, transcript, classification JSON, template_id, sha256)`.
- `promises`: add `source` (`telegram` | `recording`) and `source_ref`.
- **New events:**
  - `PHOTO_SAVED`, `GPS_CAPTURED`, `HASH_MISMATCH`;
  - `THEKEDAR_RECORDED{notice_played:true}`, `COWORKER_CONFIRMED`;
  - `TG_LINKED`, `TG_MESSAGE_IN`, `TG_MESSAGE_OUT`, `TG_HOSTILE_STOP`;
  - `PROMISE_LOGGED`, `REPROCESSED{tier_from, tier_to, diffs}`.

New extraction schemas (same `{value, evidence}` shape):
- **`coworker_confirm`:** `coworker_name`, `dates_or_days`, `site`, `consent_phrase`.
- **`thekedar_reply`** (used for recordings and Telegram): `intent` from `acknowledges` | `promise_to_pay` | `partial_payment_claim` | `disputes_days` | `disputes_rate` | `asks_details` | `refuses` | `hostile` | `other`, plus `confidence` (`high` | `low`), `amount`, `date`, `days`.

---

## 6. Corroboration level per day (deterministic, `corroboration.py`)

Signals for a confirmed workday:
- `SELF`: the worker's confirmed voice entry (base);
- `PHOTO`: a photo taken that date;
- `GPS_AT_SITE`: the entry or photo GPS lies within 300 m of the site point (accuracy ≤ 100 m);
- `COWORKER`: a confirmed co-worker confirmation covers the date;
- `THEKEDAR_ACK`: a thekedar recording or Telegram message classified `acknowledges` or `promise_to_pay`, whose days or amount cover the date or period. A **dispute** is shown as a separate `THEKEDAR_DISPUTES` flag, never hidden.

Levels:
- **L1 "Worker's record"**: SELF only;
- **L2 "+ on-site evidence"**: PHOTO or GPS_AT_SITE;
- **L3 "+ another person"**: COWORKER or THEKEDAR_ACK.

Shown as badges in the ledger and as a column in the packet, with the label *"How much of this day is backed by more than the worker's word: not a legal score."*

---

## 7. Telegram thekedar agent (`telegram_bot.py`)

**Why:** a demo stand-in for WhatsApp, whose Business API is paid. The same flow ports to the WhatsApp Cloud API later. **Telegram needs internet**, so the agent pauses offline and resumes when the connection is back.

**Runtime:**
- `python-telegram-bot` 21.x, **long polling**, started in the FastAPI lifespan only if `TELEGRAM_BOT_TOKEN` is set;
- no webhook, no public URL needed;
- the token lives in `.env` only.

**Linking (a bot can only message someone who started it):**
1. In the app, the worker taps "Connect thekedar on Telegram". The server creates an `invite_token` and shows `https://t.me/<bot_username>?start=<token>`, with Share (Web Share / `wa.me` text) and a QR code.
2. The thekedar opens the link and sends `/start <token>`. The bot asks for his language with inline buttons (हिंदी / मराठी / English); this covers the case where the thekedar's language is unknown.
3. The bot then sends the **intro notice** (always first), and logs `TG_LINKED`:
   - hi: "नमस्ते, मैं {worker} का 'अपना हिसाब' सहायक हूँ। इस चैट के संदेश {worker} के काम और भुगतान के रिकॉर्ड के रूप में सुरक्षित रखे जाते हैं।"
   - mr: "नमस्कार, मी {worker} यांचा 'आपला हिशोब' सहाय्यक आहे. या चॅटमधील संदेश {worker} यांच्या कामाच्या आणि पगाराच्या नोंदीसाठी जतन केले जातात."

**Outbound (templates only; numbers from the ledger and engine; balance always called an estimate):**
- `DAILY_UPDATE`: sent when the worker confirms a day, if `auto_daily` is on. The worker can turn it off.
  - hi: "आज {date}: {worker} ने {site} पर {start}–{end} काम किया। आज मिला: ₹{paid_today}। {worker} के रिकॉर्ड के अनुसार बाकी (अनुमान): ₹{balance}।"
  - mr: "आज {date}: {worker} यांनी {site} येथे {start}–{end} काम केले. आज मिळाले: ₹{paid_today}. {worker} यांच्या नोंदीनुसार बाकी (अंदाजे): ₹{balance}."
- `PAYMENT_ACK`: when a payment is confirmed: "₹{amount} मिले, धन्यवाद। बाकी (अनुमान): ₹{balance}।"
- `SUMMARY`: a day table for a period; the worker taps "Send summary".
- `REQUEST_WRITTEN_HISAAB`: "कृपया लिखित हिसाब और बाकी रकम की तारीख बताएं। धन्यवाद।"
- **Limits:** at most 5 bot messages per chat per day, and **no message is ever free LLM text**. Each one is stored in `tg_messages` with a `TG_MESSAGE_OUT` event.

**Inbound (text or voice):**
1. Save and hash first. A voice message is downloaded as OGG, hashed, then run through ASR with `auto` language.
2. Store the message with **Telegram's server timestamp** (`message.date`), which is a third-party time anchor, and log `TG_MESSAGE_IN`.
3. The LLM fills the `thekedar_reply` schema; grounding and normalizer checks apply to amount, date and days.

**Reply policy** (template only; each reply also creates an in-app item for the worker):

| Intent | Bot reply | In app |
|---|---|---|
| `asks_details` | `SUMMARY` template | — |
| `acknowledges` / `promise_to_pay` | "नोट कर लिया: ₹{amount}, {date}। धन्यवाद।" (date asked if ambiguous) | Pending promise card → worker confirms → `PROMISE_LOGGED` + reminder |
| `partial_payment_claim` | "नोट कर लिया। {worker} इसकी पुष्टि करेंगे।" | "Kailas says he paid ₹X. True?" → worker confirms or denies |
| `disputes_days` / `disputes_rate` | "नोट कर लिया। {worker} के रिकॉर्ड में {days} दिन दर्ज हैं। कृपया अपना लिखित हिसाब भेजें।" | Dispute flag on the affected days |
| `refuses` | "नोट कर लिया। धन्यवाद।" | Alert |
| `hostile` | **No reply.** `TG_HOSTILE_STOP`; auto messages paused | Alert + union/DLSA contacts |
| `other` / low confidence | **No reply** | "New message from Kailas", shown verbatim |

**Never:** negotiate, accept or reject an offer, mention penalties, sections or courts, threaten, or answer outside the templates.

**Pytest:** the reply policy on 6 scripted messages, including "Somvaar ko 5000 dunga" → `promise_to_pay`, "abhi paisa nahi hai" → `refuses`, and an abusive line → `hostile` with no reply.

---

## 8. Record thekedar (consented recording)

- **Entry points:** a Home button "🧾 Record thekedar" (standalone), and "Record his reply" after the hisaab check.
- **Flow:**
  1. Pick the notice language (hi / mr / en): the thekedar's language may differ from the worker's.
  2. The **notice plays automatically and can't be skipped**; the text is shown too.
  3. Recording starts only when the notice ends. Up to 60 s, with a big ■ Stop.

  Notice text (pre-recorded clip by Akash; on GPU it can be generated with Parler-TTS):
  - hi: "यह बातचीत रिकॉर्ड की जा रही है, ताकि हिसाब साफ़ रहे।"
  - mr: "हिशोब स्पष्ट राहावा म्हणून हे संभाषण रेकॉर्ड केलं जात आहे."
  - en: "This conversation is being recorded so the account stays clear."
- **Processing:**
  1. Save and hash; `THEKEDAR_RECORDED{notice_played:true}`.
  2. ASR (`auto` language), then extraction with both the `hisaab_statement` and `thekedar_reply` schemas.
  3. Deterministic comparison with the ledger → differences.
  4. **The worker confirms every number** before it counts. Two speakers plus site noise make ASR weak.
- **"Band karo" / refusal:** the worker taps Stop; only the notice is kept.

---

## 9. Co-worker confirmation

1. On a day (or a range), the worker taps "Ask co-worker to confirm".
2. The screen prompts the co-worker: *"Say your name, that you agree to be recorded, and which days {worker} worked with you."*
3. The recording is saved and hashed, then goes through ASR and the `coworker_confirm` extraction.
4. The worker confirms, the entry links to the days, and `COWORKER_CONFIRMED` is logged.

Witness audio is **never** included in any share by default. The packet lists the co-worker's name as stated, which can be redacted on export.

---

## 10. Demo (3-min desk version; all data synthetic)

1. **Hook (20 s):** "Sunita worked 13 days. The thekedar says 12 × ₹600 minus ₹2,000 advance. She has nothing written, and employers avoid every document that would prove she worked."
2. **Live (60 s):**
   - Marathi voice note → photo → GPS chip → "Saved ✓ #hash" → confirm card (green/amber) → ✅;
   - the Telegram "Kailas" phone gets the daily update.
3. **The thekedar's side (40 s):**
   - play the consented thekedar recording → the differences list;
   - on the Kailas phone, reply "Somvaar ko 5000 dunga" → a promise card appears in Sunita's app.
4. **Hisaab (30 s):** ledger with L1/L2/L3 badges → shortfall estimate with the notification citation and verification status.
5. **Packet (30 s):** PDF with the day table, corroboration column, photos + GPS + hashes, Telegram log with server timestamps, and evidence index. Optionally, a tamper demo ("chain broken at event N").

**Close:** "Open-weight models, worker-controlled, corroborated by the thekedar's own words. Not proof — a record a paralegal can use."

---

## 11. Acceptance deltas (on top of the strategy report §8.1)

- **AC9 (replaced):** with the hub unreachable, the phone still records, hashes, captures photo and GPS, and queues. After reconnecting, it uploads with matching hashes. Telegram features pause and resume.
- **AC14 (replaced):** geolocation is requested only after an opt-in during onboarding, and the coordinates are shown to the worker. A PIN is optional (cut line).
- **AC22:** every photo is SHA-256-hashed before processing and appears in the packet with its hash, device time and GPS.
- **AC23:** thekedar and co-worker recordings can't start before the notice or consent prompt; Stop is instant.
- **AC24:** the Telegram flow behaves as specified in §7:
  - linking only via the invite link, with the intro notice sent first;
  - every message in or out hashed with its Telegram timestamp;
  - outbound text only from templates;
  - hostile → no reply + alert;
  - auto messages only while `auto_daily` is on.
- **AC25:** corroboration levels are deterministic (pytest) and shown in the ledger and the packet.

---

## 12. Akash's parallel tasks (while the agent builds)

- **Now:**
  - create the bot with @BotFather and put `TELEGRAM_BOT_TOKEN`/`TELEGRAM_BOT_USERNAME` in `.env`;
  - set up a **second Telegram account** as "Kailas" (second phone or Telegram Desktop);
  - check the GPU laptop/cloud status;
  - on each phone, run the 10-minute check: `hf.co/spaces/webml-community/Qwen3.5-0.8B-WebGPU`, `hf.co/spaces/Xenova/whisper-webgpu`, `chrome://gpu`.
- **During P1:**
  - record ~8 synthetic clips into `data/demo_clips/` with a ground-truth sheet: 2 mr workday, 2 hi workday, 1 payment, 1 worker hisaab narration, 1 "thekedar" statement by a friend, 1 co-worker confirmation;
  - record the hi/mr **notice** clips.
- **Before 12:00:** put the final design into `UI/` (exported PNG per screen, and/or HTML/CSS).
- **P2–P4:** test every phase on both phones and report issues to the agent in one message.
- **P6:** review the README, rehearse, and keep the printed A4 sheet on the desk (models + params + licenses, architecture, "synthetic data").
