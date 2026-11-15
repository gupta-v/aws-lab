# 3. Presigned URLs

## The problem

A user's browser wants to upload a photo. Options:

1. **Proxy it** through your server. Works, but your server pays the bandwidth, memory, and timeout cost of every upload.
2. **Give the browser AWS keys.** Never. They'd have your permissions.
3. **Give the browser a temporary, single-purpose link straight to S3.** This is a presigned URL.

## How it works

Every S3 request must be signed with credentials. A presigned URL is a request that **you pre-signed in advance** and packed into a link. Whoever holds the link can replay exactly that request until it expires; S3 treats it as if you made it.

What the signature locks in:

- the HTTP method (GET vs PUT),
- the bucket and key,
- the expiry time,
- any headers you chose to sign (e.g. `Content-Type`).

Change any of these and S3 rejects it with 403 `SignatureDoesNotMatch`. The link holder gets no other powers: they can't list the bucket or touch other keys.

Important: **the link carries your permissions.** If the signing identity can't read an object, the link won't work either. And the signing happens locally with no network call, so generating a thousand links is cheap.

## Three kinds

### GET: temporary download

Share a private file with someone for, say, 10 minutes. You can also override the response filename so the browser downloads it as `my-report.md` instead of a UUID-style key.

### PUT: upload to one fixed key

The client sends the raw bytes with an HTTP PUT. Because headers are signed, the client **must send the same `Content-Type`** you signed. This is a common source of confusing 403s: you signed `text/plain`, the browser sent `application/octet-stream`.

Weakness: PUT cannot limit the upload size. Someone could push a 5 GB file into a link you meant for avatars.

### POST: upload with rules

A presigned POST is a form submission with a signed *policy* of conditions. The headline condition is a size range, e.g. between 1 byte and 1 MB, and S3 refuses anything outside it. You can also constrain key prefix and content type. When you accept uploads from untrusted users, prefer POST for this reason.

| | GET | PUT | POST |
|---|-----|-----|------|
| Direction | download | upload | upload |
| Size limit | n/a | no | yes |
| Client sends | plain GET | raw body + signed headers | multipart form with returned fields |

## Expiry

Every link has a lifetime (seconds). After it, S3 returns 403. Choose the shortest that fits the use: minutes for uploads, longer only for sharing.

AWS caveat: if the link was signed with **temporary credentials** (an assumed role, Lambda role, etc.), it dies when those credentials do, even if you asked for a longer expiry. A Lambda signing with its role can't make day-long links.

## Designing the key

The server picks the key, never the client. A typical pattern is `uploads/<user>/<uuid>.<ext>`:

- the UUID prevents collisions and overwrites,
- the user segment keeps one user's files together,
- the `uploads/` prefix makes lifecycle rules easy (expire temp uploads).

## Typical flow

```
Browser ──1. "I want to upload a .png"──▶ Your API
Browser ◀─2. presigned URL + key──────── Your API   (API decides key, type, limit)
Browser ──3. PUT/POST file directly────▶ S3
Your API ◀─4. S3 event (optional)──────── S3        (trigger processing)
```

Step 4 is where later labs go: S3 event → SQS → Lambda.

## Security checklist

- Treat a link like a password until it expires.
- Short expiry; narrow key; server-chosen key.
- Use POST conditions for untrusted uploads.
- Remember links show up in logs, browser history, and referrer headers.

Code: `utils/s3_utils.py` (`presign_get`, `presign_put`, `presign_post`), `labs/s3/presign.py` (all three plus expiry), `labs/s3/presign_1.py` (interactive PUT where the content type is decided *before* signing).

## Key takeaways

- A presigned URL is a pre-signed, replayable, time-limited request.
- It grants exactly one action on one key, with your permissions.
- PUT is simple; POST adds enforceable limits.
- Signed headers must match what the client sends.
