# Apna Hisaab: Implementation-Agent Handoff (PS07, OpenForge Track 1)

> **⚠️ v2 update (Fri 16 Oct 2026 = the actual build day):** [`BUILD_PLAN.md`](BUILD_PLAN.md) is now the execution plan and **overrides this file wherever they differ**. Changes:
> - GPS allowed (opt-in);
> - hybrid online/offline tiers;
> - voice plus an optional photo per entry;
> - consented "Record thekedar";
> - co-worker confirmation;
> - per-day corroboration levels;
> - a Telegram thekedar agent (template-only);
> - the UI cloned from `UI/`, mobile-first.
>
> The schedule in §7.3 below is superseded by BUILD_PLAN §3. The module specs in §10.4–§10.13 still apply. Rationale: [`suggestions.md`](suggestions.md).
>
> Self-contained build brief. Read [`PS07_Strategy_Report.md`](PS07_Strategy_Report.md) for the evidence, the decision rationale and judge Q&A.
>
> **Do not write product code before the Final Build Day (now Fri 16 Oct 2026; originally planned as Sat 17 Oct)**. Rule 5 of the rulebook disqualifies "pre-existing/unoriginal work". Before that date, only environment setup, model downloads, CLI benchmarks, data transcription and design content are allowed, and they must be disclosed in the README.

## Key facts this brief depends on

**Coordinator and team answers (13 Oct 2026, `AboutHackthon/Question&Answers.md`):**
- **Logistics:** build day **Sat 17 Oct, 07:00, 10 h, at the college**; own laptop, power and **internet available**; prep and an empty repo are allowed.
- **Judging:** submit **repo + README**; judges assess **at your desk**.
- **Builder:** **solo**, using Claude Code (Claude Pro, one reset) as a coding assistant. Disclose this in the README; it is not product AI.
- **App:** React; **installable phone web app (PWA)** → requires **HTTPS** (mkcert).
- **Voice notes:** **flexible length** plus a one-tap "Same as yesterday".

**Decisions confirmed by the team (13 Oct 2026):**
- Hardware: target an 8 GB VRAM NVIDIA laptop, with fallbacks on Anuskha's 2–4 GB NVIDIA laptop and Akash's CPU-only i3.
- Languages: Hindi, Marathi and Hinglish, plus English for the paralegal view.
- Hisaab Saathi voice agent in **worker-controlled "speak-for-me" mode**. **No AI debate or negotiation with the thekedar.**

**Current law and rates** (copied from the strategy report §3.5; all are labelled there [V], [S] or [E]):
#### 3.5 Jurisdiction and current minimum-wage source

**Legal status:**
- All four Labour Codes took effect on **21 Nov 2025** **[V]** ([EY alert, 21 Nov 2025](https://www.ey.com/content/dam/ey-unified-site/ey-com/en-in/alerts-hub/2025/11/new-labour-codes-implemented-across-the-country-effective-21-november-2025.pdf)). The Code on Wages commenced via S.O. 5322(E) (ss.1–41, 43–66, 68, 69) **[S]** (KPMG summary).
- Per the PIB release as summarised by EY, "relevant provisions of existing labour laws will remain in force during the transition period" **[V-secondary]**.

**Rules:**
- **Code on Wages (Central) Rules, 2026** were finalised **8 May 2026** as G.S.R. 343(E) **[V]** ([PRS](https://prsindia.org/billtrack/code-on-wages-central-rules-2026); [Taxmann](https://www.taxmann.com/post/blog/wages-central-rules-2026-code-on-wages-chapter-wise-guide/)). They set:
  - minimum wages on a **daily** basis; **hourly = daily ÷ 8; monthly = daily × 26**, with half-up rounding (r.3);
  - an **8-hour** normal day for daily-rated employees (r.5);
  - claims on **Form II**, filed manually or electronically, with group applications allowed for the same wage period (r.49);
  - Form V wage slip; Form IX muster roll kept for 5 years.
- **Maharashtra:** **draft** Code on Wages Rules were released 28 Apr 2026 with 45 days for objections. They specify 4 skill levels and VDA revision before 1 Apr and 1 Oct **[V]** ([SCC Online](https://www.scconline.com/blog/post/2026/05/01/draft-maharashtra-code-on-wages-rules-notified/)). Final status is unknown.
  - → Rate packs must accept **arbitrary validity windows**, not hardcoded half-years.

**Which rates apply (Code s.2(d)):** the Central Government is the "appropriate Government" for railways, mines, oil fields, major ports, air transport, telecom, banking/insurance, central PSUs and their contractors; the State Government for all others **[V]**. So a private building site in Chhatrapati Sambhajinagar uses **Maharashtra** rates, and a railway or central-PSU site uses **central-sphere** rates. Rates follow the **place of work**, not the worker's home state **[R]** (inference; confirm with legal aid).

**Current numbers:**

| Scope | Rates | Source |
|---|---|---|
| **Maharashtra**, SN 11 "Road construction, maintenance, construction industry" (रस्ते तयार करणे, देखरेख करणे, बांधकाम उद्योग), **01.07.2026–31.12.2026**, ₹/month (basic + special allowance ₹3,198) | Unskilled **22,463 / 21,598 / 20,728** (Zones I/II/III)<br>Semi-skilled **23,543 / 22,673 / 21,808**<br>Skilled (includes highly skilled) **25,058 / 24,188 / 23,323** | Notification No. RuralDevelopment/MWRules/Special Allowance/2026(2)/office-10/**7997**, dated **05.08.2026**, Office of the Commissioner of Labour, issued "under the Minimum Wages" framework by the Dy. Labour Commissioner "& Competent Authority under the Minimum Wages Act, 1948" **[V-secondary]**: English translation hosted by SGCMS ([PDF](https://www.sgcms.com/regulatory-updates/wp-content/uploads/2026/08/Translation-revised-DA-Notification-w.e.f-01.07.2026-to-31.12.2026.pdf)). **The original Marathi notification must be verified.** |
| Cross-check: Maharashtra Jan–Jun 2025 | Same basic rates; special allowance ₹2,378 (e.g., unskilled Zone I ₹21,643) | Official PDF, 20.02.2025 **[V]** |
| **Central sphere**, construction/maintenance of roads, runways, buildings and specified utility works, from **01.10.2026**, ₹/day | Unskilled **840 / 704 / 565** (Areas A/B/C)<br>Semi-skilled 933 / 794 / 661<br>Skilled 1,024 / 933 / 794<br>Highly skilled 1,111 / 1,024 / 933 | Consolidated table **[V-secondary]** ([staffnews PDF](https://www.staffnews.in/wp-content/uploads/2026/10/Minimum-Wages-VDA-order-October-2026.pdf)); issuing office unconfirmed |

**Daily equivalent:** Maharashtra Zone I unskilled = ₹22,463 ÷ 26 = **₹863.96**. The ÷26 divisor for the *state* notification is an assumption to verify; it follows the central-rules convention.

**Before computing anything, confirm:**
1. State vs. central sphere.
2. Scheduled employment (construction, SN 11).
3. Skill category; Maharashtra folds "highly skilled" into skilled.
4. **Zone of the site.** Zone I = municipal corporation limits, cantonments, and industrial areas within 20 km — this definition comes from a summary of the general notification **[V]** ([SGCMS](https://www.sgcms.com/regulatory-updates/minimum-rate-of-wages-maharashtra-august-2026/)); verify it for the construction schedule.
5. Work dates against the rate's validity window.
6. Components included (basic + special allowance).
7. Daily divisor (26) and normal hours (8) for Maharashtra.
8. Time-rated vs. piece-rated work. The MVP handles time-rated work only.

**Claim forum:**
- Code on Wages s.45 **[V]** ([text](https://aaptaxlaw.com/code-on-wages-2019/section-45-claims-under-code-and-procedure-thereof-code-on-wages-2019.html)):
  - an authority of at least Gazetted rank hears claims;
  - claims can be filed by the employee, a registered union the employee belongs to, or the Inspector-cum-Facilitator;
  - **a single application can cover many employees** of one establishment (s.45(5));
  - limitation is **3 years**, extendable for sufficient cause;
  - compensation of up to **10×**; the authority aims to decide within 3 months; it has civil-court powers.
- Which authority and form Maharashtra uses during the transition is **unknown** → ask the District Legal Services Authority (DLSA) or labour office (§3.10).

**Payment deadlines (s.17):**
- daily wage period: end of shift;
- weekly: last working day before the weekly holiday;
- fortnightly: within 2 days after the fortnight;
- monthly: before the 7th of the next month;
- on exit or termination: within 2 working days **[V]** ([s.17](https://www.advocatekhoj.com/library/bareacts/codeonwages/17.php)).

**Overtime:** at least **twice the normal rate** for hours beyond the normal working day (s.14) **[V]** ([s.14](https://www.advocatekhoj.com/library/bareacts/codeonwages/14.php)).

**Other relevant law:**
- **Free legal aid:** "an industrial workman" is eligible under the Legal Services Authorities Act s.12(f) **[V]** ([link](https://www.advocatekhoj.com/library/bareacts/legalservicesauthorities/12.php)).
- **Electronic evidence:** a BSA s.63(4) certificate has Part A (filled by the party, including the **hash value**) and Part B (by an expert). The Supreme Court declined the challenge in *Pune Bar Association v UoI* (order of 22 May 2026), calling a hash value "an electronic fingerprint" **[V]** ([LiveLaw](https://www.livelaw.in/amp/top-stories/supreme-court-rejects-challenge-to-s634-bsa-mandating-hash-value-disclosure-for-electronic-evidence-535950)).
- **Welfare registration:** MahaBOCW registration needs a **90-day work certificate**. A CAG audit found contractors issuing them improperly in bulk **[S]** ([CAG](https://cag.gov.in/uploads/download_audit_report/2025/8-Chapter-3-0693e9ae0b537b6.57830736.pdf)). Apna Hisaab's day count can *support* a certificate request; it cannot replace one.


**Models** (from the strategy report §6.3):

#### 6.3 Models to name in the proposal and README (verified on Hugging Face or primary repos)

| Role | Exact model | Params | License / terms (link) | Runtime | Status |
|---|---|---|---|---|---|
| **ASR, Hindi and Marathi (primary)** | **AI4Bharat IndicWhisper** (Vistaar) — `hindi_models`, `marathi_models` (Whisper-medium fine-tunes) | **≈763.9M each** (Whisper-medium architecture per [HF](https://huggingface.co/openai/whisper-medium); confirm from checkpoint config) | **MIT** — [github.com/AI4Bharat/vistaar](https://github.com/AI4Bharat/vistaar) ("license applies to all the fine-tuned language models") | faster-whisper int8_float16 | Ungated zip download → convert to CTranslate2 pre-build |
| **ASR multilingual / code-mix fallback** | **OpenAI Whisper large-v3-turbo** (CT2: `deepdml/faster-whisper-large-v3-turbo-ct2`) | **808.9M** | **MIT** — [HF card](https://huggingface.co/openai/whisper-large-v3-turbo) | faster-whisper int8_float16 | Ungated |
| **LLM (structuring, claim parsing)** | **Qwen3-4B-Instruct-2507**, GGUF Q4_K_M (2.50 GB, `unsloth/Qwen3-4B-Instruct-2507-GGUF`) | **4,022.5M** | **Apache-2.0** — [HF card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) | llama.cpp `llama-server`, JSON schema, T=0 | Ungated |
| **TTS (read-back)** | **AI4Bharat Indic Parler-TTS** (`ai4bharat/indic-parler-tts`; includes hi, mr, bn, or) | **937.8M** | **Apache-2.0** — [HF card](https://huggingface.co/ai4bharat/indic-parler-tts) | transformers + parler-tts, fp16 GPU | **Gated (auto-accept): accept terms tonight** |
| Challenger (decide by benchmark) | **Google Gemma 4 E4B-it** | 4.5B effective / 8B with embeddings (HF: 7,996.2M) | **Apache-2.0** — [Gemma 4 license](https://ai.google.dev/gemma/docs/gemma_4_license) | GGUF Q4_K_M 4.98 GB + mmproj 0.99 GB; audio ≤30 s; image OCR | Ungated |
| 4 GB / CPU tier LLM | Qwen3-1.7B (GGUF Q4_K_M) | 2,031.7M (HF count) | Apache-2.0 — [HF](https://huggingface.co/Qwen/Qwen3-1.7B) | llama.cpp | Ungated |
| CPU tier ASR | Whisper small | 241.7M | Apache-2.0 per [HF](https://huggingface.co/openai/whisper-small) metadata | faster-whisper int8 CPU | Ungated |
| Stretch: English gloss | IndicTrans2 indic-en dist-200M | 228.3M | MIT — [HF](https://huggingface.co/ai4bharat/indictrans2-indic-en-dist-200M) | transformers | Gated (request) |

**Considered and not used:**
- AI4Bharat IndicConformer-600M: MIT, but **gated, and our HF account was denied access**; unbenchmarked.
- Vosk: Marathi model unverified.
- Meta MMS: CC-BY-NC.
- Gemma 4 12B: 11.96B params ("large" by Rule 4.1) and too big alongside ASR and TTS.


**Hardware tiers** (from the strategy report §6.5):

#### 6.5 Hardware fit (you confirmed: target 8 GB, with 4 GB and CPU fallbacks)

| Tier | ASR | LLM | TTS | Estimated VRAM/RAM **[E]** | Latency target per entry **[E]** |
|---|---|---|---|---|---|
| **A: 8 GB NVIDIA (demo)** | IndicWhisper CT2 int8_float16 (~1 GB) | Qwen3-4B Q4_K_M 2.5 GB + KV ~0.3–0.6 GB | Parler-TTS fp16 ~1.9 GB | ~6–7 GB including CUDA contexts → fits; verify with `nvidia-smi` | ≤12 s to card; ≤5 s read-back |
| **B: 2–4 GB NVIDIA (Anuskha's laptop)** | int8 on GPU (~1 GB) | Qwen3-1.7B Q4 on GPU, or 4B partially offloaded | CPU or pre-generated phrase clips | ~3–3.5 GB VRAM | ≤30 s |
| **C: CPU only (Akash's i3-6006U, 8 GB RAM)** | Whisper small int8 | Qwen3-1.7B Q4 on CPU | Off; on-screen card + replay recording | ~4–5 GB RAM | 60–120 s (hub batch mode; demo via pre-processed data and video) |

**Requirements:**
- CUDA-capable NVIDIA GPU (RTX-class recommended) with a current driver.
- ≥16 GB system RAM recommended (8 GB minimum); ≥30 GB free SSD.
- **Python 3.11 or 3.12.** The i3 laptop has 3.14.3, which many ML wheels may not support yet.
- Node 22 LTS.

**If the GPU differs:**
- AMD or Intel GPU → llama.cpp Vulkan build for the LLM; ASR and TTS on CPU (or pre-processed).
- 6 GB NVIDIA → lazy-load or unload TTS.
- ≥12 GB → Gemma 4 E4B becomes viable as both ASR and LLM.
- **Decisively better beyond the ceiling:** a 12–16 GB GPU would allow Gemma 4 E4B plus IndicTrans2 resident together. Nice, not needed.


**Build-day schedule** (from the strategy report §7.3):

#### 7.3 Build day: Sat 17 Oct, 07:00–17:00, at the college (solo build, with Claude Code as a coding assistant)

> **Superseded:** the build day is Fri 16 Oct. Use the phases, checkpoints and cut line in [`BUILD_PLAN.md`](BUILD_PLAN.md) §3–§4. The table below is kept for reference only.

**Confirmed by the coordinators:** own laptop allowed; power sockets available; **internet available throughout**; submit **repo + README**; **judges come to your desk and judge on the spot**.

**Confirmed by you:** you are building **solo**, with Claude Pro (usage-limited, one reset) as your coding assistant. Using an AI coding assistant is a development tool, not the product's core AI (Rule 4.5). **Disclose it in the README.**

**Solo working rules:**
- At 07:00, give `IMPLEMENTATION_HANDOFF.md` §10 to Claude Code as the spec.
- Ask for **one module at a time, with tests**, and review every diff before moving on.
- **Budget Claude usage:**
  - ~40% before CP2 (engine + tests, normalizer + reconciler, API skeleton, React shell);
  - ~40% for 12:20–15:00 (packet, Saathi, PWA);
  - keep the **reset for after 15:00** bug-fixing.
  - If you hit the limit, hand-code from the spec. The product's own models run locally and don't depend on Claude.
- Internet is available, but **rehearse with the laptop's Wi-Fi off**. Switch it on only for `git push` and for the WhatsApp step on the phone.

| Time | Build (you + Claude Code) | Checkpoint |
|---|---|---|
| 07:00–07:30 | Start `llama-server`; ASR and TTS smoke tests; scaffold backend (FastAPI) and frontend (Vite React + `vite-plugin-pwa`); regenerate the mkcert certificate for the laptop's current LAN IP | Models respond |
| 07:30–09:00 | SQLite + hash chain; **wage engine + fixtures F1–F9**; rate-pack loader and resolver | `pytest` green |
| 09:00–10:30 | Upload → save + hash → ASR → normalizer → LLM extraction → reconciler; process and confirm APIs | **CP1 10:30:** 1 hi + 1 mr clip → correct, colour-coded fields via an HTTP client |
| 10:30–12:00 | React: record (**flexible length**, plus a one-tap **"Same as yesterday / कालसारखं"**), confirm card, pickers, ledger, hisaab view; TTS read-back; **HTTPS** so the phone's microphone works | **CP2 12:00: MUST path end-to-end on the laptop with Wi-Fi off; phone opens the app over HTTPS** |
| 12:00–12:20 | Lunch | — |
| 12:20–14:00 | Packet (HTML → PDF + ZIP manifest); demo **reset/seed script**; **Saboot** (excerpts) + **Bhejo** (risk note, Web Share / `wa.me`); voice hisaab check | — |
| 14:00–15:00 | **Samjhao** (template + 13 FAQ intents); **Bol ke Batao** statement (reply recording and promise log if time allows); **install the PWA on the phone** | **CP3 15:00: feature freeze; Wi-Fi-off rehearsal; reset script works** |
| 15:00–16:00 | Edge cases; tamper demo; measured latencies; README (models, params, licenses, disclosures, measured numbers); screenshots; **backup video** | — |
| 16:00–16:40 | Rehearse the **3-min desk demo** and the **6-min full demo** ×3; Q&A drill (§8.4) | — |
| 16:40–17:00 | Final push; verify the repo is public, README renders, LICENSE present; **leave the app running for judges** | Done |

**At every checkpoint, ask:**
1. Can I demo the MUST path offline right now?
2. What is the slowest step?
3. What can I cut with the least damage to the story?
4. Is my work committed?

**Solo cut line, in order, applied at CP2 if behind:**
1. Bol ke Batao reply recording and promise log (keep the ▶ statement).
2. Samjhao FAQ Q&A (keep the explanation).
3. Coach and s.17 flags.
4. Voice hisaab-check → manual contractor-claim form.
5. Web Share → download + `wa.me` link.
6. PWA install (keep the HTTPS mobile web page).
7. TTS → on-screen card + replay of the recording.
8. Playwright → browser Print-to-PDF.
9. Marathi → Hindi-only (last resort).

**Protect at all costs:** the MUST path plus Saboot and the Bhejo prompt.

**Because judges come to your desk at any time:**
- Keep the app running all afternoon, with a **one-command demo reset** that re-seeds the synthetic data.
- Put a **printed A4 sheet** on the desk: models with params and licenses, the architecture, the legal basis, and the "synthetic data" note.
- Have both a 3-min and a 6-min version of the demo ready.

**Riskiest assumption, tested first** (15 Oct, and again at 09:00 on the day): phone-recorded Hindi and Marathi notes give times, amounts and names with **≤1 correction per entry** typically, within **≤12 s on the GPU laptop**. If this fails, use **tap-first** capture for numbers and keep voice for narrative and identities.

**Acceptance criteria AC1–AC20, edge cases and demo script:** see the strategy report §8.1–§8.3.

---

## 10. Implementation-agent handoff (self-contained build brief)

### 10.0 Hard constraints (read first)

1. **Write product code only on Build Day (17 Oct 2026).** Before that: environment setup, downloads, benchmarks, data and design only (Rule 5). Disclose prep in the README.
2. **No closed AI APIs anywhere.** All inference uses open-weight models on our own hardware: the laptop, our own cloud GPU, or the phone. *(v2: internet is allowed for the online tier and for Telegram as a message transport. Capture still works offline; see BUILD_PLAN §3 P2 and P5.)* No CDNs (bundle fonts and icons); no telemetry.
3. **The LLM extracts; code computes.** No LLM arithmetic, legal reasoning or free-text read-back.
4. **Never invent values.** A field without a transcript quote is `null`. Unconfirmed values never enter computations.
5. **Audio is saved and hashed before any processing.**
6. **Synthetic demo data only**, watermarked. No real people or real builders.
7. Languages: **Marathi and Hindi** (including Hinglish) for the worker; English for the paralegal view and packet labels.
8. Repo license: **Apache-2.0.** Never commit model weights.
9. **The AI never argues, phones or negotiates with the thekedar.** *(v2: the Telegram agent in BUILD_PLAN §7 may message him, but only with code-filled templates. It introduces itself and says the chat is recorded, and a hostile message gets no reply.)* Bol ke Batao speaks only fixed templates when the worker presses play. Recording him always begins with a spoken notice that can't be skipped (BUILD_PLAN §8).
10. **Nothing is sent without the worker's choice.** Bhejo is worker-initiated, shows a risk note, excludes witness audio by default, and logs every share. *(v2: Telegram daily updates are sent automatically only while the worker's `auto_daily` setting is on, and the worker can turn it off.)*
11. **Serve over HTTPS** (mkcert cert for the laptop's LAN IP + localhost; root CA installed on the demo phone). `getUserMedia` (microphone), service workers (PWA install) and Web Share **do not work on plain-HTTP LAN origins**. Regenerate the cert at 07:00 if the venue IP differs.
12. The **app shell must work offline once installed** (service worker precache). If the hub is unreachable, recordings queue in IndexedDB on the phone and upload when it is reachable again. **Audio is never lost.** *(v2: the phone also hashes the audio and photo in the browser, captures GPS, and may process with on-device models; the server re-processes when back online. See BUILD_PLAN §3 P2/P5.)*

### 10.1 Direction

Build **Apna Hisaab**, a voice-first, offline worker ledger. A daily voice note in Hindi or Marathi is transcribed (IndicWhisper / Whisper turbo), structured (Qwen3-4B, schema-constrained), checked by a deterministic normalizer, read back (Indic Parler-TTS) and confirmed by the worker, then stored in a hash-chained SQLite ledger. A deterministic wage engine compares confirmed work and pay against a provenance-stamped Maharashtra rate pack. At payday, a "hisaab check" compares the contractor's spoken settlement against the ledger. A bilingual, hash-indexed evidence packet is exported for a paralegal.

A worker-controlled **Hisaab Saathi** voice agent (spec in §10.20) then:
- explains the result aloud;
- plays the exact proof excerpt for each difference;
- asks before sharing it on WhatsApp;
- can speak a fact-only statement to the thekedar, logging any promise from his announced, recorded reply.

### 10.2 Stack and repo layout

- **Backend:** Python 3.11, FastAPI, uvicorn, sqlite3 (WAL), faster-whisper, llama.cpp `llama-server` (separate process, OpenAI-compatible, JSON schema), transformers + parler-tts, Jinja2, Playwright (Chromium) for PDF, pytest.
- **Frontend:** React + Vite + **`vite-plugin-pwa`** (manifest with name, short_name, hi/mr-friendly icons, `display: standalone`; Workbox precache of the app shell) + `idb-keyval` for the offline recording queue.
- FastAPI serves the built files and the API on **one HTTPS origin**: `uvicorn --ssl-certfile/--ssl-keyfile` with the mkcert files. A single origin avoids CORS and mixed-content problems.

```
apna-hisaab/
  LICENSE (Apache-2.0) · README.md · .gitignore (models/, data/, media/, *.gguf, *.bin)
  backend/app/{main,config,db,events,asr,normalize,extract,reconcile,tts,rates,wage_engine,coach,hisaab,packet,saathi}.py
  backend/app/content/{faq.hi.json, faq.mr.json, samjhao.{hi,mr}.json, statement.{hi,mr}.json, risk_note.{hi,mr}.json}
  backend/app/templates/{packet.html.j2, readback.hi.json, readback.mr.json}
  backend/rate_packs/MH_SN11_construction_2026H2.json   (+ central_construction_2026-10.json: stretch)
  backend/tests/{test_wage_engine,test_normalize,test_reconcile,test_events}.py + fixtures/
  frontend/src/{screens/*, components/*, i18n/{hi,mr,en}.json}
  frontend/public/{fonts/NotoSansDevanagari*.woff2, audio/prompts/{hi,mr}/*.wav}
  scripts/{download_models, seed_demo}.*   docs/{architecture.png, benchmark.md, prep-disclosure.md}
```

### 10.3 Data model (SQLite)

> **v2:** add the columns, tables, events and schemas in [`BUILD_PLAN.md`](BUILD_PLAN.md) §5: GPS, photo kinds, `client_sha256`, `speaker`, `coworker_confirm`, the Telegram tables and the `thekedar_reply` schema.

- `workers(id TEXT PK, display_name, language 'hi'|'mr', category 'unskilled'|'semi_skilled'|'skilled'|'highly_skilled'|NULL, default_break_min INT NULL, pin_hash, consent_keep_audio BOOL, created_at)`
- `sites(id PK, worker_id, name, landmark, city, state, sphere 'state'|'central'|'unknown', zone 'I'|'II'|'III'|NULL, zone_confirmed BOOL, principal_employer NULL, maharera_no NULL)`
- `parties(id PK, worker_id, site_id, role 'mukadam'|'contractor'|'subcontractor'|'principal_employer', name NULL, phone NULL, source 'stated'|'site_board')`
- `entries(id PK, worker_id, site_id, kind 'workday'|'payment'|'hisaab_statement'|'witness', audio_path, audio_sha256, client_ts, server_ts, status 'saved'|'processed'|'confirmed'|'deleted', transcript, asr_meta JSON, extraction JSON, reconciled JSON, confirmed JSON, confirmed_at)`
- `evidence(id PK, worker_id, kind 'photo'|'witness_audio', path, sha256, caption, consent BOOL, created_at)`
- `events(seq INTEGER PK AUTOINCREMENT, worker_id, ts_server, ts_client, type, payload_json, prev_hash, hash)`, **append-only**. Event types:
  - `AUDIO_SAVED`, `ENTRY_PROCESSED`, `ENTRY_CONFIRMED`, `FIELD_EDITED`
  - `PAYMENT_CONFIRMED`, `EVIDENCE_ADDED`
  - `SITE_SET`, `PARTY_SET`, `RATE_CONTEXT_CONFIRMED`
  - `ENTRY_DELETED` (tombstone), `EXPORT_CREATED`, `ANCHOR_SENT`
  - Saathi: `EXCERPT_CREATED`, `SHARE_PREPARED`, `STATEMENT_PLAYED`, `REPLY_RECORDED`, `PROMISE_LOGGED`, `HOSTILE_STOP`
- Saathi tables:
  - `excerpts(id, entry_id, parent_sha256, start_s, end_s, path, sha256, phrase)`
  - `shares(id, recipient_role 'thekedar'|'union'|'other', items JSON[{type, sha256}], channel 'whatsapp', status 'prepared'|'handed_off', created_at)`
  - `promises(id, worker_id, source_entry_id, amount, due_date, date_status, confirmed BOOL, reminder_at)`
- `exports(id PK, worker_id, period_from, period_to, pdf_path, zip_path, manifest_sha256, chain_head, rate_pack_sha256, created_at)`

### 10.4 LLM extraction contract (llama-server, `response_format` JSON schema, temperature 0)

**Shared field shape:** `{"value": <typed|null>, "evidence": <exact transcript substring|null>}`.

| Kind | Fields |
|---|---|
| **workday** | `work_date`, `start_time` (HH:MM), `end_time`, `break_minutes`, `worked` ('yes'/'no'/'unknown'), `site`, `contractor_name`, `contractor_phone`, `principal_employer`, `work_type`, `agreed_rate` {value, unit 'day'/'month'/'job'}, `coworkers_present` [{name, evidence}], `incidents` [text], `notes` |
| **payment** | `payment_date`, `amount_paid`, `payment_mode` ('cash'/'upi'/'bank'/'unknown'), `payer_name`, `covers_from`, `covers_to`, `deductions` [{amount, reason, evidence}] |
| **hisaab_statement** | `days_counted`, `rate_per_day`, `gross_amount`, `deductions` [{amount, reason, evidence}], `paid_now`, `balance_promised`, `promised_date` |

**System-prompt rules (design spec):**
- "You copy facts from a construction worker's voice-note transcript."
- Every value must quote the transcript in `evidence`; if it isn't said, use null.
- Do not compute totals or convert units. Do not resolve relative dates; return the words (e.g., "कल").
- Output only JSON matching the schema.

Include 5 few-shot examples (2 hi, 2 mr, 1 Hinglish), prepared as content before the day.

The context includes the recording date and the worker's defaults **labelled as context, not facts**.

### 10.5 Normalizer (deterministic, `normalize.py`)

- **Digits:** Devanagari ०–९ → 0–9.
- **Number words:** hi and mr cardinals 0–100, सौ/शंभर, हज़ार/हजार, compounds ("दोन हजार पाचशे" = 2500).
- **Fractions:** सवा/सव्वा +¼, साढ़े/साडे +½, पौने/पावणे −¼, डेढ़/दीड 1½, ढाई/अडीच 2½.
- **Parts of day:**
  - सुबह/सवेरे/सकाळी → AM
  - दोपहर/दुपारी → 12–16
  - शाम/संध्याकाळी → 16–20
  - रात/रात्री → 20–04
- **Workday heuristic:** "9 से 7" without a part of day → 09:00–19:00 with status `inferred` (amber).
- **Dates:**
  - आज → recording date (green)
  - mr काल → yesterday (green)
  - hi कल, hi परसों, mr परवा → `ambiguous` (amber; ask)
  - "13 तारीख" → most recent past 13th (`inferred`)
- **Money:** "500 रुपये", "पाँच सौ", "पांचशे" → 500.
- **Output:** `{field: {value, status: 'stated'|'inferred'|'ambiguous', span}}`.

### 10.6 Reconciler (deterministic, `reconcile.py`)

1. **Grounding:** after whitespace and digit normalisation, `evidence` must be a substring of the transcript; otherwise the value becomes null and the field is flagged `UNGROUNDED`.
2. **Two readers:** for date, time and money fields, LLM == normalizer → green; one missing → amber (prefill); disagree → amber with both candidates; neither → red.
3. **ASR confidence:** if the evidence span lies in a segment with `avg_logprob < −1.0` or `no_speech_prob > 0.5` (tunable), the field becomes amber.
4. **Plausibility:**
   - end > start (otherwise flag `OVERNIGHT?`);
   - hours ≤ 16;
   - amount ≤ ₹5,000 per day (flag only);
   - date not in the future;
   - date ≥ recording date − 7 days (otherwise `LATE_ENTRY`).
5. **Defaults** (usual break, site, contractor) fill only **missing** fields and are always shown amber: "assumed — confirm".

### 10.7 Wage engine (`wage_engine.py`, pure functions, **exact rational arithmetic**)

- Use `fractions.Fraction` internally. Convert to `Decimal` with `ROUND_HALF_UP` to 2 decimals **only for display and final totals**. F5 catches the float/Decimal-division bug.
- **Inputs:** confirmed workdays (date, start, end, break) · confirmed payments · rate context (sphere, state, employment SN, category, zone, all confirmed) · optional agreed rate per day · wage period (daily/weekly/fortnightly/monthly/unknown).
- **Per day:**
  - `daily_min = monthly_total / divisor(26)`; `hourly = basis / normal_hours(8)`;
  - `hours = (end − start) − break`; `normal = min(hours, 8)`; `ot = max(0, hours − 8)`;
  - `basis = max(daily_min, agreed_daily)` if an agreed rate is known, else `daily_min`;
  - `due = basis × normal/8 + ot × (basis/8) × 2` (s.14: ≥2× the normal rate);
  - statutory-only due uses `daily_min` as the basis;
  - partial day (<8 h) is pro-rated and flagged `PARTIAL_DAY` (the paralegal checks whether full-day rules apply).
- **Totals:**
  - `due_statutory`, `due_contractual` (if an agreed rate is known), `paid_total`;
  - `shortfall_statutory = max(0, due_statutory − paid)`; `shortfall_contractual` likewise;
  - `claim_estimate = max` of the two, labelled "estimate".
- **Form II head mapping:** 3(a) paid below minimum · 3(c) overtime unpaid · 3(d) days with no payment · 3(e) deductions (as worker-reported). 3(b) weekly-rest wages, bonus and compensation are listed as **"not computed — authority decides"**.
- **s.17 late-payment flags:** per wage period, with payments allocated FIFO to unpaid days (flagged as an assumption).
- **Errors (no amounts shown):** `RATE_NOT_FOUND`, `RATE_OUT_OF_WINDOW`, `ZONE_UNCONFIRMED`, `CATEGORY_UNKNOWN`, `SPHERE_UNKNOWN`, `PIECE_RATE_UNSUPPORTED`, `NO_CONFIRMED_DAYS`.
- **Fixtures** (Maharashtra Zone I unskilled; monthly 22,463 → daily 863.9615…; hourly 107.9952…):

| ID | Scenario | Expected |
|---|---|---|
| F1 | 1 day, 8 h, paid ₹700 | due **863.96**; shortfall_statutory **163.96** |
| F2 | 09:00–19:00, break 60 (9 h) | due **1,079.95** (= daily × 1.25) |
| F3 | 4 h | due **431.98**, `PARTIAL_DAY` |
| F4 | 8 h, paid 0 | shortfall **863.96**, head 3(d) |
| F5 | 13 × F2; payments 2,000 + 2,500 | due **14,039.38** (exact 14,039.375); shortfall **9,539.38** |
| F6 | date 2027-01-05 | `RATE_OUT_OF_WINDOW` |
| F7 | zone NULL | `ZONE_UNCONFIRMED` |
| F8 | agreed ₹1,000/day, 9 h | basis 1,000 → due **1,250.00**; statutory 1,079.95; estimate 1,250.00 |
| F9 | weekly period, Mon–Sat worked, Sunday holiday, paid next Wed | `LATE_PAYMENT` (due Sat; 4 days late) |

### 10.8 Rate pack (`rate_packs/MH_SN11_construction_2026H2.json`; data, verify before use)

```json
{"pack_id":"MH-SN11-2026-07-01_2026-12-31","sphere":"state","state":"Maharashtra",
 "employment":{"sn":11,"en":"Road construction, maintenance, construction industry","mr":"रस्ते तयार करणे, देखरेख करणे, बांधकाम उद्योग"},
 "effective_from":"2026-07-01","effective_to":"2026-12-31","unit":"INR_per_month",
 "rates":{"unskilled":{"I":[19265,3198,22463],"II":[18400,3198,21598],"III":[17530,3198,20728]},
          "semi_skilled":{"I":[20345,3198,23543],"II":[19475,3198,22673],"III":[18610,3198,21808]},
          "skilled":{"I":[21860,3198,25058],"II":[20990,3198,24188],"III":[20125,3198,23323]},
          "highly_skilled":"same_as_skilled"},
 "rate_tuple":["basic","special_allowance","total"],
 "conversion":{"daily_divisor":26,"normal_hours":8,"ot_multiplier":2,"status":"ASSUMED_VERIFY_FOR_STATE"},
 "zones":{"I":"Municipal corporation limits, cantonments, industrial areas within 20 km (verify for this schedule)","II":"A/B class municipal councils (verify)","III":"Rest of state"},
 "source":{"notification_no":"RuralDevelopment/MWRules/Special Allowance/2026(2)/office-10/7997","date":"2026-08-05",
   "issuer":"Office of the Commissioner of Labour, Mumbai — Dy. Labour Commissioner (Rural Development) & Competent Authority under the Minimum Wages Act, 1948",
   "documents":[{"title":"English translation (SGCMS)","url":"https://www.sgcms.com/regulatory-updates/wp-content/uploads/2026/08/Translation-revised-DA-Notification-w.e.f-01.07.2026-to-31.12.2026.pdf","retrieved":"2026-10-13"}],
   "verification_status":"SECONDARY_TRANSLATION_VERIFY_ORIGINAL"}}
```

Store the pack's SHA-256 in every export. The UI shows `verification_status` wherever amounts appear.

### 10.9 Hash chain (`events.py`)

- `canonical = json.dumps(event_without_hash, sort_keys=True, ensure_ascii=False, separators=(",",":")).encode("utf-8")`
- `hash = sha256(prev_hash_hex.encode() + canonical).hexdigest()`; genesis `prev_hash = "0"*64`.
- Audio SHA-256 is computed on the **original uploaded bytes**, before transcoding, and included in `AUDIO_SAVED`.
- Chain-head short code: first 10 hex characters, grouped `7F3A-9C21-B4`.
- `verify()` recomputes everything and returns `{ok, broken_at_seq}`.
- Edits are new events; the old payload is never mutated.
- Deletion: `ENTRY_DELETED` with `{entry_id, content_sha256}`; content is purged from the entries and media tables.

### 10.10 API (FastAPI)

| Method & path | Purpose |
|---|---|
| `POST /api/entries/audio` (multipart: audio, kind, worker_id, client_ts) | Save + hash → `{entry_id, audio_sha256, status:"saved"}` |
| `POST /api/entries/{id}/process` | ASR → normalize → extract → reconcile → `{transcript, fields{value,status,color,candidates,evidence}, readback_text, readback_audio_url}` |
| `POST /api/entries/{id}/confirm` | `{fields}` → events → `{chain_head}` |
| `GET /api/ledger?worker_id&from&to` | Confirmed days and payments |
| `GET /api/hisaab?worker_id&from&to` | Engine output with provenance and errors |
| `POST /api/hisaab/statement` (audio) | Contractor-claim extraction + comparison + read-back |
| `POST /api/evidence/photo`, `POST /api/evidence/witness` | Hash + event (consent required for witness) |
| `GET /api/coach?worker_id` | Checklist status |
| `POST /api/export` | `{period}` → pdf + zip + manifest |
| `GET /api/chain/verify?worker_id` | `{ok, broken_at_seq}` |
| `DELETE /api/entries/{id}` | Tombstone |
| `GET /api/health` | Model load status, offline flags, tier |
| `GET /api/saathi/samjhao?worker_id&from&to` | Explanation lines (from the engine) + TTS audio URLs |
| `POST /api/saathi/ask` (audio) | ASR → intent → `{intent, answer_text, answer_audio_url}` or referral |
| `GET /api/saathi/proof?discrepancy_id` | Linked entries → excerpts `[{excerpt_id, audio_url, sha256, phrase, parent_sha256}]` |
| `POST /api/saathi/share` | `{recipient_role, item_ids, include_pdf}` → payload files + summary text + `wa_link` + `SHARE_PREPARED` |
| `GET /api/saathi/statement?worker_id&lang&include_min_wage` | Statement text + TTS audio (`STATEMENT_PLAYED` logged on play) |
| `POST /api/saathi/reply` (audio, after notice) | ASR → reply schema → `{reply_type, promise_amount, promise_date, evidence}` → confirm → `PROMISE_LOGGED` |

### 10.11 Frontend screens

1. **Language** (audio prompts).
2. **Consent** (audio + Yes/No for keeping audio).
3. **PIN.**
4. **Profile:** category pictures, site, sphere and zone confirm, contractor, usual hours and break, agreed rate.
5. **Home:** 🎙️ Work · 💵 Paid · 📒 Hisaab · 📁 Export.
6. **Record:** tap to start and tap to stop; **no minimum length**; soft cap 60 s (longer audio is chunked for ASR); "Saved ✓ #hash" appears immediately.
   - **One-tap "Same as yesterday / कालसारखं / कल जैसा"** creates today's entry from yesterday's confirmed hours, site and contractor. All fields start amber and the worker still confirms. It is logged as `ENTRY_CONFIRMED` with `source:"same_as_yesterday"`.
   - Voice is needed only for what differs.
7. **Confirm card:** icon chips; green/amber/red; tap to fix via picker or re-speak; ▶ read-back; ✅/✏️.
8. **Hisaab view:** totals, per-day table, "why?" drawer with formula and source, errors shown as needs.
9. **Hisaab check** (speak the settlement → itemised differences).
10. **Coach checklist.**
11. **Export:** period, preview, PIN, generate.
12. **Settings:** delete, wipe, PIN, verify chain.
13. **Saathi:**
    - Samjhao: ▶ explanation, 🎙️ ask a question.
    - Saboot: "▶ proof" on every discrepancy.
    - Bhejo: question → risk note → [Thekedar | Union | Not now] → tick clips → Share/Save.
    - Bol ke Batao: ▶ statement → "Record his reply?" → automatic notice → ⏺ with a big ■ Stop → promise card → ✅.
    - Promises list with reminders.

i18n keys in hi/mr/en; no external assets.

### 10.12 Read-back templates (deterministic; fill only with candidate values; unknowns spoken as unknown)

- **mr workday:** `"{date}: {start} ते {end}, {site}. ठेकेदार {contractor}. {break_phrase} बरोबर आहे का?"`
- **hi workday:** `"{date}: {start} से {end} तक, {site}. ठेकेदार {contractor}. सही है?"`
- **mr payment:** `"{date} रोजी {amount} रुपये {mode} मिळाले. बरोबर आहे का?"`
- **hi payment:** `"{date} को {amount} रुपये {mode} मिले. सही है?"`
- **Unknown fields:** mr `"{field} माहीत नाही"`, hi `"{field} पता नहीं"`.
- Use number words if the 15 Oct benchmark shows Parler misreads digits.
- Cache audio by SHA-256 of the text.

### 10.13 Packet (`packet.html.j2` → PDF + `bundle.zip`)

1. **Dues statement** (1 page, mr/hi + en): worker (nickname OK); contractor, sub-contractor and builder *as stated*; site; period; days; rate basis with citation; due, paid, estimate; disclaimer: "Prepared from the worker's own records; computed by fixed rules; not legal advice; not verified by any authority."
2. **Statement of facts:** a chronological, templated summary plus verbatim original-language transcripts (machine gloss labelled if present).
3. **Day-by-day table** in muster-roll-style columns: date, start, end, break, hours, OT, paid, mode, evidence IDs, confirmed-at, edits.
4. **Computation:** formulas, rate pack provenance and verification status, Form II heads 3(a)/(c)/(d)/(e), assumptions, "not computed" list.
5. **Evidence index:** item, type, SHA-256, device time (labelled), chain seq, anchors; chain head; device and app details (inputs for BSA s.63(4) Part A).
6. **Parties and liability note:** "contractor is an employer (Code s.2(l)); principal employer may be liable (OSH Code s.55; applicability varies): verify with legal aid".
7. **Where to go:** union or NGO; DLSA (LSA Act s.12(f)); claims authority (Code s.45; 3-year limit; group applications under s.45(5)).
8. **Declaration** with thumbprint box; witness declarations.

**Annex:** Form II field mapping (draft-era central form; Maharashtra form pending). Demo mode adds a "SYNTHETIC DEMO DATA" watermark.

### 10.14 Evidence coach checklist ("packet completeness N/12"; never a legal score)

1. Site name and landmark
2. Sphere and zone confirmed
3. Category confirmed
4. Contractor name
5. Contractor phone
6. Builder / principal employer or MahaRERA number (site-board photo)
7. Agreed rate and pay period (or "none agreed")
8. Confirmed coverage of claimed days (%)
9. Payments recorded (or "none received")
10. ≥1 witness statement
11. Hisaab statement recorded (if a settlement happened)
12. Chain anchor sent in the last 7 days

### 10.15 Task order (dependencies)

1. Contracts (schemas and endpoints)
2. DB + events
3. Wage engine + F1–F9 tests
4. Rate pack + resolver
5. ASR wrapper
6. Normalizer + tests
7. Extractor
8. Reconciler + tests
9. Process and confirm APIs
10. Record → confirm UI
11. Hisaab view
12. Packet + export
13. TTS read-back
14. Hisaab check
15. **Saathi:** Saboot → Bhejo → Samjhao → Bol ke Batao (statement first, then reply and promise)
16. Coach
17. Seed data
18. Tamper demo
19. README and docs

Steps 1–12 are the **MUST cut line**. Add **HTTPS + PWA manifest/service worker** inside step 10, since phone use depends on it.

**Solo build:** do the steps in order with Claude Code, one module per prompt, with tests. Pacing and checkpoints are in the §7.3 copy above (CP1 10:30, CP2 12:00, CP3 15:00).

### 10.16 Done / not-done acceptance checklist

- [ ] AC1–AC15 (§8.1) pass on Tier A, with Wi-Fi off.
- [ ] Demo script (§8.3) runs end-to-end twice in a row without a restart.
- [ ] Backup video recorded.
- [ ] **Phone check:** over HTTPS (valid lock), the app installs to the home screen. The mic records. With the hub unreachable, a recording queues and uploads later. "Same as yesterday" creates an amber entry that needs confirmation.
- [ ] Repo public; LICENSE present; README complete (§10.18).
- [ ] No model weights or personal data committed.
- [ ] `docs/benchmark.md` contains the *measured* numbers.

### 10.17 Must NOT build

- Closed AI APIs (open-weight models on our own cloud GPU are fine).
- ~~GPS or location tracking~~ → *v2: opt-in GPS per entry/photo is allowed; no continuous background tracking.*
- Covert recording.
- Employer-facing portals or public employer ratings.
- Automatic sharing of evidence files. *(v2 exception: Telegram daily-update templates while `auto_daily` is on.)*
- "Legally valid" or "proof" claims.
- LLM-generated legal text or arithmetic.
- Hardcoded or unverified rates without a status label.
- Real personal data in demo data.
- Blockchain.
- User accounts or cloud sync.
- Multi-device crypto attestation (deferred).
- **Any AI that talks freely to, argues with, phones or negotiates with the thekedar.** Bol ke Batao and the Telegram agent (BUILD_PLAN §7) are template-only.
- Recording without the spoken notice.
- Automatic or default sending of witness audio.
- Free-form LLM answers to legal questions (intent → pre-approved answers only).

### 10.18 README must include

- Problem and solution summary with screenshots.
- Architecture diagram.
- **Model table** (exact name, params, quantisation, license link; §6.3).
- "No closed AI API is used in the product."
- Disclosure of AI-assisted coding tools (Claude Code / Claude Pro, used as a development assistant only; no closed AI in the product).
- "Preparation before the event" list.
- Offline setup steps and a model download script.
- Hardware tested and **measured** latencies.
- Rate data sources with dates and verification status.
- Limitations (not proof; device clock; rates need verification; time-rated work only).
- Roadmap.
- License.

### 10.19 Implementation-agent checklist

Confirm offline model loads → implement in §10.15 order → run pytest after every engine or normalizer change → commit at each checkpoint (10:30 / 12:00 / 15:00) → Wi-Fi-off rehearsal at 15:00 → README and video by 16:00 → leave the app running for desk judging.

---

### 10.20 Hisaab Saathi (voice agent) spec: worker-controlled, "speak-for-me" mode chosen

**A. Samjhao (explain to the worker)**
- **Input:** `/api/hisaab` output plus hisaab-check discrepancies.
- **Output:** at most 6 lines from templates: DAYS, MIN_RATE, DUE_TOTAL, PAID_TOTAL, BALANCE_ESTIMATE, TOP_DIFFS (≤2 of MISSING_DAYS, BELOW_MIN, OT_UNPAID, DISPUTED_DEDUCTION), OPTIONS.
  - Numbers come only from the engine and are spoken as hi/mr number words.
  - The balance is always called an "estimate".
- **Voice Q&A:**
  - Flow: ASR → LLM with schema `{"intent": enum, "confidence": "high"|"low"}`.
  - Enum: `WHAT_IS_MIN_WAGE, WHY_THIS_AMOUNT, WHAT_IS_OVERTIME, WHAT_CAN_I_DO_NOW, WHERE_TO_COMPLAIN, IS_LEGAL_HELP_FREE, HOW_LONG_TO_CLAIM, WHAT_IF_I_GO_HOME, WILL_THEKEDAR_KNOW, IS_THIS_PROOF, IS_MY_DATA_SAFE, HOW_TO_DELETE, OUT_OF_SCOPE`.
  - `low` confidence or `OUT_OF_SCOPE` → the referral answer.
  - Answers are pre-written (≤3 sentences, hi/mr), reviewed against §3.5 (e.g., the 3-year limit under s.45; LSA s.12(f) free legal aid), and their audio is pre-generated.

**B. Saboot (exact proof clip)**
- **Discrepancy → entries:**
  - MISSING_DAY(date) → that day's workday entry;
  - BELOW_MIN or AGREED_RATE → the entry or onboarding item where the rate was stated;
  - payment differences → payment entries;
  - contractor's figures → the `hisaab_statement` entry.
- **Clip extraction:**
  - Take the confirmed field's evidence quote and find the ASR segment(s) containing it (normalised text; use `word_timestamps=True` spans when available).
  - Excerpt window = [start − 0.5 s, end + 0.5 s], clamped, capped at 15 s.
  - Cut with `ffmpeg -ss … -to … -i original … excerpt.opus`.
  - Log `EXCERPT_CREATED{entry_id, parent_sha256, start_s, end_s, sha256, phrase}`.
- **No match** → offer the full recording, labelled as such.

**C. Bhejo (ask, then share on WhatsApp)**
1. Ask (TTS): "क्या यह ठेकेदार को भेजना है?" / "हे ठेकेदाराला पाठवायचं का?" ("Should this be sent to the thekedar?")
2. Fixed risk note (TTS): "भेजने से ठेकेदार को पता चलेगा कि आप अपना हिसाब रखते हैं। पहले यूनियन या सहायक को भेजना ज़्यादा सुरक्षित हो सकता है।" ("Sending will let the thekedar know you keep your own records. Sending to the union or a helper first may be safer.")
3. Choices: Thekedar / Union-helper / Not now.
4. Payload:
   - recipient-specific polite summary (thekedar: facts and requests only, no legal language; union: plus estimate, chain code and PDF);
   - ticked excerpts (default: this discrepancy's clip);
   - **witness audio excluded unless opted in with a second warning**.
5. Transport:
   - if `navigator.canShare({files})` (needs **HTTPS/localhost**) → `navigator.share({files, text})` → Android share sheet → WhatsApp;
   - otherwise save the files and open `https://wa.me/<digits>?text=<urlencoded>` (or `https://wa.me/?text=…`).
   - Sending needs internet; WhatsApp queues it if offline.
6. Log `SHARE_PREPARED{recipient_role, items[{type, sha256}], channel:"whatsapp"}`. Status is "handed to WhatsApp"; delivery is not tracked.

**D. Bol ke Batao (speak for me), never a debate**
- **Statement template (hi):** "नमस्ते {thekedar}. {worker} के रिकॉर्ड में {days} दिन काम दर्ज है{period}. {diff}. अब तक {paid} रुपये मिले हैं. कृपया लिखित हिसाब और बाकी रकम की तारीख बता दीजिए. धन्यवाद."
  - English: "Hello {thekedar}. {worker}'s record shows {days} days of work{period}. {diff}. So far {paid} rupees have been received. Please give a written account and the date for the remaining amount. Thank you."
  - A Marathi equivalent is needed.
  - Optional opt-in line: "सरकारी न्यूनतम मज़दूरी {min} रुपये रोज़ है." ("The government minimum wage is {min} rupees a day.")
  - **Never** include threats, section numbers, penalties or accusations.
- **Reply capture:**
  - The worker taps "record his reply?" → the **notice is always played first**: "यह बातचीत रिकॉर्ड की जा रही है, ताकि हिसाब साफ़ रहे।" ("This conversation is being recorded so the account stays clear.")
  - Recording is ≤30 s with an instant ■ Stop.
- **Reply schema (LLM, T=0):**
  - `{"reply_type": enum[promise_to_pay, partial_payment_now, disputes_days, disputes_rate, refuses, hostile, other], "promise_amount": {value, evidence}, "promise_date": {value, evidence}, "notes"}`.
  - The grounding and two-reader rules apply to amounts and dates.
  - `hostile` → stop, `HOSTILE_STOP`, show union and helpline contacts.
  - A promise → card → the worker confirms → `PROMISE_LOGGED` plus an in-app reminder on the due date (offline).
- The app **does not generate any further reply to the thekedar.** The bounded responder is deferred.

**E. Content to prepare before build day (text only, kept in `planning/`):** FAQ answers, Samjhao, statement, notice and risk templates in hi/mr, each reviewed for factual accuracy against §3.5.


---

## Sources (opened this session unless marked [S]; dates as available)

**Competition:**
- Local `AboutHackthon/` files.
- Drive: [Problem Statements PDF](https://drive.google.com/file/d/14f1vSixLhcnhHyzD5qmSq8_AAFWDY4SG/view) (modified 5 Oct 2026); [Rulebook PDF](https://drive.google.com/file/d/1-bEAi8fsLj83uE3Lktqg11_pZV3aru2r/view) (modified 5 Oct 2026).

**Law and rates:**
- [EY alert, 21 Nov 2025](https://www.ey.com/content/dam/ey-unified-site/ey-com/en-in/alerts-hub/2025/11/new-labour-codes-implemented-across-the-country-effective-21-november-2025.pdf)
- Code on Wages (AdvocateKhoj bare act): [s.2](https://www.advocatekhoj.com/library/bareacts/codeonwages/2.php), [s.14](https://www.advocatekhoj.com/library/bareacts/codeonwages/14.php), [s.17](https://www.advocatekhoj.com/library/bareacts/codeonwages/17.php)
- [s.45 text (aaptaxlaw)](https://aaptaxlaw.com/code-on-wages-2019/section-45-claims-under-code-and-procedure-thereof-code-on-wages-2019.html)
- [PRS: Code on Wages (Central) Rules 2026](https://prsindia.org/billtrack/code-on-wages-central-rules-2026)
- [Taxmann chapter guide](https://www.taxmann.com/post/blog/wages-central-rules-2026-code-on-wages-chapter-wise-guide/)
- [SCC Online: Maharashtra draft rules, 1 May 2026](https://www.scconline.com/blog/post/2026/05/01/draft-maharashtra-code-on-wages-rules-notified/)
- [Form II (draft-era central forms)](https://cdn.taxguru.in/wp-content/uploads/2020/07/Code-on-Wages-Central-Rules-2020-Form.pdf)
- [Maharashtra Labour Dept homepage](https://mahakamgar.maharashtra.gov.in/) and its [Jan–Jun 2025 notification PDF](https://mahakamgar.maharashtra.gov.in/Site/Upload/Pdf/minimum-wages.pdf)
- [SGCMS page](https://www.sgcms.com/regulatory-updates/minimum-rate-of-wages-maharashtra-august-2026/) and [translation of notification 7997](https://www.sgcms.com/regulatory-updates/wp-content/uploads/2026/08/Translation-revised-DA-Notification-w.e.f-01.07.2026-to-31.12.2026.pdf)
- [Central-sphere Oct 2026 consolidated rates](https://www.staffnews.in/wp-content/uploads/2026/10/Minimum-Wages-VDA-order-October-2026.pdf)
- [PRS: OSH Code](https://prsindia.org/billtrack/the-occupational-safety-health-and-working-conditions-code-2020)
- [LSA Act s.12](https://www.advocatekhoj.com/library/bareacts/legalservicesauthorities/12.php)
- [LiveLaw on BSA s.63(4), 28 May 2026](https://www.livelaw.in/amp/top-stories/supreme-court-rejects-challenge-to-s634-bsa-mandating-hash-value-disclosure-for-electronic-evidence-535950)

**Worker evidence:**
- [Aajeevika, India Exclusion Report chapter](https://aajeevika.org/wp-content/uploads/2023/10/India-Exclusion-Report_Protection-of-Wages.pdf)
- [Citizen Matters, 22 Dec 2022](https://citizenmatters.in/labour-naka-ecosystem-thane-construction-worker-mumbai-informal/)
- [NDLON Jornaler@, 21 Nov 2016](https://ndlon.org/labor-organizations-launch-innovative-new-phone-app-to-redress-wage-theft-and-worker-abuses/)

**Models:**
- Hugging Face cards: [whisper-large-v3-turbo](https://huggingface.co/openai/whisper-large-v3-turbo), [whisper-medium](https://huggingface.co/openai/whisper-medium), [whisper-small](https://huggingface.co/openai/whisper-small), [faster-whisper turbo CT2](https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2), [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), [Qwen3-1.7B](https://huggingface.co/Qwen/Qwen3-1.7B), [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B), [Gemma 4 E4B](https://huggingface.co/google/gemma-4-E4B-it), [Gemma 4 E2B](https://huggingface.co/google/gemma-4-E2B-it), [Indic Parler-TTS](https://huggingface.co/ai4bharat/indic-parler-tts), [IndicTrans2 200M](https://huggingface.co/ai4bharat/indictrans2-indic-en-dist-200M), [IndicConformer (gated)](https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual)
- GGUF listings: unsloth Qwen3-4B / Gemma 4 E4B / E2B.
- [AI4Bharat Vistaar](https://github.com/AI4Bharat/vistaar)
- [arXiv 2605.03073](https://arxiv.org/abs/2605.03073)
- [Ollama gemma4](https://ollama.com/library/gemma4)

**[S] (search summaries only; pages not opened or blocked):**
- KPMG S.O. numbers
- PIB release (403)
- [Labour Ministry Compliance Handbook, Feb 2026](https://www.labour.gov.in/static/uploads/2026/02/83978455025732b99b0165def80ab171.pdf) (fetch failed)
- Jan Sahas report (blocked)
- NSS Telecom 2025 via PIB (403)
- MahaRERA display rules (housing.com; blocked)
- [CAG BOCW audit](https://cag.gov.in/uploads/download_audit_report/2025/8-Chapter-3-0693e9ae0b537b6.57830736.pdf)
- [DPDP Rules timeline (Mondaq)](https://www.mondaq.com/india/data-protection/1708164/digital-personal-data-protection-rules-2025-notified)
- Maharashtra draft-rules notification number (COW-0126/C.R.09/Lab7)
- Aajeevika "nine levels of middlemen"
- Whisper large-v3 Lahaja WER
