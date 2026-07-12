#!/usr/bin/env bash
set -euo pipefail

chat_model="${OLLAMA_CHAT_MODEL:-qwen3:4b-instruct}"
embed_model="${OLLAMA_EMBED_MODEL:-qwen3-embedding:0.6b}"

docker compose exec ollama ollama pull "$chat_model"
docker compose exec ollama ollama pull "$embed_model"

