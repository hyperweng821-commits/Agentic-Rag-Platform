#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

smoke_email="${AGENTFORGE_SMOKE_EMAIL:-}"
smoke_password="${AGENTFORGE_SMOKE_PASSWORD:-}"
api_base_url="${AGENTFORGE_API_BASE_URL:-http://127.0.0.1:8000}"
timeout_seconds="${AGENTFORGE_SMOKE_TIMEOUT_SECONDS:-180}"
poll_interval_seconds="${AGENTFORGE_SMOKE_POLL_INTERVAL_SECONDS:-2}"
csrf_cookie_name="${CSRF_COOKIE_NAME:-agentforge_csrf}"

if [[ -z "$smoke_email" || -z "$smoke_password" ]]; then
  echo "Set AGENTFORGE_SMOKE_EMAIL and AGENTFORGE_SMOKE_PASSWORD." >&2
  exit 2
fi
if [[ ! "$timeout_seconds" =~ ^[0-9]+$ ]] || ((timeout_seconds < 10 || timeout_seconds > 600)); then
  echo "AGENTFORGE_SMOKE_TIMEOUT_SECONDS must be an integer from 10 through 600." >&2
  exit 2
fi
if [[ ! "$poll_interval_seconds" =~ ^[0-9]+$ ]] || ((poll_interval_seconds < 1 || poll_interval_seconds > 10)); then
  echo "AGENTFORGE_SMOKE_POLL_INTERVAL_SECONDS must be an integer from 1 through 10." >&2
  exit 2
fi
if [[ ! "$api_base_url" =~ ^http://(127\.0\.0\.1|localhost|\[::1\])(:[0-9]{1,5})?/?$ ]]; then
  echo "AGENTFORGE_API_BASE_URL must use an explicit loopback HTTP address." >&2
  exit 2
fi
if [[ "$api_base_url" =~ :([0-9]{1,5})/?$ ]]; then
  api_port="${BASH_REMATCH[1]}"
  api_port_decimal=$((10#$api_port))
  if ((api_port_decimal < 1 || api_port_decimal > 65535)); then
    echo "AGENTFORGE_API_BASE_URL contains an invalid port." >&2
    exit 2
  fi
fi

for required_command in curl docker python3; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    echo "Required command is unavailable: $required_command" >&2
    exit 2
  fi
done

temporary_directory="$(mktemp -d "${TMPDIR:-/tmp}/agentforge-demo-smoke.XXXXXX")"
trap 'rm -r -- "$temporary_directory"' EXIT

cookie_jar="$temporary_directory/cookies.txt"
login_payload="$temporary_directory/login.json"
login_response="$temporary_directory/login-response.json"
knowledge_base_payload="$temporary_directory/knowledge-base.json"
knowledge_base_response="$temporary_directory/knowledge-base-response.json"
sample_document="$temporary_directory/demo-ingestion.txt"
upload_response="$temporary_directory/upload-response.json"
status_response="$temporary_directory/status-response.json"

json_value() {
  python3 -c 'import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
for key in sys.argv[2].split("."):
    value = value[key]
print("" if value is None else value)' "$1" "$2"
}

worker_container="$(docker compose --profile rag ps --status running --quiet worker)"
if [[ -z "$worker_container" ]]; then
  echo "The Compose worker is not running. Start the stack with: make demo" >&2
  exit 1
fi

embedding_model="$(docker compose --profile rag exec -T worker printenv OLLAMA_EMBED_MODEL)"
if ! docker compose --profile rag exec -T ollama ollama show "$embedding_model" >/dev/null 2>&1; then
  echo "The configured embedding model is unavailable: $embedding_model" >&2
  echo "Provision it explicitly with: make pull-models" >&2
  exit 1
fi

api_base_url="${api_base_url%/}"
curl --fail-with-body --silent --show-error \
  --connect-timeout 5 --max-time 15 \
  "$api_base_url/api/v1/health" >/dev/null

SMOKE_EMAIL_VALUE="$smoke_email" SMOKE_PASSWORD_VALUE="$smoke_password" \
  python3 -c 'import json, os
print(json.dumps({
    "email": os.environ["SMOKE_EMAIL_VALUE"],
    "password": os.environ["SMOKE_PASSWORD_VALUE"],
}))' >"$login_payload"

curl --fail-with-body --silent --show-error \
  --connect-timeout 5 --max-time 15 \
  --cookie-jar "$cookie_jar" \
  --header "Content-Type: application/json" \
  --data-binary "@$login_payload" \
  "$api_base_url/api/v1/auth/login" >"$login_response"

csrf_token="$(awk -F $'\t' -v name="$csrf_cookie_name" '$6 == name {token = $7} END {print token}' "$cookie_jar")"
if [[ -z "$csrf_token" ]]; then
  echo "Login did not return the configured CSRF cookie." >&2
  exit 1
fi

smoke_identity="$(date -u +%Y%m%dT%H%M%SZ)-$$"
SMOKE_IDENTITY_VALUE="$smoke_identity" python3 -c 'import json, os
identity = os.environ["SMOKE_IDENTITY_VALUE"]
print(json.dumps({
    "name": f"Demo ingestion smoke {identity}",
    "description": "Bounded local upload-to-completed smoke evidence.",
}))' >"$knowledge_base_payload"

curl --fail-with-body --silent --show-error \
  --connect-timeout 5 --max-time 15 \
  --cookie "$cookie_jar" \
  --header "Content-Type: application/json" \
  --header "X-CSRF-Token: $csrf_token" \
  --data-binary "@$knowledge_base_payload" \
  "$api_base_url/api/v1/knowledge-bases" >"$knowledge_base_response"

knowledge_base_id="$(json_value "$knowledge_base_response" id)"
printf 'AgentForge demo ingestion smoke %s\n\nThis unique document must be embedded and indexed.\n' \
  "$smoke_identity" >"$sample_document"

curl --fail-with-body --silent --show-error \
  --connect-timeout 5 --max-time 15 \
  --cookie "$cookie_jar" \
  --header "X-CSRF-Token: $csrf_token" \
  --form "file=@$sample_document;type=text/plain" \
  "$api_base_url/api/v1/knowledge-bases/$knowledge_base_id/documents" >"$upload_response"

job_id="$(json_value "$upload_response" ingestion_job.id)"
initial_status="$(json_value "$upload_response" ingestion_job.status)"
if [[ "$initial_status" != "pending" ]]; then
  echo "Upload did not create a pending ingestion job: $initial_status" >&2
  exit 1
fi

started_at="$(date +%s)"
deadline=$((started_at + timeout_seconds))
final_status="$initial_status"

while (( $(date +%s) < deadline )); do
  curl --fail-with-body --silent --show-error \
    --connect-timeout 5 --max-time 15 \
    --cookie "$cookie_jar" \
    "$api_base_url/api/v1/ingestion-jobs/$job_id" >"$status_response"
  final_status="$(json_value "$status_response" status)"
  case "$final_status" in
    completed)
      break
      ;;
    failed)
      error_code="$(json_value "$status_response" error_code)"
      echo "Ingestion job failed with $error_code: $job_id" >&2
      exit 1
      ;;
    pending | processing)
      sleep "$poll_interval_seconds"
      ;;
    *)
      echo "Ingestion job returned an invalid status: $final_status" >&2
      exit 1
      ;;
  esac
done

if [[ "$final_status" != "completed" ]]; then
  echo "Ingestion job did not complete within ${timeout_seconds}s: $job_id" >&2
  exit 1
fi

elapsed_seconds=$(($(date +%s) - started_at))
printf 'Upload-to-completed smoke passed: job=%s initial=%s final=%s elapsed_seconds=%s\n' \
  "$job_id" "$initial_status" "$final_status" "$elapsed_seconds"
