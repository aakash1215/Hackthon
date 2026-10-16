---
name: "hackathon-pitch-and-judges"
description: "Use when preparing the OpenForge final pitch, demo script or slides, or when the user wants a mock judge Q&A on the wage-theft evidence builder."
---

# Pitch & Judge Prep: Wage-Theft Evidence Builder ("Apna Hisaab")

**Judges and format:**
- Judges likely include JNEC/MGM faculty and industry partners (DomAIyn Labs and GDAI co-organise).
- **No judging rubric has been published.** Coordinators (13 Oct): **judges come to your desk and judge on the spot**; submit repo + README.
- Default to the **3-min desk demo**: live Marathi note → read-back → hisaab check → Saboot clip → Bhejo prompt → packet. Offer the full version if they have time.
- Reset the demo data between judges, and keep the printed A4 summary on the desk.
- PS07 is **not** a DomAIyn Labs statement (confirmed by coordinators); no fixed state or output format is expected.
- Track 1 judges care that open-weight AI is foundational, the solution is real and feasible, and the impact is clear.
- The venue is in Maharashtra, so a Marathi demo lands well (hypothesis).
- **Full demo script and Q&A:** `planning/PS07_Strategy_Report.md` §8.3–§8.4.

## Pitch shape (~6 min including demo; compress to the announced slot)
1. **Hook (25 s), all synthetic and labelled.** "Sunita worked 13 days. On payday the thekedar's hisaab says 12 days × ₹600 minus a ₹2,000 'advance'. She has nothing written. In 13,088 wage-theft cases, one NGO found employers avoid every document that would prove she worked."
2. **Offline and open (15 s).** Wi-Fi visibly OFF. Name the models and parameters: IndicWhisper (~764M, MIT), Qwen3-4B-Instruct-2507 (4.0B, Apache-2.0), Indic Parler-TTS (938M, Apache-2.0).
3. **Live demo:**
   - Marathi voice note → card with an amber field → **Marathi read-back** → fix → confirm.
   - Hindi payment note.
   - **Hisaab check:** 6 Oct missing from his count; ₹600 vs. **₹864/day legal minimum** (Maharashtra notification 7997, 05.08.2026, Zone I, unskilled); OT unpaid; ≈₹9,539 estimate.
   - **Samjhao** explains aloud → **Saboot** plays the exact 6 Oct clip → **Bhejo** asks "send to thekedar?" with a risk note → WhatsApp.
   - **Bol ke Batao:** the phone politely states the facts, announces recording, and logs "₹5,000 by Monday".
   - Packet PDF → tamper demo ("chain broken at event 37").
4. **How it works (30 s).** One diagram: ASR → normalizer + schema-constrained LLM (two readers) → worker confirmation → hash chain → deterministic wage engine → packet + Saathi.
5. **Why it wins (20 s).** Own language in and out; no silent guesses; current law (Labour Codes in force since 21 Nov 2025); exact proof clips; the worker stays in control; offline on one hub laptop. Tiers B/C run on cheaper hardware.
6. **Close (10 s).** "Not the thekedar's hisaab: her own." Ask: pilot with a union or DLSA.

Remove any claim that it "runs on a 2016 i3 laptop" as the main setup: the demo runs on an 8 GB GPU laptop, and the i3 is the CPU-only emergency tier.

## Demo rules
- Rehearse exact clicks; seed data; one fresh live voice note; everything SYNTHETIC and watermarked.
- Show the measured latency honestly.
- Keep the backup screen recording ready to play instantly.
- If anything breaks, say what should happen, switch to the backup, keep going.

## Mock judge Q&A
When asked to run mock judging:
1. Play three judges one at a time.
2. Ask hard questions and wait for the user's answer.
3. Score it (clarity, honesty, evidence) and suggest a tighter answer.

The judges:
- **Judge A, industry AI engineer:** models, accuracy, latency, hallucination control, why not a bigger or cloud model, Gemma 4 vs. Qwen.
- **Judge B, faculty/academic:** architecture, data integrity, testing, originality, what was built today.
- **Judge C, social impact/legal:** will a labour office or legal aid use this, privacy, worker safety and retaliation, adoption.

Likely questions and the shape of strong answers:
- **"Accuracy for Marathi/Hindi?"** Published IndicWhisper averages: Marathi 18.2 WER, Hindi 13.6, noisy Hindi 26.8. Then give *our measured* numbers. Numbers are double-checked (LLM vs. deterministic parser), read back and confirmed.
- **"LLM hallucination?"** Schema-constrained output, an evidence quote required for every value, null when not said; the LLM never computes or decides law.
- **"Legally valid?"** No tool makes evidence valid. It is a contemporaneous, worker-confirmed, tamper-evident record of the kind legal-aid cells already use (Rajasthan LEAD: ₹15 crore, 60,000+ workers). A BSA s.63(4) certificate needs hash values, which the packet lists. Code on Wages s.45 claims must be filed within 3 years.
- **"Couldn't she fake it?"** Any self-record can be faked; we make it harder and visible (daily entries, hash chain, SMS/hub anchors, witnesses). The employer's statutory registers are the counter-record, and our table mirrors their columns.
- **"Whose minimum wage applies to a Bihar worker in Maharashtra?"** The place of work, via the "appropriate Government" (s.2(d)). Central-sphere sites use central rates.
- **"Who pays if the thekedar vanishes?"** The contractor is an "employer" (s.2(l)). The principal employer *may* be liable (OSH Code s.55; depends on facts and size). We capture the builder's identity; the paralegal decides.
- **"Why not let the AI argue with the thekedar?"** Rejected on evidence: retaliation risk, legal misstatements, the AI might accept a bad deal, and ASR is unreliable in shouting matches. So it speaks only fixed polite facts when she presses play, announces before recording, and logs promises.
- **"Isn't sending evidence to the thekedar dangerous?"** It can be. The app asks first, explains the risk, offers union-first, sends only the clips she ticks (no witness voices by default), and logs every share.
- **"Recording the thekedar: legal?"** Never covert: a spoken notice, then an instant Stop. Admissibility is for legal aid to advise; we don't claim it.
- **"Why AI at all?"** Low literacy plus own language: speech in, speech out, and free speech turned into structured, checkable fields.
- **"Where do rates come from? What if they're old?"** Notification 7997 with its validity window and verification status; the engine refuses dates outside it. The official site still links the 2025 PDF, which is why provenance matters.
- **"Did you build this alone?"** Yes, solo, with Claude Code as a coding assistant (disclosed in the README). The product's AI is entirely open-weight and local.
- **"What did you build today?"** Prep (research, downloads, CLI benchmarks, data, synthetic audio) is disclosed; all product code was written today, and git history shows it.
- **"Which parts used closed AI?"** None in the product. State exactly how AI coding assistants were used in development.
- **"Will workers use it daily?"** Unproven. The design makes payday the key moment, with a 20 s note and hub-assisted onboarding; there is a validation plan and a hub-interview fallback mode.

## Slide checklist (if slides are needed)
Title + team · problem story · solution & USP (hisaab moment, two-reader check, Saathi) · architecture with model names, params and licenses · demo screenshot or live · impact & adoption (unions, DLSA, BOCW facilitation centres) · limitations & roadmap.

## Delivery
- One speaker per section, smooth handoffs.
- Numbers over adjectives; say "may" and "estimate" for legal and money claims.
- If something breaks: say what should happen, switch to the backup recording, keep going.
