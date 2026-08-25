#!/usr/bin/env bash
export LD_LIBRARY_PATH=/usr/local/cuda/targets/x86_64-linux/lib:$LD_LIBRARY_PATH
MODEL="${1:-/var/home/imshubhamsocial/Projects/Workspace/Personal/LLMs/Cluster/assets/gemma-4-E4B-it-Q4_K_M.gguf}"
nohup setsid taskset -c 0-11 /var/home/imshubhamsocial/Projects/Workspace/Personal/LLMs/Cluster/llama.cpp/build/bin/llama-server \
  -m "$MODEL" \
  --port 8138 \
  --jinja \
  -ngl 99 \
  -c 65536 \
  --cache-type-k q4_0 \
  --cache-type-v q4_0 \
  --flash-attn on \
  -np 1 \
  --spec-default \
  --cache-reuse 64 \
  --threads 6 \
  --threads-batch 6 \
  --cpu-range 0-11 \
  --cpu-strict 1 \
  --cache-prompt > /dev/shm/llama_server_hardened.log 2>&1 &
disown
