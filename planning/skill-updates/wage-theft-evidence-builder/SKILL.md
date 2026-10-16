---
name: "wage-theft-evidence-builder"
description: "Use when designing, coding, debugging, demoing or explaining the PS07 Migrant Worker Wage-Theft Evidence Builder for the OpenForge hackathon (Track 1)."
---

# PS07: Migrant Worker Wage-Theft Evidence Builder ("Apna Hisaab")

Project context: OpenForge Hackathon (SWAYAMBHU 2026, JNEC / MGM University), Track 1 "Open Weight AI & Open Source Tools".

- **Proposal deadline:** 13 Oct 2026, midnight (extended).
- **Final Build Day:** **Sat 17 Oct 2026, 07:00, 10 hours, at the college** (confirmed by coordinators). Own laptop, power and **internet available**. Submit **repo + README**; **judges assess at your desk**.
- **Builder:** solo (Akash), using Claude Code as a coding assistant; disclose it in the README.
- **Phone app:** must be installable as a **PWA over HTTPS** (mkcert), because phone mic, service worker and Web Share need a secure context.
- **Voice notes:** flexible length plus a one-tap "Same as yesterday".
- **Source of truth for details:** `planning/PS07_Strategy_Report.md` and `planning/IMPLEMENTATION_HANDOFF.md` in the project folder. Last verified 13 Oct 2026; these synced notes may be overwritten by a future skill sync.

## The product in one line
**Apna Hisaab**, "the worker's own hisaab", works like this:
1. A construction worker speaks a 20-second daily note in Hindi or Marathi.
2. Open-weight ASR transcribes it.
3. An open LLM structures it, and a deterministic numeral parser cross-checks it ("two-reader" check).
4. The app reads it back in the worker's language; the worker confirms.
5. The record is stored in a hash-chained offline ledger.
6. A deterministic wage engine compares work and pay against a provenance-stamped rate pack.
7. On payday, a "hisaab check" compares the contractor's spoken settlement against the ledger.
8. A bilingual, hash-indexed evidence packet is produced for a paralegal.

The **Hisaab Saathi** voice agent then:
- explains the result aloud (Samjhao);
- plays the exact proof clip behind each difference (Saboot);
- asks before sharing on WhatsApp (Bhejo);
- can speak a fact-only statement to the thekedar (Bol ke Batao).

## Non-negotiables (disqualification or safety risk)
- Open-weight AI is the foundation: ASR, LLM and TTS are all open models. **No closed AI APIs** (OpenAI/Gemini/Claude) in the product. Disclose AI-assisted coding in the README.
- Public GitHub repo, Apache-2.0. The README states the exact models, **parameter counts** and license links.
- **No product code before 17 Oct.** Prep (research, downloads, CLI benchmarks, rate-data transcription, synthetic audio, design content) is OK but must be disclosed.
- The LLM extracts; **code computes**. No LLM arithmetic, legal reasoning or free-text read-back.
- Never invent values. A field without a transcript quote is null; only worker-confirmed values count.
- Save and hash the audio **before** any AI call. Fully offline demo path.
- **The AI never debates, negotiates with or phones the thekedar** (rejected for retaliation, legal and ASR-reliability risk). Bol ke Batao plays fixed polite templates only when the worker presses play.
- Recording the thekedar's reply **always starts with a spoken notice**, with an instant Stop.
- Nothing is sent automatically. Bhejo asks first, plays a risk note, offers union-first, and excludes witness audio by default.
- No GPS, no covert recording, no employer portal or ratings. Synthetic demo data only.

## Hardware tiers (team decision, 13 Oct 2026)
| Tier | Machine | Models |
|---|---|---|
| A (demo) | NVIDIA, 8 GB VRAM (CUDA) | IndicWhisper CT2 int8_float16 (~1 GB) + Qwen3-4B Q4_K_M (2.5 GB) + Indic Parler-TTS fp16 (~1.9 GB) ≈ 6–7 GB total **(estimate; verify with nvidia-smi)** |
| B | Anuskha's NVIDIA 2–4 GB | ASR on GPU, Qwen3-1.7B, TTS on CPU or pre-generated clips |
| C | Akash's i3-6006U, 8 GB RAM, no CUDA | Whisper small int8 + Qwen3-1.7B on CPU; no TTS; demo via pre-processed data + video |

Use **Python 3.11/3.12**, not 3.14: many ML wheels may not support it yet.

## Stack and models (verified on Hugging Face or primary repos, 13 Oct 2026)
| Role | Model | Params | License |
|---|---|---|---|
| ASR hi/mr | AI4Bharat **IndicWhisper** (Vistaar; Whisper-medium fine-tunes; ungated zips → convert to CTranslate2) | ≈763.9M | MIT (github.com/AI4Bharat/vistaar) |
| ASR fallback / code-mix | **Whisper large-v3-turbo** (CT2: deepdml/faster-whisper-large-v3-turbo-ct2) | 808.9M | MIT |
| LLM | **Qwen3-4B-Instruct-2507** GGUF Q4_K_M (2.50 GB) via llama.cpp `llama-server`, JSON schema, T=0 | 4,022.5M | Apache-2.0 |
| TTS | **AI4Bharat Indic Parler-TTS** (gated: accept terms) | 937.8M | Apache-2.0 |
| Challenger | Gemma 4 E4B-it (audio ≤30 s; Q4_K_M 4.98 GB + 0.99 GB mmproj) | 4.5B eff / 8B | Apache-2.0 |
| Tier B/C | Qwen3-1.7B; Whisper small | 2,031.7M; 241.7M | Apache-2.0 |

- **Published WER (Vistaar):** IndicWhisper Hindi avg 13.6, Marathi 18.2, noisy Hindi (Gramvaani) 26.8. Still confirm all numbers with the worker.
- **Not used:** IndicConformer (gated; access denied); Meta MMS (CC-BY-NC); Vosk (Marathi unverified).
- **PDF:** Jinja2 HTML + bundled Noto Sans Devanagari → **Playwright/Chromium** PDF (fallback: browser Print-to-PDF). **Avoid ReportLab**, which mis-shapes Devanagari, and WeasyPrint, which is painful on Windows.
- **Backend:** FastAPI + SQLite (WAL). **Frontend:** React (Vite) mobile PWA, hi/mr/en, icons and audio prompts (or Jinja2 + HTMX if no React skill).

## Core pipeline
1. MediaRecorder (≤30 s) → save original bytes + SHA-256 → event `AUDIO_SAVED` → ffmpeg to 16 kHz WAV.
2. ASR (language forced from the worker profile) → transcript + segment confidences and timestamps.
3. **Normalizer** (deterministic):
   - Devanagari digits; hi/mr number words; सवा/साढ़े/पौने/डेढ़/ढाई and सव्वा/साडे/पावणे/दीड/अडीच;
   - parts of day;
   - Hindi "कल" and "परसों" and Marathi "परवा" are **ambiguous → ask**.
4. **LLM extraction:** schema fields shaped `{value, evidence}`, where `evidence` must be an exact transcript substring.
5. **Reconciler:**
   - grounding check (no quote → null);
   - LLM vs. normalizer agree → green, disagree → amber, missing → red;
   - low ASR confidence → amber;
   - plausibility checks;
   - profile defaults shown amber ("assumed — confirm").
6. Read-back from a **deterministic template** → Indic Parler-TTS → worker ✅/✏️ → hash-chained events.
7. Deterministic wage engine → hisaab view → packet → Saathi.

## Wage engine (deterministic, `fractions.Fraction`, round half-up only for display)
- **Per day:**
  - `daily = monthly_total / 26`; `hourly = basis / 8`;
  - `basis = max(daily_min, agreed_daily)`;
  - `due = basis × normal/8 + OT_hours × basis/8 × 2` (Code on Wages **s.14**: OT ≥2× the normal rate);
  - partial day pro-rated and flagged.
- **Totals:** statutory and contractual dues, paid, shortfall, estimate.
- **Form II heads:** 3(a) below minimum, 3(c) OT, 3(d) unpaid days, 3(e) deductions. Weekly rest, bonus and compensation are **not computed**.
- **s.17 late-payment flags:**
  - daily wage period → end of shift;
  - weekly → last working day;
  - fortnightly → within 2 days;
  - monthly → before the 7th;
  - on exit → within 2 working days.
- **Errors (no number shown):** `RATE_OUT_OF_WINDOW`, `ZONE_UNCONFIRMED`, `CATEGORY_UNKNOWN`, `SPHERE_UNKNOWN`, `PIECE_RATE_UNSUPPORTED`, `NO_CONFIRMED_DAYS`.
- **Fixtures** (Maharashtra Zone I unskilled, ₹22,463/month):
  - 8 h day = **863.96**;
  - 9 h (1 h OT) = **1,079.95**;
  - 13 such days = **14,039.38** (exact 14,039.375 — catches Decimal-division bugs); minus ₹4,500 paid = **9,539.38**;
  - agreed ₹1,000/day, 9 h = **1,250.00**.

## Rate data (rate packs carry provenance, validity window and verification status; never hardcode)
- **Maharashtra, SN 11 "Road construction, maintenance, construction industry"** (रस्ते तयार करणे, देखरेख करणे, बांधकाम उद्योग), 01.07.2026–31.12.2026, ₹/month = basic + special allowance ₹3,198:
  - Unskilled: Z-I **22,463**, Z-II 21,598, Z-III 20,728
  - Semi-skilled: 23,543 / 22,673 / 21,808
  - Skilled (includes highly skilled): 25,058 / 24,188 / 23,323
  - Source: notification **No. …/2026(2)/office-10/7997 dated 05.08.2026** (English translation hosted by SGCMS) — **verify the Marathi original**.
- **Stale official data:** as of 13 Oct 2026 the official mahakamgar.maharashtra.gov.in "किमान वेतन" link still serves the Jan–Jun 2025 PDF (same basic rates, allowance ₹2,378).
- **Central sphere** (railways, central PSUs, ports etc. and their contractors; Code s.2(d)), construction, from 01.10.2026, ₹/day, Areas A/B/C:
  - unskilled 840 / 704 / 565
  - semi-skilled 933 / 794 / 661
  - skilled 1,024 / 933 / 794
  - highly skilled 1,111 / 1,024 / 933
  - Secondary consolidation; the issuing office is unconfirmed.
- **Assumptions to verify:** ÷26 divisor and 8 h normal day for the Maharashtra notification; zone definitions (Zone I = municipal corporation, cantonment, and industrial areas within 20 km) for the construction schedule. Rates follow the **place of work**.

## Legal context (verified 13 Oct 2026; say "may"; don't overclaim)
- All four Labour Codes have been in force since **21 Nov 2025**; existing provisions continue during the transition.
- Code on Wages (Central) Rules 2026 are final (**G.S.R. 343(E), 8 May 2026**): hourly = daily ÷ 8; monthly = daily × 26; 8 h normal day; claims on **Form II** (manual or electronic), with group applications allowed.
- **Maharashtra Code on Wages Rules 2026 are still a draft** (published 28 Apr 2026).
- **s.45 claims:**
  - an authority of at least Gazetted rank hears them;
  - filed by the employee, a registered union, or the Inspector-cum-Facilitator;
  - one application can cover many employees (s.45(5));
  - **3-year limit**; compensation up to 10×.
- Contractor and sub-contractor = "employer" (s.2(l), s.2(f)). The principal employer may be liable if the contractor fails to pay (OSH Code s.55; contract-labour chapter applies to establishments with ≥50 workers): **paralegal decides**.
- Free legal aid: LSA Act **s.12(f)** "industrial workman".
- BSA **s.63(4)** certificate: Part A includes the **hash value**. The Supreme Court declined the challenge in *Pune Bar Association v UoI*, 22 May 2026.
- MahaBOCW registration needs a 90-day work certificate; the app can support but not replace it.
- **Evidence base:** Aajeevika/LEAD documentation (13,088 wage-theft cases; employers avoid documents; LEAD recovered ₹15 crore for 60,000+ workers using informal documentation, photos, digital receipts and co-worker verification).

## Packet (forum-neutral "dues statement and evidence file", not "proof")
1. Dues statement (mr/hi + en) with disclaimer.
2. Statement of facts plus verbatim transcripts.
3. Muster-roll-style day table.
4. Computation with provenance, Form II heads, assumptions and a "not computed" list.
5. Evidence index (SHA-256, device time, chain seq, anchors).
6. Parties and liability note.
7. Where to go (union, DLSA, s.45 authority).
8. Declaration and thumbprint box. "SYNTHETIC DEMO DATA" watermark in demo mode.

## Hisaab Saathi (worker-controlled; spec in IMPLEMENTATION_HANDOFF §10.20)
- **Samjhao:** spoken explanation from engine numbers. Voice Q&A: the LLM picks an intent from a fixed enum → pre-approved answer. Out of scope → "ask union / legal aid".
- **Saboot:** discrepancy → linked entry → evidence quote → ASR segment timestamps → 5–10 s ffmpeg excerpt (own hash plus parent hash).
- **Bhejo:** "send to thekedar?" → risk note → [thekedar | union | not now] → summary + ticked clips → Web Share sheet (needs HTTPS or localhost) or download + `wa.me` link. Logs `SHARE_PREPARED`.
- **Bol ke Batao:** fact-only hi/mr statement (no threats or sections; minimum-wage line opt-in) → mandatory recording notice → reply ≤30 s → LLM reply schema → worker confirms a promise → `PROMISE_LOGGED` plus a reminder. A hostile reply stops the flow and shows contacts. The bounded responder is deferred.

## Demo data
- 30 SYNTHETIC clips recorded by the team (12 mr, 12 hi, 6 Hinglish; 5 noisy; 2 phones) with a ground-truth sheet.
- Persona "Sunita" (fictional helper, Marathi), thekedar "Kailas", builder "Example Developers", Zone I, 13 days, 9:00–19:00 with a 1 h break, paid ₹4,500.

## Pitfalls
- LLM doing maths or law.
- Losing audio on ASR failure.
- Any internet in the demo path.
- English-only UI.
- Trusting ASR on numbers.
- Hardcoded or unverified rates without a status label.
- Calling the output "legally valid" or "proof".
