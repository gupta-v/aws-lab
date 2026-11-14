import os
from utils.s3_utils import BUCKET, get_s3, put_text, get_text, upload, download, list_objects, list_folders

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