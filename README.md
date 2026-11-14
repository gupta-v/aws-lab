# aws-lab

Local AWS labs (Floci emulator) for the 38-day [AI Cloud Ops roadmap](https://ai-cloud-ops-roadmap.vercel.app/).

```
utils/         shared helpers (s3_utils, ddb_utils)
setup/         start emulator + seed resources
labs/<service>/   s3/, ddb/, ... one folder per AWS service
floci-data/    emulator persistence (committed, syncs between workstations)
```

Progress: [docs/roadmap.md](docs/roadmap.md).

Run everything from repo root as modules:

```
uv run -m setup.floci
uv run -m setup.s3_lab
uv run -m labs.s3.presign
```

## Config

`cp .env.example .env`, then run with `uv run --env-file .env -m setup.floci` (or set `UV_ENV_FILE=.env` once).
