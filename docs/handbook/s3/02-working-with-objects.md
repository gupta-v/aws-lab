# 2. Working with objects

## Writing

A **PUT** stores an object under a key. Two behaviours to internalise:

1. **Overwrite is silent.** Putting to an existing key replaces it. No warning, no conflict check. If two writers race, last one wins. (Versioning in chapter 4 is the safety net; *conditional writes* exist on S3 for "only if absent" patterns.)
2. **Content-Type is metadata you choose.** S3 doesn't guess. If you store HTML as `text/plain`, browsers show source instead of rendering it. Set it deliberately.

Objects are immutable once written. "Updating" always means writing a replacement.

## Reading

A **GET** returns the metadata plus the body as a *stream*. For small objects you read it all into memory; for large ones you stream it to disk instead of loading gigabytes into RAM. Asking for a key that doesn't exist raises a `NoSuchKey` error, which is a normal control-flow case rather than a crash.

You can also fetch part of an object with a **range request** (bytes 0–1023), which is how video seeking and Parquet readers avoid downloading everything.

## Listing

Listing is the operation people misuse most.

- A single list call returns **at most 1000 keys**. Anything larger needs *pagination*: you get a continuation token and ask again. SDKs wrap this in a paginator so you don't loop by hand.
- Results come back sorted by key (UTF-8 order), which is why date-prefixed keys list chronologically.
- Listing is an API call you pay for, and it scales with the number of keys. Millions of objects means listing is slow; prefer well-chosen prefixes, or keep your own index (e.g. a DynamoDB table) for lookups.

**Prefix + delimiter** recap, with an example. Given:

```
reports/2026/oct/report-01.md
reports/2026/oct/report-02.md
reports/2026/nov/report-11.md
```

| Request | Result |
|---------|--------|
| prefix `reports/2026/` | all three keys |
| prefix `reports/2026/`, delimiter `/` | common prefixes `oct/`, `nov/`; no files |
| prefix `reports/2026/nov/`, delimiter `/` | one file: `report-11.md` |

Code: `labs/s3/practice.py` (`list_objects`, `list_folders`).

## Large objects and multipart upload

A single PUT is capped at 5 GB and, more practically, a single failed connection at 4.9 GB wastes everything. **Multipart upload** fixes this:

1. *Initiate* an upload and get an upload ID.
2. Upload numbered **parts** (5 MB to 5 GB each), in parallel if you like.
3. *Complete* the upload; S3 stitches the parts into one object (up to 5 TB).

Benefits: parallel speed, and a failed part is retried alone. SDK helpers decide automatically: below a size threshold they do one PUT, above it they go multipart.

The hidden cost: if step 3 never happens (crashed client), the uploaded parts sit in the bucket, invisible in listings but billed. A lifecycle rule to abort incomplete uploads (chapter 4) is standard hygiene.

Code: `labs/s3/practice.py` (`upload` with a transfer config).

## ETag, briefly

Every object has an ETag. For simple uploads it is the MD5 of the content, so you can verify integrity. For multipart uploads it is *not* a plain MD5 (it has a `-N` suffix for N parts), so don't compare it to a local MD5 of the file.

## Cost and performance notes

- You pay for storage, requests, and data transfer *out*. Many tiny objects cost more in requests than a few big ones.
- S3 scales request rates per prefix (thousands of requests per second), so spreading load across prefixes helps at extreme scale. Most projects never hit this.

## Key takeaways

- Objects are immutable; writes replace, silently.
- Stream big reads; paginate listings; use multipart for big writes.
- Prefix and delimiter turn a flat namespace into browsable "folders".
- Clean up abandoned multipart uploads.
