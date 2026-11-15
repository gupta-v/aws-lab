# aws-lab

Local AWS labs (Floci emulator) for the 38-day [AI Cloud Ops roadmap](https://ai-cloud-ops-roadmap.vercel.app/).

```
utils/         plumbing only: clients, type helpers, .env loader (s3_utils, ddb_utils)
setup/         start emulator + seed resources
labs/<service>/   s3/, ddb/, ... one folder per AWS service; CRUD functions are written in the labs
floci-data/    emulator persistence (committed, syncs between workstations)
```

Progress: [docs/roadmap/roadmap.md](docs/roadmap/roadmap.md).

Run everything from repo root by file path:

```
uv run setup/floci.py        # start emulator
uv run setup/s3_lab.py       # seed S3
uv run setup/ddb_lab.py      # create DDB table
uv run labs/s3/practice.py   # run an S3 lab
uv run labs/ddb/crud.py      # run the DDB CRUD lab
```

Stop the emulator with `floci stop` before committing `floci-data/`.

## Config

`cp .env.example .env`. `utils` loads `.env` on import, so no `--env-file` flag is needed. Remove `AWS_ENDPOINT_URL` to hit real AWS.
