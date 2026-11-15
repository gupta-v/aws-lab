# 4. Global secondary indexes (GSI)

## The problem

Base table: PK `user_id`, SK `job_id`. Question: *"show all pending jobs across every user."*

The base key can't answer it: pending jobs are scattered across every user's drawer. Your only option would be a Scan with a filter, reading the whole table to find a few items (chapter 3).

## The idea

A **GSI** is an automatically maintained **second copy of your data organised under a different key**. You pick a new PK (and optional SK); DynamoDB keeps the index in sync every time the base table changes. Then you Query the index exactly like a table.

Picture: a second filing cabinet where the same folders are re-filed by *status* instead of by *user*. You never write to it yourself.

For the jobs table:

```
Base table             user_id (drawer) → job_id (order)
status-index (GSI)     status  (drawer) → job_id (order)
```

Querying `status = pending` now opens a single "pending" drawer holding only pending jobs, newest first.

Code: index creation in `utils/ddb_utils.py` (`add_status_index`), query in `labs/ddb/jobs_repo.py` (`list_by_status`).

## Seeing the difference

`labs/ddb/gsi.py` compares the two approaches with `read X → returned Y`:

- Scan + filter: reads every item, returns pending ones.
- GSI Query: reads only the pending drawer, returns the same set.

Same answer, far less work. The gap grows with table size.

## Design choices when making an index

### Key schema
Same rules as chapter 2: the index PK must be something your query supplies; the SK gives ordering and range filtering inside that drawer.

Caution: `status` has very few distinct values, so a GSI keyed on it concentrates traffic in a few big drawers. It's fine at lab scale. At large scale you'd spread it (e.g. add a shard suffix like `pending#3`, or combine with another attribute).

### Projection: what gets copied into the index

| Projection | Index contains | Trade-off |
|-----------|----------------|-----------|
| `KEYS_ONLY` | only the index and table keys | smallest and cheapest; follow up with `GetItem` for the rest |
| `INCLUDE` | keys plus chosen attributes | middle ground |
| `ALL` | the whole item | simplest to query; costs the most storage and write units |

The lab uses `ALL` for convenience.

## Behaviour you must know

- **Eventually consistent only.** You can't do strongly consistent reads on a GSI. After a write there's a brief lag before the index reflects it.
- **Writes cost more.** Each write to the base table also writes to every affected index, and you pay for that.
- **Not unique.** Unlike base table keys, many items can share the same GSI key. A GSI is for lookup, not for enforcing uniqueness.
- **Sparse indexes.** An item appears in the index only if it has the index's key attributes. Omit the attribute and the item isn't indexed. This is a neat trick: give only "open" jobs a `needs_review` attribute, and that index contains only them.
- **Updates move items between drawers.** The lab flips a job pending → done, then counts again: the item vanishes from the pending drawer without you touching the index.
- **You write to the table, never to the index.**
- Adding a GSI to an existing table triggers a background **backfill**; the index status is `CREATING` until it becomes `ACTIVE`.

## GSI vs LSI

A *local* secondary index shares the base table's PK and gives an alternate SK. It must be defined at table creation and has a 10 GB per-partition limit. GSIs are far more flexible (any key, added later), so they are the usual choice.

## Cost of over-indexing

Every index multiplies write cost and storage. Add one per real access pattern, not speculatively.

## Key takeaways

- GSI = automatically maintained re-filing of the table under a different key.
- Use it to turn a Scan into a Query for a known access pattern.
- Eventually consistent, extra write cost, and not unique.
- Choose projection by what the query needs; watch low-cardinality keys at scale.
