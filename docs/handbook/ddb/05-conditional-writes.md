# 5. Conditional writes

## The problem: races and duplicates

Plain writes don't look before they leap. Real systems hit two classic failures:

1. **Double processing.** An SQS message is delivered twice, or two workers poll the same queue. Both read "pending", both start the job, and the user is charged twice.
2. **Silent overwrite.** A retried create replaces an item that already moved on to `running`.

A read-then-write sequence ("check status; if pending, update") is **not safe**, because another worker can change the item between your check and your write.

## The idea

A **conditional write** attaches a condition to the write. DynamoDB checks it and applies the write **atomically, in one step**. If the condition is false, nothing is written and you get a `ConditionalCheckFailedException`.

So the check and the write can't be separated by anyone else. This is **optimistic concurrency**: don't lock, just make the write fail if the world changed.

Applies to `PutItem`, `UpdateItem`, and `DeleteItem` via a `ConditionExpression`.

## Condition building blocks

- `attribute_not_exists(job_id)`: item (key) isn't there yet.
- `attribute_exists(job_id)`: item is there.
- Comparisons on attributes: `#s = :pending`, `version = :v`, `attempts < :max`.
- Combine with `AND`, `OR`, `NOT`.

Using the key attribute inside `attribute_not_exists` / `attribute_exists` is the standard way to ask "does this item exist?".

## Four patterns

### 1. Create only if new (insert, not upsert)
`PutItem` + `attribute_not_exists(key)`. A second attempt fails instead of overwriting. Result: safe, idempotent creates (a client retrying with the same id causes no damage).

### 2. Claim a job (compare-and-set)
`UpdateItem` setting `status = running` **only if** `status = pending`. When two workers race, exactly one wins; the loser gets the failure and moves on. A late duplicate delivery also fails harmlessly because the status is already `running`.

### 3. Update only if it exists
`UpdateItem` + `attribute_exists(key)`. Fixes the upsert surprise from chapter 3: a typo'd id now raises an error instead of creating a junk item.

### 4. Optimistic locking with a version number
Store `version`. Read it, then write with `version = :seen` and increment it. If someone else changed the item, your condition fails, so you re-read and retry. Prevents lost updates in read-modify-write cycles.

Code: `labs/ddb/jobs_repo.py` (`create_job`, `claim_job`, `safe_update_status`); the demo `labs/ddb/conditional.py` runs all of them, including two threads racing for one job.

## Handling the failure

`ConditionalCheckFailedException` is **not an error to crash on**; it is the signal that the guard worked. Treat it as a normal result:

- Create → "already exists", maybe fetch it.
- Claim → "someone else has it", skip.
- Update on missing → report not found.

The helpers here turn it into a boolean (or a `LookupError`) so calling code stays simple.

Other exceptions (throttling, network) are different and usually worth retrying.

## Why this matters for idempotency

An operation is **idempotent** if doing it twice has the same effect as once. Distributed systems (queues, retries, Lambda) deliver messages *at least once*, so duplicates are normal, and the consumer must tolerate them. A conditional write is the cheapest way to make a consumer idempotent: the second attempt fails the condition and does nothing. This is the foundation for the S3 → SQS → Lambda → DynamoDB pipeline coming later.

## Related tools

- **`ReturnValues`**: ask for the old or new item back from a write. The safe-update helper uses `ALL_OLD` to return what was changed.
- **`ReturnValuesOnConditionCheckFailure`**: get the existing item back when a condition fails, saving a follow-up read.
- **Transactions** (`TransactWriteItems`): conditional writes across several items, all-or-nothing, at roughly double the cost. Reach for them only when one item isn't enough.

## Key takeaways

- Check-then-write in separate calls is a race; a condition makes it one atomic step.
- Failure of the condition is a normal outcome, handled, not crashed on.
- Patterns: create-if-new, claim-if-pending, update-if-exists, version check.
- Conditional writes are how you build idempotent workers.
