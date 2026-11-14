# aws-lab

Local AWS labs against Floci emulator, for 38-day AI Cloud Ops roadmap. Python >=3.14, managed with `uv`, deps: boto3, httpx.

## Layout

- `utils/` plumbing only (`s3_utils.py`, `ddb_utils.py`): client getters, type helpers, table setup. `utils/__init__.py` loads `.env` on import. Reuse, don't re-create boto3 clients in labs.
- `setup/` start emulator + seed resources (`floci.py`, `s3_lab.py`, `ddb_lab.py`).
- `labs/<service>/` one folder per AWS service (`s3/`, `ddb/`). CRUD functions are written in the labs on purpose (learning); `labs/ddb/jobs_repo.py` holds import-safe DDB helpers, `crud.py` is the demo.
- `floci-data/` emulator persistence, committed on purpose (syncs state across 2 workstations). Stop Floci before commit/pull.

## Run

Always from repo root, by file path (each script adds the repo root to `sys.path` itself, so `utils` imports work):

```
uv run setup/floci.py        # start emulator
uv run setup/s3_lab.py       # seed S3
uv run setup/ddb_lab.py      # create DDB table
uv run labs/s3/presign.py    # run an S3 lab
uv run labs/ddb/crud.py      # run the DDB lab
```

`--env-file .env` is optional: importing `utils` loads `.env`. Every runnable script must keep its `sys.path.insert` line. Do not use `-m` or drop the `.py`.

Config: `cp .env.example .env`. `AWS_ENDPOINT_URL=http://localhost:4566` points boto3 at Floci; remove it to hit real AWS.

## Conventions

- New lab = new module under `labs/<service>/`; new seed = `setup/<service>_lab.py`.
- Plumbing goes in `utils/`. Lab code (the AWS calls being learned) stays in the lab; move it to `utils/` or a `<lab>_repo.py` only when a second lab needs it.
- Lab scripts must be import-safe or live in a separate demo file (no top-level inserts in helper modules).
- Creds in `.env.example` are dummy (`test`). Never commit real keys or `.env`.
- Check `AWS_ENDPOINT_URL` before destructive calls: unset means real AWS.
- No test suite yet.
