import os
import boto3
from botocore.config import Config
from boto3.s3.transfer import TransferConfig

BUCKET = os.getenv("S3_BUCKET", "my-bucket")


def get_s3():
    """S3 client that works on Floci locally and on real AWS unchanged."""
    endpoint = os.getenv("AWS_ENDPOINT_URL")          # set → Floci, unset → real AWS
    is_local = bool(endpoint and "localhost" in endpoint)
    cfg = Config(s3={"addressing_style": "path"}) if is_local else None
    return boto3.client("s3", config=cfg)             # credentials come from the chain

def list_buckets(s3):
    return [b["Name"] for b in s3.list_buckets()["Buckets"]]

def list_objects(s3, bucket, prefix=""):
    """Yields every object, however many pages there are."""
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            yield obj["Key"], obj["Size"]


def put_text(s3, bucket, key, text, content_type="text/plain"):
    s3.put_object(Bucket=bucket, Key=key, Body=text.encode(), ContentType=content_type)

def get_text(s3, bucket, key):
    return s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode()

def upload(s3, path, bucket, key):
    cfg = TransferConfig(multipart_threshold=8 * 1024**2)   # multipart above 8 MB
    s3.upload_file(path, bucket, key, Config=cfg)

def download(s3, bucket, key, path):
    s3.download_file(bucket, key, path)

def list_folders(s3, bucket, prefix=""):
    """Top-level 'folders' and files under a prefix, like ls."""
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter="/")
    folders = [p["Prefix"] for p in resp.get("CommonPrefixes", [])]
    files = [o["Key"] for o in resp.get("Contents", [])]
    return folders, files

def presign_get(s3, bucket, key, expires=300, download_name=None):
    params = {"Bucket": bucket, "Key": key}
    if download_name:   # makes the browser download with this filename
        params["ResponseContentDisposition"] = f'attachment; filename="{download_name}"'
    return s3.generate_presigned_url("get_object", Params=params, ExpiresIn=expires)

def presign_put(s3, bucket, key, content_type, expires=300):
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )

def presign_post(s3, bucket, key, max_mb=5, expires=300):
    return s3.generate_presigned_post(
        Bucket=bucket, Key=key, ExpiresIn=expires,
        Conditions=[["content-length-range", 1, max_mb * 1024**2]],
    )


if __name__ == "__main__":
    s3 = get_s3()
    print("Endpoint:", s3.meta.endpoint_url)
    print("Buckets:", list_buckets(s3))
    for key, size in list_objects(s3, BUCKET):
        print(f"{size:>8} bytes  {key}")