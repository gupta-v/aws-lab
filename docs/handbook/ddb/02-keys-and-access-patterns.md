# 2. Keys and access patterns

## The method: queries first, schema second

In SQL you model the *data*, then write whatever queries you need. In DynamoDB you reverse it:

1. **List every question the application must answer.** These are the *access patterns*.
2. **Pick keys so each question is one Query** on a single drawer (or one index).
3. Accept some duplication or extra indexes where one table layout can't serve every question.

If you can't state a query up front, you can't model for it.

## Example: a research-jobs table

Access patterns for an AI research app:

| # | Question | Frequency |
|---|----------|-----------|
| A | Get one job by id | every poll |
| B | List a user's jobs, newest first | every page load |
| C | List a user's jobs in a date range | reports |
| D | List all pending jobs across users | worker dispatch |

Mapping to keys:

- A, B, C all start with "for this user", so **PK = `user_id`**.
- B and C need time ordering, so the **SK must sort by time**.
- D is a different drawer entirely (by status), which no choice of base-table key serves well alongside A–C. That is what a **GSI** is for (chapter 4).

## Choosing the partition key

Ask:

1. **Does every query supply it?** If a query can't provide the PK value, it can't Query.
2. **Does it spread load?** Many distinct values, roughly even traffic.
3. **Is it stable?** You cannot change a key on an existing item; you'd delete and recreate it.

| Candidate | Verdict |
|-----------|---------|
| `user_id` | good: many values, natural "my stuff" query |
| `status` | bad as a base PK: three values means three giant hot drawers (fine as a *GSI* key, see chapter 4) |
| `created_date` | bad: all today's writes hit one drawer |

## Choosing the sort key

The SK gives you three things inside a drawer:

- **Ordering**: items come back sorted by SK.
- **Range queries**: `=`, `<`, `>`, `BETWEEN`, `begins_with`.
- **Uniqueness**: PK + SK together must be unique.

### Time-sortable ids

A trick used here: make the SK itself start with the timestamp, e.g. `20261114T223000-a1b2c3d4`.

- Sorting by the key *is* sorting by time, so "newest first" and "between Nov 1 and Nov 30" are cheap key operations, no extra attribute needed.
- The random suffix keeps two jobs created in the same second distinct.
- Use a format where text order equals time order (zero-padded, most significant first, ISO-style). `11-14-2026` sorts wrongly; `20261114` sorts correctly.

The roadmap's suggested form is `created_at#job_id`, the same idea with an explicit `#` separator. The lab folds the timestamp into the id itself, which saves an attribute and gives the same behaviour.

Code: `utils/ddb_utils.py` (`new_job_id`), range query in `labs/ddb/jobs_repo.py` (`list_user_jobs`).

### Composite sort keys

Packing several fields into the SK (`region#status#date`) lets one drawer answer hierarchical questions with `begins_with`: all of `eu#`, or only `eu#pending#`. Order the parts from broadest to most specific.

## One table vs many

Relational habit says one table per entity. DynamoDB practice often puts several entity types in **one table** with generic key names and prefixes (`USER#42`, `JOB#...`), so related items live in the same drawer and load in one Query. It's powerful but harder to read; for a first project, one table per entity is fine.

## Common mistakes

- Designing like SQL, then discovering you need a join.
- Using a low-cardinality attribute as the PK.
- Forgetting a query until after launch (fix: a new GSI, chapter 4).
- Putting the timestamp somewhere that doesn't sort.

## Key takeaways

- Write the access patterns first; the keys follow from them.
- PK = what every query knows, spread evenly. SK = how you want results ordered or filtered.
- A SK that sorts correctly as text gives you free time-range queries.
- Patterns the base key can't serve become GSIs.
