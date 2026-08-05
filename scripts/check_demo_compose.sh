#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

temporary_directory="$(mktemp -d "${TMPDIR:-/tmp}/agentforge-demo-compose.XXXXXX")"
trap 'rm -r -- "$temporary_directory"' EXIT

rendered_config="$temporary_directory/compose.json"
dry_run="$temporary_directory/make-demo.txt"

docker compose --profile rag config --format json >"$rendered_config"
make --no-print-directory -n demo >"$dry_run"

python3 - "$rendered_config" <<'PY'
import json
import sys
from pathlib import Path

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
services = config["services"]

required_services = {"api", "chroma", "migrate", "ollama", "postgres", "worker"}
missing_services = required_services - services.keys()
assert not missing_services, f"demo services missing: {sorted(missing_services)}"

api = services["api"]
migrate = services["migrate"]
worker = services["worker"]

assert worker["image"] == api["image"], "worker must reuse the API image"
assert worker["command"] == [
    "python",
    "-m",
    "app.workers.ingestion_worker",
], "worker must invoke the existing ingestion-worker module"
assert not worker.get("ports"), "worker must not publish a host port"
assert set(worker["networks"]) == {"backend"}, "worker must use only the backend network"
assert worker["restart"] == "unless-stopped", "worker restart policy changed"
assert worker["healthcheck"]["disable"] is True, "worker must not inherit the API HTTP probe"


def volume_source(service: dict[str, object], target: str) -> str:
    for mount in service.get("volumes", []):
        if mount["target"] == target:
            assert mount["type"] == "volume", f"{target} must be a named volume"
            return str(mount["source"])
    raise AssertionError(f"service does not mount {target}")


api_upload = volume_source(api, "/app/data/uploads")
worker_upload = volume_source(worker, "/app/data/uploads")
assert worker_upload == api_upload, "API and worker must share the upload volume"
api_mount_targets = {mount["target"] for mount in api.get("volumes", [])}
assert "/app" not in api_mount_targets
assert "/app/.venv" not in api_mount_targets, "a stale volume must not mask image dependencies"

dependencies = worker["depends_on"]
expected_conditions = {
    "chroma": "service_healthy",
    "migrate": "service_completed_successfully",
    "ollama": "service_healthy",
    "postgres": "service_healthy",
}
for service_name, condition in expected_conditions.items():
    actual = dependencies.get(service_name, {}).get("condition")
    assert actual == condition, f"worker dependency {service_name} must use {condition}"

assert migrate["command"] == ["alembic", "upgrade", "head"]
assert api["depends_on"]["migrate"]["condition"] == "service_completed_successfully"

environment = worker["environment"]
assert environment["DATABASE_URL"].split("@", 1)[1].startswith("postgres:5432/")
assert environment["CHROMA_HOST"] == "chroma"
assert environment["OLLAMA_BASE_URL"] == "http://ollama:11434"
assert not [name for name in environment if "PRINCIPAL" in name.upper()]
PY

expected_command="docker compose --profile rag up --build -d"
if ! grep -Fqx "$expected_command" "$dry_run"; then
  echo "make demo does not start the complete rag profile" >&2
  exit 1
fi

echo "Demo Compose configuration is valid."
