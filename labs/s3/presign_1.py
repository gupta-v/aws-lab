"""Interactive presigned PUT: upload a file path or typed text.
The Content-Type is worked out first, then signed, so the upload must send the same type."""
import mimetypes, uuid
import os
import sys
from pathlib import Path
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from utils.s3_utils import BUCKET, get_s3, get_text, presign_put  # noqa: E402

s3 = get_s3()

def is_file_path(text: str) -> bool:
    """True if text (optionally quoted, e.g. a dragged-in path) is an existing file."""
    try:
        return bool(text) and Path(text.strip('"\'')).is_file()
    except OSError:
        return False

content = input("Enter a path or write something to upload: ").strip()

# 1. Work out WHAT we're uploading
if is_file_path(content):
    path = Path(content.strip('"\''))
    data = path.read_bytes()
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    key = f"uploads/vaibhav/{uuid.uuid4()}{path.suffix}"
    print(f"Uploading file: {path.name} ({len(data)} bytes, {content_type})")
else:
    data = content.encode()
    content_type = "text/plain"
    key = f"uploads/vaibhav/{uuid.uuid4()}.txt"
    print(f"Uploading text: {content}")

# 2. THEN sign the URL for exactly that type
put_url = presign_put(s3, BUCKET, key, content_type)
r = httpx.put(put_url, content=data, headers={"Content-Type": content_type})

# 3. Confirm (only show contents for text)
print("PUT status:", r.status_code, "| key:", key)
if content_type.startswith("text/"):
    print("Stored:", get_text(s3, BUCKET, key))