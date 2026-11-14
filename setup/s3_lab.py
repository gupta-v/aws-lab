import os
from utils.s3_utils import BUCKET, get_s3, put_text

s3 = get_s3()
region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

existing = [b["Name"] for b in s3.list_buckets()["Buckets"]]
if BUCKET not in existing:
    # us-east-1 rejects an explicit LocationConstraint
    kw = {} if region == "us-east-1" else {"CreateBucketConfiguration": {"LocationConstraint": region}}
    s3.create_bucket(Bucket=BUCKET, **kw)

put_text(s3, BUCKET, "hello-floci.txt", "hello from floci")
for i in range(1, 21):
    month = "oct" if i <= 10 else "nov"
    put_text(s3, BUCKET, f"reports/2026/{month}/report-{i:02}.md", f"# Report {i}", "text/markdown")

print("Lab ready:", sum(1 for _ in s3.list_objects_v2(Bucket=BUCKET).get("Contents", [])), "objects")