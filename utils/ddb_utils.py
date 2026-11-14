import uuid
from datetime import datetime, timezone
import os
import time
import boto3
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer

TABLE = os.getenv("DDB_TABLE", "research-jobs")

def get_ddb():
    """DynamoDB client: endpoint, region and credentials come from env (Floci or real AWS)."""
    return boto3.client("dynamodb")

def table_exists(ddb, name):
    return name in ddb.list_tables()["TableNames"]

def create_jobs_table(ddb, name=TABLE):
    """PK = user_id (which drawer), SK = job_id (order inside the drawer)."""
    if table_exists(ddb, name):
        return False
    ddb.create_table(
        TableName=name,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "job_id",  "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "job_id",  "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    ddb.get_waiter("table_exists").wait(TableName=name)
    return True

def new_job_id(when=None):
    """Time-sortable id like 20261114T223000-a1b2c3d4 (sorting by id = sorting by time)."""
    when = when or datetime.now(timezone.utc)
    return f"{when:%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:8]}"

def describe(ddb, name=TABLE):
    t = ddb.describe_table(TableName=name)["Table"]
    keys = [(k["AttributeName"], k["KeyType"]) for k in t["KeySchema"]]
    return t["TableName"], t["TableStatus"], keys


# The client wants typed values: {"status": {"S": "pending"}}.
# These two translate plain Python dicts to that format and back.
_ser, _de = TypeSerializer(), TypeDeserializer()

def to_ddb(d):   return {k: _ser.serialize(v) for k, v in d.items()}
def from_ddb(i): return {k: _de.deserialize(v) for k, v in i.items()}

STATUS_INDEX = "status-index"

def add_status_index(ddb, name=TABLE, index=STATUS_INDEX):
    """Add a GSI: PK = status (which drawer), SK = job_id (newest first). Safe to re-run."""
    t = ddb.describe_table(TableName=name)["Table"]
    if any(g["IndexName"] == index for g in t.get("GlobalSecondaryIndexes", [])):
        return False
    ddb.update_table(
        TableName=name,
        AttributeDefinitions=[                                   # types of the NEW key fields
            {"AttributeName": "status", "AttributeType": "S"},
            {"AttributeName": "job_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexUpdates=[{"Create": {
            "IndexName": index,
            "KeySchema": [
                {"AttributeName": "status", "KeyType": "HASH"},
                {"AttributeName": "job_id", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"},             # copy whole items into the index
        }}],
    )
    while True:                                                  # index builds in the background
        gsis = ddb.describe_table(TableName=name)["Table"].get("GlobalSecondaryIndexes", [])
        if any(g["IndexName"] == index and g["IndexStatus"] == "ACTIVE" for g in gsis):
            return True
        time.sleep(1)