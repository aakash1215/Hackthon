# Acceptance checks (BUILD_PLAN §11 deltas + hard rules)

Checked on build day, 16 Oct 2026. "pytest" = `cd backend && .venv/Scripts/python -m pytest -q` (105 tests).
"E2E" = headless phone runs (Chromium, 360–390 px, fake mic/GPS) against the running hub.

| # | Check | How it was verified | Result |
|---|---|---|---|
| AC9 | Hub unreachable → the phone still records, hashes, takes photo + GPS and queues; after reconnecting it uploads with matching hashes. Telegram pauses and resumes. | `scripts/e2e_pwa.py`: airplane mode → record → reload offline (service worker) → reconnect → `hash_match=1`. Telegram: the outbox keeps `pending` rows and the supervisor retries every 30 s (seen live: this Wi-Fi blocks api.telegram.org, the hub kept running). | ✅ (Telegram resume not yet seen live) |
| AC14 | GPS only after opt-in; coordinates shown to the worker. PIN optional. | `test_gps_dropped_unless_worker_opted_in`; the GPS chip on the photo step (E2E screenshot). PIN cut (§4 #7). | ✅ |
| AC22 | Every photo SHA-256-hashed before processing, and shown in the packet with hash, device time and GPS. | `test_payment_proof_photo_and_site_board`, `test_gps_and_photo_on_the_day_give_l2` (phone hash = hub hash); packet section 6 (screenshot `docs/screenshots/07_packet.png`). | ✅ |
| AC23 | Thekedar and co-worker recordings can't start before the notice / consent prompt; Stop is instant. | `test_thekedar_recording_requires_notice` (hub rejects without `notice_played`), `test_thekedar_refusal_keeps_only_the_notice…`, `test_coworker_confirmation_raises_day_to_l3` (consent required); `scripts/e2e_p3.py` asserts no Stop button exists while the notice plays. | ✅ |
| AC24 | Telegram as §7: invite-only linking, intro first, every message hashed with Telegram time, template-only outbound, hostile → no reply + alert, auto messages only while `auto_daily`. | `tests/test_telegram.py` (16 tests incl. the 6 scripted messages, daily limit, pause, flush with Telegram time + SHA-256); `scripts/e2e_p4.py` with the real LLM. | ✅ offline · ⏳ live Kailas test (network blocks Telegram here) |
| AC25 | Corroboration levels deterministic and shown in the ledger and the packet. | `tests/test_corroboration.py` (9 tests); ledger badges and packet column (E2E + packet screenshots). | ✅ |
| Rule 1 | No closed AI API in the product. | `grep -rniE "openai\|anthropic\|generativeai\|gemini…" backend/app frontend/src scripts` → only a comment naming llama-server's OpenAI-*compatible* protocol; no client libraries in requirements or package.json. | ✅ |
| Rule 3 | Never invent values: evidence must be a transcript substring, otherwise null. | `test_reconcile.py`, `test_thekedar_recording_to_differences…` (an invented `paid_now` quote is dropped as `UNGROUNDED`). | ✅ |
| Rule 4 | Save + SHA-256 before any AI call. | `test_save_hashes_original_bytes_before_anything_else`; Telegram voice saved + hashed before ASR (`save_inbound`). | ✅ |
| Rule 9/10 | Synthetic data only; no weights, `.env`, certs, `data/`, `media/` tracked; Apache-2.0. | `git ls-files` check → none; `LICENSE` = Apache-2.0; demo data watermarked "SYNTHETIC DEMO DATA". | ✅ |
| Rule 11 | Wage engine / rates / money untouched; F1–F9 green. | pytest. | ✅ |
