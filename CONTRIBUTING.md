# Contributing

## Branches

- `main` must remain releasable.
- Use short-lived branches named `feat/*`, `fix/*`, `docs/*` or `chore/*`.

## Pull requests

- Keep each pull request focused on one engineering change.
- Add or update tests with behavior changes.
- Update architecture decisions when a change affects system boundaries.
- Do not merge until required CI checks pass.

## Local quality gates

Run `make lint`, `make typecheck` and `make test` before opening a pull request.

