# Suggestions & Design Discussion — 16 Oct 2026

> Session notes from Final Build Day itself (Fri 16 Oct 2026, morning). The execution plan built from these notes is [`BUILD_PLAN.md`](BUILD_PLAN.md). Captures the concerns raised by Akash, the discussion with Claude Code, the decisions taken, and the resulting suggestions. Where this file conflicts with `PS07_Strategy_Report.md` or `IMPLEMENTATION_HANDOFF.md`, **this file is newer** (see §5 "Decisions that override earlier docs").

---

## 1. The core concern: "A worker-only log is not proof"

### What Akash raised
The problem statement asks for a *proof/evidence builder*, but the current design is entirely worker-side: the worker speaks, the app records. If the worker is lying, or misunderstood what the thekedar said, then only recording the worker's side is not enough.

### Discussion / response
**The concern is valid** — a one-sided self-log is contestable ("he's lying", "he misunderstood the rate"). Currently the only non-worker signals are the hash chain and an optional co-worker statement (which sat at #7 in the SHOULD list).

**But the worker-side base is still correct, for four reasons:**
1. **It is what PS07 asks for.** "A worker logs daily attendance and hours worked — a voice note … is enough." Judges won't penalise the worker-side base, but they *will* ask about credibility, so have the answer ready.
2. **Record-keeping is the employer's legal duty.** The Code on Wages requires employers to maintain muster rolls and wage registers. Thekedars typically don't — Aajeevika research documents deliberate document avoidance. When the employer's record is missing, a contemporaneous, daily, tamper-evident worker record is often the *only* record that exists.
   **Pitch line:** *"We don't replace the employer's record — we fill the gap his missing record leaves."*
3. **Minimum wage doesn't depend on the agreement.** The statutory floor applies whatever the thekedar promised, so "misunderstood the rate" matters less than it sounds. What must be credible is **days and hours worked**, not the agreed rate.
4. **A contractor-side app won't work.** Thekedars won't voluntarily use a tool that builds a case against them, and asking them to raises retaliation risk for the worker.
5. final suggestion from my side both an photo + voice both as a proof is much better , flow voice uploaded , optional image taken all saved 

### Suggestion: move from "worker says" → "worker says + corroboration"
| Layer | What it adds | Notes |
|---|---|---|
| **Co-worker cross-check** (most important) | A co-worker confirms the day via a short voice note or QR tap; or two workers' logs for the same site/date match | This is how LEAD verifies cases. Enables a group claim under s.45(5). **Promote from SHOULD #7 to near the top.** |
| **Outside anchors** | Photo of UPI/bank SMS per payment; photo of site board; chain-head code SMSed to a union/family number | The SMS gives a third-party timestamp, showing the entry existed on that date and wasn't fabricated later. |
| **Thekedar's own words (consented)** | Hisaab check (worker narrates what the thekedar said) + consented direct recording of the thekedar | This *is* the contractor side. Make it more visible in the pitch. |
| **Per-day corroboration level** | "self only" → "self + co-worker" → "self + co-worker + payment record" | The packet shows the paralegal how strong each day's record is, instead of claiming it's all proof. |

---

## 2. Follow-up ideas from Akash and the verdicts

### 2.1 Optional photo/video of the worker at work — **Photo: YES. Video: skip.**
- Photo per day (site, site board, the work done) is cheap: one `<input type="file" accept="image/*" capture>`, saved and SHA-256 hashed like audio. ~30 min of work.
- Be honest about what it shows: **presence, not hours**. Present it as one corroboration layer among several.
- Video: big files, slow hashing on phone, little extra value → leave out.
- Co-workers' faces in photos need their consent.
- **GPS: KEEP** (Akash's decision — reverses the earlier "no GPS" rule). Present it in README/pitch as *worker-controlled, opt-in* location stamping that strengthens "was at site".

### 2.2 Recording the thekedar directly, with his permission — **YES (mostly already planned).**
the Bol ke Batao reply-recording & a standalone **"Record thekedar's hisaab"** button (optional like when an thekedar lang is unkown or the worker wants to record directly the thekedar then thier sholud be an option to record the thekedar)
1. Spoken notice plays first (cannot be switched off).
2. His permission is captured on the recording itself.
3. LLM extracts his stated days / rate / amount.
4. App compares against the worker's confirmed log → itemised differences.

This is the strongest answer to the "only the worker side" concern — the thekedar's own words become evidence.
Cautions:
- ASR is weak on two people talking over site noise → **worker confirms every number**.
- Keep the instant Stop button and the mandatory notice.

### 2.3 Telegram bot agent that chats with the thekedar 
an telegram bot that can be handled via an agent which can directly interact with the thekedar via messages answer to his chats record them as proof (this is just for demo as whatsapp api is paid) like that agent can automadetly send messages or maintain daily record like today the thekedar didnt paid me, this is what remmaning , today he paid me

---

## 3. Online / offline architecture (Akash's decision)

**Not strictly fully-offline.** Some features may stay off without internet and come back when it returns. Models downgrade when offline:
- **Online (best quality):** the current planned stack on a GPU laptop or cloud (still open-weight).
- **Offline:** smaller open models running directly on a decent phone.
- Items captured offline are **queued and reprocessed** on the full stack when internet returns; the worker re-confirms.

### Key principle
**Offline mode must not depend on on-phone AI.** These all work with no model at all:
record → save audio + SHA-256 → GPS + photo → JS numeral parser → "same as yesterday" → store in queue.
On-phone AI is a bonus on top.
**Pitch line:** *"No internet never means no record."*

# and can still be processed with on device ai, later can be reasssesed if needed

---

## 4. Model research for the target phones

### 4.1 Target phones
| Phone | Chip | GPU | RAM |
|---|---|---|---|
| Samsung Galaxy A33 5G | Exynos 1280 | Mali-G68 MP4 | 6 GB (variant) |
| Vivo Y73 | MediaTek Helio G95 | Mali-G76 MC4 | 8 GB |

Both are mid-range. Realistic budget: a ~250M-parameter speech model + a ~1–2B language model at 4-bit. **Too big:** Gemma 4 E2B (in PWA form), any 4B model, Indic Parler-TTS.

### 4.2 Recommended tiers
| Job | Online (laptop / cloud GPU) | Offline (on the phone, inside the PWA) |
|---|---|---|
| **Speech-to-text** | AI4Bharat IndicWhisper (current plan) | **Whisper-small** in-browser via transformers.js (`onnx-community/whisper-small`), language forced to hi/mr. For Hindi, **`vasista22/whisper-hindi-small`** is better (Apache-2.0, ~181 MB at q5_1; needs ONNX export first). **Marathi has no strong small model** → rely on read-back + worker confirmation. |
| **Structuring (LLM)** | Qwen3-4B-Instruct-2507 (current plan) | **Qwen3.5-0.8B** (873.4M params, Apache-2.0) — ready-made in-browser WebGPU demos exist. On 8 GB phones, **Qwen3.5-2B** (2,274.1M params; Q4_K_M = 1.28 GB) if fast enough. |
| **Speaking back (TTS)** | Indic Parler-TTS | **Pre-recorded clips.** Read-back is a fixed template → on the GPU box, generate template phrases + numbers 0–100 with Parler-TTS and stitch them on the phone. Fully open-weight, works offline. Phone's built-in voice = last resort only (not an open model). |
| **Number check** | Deterministic parser | **Same parser ported to JavaScript.** No model needed → two-reader check still works offline. |

### 4.3 Considered and rejected for build day: Gemma 4 E2B
- Pros: one Apache-2.0 model doing ASR + structuring; 2.3B effective params (5.1B with embeddings); audio input up to 30 s; built for phones.
- Cons:
  - GGUF Q4_0 (3.35 GB) + audio/vision projector (0.99 GB) ≈ **4.3 GB**; Google's LiteRT-LM phone format ≈ **2.58 GB**.
  - LiteRT-LM needs a **native Android (Kotlin) app** → gives up the PWA.
  - **No published Hindi/Marathi accuracy numbers** found; one developer report notes odd Hindi substitutions.
- Verdict: good **"next version"** upgrade, not a build-day choice.

### 4.4 Risk: in-browser GPU support on these phones
The Vivo Y73 launched on Android 11; WebGPU in Chrome on that phone is uncertain. Without it, models fall back to the much slower CPU/WASM path.

**Do-now 10-minute check per phone** — open:
- `hf.co/spaces/webml-community/Qwen3.5-0.8B-WebGPU`
- `hf.co/spaces/Xenova/whisper-webgpu`
- `chrome://gpu`

If either demo is too slow, drop that model from the offline tier rather than fight it on build day.

---

## 5. Decisions that override earlier docs
| Topic | Earlier plan | Now |
|---|---|---|
| GPS | No GPS | **GPS allowed** (opt-in, worker-controlled) |
| Offline | Fully offline demo path | **Hybrid**: full stack online, degraded on-device models offline, queue + reprocess |
| Photo evidence | Site-board photo only | **Optional daily photo** as presence corroboration |
| Co-worker witness | SHOULD #7 | **Promote near the top** (key credibility layer) |
| Thekedar recording | Only inside Bol ke Batao | **Standalone consented "Record thekedar's hisaab" button** |
| Telegram | — | **Agent ↔ thekedar on Telegram: approved by Akash** as a demo stand-in for the paid WhatsApp API, with guardrails (template-only replies, intro notice, hostile → no reply). Spec: BUILD_PLAN §7 |
| Recording thekedar | Inside Bol ke Batao only | Also standalone, with a notice-language picker for when the thekedar's language is unknown (BUILD_PLAN §8) |
| Entry flow | Voice only | **Voice → optional photo → GPS → all saved and hashed** |


## 7. Housekeeping noticed
- `git status` on 16 Oct showed the whole `backend/` folder (wage engine, rate packs, F1–F9 tests) **deleted in the working tree** but still present in commit `6e639cb`. If unintentional: `git restore backend/`.

---

## Sources
- [Gemma 4 E2B model card (Hugging Face)](https://huggingface.co/google/gemma-4-E2B-it)
- [Gemma 4 model card (Google)](https://ai.google.dev/gemma/docs/core/model_card_4)
- [Gemma 4 E2B LiteRT-LM build](https://huggingface.co/huggingworld/gemma-4-E2B-it-litert-lm)
- [Gemma 4 E2B QAT Q4_0 GGUF](https://huggingface.co/google/gemma-4-E2B-it-qat-q4_0-gguf)
- [Gemma 4 E2B Android dictation project (Hindi note)](https://github.com/hkgill/gillspeak/pull/6)
- [Qwen3.5-0.8B](https://hf.co/Qwen/Qwen3.5-0.8B)
- [Qwen3.5-2B](https://hf.co/Qwen/Qwen3.5-2B)
- [Qwen3.5-2B GGUF (unsloth)](https://huggingface.co/unsloth/Qwen3.5-2B-GGUF)
- [Qwen3.5 small series overview (NYU Shanghai RITS)](https://rits.shanghai.nyu.edu/ai/qwen-3-5-small-models-9b-parameters-that-beat-120b)
- [Indic Whisper ggml builds](https://huggingface.co/ukta-app/indic-whisper-ggml)
- [vasista22/whisper-hindi-small](https://hf.co/vasista22/whisper-hindi-small)
- [onnx-community/whisper-small](https://hf.co/onnx-community/whisper-small)
- [whisper.cpp Android example](https://huggingface.co/datasets/echodict/whisper.cpp/blob/main/examples/whisper.android/README.md)
- [Whisper WebGPU guide](https://hackernoon.com/turn-audio-to-text-on-your-device-free-whisper-webgpu-guide)
- [Samsung Galaxy A33 5G specs (GSMArena)](https://m.gsmarena.com/samsung_galaxy_a33_5g-ampp-11429.php)
- [Vivo Y73 specs (comparison)](https://www.giznext.com/compare/vivo-y73-vs-samsung-galaxy-m33-5g)
