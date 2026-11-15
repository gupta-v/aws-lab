# DynamoDB Handbook

Theory and mental models for Amazon DynamoDB (Day 3: data modelling). Each chapter explains the concept, then points to lab code where you can see it.

| # | Chapter | Question it answers |
|---|---------|---------------------|
| 1 | [What DynamoDB is](01-what-ddb-is.md) | How is it different from SQL? Items, keys, partitions, capacity. |
| 2 | [Keys and access patterns](02-keys-and-access-patterns.md) | How do I choose partition and sort keys? |
| 3 | [CRUD, Query vs Scan](03-crud-query-scan.md) | How do reads and writes work, and why is Scan the trap? |
| 4 | [Global secondary indexes](04-global-secondary-indexes.md) | How do I support a second way of querying? |
| 5 | [Conditional writes](05-conditional-writes.md) | How do I stop races and duplicates? |

Read in order; each builds on the last.

## Roadmap mapping

| Roadmap item | Chapter |
|--------------|---------|
| 3.1 Keys and access patterns | 1, 2 |
| 3.2 CRUD, Query vs Scan | 3 |
| 3.3 Global secondary indexes | 4 |
| 3.4 Conditional writes | 5 |

## Code index

| Concept | Where to look |
|---------|---------------|
| Client, table creation, type helpers | `utils/ddb_utils.py` |
| Seeding the table | `setup/ddb_lab.py` |
| CRUD, query, GSI and conditional helpers | `labs/ddb/jobs_repo.py` |
| CRUD and 50-item insert demo | `labs/ddb/crud.py` |
| Scan vs Query vs filter | `labs/ddb/scan.py` |
| GSI | `labs/ddb/gsi.py` (index creation in `utils/ddb_utils.py`) |
| Conditional writes and races | `labs/ddb/conditional.py` |
