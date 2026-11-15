"""Job CRUD helpers (raw boto3). Import-safe: no demo code runs on import."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from utils.ddb_utils import TABLE, to_ddb, from_ddb  # noqa: E402


def _key(user_id, job_id):
    """Full primary key (PK + SK) in DynamoDB typed format."""
    return to_ddb({"user_id": user_id, "job_id": job_id})

def put_job(ddb, job, table=TABLE):
    """Create OR fully replace (no error if it already exists)."""
    ddb.put_item(TableName=table, Item=to_ddb(job))

def get_job(ddb, user_id, job_id, table=TABLE):
    """One item by its full key, or None."""
    resp = ddb.get_item(TableName=table, Key=_key(user_id, job_id))
    return from_ddb(resp["Item"]) if "Item" in resp else None

def update_status(ddb, user_id, job_id, status, table=TABLE):
    """Change one field. Note: creates the item if the key doesn't exist."""
    ddb.update_item(
        TableName=table,
        Key=_key(user_id, job_id),
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={"#s": "status"},      # 'status' is a reserved word
        ExpressionAttributeValues=to_ddb({":s": status}),
    )

def delete_job(ddb, user_id, job_id, table=TABLE):
    """No error if it doesn't exist."""
    ddb.delete_item(TableName=table, Key=_key(user_id, job_id))

def list_user_jobs(ddb, user_id, newest_first=True, limit=None,
                   start=None, end=None, table=TABLE):
    """Query ONE drawer. start/end are dates like '20261101' (job_id starts with time)."""
    expr, values = "user_id = :u", {":u": user_id}
    if start and end:
        expr += " AND job_id BETWEEN :a AND :b"
        values.update({":a": start, ":b": end + "~"})   # '~' sorts after digits -> whole end day included
    kwargs = dict(TableName=table, KeyConditionExpression=expr,
                  ExpressionAttributeValues=to_ddb(values),
                  ScanIndexForward=not newest_first)    # False = newest first
    if limit:
        kwargs["Limit"] = limit
    return [from_ddb(i) for i in ddb.query(**kwargs)["Items"]]

def list_by_status(ddb, status, newest_first=True, limit=None, table=TABLE):
    """Query the GSI: ONE status drawer across ALL users."""
    kwargs = dict(TableName=table, IndexName="status-index",
                  KeyConditionExpression="#s = :s",
                  ExpressionAttributeNames={"#s": "status"},
                  ExpressionAttributeValues=to_ddb({":s": status}),
                  ScanIndexForward=not newest_first)
    if limit:
        kwargs["Limit"] = limit
    return [from_ddb(i) for i in ddb.query(**kwargs)["Items"]]

# ---------- 3.4 conditional writes ----------

def create_job(ddb, job, table=TABLE):
    """Put ONLY IF this key doesn't exist yet. Returns True if created, False if it was already there."""
    try:
        ddb.put_item(TableName=table, Item=to_ddb(job),
                     ConditionExpression="attribute_not_exists(job_id)")
        return True
    except ddb.exceptions.ConditionalCheckFailedException:
        return False

def claim_job(ddb, user_id, job_id, worker, table=TABLE):
    """pending -> running ONLY IF still pending. Returns True if this worker won the job."""
    try:
        ddb.update_item(
            TableName=table,
            Key=_key(user_id, job_id),
            UpdateExpression="SET #s = :running, worker = :w",
            ConditionExpression="#s = :pending",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues=to_ddb({":running": "running", ":pending": "pending", ":w": worker}),
        )
        return True
    except ddb.exceptions.ConditionalCheckFailedException:
        return False

def safe_update_status(ddb, user_id, job_id, status, table=TABLE):
    """Like update_status, but FAILS for a job that doesn't exist (no junk items).
    Returns the old item on success, raises LookupError if missing."""
    try:
        resp = ddb.update_item(
            TableName=table,
            Key=_key(user_id, job_id),
            UpdateExpression="SET #s = :s",
            ConditionExpression="attribute_exists(job_id)",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues=to_ddb({":s": status}),
            ReturnValues="ALL_OLD",
        )
        return from_ddb(resp["Attributes"])
    except ddb.exceptions.ConditionalCheckFailedException:
        raise LookupError(f"job {user_id}/{job_id} does not exist")