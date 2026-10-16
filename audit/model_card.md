# Model card: Apna Hisaab extraction model

Inspected by the KOALA audit (`scripts/audit_model.sh`). The weights are not in git (`models/` is ignored).

## Model
- **Base model:** Qwen3-1.7B (open-weight, Apache-2.0, Alibaba Qwen team), quantised GGUF `Qwen3-1.7B-Q4_K_M`.
- **Runtime:** llama.cpp `llama-server`, OpenAI-compatible API on `127.0.0.1:8080` (`LLM_BASE_URL`, `LLM_MODEL` in `.env`).
- **Speech:** faster-whisper `small` (open-weight, MIT), run locally in the hub.
- **Not fine-tuned.** We use prompts, few-shot examples and a JSON schema only.

## Training
No training or fine-tuning by us. The base model's training is described in the Qwen3 technical report. See
[training_data.md](training_data.md). Evaluation: [eval_results.md](eval_results.md). Runtime settings:
[model_config.yaml](model_config.yaml).

## Intended use
- Turn a construction worker's spoken Hindi or Marathi note (already transcribed) into a JSON record:
  work date, start and end time, break, payment amount.
- Classify a thekedar's (contractor's) reply into a fixed intent, such as a promise to pay or a refusal.
- **Every field is `{value, evidence}`.** `evidence` must be an exact substring of the transcript, or code sets the
  value to null (`backend/app/reconcile.py`). The worker confirms every value on screen before it is stored.
- **The model does no arithmetic and no legal reasoning.** Wages are computed by deterministic code
  (`backend/app/wage_engine.py`).

## Out of scope
- Legal advice, legal determinations, or any "proof" claim. Outputs are an evidence file and an estimate.
- Free-text generation shown to anyone as fact.

## Limitations and risks
- A 1.7B model on CPU is slow (tens of seconds per note) and misses some fields, so the worker corrects them on
  the confirm screen.
- Hinglish and dialect speech lowers ASR accuracy.
- It can misclassify a threat as neutral. A deterministic word guard runs first (`backend/app/tg_policy.py`).
- Prompt injection is possible through a thekedar's Telegram text. The text is only classified or answered under
  code checks; it can't trigger actions.

## Optional closed model (disclosed)
`CHAT_API_KEY` plus the worker's choice enables an optional ChatGPT engine (`backend/app/cloud.py`), and
`TG_AGENT=chatgpt` enables the Telegram reply agent (`backend/app/tg_agent.py`). Both are off by default and fall
back to the open-weight model. This card and the KOALA probes cover the open-weight model only.
