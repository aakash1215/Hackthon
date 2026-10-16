# Privacy notice (summary)

**Data principal:** the construction worker using the app. Other people (the thekedar, a co-worker) are recorded
only after a spoken notice that can't be skipped, with consent captured on the recording and an instant Stop.

## What is collected, and why
| Data | Purpose | Where it is kept |
|---|---|---|
| Name, work type, site, thekedar name and phone | Build the worker's own work and pay record | The worker's phone and their hub (`data/`) |
| Voice notes and photos (SHA-256 hashed before any AI step) | Evidence of work days and payments | Hub `data/media/`. If the worker says "don't keep my voice", only the hash is kept |
| GPS | Only if the worker opts in. The coordinates are shown to them first | Stored with that entry |
| Telegram messages with the thekedar | Record of what the thekedar said | Hub, hashed with Telegram's server time |

## The worker's choices
- Consent screen at sign-up (what is stored, that nothing is sent without permission, GPS opt-in, deletion).
- "Keep my voice recordings" can be switched off at any time in Settings.
- Any entry can be deleted (its content is purged; a tombstone with its hash stays in the hash chain).
- Logging out removes everything from the phone.

## Sharing
Nothing goes to the thekedar or anyone else without the worker tapping send or turning on the Telegram agent.
The evidence file is exported only when the worker asks for it.

## Gaps (honest)
- There is no named grievance officer or route yet.
- A full account erasure on the hub needs an operator. There is no self-service button yet.
- The optional ChatGPT engine sends transcripts to OpenAI when the worker enables it.
