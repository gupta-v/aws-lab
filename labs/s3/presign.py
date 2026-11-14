"""Presigned URLs: temporary links that let anyone GET/PUT/POST an object without AWS keys.
Covers GET, PUT, POST with a size limit, expiry, and a browser download filename."""
import os
import sys
import time, uuid, httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from utils.s3_utils import BUCKET, get_s3, get_text, presign_get, presign_put, presign_post  # noqa: E402

s3 = get_s3()

# 1. Download link: anyone with it can read, no AWS keys needed
url = presign_get(s3, BUCKET, "reports/2026/nov/report-11.md")
print("GET link:", url[:90], "...")
print("Fetched:", httpx.get(url).text)

# 2. Upload with a PUT link (content type must match what was signed)
key = f"uploads/vaibhav/{uuid.uuid4()}.txt"
put_url = presign_put(s3, BUCKET, key, "text/plain")
r = httpx.put(put_url, content=b"uploaded via presigned PUT", headers={"Content-Type": "text/plain"})
print("PUT status:", r.status_code, "| stored:", get_text(s3, BUCKET, key))

# 3. Upload with a presigned POST and a size limit
key2 = f"uploads/vaibhav/{uuid.uuid4()}.txt"
post = presign_post(s3, BUCKET, key2, max_mb=1)
r = httpx.post(post["url"], data=post["fields"], files={"file": ("note.txt", b"small file, allowed")})
print("POST small:", r.status_code)
big = b"x" * (2 * 1024**2)  # 2 MB > 1 MB limit
r = httpx.post(post["url"], data=post["fields"], files={"file": ("big.txt", big)})
print("POST too big:", r.status_code, "(expect 4xx)")

# 4. Expiry
short = presign_get(s3, BUCKET, "hello-floci.txt", expires=2)
time.sleep(4)
print("Expired link status:", httpx.get(short).status_code, "(expect 403)")

# 5. Open this one in your browser: it downloads with a friendly name
print("Browser test:", presign_get(s3, BUCKET, "reports/2026/oct/report-01.md", download_name="my-report.md"))