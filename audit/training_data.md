# Training data

**We train nothing.** Apna Hisaab uses the published Qwen3-1.7B and Whisper small weights as they are, with no
fine-tuning.

- **Data source / dataset:** the base models' own pre-training data, as documented by their providers (Qwen3
  technical report; OpenAI Whisper paper). We have no access to those datasets and add nothing to them.
- **License:** Qwen3-1.7B is Apache-2.0 and Whisper is MIT (see [license.md](license.md)).
- **Collection:** we collect no training data. The few-shot examples in our prompts (`backend/app/extract.py`) and
  the demo data (`scripts/seed_demo.py`) are **synthetic**, marked "SYNTHETIC DEMO DATA", and describe no real
  person.
- **Worker data** (voice notes, confirmed records) is never used to train or tune any model.
