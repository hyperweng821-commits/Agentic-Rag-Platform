# Deployment guide

Development uses `compose.yaml`; isolated integration infrastructure uses `compose.test.yaml`. Tagged releases publish separate API and web images to GitHub Container Registry.

In Phase 3, `docker compose up --build` starts only `postgres` and `api`. ChromaDB and Ollama require `--profile rag`; the React shell requires `--profile frontend`. There is no worker service or worker image in this phase.

`compose.test.yaml` keeps ChromaDB behind the same `rag` profile. The current backend unit tests use mocks and do not require this Compose file.

Production secrets, TLS termination, backups and deployment-host configuration are intentionally deferred until the deployment phase.
