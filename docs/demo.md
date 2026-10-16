# 3-minute desk demo (BUILD_PLAN §10) — all data SYNTHETIC

## Before the judges arrive (5 min)

1. **Network:** laptop on the **phone hotspot** (venue Wi-Fi blocks phone↔laptop traffic and api.telegram.org).
   If the LAN IP changed: `bash scripts/make_certs.sh` (and reinstall nothing on the phones; the CA stays).
2. **LLM:** `bash scripts/start_llm.sh cpu` (one slot, all cores). Check `curl http://127.0.0.1:8080/health`.
3. **Reset the demo data and start the hub on it** (repo root, Git Bash):
   ```bash
   bash scripts/demo_reset.sh
   ```
   It prints `Open on the phone: https://<LAN-IP>:8443/?demo=demo-sunita`. Your real data in `data/apna.db` is
   not touched. (Back to real data: stop the hub, start `cd backend && .venv/Scripts/python -m app.main`.)
4. **Sunita's phone:** open that URL → Home shows "नमस्ते, सुनीता (डेमो)". (Or: welcome → "पहले से खाता है? लॉग इन
   करें" → सुनीता (डेमो) → PIN **1234**.)
5. **Kailas's phone (Telegram, second account):** in Sunita's app: Settings → "ठेकेदार से Telegram पर जुड़ें" →
   "जोड़ने का लिंक बनाएँ" → open the link / scan the QR on Kailas's phone → Start → हिंदी → he gets the intro
   notice. (`/api/health` must show `"telegram": {"running": true}`; if not, check the hotspot.)
6. Check `https://<LAN-IP>:8443/api/health` → `llm.ok: true`, `asr.ok: true`.

## The 3 minutes

| Time | Say | Do |
|---|---|---|
| 0:00–0:20 **Hook** | "Sunita worked 13 days. The thekedar says 12 × ₹600 minus a ₹2,000 advance. She has nothing written, and employers avoid every document that would prove she worked." | Home screen. |
| 0:20–1:20 **Live** | "She just speaks — Marathi. Saved and hashed on the phone first; works without internet." | Tap the mic → speak a day ("आज सकाळी नऊ ते संध्याकाळी सात काम केलं") → Stop → photo (optional) → GPS chip → **"आवाज़ सुरक्षित" + save code** at once. The hub processes in the background (~1–1.5 min on this CPU) — meanwhile go on; come back to "पक्का करें" → green/amber chips → ✅ "सही है". Kailas's phone gets the **daily update** (if linked). |
| 1:20–2:00 **Thekedar's side** | "Here is what the thekedar said — recorded only after a notice that can't be skipped." | खाता → हिसाब जाँचें → "पिछले मिलान" → the seeded recording → **मिलान: 4 differences** (12 vs 13 days, ₹600 vs ₹864 minimum, 13 h overtime not counted, ₹2,000 advance not in her record). On Kailas's phone, type **"Somvaar ko 5000 dunga"** → Sunita's Home shows the **promise card** (bot replied only "नोट कर लिया: ₹5,000, Somvaar। धन्यवाद।"). Optional: an abusive line → **no reply**, S8 help screen. |
| 2:00–2:30 **Hisaab** | "Every rupee is computed by code, with the notification number and its verification status — never by the AI." | **खाता first** (show the L1/L2/L3 badges: co-worker days L3, GPS days L2, the rest L1 — *do this before confirming the promise; confirming it makes the month L3*) → हिसाब: **₹9,539 बाकी (अनुमान)**, बनता ₹14,039, मिला ₹4,500, अधिसूचना 7997, "मूल मराठी अधिसूचना से जाँचना बाकी". |
| 2:30–3:00 **Packet** | "Not proof — a record a paralegal can use." | फ़ाइल → the N/12 ring ("not a legal score") → "PDF बनाएँ" → open the PDF: dues statement, day table with corroboration column, photos with SHA-256 + GPS, the thekedar's words + Telegram log with server timestamps, evidence index + chain head. Optional tamper demo: Settings → "फिर जाँचें" shows "सब सही". |

**Close:** "Open-weight models, worker-controlled, corroborated by the thekedar's own words. Not proof — a record a paralegal can use."

## If something breaks

* **Processing slow:** say so — it is the 2-core CPU tier; the note is already saved + hashed. Show a seeded day instead.
* **Telegram blocked:** show the seeded Telegram thread (Settings → Telegram) and the promise card already on Home;
  `scripts/e2e_p4.py` proves the flow offline.
* **Phone can't reach the hub:** record anyway (airplane mode works) → "फ़ोन में सेव · भेजना बाकी" → it uploads later
  with the same hash. Fallback: the screen video.
* **Judges' questions:** models + licenses and measured latencies in `README.md`; checks in `docs/acceptance.md`.
