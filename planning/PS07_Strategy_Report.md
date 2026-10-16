# Apna Hisaab (अपना हिसाब / आपला हिशोब): PS07 Strategy Report

> OpenForge Hackathon (SWAYAMBHU 2026, JNEC / MGM University), Track 1 "Open Weight AI & Open Source Tools", PS07 "Migrant Worker Wage-Theft Evidence Builder". Prepared Tue 13 Oct 2026. **Planning only: no product code has been written** (Rule 5). Proposal PPT due **13 Oct, midnight**; Final Build Day **Sat 17 Oct 2026, 07:00, 10 hours, at the college** (confirmed by coordinators).
>
> **Update 13 Oct (after coordinator and team answers in `AboutHackthon/Question&Answers.md`):**
> - **Venue and resources:** you are **building solo** with Claude Code as a coding assistant. Own laptop, power and **internet are available**; prep (including an empty repo) is allowed.
> - **Judging:** submit **repo + README**; judges assess **at your desk**. There are no extra Track 1 rules, and PS07 is not a DomAIyn Labs statement.
> - **Phone app:** it must be **installable on a phone (PWA)**, which needs **HTTPS** (mkcert); phone microphones won't work over plain-HTTP LAN.
> - **Voice notes:** **flexible length**, with a one-tap **"Same as yesterday"**.
> - **Changed sections:** §2.3, §2.4, §3.10, §5.2, §7.1–§7.3, §8.3, §9.1–§9.4.
>
> Companion file: [`IMPLEMENTATION_HANDOFF.md`](IMPLEMENTATION_HANDOFF.md) is the self-contained build brief for the implementation agent (section 10 of the original plan).

## Context

- **Why this exists:** the team needs one research-backed, differentiated PS07 solution and a 10-hour build plan it can actually execute. The proposal must name specific open-weight models with parameter counts and licenses (Rule 3.3).
- **What prompted it:** the request to inspect the official materials, verify the rules, research the real problem, the law and the models, choose one concept, and hand off a build-ready plan without writing code early (Rule 5 disqualifies "pre-existing/unoriginal work").
- **Intended outcome:** the recommendation below, a proposal-ready model table (§6.3), a pre-build checklist (§7), and a self-contained handoff (§10, now in [`IMPLEMENTATION_HANDOFF.md`](IMPLEMENTATION_HANDOFF.md); every "§10.x" reference in this report points there). On approval, a dated note was also appended to `AboutHackthon/device.info` and the three OpenForge skills were updated.
- **What you confirmed on 13 Oct:**
  - Target an **8 GB VRAM NVIDIA laptop**, with a guaranteed **2–4 GB fallback** and a CPU emergency mode.
  - **PPT due 13 Oct at midnight; build day 17 Oct.**
  - The team can record **Hindi, Marathi and Hinglish** (plus English).
  - Fix `device.info` and the **3 OpenForge skills** after approval.
- **Added after your plan review (13 Oct):** a **Hisaab Saathi voice agent**:
  - **Samjhao:** explains the case to the worker simply, in her own language.
  - **Saboot:** picks the *exact* recording excerpt behind each discrepancy.
  - **Bhejo:** asks "send this to the thekedar?" and shares it on WhatsApp.
  - **Bol ke Batao:** a speak-for-me statement to the thekedar, with announced reply recording and a promise log.
  - **You chose the worker-controlled "speak-for-me" mode over a free AI debate agent.** The free debate agent is rejected (§4.1) and a bounded responder is deferred.
- **Evidence labels used throughout:**
  - **[V]** verified from a source opened in this session.
  - **[S]** search-result summary only; the page was not opened, so treat it as unverified.
  - **[E]** estimate.
  - **[H]** hypothesis that needs field validation.
  - **[R]** recommendation.

---

## 1. Recommendation in one minute

| | |
|---|---|
| **Product** | **Apna Hisaab** ("my own account"; working name). In the worker's words: *"Thekedar ka hisaab nahin, apna hisaab."* |
| **Target user** | A daily-rated migrant or seasonal construction worker (helper or mason) hired through a thekedar for a private building site in Maharashtra. They speak Hindi or Marathi (often code-mixed), have limited literacy, and use their own or a shared Android phone. **Activation user:** a paralegal, union organiser or legal-aid volunteer who turns the worker's record into mediation or a claim. |
| **Core promise** | *Speak a few seconds a day (or tap "same as yesterday"). On payday, Apna Hisaab tells you in your own language what you are owed under the law and your deal, and gives a paralegal a case file they can check and act on.* |
| **Differentiator** | **1. Built around the hisaab moment.** The worker speaks the contractor's settlement and the app reconciles it against their own confirmed record.<br>**2. Spoken read-back plus a "two-reader" number check.** The open LLM and a deterministic Hindi/Marathi numeral parser must agree, or the app asks. Nothing counts until the worker confirms.<br>**3. "Who owes me?" evidence coach.** It captures thekedar, sub-contractor and builder identity, witnesses and payment proof while they can still be obtained.<br>**4. Law-mapped, provenance-stamped arithmetic.** Done by deterministic code, organised by Form II relief heads, and citing the notification number and date.<br>**5. Paralegal-ready bilingual packet.** Includes a SHA-256 evidence index (hash values are what BSA s.63(4) certificates ask for) and a one-page dues statement for mediation.<br>**6. Hisaab Saathi voice agent.** It explains the result aloud, plays the exact clip that proves each difference, and asks before sending it (to the thekedar or the union) on WhatsApp. It can also speak a polite, fact-only statement to the thekedar and log any promise he makes. The worker stays in control; the AI never argues or negotiates. |
| **Expected impact** | Legal-aid cells already recover wages by turning informal documentation into mediated settlements. Rajasthan's LEAD cell reported "Rs. 15 crores to over 60,000 informal and migrant workers" since 2010 **[V]** (Aajeevika chapter, p.283). The binding constraint is proving the employment relationship, days and amounts **[V]** (p.277). Apna Hisaab produces exactly that record, in the format paralegals already use. Recovery uplift per worker is **[H]**. |
| **Why Track 1** | Three open-weight models carry the load: speech recognition (ASR), structuring (LLM) and read-back (text-to-speech, TTS). Without them a low-literacy worker cannot use the product. All three run **offline on one laptop** under MIT or Apache-2.0 licenses. |
| **Why it can win** | The live demo: a Marathi voice note, read back in Marathi, produces a shortfall computed from **Maharashtra notification No. 7997 dated 05.08.2026**, ends in a verifiable packet, and runs with **Wi-Fi visibly off**. It is grounded in the law as it stands after the **Labour Codes took effect on 21 Nov 2025** and is honest about its limits. Typical PS07 entries will show English PDFs, hardcoded wages and LLM arithmetic. Winning is not promised. |

**Facts the proposal must state (Rule 3.3; details and links in §6.3):**
- ASR: **AI4Bharat IndicWhisper** (Hindi and Marathi checkpoints; Whisper-medium fine-tunes, about 764M params; MIT) and **OpenAI Whisper large-v3-turbo** (808.9M; MIT).
- LLM: **Qwen3-4B-Instruct-2507** (4.02B; Apache-2.0).
- TTS: **AI4Bharat Indic Parler-TTS** (937.8M; Apache-2.0).
- Evaluated alternative: **Google Gemma 4 E4B-it** (4.5B effective / 8B total; Apache-2.0).
- No closed AI API anywhere in the product.

---

## 2. What the files and rules actually say

### 2.1 Inventory (everything was read; no existing product code)

| File | Read? | Notes |
|---|---|---|
| `AboutHackthon/ChoosenProblemStatment.json` | ✅ | PS07 text, track and suggested tools |
| `AboutHackthon/TrackRules.txt` | ✅ | Track 1 rules 1.1–1.5 (same as rulebook 4.1–4.5) |
| `AboutHackthon/TrackGuide&ParticipationRules.pdf` | ✅ (4 pages) | Full rulebook (sections 1–6) |
| `AboutHackthon/MaketingMatrialForHackthon.txt` | ✅ | Dates, venue, prizes, Drive links |
| `AboutHackthon/image.png` (poster) | ✅ | Dates, venue, contacts, "40 teams ~150 participants" |
| `AboutHackthon/device.info` | ✅ | Akash: i3-6006U, 8 GB RAM, AMD R5 M330 2 GB (no CUDA). "Anuskha": NVIDIA, 2–4 GB VRAM, details pending |
| Drive: Problem Statements PDF (`14f1v…`, modified 2026-10-05 11:27 UTC) | ✅ via Drive connector | 8 Track 1 and 5 Track 2 statements. No authorship labels. "…or propose an original idea fitting the track's theme" |
| Drive: Rulebook PDF (`1-bEA…`, modified 2026-10-05 11:28 UTC) | ✅ | Identical to the local copy; **no post-extension update online** |
| `CLAUDE_HACKATHON_IDEATION_PROMPT.md` | ✅ | An earlier version of this prompt; superseded |
| `.agents/skills/*`, `skills-lock.json` | ✅ | Tooling (brainstorming, grill-me), not project content |

### 2.2 Source-of-truth table

| Requirement | Exact interpretation | Source | Consequence for design |
|---|---|---|---|
| Problem | Offline-first tool. A worker logs attendance and hours (a voice note is enough). Open-weight speech and language models transcribe, structure and compile a "legally-usable wage-claim document" that compares hours against the **applicable state's** minimum-wage notification. | PS07 JSON; Drive PS PDF | Voice → ASR → LLM → ledger → deterministic comparison → packet. A jurisdiction resolver is mandatory. |
| Suggested tools | Whisper (open-weight) or Vosk; small LLM; SQLite; FastAPI/Node/Spring; React/Angular | PS07 | Stack: FastAPI + SQLite + React. |
| AI must be foundational | "…an important, foundational part…not a cosmetic addition" | Rule 4.2 | All three models sit on the critical path. |
| No closed AI as core | GPT/Claude/Gemini APIs only for incidental use, and **must be disclosed** | Rule 4.5 | No closed API calls in code. README discloses any AI-assisted coding. |
| Public repo | Public GitHub repository | Rule 4.3 | Push at the end (needs a hotspot). |
| README | Exact models, **parameter counts**, link to license/terms | Rule 4.4 | Pre-filled model table in §6.3 and §10. |
| SLM definition | ≤10B params counts as "small" (a definition, not a limit) | Rule 4.1 | 4B LLM. Gemma 4 12B (11.96B) would count as "large"; not needed. |
| Proposal | 6-slide PPT in the prescribed format; Track 1 must name models | Rules 3.2, 3.3 | §6.3 is proposal-ready. |
| Submissions | One per team, through the official channel | Rules 3.4, 3.5 | — |
| Disqualification | Plagiarism or **pre-existing/unoriginal work**; violating "Sections 4.1–4.4, 4.5–4.8"; false information | Rule 5 | All product code is written on build day; prep is disclosed. |
| Clarifications | Must be raised **before the Round 1 deadline**; queries after shortlisting "may not be entertained" | Rule 6.2 | **Send the coordinator questions (§9.1) tonight.** |
| Changes | Committee may change dates, venue or rules | Rule 6.1 | Re-check the day before the build. |
| Judging criteria | **Not published** in any local or Drive material | All sources | The §4 rubric is *our own* decision aid. |
| Build-day deliverables (Track 1) | Only the public repo and README citations are explicit; no Track 1 demo format is stated (Track 2 lists prototype, documentation, demo) | Rulebook §4 | Assume live demo plus jury Q&A; confirm with coordinators. |
| PS07 authorship | Not stated. The poster says 3 Track 1 statements come from DomAIyn Labs. PS01–PS03 share a distinct, detailed security format, so PS07 is likely *not* one of them **[H]** | Drive PS PDF; marketing text | Pitch to faculty and industry judges alike. |
| Team, fee, prize | 1–4 members; ₹200; ₹10,000 Track 1 winner plus partner prizes | Rule 1.1; poster | — |

### 2.3 Dates and logistics

| Item | Poster | Marketing text | Rulebook | **Confirmed by you (13 Oct)** |
|---|---|---|---|---|
| Round 1 window | 05–12 Oct | 06–12 Oct | 03–11 Oct 23:59 (3.1); registration by 12 Oct 23:59 (2.4) | **PPT due 13 Oct, midnight (extended)** |
| Shortlist | 13 Oct | 13 Oct | 13 Oct | **1–2 days after PPT submission** (coordinators) |
| Final Build Day | 16 Oct, 07:30, 10 h | 16 Oct, 07:30 | — | **Sat 17 Oct 2026, 07:00, 10 hours** (coordinators) |
| Venue | "JNEC campus — department computer labs & computing centres" | "CSE Seminar Hall" | — | **At the college. Own laptops allowed, power sockets available, internet available throughout** (coordinators) |

### 2.4 Conflicts, gaps and unreadable items

1. **Dates:** three conflicting windows; resolved by your confirmation above.
2. **Venue:** "Seminar Hall" vs. "computer labs". **Resolved 13 Oct:** at the college; own laptops, power and internet are all available (§9.1).
3. **Hardware:** `device.info` says 2–4 GB VRAM; the brief says up to 8 GB. **Resolved:** 8 GB target with 4 GB and CPU fallbacks (§6.5).
4. **Rule 5** cites "Sections 4.1–4.4, 4.5–4.8". Sections 4.6–4.8 do not exist in the document → ask coordinators whether hidden rules exist.
5. **Track 2** explicitly says core functionality must be built during the hackathon. Track 1 does not, but the Rule 5 originality clause applies to all → treat it as binding.
6. **The 3 synced OpenForge skills** assume a CPU-only i3 stack, Whisper base/small, WeasyPrint/ReportLab PDFs (ReportLab cannot shape Devanagari properly), the "CSE Seminar Hall" venue, and "verify" placeholders for the law. All of these are superseded here; they will be corrected after approval.
7. **Stale official data:** as of 13 Oct 2026, the Maharashtra Labour Department homepage "किमान वेतन" link still serves the **Jan–Jun 2025** notification dated 20.02.2025 **[V]** ([PDF](https://mahakamgar.maharashtra.gov.in/Site/Upload/Pdf/minimum-wages.pdf); [site](https://mahakamgar.maharashtra.gov.in/), footer "last updated 13-10-2026"). Stale rates are a live risk, not a hypothetical one.
8. **Not readable or not fetched this session:**
   - Labour Ministry Compliance Handbook PDF (fetch failed).
   - PIB pages (HTTP 403).
   - Jan Sahas, housing.com and Cornell pages (DNS or policy blocks).
   - Gated IndicConformer model card (our Hugging Face account has no access).
   - Final Code on Wages (Central) Rules 2026 PDF (text not extractable).
   - Claims based on these are marked **[S]**.

---

## 3. Problem evidence and open questions

### 3.1 How wage theft actually happens (worker workflow before, during and after a dispute)

The core source is Jayaram & Jain, "Protection of Wages of Seasonal, Circular Migrant Labour in India", *India Exclusion Report* (Aajeevika Bureau). It draws on legal-aid case work; references run to June 2020 and the file was uploaded in Oct 2023 **[V]** ([PDF](https://aajeevika.org/wp-content/uploads/2023/10/India-Exclusion-Report_Protection-of-Wages.pdf)).

- **Before (hiring):** workers at nakas, or recruited from villages, "are unable to seek basic information … or even the contact details of the contractor". Contractors "do not like to hire workers that ask questions" (p.270).
- **During (work):** "Workers rarely keep an adequate, written record…This leads to a one-way record-keeping by the employer, who after the work is performed, provides *hisaab*…which workers find hard to challenge". Contractors "provide abstruse calculations" (p.270).
  - Across **13,088 wage-theft cases**, employers "try their best to avoid any documentation that would establish an employer–employee relationship" (receipts, attendance registers, written hisaab) (p.272).
  - Women are hired as a *jodi* and paid "as 1.5 labourers"; their wages are handed to husbands (p.272).
- **Dispute:** ">68 per cent of the 300 migrants studied reported…a major dispute at work (most frequently related to wages)…none of the workers had taken their case to any formal legal channel" (2008 study, cited p.268). Workers fear losing work and false theft accusations (p.272, p.284).
- **After:** "The first step…is to prove employer–employee relationship" (p.277). Piece-rate and multi-task pay makes calculations complex, so incomplete documentation leads to cases being dismissed as "unviable".
  - Workers go home after disputes, but cases must be lodged where the dispute occurred (pp.277, 285).
- **Naka reality:** contractors hire different people daily and some "disappear after the project work was completed". Nakas group workers linguistically; workers there come from Karnataka, AP, Maharashtra, UP and Telangana **[V]** (Citizen Matters, Thane, 22 Dec 2022, [link](https://citizenmatters.in/labour-naka-ecosystem-thane-construction-worker-mumbai-informal/)).

### 3.2 What already works, and the gap

- **Rajasthan LEAD cell** (from the same Aajeevika chapter, p.283) "makes informal documentation acceptable for formal processes":
  - It records oral testimonies and case files "signed by all parties".
  - It builds wage calculations "based on the accounts of workers", using "photographs…at the worksite, payslips or digital payment receipts".
  - It authenticates these "with co-workers, contractors, employers or visits to the worksite".
  - Results: ₹15 crore recovered for more than 60,000 workers.
  - **Its gaps (p.284–285):** workers living on site fear reporting; women report through men; workers' own notes are "incomplete, erratic and arbitrary and heavily manipulated".
  - → **Apna Hisaab produces exactly LEAD's inputs**, in a consistent, worker-confirmed, timestamped form that women can operate themselves.
- **The authors' recommendations:** courts should "accept and encourage…photographs of the worksite, digital receipts…workers' informal records" (p.289). Hisaab records should be "maintained by, both workers and contractors" (p.291).
- **Prior art:** Jornaler@ (NDLON with New York worker centres, announced 21 Nov 2016) lets day labourers track hours, report wage theft and abusive employers, and store data anonymously, gated by a worker-centre code **[V]** ([NDLON](https://ndlon.org/labor-organizations-launch-innovative-new-phone-app-to-redress-wage-theft-and-worker-abuses/)).
  - The lesson is the worker-centre partnership model.
  - **What's new here:** own-language voice in and voice out, offline open models, Indian-law computation, integrity mechanisms and a paralegal packet.

### 3.3 Who the workers are; MVP languages

- **Workforce:**
  - Jan Sahas' COVID rapid assessment (Apr 2020) phoned **3,196 migrant construction workers** in North and Central India: 94% lacked BOCW cards, 17% had no bank account and 55% were "severely underpaid" **[S]** (page blocked: [link](https://ruralindiaonline.org/en/library/resource/voices-of-the-invisible-citizens/)).
  - No source found for the origin-state mix of construction workers in Chhatrapati Sambhajinagar specifically **[H]**: likely intra-state Marathwada/Vidarbha plus Hindi-belt inter-state migrants.
- **Phones:** NSS Comprehensive Modular Survey: Telecom 2025 found ~85.5% of households own at least one smartphone **[S]** ([PIB](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2132330), 403). No migrant-specific figure was found. Shared phones and low-end Android devices are **[H]**.
- **MVP languages [R]: Hindi (including Hinglish) and Marathi** for capture and read-back; **English** for the paralegal and official view.
  - This matches the team's native testing ability (confirmed) and the two groups most plausibly present on Maharashtra sites.
  - Deferred until native testers are available: Bengali, Odia, Bhojpuri, Telugu, Kannada (several are covered by AI4Bharat models).

### 3.4 Who is responsible for paying (subcontracting chains)

- **The thekedar is an "employer".** Under the Code on Wages, "employer" includes a contractor (s.2(l)), and "contractor" includes a sub-contractor (s.2(f)) **[V]** ([s.2](https://www.advocatekhoj.com/library/bareacts/codeonwages/2.php)).
- **Principal employer (builder/owner) fallback:**
  - OSH Code 2020 s.55, "Responsibility for payment of wages": the contractor pays (electronically, informing the principal employer). If the contractor fails or short-pays, "the principal employer will be liable to make payment to the contract labour" **[S]** (Labour Ministry Compliance Handbook, Feb 2026, [PDF](https://www.labour.gov.in/static/uploads/2026/02/83978455025732b99b0165def80ab171.pdf); search excerpt only).
  - PRS notes that contract-labour provisions apply to establishments or contractors with **≥50 workers** **[V]** ([PRS](https://prsindia.org/billtrack/the-occupational-safety-health-and-working-conditions-code-2020)). Liability may therefore not reach small jobs.
  - Aajeevika argued the codes weakened principal-employer liability (p.278–289).
  - → **The app records identities; a paralegal decides liability.**
- **Chains are long:** "at least nine levels of middlemen" in construction **[S]** (Aajeevika/Migrantscape summary).
- **Identifying the builder:** MahaRERA requires the registration certificate to be displayed prominently at the project site, and QR codes on advertisements (order dated 25 Jul 2023) **[S]** ([summary](https://housing.com/news/qr-code-display-in-all-maharera-registered-projects-mandatory-from-aug-1-2023/)). A photo of the site board is a cheap, non-covert way to identify the principal employer.
- **Design consequence [R]:** capture every layer the worker knows (mukadam → thekedar → sub-contractor → builder), the site board and the site address. Never infer identities.

### 3.5 Jurisdiction and current minimum-wage source

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

### 3.6 Where inference runs for a real worker (deployment story)

| Stage | Where | Why |
|---|---|---|
| **Capture** | The worker's own or shared Android phone (offline PWA). Audio is saved and SHA-256 hashed at capture. A fallback quick-tap record covers present/absent and start/end times. | Works with no AI, no network and low literacy |
| **Understanding** (ASR → LLM → TTS) | **Phase 1 (realistic now):** a **hub laptop** with an 8 GB GPU at a union, NGO, legal-aid clinic or BOCW Worker Facilitation Centre. Phones sync over the hub's **local Wi-Fi hotspot (no internet)** weekly or at payday, or the paralegal visits nakas and sites. | Indic-quality ASR plus a 4B LLM plus TTS needs a GPU; the hub also supplies the paralegal |
| **Phase 2** | On-phone lite processing. Gemma 4 E2B is published for Android (LiteRT-LM) **[V-listing]**; on-device audio is unverified. | Future |
| **Phase 3** | IVR or missed-call capture for feature phones via a hub GSM gateway | Deferred |
| **Demo mapping** | One 8 GB laptop acts as the hub server; the UI runs in a phone-sized browser window (optionally a real phone on the laptop's hotspot). | Honest mapping |

Deferred processing reduces accuracy because memory fades. The phone therefore stores audio and quick taps immediately, and the worker confirms the AI's reading at the next sync, together with the paralegal.

### 3.7 Record integrity and timing: what can and cannot be shown

- **Can:**
  - a SHA-256 hash of each original recording at capture;
  - an **append-only, hash-chained event log** (edits are new events; originals are kept);
  - a short chain-head code;
  - an export manifest listing every hash (matching BSA s.63(4) Part A's hash field);
  - **third-party anchors:** (a) SMS the chain-head code to a union, NGO or family number — works without internet, and the recipient's phone timestamps it; (b) the hub countersigns at sync; (c) co-worker witness statements; (d) external records such as UPI or bank SMS with bank timestamps and site-board photos.
- **Cannot:**
  - prove when a recording was made, because the device clock can be changed;
  - prevent someone from fabricating a whole new chain;
  - authenticate who is speaking.
- **How to describe it:** "tamper-evident, device-time-stamped, corroborated by anchors". Never "proof".

### 3.8 Highest-risk failure modes

| Failure | Mitigation (built into the flow) |
|---|---|
| Misheard numbers, times or dates (साढ़े/साडे, सवा/सव्वा, डेढ़/दीड, ढाई/अडीच; Hindi "कल" = yesterday *or* tomorrow; Marathi "परवा" ambiguous) | Deterministic hi/mr numeral and time normalizer **and** LLM extraction must agree, otherwise the field turns **amber** and the app asks. Spoken read-back. Clock and keypad pickers. Ambiguous relative dates always trigger a question. |
| Entity-dense speech is where ASR fails: even strong systems reach only 0.03–0.16 entity-hit rate on synthetic Telugu entity audio | **[V]** ([arXiv 2605.03073](https://arxiv.org/abs/2605.03073)) → never trust ASR on numbers without confirmation |
| LLM invents values | JSON-schema-constrained decoding at temperature 0. An **evidence-span grounding check**: every value must quote transcript text, otherwise it is set to `null`. Profile defaults are shown as "assumed from your usual site — confirm?" |
| False certainty | Green/amber/red per field. "Worker-confirmed" vs. "machine-read" labels everywhere. Unconfirmed items are listed separately in the packet. |
| Stale or wrong rates | Rate packs carry validity windows, provenance and a verification status. The engine **refuses** dates outside a window and never invents a rate. |
| Wrong jurisdiction, category or zone | An explicit resolver step. Every result shows which inputs set the rate. A paralegal override is logged as an event. |
| Offline sync conflicts | MVP is single-device. Deployment: append-only events keyed by (device_id, seq); no in-place edits. |
| Device loss or shared phone | PIN per profile; minimal data kept on the phone; hub backup (deployment). |
| Employer retaliation | No autonomous AI contact with the employer; nothing is shared automatically; witness names can be redacted; guidance to approach a union or DLSA. |
| Sharing evidence with the thekedar backfires (he learns she keeps records, pressures witnesses, deletes or forwards clips) | Bhejo always asks first and plays a spoken risk note. It offers **union/paralegal as the safer alternative** and sends only the summary plus clips the worker picks. **Witness audio is excluded by default.** Originals stay on the device; every share is hash-logged (`SHARE_PREPARED`). |
| Speak-for-me escalates the conflict | **Fixed, polite, fact-only templates** (days, payments, request for a written hisaab and a payment date). No threats or legal accusations; the minimum-wage line is opt-in. Replies are recorded **only after an announced notice**, with a big Stop button. A hostile-reply intent stops the flow and shows union/helpline contacts. |
| The LLM gives legal advice in Q&A | The LLM only **classifies** a question into a fixed intent list; answers are **pre-written and reviewed**. Anything out of scope → "ask your union or legal aid". |
| Over-claiming legal force | Vocabulary such as "dues statement" and "evidence file" plus disclaimers; no "proof" or "valid claim" language. |

### 3.9 Facts vs. hypotheses

- **Sourced facts [V]:**
  - one-way contractor hisaab and avoidance of documentation;
  - the employment relationship is the first legal hurdle;
  - LEAD-style informal documentation works;
  - the Codes are in force;
  - current Maharashtra and central rates;
  - s.45 forum, s.14 overtime, s.17 deadlines, BSA s.63(4) hash values.
- **Hypotheses [H] to validate:**
  1. workers will record a short note daily (length flexible; "same as yesterday" tap), or at least on paydays;
  2. phones are shared, and a PIN is acceptable;
  3. Marathi/Hindi read-back builds trust;
  4. payday is the trigger moment;
  5. paralegals will accept this packet format;
  6. unions or NGOs will run a hub laptop;
  7. site boards are photographable without risk.

### 3.10 Field-validation guide (do on 14–16 Oct)

**Update 13 Oct:** you have **no union, NGO or DLSA contacts** and are working solo. Use this light-touch version and keep every adoption claim labelled **[H]** in the pitch:
- **(a)** Visit or phone the **DLSA office** (official number from the district court or NALSA website) with **Q5–Q6** only. This is the highest value: forum, form and packet feedback.
- **(b)** Ask 1–2 friends or relatives who have worked with thekedars **Q1–Q4**, informally and anonymously.
- **(c)** Do **not** approach naka workers alone without an organisation present.
- If none of this happens before 17 Oct, say so honestly: "validation planned with DLSA and unions".

**Who to approach (full version, if contacts appear):**
- 3–5 workers at a labour naka in Chhatrapati Sambhajinagar (07:00–09:00), **only with a union or NGO representative present**;
- one construction-workers' union organiser;
- the **DLSA** office or a law-college legal-aid clinic;
- if possible, the Assistant Commissioner of Labour's office (public counter), for the forum and form question.

**Consent and safety:**
- Introduce yourselves as students; explain that this is research and that **no recordings or names are taken**.
- Notes only, anonymised. Never photograph people.
- Don't visit sites or contractors. Don't promise help you can't give. Stop if anyone seems uncomfortable or a contractor is nearby.
- Offer helpline or legal-aid information in return.

**Questions, and which assumption each answer confirms or kills:**

| # | Question | Assumption tested | Kill signal |
|---|---|---|---|
| 1 | "Last time you were paid less than promised: what did you have to show? What did the thekedar say?" | Hisaab moment; one-way records | Workers say written slips are common |
| 2 | "Do you know the thekedar's full name and phone? The builder's name? Is there a board at the site?" | Identity gap; site-board capture | Identities are always known and documented |
| 3 | "Would you speak a few seconds into a phone each evening (or tap 'same as yesterday')? Whose phone? What would stop you?" (Your feedback: 20 s may be too much, so keep it flexible.) | Daily habit; phone sharing; fear | Recording feels unsafe → pivot to the hub-interview mode (§4) |
| 4 | "Which language at home vs. at work? Would you trust the phone reading back what you said?" | Languages; read-back trust | Read-back distrusted → show icons only |
| 5 | (Paralegal/DLSA) "If a worker brings this one-page dues statement plus file, what would you need? What's missing?" | Packet format | Format rejected → redesign the packet |
| 6 | (DLSA/labour office) "Which authority and form handles unpaid or minimum-wage claims in Maharashtra right now?" | Forum during the transition | — (resolves §3.5) |
| 7 | (Union/NGO) "Would you run a laptop hub that processes members' notes weekly? Who should hold the data?" | Deployment model | No operator → reconsider on-phone mode |

---

## 4. Shortlist and decision

### 4.1 Candidates (10 explored privately; best 5 shown)

| | Concept | Key user insight | Distinctive mechanism | Essential open-weight AI role | Feasibility (10 h) | Demo moment | Primary risk |
|---|---|---|---|---|---|---|---|
| **A** | **Apna Hisaab**: worker-held counter-hisaab, evidence coach and paralegal packet | Disputes crystallise at the contractor's hisaab; the worker has no counter-record (Aajeevika p.270) | Payday reconciliation; two-reader number check plus read-back; "who owes me" identity capture; Form II-mapped deterministic computation; hash-chained packet | ASR (hi/mr) → LLM structuring and contractor-claim parsing → TTS read-back | High (single device; one pipeline) | Marathi note → Marathi read-back → shortfall with notification citation → packet, offline | Daily-use adoption **[H]** |
| B | **Toli Khata** (crew ledger): a gang cross-attests days on multiple phones; group claim under s.45(5) | Collective claims cut individual retaliation risk and corroborate each other (LEAD verifies with co-workers) | Peer attestation by QR/Bluetooth-signed entries; group packet | Same pipeline, multi-user | Low–medium (multi-device sync, crypto) | Two phones attest each other | Sync and crypto complexity; mukadam power dynamics |
| C | **Sahayak Kendra console**: a paralegal hub turns oral interviews and voice notes into case files; the worker needs no app | Paralegals are the real bottleneck; workers won't install apps | Batch transcription, structuring and case tracking | ASR + LLM on interviews | High | Paralegal imports 10 notes → case file | Not contemporaneous; WhatsApp import needs internet; weaker fit to "worker logs daily" |
| D | **Payday early-warning diary** | Losses accumulate quietly until the contractor vanishes | s.17 deadline alerts; running dues | Light (ASR only) | Very high | "Weekly wages overdue by 2 days" alert | AI not foundational enough; low novelty |
| E | Obvious baseline: voice diary → English PDF | — | — | ASR + LLM (often also doing the maths) | Very high | PDF | Hallucinated or hardcoded wages; no read-back; overclaims; undifferentiated |

**Cut in one line each:**
- **IVR/missed-call diary:** needs telephony infrastructure; not buildable offline in 10 h. Kept as deployment phase 3.
- **Rights chatbot:** generic; produces no evidence.
- **Public "bad employer" map:** defamation and retaliation risk; needs network effects.
- **UPI/payslip OCR-only:** most pay is cash. Folded into A as a stretch.
- **Standalone BOCW 90-day tracker:** the certificate must come from the employer; overclaim risk. Kept as secondary messaging.
- **GPS-geofenced attendance:** location surveillance. Rejected.
- **Covert recording of the contractor:** unsafe and legally risky. Rejected.
- **Free-form AI "debate" or negotiation with the thekedar (in person or by AI phone call):** rejected after review with you. It risks retaliation (workers fear job loss and false theft accusations, Aajeevika p.272/284), AI legal misstatements, the AI "accepting" a deal on her behalf, and unreliable ASR in heated multi-speaker speech. Replaced by worker-controlled **Bol ke Batao (speak-for-me)**. A **bounded responder** (replying to disputes only with ledger facts) is deferred.
- **Blockchain timestamping:** needs internet. SMS anchoring achieves the same goal offline. Rejected.

D's alerts and C's paralegal view are **folded into A** as a SHOULD and a hub mode respectively.

### 4.2 How A beats the obvious PS07 entry, on things judges will notice

| Obvious entry | Apna Hisaab |
|---|---|
| English UI and English PDF | Marathi/Hindi voice in **and voice out**; bilingual packet |
| LLM computes or hardcodes "minimum wage ₹X" | Deterministic engine citing **notification 7997 / 05.08.2026, SN 11, zone and category, validity window**; refuses outside the window |
| LLM guesses missing values | Evidence-span grounding plus two-reader check; amber or red fields; worker confirmation required |
| "Legally valid claim" rhetoric | Forum-neutral dues statement and evidence file mapped to Form II heads; honest disclaimers |
| No employer identity | Contractor → builder chain; site-board photo; witnesses |
| No integrity | Hash chain, audio hashes, tamper demo, SMS anchor |
| Implicit cloud | Wi-Fi visibly off; named open models with parameter counts |
| A static PDF is the end of the story | **Hisaab Saathi** explains the case aloud, plays the *exact* clip behind each difference, asks before sending it on WhatsApp (thekedar or union), and can speak a polite factual statement to the thekedar, logging his promise |

### 4.3 Hard gates

| Gate | A | B | C | D | E |
|---|---|---|---|---|---|
| Competition compliance (open AI foundational; no closed core) | ✅ | ✅ | ✅ | ⚠️ AI thin | ✅ |
| Worker safety (no surveillance or covert recording; worker-controlled) | ✅ | ⚠️ group pressure | ✅ | ✅ | ⚠️ overclaims |
| Credible offline operation | ✅ | ⚠️ sync | ⚠️ import path | ✅ | ✅ |
| Viable 10-h MVP | ✅ | ❌ | ✅ | ✅ | ✅ |

B fails the 10-hour gate and D fails track fit, so both are eliminated. C passes only with local file import.

### 4.4 Comparison (*our own decision aid; no official rubric exists*)

Weights: impact 20, track fit 15, originality 15, feasibility 15, reliability/offline 10, worker trust and safety 15, demo clarity 10. Scores are 1–5, then weighted to 100.

| | Impact | Track | Orig. | Feas. | Rel. | Trust | Demo | **Total** |
|---|---|---|---|---|---|---|---|---|
| **A** | 5 | 5 | 4 | 4 | 4 | 5 | 5 | **92** |
| C | 4 | 5 | 3 | 4 | 4 | 4 | 3 | 78 |
| E | 3 | 4 | 1 | 5 | 4 | 2 | 3 | 62 |

**Winner A vs. runner-up C:** only worker-side, same-day capture creates *contemporaneous* evidence, and that is the scarce asset LEAD-style paralegals lack. C only processes memories after the fact. A also includes C's paralegal view as its hub mode.

**What would falsify A:** field validation (§3.10, Q3) shows workers will not record even on paydays, or that recording is unsafe. In that case, **pivot to C (hub-interview mode) on the same codebase**. Second falsifier: Marathi entity accuracy too low even with confirmation. Then switch capture to tap-first (clock and keypad) and keep voice for narrative and identities.

**Strongest counterargument:** "Logging apps die from non-use. The workers most at risk (living on site, dependent on the contractor) are least able to log. The bottleneck is enforcement, not documentation."

**Response:**
- The design is payday-centric (minimum effort, logging when it matters) with hub-assisted onboarding.
- It plugs into existing mediation channels rather than courts.
- Its weekly hub mode serves low-autonomy workers.
- Adoption is still **unproven** and we will say so.

---

## 5. Product and experience

### 5.1 Primary user, job-to-be-done, MVP promise

- **Primary user:** "Sunita" (synthetic persona): an unskilled helper on a private building site in Chhatrapati Sambhajinagar (Zone I), hired by a thekedar, Marathi-speaking, low literacy, using a shared Android phone.
- **Job-to-be-done:** "When the thekedar reads out his hisaab, help me know, and show, exactly what I'm owed, in my language, without writing anything."
- **MVP promise:** daily voice log → confirmed ledger → payday hisaab check → paralegal-ready packet, entirely offline.

### 5.2 Scope

| Tier | Items |
|---|---|
| **MUST** (demo dies without it) | Onboarding (language, consent, PIN, category, site with sphere and zone confirm, contractor)<br>**Mobile web app over HTTPS (mkcert) usable from a phone; installable as a PWA (manifest + service worker) — your requirement**<br>Voice log (workday, payment): **flexible length** (no minimum; soft cap 60 s) plus a one-tap **"Same as yesterday / कालसारखं"** that copies yesterday's confirmed hours and site for re-confirmation → audio saved and hashed **first** → ASR → normalizer + LLM extraction → reconcile → confirmation card (green/amber/red) → confirm → hash-chained ledger<br>Deterministic wage engine with provenance<br>Hisaab screen<br>Packet (HTML → PDF) with dues statement, day table, computation, evidence index<br>Seeded synthetic 2-week scenario<br>Offline operation |
| **SHOULD** (in priority order) | 1. TTS read-back (hi/mr)<br>2. **Hisaab check** (speak the contractor's settlement → itemised discrepancies)<br>3. **Hisaab Saathi:**<br>&nbsp;&nbsp;• **Samjhao**: explains the case aloud from engine results; voice follow-up Q&A gets pre-approved answers<br>&nbsp;&nbsp;• **Saboot**: exact-clip excerpt per discrepancy, with hashes<br>&nbsp;&nbsp;• **Bhejo**: asks "send to thekedar?" with a risk note and a union alternative; WhatsApp via the share sheet, or download + `wa.me` link<br>&nbsp;&nbsp;• **Bol ke Batao**: speak-for-me statement to the thekedar; announced reply recording → promise log + reminder<br>4. Chain verification and tamper demo<br>5. Evidence coach checklist ("packet completeness 8/12", *not* a legal score)<br>6. s.17 late-payment flags<br>7. Witness statement (co-worker voice, consented)<br>8. Deletion tombstones |
| **STRETCH** | Site-board photo (stored and hashed; OCR via Gemma 4 vision) · SMS anchor ("send code to trusted contact" via `sms:` link) · central-sphere rate pack (Oct 2026) · IndicTrans2 English gloss · PWA install and local-Wi-Fi hub sync from a real phone · **HTTPS hub so the phone's Web Share sheet can attach clips directly to WhatsApp** · group packet (s.45(5)) |
| **DEFERRED** | On-device inference · IVR · multi-device crypto attestation · other states and languages · Form II auto-fill and filing · cloud anything · **bounded responder** (AI answers disputes with ledger facts) |
| **REJECTED** | Free-form AI debate or negotiation with the thekedar · AI phone calls to the thekedar · covert recording · automatic sending |

### 5.3 User journey

0. **Hub onboarding (5 min, assisted, once).**
   - Pick a language with audio prompts.
   - Hear a consent message in your language: what is recorded, kept on this device and hub only, never sent to the employer, deletable any time. Choose "Keep my voice recordings: Yes / No (transcript only, weaker evidence)".
   - Set a PIN.
   - Pick your work category from pictures (helper, mason, carpenter…), mapped to unskilled, semi-skilled or skilled with an explainer; **confirm**.
   - Set up the site: name and landmark; city → zone suggestion → **confirm**; "Is this for railways, a central PSU, an airport, a port or mines?" → sphere.
   - Contractor name and phone *as known*; usual hours and break; agreed rate and pay period *if known*. Each item can be "don't know", which stays empty.
1. **Daily log.**
   - Tap the big 🎙️ "आजचे काम / आज का काम" and speak up to 30 s, e.g. *"आज सकाळी नऊ ते संध्याकाळी सात काम केलं, कैलास ठेकेदार, साईटवर सुरेशपण होता."* ("Today I worked from nine in the morning to seven in the evening, contractor Kailas, Suresh was also on site.")
   - The screen shows "Saved ✓ (audio hash 7F3A…)" immediately, then a card: 📅 13 Oct · 🕘 09:00 → 🕖 19:00 · ☕ 60 min (your usual break, **amber: assumed — confirm**) · 👷 Kailas · 👥 Suresh.
   - The app reads the card back in Marathi. Tap ✅ बरोबर or ✏️ बदला.
2. **Payment.** 💵 "पैसे मिळाले / पैसा मिला" → amount, mode and date → card → confirm.
3. **Missing or uncertain fields.**
   - Amber: the app asks one question at a time ("संध्याकाळी किती वाजता काम संपलं?" — "What time did work end in the evening?"), with a clock picker or keypad as alternatives.
   - "Don't know" leaves the field missing. The app never guesses.
4. **Evidence coach** (contextual, max 1 prompt per day):
   - first day at a new site → "photo of the site board?";
   - once → "co-worker statement?";
   - weekly → "send your code to your union/family?".
5. **Hisaab check (payday).**
   - Tap 📒 "हिशोब तपासा" and speak what the thekedar said (*"12 दिवस, 600 रोज, 2000 उचल कापली"* — "12 days, 600 a day, 2000 advance deducted").
   - App: "Your record has **13** days (6 Oct missing from his count). The legal minimum is ₹864/day (Zone I, unskilled, notification 7997). Your dues are ₹14,039; you received ₹4,500, so **₹9,539 is outstanding** (estimate). He deducted a ₹2,000 'advance' that you marked as not received."
   - The **Hisaab Saathi** then guides her:
     - **5a Samjhao (explain).** The app speaks 4–6 short sentences built from the engine results (e.g., "You worked 13 days. The law says at least ₹864 a day. You received ₹4,500. About ₹9,539 may still be due. His count skips 6 Oct.").
       - She can ask by voice, e.g. "अब मैं क्या करूँ?" ("What do I do now?") or "हे कायद्यात कुठे आहे?" ("Where does the law say this?").
       - The LLM maps the question to a fixed intent, and the app plays a pre-written, reviewed answer. Anything else gets "ask your union or legal aid".
     - **5b Saboot (exact proof).** Each difference has a "▶ proof" button that plays the **exact 5–10 s excerpt**, e.g. her 6 Oct note "६ तारखेला सकाळी नऊ ते सात…" ("on the 6th, from nine in the morning to seven…"). The excerpt is cut using the ASR segment timestamps around the confirmed evidence quote, and its own hash plus the parent hash are logged.
     - **5c Bhejo (send?).**
       - The app asks: "Do you want to send this to the thekedar?"
       - A short spoken risk note follows: "He will know you keep records; sending to your union first may be safer."
       - Choices: [Send to thekedar] [Send to union/helper] [Not now].
       - The payload is a polite summary text plus the clips she ticks (default: the discrepancy's excerpt; **witness audio excluded unless she opts in**), plus the dues statement for the union.
       - It opens WhatsApp through the phone's share sheet, or saves the files and opens a `wa.me` link with the text prefilled. Sending needs internet; WhatsApp queues it if she is offline.
     - **5d Bol ke Batao (speak for me).** In person, or on speaker during a call, she presses ▶.
       - The phone politely states the facts in the thekedar's language (days and payments, a request for a written hisaab and a payment date; the minimum-wage line is opt-in).
       - Then: "Record his reply?" → the phone **announces** "this is being recorded so the hisaab stays clear" and records up to 30 s.
       - ASR + LLM extract any promise ("₹5,000 on Monday"); she confirms → `PROMISE_LOGGED` + an in-app reminder.
       - A hostile reply → stop; the app shows union and helpline contacts.
     - Or skip all this and export the packet for a paralegal.
6. **Wage view:** per-day table and totals. Tapping any amount shows its formula and source.
7. **Export:**
   - choose the period → preview → PIN → `packet.pdf` + `bundle.zip`;
   - share only by explicit action (print, USB, hub);
   - witness names can be redacted.
8. **Privacy:** delete an entry (leaves a tombstone event), wipe all, change PIN.

### 5.4 Safeguards

- **Consent:** spoken consent at onboarding and for each witness statement (the co-worker states consent on the recording).
- **No covert recording:** the worker records their own account. The contractor's hisaab is **narrated by the worker afterwards**. The thekedar's voice is captured only in Bol ke Batao, **after a spoken announcement** that cannot be switched off, with an instant Stop.
- **AI never contacts or negotiates with the employer.** It speaks only fixed, polite, factual templates when the worker presses play. Nothing is ever sent automatically.
- **Minimisation:**
  - no GPS (site described in words);
  - no Aadhaar;
  - name optional (a nickname is fine);
  - phone numbers only as the worker chooses.
- **Access:** PIN per worker profile (shared phones); discreet neutral app name; no employer portal; no auto-upload.
- **Sharing (Bhejo):** worker-initiated only, behind a spoken risk note. Union-first is offered and witness audio excluded by default. Shared copies are excerpts, while the originals and hashes stay on the device. Each share is logged in the chain. Once on WhatsApp, data leaves the app's control; the worker is told this.
- **Integrity vs. deletion:** deletion removes the content but keeps a hash tombstone so the chain stays verifiable; the packet discloses deletions.
- **Retention:** data stays on the device or hub until the worker deletes it; the default prompt asks after a claim period closes.
- **Law:** DPDP Rules 2025 were notified in Nov 2025; core fiduciary obligations start around **13–14 May 2027** **[S]** ([summary](https://www.mondaq.com/india/data-protection/1708164/digital-personal-data-protection-rules-2025-notified)). The design aligns now (notice, consent, purpose limitation, deletion). In deployment, the hub operator is the data fiduciary.

### 5.5 Offline behaviour and error states

- **All AI is local.** `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`; the LLM server binds to 127.0.0.1; fonts are bundled; no CDNs or telemetry.
- **Audio is written before processing.** If AI is busy or down, the entry shows "Saved ✓ — will understand later" and a queue resumes after restart.
- **Errors:**
  - mic denied → keypad and picker capture;
  - no speech or low confidence → "couldn't hear clearly, please repeat" (audio kept);
  - invalid LLM JSON → one retry, then normalizer-only values (all amber);
  - rate missing or out of window → "Comparison unavailable: need X", **no number shown**;
  - TTS failure → card stays on screen plus "▶ replay my recording".

### 5.6 Accessibility and localisation priorities

- Icons and numerals first; minimal text.
- Every screen has a one-tap audio prompt in hi/mr, pre-generated with Indic Parler-TTS on build day.
- Touch targets ≥48 px; high contrast; Latin digits with Devanagari labels (validate in the field, Q4).
- Marathi and Hindi first; English for the paralegal and packet.

### 5.7 Explicit exclusions

- Not a lawyer and not "proof"; it neither files claims nor contacts employers.
- No GPS, no covert recording, no employer ratings, no cloud accounts.
- No autonomous AI talking to, arguing with, phoning or negotiating with the thekedar; no free-form LLM speech to the employer.
- No piece-rate or multi-employer-per-day computation in the MVP (these are flagged for the paralegal).
- No automatic weekly-rest-day pay, bonus or compensation computation (listed as "not computed — authority decides").

---

## 6. Architecture and model choice

### 6.1 Components and data flow

```
[Worker UI: React (Vite) mobile web/PWA · hi / mr / en · icons + audio prompts]
   │ MediaRecorder, flexible length (no minimum; soft cap 60 s; chunked for ASR) · taps · photos
   ▼
[Hub server: FastAPI (Python 3.11) on 127.0.0.1 / local Wi-Fi]
 1 Intake ──── write original bytes → SHA-256 → event AUDIO_SAVED → ffmpeg → 16 kHz mono WAV
 2 ASR ─────── faster-whisper / CTranslate2 (GPU int8_float16)
               hi → IndicWhisper-hi │ mr → IndicWhisper-mr │ fallback → Whisper large-v3-turbo
               → transcript + segment confidences (avg_logprob, no_speech_prob)
 3 Normalizer  deterministic: Devanagari digits, hi/mr number words, सवा/साढ़े/पौने/डेढ़/ढाई,
               सव्वा/साडे/पावणे/दीड/अडीच, parts of day, relative dates (ambiguous → ask)
 4 Extractor ─ llama.cpp llama-server · Qwen3-4B-Instruct-2507 Q4_K_M · JSON-schema-constrained · T=0
               → fields {value, evidence_quote}
 5 Reconciler  deterministic: evidence-span grounding · two-reader agreement · plausibility
               → green / amber / red per field
 6 Read-back ─ deterministic hi/mr sentence template → Indic Parler-TTS (GPU fp16) → WAV (cached)
   ◄────────── card + audio → worker confirms / edits → event ENTRY_CONFIRMED
 7 Ledger ──── SQLite (WAL) + append-only SHA-256 hash-chained events
 8 Rates+Engine resolver (sphere/state, employment, category, zone, date) → rate_packs/*.json
               (provenance, validity) → pure-Python Decimal wage engine
 9 Coach ───── deterministic completeness checklist
10 Hisaab check LLM parses contractor's settlement (schema) → engine compares → read-back
11 Packet ──── Jinja2 HTML + bundled Noto Sans Devanagari → PDF (Playwright Chromium)
               + bundle.zip (audio, photos, ledger.json, manifest.json of SHA-256, chain head)
12 Saathi ──── (Hisaab Saathi voice agent; worker-controlled)
   Samjhao      engine results → hi/mr explanation template → TTS
                follow-up question → ASR → LLM intent (fixed enum) → pre-approved answer → TTS
                (unknown → "ask your union / legal aid")
   Saboot       discrepancy → linked entries → confirmed evidence quote → ASR segment/word
                timestamps → ffmpeg excerpt (5–10 s) → SHA-256 + parent hash + offsets
   Bhejo        "send to thekedar?" → spoken risk note → [thekedar | union | not now]
                → payload (polite summary text + ticked excerpts [+ dues PDF])
                → Web Share sheet (secure context) or download + wa.me link → WhatsApp (needs internet)
   Bol ke Batao fact-only hi/mr template → TTS on speaker → mandatory spoken recording notice
                → reply ≤30 s → ASR → LLM reply schema (promise / dispute / refuse / hostile)
                → worker confirms → PROMISE_LOGGED + reminder · hostile → stop + contacts
```

### 6.2 Deterministic vs. model-driven responsibilities

| Step | Done by | Rationale |
|---|---|---|
| Speech → text | **ASR model** | Own-language input without literacy |
| Numbers, times, dates | **Deterministic normalizer**, cross-checked against the LLM | Entity-dense speech is where ASR and LLMs fail (§3.8) |
| Who, where, what, how much (fields and evidence quotes) | **LLM, schema-constrained** | Free speech → structure is the LLM's real value |
| Grounding, plausibility, confidence | Deterministic | Auditable; no hidden judgement |
| Read-back sentence | Deterministic template; **TTS model speaks it** | The TTS never voices unconfirmed LLM free text |
| Confirmation | **Human (worker)** | Nothing counts until confirmed |
| Jurisdiction and rate selection | Deterministic resolver plus human confirmation | Law is not inferred |
| Arithmetic and Form II head mapping | **Deterministic engine** | Must be exact and explainable |
| Contractor-settlement parsing | LLM (schema), then deterministic comparison | — |
| Packet text | Deterministic templates; verbatim transcripts; optional machine gloss labelled as such | No generated legal prose |
| Integrity | Deterministic crypto (SHA-256 chain) | — |
| Explaining the case to the worker (Samjhao) | Deterministic template filled from engine output; **TTS speaks** | Numbers can never drift from the computation |
| Worker's follow-up voice questions | **LLM classifies** into a fixed intent enum → pre-written, reviewed answers; out-of-scope → referral | No free-form legal advice |
| Picking the exact proof clip (Saboot) | Deterministic: evidence quote ↔ ASR segment timestamps → ffmpeg excerpt | Traceable to the original hash |
| Statement to the thekedar (Bol ke Batao) | Deterministic template; **TTS speaks** when the worker presses play | The AI never improvises to the employer |
| Thekedar's reply | ASR → **LLM reply/promise schema** → worker confirms | Promises are logged, never negotiated |
| Sending on WhatsApp (Bhejo) | **Worker action only** (share sheet or `wa.me`) | Consent and control |

### 6.3 Models to name in the proposal and README (verified on Hugging Face or primary repos)

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

### 6.4 Alternatives compared

| Choice | Option | For | Against |
|---|---|---|---|
| ASR | **IndicWhisper hi/mr** | Best published Indic WER: Hindi avg **13.6**, Marathi avg **18.2**, vs. Google/Azure/NVIDIA on Hindi (Google 23.9, Azure 20.0) **[V]** ([Vistaar](https://github.com/AI4Bharat/vistaar)); MIT; ungated | Per-language models; 2023 vintage; noisy Hindi (Gramvaani) still 26.8; download host must be checked |
| | Whisper large-v3-turbo | One model; code-mix; easy | Weaker Indic accuracy (third-party Hindi report for large-v3: 32.4 WER on Lahaja **[S]**) |
| | Gemma 4 E4B audio | One model for ASR, extraction and OCR; Apache-2.0 | **30 s audio cap**; Ollama lists only text and image input **[V]** ([Ollama](https://ollama.com/library/gemma4)); higher VRAM; unbenchmarked on hi/mr |
| LLM | **Qwen3-4B-Instruct-2507** | 2.5 GB; mature llama.cpp support; leaves VRAM headroom for TTS | Marathi extraction quality unbenchmarked |
| | Gemma 4 E4B | Strong multilingual (pretrained on 140+ languages); vision | ~6 GB with projector; contention with TTS on 8 GB |
| TTS | **Indic Parler-TTS** | Open-weight; hi and mr; Apache-2.0 | Speed and number pronunciation unbenchmarked |
| | Browser/OS TTS | Zero cost | Not open-weight; offline voices vary → last-resort fallback only |

### 6.5 Hardware fit (you confirmed: target 8 GB, with 4 GB and CPU fallbacks)

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

### 6.6 Evidence gaps (nothing below is benchmarked yet)

- ASR entity accuracy on *our* phone-recorded hi/mr/Hinglish audio.
- Qwen3-4B vs. Gemma 4 field accuracy on Marathi transcripts.
- Parler-TTS latency and how it reads digits in Marathi.
- Co-resident VRAM of all three models.
- Whether the IndicWhisper object-store download is still live.
- Gemma 4 audio support in llama.cpp.
- Playwright Chromium offline install on the build laptop.
- Tier B and C latencies.

All of these are scheduled for 14–15 Oct (§7.2).

---

## 7. Pre-build prep and 10-hour build plan

### 7.1 Tonight (Tue 13 Oct, before midnight)

1. **Submit the PPT**, using §1, §3 (evidence), §4.2 (USP), §6.3 (models with params and licenses), §6.5/§7 (feasibility) and the Sources list.
2. ~~Send the coordinator questions~~ **Done: answers recorded in §9.1.**
3. On Hugging Face: **accept the Indic Parler-TTS terms**; request IndicConformer and IndicTrans2 access (optional).
4. Start overnight downloads (list in §7.2).

### 7.2 Wed 14 – Fri 16 Oct (prep only; no product code)

| Day | Task | Output | Originality note |
|---|---|---|---|
| **14 Oct** | Secure the 8 GB laptop; record GPU, driver and OS. Install the NVIDIA driver, Python 3.11 (uv/conda), Node 22, Git, ffmpeg, llama.cpp CUDA build, and pip packages (faster-whisper, ctranslate2, torch CUDA, transformers, parler-tts, fastapi, uvicorn, jinja2, playwright + `playwright install chromium`, pytest). Build pip wheel and npm caches. | Working offline toolchain | Environment prep |
| 14 Oct | Download (~25–30 GB **[E]**): Qwen3-4B Q4_K_M; Qwen3-1.7B Q4_K_M; Gemma 4 E4B Q4_K_M + mmproj; whisper-large-v3-turbo CT2; IndicWhisper hi and mr zips → CT2 conversion; Indic Parler-TTS; whisper-small CT2; Noto Sans Devanagari. **Copy everything to a USB SSD.** | Models on SSD and backup | Downloads |
| 14 Oct (07:00–09:00) | Field validation (§3.10) if a union or NGO contact is available | Notes against Q1–Q7 | Research |
| 15 Oct | Record **≥20 SYNTHETIC clips** (solo: your voice plus 1–2 friends or family): mr, hi and Hinglish; 3–20 s each; 2 phones; ≥4 with site noise. Work from scripts with a ground-truth sheet; written consent from each speaker. | Test set + truth sheet | Data |
| 14 Oct | **HTTPS for the phone:** install mkcert, `mkcert -install`, create a cert for the laptop's LAN IP(s) + localhost, install the root CA on the demo Android phone. Check with an off-the-shelf static HTTPS server (e.g., `npx http-server -S`) that the phone shows a valid lock. Phone mic, PWA install and Web Share all **require a secure context**. | Trusted HTTPS on phone | Environment |
| 15 Oct | **Benchmarks using CLIs only:** ASR entity accuracy and latency per model; `llama-server --json-schema` extraction (Qwen3-4B vs. Gemma 4 E4B); TTS (10 sentences with numbers); peak VRAM with all three loaded. Repeat the key checks on the 4 GB laptop. | `benchmark.md` table and defaults chosen | Measurements, not product code |
| 16 Oct | Verify the **original Marathi notification 7997** and the construction zone definitions. Fill the rate-pack data sheet. Hand-compute the oracle fixtures F1–F8 (§10.7) in a spreadsheet. | Verified rate data + oracle | Data transcription |
| 16 Oct | Content: hi/mr/en string sheet; read-back templates; consent script; coach prompts; **Saathi texts** (13 FAQ answers, Samjhao lines, thekedar statement, recording notice, risk note), each fact-checked against §3.5; persona and demo script; few-shot examples (all kept in `planning/`). | Content sheets | Design artefacts |
| 16 Oct | **Offline rehearsal** (Wi-Fi off; load every model via CLI). Create an empty public repo with LICENSE only if coordinators allow. Test hotspot git push. | Go/no-go per tier | — |
| 16 Oct | Pack: 3 laptops, chargers, extension board, USB mic, 2 Android phones, USB SSD (models, wheels, installers), printed runbook and demo script. | Kit | — |

**Benchmark decision rules:**
- Default ASR per language = highest entity accuracy (times, amounts, names), not WER alone.
- LLM = highest field accuracy at 100% schema-valid JSON. Switch to Gemma 4 only if it beats Qwen3-4B by ≥10 points on Marathi **and** fits alongside TTS.
- If Parler mispronounces digits, the read-back template emits number words.

**Originality:** everything above is environment, downloads, measurement, data or design. Confirm with coordinators (§9.1 Q3). Keep it in `planning/` and docs, not the product repo, and list it in the README under "Preparation before the event".

### 7.3 Build day: Sat 17 Oct, 07:00–17:00, at the college (solo build, with Claude Code as a coding assistant)

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

---

## 8. Acceptance tests, demo, and judge Q&A

### 8.1 Measurable acceptance criteria

| ID | Criterion | How to check |
|---|---|---|
| AC1 | Every recording is persisted with its SHA-256 **before** any AI call. Killing the server mid-ASR loses nothing. | Kill the process during processing → the entry is listed as "saved" after restart |
| AC2 | 10 scripted demo clips (5 hi, 5 mr): ≥80% of numeric fields (date, start, end, amount) correct *before* correction **[target]**; 100% after the confirm flow | Compare against the ground-truth sheet; record actual numbers in README |
| AC3 | 5 adversarial transcripts (no amount; no end time; Hindi "कल"; no contractor; two amounts): **0 ungrounded values stored**. Each missing value shows red or amber with a question. | Unit and integration test |
| AC4 | When the LLM and the normalizer disagree, the field turns amber and both candidates are shown | Fixture transcript |
| AC5 | Wage engine fixtures F1–F9 (§10.7) pass **exactly**, including the error codes (no number shown on error) | pytest |
| AC6 | Every amount (screen and PDF) exposes its formula and source: notification no., date, SN, zone, category, validity window, divisor status | Manual check |
| AC7 | hi and mr read-back plays for confirm cards; ≤5 s on Tier A **[target]** | Stopwatch / logs |
| AC8 | Tier A p50 ≤12 s from stop-recording to card for typical 3–20 s clips **[target]** | Logged timings |
| AC9 | With **all network adapters disabled**, the full demo path works and makes no outbound connections | Windows Resource Monitor / `netstat -b` |
| AC10 | Editing any `events` row directly in SQLite → `verify` reports the first broken seq. Manifest hashes match `certutil -hashfile <f> SHA256`. | Tamper demo |
| AC11 | PDF renders Devanagari conjuncts correctly and contains: dues statement, day table, computation with Form II heads, assumptions, "not computed" list, evidence index, chain head, disclaimer, declaration box; "SYNTHETIC DEMO DATA" watermark in demo mode | Visual check |
| AC12 | After restart, unprocessed audio appears and can be processed | Restart test |
| AC13 | Deleting an entry removes it from the UI and exports but leaves a tombstone. "Wipe" removes the DB and media. | Manual check |
| AC14 | No geolocation permission requested; PIN required to open a profile and to export | Browser permission panel |
| AC15 | README has exact models, params, quantisation, license links, no-closed-API statement, AI-assisted-coding disclosure, prep disclosure, measured latencies, rate sources with dates and verification status. LICENSE is Apache-2.0. `grep -ri "openai\|anthropic\|generativeai"` in code finds no API clients. | Checklist |
| AC21 | **Phone app:** served over HTTPS (mkcert, valid lock); installs as a PWA; the mic works on the phone. With the hub unreachable, a recording queues in IndexedDB and uploads later with its hash unchanged. "Same as yesterday" creates an amber entry that requires confirmation. | Android phone walkthrough |
| AC16 | **Samjhao:** every number spoken or shown equals the engine output for the same period (no rounding drift). An out-of-scope voice question ("Should I sue him?") gets the referral answer, never free text. | Fixture comparison; 5 scripted questions |
| AC17 | **Saboot:** for 5 discrepancies in the seeded data, the excerpt contains the evidence phrase (manual listen). Excerpt SHA-256, parent hash and offsets are logged (`EXCERPT_CREATED`). No matching segment → whole note offered. | Manual check + event check |
| AC18 | **Bhejo:** nothing can be sent without (a) the "send to thekedar?" question, (b) the spoken risk note, (c) explicit confirmation. Witness audio is excluded unless opted in. `SHARE_PREPARED` logs recipient role and item hashes. Works with no internet (download + `wa.me` fallback). | Walkthrough |
| AC19 | **Bol ke Batao:** only template text is spoken to the thekedar. Reply recording cannot start without the spoken notice. Stop works instantly. | Walkthrough |
| AC20 | **Promise extraction:** in 3 scripted replies ("Somvaar ko 5,000 dunga", "Abhi paisa nahi hai", an abusive line), outputs are `promise_to_pay` (₹5,000; date asked if ambiguous), `refuses`, `hostile`. Hostile stops the flow and shows contacts. Promises need worker confirmation and are hash-logged. | Scripted test |

### 8.2 Edge-case test plan

| Case | Input | Expected behaviour |
|---|---|---|
| Noisy audio | Site-noise clip | Low ASR confidence → amber → the app asks; audio kept |
| Code-switched speech | "aaj 9 baje se 7 baje tak kaam kiya, 500 mila" | Fields extracted; normalizer and LLM agree → green |
| Uncertain numbers | "साढ़े नौ से सात" | Start 09:30. End 19:00 shown **amber** ("7 after 9:30 → evening, inferred") |
| Ambiguous date | Hindi "कल" | Date amber → "Yesterday or tomorrow?" (never guessed) |
| Missing field | No end time | End time red → question. If the worker says "full day", the day counts at the normal rate with OT = 0, flagged `HOURS_NOT_RECORDED` |
| Wrong jurisdiction | Site marked railway / central PSU | Maharashtra rates **not** applied → "Central-sphere rates apply" (central pack is a stretch; otherwise "not loaded") |
| Date outside the rate window | Entry dated 2027-01-05 | `RATE_OUT_OF_WINDOW`; comparison unavailable for that day |
| Category or zone unknown | Not set | `CATEGORY_UNKNOWN` / `ZONE_UNCONFIRMED`; no number shown |
| Stale pack | Today > `effective_to` | Banner: "Rates may be outdated — check the latest notification" |
| Offline | Wi-Fi off | Everything works (AC9) |
| App restart | Kill mid-processing | Queue resumes (AC12) |
| LLM down | Stop llama-server | Normalizer-only values, all amber; no crash |
| TTS down | Disable TTS | Card plus "replay my recording" |
| Over-long note | 45 s recording | UI stops at 30 s and asks for a second note |
| Export | Pick a period | PDF and ZIP produced; hashes verify |
| Deletion and privacy | Delete an entry | Tombstone kept; the packet states the number of deletions |
| Shared phone | Second profile | Separate data, separate PIN |
| Tamper | Edit a DB row | "Chain broken at event N" |
| Exact clip not found | Evidence quote not inside any ASR segment | Offer the whole note; label "full recording" |
| Worker wants to send witness audio to the thekedar | Ticks a witness clip | Extra warning ("this can expose Suresh"); explicit second confirmation |
| No internet when sending | Bhejo offline | Files saved; `wa.me` link opens WhatsApp, which queues the message; status "handed to WhatsApp" |
| Web Share unavailable (HTTP hub) | Phone on the LAN hub over http | Falls back to download + `wa.me` text link |
| Thekedar's reply is abusive or threatening | Hostile line | Recording stops; safety message; union/helpline contacts; nothing argued back |
| Thekedar refuses to be recorded | Says "band karo" | Worker taps Stop; nothing is kept beyond the notice |
| Ambiguous promise date ("agle hafte") | Reply audio | Promise logged with date **ambiguous** → worker asked to set it or leave it open |

> **Judges come to your desk (coordinators, 13 Oct).** Keep the app running and run the **3-min desk version** by default: live Marathi note → read-back → hisaab check → Saboot clip → Bhejo prompt → packet. Offer the full version below if they have time. Reset the demo data between judges with one command, and keep the printed A4 summary on the desk.

### 8.3 Demo script (~6 min, **all data synthetic and labelled**, Wi-Fi visibly off; for a 5-min slot, shorten Samjhao and skip the reply recording)

Cast (all fictional): **Sunita** (helper, Marathi), thekedar **"Kailas"**, builder **"Example Developers"**, site "Example Heights", Zone I, Chhatrapati Sambhajinagar.

| Time | Beat | What judges see |
|---|---|---|
| 0:00–0:25 | **Hook** | "Sunita worked 13 days. On payday the thekedar's hisaab: '12 days × ₹600, minus ₹2,000 advance'. She has nothing written down, and across 13,088 wage-theft cases one NGO found employers avoid every document that would prove she worked." |
| 0:25–0:40 | **Open and offline** | Wi-Fi off; "IndicWhisper, Qwen3-4B, Indic Parler-TTS: all on this laptop" |
| 0:40–1:40 | **Live Marathi note** | Teammate speaks → "Saved ✓ #7F3A…" → card with the break shown **amber (assumed)** → **Marathi read-back** → correct the end time with the picker → ✅ |
| 1:40–2:00 | **Hindi/Hinglish payment** | "Paisa mila" → ₹2,500 cash → confirm |
| 2:00–2:40 | **Hisaab check** | Speak the thekedar's settlement → itemised result: **6 Oct missing from his count**; rate ₹600 vs. **₹864 legal minimum**; OT unpaid; "advance" disputed. Tap an amount → formula and **notification 7997 · 05.08.2026 · SN 11 · Zone I · unskilled · valid 01.07–31.12.2026**. Read back in Marathi: "≈ ₹9,539 outstanding (estimate)" |
| 2:40–3:05 | **Samjhao** | The Saathi explains in simple Marathi ("13 days… at least ₹864 a day… about ₹9,539 may be due… his count skips 6 Oct"). The worker asks "आता मी काय करू?" ("What do I do now?") → a pre-approved answer listing her options |
| 3:05–3:20 | **Saboot** | Tap "6 Oct missing" → **▶ plays the exact 6-second excerpt** of her 6 Oct note, with its hash code |
| 3:20–3:45 | **Bhejo** | "Send this to the thekedar?" → spoken risk note → she picks *thekedar* → WhatsApp opens with the polite summary and that clip. Shown on a teammate's phone with data; the laptop stays offline. |
| 3:45–4:25 | **Bol ke Batao** | A teammate plays the thekedar. Her phone states the facts politely in Hindi and **announces** recording. He replies "Somvaar ko 5,000 de dunga" → the app logs a **promise of ₹5,000 by Mon 19 Oct** (hash-chained) with a reminder. "The AI never argues; it states facts and records promises." |
| 4:25–5:00 | **Packet + tamper** (coach: "completeness 9/12") | PDF: dues statement (mr + en), day table, Form II heads, SHA-256 index. Change one DB value → **"Chain broken at event 37"** |
| 5:00–5:30 | **Deployment + honesty** | Hub laptop at a union / NGO / DLSA; phones sync over local Wi-Fi; Tier B/C fallbacks. Limits: device clock, not proof, rates need verification |
| 5:30–5:45 | **Close** | "Not the thekedar's hisaab: her own." Ask: pilot with a union or DLSA. |

**Backups:**
- Live ASR fails → "upload recording" with a pre-recorded clip.
- Laptop fails → backup video plus screenshots.
- Any step stalls → say what should happen and move on.

### 8.4 Hardest judge questions, with honest answers

1. **"Is this legally valid?"** No tool makes evidence valid. It is a contemporaneous, worker-confirmed, tamper-evident record with original audio and witnesses: the kind of informal documentation legal-aid cells already turn into settlements (LEAD: ₹15 crore, 60,000+ workers). For courts, a BSA s.63(4) certificate needs hash values (Part A), and our packet lists them. Part B needs an expert. Claims under Code on Wages s.45 must be filed within 3 years.
2. **"Couldn't a worker fake entries?"** Any self-record can be faked. We make it harder and visible: daily contemporaneous entries, hash chain, SMS and hub anchors, co-worker statements, and consistency checks. The employer's statutory registers (Form I wages, Form IX muster roll) are the counter-record, and our day table uses the same columns so an inspector can compare line by line.
3. **"How accurate is Marathi ASR?"** Published IndicWhisper averages: Marathi 18.2 WER, Hindi 13.6; noisy Hindi 26.8. Our benchmark on 30 synthetic clips: *[fill in measured numbers]*. That is exactly why numbers are cross-checked, read back and confirmed.
4. **"LLM hallucinations?"** Schema-constrained decoding, evidence quotes required, null when not said, two-reader check. The LLM never computes or decides law.
5. **"Why not a bigger or cloud model?"** Privacy, offline use and NGO cost. Bigger models don't fix ASR errors; confirmation does. Gemma 4 E4B was benchmarked as an alternative *[result]*.
6. **"Why does this need AI?"** Low literacy plus own language means speech must go in and speech must come out, and free speech must become structured fields. Without AI it's a paper diary no official can use.
7. **"Where do the rates come from? What if they're old?"** Notification 7997 (05.08.2026), stored with its validity window and verification status. The engine refuses dates outside the window. The official site still links the 2025 PDF, which is exactly why provenance matters.
8. **"A Bihar worker in Maharashtra: whose minimum wage applies?"** The place of work, via the "appropriate Government" (s.2(d)). Central-sphere sites (railways, central PSUs) use central rates.
9. **"Who pays if the thekedar vanishes?"** The contractor is an "employer" (s.2(l)). The principal employer may be liable under OSH Code s.55; applicability depends on size and facts. We capture the builder's identity; the paralegal decides.
10. **"Privacy and retaliation?"** Local only, PIN, no GPS, nothing employer-facing, explicit export only, witness redaction. Aligned with DPDP (core obligations from ~May 2027).
11. **"Will workers really use it daily?"** Unproven. The design makes payday the key moment, takes a few seconds (or one 'same as yesterday' tap), and is hub-assisted. Our validation plan and a hub-interview fallback mode use the same codebase.
12. **"What was built today vs. before?"** Before: research, downloads, CLI benchmarks, rate-data transcription, synthetic audio. All product code was written today; the git history shows it.
13. **"Other states and languages?"** Rate packs per state. AI4Bharat models cover 20+ Indian languages; native testers are needed.
14. **"Sustainability?"** Open source; one laptop per hub; natural adopters are unions, NGOs, DLSAs and BOCW facilitation centres.
15. **"Why not let the AI argue with the thekedar for her?"** We considered it and rejected it on evidence. Workers fear losing work and false theft accusations, an AI can misstate the law or "accept" a bad deal, and speech recognition is least reliable in heated, multi-speaker talk. So the AI speaks only fixed, polite, factual lines when *she* presses play, records his reply only after announcing it, and logs promises. Humans (her, the union, legal aid) negotiate.
16. **"Isn't sending evidence to the thekedar dangerous?"** It can be, so the app asks first, explains the risk in her language, offers union-first, sends only the clips she ticks (no witness voices by default), and logs what left the phone. The choice stays hers.
17. **"Is recording the thekedar legal or admissible?"** We never record covertly: a spoken notice comes first, and Stop is instant. Whether and how a recording can be used is for legal aid to advise; we don't claim admissibility.

---

## 9. Risks, assumptions, and questions for us

### 9.1 Coordinator questions: **answered 13 Oct** (from `AboutHackthon/Question&Answers.md`)

| # | Question | Answer | Effect on the plan |
|---|---|---|---|
| 1 | Start, duration, venue; own laptops; power | College; **07:00, 10 hours**; own laptops allowed; power sockets available | Schedule moved to 07:00–17:00 (§7.3); Tier A laptop confirmed usable |
| 2 | Internet at the venue | **Yes, throughout** | Push any time; WhatsApp step can be live. Keep the offline-first design and the Wi-Fi-off demo |
| 3 | Pre-build prep and empty repo | **Allowed** | Do §7.2 in full; create the public repo with LICENSE now |
| 4 | Deliverables, presentation, rubric | **Repo + README**; judges assess **at your desk** | Desk-demo format, reset script, printed A4 sheet (§7.3, §8.3) |
| 5 | Sections 4.6–4.8 | **No extra rules** | — |
| 6 | PS07 author and expectations | **Not DomAIyn Labs; no fixed state or format** | Maharashtra focus stays (venue state; rate pack is pluggable) |
| 7 | Shortlist date | **1–2 days after PPT submission** | Prep starts now regardless of the result |

### 9.2 Team questions: **answered 13 Oct**

| # | Question | Answer | Effect on the plan |
|---|---|---|---|
| 1 | Team size and skills | **Solo**; strong all-round coder; Claude Pro (one reset) as coding assistant | Solo schedule and cut line (§7.3); Claude budget; disclose AI-assisted coding |
| 2 | GPU laptop | Capable Windows PC; exact GPU unknown | Record the GPU in `device.info` once known; benchmark on 15 Oct decides tiers |
| 3 | Contacts at a union, NGO or DLSA | **None** | Light-touch validation only (§3.10); label adoption claims as hypotheses |
| 4 | React | **Yes**, and the app must be **installable as a phone web app** | React + `vite-plugin-pwa` + **HTTPS via mkcert** (§5.2, §7.2) |
| 5 | Name | "Fine; suggest better if any" | Keep **Apna Hisaab**; alternatives: *Hisaab Saathi* (names the voice agent, works in Hindi and Marathi) or *Haq ka Hisaab*. Your call. |
| — | Field feedback | "20 s may be too much; keep it flexible" | No minimum length; soft cap 60 s; one-tap **"Same as yesterday / कालसारखं"**; voice only for what differs |

### 9.3 Risk register (impact-first)

| # | Risk | Likelihood | Impact | Mitigation | Fallback |
|---|---|---|---|---|---|
| R1 | ~~Own laptops not allowed, or no power~~ **Resolved: allowed** | — | — | — | — |
| R16 | **Solo builder runs out of time** | H | High | Solo cut line; module-by-module with tests; feature freeze at 15:00 | MUST + Saboot + Bhejo only |
| R17 | **Claude usage limit hit mid-day** | M | High | Budget usage (§7.3); detailed handoff spec lets you hand-code | Hand-code from §10; models are local |
| R18 | **Phone can't use mic or install the PWA** (no HTTPS / untrusted cert / LAN IP changed) | M | High | mkcert CA installed on the phone beforehand; regenerate the cert for the venue IP at 07:00 | Demo on the laptop browser (localhost is a secure context) |
| R2 | GPU laptop unavailable or fails | M | High | Test Tier B on Anuskha's laptop 15 Oct | Tier C + video |
| R3 | Originality challenge | L | Critical | Coordinators confirmed prep is allowed; disclose it; git history | — |
| R4 | Poor Marathi ASR/LLM accuracy | M | High | IndicWhisper-mr; two-reader check; tap-first numbers | Hindi-led demo |
| R5 | Rate data wrong (secondary translation) | M | High | Verify the original; show status; refuse out-of-window | Label "secondary source" on screen |
| R6 | Legal misstatement | M | High | Only §3.5 citations; "may" language | — |
| R7 | Scope creep | H | High | Cut line and checkpoints | — |
| R8 | Windows dependency problems (Python 3.14, CUDA, Playwright) | M | Med | Python 3.11 env; offline wheels; rehearsal | Browser print-to-PDF |
| R9 | TTS slow | M | Med | Cache; lazy load | Replay audio |
| R10 | No internet for the final push | M | Med | Hotspot; push at checkpoints | Ask organisers |
| R11 | ~~No React skills~~ **Resolved: React known** | — | — | — | — |
| R12 | Mic or audio failure | M | Med | USB mic; upload path | Video |
| R13 | Retaliation after Bhejo or Bol ke Batao | M | High | Ask first, spoken risk note, union-first option, fact-only templates, announced recording, hostile-stop | Default the demo narrative to "send to union" |
| R14 | Web Share file sharing needs a secure context (HTTPS/localhost), so a LAN hub over HTTP can't attach files | H | Low–Med | Download + `wa.me` text-link fallback | HTTPS hub (stretch) |
| R15 | Speak-for-me feels robotic or is ignored by the thekedar | M | Low | Short, natural hi/mr templates; worker can just use it as a script to read | Script view |

### 9.4 Assumptions

| ID | Assumption | Basis |
|---|---|---|
| A1 | ~~Build day runs 07:30–17:30~~ → **confirmed 07:00, 10 h** | Coordinators |
| A2 | ~~Own laptops allowed~~ → **confirmed** | Coordinators |
| A3 | ~~No venue internet~~ → **internet available**; still build offline-first and demo with Wi-Fi off | Coordinators |
| A4 | ÷26 divisor and an 8 h normal day apply to the Maharashtra construction notification | Central-rules convention; verify |
| A5 | Chhatrapati Sambhajinagar municipal-corporation limits are Zone I for the construction schedule | Verify |
| A6 | The SGCMS translation of notification 7997 matches the Marathi original | Verify |
| A7 | IndicWhisper downloads are live | Verify 14 Oct |
| A8 | ~~Team of 3–4~~ → **solo builder**, strong overall coder, knows React, Claude Pro as coding assistant | You |
| A9 | Judges include Marathi speakers | Venue location **[H]** |
| A10 | MVP workers are time-rated, with one contractor per day | Scope decision |

---

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
