# Downloads & requirements: Apna Hisaab build day (Fri 16 Oct 2026)

Everything the build needs, where it comes from, and where it goes.
- **Status column:** ✅ already on the i3 laptop (checked 16 Oct, 10:15) · ⬜ to download.
- **Free disk on C:** 33 GB. CPU tier ≈ 4 GB; GPU tier ≈ 12–16 GB more.
- All model files go under `models/`, which is gitignored. **Never commit them.**

---

## 0. Already installed on the i3 laptop (no action)

| Tool | Version found | Used for |
|---|---|---|
| Python | 3.11, 3.12, 3.13, 3.14 (default 3.14 ⚠️) | Use **3.12** for the venv (`uv venv -p 3.12`); ML wheels may not support 3.14 |
| uv | 0.12.5 | venv + pip + `uvx` |
| Node / npm | 24.14.1 / 11.11.0 | Frontend (Vite + React) |
| ffmpeg | 8.1 full build | Audio transcode to 16 kHz WAV, Saboot excerpts |
| git / gh | 2.53 / 2.102 | Repo, push |
| NVIDIA GPU | **none** (`nvidia-smi` not found) | → CPU tier on this laptop |

---

## 1. Download NOW: CPU / dev tier (this laptop)

| # | What | Size | Where from | Put it in |
|---|---|---|---|---|
| 1 | **llama.cpp `llama-server`**, Windows CPU build | ~30 MB | GitHub releases → `llama-b11678-bin-win-cpu-x64.zip` (or newer): https://github.com/ggml-org/llama.cpp/releases | `models/llama.cpp/cpu/` (unzip) |
| 2 | **LLM: Qwen3-1.7B** Q4_K_M | 1.11 GB | https://huggingface.co/unsloth/Qwen3-1.7B-GGUF → `Qwen3-1.7B-Q4_K_M.gguf` | `models/llm/` |
| 2b | *(alternative LLM; keep whichever gives valid JSON faster)* **Qwen3.5-2B** Q4_K_M | 1.28 GB | https://huggingface.co/unsloth/Qwen3.5-2B-GGUF → `Qwen3.5-2B-Q4_K_M.gguf` | `models/llm/` |
| 3 | **ASR: faster-whisper small** (CTranslate2) | 0.48 GB | https://huggingface.co/Systran/faster-whisper-small (all files) | `models/asr/faster-whisper-small/` |
| 4 | **mkcert** (HTTPS for the phone) | 5 MB | https://github.com/FiloSottile/mkcert/releases → `mkcert-v1.4.4-windows-amd64.exe` (rename to `mkcert.exe`) | Somewhere on PATH, e.g. `C:\tools\` |
| 5 | **Playwright Chromium** (packet → PDF) | ~150 MB | `uv run playwright install chromium` (after the pip install in §4) | Playwright's own cache |
| 6 | **Noto Sans Devanagari** font | ~1 MB | npm `@fontsource/noto-sans-devanagari` (bundled into the app, no CDN), or https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari | `frontend/` via npm; copy a `.woff2` to `backend/app/static/fonts/` for the PDF |

**Commands (run in the background; Git Bash):**
```bash
mkdir -p models/llm models/asr models/llama.cpp/cpu
# llama.cpp CPU
gh release download b11678 -R ggml-org/llama.cpp -p "llama-b11678-bin-win-cpu-x64.zip" -D models/llama.cpp && \
  unzip -o models/llama.cpp/llama-b11678-bin-win-cpu-x64.zip -d models/llama.cpp/cpu
# LLM + ASR (Hugging Face CLI via uvx; no install needed)
uvx --from huggingface_hub hf download unsloth/Qwen3-1.7B-GGUF Qwen3-1.7B-Q4_K_M.gguf --local-dir models/llm
uvx --from huggingface_hub hf download Systran/faster-whisper-small --local-dir models/asr/faster-whisper-small
```

**Start the LLM server (CPU):**
```bash
models/llama.cpp/cpu/llama-server.exe -m models/llm/Qwen3-1.7B-Q4_K_M.gguf --host 127.0.0.1 --port 8080 -c 4096 --jinja
```

---

## 2. GPU / demo tier (when the 6–8 GB GPU laptop or cloud GPU is ready)

| # | What | Size | Where from | Put it in |
|---|---|---|---|---|
| 7 | **llama.cpp CUDA build** (Windows GPU laptop) | ~200 MB + ~400 MB | Same releases page → `llama-b11678-bin-win-cuda-12.4-x64.zip` **plus** `cudart-llama-bin-win-cuda-12.4-x64.zip` (use the 13.4 pair if the driver supports CUDA 13) | `models/llama.cpp/cuda/` (unzip both into the same folder) |
| 7-L | *(Linux cloud GPU instead)* llama.cpp server | — | Docker `ghcr.io/ggml-org/llama.cpp:server-cuda`, or build: `cmake -B build -DGGML_CUDA=ON && cmake --build build -j` | — |
| 8 | **LLM: Qwen3-4B-Instruct-2507** Q4_K_M | 2.50 GB | https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF → `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` | `models/llm/` |
| 9 | **ASR: Whisper large-v3-turbo** (CTranslate2, ready-made) | 1.62 GB | https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2 (all files) | `models/asr/whisper-turbo-ct2/` |
| 10 | **ASR: AI4Bharat IndicWhisper Hindi** (better hi; MIT) | ~1.5–3 GB *(unverified)* | https://indicwhisper.objectstore.e2enetworks.net/hindi_models.zip (repo: https://github.com/AI4Bharat/vistaar) | `models/asr/indicwhisper-hi/` → convert (below) |
| 11 | **ASR: AI4Bharat IndicWhisper Marathi** | ~1.5–3 GB *(unverified)* | https://indicwhisper.objectstore.e2enetworks.net/marathi_models.zip | `models/asr/indicwhisper-mr/` → convert |
| 12 | **TTS: AI4Bharat Indic Parler-TTS** (Apache-2.0, **gated**) | ~3.8 GB | 1) Log in at huggingface.co and click "Agree" on https://huggingface.co/ai4bharat/indic-parler-tts · 2) create a read token at https://huggingface.co/settings/tokens · 3) `uvx --from huggingface_hub hf auth login` | HF cache, or `models/tts/indic-parler-tts/` |

**IndicWhisper → CTranslate2 conversion** (on the GPU box, after the unzip; the zips hold Hugging Face transformers checkpoints):
```bash
uv pip install ctranslate2 transformers torch
ct2-transformers-converter --model models/asr/indicwhisper-hi/<unzipped_folder> \
  --output_dir models/asr/indicwhisper-hi-ct2 --quantization int8_float16 \
  --copy_files tokenizer.json preprocessor_config.json   # copy whichever of these exist
```
If the download or conversion isn't done by ~13:00, **skip it** and use #9 (turbo). The ASR model is set in `.env`.

**Start the LLM server (GPU):**
```bash
models/llama.cpp/cuda/llama-server.exe -m models/llm/Qwen3-4B-Instruct-2507-Q4_K_M.gguf --host 127.0.0.1 --port 8080 -c 8192 -ngl 99 --jinja
```

---

## 3. Phones (Samsung A33 5G, Vivo Y73)

| # | What | Where from | How |
|---|---|---|---|
| 13 | **Chrome, latest** | Play Store | Update before testing (WebGPU, PWA install) |
| 14 | **mkcert root CA** on each phone | On the laptop: `mkcert -CAROOT` → copy `rootCA.pem` to the phone (USB / Telegram "Saved Messages") | Android: Settings → Security → Encryption & credentials → Install a certificate → **CA certificate** → pick `rootCA.pem` |
| 15 | **Telegram app** on 2 accounts (worker "Sunita" + thekedar "Kailas") | Play Store, or Telegram Desktop https://desktop.telegram.org | The second account plays the thekedar in the demo |
| 16 | *(P5 stretch)* On-phone ASR: **whisper-small ONNX** | https://huggingface.co/onnx-community/whisper-small | Downloaded by the PWA on first use, or better, served from our own origin (`models/web/whisper-small/`) so it works offline |
| 17 | *(P5 stretch)* On-phone LLM: **Qwen3.5-0.8B ONNX** | https://huggingface.co/onnx-community/Qwen3.5-0.8B-ONNX | Same as above (`models/web/qwen3.5-0.8b/`) |
| 18 | WebGPU check (10 min, both phones) | https://huggingface.co/spaces/webml-community/Qwen3.5-0.8B-WebGPU · https://huggingface.co/spaces/Xenova/whisper-webgpu · `chrome://gpu` | Note speed + whether WebGPU is "Hardware accelerated" |

---

## 4. Python packages (`backend/`, venv with Python 3.12)

Already in `backend/requirements.txt` (restore `backend/` first: `git restore backend/`):
`fastapi`, `uvicorn[standard]`, `python-multipart`, `jinja2`, `httpx`, `pytest`.

Add for build day:

| Package | Why | Tier |
|---|---|---|
| `faster-whisper` | ASR (CTranslate2) | all |
| `python-dotenv` | `.env` config | all |
| `python-telegram-bot` (v21+) | Telegram thekedar agent (long polling) | all |
| `playwright` | Packet HTML → PDF (+ `playwright install chromium`) | all |
| `pillow` | Photo thumbnails / EXIF (GPS) read for the packet | all |
| `qrcode` | Telegram invite QR | all |
| `huggingface_hub` | Model downloads (or use `uvx`) | all |
| `torch`, `transformers` | IndicWhisper conversion + Parler-TTS | GPU only |
| `parler-tts` | Indic Parler-TTS | GPU only: `uv pip install git+https://github.com/huggingface/parler-tts.git` |
| `ctranslate2` | Comes with faster-whisper; provides `ct2-transformers-converter` | GPU only (conversion) |

```bash
cd backend && uv venv -p 3.12 && uv pip install -r requirements.txt \
  faster-whisper python-dotenv python-telegram-bot playwright pillow qrcode huggingface_hub \
  && uv run playwright install chromium
```

---

## 5. Node packages (`frontend/`)

| Package | Why |
|---|---|
| `react`, `react-dom`, `vite`, `@vitejs/plugin-react` | App (`npm create vite@latest frontend -- --template react`) |
| `vite-plugin-pwa` | Manifest + service worker (installable PWA, offline shell) |
| `idb-keyval` | IndexedDB offline recording queue |
| `@fontsource/noto-sans-devanagari` | Bundled Devanagari font (no CDN) |
| `@huggingface/transformers` | *(P5 stretch)* on-phone Whisper / Qwen via WebGPU/WASM |

```bash
npm create vite@latest frontend -- --template react && cd frontend && \
npm i idb-keyval @fontsource/noto-sans-devanagari && npm i -D vite-plugin-pwa
```

---

## 6. Accounts, keys & manual steps (Akash)

| # | What | Where | Goes into |
|---|---|---|---|
| 19 | **Telegram bot token** | Telegram → @BotFather (https://t.me/BotFather) → `/newbot` → name + username ending in `bot` | `.env`: `TELEGRAM_BOT_TOKEN=…`, `TELEGRAM_BOT_USERNAME=…` (**never commit**) |
| 20 | **Hugging Face account + read token** (for gated Parler-TTS) | https://huggingface.co/settings/tokens | `hf auth login` (stored in the HF cache, not the repo) |
| 21 | **HTTPS certificates** | `mkcert -install` then `mkcert -cert-file certs/cert.pem -key-file certs/key.pem localhost 127.0.0.1 <LAN-IP>` | `certs/` (gitignored). Redo if the hotspot IP changes |
| 22 | **Hotspot** | Laptop or phone hotspot (venue Wi-Fi often blocks phone ↔ laptop) | — |
| 23 | **Demo clips** (~8, synthetic) + notice clips (hi/mr) | Record on the phone (see BUILD_PLAN §12) | `data/demo_clips/` (gitignored) |
| 24 | **UI design** | Your Canva export (PNG per screen and/or HTML/CSS) | `UI/` |

---

## 7. Disk budget

| Tier | Items | Approx. |
|---|---|---|
| CPU/dev | llama.cpp CPU + Qwen3-1.7B (+ Qwen3.5-2B) + whisper-small + Chromium | ~2–3.5 GB |
| GPU/demo | llama.cpp CUDA + Qwen3-4B + turbo + 2× IndicWhisper (+ CT2 copies) + Parler-TTS + torch | ~12–16 GB |
| Phone (P5) | whisper-small ONNX + Qwen3.5-0.8B ONNX (served from `models/web/`) | ~1–1.5 GB |

**Total, if everything is downloaded:** ~20 GB of the 33 GB free on C:. Delete the IndicWhisper zips after conversion.
