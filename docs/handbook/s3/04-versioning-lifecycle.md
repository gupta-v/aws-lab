# 4. Versioning and lifecycle

Two features that answer two different worries: *"what if I (or a bug) destroy data?"* and *"what if storage cost keeps growing?"*

## Versioning

### The idea

With versioning **off**, a key holds one object; a PUT overwrites it and a DELETE removes it, both irreversibly.

With versioning **on**, every write to a key creates a *new version* with a unique version ID. The key's "current" object is simply the newest version. Older versions stay stored and retrievable.

Example timeline for `notes/plan.md`:

```
PUT "v1"   → version A
PUT "v2"   → version B
PUT "v3"   → version C   ← current
GET key    → "v3"
GET key + versionId=A → "v1"
```

That second GET is your "undo".

### Deleting

A normal DELETE (no version ID) does **not** remove data. S3 adds a **delete marker**, a special newest "version" that makes the key look missing:

```
version C   "v3"
delete marker  ← current: GET returns 404
```

Everything underneath is intact. To **restore**, delete the delete marker; version C becomes current again.

To destroy data for real you delete a *specific version ID*. That is permanent, with no undo.

| Action | Versioning off | Versioning on |
|--------|----------------|---------------|
| Overwrite | old data lost | old data kept as a version |
| Delete | data gone | delete marker added |
| Delete with version ID | n/a | that version gone for good |

### Things to know

- Once enabled you can only **suspend** versioning, not return to the never-enabled state.
- Every version is billed. A file rewritten daily for a year is 365 stored copies.
- Versioning pairs well with **MFA Delete** and **Object Lock** when you need real tamper protection.
- It protects against accidents and bugs, not against someone with permission to delete versions.

Code: `labs/s3/versioning.py`, steps 1 to 6.

## Lifecycle rules

### The idea

Data value changes with age. Last week's report is read often; last year's almost never. A **lifecycle configuration** is a set of rules, each with a *filter* (prefix or tag) and *actions* triggered by age:

- **Transition**: move to a cheaper storage class.
- **Expiration**: delete the object.
- **Non-current version expiration**: delete old versions (the antidote to versioning bloat).
- **Abort incomplete multipart uploads**: reclaim orphaned parts (chapter 2).

### Storage classes

Cost trades against retrieval speed and fees.

| Class | Use | Storage price | Retrieval |
|-------|-----|---------------|-----------|
| STANDARD | hot, frequent access | highest | instant, free |
| STANDARD_IA | infrequent access | lower | instant, per-GB fee, 30-day minimum |
| GLACIER (flexible) | archive | very low | minutes to hours |
| Intelligent-Tiering | unknown or changing pattern | auto-moves between tiers | instant tiers, small monitoring fee |

(Prices change; check the S3 pricing page before relying on numbers.)

### Example policy design

| Data | Rule | Reasoning |
|------|------|-----------|
| `uploads/` temp files | expire after 7 days | users abandon them; no reason to keep |
| `reports/` | IA at 30 days, Glacier at 365 | read often at first, then archival |
| whole bucket | drop non-current versions after 30 days | keep an undo window without paying forever |
| whole bucket | abort stale multipart uploads after 7 days | invisible, billed leftovers |

Rules are matched by key prefix, which is another reason chapter 1 stressed designing keys around how data ages: `uploads/` and `reports/` get different treatment only because they sit under different prefixes.

### Behaviour notes

- Lifecycle runs asynchronously on AWS, roughly daily. Expect delay, not precision.
- Setting a lifecycle configuration **replaces** the previous one entirely, so always submit the full rule set.
- Transitions have rules of their own (minimum object sizes, minimum days in a class). Small objects can cost *more* after transitioning.
- Days-based rules are hard to demonstrate in a short local lab; here the value is learning to read and write the policy.

Code: `labs/s3/versioning.py` (the `rules` block).

## Putting them together

Versioning gives safety; lifecycle bounds its cost. A common production baseline:

1. Enable versioning on buckets holding data you can't regenerate.
2. Expire non-current versions after N days.
3. Abort incomplete multipart uploads.
4. Transition cold prefixes to cheaper classes.

## Key takeaways

- Versioning turns overwrite and delete into reversible operations.
- Delete marker = soft delete; delete by version ID = permanent.
- Lifecycle automates cost control by age and prefix.
- Versioning and lifecycle are meant to be used as a pair.
