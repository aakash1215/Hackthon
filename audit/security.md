# Security policy

- **Integrity:** every original audio or photo file is SHA-256 hashed before any AI call. Every event goes into an
  append-only hash chain (`backend/app/events.py`). `GET /api/chain/verify` recomputes it.
- **Access control:** each worker logs in with a 4-digit PIN, stored hashed on the hub, with lockout after
  repeated wrong tries. Known gap: API calls are not yet bound to a session token, so the hub must stay on a
  trusted LAN.
- **Transport:** HTTPS with local mkcert certificates on the LAN (`certs/`, gitignored).
- **Secrets:** `.env`, bot tokens, certificates, `data/` and model weights are never committed (`.gitignore`).
- **Model safety:** LLM output is schema-constrained JSON. Every value must quote the transcript. Messages to the
  thekedar come from templates, or from the code-checked agent when `TG_AGENT=chatgpt`. A deterministic hostile
  guard runs before any model.

## Incident response
1. Run `GET /api/chain/verify`. A broken chain shows the first altered event (`broken_at_seq`).
2. If a token leaks, rotate the Telegram bot token with @BotFather and `CHAT_API_KEY` in the provider console,
   then update `.env` and restart the hub.
3. If the hub is lost or tampered with, re-export evidence files from a backup of `data/`. Each export's
   manifest lists the SHA-256 of every file.

## Responsible disclosure
Report vulnerabilities privately to the maintainer listed in `../README.md`, not in a public issue. We aim to
acknowledge within 7 days.
