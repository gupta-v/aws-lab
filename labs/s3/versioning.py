from utils.s3_utils import BUCKET, get_s3, put_text, get_text
import json

s3 = get_s3()
KEY = "notes/plan.md"

# 1. Turn versioning ON
s3.put_bucket_versioning(Bucket=BUCKET, VersioningConfiguration={"Status": "Enabled"})
print("Versioning:", s3.get_bucket_versioning(Bucket=BUCKET).get("Status"))

# 2. Write the same key 3 times
for text in ["v1: first draft", "v2: better", "v3: final"]:
    put_text(s3, BUCKET, KEY, text)
print("Current:", get_text(s3, BUCKET, KEY))

# 3. List every version (newest first)
versions = s3.list_object_versions(Bucket=BUCKET, Prefix=KEY)["Versions"]
for v in versions:
    print(v["VersionId"][:12], "<- latest" if v["IsLatest"] else "", v["Size"], "bytes")

# 4. Read an OLD version: the "undo"
oldest = versions[-1]["VersionId"]
old = s3.get_object(Bucket=BUCKET, Key=KEY, VersionId=oldest)["Body"].read().decode()
print("Oldest version:", old)

# 5. Delete: adds a delete marker, data still stored
s3.delete_object(Bucket=BUCKET, Key=KEY)
resp = s3.list_object_versions(Bucket=BUCKET, Prefix=KEY)
print("Delete markers:", len(resp.get("DeleteMarkers", [])),
      "| versions still stored:", len(resp["Versions"]))

# 6. Restore: delete the delete marker
marker = resp["DeleteMarkers"][0]["VersionId"]
s3.delete_object(Bucket=BUCKET, Key=KEY, VersionId=marker)
print("Restored:", get_text(s3, BUCKET, KEY))


rules = {"Rules": [
    # temp user uploads: delete after 7 days
    {"ID": "temp-uploads", "Status": "Enabled", "Filter": {"Prefix": "uploads/"},
     "Expiration": {"Days": 7}},
    # reports: cheaper storage as they age
    {"ID": "archive-reports", "Status": "Enabled", "Filter": {"Prefix": "reports/"},
     "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"},
                     {"Days": 365, "StorageClass": "GLACIER"}]},
    # whole bucket: delete old versions after 30 days + clean failed multipart uploads
    {"ID": "cleanup", "Status": "Enabled", "Filter": {"Prefix": ""},
     "NoncurrentVersionExpiration": {"NoncurrentDays": 30},
     "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}},
]}
s3.put_bucket_lifecycle_configuration(Bucket=BUCKET, LifecycleConfiguration=rules)
print(json.dumps(s3.get_bucket_lifecycle_configuration(Bucket=BUCKET)["Rules"], indent=2))