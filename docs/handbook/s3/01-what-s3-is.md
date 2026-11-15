# 1. What S3 is

## Object storage, not a file system

A normal disk gives you a tree of directories and files you can open, seek into, and edit in place. S3 gives you something simpler: you **put** a whole object and **get** a whole object, over HTTP. There is no "open file and change byte 500". To change an object you upload a new copy.

That simplicity is the trade that buys S3 its properties: practically unlimited capacity, very high durability (AWS quotes eleven 9s), and access from anywhere with an HTTP client.

Good fit: images, backups, logs, datasets, static sites, model artifacts, Terraform state.
Poor fit: a database, or a file you append to constantly.

## The three nouns

- **Bucket**: a top-level container. Its name is globally unique across all AWS accounts, and it lives in one region.
- **Key**: the object's full name within the bucket, e.g. `reports/2026/nov/report-11.md`.
- **Object**: the bytes (up to 5 TB) plus metadata such as `Content-Type`, size, and ETag.

So the address of anything is just *bucket + key*. It behaves like a giant dictionary: `bucket[key] → bytes`.

## "Folders" are an illusion

The key `reports/2026/nov/report-11.md` does not mean a `reports` directory contains a `2026` directory. It is one flat string that happens to contain slashes. The console draws folders because humans like them.

Consequences:

- You can't "create an empty folder" in any real sense (the console fakes it with a zero-byte key ending in `/`).
- You can't rename or move a folder cheaply. A "rename" is copy every key, then delete the old ones.
- Listing by **prefix** is how you emulate directories. Asking for everything starting with `reports/2026/nov/` is the equivalent of `ls` on a folder. Adding a **delimiter** (`/`) makes S3 group the results into "sub-folders" (called *common prefixes*) and direct files.

Design tip: choose key layouts for how you'll query them. `reports/2026/nov/...` makes "all November reports" a cheap prefix scan; `reports/november-2026-...` does not.

Code: `setup/s3_lab.py` seeds this exact layout.

## Where S3 sits in the cloud (Day 1 vocabulary)

- **Region**: a geographic area (e.g. `us-east-1`). A bucket lives in exactly one region; data never leaves it unless you configure replication. Pick the region near your users or your compute, and mind data-residency rules.
- **Availability zone (AZ)**: one or more isolated data centres inside a region. Standard S3 stores each object across at least three AZs, which is where the durability comes from. (One Zone classes keep a single AZ and cost less.)
- **Shared responsibility**: AWS secures the infrastructure (disks, facilities, the service itself). You secure what you put in it: bucket policies, public-access settings, encryption choices, who gets keys. Nearly every S3 breach in the news is a customer-side misconfiguration, not an AWS failure.
- **Service map**: S3 is the *storage* service. In an AI app it holds uploads, datasets, agent reports, and model artifacts, while DynamoDB holds small queryable state and Lambda/SQS react to events.

## Consistency

S3 is strongly consistent: after a successful write, any following read or list sees it. (Older S3 was eventually consistent; many old blog posts still describe that. Ignore them.)

## Talking to S3 from code

boto3 is the Python SDK. The key idea is that the **same code runs against the emulator or real AWS**, controlled by one environment variable pointing at a different endpoint. If it's unset you are talking to real AWS, which is why destructive scripts should check it first.

Two details worth knowing:

- **Addressing style.** Real S3 puts the bucket in the hostname (`my-bucket.s3.amazonaws.com`). A local emulator on `localhost` can't do that, so it uses *path style* (`localhost:4566/my-bucket/key`).
- **Credentials** are never written into code. boto3 walks a chain: environment variables, shared config files, then an attached role. On real infrastructure you almost always want the role.

Code: `utils/s3_utils.py` (`get_s3`).

## Security defaults

New buckets are private and block public access by default. Access is granted through IAM policies (who may do what), and optionally bucket policies. Presigned URLs (chapter 3) are the escape hatch for temporary, narrow access.

## Key takeaways

- Whole-object put/get over HTTP; no in-place edits.
- Address = bucket + key; the namespace is flat.
- Folders are prefixes; design keys around your listing needs.
- Strongly consistent today.
