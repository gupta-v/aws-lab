# 1. What DynamoDB is

## A different kind of database

A relational database (Postgres, MySQL) stores normalised tables and lets you ask almost any question later with SQL `JOIN`s and `WHERE`s. The database does the hard work at query time.

DynamoDB is a **key-value / document database** that makes the opposite trade: it only does a few operations, but each one stays fast (single-digit milliseconds) whether the table has a thousand items or a billion. There are no joins, no ad-hoc queries, and no server to manage.

The price: **you must know your questions before you design the table.** That is the single biggest mental shift, and the whole of chapter 2.

Good fit: job status, sessions, carts, user profiles, event records, anything looked up by a known key.
Poor fit: analytics, reporting, "search everything by anything".

## The vocabulary

- **Table**: a collection of items. Only the key attributes are declared up front.
- **Item**: one record, up to 400 KB. Like a row, but different items can have different attributes (schemaless apart from keys).
- **Attribute**: a field on an item. Types include string (`S`), number (`N`), binary, boolean, list, map, sets.
- **Primary key**: uniquely identifies an item. Two flavours:
  - *Partition key only* (simple key).
  - *Partition key + sort key* (composite key).

### The filing-cabinet picture

- **Partition key (PK)** = which **drawer**. DynamoDB hashes it to decide where the data physically lives.
- **Sort key (SK)** = the **order inside the drawer**.
- An item is found by *drawer + position*. Reading one drawer, in order, is cheap. Searching across all drawers is not.

Example with a jobs table (PK `user_id`, SK `job_id`):

```
Drawer u-asha     : job 20261003T... , job 20261019T... , job 20261107T...
Drawer u-rohan    : job 20261001T... , job 20261120T...
Drawer u-vaibhav  : job 20261014T... , ...
```

Code: `utils/ddb_utils.py` (`create_jobs_table`) defines this key schema.

## Partitions and why key choice matters

DynamoDB spreads data across many internal **partitions**, chosen by hashing the partition key. This is what makes it scale, and it implies:

- A good PK has **many distinct values** and spreads traffic evenly (user id, order id).
- A bad PK concentrates load on one drawer (a **hot partition**): e.g. `status` with three values, or a date where today's writes all hit one key.
- Each partition has throughput limits. One very hot key gets throttled even if the table as a whole is idle.

## Capacity and billing

Two modes:

- **On-demand (pay per request)**: no planning, pay per read and write. Best for new, spiky, or unknown workloads. The labs use this.
- **Provisioned**: you reserve read/write capacity units; cheaper at steady, predictable load, with optional auto-scaling.

Roughly: one read unit = one strongly consistent read of up to 4 KB; one write unit = a write of up to 1 KB. Larger items cost more units, which is why you read and write small items and avoid fat ones.

## Consistency

- **Eventually consistent reads** (default): cheaper, may briefly miss a write that just happened.
- **Strongly consistent reads**: always see the latest write, at double the read cost. Not available on GSIs (chapter 4).

## Talking to it from code

boto3 offers two layers. The **client** (used in the labs) speaks DynamoDB's native wire format, where every value carries its type: `{"status": {"S": "pending"}}`. The higher-level **resource/Table** API hides that. The labs use the client plus small translate helpers, because seeing the typed format teaches you what DynamoDB actually stores.

As with S3, one environment variable decides whether calls hit the local emulator or real AWS.

Code: `utils/ddb_utils.py` (`get_ddb`, `to_ddb`, `from_ddb`).

## Key takeaways

- Fast and scalable because it only supports key-based access.
- Design from the queries; there is no ad-hoc querying later.
- PK = drawer (distribution), SK = order inside the drawer.
- Spread keys evenly to avoid hot partitions.
- On-demand billing is the sensible default while learning.
