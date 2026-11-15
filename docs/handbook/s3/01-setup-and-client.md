# 1. Setup and client

Files: `utils/s3_utils.py`, `setup/s3_lab.py`

## One client, local or real AWS

`get_s3()` builds a boto3 S3 client. The endpoint comes from the environment:

- `AWS_ENDPOINT_URL=http://localhost:4566` → boto3 talks to Floci (the local emulator).
- Variable unset → boto3 talks to **real AWS**. Same code, no changes.

boto3 reads `AWS_ENDPOINT_URL` by itself; `get_s3()` only checks it to decide on addressing style.

### Path-style addressing (local only)

Real S3 uses virtual-host style: `my-bucket.s3.amazonaws.com/key`. On `localhost` that hostname cannot resolve, so locally we force path style: `localhost:4566/my-bucket/key`.

```python
Config(s3={"addressing_style": "path"})
```

### Credentials

Not passed in code. boto3 finds them through its credential chain (env vars, shared config, role). `.env.example` holds dummy `test` creds for Floci. Never commit real keys.

## Seeding the lab (`setup/s3_lab.py`)

1. List buckets; create `BUCKET` (env `S3_BUCKET`, default `my-bucket`) only if missing.
2. `us-east-1` rejects an explicit `LocationConstraint`; every other region requires one. The script handles both.
3. Upload `hello-floci.txt` plus 20 reports: `reports/2026/oct/report-01..10.md` and `reports/2026/nov/report-11..20.md`.

Safe to re-run: bucket creation is guarded, puts just overwrite.

## Helpers in `s3_utils.py`

| Function | Purpose |
|----------|---------|
| `get_s3()` | client (see above) |
| `list_buckets(s3)` | bucket names |
| `put_text` / `get_text` | write/read a string object |
| `presign_get/put/post` | temporary links, see chapter 3 |

Its `__main__` block prints the endpoint, buckets, and objects with sizes (a quick connectivity check).
