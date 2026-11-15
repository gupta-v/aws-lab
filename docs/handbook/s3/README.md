# S3 Handbook

Theory and mental models for Amazon S3. Each chapter explains the concept, then points to the lab code where you can see it in action.

| # | Chapter | Question it answers |
|---|---------|---------------------|
| 1 | [What S3 is](01-what-s3-is.md) | How is S3 different from a disk? What are buckets, keys, and "folders"? |
| 2 | [Working with objects](02-working-with-objects.md) | How do reads, writes, listing, and big uploads behave? |
| 3 | [Presigned URLs](03-presigned-urls.md) | How do I give someone temporary access without sharing keys? |
| 4 | [Versioning and lifecycle](04-versioning-lifecycle.md) | How do I protect data from mistakes and control storage cost? |

Read in order; each builds on the last.

## Roadmap mapping

| Roadmap item | Chapter |
|--------------|---------|
| 1.1 Cloud mental model, 1.2 Service map (S3 parts) | 1 |
| 2.1 boto3 sessions, clients, endpoints | 1 |
| 2.2 Upload, download, list | 2 |
| 2.3 Presigned URLs | 3 |
| 2.4 Versioning, lifecycle, storage classes | 4 |

## Self-check (Day 2 questions from the roadmap)

1. What problem does a presigned URL solve? → chapter 3, "The problem".
2. When would you turn on bucket versioning? → chapter 4, "Putting them together".

Also from Day 1: regions vs AZs, and what AWS vs you are responsible for → chapter 1, "Where S3 sits in the cloud".

## Code index

| Concept | Where to look |
|---------|---------------|
| Client setup, local vs real AWS | `utils/s3_utils.py` (`get_s3`) |
| Seeding sample data | `setup/s3_lab.py` |
| Object CRUD, listing, multipart | `labs/s3/practice.py` |
| Presigned GET / PUT / POST | `labs/s3/presign.py`, `labs/s3/presign_1.py` |
| Versioning, lifecycle | `labs/s3/versioning.py` |
