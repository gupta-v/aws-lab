"""S3 CRUD practice: put/get text, list by prefix and folder, multipart upload/download, silent overwrite."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from boto3.s3.transfer import TransferConfig  # noqa: E402
from utils.s3_utils import BUCKET, get_s3  # noqa: E402


def put_text(s3, bucket, key, text, content_type="text/plain"):
    """CREATE/overwrite: store a string as an object. Same key again = silent overwrite."""
    s3.put_object(Bucket=bucket, Key=key, Body=text.encode(), ContentType=content_type)

def get_text(s3, bucket, key):
    """READ: fetch an object and decode its body (a stream) to str. Raises NoSuchKey if missing."""
    return s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode()

def upload(s3, path, bucket, key):
    """Upload a local file; boto3 switches to multipart automatically above the threshold."""
    cfg = TransferConfig(multipart_threshold=8 * 1024**2)   # multipart above 8 MB
    s3.upload_file(path, bucket, key, Config=cfg)

def download(s3, bucket, key, path):
    """Save an object to a local file path."""
    s3.download_file(bucket, key, path)

def list_objects(s3, bucket, prefix=""):
    """Yield (key, size) for every object under prefix; the paginator handles the 1000-per-page limit."""
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            yield obj["Key"], obj["Size"]

def list_folders(s3, bucket, prefix=""):
    """Like `ls`: Delimiter="/" groups keys into (folders, files) one level below prefix."""
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter="/")
    return [p["Prefix"] for p in resp.get("CommonPrefixes", [])], [o["Key"] for o in resp.get("Contents", [])]


s3, B = get_s3(), BUCKET

# 1. Write 20 small "reports" into folder-like prefixes
for i in range(1, 21):
    month = "oct" if i <= 10 else "nov"
    put_text(s3, B, f"reports/2026/{month}/report-{i:02}.md", f"# Report {i}", "text/markdown")

# 2. Read one back from memory
print(get_text(s3, B, "reports/2026/nov/report-15.md"))

# 3. List by prefix, then ls-style
print("Nov reports:", sum(1 for _ in list_objects(s3, B, "reports/2026/nov/")))
print("Folders under reports/2026/:", list_folders(s3, B, "reports/2026/"))

# 4. A 20 MB file to trigger multipart upload
with open("big.bin", "wb") as f:
    f.write(os.urandom(20 * 1024**2))
upload(s3, "big.bin", B, "data/big.bin")
download(s3, B, "data/big.bin", "big-back.bin")
print("Round trip OK:", os.path.getsize("big.bin") == os.path.getsize("big-back.bin"))

# 5. Overwrite is silent
put_text(s3, B, "reports/2026/nov/report-15.md", "# Overwritten!")
print(get_text(s3, B, "reports/2026/nov/report-15.md"))