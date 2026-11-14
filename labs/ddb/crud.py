import os
import sys
import random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from utils.ddb_utils import TABLE, get_ddb, new_job_id, to_ddb, from_ddb  # noqa: E402


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


ddb = get_ddb()

# CREATE
job = {"user_id": "u-vaibhav", "job_id": new_job_id(),
       "query": "what is RAG", "status": "pending", "tokens": 0}
put_job(ddb, job)
print("Put:", job["job_id"])

# READ
print("Get:", get_job(ddb, "u-vaibhav", job["job_id"]))
print("Missing:", get_job(ddb, "u-vaibhav", "nope"))

# UPDATE only the status
update_status(ddb, "u-vaibhav", job["job_id"], "done")
print("After update:", get_job(ddb, "u-vaibhav", job["job_id"]))

# DELETE
delete_job(ddb, "u-vaibhav", job["job_id"])
print("After delete:", get_job(ddb, "u-vaibhav", job["job_id"]))



ddb = get_ddb()
users = ["u-vaibhav", "u-asha", "u-rohan"]
start = datetime(2026, 10, 1, tzinfo=timezone.utc)

# INSERT 50 jobs spread over Oct–Nov
for n in range(50):
    user = random.choice(users)
    when = start + timedelta(days=random.randint(0, 60), minutes=n)
    put_job(ddb, {"user_id": user, "job_id": new_job_id(when),
                  "query": f"research topic #{n}",
                  "status": random.choice(["pending", "running", "done"])})
print("Inserted 50 jobs")

# QUERY 1: newest 5 for one user
print("\nNewest 5 for u-vaibhav:")
for j in list_user_jobs(ddb, "u-vaibhav", limit=5):
    print(" ", j["job_id"], j["status"])

# QUERY 2: date range
nov = list_user_jobs(ddb, "u-vaibhav", start="20261101", end="20261130")
print("\nu-vaibhav jobs in November:", len(nov))