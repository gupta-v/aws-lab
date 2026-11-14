# aws-lab

Local AWS labs against Floci emulator, for 38-day AI Cloud Ops roadmap. Python >=3.14, managed with `uv`, deps: boto3, httpx.

## Layout

- `utils/` shared helpers (`s3_utils.py`, `ddb_utils.py`). Reuse, don't re-create boto3 clients in labs.
- `setup/` start emulator + seed resources (`floci.py`, `s3_lab.py`, `ddb_lab.py`).
- `labs/<service>/` one folder per AWS service (`s3/`, `ddb/`).
- `floci-data/` emulator persistence, committed on purpose (syncs state across 2 workstations). Stop Floci before commit/pull.

## Run

Always from repo root, as modules (imports rely on it):

```
uv run --env-file .env -m setup.floci      # start emulator
uv run --env-file .env -m setup.s3_lab     # seed S3
uv run --env-file .env -m labs.s3.presign  # run a lab
```

Config: `cp .env.example .env`. `AWS_ENDPOINT_URL=http://localhost:4566` points boto3 at Floci; remove it to hit real AWS.

## Conventions

- New lab = new module under `labs/<service>/`; new seed = `setup/<service>_lab.py`.
- Shared code goes in `utils/`, not copied between labs.
- Creds in `.env.example` are dummy (`test`). Never commit real keys or `.env`.
- Check `AWS_ENDPOINT_URL` before destructive calls: unset means real AWS.
- No test suite yet.
