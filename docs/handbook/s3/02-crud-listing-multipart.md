# 2. CRUD, listing, multipart

File: `labs/s3/practice.py`

The CRUD functions live in the lab on purpose (learning), not in `utils/`.

## Put and get

```python
s3.put_object(Bucket=b, Key=k, Body=text.encode(), ContentType=ct)
s3.get_object(Bucket=b, Key=k)["Body"].read().decode()
```

- `Body` is bytes, so encode strings.
- `get_object` returns a **stream** in `["Body"]`; `.read()` pulls it into memory. Fine for small objects, use `download_file` for big ones.
- Missing key → `NoSuchKey` error.
- **Overwrite is silent.** Putting the same key again replaces the object with no warning (unless versioning is on, chapter 4).

## Listing

### By prefix, paginated

`list_objects_v2` returns max 1000 keys per call. Use the paginator:

```python
for page in s3.get_paginator("list_objects_v2").paginate(Bucket=b, Prefix=prefix):
    for obj in page.get("Contents", []):
        ...
```

`Contents` is absent when nothing matches, hence `.get("Contents", [])`.

### ls-style folders

`Delimiter="/"` groups keys one level below the prefix:

- `CommonPrefixes` → "folders" (e.g. `reports/2026/oct/`)
- `Contents` → files directly at that level

Folders do not exist as objects; they are just shared key prefixes.

## Multipart upload

`upload_file` / `download_file` are managed transfers. With
`TransferConfig(multipart_threshold=8 * 1024**2)` boto3 splits files over 8 MB into parts and uploads them (in parallel), then S3 stitches them together.

Why it matters:

- Max single PUT is 5 GB; multipart goes to 5 TB.
- A failed part can be retried alone.
- Abandoned multipart uploads keep costing storage. The lifecycle rule `AbortIncompleteMultipartUpload` (chapter 4) cleans them.

The lab writes a 20 MB random file, uploads it to `data/big.bin`, downloads it back, and compares sizes.

## Cleanup note

The lab leaves `big.bin` and `big-back.bin` in the repo root. Delete them when done.
