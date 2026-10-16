#!/usr/bin/env bash
# Download model servers and weights into models/ (gitignored).
# Usage (Git Bash, from the repo root):
#   bash scripts/download_models.sh cpu    # i3 dev box: llama.cpp CPU, Qwen3-1.7B, Qwen3.5-2B, whisper-small, mkcert
#   bash scripts/download_models.sh gpu    # GPU box (Windows, CUDA 12.4): llama.cpp CUDA, Qwen3-4B-2507, whisper-turbo
#   bash scripts/download_models.sh indic  # GPU box, optional: IndicWhisper hi/mr zips (convert afterwards)
# Each step is skipped when its output already exists, so re-running is safe.
set -u
cd "$(dirname "$0")/.."
LLAMA_TAG="${LLAMA_TAG:-b11678}"
CUDA_VER="${CUDA_VER:-12.4}"
HF="uvx --from huggingface_hub hf"
mkdir -p models/llm models/asr models/llama.cpp models/tools

step() { echo; echo "=== $(date +%H:%M:%S) $*"; }

llama_zip() {  # $1 = asset name, $2 = target dir
  local asset="$1" dir="$2"
  [ -f "models/llama.cpp/$asset" ] || gh release download "$LLAMA_TAG" -R ggml-org/llama.cpp -p "$asset" -D models/llama.cpp
  mkdir -p "$dir" && unzip -oq "models/llama.cpp/$asset" -d "$dir"
}

case "${1:-cpu}" in
  cpu)
    step "llama.cpp CPU ($LLAMA_TAG)"
    [ -f models/llama.cpp/cpu/llama-server.exe ] || llama_zip "llama-$LLAMA_TAG-bin-win-cpu-x64.zip" models/llama.cpp/cpu
    step "mkcert"
    [ -f models/tools/mkcert.exe ] || curl -fsSL -o models/tools/mkcert.exe \
      https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-windows-amd64.exe
    step "faster-whisper small"
    $HF download Systran/faster-whisper-small --local-dir models/asr/faster-whisper-small
    step "Qwen3-1.7B Q4_K_M"
    $HF download unsloth/Qwen3-1.7B-GGUF Qwen3-1.7B-Q4_K_M.gguf --local-dir models/llm
    step "Qwen3.5-2B Q4_K_M (alternative)"
    $HF download unsloth/Qwen3.5-2B-GGUF Qwen3.5-2B-Q4_K_M.gguf --local-dir models/llm
    ;;
  gpu)
    step "llama.cpp CUDA $CUDA_VER ($LLAMA_TAG)"
    llama_zip "llama-$LLAMA_TAG-bin-win-cuda-$CUDA_VER-x64.zip" models/llama.cpp/cuda
    llama_zip "cudart-llama-bin-win-cuda-$CUDA_VER-x64.zip" models/llama.cpp/cuda
    step "Qwen3-4B-Instruct-2507 Q4_K_M"
    $HF download unsloth/Qwen3-4B-Instruct-2507-GGUF Qwen3-4B-Instruct-2507-Q4_K_M.gguf --local-dir models/llm
    step "faster-whisper large-v3-turbo (CT2)"
    $HF download deepdml/faster-whisper-large-v3-turbo-ct2 --local-dir models/asr/whisper-turbo-ct2
    ;;
  indic)
    for lang in hindi marathi; do
      step "IndicWhisper $lang"
      curl -fL -C - -o "models/asr/indicwhisper-$lang.zip" \
        "https://indicwhisper.objectstore.e2enetworks.net/${lang}_models.zip"
    done
    ;;
  *) echo "usage: $0 cpu|gpu|indic"; exit 2 ;;
esac
step "done ($1)"
