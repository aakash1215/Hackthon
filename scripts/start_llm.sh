#!/usr/bin/env bash
# Start llama-server on 127.0.0.1:8080. Usage (Git Bash, repo root):
#   bash scripts/start_llm.sh cpu [model.gguf]   # default Qwen3-1.7B-Q4_K_M.gguf
#   bash scripts/start_llm.sh gpu [model.gguf]   # default Qwen3-4B-Instruct-2507-Q4_K_M.gguf, all layers on GPU
# Set HOST=0.0.0.0 on a cloud GPU box so the laptop can reach it (LLM_BASE_URL=http://<box>:8080/v1).
set -eu
cd "$(dirname "$0")/.."
HOST="${HOST:-127.0.0.1}"
case "${1:-cpu}" in
  cpu) exec models/llama.cpp/cpu/llama-server.exe -m "models/llm/${2:-Qwen3-1.7B-Q4_K_M.gguf}" \
         --host "$HOST" --port 8080 -c 4096 --jinja ;;
  gpu) exec models/llama.cpp/cuda/llama-server.exe -m "models/llm/${2:-Qwen3-4B-Instruct-2507-Q4_K_M.gguf}" \
         --host "$HOST" --port 8080 -c 8192 -ngl 99 --jinja ;;
  *) echo "usage: $0 cpu|gpu [model.gguf]"; exit 2 ;;
esac
