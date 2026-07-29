# Deployment guide

Development uses `compose.yaml`; isolated integration infrastructure uses
`compose.test.yaml`. Tagged releases publish separate API and web images to
GitHub Container Registry.

`docker compose up --build` starts only `postgres` and `api`. ChromaDB and
Ollama require `--profile rag`; the React shell requires
`--profile frontend`. There is no worker service or worker image.

The default project exposes only application development ports:

- API binds to `127.0.0.1:${API_PORT:-8000}`;
- Web binds to `127.0.0.1:${WEB_PORT:-3000}` when its profile is enabled;
- PostgreSQL, Chroma, and Ollama are not published to the host.

Containers use `postgres:5432`, `chroma:8000`, and `ollama:11434` on their
Compose networks. The backend network remains internal. Ollama alone also
joins the model-egress network for explicit model pulls.

Use an in-container client for direct development database access:

```bash
docker compose exec postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Do not publish Chroma as an unauthenticated debugging endpoint. Chroma is a
derived index and never an authorization source.

`compose.test.yaml` keeps Chroma behind the `rag` profile. Its PostgreSQL and
Chroma test ports bind only to `127.0.0.1`, so they support isolated host-side
integration tests without listening on external interfaces. Ordinary unit
tests use fakes and do not require this Compose file.

AF-2S1 adds local opaque-session authentication, CSRF protection, and
PostgreSQL membership authorization. These controls and loopback defaults do
not make this a production deployment. Production secret management, TLS
termination, backups, separate worker/database roles, hostile-document
resource containment, external identity, and additional deployment-host
hardening remain AF-2S2/P1 work.

Each API process limits concurrent Argon2 verification and rehash jobs with
`ARGON2_MAX_CONCURRENCY` (default `2`, allowed range `1` through `8`). Raising
the value increases peak memory use because each current Argon2id job uses at
least 64 MiB. Production configuration rejects both insecure session cookies
and `APP_DEBUG=true` before startup.
