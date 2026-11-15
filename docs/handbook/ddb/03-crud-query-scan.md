# 3. CRUD, Query vs Scan

## The four basics

| Operation | API | Behaviour |
|-----------|-----|-----------|
| Create / replace | `PutItem` | Writes the whole item. If the key exists, it is **fully replaced**, silently. |
| Read | `GetItem` | Needs the **full key** (PK + SK). Returns one item, or nothing. |
| Update | `UpdateItem` | Changes only the named attributes. **Creates the item if the key doesn't exist** (an "upsert"). |
| Delete | `DeleteItem` | Removes by full key. No error if it was already gone. |

Two surprises worth remembering:

- `PutItem` overwrites without asking. Chapter 5 shows how to prevent that.
- `UpdateItem` on a nonexistent key quietly creates a junk item containing just the key and the updated field. Chapter 5 also fixes this.

Code: `labs/ddb/jobs_repo.py` (`put_job`, `get_job`, `update_status`, `delete_job`), demo in `labs/ddb/crud.py`.

### Update expressions and reserved words

Updates use a mini language: `SET status = :s`. Values are passed separately as placeholders (`:s`) rather than concatenated into the string, which avoids injection and quoting problems. Attribute names that collide with DynamoDB's reserved words (`status`, `name`, `data`, and hundreds more) must be aliased with `#`: `SET #s = :s` plus a map `{"#s": "status"}`. You will hit this constantly.

## Query vs Scan

This is the most important performance idea in DynamoDB.

**Query**: reads *one drawer* (one PK value), optionally narrowed by a condition on the SK. Cost is proportional to the items it reads in that drawer.

**Scan**: reads *every item in the table*, then optionally filters. Cost is proportional to the size of the whole table.

Analogy: Query opens one drawer and reads in order. Scan empties the entire cabinet onto the floor and looks at everything.

### The filter trap

Both can take a `FilterExpression`. Crucially, **filters run after reading**. You still pay (and are limited) for everything read; the filter only trims what's returned.

The lab prints `read X → returned Y` for each case:

| Call | What gets read | What comes back |
|------|----------------|-----------------|
| Scan + filter `status=pending` | the whole table | only pending |
| Query `user_id=asha` | asha's drawer | asha's items |
| Query + filter | asha's drawer | asha's pending ones |

Notice that read count can be far larger than returned count. That gap is wasted money and time. If you often filter on an attribute, it probably deserves to be a key (chapter 4).

### The Limit + Filter trap

`Limit=5` limits items **evaluated**, not items returned. With a filter, DynamoDB reads 5 items, throws away the ones that don't match, and may return 0, 1, or 2. A response with fewer results than expected does *not* mean the end: check for `LastEvaluatedKey`.

### Pagination

Any read stops after **1 MB** of data (or `Limit`). If more remains, the response includes `LastEvaluatedKey`; pass it back as `ExclusiveStartKey` to continue. Never assume one call returned everything.

## Query details

- Key condition: PK must be `=`; SK may use `=`, `<`, `<=`, `>`, `>=`, `BETWEEN`, `begins_with`.
- Order: ascending by SK by default; `ScanIndexForward=False` gives newest first.
- Date range: with a time-prefixed SK, `BETWEEN '20261101' AND '20261130~'` covers whole days. The trailing `~` sorts after digits so the whole end day is included, since `20261130T...` is greater than `20261130` as text.

Code: `labs/ddb/jobs_repo.py` (`list_user_jobs`), `labs/ddb/scan.py`, 50-item seed in `labs/ddb/crud.py`.

## When Scan is acceptable

- Tiny tables, one-off scripts, migrations, exports.
- Never on a hot path of a real application.

## Key takeaways

- Get/Put/Update/Delete work on full keys; update is an upsert, put is a replace.
- Query = one drawer, cheap. Scan = whole table, expensive.
- Filters don't reduce what is read, only what is returned.
- `Limit` with a filter returns fewer than expected; paginate with `LastEvaluatedKey`.
